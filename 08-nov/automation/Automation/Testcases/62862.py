# coding=utf-8
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""

Main file for executing this test case

Note regarding sql credentials :


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

    check_for_phase2_start() -- checks if phase 2 pruning has started

    check_for_phase3_start() -- checks if phase 3 pruning has started

    run_and_suspend_defrag_job() -- Check if chunk is compacted, if yes then suspend/resume the job


Sample JSON: values under [] are optional
"62862": {
            "ClientName": "",
            "AgentName": "File System",
            "MediaAgentName": "",
            "CloudLibraryName": ""
            ["DDBPath": "",
            "ScaleFactor": "12",
            "UseScalable": true]
        }


Note:
    1. providing cloud library is must as there are various vendors for configuration. best is to have it ready
    [mmhelper.configure_cloud_library can be used if need to create library]
    2. for linux, its mandatory to provide ddb path for a lvm volume
    3. ensure that MP on cloud library is set with pruner MA


    SQL Connection :
        In order to ensure security,
        sql credentials have to be passed to the TC via config.json file under CoreUtils/Templates
        populate the following fields in config file as required,
        "SQL": {
               "Username": "<SQL_SERVER_USERNAME>",
                "Password": "<SQL_SERVER_PASSWORD>"
            }

        At the time of execution the creds will be automatically fetched by TC.


    design:
    Add regkey to 1% fragment consideration

    add dedupe sp with provided DDB path or self search path (use provided cloud lib)
    disable garbage collection on dedupe store
    reduce MMPruneProcessInterval

    generate content considering scale factor true or false
    Run job with 100 files - J1
    Delete alternate files in content
    Run job with alternate 50 files - J2

    Delete J1
    Run aging and wait for physical pruning
    wait for phase 2 & 3 pruning to happen -> log parsing

    run space reclaim with reg key AuxcopySfileFragPercent 1
    Suspend Space reclaim job after found 1st compacted chunk and then Resume the job

    check to be compacted chunk and compacted chunk count is same.

"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from MediaAgents.MAUtils.mahelper import DedupeHelper
from AutomationUtils import config


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Suspend And Resume Space Reclamation job during Defrag Phase"
        self.tcinputs = {
            "MediaAgentName": None,
            "CloudLibraryName": None
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
        self.backupset = None
        self.subclient = None
        self.primary_copy = None
        self.media_agent_machine = None
        self.sql_password = None

    def setup(self):
        """ Setup function of this test case. """
        # input values
        self.library_name = self.tcinputs.get('CloudLibraryName')

        # get value or set None
        self.ddb_path = self.tcinputs.get('DDBPath')
        self.scale_factor = self.tcinputs.get('ScaleFactor')

        # defining names
        self.subclient_name = f"{self.id}_SC_{self.tcinputs.get('MediaAgentName')[::-1]}"
        self.backupset_name = f"{str(self.id)}_BS_{self.tcinputs.get('MediaAgentName')[::-1]}"
        self.storage_policy_name = f"{str(self.id)}_SP_{self.tcinputs.get('MediaAgentName')[::-1]}"

        # machine objects
        self.client_machine = Machine(self.tcinputs.get('ClientName'), self.commcell)
        self.media_agent_machine = Machine(self.tcinputs.get('MediaAgentName'), self.commcell)

        # select drive on client & MA for content and DDB
        op_selector = OptionsSelector(self.commcell)
        client_drive = self.client_machine.join_path(
            op_selector.get_drive(self.client_machine), 'automation', self.id)
        media_agent_drive = self.media_agent_machine.join_path(
            op_selector.get_drive(self.media_agent_machine), 'automation', self.id)


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

        # handling password security
        # sql connections
        self.sql_username = config.get_config().SQL.Username
        self.sql_password = config.get_config().SQL.Password

    def setup_environment(self):
        """
        Configures all entities based on tcInputs. If path is provided TC will use this path instead of self selecting
        """
        self.log.info("setting up environment...")
        # Fragmentation % set to 1
        if not self.media_agent_machine.check_registry_exists('MediaAgent', 'AuxcopySfileFragPercent'):
            self.media_agent_machine.create_registry('MediaAgent', value='AuxCopySfileFragPercent',
                                                     data='1', reg_type='DWord')
            self.log.info("adding sfile fragment percentage to 1!")

        if not self.commcell.disk_libraries.has_library(self.library_name):
            self.log.error("Cloud library %s does not exist!", self.library_name)
            raise Exception(f"Cloud library {self.library_name} does not exist!")
        self.library = self.commcell.disk_libraries.get(self.library_name)

        if not self.media_agent_machine.check_directory_exists(self.ddb_path):
            self.media_agent_machine.create_directory(self.ddb_path)
        self.storage_policy = self.dedupehelper.configure_dedupe_storage_policy(
            self.storage_policy_name, library_name=self.library.name, ddb_ma_name=self.tcinputs.get("MediaAgentName"),
            ddb_path=self.media_agent_machine.join_path(self.ddb_path, "Part1Dir"))

        # add partition for dedupe engine
        part2_dir = self.media_agent_machine.join_path(self.ddb_path,
                                                       "Part2Dir" + self.dedupehelper.option_selector.get_custom_str())
        if not self.media_agent_machine.check_directory_exists(part2_dir):
            self.media_agent_machine.create_directory(part2_dir)
        self.log.info("adding partition for the dedup store")
        store = self.get_active_files_store()
        self.storage_policy.add_ddb_partition(self.storage_policy.get_copy('Primary').copy_id, str(store.store_id),
                                              part2_dir, self.tcinputs.get("MediaAgentName"))

        self.log.info("setting primary copy retention to 1 day, 0 cycle")
        self.primary_copy = self.storage_policy.get_copy('Primary')
        self.primary_copy.copy_retention = (1, 0, 1)

        self.log.info("disabling garbage collection to avoid complications in waiting for physical prune")

        # get store object
        store.enable_garbage_collection = False
        self.mmhelper.configure_backupset(self.backupset_name, self.agent)

        self.subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                           self.subclient_name,
                                                           self.storage_policy_name,
                                                           self.content_path,
                                                           self.agent)
        self.subclient.data_readers = 1
        self.subclient.allow_multiple_readers = True
        # check if both values will be reverted back. If not, revert in cleanup
        self.mmhelper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        self.mmhelper.update_mmconfig_param('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15, 15)
        self.mmhelper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 5)

    def get_active_files_store(self):
        """Returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.storage_policy_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

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
                Default - 2048 MB

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
            self.log.info("deleting alternate content files...")
            for i, file in enumerate(files_list):
                if i % 3 == 0:
                    self.client_machine.delete_file(file)

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

        time.sleep(90)
        (matched_line, matched_string) = self.dedupehelper.parse_log(
            self.commcell.commserv_client, log_file, log_string, jobid=space_reclaim_job.job_id)

        if matched_line:
            # Total chunks to be compacted [4], Total chunks compacted [4], Total chunks with data gain [0]
            # on SIDB StoreID [70] in DV2 job
            chunks_to_compact = int(matched_line[0].split()[11].split('[')[1].split(']')[0])
            chunks_compacted = int(matched_line[0].split()[15].split('[')[1].split(']')[0])
            self.log.info("Chunks to be Compacted: [%s], Chunks Compacted: [%s]",
                          chunks_to_compact, chunks_compacted)
            if chunks_to_compact != chunks_compacted:
                raise Exception("VALIDATION FAILED: Chunks Compacted does not equal Chunks to be Compacted")
            self.log.info("VALIDATION PASSED: All chunks were processed for compaction.")
        else:
            raise Exception("Log string [Total Chunks to be compacted] Not Found")

    def check_for_phase2_start(self, store_id, primary_count):
        """Check if phase 2 pruning started on store.
        LOGIC: phase 2 completed: primary count decreased compared to post backup value [primary_count].

        Args:
            store_id(int)       : store id on which phase 2 needs to be checked
            primary_count(int)  : primary records count post all backups and before running data aging
        Returns:
             (bool, int) :   if the phase is started then True else False and zeroref count
        """
        self.log.info("checking if Phase 2 started [logic: current primary count < post backup primary count ]")

        for _ in range(5):
            current_primary_count = int(self.dedupehelper.get_primary_recs_count(store_id,
                                                                                 db_password=self.sql_password,
                                                                                 db_user=self.sql_username))
            current_zeroref_count = int(self.dedupehelper.get_zeroref_recs_count(store_id,
                                                                                 db_password=self.sql_password,
                                                                                 db_user=self.sql_username))
            self.log.info("RESULT: primary count[%s] zeroref count[%s]", current_primary_count, current_zeroref_count)
            if current_primary_count < int(primary_count):
                self.log.info("Phase 2 pruning started...")
                return True, current_zeroref_count
            time.sleep(60)
        self.log.error("timeout reached, Phase 2 pruning did not start")
        return False, 0

    def check_for_phase3_start(self, store_id, zeroref_count):
        """Checks if phase 3 pruning started on store.
        LOGIC: phase 3 completed: zeroref count decreased compared to value during phase2 [zeroref_count].

        Args:
            store_id (integer)      : store id on which phase 2 needs to be checked
            zeroref_count (integer) : zeroref records count during phase2 check
        Returns:
             (bool) : if the phase is started then True else False
        """
        count = 0
        self.log.info("checking if Phase 3 started [logic: phase 2 zeroref count > latest zeroref count]")

        latest_zeroref_count = int(self.dedupehelper.get_zeroref_recs_count(store_id, db_password=self.sql_password,
                                                                            db_user=self.sql_username))
        while zeroref_count <= latest_zeroref_count and count < 15:
            count += 1
            time.sleep(60)
            self.log.info("zeroref count before phase3 [%s], latest zeroref count[%s]", zeroref_count,
                          latest_zeroref_count)
            latest_zeroref_count = int(self.dedupehelper.get_zeroref_recs_count(store_id,
                                                                                db_password=self.sql_password,
                                                                                db_user=self.sql_username))
        if zeroref_count > latest_zeroref_count:
            self.log.info("Phase 3 pruning started...")
            return True
        self.log.error("timeout reached, Phase 3 pruning did not start")
        return False

    def run_and_suspend_defrag_job(self, store):

        """
        Runs Defrag job with type and option selected and waits for job to complete
        Args:
            store (object) - object of the store to run DV2 job on
        """

        self.log.info("Running Space Reclamation Job")
        store.refresh()
        space_reclaim_job = store.run_space_reclaimation(
            clean_orphan_data=False,
            use_scalable_resource=self.tcinputs.get("UseScalable", True), num_streams=1)
        self.log.info("Space Reclaim job ID : %s", space_reclaim_job.job_id)

        # 13352 990   08/10 05:54:37 7923 CompactChunk() - Compacted chunk [5, 213, 9643].
        if self.tcinputs.get('UseScalable', True):
            log_file = 'ScalableDDBVerf.log'
        else:
            log_file = 'DataVerf.log'

        self.log.info("Wait for maximum five minutes")
        log_string = "CompactChunk() - Compacted chunk"
        wait_limit = 0
        while wait_limit < 60:
            self.log.info("Keep Checking logging for Compacted, if found then suspend the job")
            (matched_line, matched_string) = self.dedupehelper.parse_log(
                self.commcell.commserv_client, log_file, log_string, jobid=space_reclaim_job.job_id)

            if matched_line:
                self.log.info("Chunk Compacted: [%s]", matched_line)
                if space_reclaim_job.phase == "Defragment Data":
                    self.log.info("Job Phase : [%s]. will suspend the job", space_reclaim_job.phase)
                    space_reclaim_job.pause(wait_for_job_to_pause=True)
                    self.log.info("Suspended Space Reclaim job: %s", space_reclaim_job.job_id)
                    space_reclaim_job.resume(wait_for_job_to_resume=True)
                    self.log.info("Resumed Space Reclaim job: %s", space_reclaim_job.job_id)

                    self.log.info("Wait for Space Reclaim job to complete: %s", space_reclaim_job.job_id)
                    if not space_reclaim_job.wait_for_completion():
                        raise Exception(f"Failed to complete DDB Space reclaim(Job Id: {space_reclaim_job.job_id})"
                                        f"with error: {space_reclaim_job.delay_reason}")
                    self.log.info("Space Reclamation Job(Id: %s) completed", space_reclaim_job.job_id)
                    return space_reclaim_job

                else:
                    self.log.error("Job is not in Defragment Data Phase")
                    return None

            wait_limit += 1
            time.sleep(5)
            self.log.info("Wait for job to go in Defragment Data :  Another 5 second try")

        return None

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()
            with_ocl = False
            backup_job_list = []
            job1 = self.run_backup()
            backup_job_list.append(job1.job_id)
            job2 = self.run_backup(delete_alternative=True)
            backup_job_list.append(job2.job_id)
            store = self.get_active_files_store()

            primary_recs = self.dedupehelper.get_primary_recs_count(store.store_id, db_password=self.sql_password,
                                                                    db_user=self.sql_username)
            self.log.info("Deleting 1st Backup [%s]", job1.job_id)
            self.primary_copy.delete_job(job1.job_id)
            self.mmhelper.submit_data_aging_job(storage_policy_name=self.storage_policy_name, copy_name='primary')

            phase_2_started, zero_ref_count = self.check_for_phase2_start(store.store_id, primary_recs)
            if not phase_2_started:
                raise Exception("Phase 2 pruning did not happen")
            else:
                if not with_ocl:
                    self.check_for_phase3_start(store.store_id, zero_ref_count)

            # Suspend and Resume Space reclaim job after found 1st compacted chunk
            space_reclaim_job = self.run_and_suspend_defrag_job(store)
            if not space_reclaim_job:
                raise Exception("failed to suspend Space Reclaimation job")

            self.log.info("Space Reclamation Job(Id: %s) completed", space_reclaim_job.job_id)
            self.validate_space_reclaim(space_reclaim_job)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED. Cleaning Up the Entities')
            self.cleanup()
        else:
            self.log.warning('Test Case FAILED. Hence Not CleaningUp for debugging')
