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

    remove_drillhole_flag() -- removes mount path with drill hole flag if set

    update_mmpruneprocess() -- updates MMPruneProcessInterval to 10 mins or reverts to noted time

    get_active_files_store() -- gets active files DDB store id

    cleanup()   --  cleanups all created entities

    run_backup()    -- runs backup need for the case

    run_data_aging()    -- runs data aging job for storage policy copy created by case

    run_dv2_job()       -- runs DV2 job with options provided

    run_space_reclaim_job()   -- runs space reclaim job with validation of validate and prune

    create_orphan_chunk()   -- created a dummy orphan chunk for store id

    validate_space_reclaim() -- validates the DDB space reclaim job

Note:
    1. will be considering MP and DDB path if provided for configurations
    2. Make sure "Ransomware protection" is disabled on MA properties and service restart before running the case

Sample JSON: values under [] are optional
"58327": {
            "ClientName": "client name",
            "AgentName": "File System",
            "MediaAgentName": "ma name",
            "SqlSaPassword": "sql password",
            ["DDBPath": "/ddb/58327/ddb",
            "MountPath": "/data/58327/lib",
            "ContentPath": "/data/58327/content",
            "ScaleFactor": "5"]
        }

design:
    add disable drillhole key on MA
    add regkey to 0% fragment consideration
    create library with provided mp path or self search path
    disable flag from MP for drillhole

    add dedupe sp with provided DDB path or self search path
    disable garbage collection on dedupe store

    generate content considering scale factor ture or fals
    Run job with 100 files - J1
    Delete alternate files in content
    Run job with alternate 50 files - J2

    Delete J1
    Run aging and wait for physical pruning
    wait for phase 2 & 3 pruning to happen
    add a dummy orphan chunk

    run space reclaim with OCL enabled (level 4)
        verify orphan chunk is pruned
        verify 3 phases overall
        verify store is set with validate and prune flags

    generate content considering scale factor ture or fals
    Run job with 100 files - J1
    Delete alternate files in content
    Run job with alternate 50 files - J2

    Delete J1
    Run aging and wait for physical pruning
    wait for phase 2 & 3 pruning to happen
    add a dummy orphan chunk

    run space reclaim with ocl disabled (level 4)
        verify compacted chunks
        verify orphan dummy chunk is not pruned
        verify 2 phases overall
        verify store is set with validate and prune flags
"""
import time
from cvpysdk import deduplication_engines
from AutomationUtils import constants
from AutomationUtils import cvhelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from MediaAgents.MAUtils.mahelper import DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Simplify DV2 project - Space reclaim job case"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.mount_path = None
        self.ddb_path = None
        self.scale_factor = None
        self.mmhelper = None
        self.dedupehelper = None
        self.client_machine = None
        self.library = None
        self.storage_policy = None
        self.backupset = None
        self.subclient = None
        self.drillhole_key_added = True
        self.mmpruneprocess_value = None
        self.primary_copy = None
        self.media_agent_machine = None
        self.orphan_chunks_folder = None
        self.orphan_chunks_file = None
        self.sql_password = None
        self.ma_client = None
        self.sidb_id = None
        self.store_obj = None

    def setup(self):
        """ Setup function of this test case. """
        self.content_path = self.tcinputs.get('ContentPath')
        self.mount_path = self.tcinputs.get('MountPath')
        self.ddb_path = self.tcinputs.get('DDBPath')
        self.scale_factor = self.tcinputs.get('ScaleFactor')
        self.subclient_name = str(self.id) + "_SC"
        self.library_name = str(self.id) + f"_lib_{self.tcinputs.get('MediaAgentName')}"
        self.storage_policy_name = str(self.id) + f"_SP__{self.tcinputs.get('MediaAgentName')}"
        self.backupset_name = str(self.id) + "_BS"
        self.client_machine = Machine(self.tcinputs['ClientName'], self.commcell)
        self.media_agent_machine = Machine(self.tcinputs['MediaAgentName'], self.commcell)
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        encrypted_pass = Machine(self.commcell.commserv_client).get_registry_value("Database", "pAccess")
        self.sql_password = cvhelper.format_string(self._commcell, encrypted_pass).split("_cv")[1]
        if self.media_agent_machine.os_info.lower() == 'windows':
            self.log.info('Disabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(False)
            self.log.info("Successfully disabled Ransomware protection on MA")
        self.ma_client = self.commcell.clients.get(self.tcinputs['MediaAgentName'])

    def setup_environment(self):
        """
        configures all entities based tcinputs. if path is provided TC will use this path instead of self selecting
        """
        self.log.info("setting up environment...")

        # select drive on MA for MP and DDB
        op_selector = OptionsSelector(self.commcell)
        media_agent_drive = self.media_agent_machine.join_path(
            op_selector.get_drive(self.media_agent_machine, 25*1024), 'automation', self.id)
        if not self.mount_path:
            self.mount_path = self.media_agent_machine.join_path(media_agent_drive, 'mountpath')
        else:
            self.log.info("will be using user specified path [%s] for mount path configuration", self.mount_path)
        if not self.ddb_path:
            self.ddb_path = self.media_agent_machine.join_path(media_agent_drive, 'DDB')
        else:
            self.log.info("will be using user specified path [%s] for DDB path configuration", self.ddb_path)

        # select drive on client for content and restore
        client_drive = self.client_machine.join_path(
            op_selector.get_drive(self.client_machine, 25*1024), 'automation', self.id)
        if not self.content_path:
            self.content_path = self.client_machine.join_path(client_drive, 'content_path')
        else:
            self.log.info("will be using user specified path [%s] for backup content", self.content_path)

        if not self.media_agent_machine.check_registry_exists('MediaAgent', 'DedupDrillHoles'):
            self.media_agent_machine.create_registry('MediaAgent', value='DedupDrillHoles', data='0', reg_type='DWord')
            self.log.info("added regkey to disable drillholes!")
            self.drillhole_key_added = True
        else:
            self.log.info("drillhole regkey already exists")

        # uncomment below part of the code to make it a fix if fragmentation % is lower than 20
        # if not self.media_agent_machine.check_registry_exists('MediaAgent', 'AuxcopySfileFragPercent'):
        #     self.media_agent_machine.create_registry('MediaAgent', value='AuxcopySfileFragPercent',
        #                                              data='0', reg_type='DWord')
        #     self.log.info("adding sfile fragment percentage to 0!")

        self.library = self.mmhelper.configure_disk_library(self.library_name,
                                                            self.tcinputs["MediaAgentName"],
                                                            self.mount_path)
        self.remove_drillhole_flag(self.library.library_id)

        self.storage_policy = self.dedupehelper.configure_dedupe_storage_policy(self.storage_policy_name,
                                                                                self.library.name,
                                                                                self.tcinputs["MediaAgentName"],
                                                                                self.ddb_path)

        self.log.info("setting primary copy retention to 1 day, 0 cycle")
        self.primary_copy = self.storage_policy.get_copy('Primary')
        self.primary_copy.copy_retention = (1, 0, 1)

        self.log.info("disabling garbage collection to avoid complications in waiting for physical prune")
        store = self.get_active_files_store()
        store.enable_garbage_collection = False

        self.mmhelper.configure_backupset(self.backupset_name, self._agent)

        self.subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                           self.subclient_name,
                                                           self.storage_policy_name,
                                                           self.content_path,
                                                           self._agent)
        self.update_mmpruneprocess()

    def remove_drillhole_flag(self, library_id, revert=False):
        """
        this method will remove drill hole flag for all mount paths of a library

        Args:
             library_id - library id which has all mount paths to disable drill hole
        """
        if not revert:
            self.log.info("removing drill hole flag at mount path level...")
            query = f"""
                    update MMMountPath
                    set Attribute = Attribute & ~128
                    where LibraryId = {library_id}"""
        else:
            self.log.info("reverting drill hole flag at mount path level...")
            query = f"""
                    update MMMountPath
                    set Attribute = Attribute | 128
                    where LibraryId = {library_id}"""
        self.log.info("QUERY: %s", query)
        self.mmhelper.execute_update_query(query, db_password=self.sql_password, db_user='sqladmin_cv')

    def update_mmpruneprocess(self):
        """reduced MMPruneProcess interval to 2mins and reverts back if already set"""
        if not self.mmpruneprocess_value:
            self.log.info("setting MMPruneProcessInterval value to 10")
            query = f"""update MMConfigs set value = 10 where name = 'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS'"""
        else:
            self.log.info("reverting MMPruneProcessInterval value to %s", self.mmpruneprocess_value)
            query = f"""update MMConfigs set value = {self.mmpruneprocess_value}
            where name = 'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS'"""
        self.log.info("QUERY: %s", query)
        self.mmhelper.execute_update_query(query, db_password=self.sql_password, db_user='sqladmin_cv')

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.storage_policy_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def cleanup(self):
        """
        performs cleanup of all entities
        """
        try:
            flag = 0
            self.log.info("cleanup started")
            self.remove_drillhole_flag(self.library.library_id, revert=True)
            additional_content = self.client_machine.join_path(self.content_path, 'generated_content')
            if self.client_machine.check_directory_exists(additional_content):
                self.log.info("deleting additional content...")
                self.client_machine.remove_directory(additional_content)
                flag = 1
            if self._agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("deleting backupset...")
                self._agent.backupsets.delete(self.backupset_name)
                flag = 1
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("deleting storage policy...")
                self.commcell.storage_policies.delete(self.storage_policy_name)
                flag = 1
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.log.info("deleting library...")
                self.commcell.disk_libraries.delete(self.library_name)
                flag = 1

            if not flag:
                self.log.info("no entities found to clean up!")
            else:
                self.log.info("cleanup done.")

        except Exception as exp:
            self.log.warning(f"Something went wrong while cleanup! - {exp}")

    def run_backup(self, backup_type="FULL", size=1.0, delete_alternative=False):
        """
        this function runs backup by generating new content to get unique blocks for dedupe backups.
        if scalefactor in tcinput, creates factor times of backup data

        Args:
            backup_type (str): type of backup to run
                Default - FULL

            size (int): size of backup content to generate
                Default - 1 GB

            delete_alternative (bool): to run a backup by deleting alternate content, set True
                Default - False

        Returns:
        (object) -- returns job object to backup job
        """
        additional_content = self.client_machine.join_path(self.content_path, 'generated_content')
        if not delete_alternative:
            # add content
            if self.client_machine.check_directory_exists(additional_content):
                self.client_machine.remove_directory(additional_content)
            # if scale test param is passed in input json, multiple size factor times and generate content
            if self.scale_factor:
                size = size * int(self.scale_factor)
            # calculate files
            files = (size * 1024 * 1024) / 10240
            self.client_machine.generate_test_data(additional_content, dirs=1, files=int(files), file_size=10240)
        else:
            files_list = self.client_machine.get_files_in_path(additional_content)
            self.log.info("deleting alternate content files...")
            for i, file in enumerate(files_list):
                if i & 2 == 0:
                    self.client_machine.delete_file(file)
        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(backup_type, job.delay_reason)
            )
        self.log.info("Backup job completed.")
        return job

    def run_data_aging(self):
        """
        runs data aging job for a given storage policy, copy.
        """
        da_job = self.commcell.run_data_aging(copy_name='Primary',
                                              storage_policy_name=self.storage_policy_name,
                                              is_granular=True,
                                              include_all_clients=True)

        self.log.info("data aging job: %s", da_job.job_id)
        if not da_job.wait_for_completion():
            raise Exception(f"Failed to run data aging with error: {da_job.delay_reason}")
        self.log.info("Data aging job completed.")

    def run_dv2_job(self, store, dv2_type, option):
        """
        Runs DV2 job with type and option selected and waits for job to complete

        Args:
            store (object) - object of the store to run DV2 job on

            dv2_type (str) - specify type either full or incremental

            option (str) - specify option, either quick or complete

        Returns:
             (object) - completed DV2 job object
        """

        self.log.info("running [%s] [%s] DV2 job on store [%s]...", dv2_type, option, store.store_id)
        if dv2_type == 'incremental' and option == 'quick':
            job = store.run_ddb_verification()
        elif dv2_type == 'incremental' and option == 'complete':
            job = store.run_ddb_verification(quick_verification=False)
        elif dv2_type == 'full' and option == 'quick':
            job = store.run_ddb_verification(incremental_verification=False)
        else:
            job = store.run_ddb_verification(incremental_verification=False, quick_verification=False)
        self.log.info("DV2 job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run dv2 job with error: {job.delay_reason}")
        self.log.info("DV2 job completed.")
        return job

    def run_space_reclaim_job(self, store, with_ocl=0):
        """
        runs space reclaim job on the provided store object

        Args:
            store (object) - store object wher espace reclaim job needs to run

            with_ocl (int) - 0 for Defrag+OCL, 1 for only Defrag and 2 for only OCL

        Returns:
            (object) job object for the space reclaim job
        """
        if with_ocl == 0:
            self.log.info("Submitting Space Reclamation job with Defrag=[True] and OCL=[True]")
            space_reclaim_job = store.run_space_reclaimation(level=4, clean_orphan_data=True)
        elif with_ocl == 1:
            self.log.info("Submitting Space Reclamation job with Defrag=[True] and OCL=[False]")
            space_reclaim_job = store.run_space_reclaimation(level=4, clean_orphan_data=False, defragmentation=True)
        else:
            self.log.info("Submitting Space Reclamation job with Defrag=[False] and OCL=[True]")
            space_reclaim_job = store.run_space_reclaimation(level=4, clean_orphan_data=True, defragmentation=False)

        self.log.info(f"Space reclaim job id [{space_reclaim_job.job_id}]")
        # validate resync scheduled immediately on job start
        if not space_reclaim_job.wait_for_completion():
            raise Exception(f"Failed to run DDB Space reclaim with error: {space_reclaim_job.delay_reason}")
        self.log.info("DDB Space reclaim job completed.")
        return space_reclaim_job

    def create_orphan_data(self, store_id):
        """this method creates a dummy dedupe chunk with testcase id

        Args:
            store_id (int)  - store id on which dummy chunks needs to be created"""

        self.log.info("creating orphan data...")

        self.log.info("Generating  unique data of size 1 GB")
        self.mmhelper.create_uncompressable_data(self.client.client_name, self.content_path, 0.1)
        self.log.info("Setting number of Readers on subclient to 1")
        self.subclient.data_readers = 1
        self.log.info("Running 1 backup of size 1 GB")

        job = self.subclient.backup("Incremental")
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run Incremental backup with error: {job.delay_rason}")
        self.log.info("Backup job completed.")
        file_size = 0
        folder_size = 0
        self.log.info("Fetching chunk to be made orphan")
        orphan_chunks_list = []
        chunks_list = self.mmhelper.get_chunks_for_job(job.job_id, order_by = 1)
        os_sep =self.media_agent_machine.os_sep
        chunk_details = chunks_list[0]
        chunk = os_sep.join(chunk_details[0:2])
        chunk = f"{chunk}{os_sep}CV_MAGNETIC{os_sep}{chunk_details[2]}{os_sep}CHUNK_{chunk_details[3]}"
        orphan_chunks_list.append(chunk)
        orphan_data_path =f"{chunk_details[0]}{os_sep}{chunk_details[1]}{os_sep}CV_MAGNETIC{os_sep}{chunk_details[2]}"

        #Sometimes when the commcell is new and doesn't have chunk IDs reaching upto test case ID, this orphan
        #chunk id may not get removed by OCL

        self.orphan_chunks_folder = orphan_chunks_list[-1]
        self.orphan_chunks_file = self.media_agent_machine.join_path(orphan_data_path,
                                                                 f'CHUNKMAP_TRAILER_{chunk_details[-1]}')

        file_size = self.media_agent_machine.get_file_size(self.orphan_chunks_file, size_on_disk=True)
        folder_size = self.media_agent_machine.get_folder_size(self.orphan_chunks_folder, size_on_disk=True)
        self.log.info(f"Orphan Chunk ==> {self.orphan_chunks_folder}")
        self.log.info(f"Orphan Chunks : Total Folder Size => {folder_size} Total File Size = {file_size}")



        self.log.info("Disable Phase 3 pruning on MA by adding additional setting DedupPrunerDisablePhase3 at MediaAgent level")
        self.ma_client.add_additional_setting('MediaAgent', 'DedupPrunerDisablePhase3', 'INTEGER', '1')
        log_lines_before = 0
        matched_lines = self.dedupehelper.validate_pruning_phase(self.sidb_id, self.tcinputs['MediaAgentName'], phase=2)
        if matched_lines:
            log_lines_before = len(matched_lines)
        self.log.info(f"Total number of phase 2 pruning log lines before deleting job = {log_lines_before}")

        self.log.info(f"Deleting job {job.job_id}")
        sp_copy = self.storage_policy.get_copy("primary")
        sp_copy.delete_job(job.job_id)

        self.log.info("Waiting for Phase 2 pruning to complete")

        for i in range(10):
            self.log.info("data aging + sleep for 240 seconds: RUN %s", (i + 1))

            job = self.mmhelper.submit_data_aging_job()

            self.log.info(f"Data Aging job: {job.job_id}")
            if not job.wait_for_completion():
                if job.status.lower() == "completed":
                    self.log.info(f"job {job.job_id} completed")
                else:
                    raise Exception(f"Job {job.job_id} Failed with {job.delay_reason}")
            matched_lines = self.dedupehelper.validate_pruning_phase(self.sidb_id, self.tcinputs['MediaAgentName'], phase=2)

            if matched_lines and len(matched_lines) != log_lines_before:
                self.log.info(matched_lines)
                self.log.info(f"Successfully validated the phase 2 pruning on sidb - {self.sidb_id}")
                pruning_done = True
                break
            else:
                self.log.info(f"Continuing with next attempt")

        self.log.info("Preparing store for Corruption")


        self.log.info("Marking store for corruption after checking that SIDB2 is not running")


        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        if dedup_engines_obj.has_engine(self.storage_policy_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_policy_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])

        self.log.info("Explicitly marking store for recovery")
        if self.dedupehelper.wait_till_sidb_down(str(self.store_obj.store_id), self.ma_client, timeout=600):
            self.log.info("SIDB2 process is not running, can mark the store for recovery")

        else:
            self.log.error("SIDB2 process is still running and can't mark the store for recovery")
            raise Exception("SIDB2 process is still running and can't mark the store for recovery")


        substore_obj = self.store_obj.get(self.store_obj.all_substores[0][0])
        substore_obj.mark_for_recovery()


        self.log.info("Starting Full Reconstruction Job")
        recon_job = self.store_obj.recover_deduplication_database(full_reconstruction=True)
        self.log.info(f"Started DDB Recon job id {recon_job.job_id}")
        if recon_job.wait_for_completion():
            self.log.info(f"Full recon with job id {recon_job.job_id} completed successfully")
        else:
            raise Exception(f"Full recon with job id {recon_job.job_id} failed to complete with JPR {recon_job.delay_reason}")

        self.log.info("Removing additional setting to disable Phase 3")
        self.ma_client.delete_additional_setting('MediaAgent', 'DedupPrunerDisablePhase3')

        self.log.info("Orphan chunks generated successfully.")
        self.log.info("Setting IdxSIDBRecoveryHistory table flags column value to 2 to suppress last Full Recon. "
                      "This will avoid automatic conversion of only Defrag job to  OCL + Defrag")
        query = f"update idxsidbrecoveryhistory set flags=2 where sidbstoreid={self.store_obj.store_id}"
        self.log.info(f"QUERY ==> {query}")
        self.mmhelper.execute_update_query(query, db_password=self.sql_password, db_user='sqladmin_cv')
        self.log.info("Successfully ran the update query")
        return file_size + folder_size

    def validate_space_reclaim(self, space_reclaim_job, with_ocl=0):
        """
        validates the space reclaim job for following:
        1. validate and prune flags set on store (needs to be done immediatly after job completion)
        2. orphan chunk deletion (prune and skip)
        3. orphan chunk phase (with and without)
        4. sub optype for space reclaim job
        5. size difference before and after space reclaim (this is done in main run)

        Args:
            space_reclaim_job (object)        - space reclaim job object

            with_ocl (int)                    - 0 for Defrag+OCL, 1 for only Defrag and 2 for only OCL

        """
        self.log.info("VALIDATION: orphan chunk existance")

        def is_orphan_chunk_exists():
            if self.media_agent_machine.check_file_exists(self.orphan_chunks_file)\
                    and self.media_agent_machine.check_directory_exists(self.orphan_chunks_folder):
                self.log.info("Orphan chunk exists")
                return True
            self.log.info("Orphan chunk is removed")
            return False
        if (with_ocl in (0, 2) and not is_orphan_chunk_exists()) or (with_ocl == 1 and is_orphan_chunk_exists()):
            self.log.info("orphan chunk validation pass")
        else:
            raise Exception("orphan chunk validation failed")

        self.log.info("VALIDATION: phases for space reclaim job with OCL [%s]", with_ocl)
        query = f"select count(1) from JMAdminJobAttemptStatsTable where jobid = {space_reclaim_job.job_id}"
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("RESULT (number of phases): %s", result[0])
        if result and (with_ocl in (0, 2) and int(result[0]) == 3) or ( with_ocl == 1 and int(result[0]) == 2):
            self.log.info(f"Space Reclamation Job ran {result[0]} phases as expected when with_ocl was set to {with_ocl}")
        else:
            raise Exception("Space reclamation job attempts not expected")


        self.log.info("VALIDATION: sub optype for space reclamation job")
        query = f"select opType, subOpType from jmjobstats where jobid = {space_reclaim_job.job_id}"
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("RESULT (optype and suboptype): %s", result)
        if not result:
            raise Exception("no result returned from query")
        if int(result[0]) != 31 and int(result[1]) != 141:
            raise Exception("Space reclaim job optype is not correct")
        self.log.info("Space reclamation job optype is set as expected")



    def run(self):
        """Run function of this test case"""
        try:

            self.cleanup()
            self.setup_environment()

            pruning_line_count = 0
            orphan_chunk_size = 0
            return_list = self.dedupehelper.get_sidb_ids(self.storage_policy.storage_policy_id, "Primary")
            self.sidb_id = int(return_list[0])
            for case in range(3):

                if case % 3 == 0:
                    self.log.info("*** DEFRAG with OCL case ***")
                elif case % 3 == 1:
                    self.log.info("*** DEFRAG without OCL case ***")
                else:
                    self.log.info("*** Only OCL case ***")


                job1 = self.run_backup()
                store = self.get_active_files_store()
                time.sleep(30)
                self.run_backup(delete_alternative=True)
                self.primary_copy.delete_job(job1.job_id)

                for iter in range(3):
                    self.run_data_aging()
                size_before = self.media_agent_machine.get_folder_size(self.mount_path, size_on_disk=True)
                pruning_done = False
                for attempt in range(10):
                    matched_lines = self.dedupehelper.validate_pruning_phase(self.sidb_id,
                                                                              self.tcinputs['MediaAgentName'])
                    if matched_lines and case == 0:
                        pruning_line_count = len(matched_lines)
                        self.log.info(matched_lines)
                        self.log.info(f"Pruning is complete for Case 1 with matched_lines count = {pruning_line_count}")
                        pruning_done = True
                        break
                    elif matched_lines and case == 1:
                        if len(matched_lines) != pruning_line_count:
                            self.log.info(f"Pruning is complete for Case 2 with matched_lines count = {pruning_line_count}")
                            pruning_done = True
                            self.log.info(matched_lines)
                            pruning_line_count = len(matched_lines)
                            break
                    elif matched_lines and case ==2:
                        if len(matched_lines) != pruning_line_count:
                            self.log.info(f"Pruning is complete for Case 2 with matched_lines count = {pruning_line_count}")
                            pruning_done = True
                            self.log.info(matched_lines)
                            break
                    self.log.info(f"Pruning is not complete yet - Attempt - {attempt + 1}")
                    time.sleep(240)

                if pruning_done:
                    self.log.info("Successfully completed pruning.")
                else:
                    self.log.error("Pruning is not complete even after 40 minutes. Raising exception.")
                    raise Exception("Phase 3 pruning did not happen even after 40 minutes.")

                store.refresh()
                if case != 2:
                    self.log.info("Creating Orphan Chunk")
                    orphan_chunk_size = self.create_orphan_data(self.sidb_id)
                else:
                    self.log.info("Not creating Orphan chunk again as already created in previous iteration")

                size_before_space_reclaim = self.media_agent_machine.get_folder_size(self.mount_path,size_on_disk=True)

                space_reclaim_job = self.run_space_reclaim_job(store, case)
                size_after = self.media_agent_machine.get_folder_size(self.mount_path,size_on_disk=True)
                self.validate_space_reclaim(space_reclaim_job, case)
                self.log.info(f"Size Before : {size_before_space_reclaim} | Size After : {size_after}")
                if size_before_space_reclaim > size_after:
                    self.log.info("space reclaim job reduced mount path size from [%s] to [%s]",
                                  size_before_space_reclaim, size_after)
                else:
                    raise Exception(f"""space reclaim job did not reduce mount path size,
                    before[{size_before_space_reclaim}] after[{size_after}]""")
                if case == 2:
                    self.log.info("Check that Defrag job has not defragmented any chunks when only OCL was run")
                    self.log.info(f"Orphan Chunk Size = {orphan_chunk_size}")
                    size_reclaimed = size_before_space_reclaim - size_after
                    #Giving a 20% allowance on top of orphan chunk size
                    if size_reclaimed <= orphan_chunk_size * 1.2:
                        self.log.info(f"Reduced size is same as orphan chunk size")
                    else:
                        self.log.error(f"Reduced size is not same as orphan chunk size")

                self.log.info("run DV2 after 5 mins to make sure all good after space reclaim job")
                time.sleep(300)
                self.run_dv2_job(store, 'full', 'complete')
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if self.mmpruneprocess_value:
                self.update_mmpruneprocess()
            self.log.info("Removing additional setting to disable Phase 3")
            self.ma_client.delete_additional_setting('MediaAgent', 'DedupPrunerDisablePhase3')
            # uncomment below part of the code to make it a fix if fragmentation % is lower than 20
            # self.log.info("removing regkey AuxcopySfileFragPercent...")
            # self.media_agent_machine.remove_registry('MediaAgent', 'AuxcopySfileFragPercent')
            if self.media_agent_machine.os_info.lower() == 'windows':
                self.log.info('Enabling Ransomware protection on MA')
                self.commcell.media_agents.get(
                    self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)
                self.log.info("Successfully enabled Ransomware protection on MA")
            if self.drillhole_key_added:
                self.media_agent_machine.remove_registry('MediaAgent', value='DedupDrillHoles')
                self.log.info("removed regkey to disable drillholes!")
            self.cleanup()
