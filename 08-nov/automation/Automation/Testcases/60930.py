# coding=utf-8
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

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

    run_ddb_recon() -- starts a ddb recon job

    mmvolume_get_physical_size() -- gets physical size of volume from MMVolume table

    wait_for_volume_size_update() -- poll for volume size update with a timeout set

    reduce_volume_size_update_time() -- reduces volume size update time

    get_volumes_for_job() -- gets volumes list from provided jobs

Sample JSON: values under [] are optional
"60930": {
            "ClientName": "",
            "AgentName": "File System",
            "MediaAgentName": "",
            "CloudLibraryName": ""
            ["DDBPath": "",
            "ContentPath": "",
            "ScaleFactor": "5",
            "UseScalable": true]
        }


Note:
    1. providing cloud library is must as there are various vendors for configuration. best is to have it ready
    [mmhelper.configure_cloud_library can be used if need to create library]
    2. for linux, its mandatory to provide ddb path for a lvm volume
    3. ensure that MP on cloud library is set with pruner MA

design:
    [optional] add regkey to 0% fragment consideration

    add dedupe sp with provided DDB path or self search path (use provided cloud lib)
    disable garbage collection on dedupe store
    reduce MMPruneProcessInterval
    reduce volume size update interval

    generate content considering scale factor true or false
    Run job with 100 files - J1
    Delete alternate files in content
    Run job with alternate 50 files - J2

    Delete J1
    Run aging and wait for zeroref count to increase
    after zeroref count is greater than 0, corrupt store and start full recon

    make a not of volume sizes from MMVolume

    run space reclaim with OCL enabled (level 4)
        verify orphan chunk is pruned -> log parsing
        verify 3 phases overall
        verify store is set with validate and prune flags

    make a note of volume sizes post defrag job and compare to see size reduction

    generate content considering scale factor true or false
    Run job with 100 files - J1
    Delete alternate files in content
    Run job with alternate 50 files - J2

    Delete J1
    Run aging and wait for physical pruning
    wait for phase 2 & 3 pruning to happen -> log parsing

    make a not of volume sizes from MMVolume
    run space reclaim with ocl disabled (level 4)
        verify compacted chunks
        verify 2 phases overall
        verify store is set with validate and prune flags
    make a note of volume sizes post defrag job and compare to see size reduction
    run DV2 and make sure no bad chunks are added
    check archChunkDDBDrop for no bad chunks
"""
import time
from AutomationUtils import constants
from AutomationUtils import commonutils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from MediaAgents.MAUtils.mahelper import DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "cloud defrag - basic case with validation"
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
        self.allow_compaction_key_added = False
        self.allow_compaction_key_updated = False
        self.optionobj = None

    def setup(self):
        """ Setup function of this test case. """
        # input values
        self.optionobj = OptionsSelector(self.commcell)
        self.library_name = self.tcinputs.get('CloudLibraryName')

        # get value or set None
        self.ddb_path = self.tcinputs.get('DDBPath')
        self.content_path = self.tcinputs.get('ContentPath')
        self.scale_factor = self.tcinputs.get('ScaleFactor')

        # defining names
        self.subclient_name = f"{str(self.id)}_SC_{self.tcinputs.get('MediaAgentName')[::-1]}"
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

        if not self.content_path:
            self.content_path = self.client_machine.join_path(client_drive, 'content_path')
        else:
            self.log.info("will be using user specified path [%s] for backup content", self.content_path)
            self.content_path = self.client_machine.join_path(self.content_path, 'automation', self.id, 'Content')

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
        self.sql_password = commonutils.get_cvadmin_password(self.commcell)

    def setup_environment(self):
        """
        Configures all entities based on tcInputs. If path is provided TC will use this path instead of self selecting
        """
        self.log.info("setting up environment...")
        # uncomment below part of the code to make it a fix if fragmentation % is lower than 20
        # if not self.media_agent_machine.check_registry_exists('MediaAgent', 'AuxcopySfileFragPercent'):
        #     self.media_agent_machine.create_registry('MediaAgent', value='AuxCopySfileFragPercent',
        #                                              data='0', reg_type='DWord')
        #     self.log.info("adding sfile fragment percentage to 0!")

        if not self.commcell.disk_libraries.has_library(self.library_name):
            self.log.error("Cloud library %s does not exist!", self.library_name)
            raise Exception(f"Cloud library {self.library_name} does not exist!")
        self.library = self.commcell.disk_libraries.get(self.library_name)

        if not self.media_agent_machine.check_directory_exists(self.ddb_path):
            self.media_agent_machine.create_directory(self.ddb_path)
        self.storage_policy = self.dedupehelper.configure_dedupe_storage_policy(
            self.storage_policy_name, library_name=self.library.name, ddb_ma_name=self.tcinputs.get("MediaAgentName"),
            ddb_path=self.media_agent_machine.join_path(self.ddb_path, "Part1Dir"))

        # get store object
        store = self.get_active_files_store()
        # add partition for dedupe engine
        part2_dir = self.media_agent_machine.join_path(self.ddb_path,
                                                       "Part2Dir" + self.dedupehelper.option_selector.get_custom_str())
        if not self.media_agent_machine.check_directory_exists(part2_dir):
            self.media_agent_machine.create_directory(part2_dir)
        self.log.info("adding partition for the dedup store")
        self.storage_policy.add_ddb_partition(self.storage_policy.get_copy('Primary').copy_id, str(store.store_id),
                                              part2_dir, self.tcinputs.get("MediaAgentName"))

        self.log.info("setting primary copy retention to 1 day, 0 cycle")
        self.primary_copy = self.storage_policy.get_copy('Primary')
        self.primary_copy.copy_retention = (1, 0, 1)

        self.log.info("disabling garbage collection to avoid complications in waiting for physical prune")
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
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("deleting backupset: %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("deleting storage policy: %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("deleting content")
                self.client_machine.remove_directory(self.content_path)
            self.log.info("cleanup completed")
        except Exception as exe:
            self.log.warning("error in cleanup: %s. please cleanup manually", str(exe))

    def run_backup(self, backup_type="FULL", size=2048.0, delete_alternative=False):
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
                                                     additional_content, size//1024, file_size=file_size)
        else:
            new_target=""
            folders_list = self.client_machine.get_folders_in_path(additional_content)
            self.log.info(folders_list)
            if folders_list:
                new_target = folders_list[0]
            self.log.info(f"Deleting every alternate file from {new_target}")
            self.optionobj.delete_nth_files_in_directory(self.client_machine, new_target, 3, "delete")

        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run {backup_type} backup with error: {job.delay_reason}")
        self.log.info("Backup job completed.")
        return job

    def validate_space_reclaim(self, space_reclaim_job, with_ocl=False):
        """ Validates the space reclaim job for following:
        1. validate and prune flags set on store (needs to be done immediately after job completion)
        2. orphan chunk phase (with and without)
        3. opType and subOpType for space reclaim job
        4. size difference before and after space reclaim (this is done by checking mmvolume physicalbytesmb)
        5. check AuxCopyMgr logging for all chunks to be processed

        Args:
            space_reclaim_job (Job)  : space reclaim job object

            with_ocl (bool)             : set True to validate job with OCL. [Default: False]
        Raises:
            Exception   :   if validations fail
        """

        self.log.info("VALIDATION: phases for space reclaim job with OCL [%s]", with_ocl)
        query = f"""select count(1)
                from JMAdminJobAttemptStatsTable
                where jobId = {space_reclaim_job.job_id}"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()

        if not result:
            raise Exception(f"VALIDATION FAILED: phases for space reclaim job with OCL [{with_ocl}]"
                            ": no result returned from query")
        self.log.info("RESULT (job attempts): %s", result[0])
        if (with_ocl and int(result[0]) != 3) or (not with_ocl and int(result[0]) != 2):
            raise Exception(f"VALIDATION FAILED: phases for space reclaim job with OCL [{with_ocl}]: Incorrect")
        self.log.info("VALIDATION PASSED: phases ran as expected")

        self.log.info("VALIDATION: job opType, subOpType for space reclamation job")
        query = f"""select opType, subOpType from 
                JMJobStats
                where jobId = {space_reclaim_job.job_id}"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()

        self.log.info("RESULT (opType and subOpType): %s", result)
        if not result:
            raise Exception("VALIDATION FAILED: job opType, subOpType for space reclamation job"
                            ": no result returned from query")

        if (self.tcinputs.get("UseScalable", True)) and (int(result[0]) != 31 or int(result[1]) != 106):
            raise Exception("VALIDATION FAILED: job opType, subOpType for Scalable space reclamation job: Incorrect")
        elif (not self.tcinputs.get("UseScalable", True)) and (int(result[0]) != 31 or int(result[1]) != 141):
            raise Exception("VALIDATION FAILED: job opType, subOpType for NonScalable space reclamation job: Incorrect")
        self.log.info("VALIDATION PASSED: job opType, subOpType are set as expected")


        self.log.info("VALIDATION: chunks to process == chunks processed")
        # log line: 40292 9318  08/18 15:06:51 4659230 AuxCopyManager::finish Total chunks to be compacted [4],
        # Total chunks compacted [3], Total chunks with data gain [0] on SIDB StoreID [1817] in DV2 job
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
            #raise Exception("Log string [Total Chunks to be compacted] Not Found")
            self.log.error("Log string [Total Chunks to be compacted] Not Found")


        # compacted chunk -> look for 'Compacted chunk ' logging for defrag job

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
                                                                                 db_user='sqladmin_cv'))
            current_zeroref_count = int(self.dedupehelper.get_zeroref_recs_count(store_id,
                                                                                 db_password=self.sql_password,
                                                                                 db_user='sqladmin_cv'))
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
                                                                            db_user='sqladmin_cv'))
        while zeroref_count <= latest_zeroref_count and count < 15:
            count += 1
            time.sleep(60)
            self.log.info("zeroref count before phase3 [%s], latest zeroref count[%s]", zeroref_count,
                          latest_zeroref_count)
            latest_zeroref_count = int(self.dedupehelper.get_zeroref_recs_count(store_id,
                                                                                db_password=self.sql_password,
                                                                                db_user='sqladmin_cv'))
        if zeroref_count > latest_zeroref_count:
            self.log.info("Phase 3 pruning started...")
            return True
        self.log.error("timeout reached, Phase 3 pruning did not start")
        return False

    def run_ddb_recon(self, store):
        """Marks all partition of the store for recovery and run a full recon job

        Args:
            store (Store):  object of the store on which full recon needs to be run
        Returns:
            (Job) : job object of the recon job
        """
        store.refresh()
        self.log.info('Wait for SIDB Process to go down on the DDB MA')
        if not self.dedupehelper.wait_till_sidb_down(store.store_id, self.media_agent_machine.client_object):
            self.log.error('Error waiting for SIDB Process to Go Down')
        substores = store.all_substores
        for substore in substores:
            substore_obj = store.get(substore[0])
            self.log.info(f"marking store[{substore_obj.store_id}] substore[{substore_obj.substore_id}] for recovery")
            substore_obj.mark_for_recovery()

        self.log.info("running Full Recon job...")
        recon_job = store.recover_deduplication_database(full_reconstruction=True)
        self.log.info(f"Full Recon job [{recon_job.job_id}]")
        if not recon_job.wait_for_completion():
            raise Exception(f"Full recon failed with error: {recon_job.delay_reason}")
        self.log.info("Full recon job completed.")
        return recon_job

    def mmvolume_get_physical_size(self, volume_list):
        """Get the sum of physical size mb from MMVolume table for volumes list

        Args:
            volume_list (list) : list of volumes to wait for size update
        Returns:
             (int)  :   total size of all the volumes from MMVolume table
        """
        self.log.info("getting physical size from MMVolume for volume %s...", volume_list)
        query = f"""select sum(PhysicalBytesMB) from MMVolume
                where volumeId in ({','.join(volume_list)})"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("RESULT (total physical size): %s", result[0])
        if not result[0]:
            return 0
        return int(result[0])

    def wait_for_volume_size_update(self, volume_list):
        """Wait for volume size update to happen if not already done with a timeout of 30 mins

        Args:
            volume_list (list) : list of volumes to wait for size update
        Returns:
             (bool) :   True is volume size update time is set to -1, False if timeout
        """
        flag = count = 0
        self.log.info("checking if volume size update time is set to -1 for volumes %s...", volume_list)
        query = f"""select RMSpareStatusUpdateTime, volumeId
                from MMVolume
                where volumeId in ({','.join(volume_list)})"""
        self.log.info("QUERY: %s", query)
        while count < 30:
            self.csdb.execute(query)
            result = self.csdb.fetch_all_rows()
            self.log.info("RESULT: %s", result)
            for value in result:
                if int(value[0]) > -1:
                    flag = 1
            if flag:
                time.sleep(60)
                count += 1
                flag = 0
            else:
                return True
        self.log.error("timeout reached while waiting for volume size update!")
        return False

    def reduce_volume_size_update_time(self, volume_list, days=1):
        """Reduces RMSpareStatusUpdate time from MMVolume with days of time

        Args:
            volume_list(list)   : list of volumes on which size update time needs to be reduced
            days(int)           : number of days to reduce the time. default is 1 day
        """
        self.log.info("reducing RMSpareStatusUpdate time with %s days", days)
        query = f"""update MMVolume
                set RMSpareStatusUpdateTime = 10000
                where VolumeId in ({','.join(volume_list)})"""
        self.log.info("QUERY: %s", query)
        self.mmhelper.execute_update_query(query, db_password=self.sql_password, db_user='sqladmin_cv')

    def get_volumes_for_job(self, job_list, copy_id):
        """Get the all volumes from MMVolume table for the given jobs
        Args:
            job_list    - list of job ids to get associated volumes
            copy_id     - copy id on which the jobs reside

        Returns:
             list    - all the volumes from MMVolume table
        """
        self.log.info("getting physical size from MMVolume for jobs %s...", tuple(job_list))
        query = f"""select distinct V.volumeId
                from archChunkMapping ACM, archChunk AC, MMVolume V
                where ACM.jobId in ({','.join(job_list)})
                    and ACM.archCopyId = {copy_id}
                    and ACM.archChunkId = AC.id
                    and AC.volumeId = V.VolumeId"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info("RESULT (volumes): %s", result)
        if not result:
            return 0
        result_list = []
        for val in result:
            result_list.append(val[0])
        return result_list

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()
            store = self.get_active_files_store()
            base_pruned = 0
            for case in range(2):
                backup_job_list = []
                if case % 2 == 0:
                    self.log.info("*** space reclaim with OCL case %s ***", case+1)
                    with_ocl = True
                else:
                    self.log.info("*** space reclaim without OCL case %s ***", case+1)
                    with_ocl = False
                job1 = self.run_backup()
                backup_job_list.append(job1.job_id)
                job2 = self.run_backup(delete_alternative=True)
                backup_job_list.append(job2.job_id)
                self.log.info("Deleting 1st Backup [%s]", job1.job_id)
                self.primary_copy.delete_job(job1.job_id)
                output = self.dedupehelper.validate_pruning_phase(store.store_id, self.tcinputs['MediaAgentName'])
                if output:
                    base_pruned = len(output)
                self.log.info(f"Number of phase 3 pruning log lines at the beginning = {base_pruned}")
                phase_3_started = False
                da_job = self.mmhelper.submit_data_aging_job(storage_policy_name=self.storage_policy_name,
                                                             copy_name='primary')
                if not da_job.wait_for_completion():
                    raise Exception(f"Failed to run Data Aging (Job Id: {da_job.job_id})"
                                f"with error: {da_job.delay_reason}")

                for attempt in range(1, 10):
                    self.log.info(f"Checking for Phase 3 complete - Attempt {attempt}")
                    output = self.dedupehelper.validate_pruning_phase(store.store_id, self.tcinputs['MediaAgentName'])
                    if not output or len(output) <= base_pruned:
                        self.log.info("Phase 3 pruning is not complete yet. Checking again after 4 minutes")
                        time.sleep(240)
                    else:
                        self.log.info(output)
                        base_pruned = len(output)
                        self.log.info(f"Modifying number of phase 3 pruning log lines to = {base_pruned}")
                        phase_3_started = True
                        self.log.info("Phase 3 pruning is complete. Moving ahead.")
                        break
                if not phase_3_started:
                   self.log.error("Phase 3 pruning is not complete even after timeout of 40 minutes.")
                   raise Exception("Phase 3 pruning is not complete even after timeout of 40 minutes.")

                if with_ocl:
                    job3 = self.run_backup()
                    self.log.info("Deleting 3rd Backup [%s]", job3.job_id)
                    self.primary_copy.delete_job(job3.job_id)
                    phase_2_started = False
                    for attempt in range(1, 20):
                        self.log.info(f"Checking for Phase 2 complete - Attempt {attempt}")
                        output = self.dedupehelper.validate_pruning_phase(store.store_id, self.tcinputs['MediaAgentName'],
                                                                          phase=2)
                        if not output:
                            self.log.info("Phase 2 pruning is not complete yet. Checking again after 2 minutes")
                            time.sleep(120)
                        else:
                            self.log.info(output)
                            phase_2_started = True
                            self.log.info("Phase 2 pruning is complete. Moving ahead.")
                            break
                    if not phase_2_started:
                        raise Exception("Phase 2 pruning did not happen even after timeout of 40 minutes")
                    self.run_ddb_recon(store)

                volume_list = self.get_volumes_for_job(backup_job_list, self.primary_copy.copy_id)
                # reduce volume size update time and wait for size update
                self.reduce_volume_size_update_time(volume_list)
                if self.wait_for_volume_size_update(volume_list):
                    physical_size_before = self.mmvolume_get_physical_size(volume_list)
                else:
                    self.log.error("fail - to get volume size before defrag")
                    raise Exception("fail - to get volume size before defrag")
                store.refresh()

                self.log.info("Running Space Reclamation Job")
                space_reclaim_job = store.run_space_reclaimation(
                    clean_orphan_data=with_ocl,
                    use_scalable_resource=self.tcinputs.get("UseScalable", True))
                if not space_reclaim_job.wait_for_completion():
                    raise Exception(f"Failed to run DDB Space reclaim(Job Id: {space_reclaim_job.job_id})"
                                    f"with error: {space_reclaim_job.delay_reason}")
                self.log.info("Space Reclamation Job(Id: %s) completed", space_reclaim_job.job_id)
                self.validate_space_reclaim(space_reclaim_job, with_ocl=with_ocl)

                query_get_total_space_reclaimed = f"""
SELECT uncompBytes
FROM JMAdminJobStatsTable WITH (NOLOCK)
WHERE jobId = {space_reclaim_job.job_id}"""
                self.log.info(f"Executing query: {query_get_total_space_reclaimed}")
                total_space_reclaimed_bytes = self.mmhelper.execute_select_query(query_get_total_space_reclaimed)
                self.log.info(f"Query result: {total_space_reclaimed_bytes}")
                total_space_reclaimed_mb = int(total_space_reclaimed_bytes[0][0]) / (1024 * 1024)
                self.log.info(f"Total Space Reclaimed value reported: {total_space_reclaimed_mb} MB")

                # reduce volume size update time and wait for size update
                self.reduce_volume_size_update_time(volume_list)
                if self.wait_for_volume_size_update(volume_list):
                    physical_size_after = self.mmvolume_get_physical_size(volume_list)
                    self.log.info("VALIDATION: volume size before defrag [%s] > volume size after defrag [%s]",
                                  physical_size_before, physical_size_after)
                    if physical_size_before > physical_size_after:
                        self.log.info("PASS - volumes size reduced post defrag")

                        self.log.info(f"Size of volume reduced by: {physical_size_before - physical_size_after} MB")
                        self.log.info(f"Total Space Reclaimed value reported: {total_space_reclaimed_mb} MB")

                        diff = abs(total_space_reclaimed_mb - (physical_size_before - physical_size_after))
                        percent_diff = diff * 100 / total_space_reclaimed_mb
                        self.log.info(f"mmvolume physical size vs space reclaimed value reported = {percent_diff}%")
                        if percent_diff > 25:
                            self.log.error("mmvolume physical size vs space reclaimed value reported => 25%")
                            raise Exception("mmvolume physical size vs space reclaimed value reported => 25%")
                        else:
                            self.log.info("mmvolume physical size vs space reclaimed value reported =< 25%")

                    else:
                        raise Exception("FAIL - volume size is not reduced post defrag")
                else:
                    raise Exception("volume size update wait timed out!")

                self.log.info("run DV2 to make sure all good after space reclaim job")
                dv2_job = store.run_ddb_verification(False, False, self.tcinputs.get("UseScalable", True))
                if not dv2_job.wait_for_completion():
                    raise Exception(f"Failed to run DV2(Job Id: {dv2_job.job_id}) with error: {dv2_job.delay_reason}")
                self.log.info("DV2 Job(Id: %s) completed", dv2_job.job_id)

                bad_chunks = self.mmhelper.get_bad_chunks(job_id=dv2_job.job_id, log_chunks=True)
                if bad_chunks:
                    raise Exception(f"bad chunks found by DV2 job [{dv2_job.job_id}]")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        try:
            self.log.info('Performing unconditional cleanup')
            self.cleanup()
        except Exception as ex:
            self.log.warning(f'Cleanup FAILED - {ex}')
