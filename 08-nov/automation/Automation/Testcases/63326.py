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

    get_compacted_sfile() -- Gets compacted sfile

    wait_for_pruning() -- Check if pruning is completed successfully

    perform_defrag_tuning() --  This function enables or disables defrag related settings
    
    verify_job_status() -- Verifies the job status

    run_ddb_verification() -- Runs the ddb verification job

    get_mount_path_id() -- Gets the mount path id of the chunk

    rename_sfile_to_compact2() -- Renames sfile to .compact2

    disable_ransomware_protection() -- Disables / Enables the ransomware protection


Sample JSON: values under [] are optional
"63326": {
            "ClientName": "",
            "AgentName": "File System",
            "MediaAgentName": "",
            ["DDBPath": "",
            "ScaleFactor": "12",
            "UseScalable": true,
            "mount_path":]
        }


Note:
    1. for linux, its mandatory to provide ddb path for a lvm volume
    2. ensure that MP on cloud library is set with pruner MA

    design:
    Add regkey "AuxcopySfileFragPercent with dword value as 1" on MediaAgent for 1% fragment consideration

    add dedupe sp with provided DDB path or self search path
    disable garbage collection on dedupe store
    reduce MMPruneProcessInterval

    generate content considering scale factor true or false
    Run job with X files - J1
    Delete alternate files in content


    Delete J1
    Run aging and wait for physical pruning
    wait for phase 2 & 3 pruning to happen -> log parsing
    run space reclaim with reg key AuxcopySfileFragPercent 1
    Note down the compacted chunk
    Rename the compacted chunk sfile to sfile.compact and sfile.temp
    Run the DV2 job and job complete without any error

    Rename the compacted chunk sfile to sfile.compact and sfile.temp
    Run the Restore job from primary and job complete without any error

    Rename the compacted chunk sfile to sfile.compact and sfile.temp
    Run the Auxcopy job and job complete without any error

"""

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
        self.name = "Compact2 Recovery on Disk Storage"
        self.tcinputs = {
            "MediaAgentName": None,
            "ClientName": None,
            "AgentName": None
        }

        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.reset_ransomware = None
        self.content_path = None
        self.ddb_path = None
        self.scale_factor = None
        self.mmhelper = None
        self.dedupehelper = None
        self.client_machine = None
        self.library = None
        self.storage_policy = None
        self.media_agent_obj = None
        self.storage_pool_name = None
        self.ma_name = None
        self.gdsp = None
        self.backupset = None
        self.subclient = None
        self.primary_copy = None
        self.media_agent_machine = None
        self.mountpath = None
        self.is_user_defined_mp = None
        self.is_user_defined_dedup = None
        self.store_obj = None
        self.optionobj = None
        self.mount_path_id = None
        self.client_system_drive = None
        self.ma_library_drive = None
        self.library_name = None

    def setup(self):
        """ Setup function of this test case. """
        # input values
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        # get value or set None
        self.ddb_path = self.tcinputs.get('DDBPath')
        self.scale_factor = self.tcinputs.get('ScaleFactor', 5)

        # defining names
        self.client_machine = Machine(self.client)
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.subclient_name = f"{self.id}_SC_{self.ma_name[::-1]}"
        self.backupset_name = f"{self.id}_BS_{self.ma_name[::-1]}"
        self.storage_policy_name = f"{self.id}_SP_{self.ma_name[::-1]}"
        self.storage_pool_name = f"StoragePool_TC_{self.id}_{self.ma_name}"
        self.media_agent_machine = Machine(self.ma_name, self.commcell)
        self.optionobj = OptionsSelector(self.commcell)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine, 5120)
        self.ma_library_drive = self.optionobj.get_drive(self.media_agent_machine, 5120)
        self.secondary_library_name = f"Library2_TC_{self.id}_{self.ma_name}"

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.media_agent_machine.join_path(self.tcinputs.get("mount_path"), self.id)
        else:
            self.mountpath = self.media_agent_machine.join_path(self.ma_library_drive, self.id)

        # select drive on client & MA for content and DDB
        client_drive = self.client_machine.join_path(
            self.client_system_drive, 'automation', self.id)
        media_agent_drive = self.media_agent_machine.join_path(
            self.ma_library_drive, 'automation', self.id)

        self.content_path = self.client_machine.join_path(client_drive, 'content_path')

        if not self.ddb_path:
            if "unix" in self.media_agent_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not provided for Unix MA!..")
            self.ddb_path = self.media_agent_machine.join_path(media_agent_drive, 'DDB')
        else:
            self.log.info("will be using user specified path [%s] for DDB path configuration", self.ddb_path)

        # helper objects
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)

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

    def disable_ransomware_protection(self, media_agent_obj):
        """
        disable ransomware protection on client

        Args:
            media_agent_obj (obj)  --  MediaAgent object for the testcase run
         """
        ransomware_status = self.mmhelper.ransomware_protection_status(
        self.commcell.clients.get(media_agent_obj.name).client_id)
        self.log.info("Current ransomware status is: %s", ransomware_status)
        if ransomware_status:
            self.reset_ransomware = True
            self.log.info(
                "Disabling ransomware protection on %s", media_agent_obj.name)
            media_agent_obj.set_ransomware_protection(False)
        else:
            self.log.info("Ransomware protection is already disabled on %s", media_agent_obj.name)

    def setup_environment(self):
        """
        Configures all entities based on tcInputs. If path is provided TC will use this path instead of self selecting
        """
        self.log.info("setting up environment...")
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)

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

        # creating a secondary library
        self.mmhelper.configure_disk_library(self.secondary_library_name, self.ma_name,
                                             self.mountpath)
        self.commcell.storage_policies.refresh()

        self.gdsp = self.commcell.storage_policies.get(self.storage_pool_name)

        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                     library=self.library_name,
                                                                     media_agent=self.ma_name,
                                                                     global_policy_name=self.storage_pool_name,
                                                                     dedup_media_agent=self.ma_name,
                                                                     dedup_path=self.ddb_path)
        else:
            self.storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)

        copy1 = '%s_copy1' % str(self.id)
        self.dedupehelper.configure_dedupe_secondary_copy(self.storage_policy, copy1, self.secondary_library_name,
                                                          self.ma_name,
                                                          self.ddb_path,
                                                          self.ma_name)

        self.mmhelper.configure_backupset(self.backupset_name, self.agent)

        self.subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                           self.subclient_name,
                                                           self.storage_policy_name,
                                                           self.content_path,
                                                           self.agent)

        # Fragmentation % set to 1
        if not self.media_agent_machine.check_registry_exists('MediaAgent', 'AuxcopySfileFragPercent'):
            self.media_agent_machine.create_registry('MediaAgent', value='AuxCopySfileFragPercent',
                                                     data='1', reg_type='DWord')
            self.log.info("adding sfile fragment percentage to 1!")

        self.get_active_files_store()

        self.log.info("setting primary copy retention to 1 day, 0 cycle")
        self.primary_copy = self.storage_policy.get_copy('Primary')
        self.primary_copy.copy_retention = (1, 0, 1)
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True
    
        self.mmhelper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        self.mmhelper.update_mmconfig_param('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15, 15)
        self.mmhelper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 5)
        self.perform_defrag_tuning()

        if not self.media_agent_machine.check_registry_exists('Cvd', 'nCOMPACTOR'):
            self.media_agent_machine.create_registry('Cvd', value='nCOMPACTOR',
                                                     data='3', reg_type='DWord')

        self.mount_path_id = self.get_mount_path_id(self.library.library_id)

        if not "unix" in self.media_agent_machine.os_info.lower():
            self.disable_ransomware_protection(self.media_agent_obj)

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
            self.commcell.refresh()
            self.log.info("cleanup started")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("deleting content")
                self.client_machine.remove_directory(self.content_path)

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("deleting backupset: %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_pool_name):
                self.log.info("deleting storage policy: %s", self.storage_pool_name)
                self.commcell.storage_policies.delete(self.storage_pool_name)

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info("deleting storage pool: %s", self.storage_pool_name)
                self.commcell.storage_pools.delete(self.storage_pool_name)

            if self.commcell.disk_libraries.has_library(self.library_name):
                self.log.info("deleting library: %s", self.library_name)
                self.commcell.disk_libraries.delete(self.library_name)
            
            if self.commcell.disk_libraries.has_library(self.secondary_library_name):
                self.log.info("deleting library: %s", self.secondary_library_name)
                self.commcell.disk_libraries.delete(self.secondary_library_name)

            if not self.media_agent_machine.check_registry_exists('Cvd', 'nCOMPACTOR'):
                self.media_agent_machine.remove_registry('Cvd', 'nCOMPACTOR')

            self.commcell.refresh()

            self.log.info("cleanup completed")

        except Exception as exe:
            self.log.warning("error in cleanup: %s. please cleanup manually", str(exe))

    def verify_job_status(self, compacted_sfile, job, error_present):
        """
            check if job succeeded

            Args:
                compacted_sfile (str) -- Path of the compacted sfile container
                dv2_job (object)      --  DV2 job object
                error_present (bool)  --  True if error should be present, False otherwise
        """
        if (error_present is False and job.state.lower() == 'completed') \
                or (error_present is True and job.state.lower() == 'completed w/ one or more errors'):
            self.log.info("Job %s Verifying Status Success",
                          job.job_id)
            
            compact2_file = compacted_sfile + ".compact2"

            if self.media_agent_machine.check_file_exists(compact2_file):
                raise Exception(f"Compact2 Sfile is still present: {compact2_file}")
            
            if not self.media_agent_machine.check_file_exists(compacted_sfile):
                raise Exception(f"Recovered Sfile is not present : {compacted_sfile}")

        else:
            raise Exception(
                "Job {} Verifying Status Failed".format(job.job_id))

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
            files_list = self.client_machine.get_files_in_path(additional_content)
            self.log.info("Deleting every third file")
            for file in files_list[::3]:
                self.client_machine.delete_file(file)

        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run {backup_type} backup with error: {job.delay_reason}")
        self.log.info("Backup job completed.")

        query = f"""SELECT    archchunkid
                    FROM      archchunkmapping
                    WHERE     archfileid
                    IN       ( SELECT    id
                                FROM      archfile 
                                WHERE     jobid={job.job_id} 
                                AND       filetype=1)"""

        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()

        self.log.info(f"Query output : {res}")

        chunks = []
        for i in range(len(res)):
            chunks.append(res[i][0])
        self.log.info("got the chunks belonging to the backup job")
        self.log.info("Chunks are: %s", chunks)
        return (job, chunks)

    def run_ddb_verification(self, is_incr_dv2, is_quick_dv2):
        """
            run ddb verification

            Args:
                is_incr_dv2 (bool)           --  Is Incremental DV2 to be submitted or not
                is_quick_dv2 (bool)       --  Is this a quick DV2 request

            Returns:
                job object of the verification job
        """
        self.log.info("Running DDB verification")
        job = self.store_obj.run_ddb_verification(incremental_verification=is_incr_dv2,
                                                       quick_verification=is_quick_dv2)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run dv2 job with error: {job.delay_reason}")
        self.log.info(f"DV2 job completed having job id {job.job_id}.")
        return job

    def get_mount_path_id(self, library_id):
        """
            get the mount path id of the chunk

            Args:
                library_id (str)  --  Library ID

            Return:
                mount path id of the chunk
        """

        self.log.info("Getting mount path id")
        query = f"""select * from MMMountPath where LibraryId={library_id}"""

        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()

        self.log.info(f"Query output : {res}")

        mount_path_id = res[0]

        self.log.info("Mount path id is %s", mount_path_id)

        return mount_path_id

    def get_compacted_sfile(self, level):

        """
        Runs Defrag job with type and option selected and waits for atleast one chunk compaction, kills the cvd on MA and the job
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

        log_string = "CompactSFile\(\) - Compacted Sfile \[.+_\d+]"
        self.log.info("Keep Checking logging for Compacted")

        while space_reclaim_job.status.lower() != 'completed':
            matched_line, matched_string = self.dedupehelper.parse_log(
                client=self.ma_name, log_file=log_file,
                regex=log_string, jobid=space_reclaim_job.job_id,
                escape_regex=False, single_file=True)

            if matched_line:
                self.log.info("Sfile Compacted: [%s]", matched_line)
                for content in matched_string:
                    get_content = re.search("\[.+\]", content)
                    value = get_content.group()[1:-1]
                    # sfile_containers.append(value)
                    self.log.info(f"Compacted sfile is: {value}")
                    if not space_reclaim_job.wait_for_completion():
                        raise Exception(f"Space reclaim job {space_reclaim_job.job_id} was {space_reclaim_job.status}")
                    return value
            
            self.log.info("Sleeping for 20 seconds before checking the logs again")
            sleep(20)

                # Since we only need one sfile, returning first compacted sfile
        raise Exception(f"Space relamation job {space_reclaim_job.job_id} completed or no chunk compacted.")

    def rename_sfile_to_compact2(self, sfile):
        """
        Renames a given as to sfile.compact
        Args:
            sfile (str) -- Path to compacted sfile
        """

        self.log.info("Renaming %s to %s", sfile, sfile + ".compact2")
        self.media_agent_machine.rename_file_or_folder(sfile, sfile + ".compact2")

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()
            job1, chunks = self.run_backup()

            job2 = self.run_backup(delete_alternative=True)[0]

            self.log.info("Deleting 1st Backup [%s]", job1.job_id)
            self.primary_copy.delete_job(job1.job_id)
            self.mmhelper.submit_data_aging_job(storage_policy_name=self.storage_policy.name, copy_name='Primary')
            pruned_lines = 0
            matched_lines = self.wait_for_pruning(pruned_lines)
            self.log.info("Matched Lines : " + str(matched_lines))
            pruned_lines = len(matched_lines)
            space_reclaim_job1_compacted_sfile = self.get_compacted_sfile(2)
            if not space_reclaim_job1_compacted_sfile:
                raise Exception("Compaction didn't happen")

            self.rename_sfile_to_compact2(space_reclaim_job1_compacted_sfile)

            ddb_verification_job_1 = self.run_ddb_verification(is_incr_dv2=False, is_quick_dv2=False)
            self.verify_job_status(space_reclaim_job1_compacted_sfile,
                ddb_verification_job_1, error_present=False)

            self.rename_sfile_to_compact2(space_reclaim_job1_compacted_sfile)

            self.log.info("Starting Restore job")

            restore_job = self.subclient.restore_in_place([self.content_path])

            self.log.info(f"Restore job {restore_job.job_id} has started. Waiting for completion")

            if not restore_job.wait_for_completion():
                raise Exception(f"Restore job {restore_job.job_id} failed")

            self.verify_job_status(space_reclaim_job1_compacted_sfile,
                restore_job, error_present=False)

            self.rename_sfile_to_compact2(space_reclaim_job1_compacted_sfile)

            copy1 = '%s_copy1' % str(self.id)

            auxcopy_job = self.storage_policy.run_aux_copy(copy1)

            self.log.info("Auxcopy job [%s] has started.", auxcopy_job.job_id)

            if not auxcopy_job.wait_for_completion():
                self.log.error("Auxcopy job [%s] has failed with %s.", auxcopy_job.job_id, auxcopy_job.delay_reason)
                raise Exception("Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id,
                                                                                auxcopy_job.delay_reason))

            self.log.info("Auxcopy job [%s] has completed.", auxcopy_job.job_id)

            self.verify_job_status(space_reclaim_job1_compacted_sfile,
                auxcopy_job, error_present=False)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED')
        else:
            self.log.warning('Test Case FAILED')
        self.perform_defrag_tuning(enable=False)
        
        self.log.info("Cleaning up the entities")
        self.cleanup()
        if self.reset_ransomware:
            self.log.info(
                "Enabling ransomware protection on MA")
            self.media_agent_obj.set_ransomware_protection(True)
