# coding=utf-8
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""

Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    setup_environment() -- configures entities based on inputs

    get_active_files_store() -- gets active files DDB store id

    cleanup()   --  cleanups all created entities

    run_backup()    -- runs backup need for the case

    validate_space_reclaim() -- validates the DDB space reclaim job

    get_compacted_chunk() -- Check if chunk is compacted, if yes then suspend/resume the job

    wait_for_pruning() -- Check if pruning is completed successfully


Sample JSON: values under [] are optional
"62863": {
            "ClientName": "",
            "AgentName": "File System",
            "MediaAgentName": "",
            ["dedup_path": "",
            "ScaleFactor": "12",
            "UseScalable": true,
            "mount_path":]
        }


Note:
    1. for linux, its mandatory to provide ddb path for a lvm volume
    2. ensure that MP on cloud library is set with pruner MA

    design:
    Add regkey "AuxcopySfileFragPercent with dword value as 1" on MediaAgent for 1% fragment consideration
    add dedupe sp with provided DDB path or self search path (use provided cloud lib)
    disable garbage collection on dedupe store

    generate content considering scale factor true or false
    Run job with X files - J1
    Delete alternate files in content
    Run job with alternate files - J2

    Delete J1
    Run aging and wait for physical pruning
    wait for phase 2 & 3 pruning to happen -> log parsing
    run space reclaim with reg key AuxcopySfileFragPercent 1 on MediaAgent
    Note down the compacted chunk from the below log on ScalableDDBVerf.log(UseScalable is True) / DataVerf.log
    4992  25bc  01/04 02:58:16 457556 CompactChunk() - Compacted chunk [166, 3606, 401083]. Speed Read [272.67] MB/sec. Write [120.48] MB/sec.

    Delete alternate files in content
    Run job with alternate X/2 files - J3
    Delete J2

    Run aging and wait for physical pruning
    wait for phase 2 & 3 pruning to happen -> log parsing
    run space reclaim with reg key AuxcopySfileFragPercent 1

    Validate we are doing the compaction on same chunk without any issue.

"""

import time
import re
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from MediaAgents.MAUtils.mahelper import DedupeHelper
from time import sleep


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Run Space Reclamation job on Already Compacted Chunk"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.ddb_path = None
        self.scale_factor = None
        self.mmhelper = None
        self.dedupehelper = None
        self.client_machine = None
        self.library = None
        self.storage_policy = None
        self.storage_pool_name = None
        self.ma_name = None
        self.backupset = None
        self.subclient = None
        self.primary_copy = None
        self.media_agent_machine = None
        self.mountpath = None
        self.is_user_defined_mp = None
        self.is_user_defined_dedup = None
        self.store_obj = None

    def setup(self):
        """ Setup function of this test case. """
        # input values
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        # get value or set None
        self.ddb_path = self.tcinputs.get('dedup_path')
        self.scale_factor = self.tcinputs.get('ScaleFactor', 6)

        # defining names
        self.client_machine = Machine(self.client)
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.subclient_name = f"{self.id}_SC_{self.ma_name[::-1]}"
        self.backupset_name = f"{self.id}_BS_{self.ma_name[::-1]}"
        self.storage_policy_name = f"{self.id}_SP_{self.ma_name[::-1]}"
        self.storage_pool_name = f"StoragePool_TC_{self.id}_{self.ma_name[1:]}"
        self.media_agent_machine = Machine(self.ma_name, self.commcell)
        self.optionobj = OptionsSelector(self.commcell)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine, 15)
        self.ma_library_drive = self.optionobj.get_drive(self.media_agent_machine, 15)

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.media_agent_machine.join_path(self.tcinputs.get("mount_path"), self.id)
        else:
            self.mountpath = self.media_agent_machine.join_path(self.ma_library_drive, self.id)

        # select drive on client & MA for content and DDB
        client_drive = self.client_machine.join_path(
            self.optionobj.get_drive(self.client_machine), 'automation', self.id)
        media_agent_drive = self.media_agent_machine.join_path(
            self.optionobj.get_drive(self.media_agent_machine), 'automation', self.id)

        self.content_path = self.client_machine.join_path(client_drive, 'content_path')

        if not self.ddb_path:
            if "unix" in self.media_agent_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not provided for Unix MA!..")
            self.ddb_path = self.media_agent_machine.join_path(media_agent_drive, 'DDB')
        else:
            self.log.info("will be using user specified path [%s] for DDB path configuration", self.ddb_path)
            self.ddb_path = self.media_agent_machine.join_path(self.ddb_path, 'automation', self.id, 'DDB')

        # helper objects
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)

    def perform_defrag_tuning(self, enable=True):
        """
        This function enables or disables defrag related settings
        - 128 attribute on MountPath
        - DedupeDrillHoles on MediaAgent

        Args:
            enable(boolean) - Boolean value for enabling or disabling the Defrag related settings
        """
        # Find Mountpath and turn off 128 bit if enable=True, turn on 128 if enable=False
        mountpath_attributes = "& ~128"
        ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
        if not enable:
            self.log.info("Removing Drill Holes Regkey")
            ma_client.delete_additional_setting("MediaAgent", "DedupDrillHoles")
            self.log.info("adding 128 attribute back to mountpaths of library %s", self.library_name)
            mountpath_attributes = "|128"
        else:
            self.log.info("setting drill holes regkey to 0")
            ma_client.add_additional_setting("MediaAgent", "DedupDrillHoles", 'INTEGER', '0')
            self.log.info("removing 128 attribute from mountpaths of library %s", self.library_name)

        query = f"update MMMountpath set attribute = attribute {mountpath_attributes} where mountpathid in (" \
                f"select mountpathid from MMMountpath where libraryid in (" \
                f"select libraryid from MMLibrary where aliasname = '{self.library_name}'))"

        self.log.info("QUERY => %s", query)
        self.optionobj.update_commserve_db(query)

    def setup_environment(self):
        """
        Configures all entities based on tcInputs. If path is provided TC will use this path instead of self selecting
        """
        self.log.info("setting up environment...")

        if not self.media_agent_machine.check_directory_exists(self.mountpath):
            self.log.info("Creating mountpath directory [%s]", self.mountpath)
            self.media_agent_machine.create_directory(self.mountpath)

        self.log.info("Creating a storage pool")

        # Creating a storage pool and associate to a SP

        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mountpath,
                                                                self.ma_name,
                                                                self.ma_name,
                                                                self.ddb_path)
        else:
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)

        self.log.info("Done creating a storage pool")

        self.log.info("Configuring Storage Policy ==> %s", self.storage_policy_name)

        self.library_name = self.storage_pool_name

        self.commcell.disk_libraries.refresh()

        if not self.commcell.disk_libraries.has_library(self.library_name):
            self.log.error("Disk library %s does not exist!", self.library_name)
            raise Exception(f"Disk library {self.library_name} does not exist!")
        else:
            self.library = self.commcell.disk_libraries.get(self.library_name)

        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                     library=self.library_name,
                                                                     media_agent=self.ma_name,
                                                                     global_policy_name=self.storage_pool_name,
                                                                     dedup_media_agent=self.ma_name,
                                                                     dedup_path=self.ddb_path)
        else:
            self.storage_policy = self.commcell.storage_policies.has_policy(self.storage_policy_name)

        # Fragmentation % set to 1
        if not self.media_agent_machine.check_registry_exists('MediaAgent', 'AuxcopySfileFragPercent'):
            self.media_agent_machine.create_registry('MediaAgent', value='AuxCopySfileFragPercent',
                                                     data='1', reg_type='DWord')
            self.log.info("adding sfile fragment percentage to 1!")

        # add partition for dedupe engine
        part2_dir = self.media_agent_machine.join_path(self.ddb_path,
                                                       "Part2Dir" + self.dedupehelper.option_selector.get_custom_str())
        if not self.media_agent_machine.check_directory_exists(part2_dir):
            self.media_agent_machine.create_directory(part2_dir)

        self.log.info("adding partition for the dedup store")
        self.get_active_files_store()
        self.storage_policy.add_ddb_partition(self.storage_policy.get_copy('Primary').copy_id, str(self.store_obj.store_id),
                                              part2_dir, self.tcinputs.get("MediaAgentName"))

        self.log.info("setting primary copy retention to 1 day, 0 cycle")
        self.log.info("setting primary copy retention to 1 day, 0 cycle")
        self.log.info("setting primary copy retention to 1 day, 0 cycle")
        self.primary_copy = self.storage_policy.get_copy('Primary')
        self.primary_copy.copy_retention = (1, 0, 1)

        self.log.info("disabling garbage collection to avoid complications in waiting for physical prune")

        # get store object
        self.mmhelper.configure_backupset(self.backupset_name, self.agent)

        self.subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                           self.subclient_name,
                                                           self.storage_policy_name,
                                                           self.content_path,
                                                           self.agent)
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True
        # check if both values will be reverted back. If not, revert in cleanup
        self.mmhelper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        self.mmhelper.update_mmconfig_param('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15, 15)
        self.mmhelper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 5)

        self.perform_defrag_tuning()

    def get_active_files_store(self):
        """Returns active store object for files iDA"""

        self.commcell.deduplication_engines.refresh()
        dedup_engines_obj = self.commcell.deduplication_engines
        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])
                self.log.info("Disabling Garbage Collection on DDB Store == %s" + str(dedup_store[0]))
                self.store_obj.enable_garbage_collection = False

    def wait_for_pruning(self, pruned_lines):
        for _ in range(7):
            matched_lines = self.dedupehelper.validate_pruning_phase(self.store_obj.store_id, self.ma_name)
            if matched_lines is None or not (len(matched_lines) != pruned_lines):
                self.log.info("Waiting for pruning to complete")
                sleep(300)
            else:
                self.log.info("Pruning is complete!")
                return matched_lines
        raise Exception("Pruning is not done")

    def cleanup(self):
        """Performs cleanup of all entities"""
        try:
            self.log.info("cleanup started")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("deleting content")
                self.client_machine.remove_directory(self.content_path)

            if self.media_agent_machine.check_registry_exists('MediaAgent', 'AuxcopySfileFragPercent'):
                self.log.info("Removing AuxcopySfileFragPercent reg key from MA")
                self.media_agent_machine.remove_registry('MediaAgent', value='AuxCopySfileFragPercent')

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("deleting backupset: %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("deleting storage policy: %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info("deleting storage pool: %s", self.storage_pool_name)
                self.commcell.storage_pools.delete(self.storage_pool_name)

            self.commcell.refresh()

            self.log.info("cleanup completed")


        except Exception as exe:
            self.log.warning("error in cleanup: %s. please cleanup manually", str(exe))

    def run_backup(self, backup_type="FULL", size=1024.0, delete_alternative=False):
        """Run backup by generating new content to get unique blocks for dedupe backups.
        If ScaleFactor in tcInputs, creates factor times of backup data

        Args:
            backup_type (str): type of backup to run
                Default - FULL

            size (int): size of backup content to generate
                Default - 1024 MB

            delete_alternative (bool): deleting alternate content(every 3rd file) before running backup
                Default - False
        Returns:
            (Job): returns job object of the backup job
        """
        additional_content = self.client_machine.join_path(self.content_path, 'generated_content')
        if not delete_alternative:
            # add content
            if self.client_machine.check_directory_exists(additional_content):
                self.client_machine.remove_directory(additional_content)
            # if scalefactor param is passed in input json, multiple size factor times and generate content
            if self.scale_factor:
                size = size * int(self.scale_factor)
            file_size = 512
            self.mmhelper.create_uncompressable_data(self.client_machine,
                                                     additional_content, size // 1024, file_size=file_size)
        else:
            target = ""
            target_folders = self.client_machine.get_folders_in_path(additional_content)
            self.log.info(target_folders)
            if target_folders:
                target = target_folders[0]
            self.log.info(f"Deleting every alternate file from {target}")
            self.optionobj.delete_nth_files_in_directory(self.client_machine, target, 3, "delete")

        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run {backup_type} backup with error: {job.delay_reason}")
        self.log.info("Backup job completed.")
        return job

    def validate_space_reclaim(self, space_reclaim_job):
        """ Validates the space reclaim job for following:
        1. check AuxCopyMgr logging for all chunks to be processed

        Args:
            space_reclaim_job (Job)  : space reclaim job object

        Raises:
            Exception   :   if validations fail
        """

        self.log.info("VALIDATION: chunks to process == chunks processed")

        log_string = "Total chunks to be compacted"
        if self.tcinputs.get('UseScalable', True):
            log_file = 'MediaManagerDashCopy.log'
        else:
            log_file = 'AuxCopyMgr.log'

        (matched_line, matched_string) = self.dedupehelper.parse_log(
            self.commcell.commserv_client, log_file, log_string, jobid=space_reclaim_job.job_id)

        if matched_line:
            chunks_to_compact = int(matched_line[0].split()[11].split('[')[1].split(']')[0])
            chunks_compacted = int(matched_line[0].split()[15].split('[')[1].split(']')[0])
            self.log.info("Chunks to be Compacted: [%s], Chunks Compacted: [%s]",
                          chunks_to_compact, chunks_compacted)
            if chunks_to_compact != chunks_compacted:
                raise Exception("VALIDATION FAILED: Chunks Compacted does not equal Chunks to be Compacted")
            self.log.info("VALIDATION PASSED: All chunks were processed for compaction.")
        else:
            raise Exception("Log string [Total Chunks to be compacted] Not Found")

    def get_compacted_chunk(self, level):

        """
        Runs Defrag job with type and option selected and waits for job to complete
        Args:
            level (int) - level for the space reclamation job
        """

        self.log.info("Running Space Reclamation Job")
        self.store_obj.refresh()
        space_reclaim_job = self.store_obj.run_space_reclaimation(
            level=level,
            clean_orphan_data=False,
            use_scalable_resource=self.tcinputs.get("UseScalable", True)
        )

        self.log.info("Space Reclaim job ID : %s", space_reclaim_job.job_id)
        if self.tcinputs.get('UseScalable', True):
            log_file = 'ScalableDDBVerf.log'
        else:
            log_file = 'DataVerf.log'

        self.log.info("Wait till the job completes")

        space_reclaim_job.wait_for_completion()

        log_string = "CompactChunk\(\) - Compacted chunk \[\d+, \d+, \d+\]"
        self.log.info("Keep Checking logging for Compacted")
        matched_line, matched_string = self.dedupehelper.parse_log(
            client=self.ma_name, log_file=log_file,
            regex=log_string, jobid=space_reclaim_job.job_id,
            escape_regex=False)

        if matched_line:
            self.log.info("Chunk Compacted: [%s]", matched_line)
            chunk_ids = []
            for content in matched_string:
                get_content = re.search('\[\d+, \d+, \d+\]', content)
                values = get_content.group()[1:-1]
                chunk_id = int(values.split(", ")[-1])
                chunk_ids.append(chunk_id)
            self.log.info("Space Reclamation Job(Id: %s) completed", space_reclaim_job.job_id)
            self.log.info("Compacted chunks are " + str(chunk_ids))
            return chunk_ids
        else:
            raise Exception("Job is not in Defragment Data Phase")

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()
            backup_job_list = []
            job1 = self.run_backup()
            backup_job_list.append(job1.job_id)
            job2 = self.run_backup(delete_alternative=True)
            backup_job_list.append(job2.job_id)
            self.log.info("Deleting 1st Backup [%s]", job1.job_id)
            self.primary_copy.delete_job(job1.job_id)
            self.mmhelper.submit_data_aging_job(storage_policy_name=self.storage_policy.name, copy_name='Primary')
            pruned_lines = 0
            matched_lines = self.wait_for_pruning(pruned_lines)
            self.log.info("Matched Lines : " + str(matched_lines))
            pruned_lines = len(matched_lines)

            space_reclaim_job1_compacted_chunk = self.get_compacted_chunk(2)
            if not space_reclaim_job1_compacted_chunk:
                raise Exception("Compaction didn't happen")

            job3 = self.run_backup(delete_alternative=True)

            self.log.info("Deleting 2nd Backup [%s]", job2.job_id)
            self.primary_copy.delete_job(job2.job_id)
            data_aging_job = self.mmhelper.submit_data_aging_job(storage_policy_name=self.storage_policy.name,
                                                                 copy_name='Primary')

            data_aging_job.wait_for_completion()
            matched_lines = self.wait_for_pruning(pruned_lines)
            self.log.info("Matched Lines : " + str(matched_lines))

            space_reclaim_job2_compacted_chunk = self.get_compacted_chunk(4)
            if not space_reclaim_job2_compacted_chunk:
                raise Exception("Did not get any compacted chunks after running Space Reclamation job")

            res = list(set(space_reclaim_job1_compacted_chunk).intersection(space_reclaim_job2_compacted_chunk))

            if res:
                self.log.info("Space Reclamation happened on (compacted: %s) chunk(s)", res)

            else:
                raise Exception("Space Reclamation did not happen on already compacted chunk(s)")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        try:

            self.log.info('Cleaning Up the Entities unconditionally')
            self.perform_defrag_tuning(enable=False)
            self.cleanup()
        except Exception as ex:
            self.log.warning(f"Cleanup failed - {ex}")
