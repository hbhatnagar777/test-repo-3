# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    cleanup()       --  cleans up the entities

    initial_setup() --  initial setting up of library, storage pools, storage policy, subclient

    validate_pick_data_from_running_backup_jobs()   --  Validates whether chunk level auxcopy is working as expected

    validate_pick_new_data_for_sra_auxcopy()        --  Validates whether auxcopy is picking new backup data
                                                        written after it is launched

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case


TcInputs to be passed in JSON File:
    "65547": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "PrimaryCopyMediaAgent": Name of a MediaAgent - we create Library for Primary Copies here
        "SecondaryCopyMediaAgent": Name of a MediaAgent - we create Library for Secondary Copies here
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "library_name"  : Name of Existing Library to be Used
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
        "copy_library_name"  : Name of Existing Library to be Used
        "copy_mount_path"    : Path to be used as MP for Library
        "copy_dedup_path"    : Path to be used for creating Dedupe-Partitions
    }

Steps:

1. Configure Environment: Storage Policy 2 Dedupe Copies, Backupset, Subclient.
2. Set pick data from running jobs on secondary copy and turn off SpaceOptimization, pick new data for auxcopy jobs
3. Run Backup(s) to the Primary Copy
4. Run a Larger Backup and then start auxcopy copy picks up the data from running job --> archchunktoreplicate chunkids
5. wait for backup and aux jobs to complete
6. turn off pick data from running jobs and turn on pick new data for auxcopy jobs
7. Set the network throughput throttle and start auxcopy and run a new small backup which completes quickly.
8. after 20 mins aux should pick data from new backup job. --> archchunktoreplicate chunkids
9. wait for auxcopy job to complete
10. CleanUp the Environment

"""
import time
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = 'AuxCopy - Chunk level copy and pick new data'
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
        self.ma_1_name = None
        self.ma_2_name = None
        self.client_name = None
        self.utility = None
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ma_1_path = None
        self.ma_2_path = None
        self.client_path = None
        self.ddb_1_path = None
        self.ddb_2_path = None
        self.content_path = None
        self.mount_path_1 = None
        self.mount_path_2 = None
        self.copy_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_pool_1_name = None
        self.storage_pool_2_name = None
        self.storage_policy_name = None
        self.storage_pool_1 = None
        self.storage_pool_2 = None
        self.subclient = None
        self.primary_copy = None
        self.secondary_copy = None
        self.storage_policy = None

        self.backup_jobs = []
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_copy_mp = False
        self.is_user_defined_copy_dedup = False
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        self.client_name = self.tcinputs.get('ClientName')
        self.ma_1_name = self.tcinputs.get('PrimaryCopyMediaAgent')
        self.ma_2_name = self.tcinputs.get('SecondaryCopyMediaAgent')

        self.utility = OptionsSelector(self.commcell)
        self.ma_machine_1 = Machine(self.ma_1_name, self.commcell)
        self.ma_machine_2 = Machine(self.ma_2_name, self.commcell)
        self.client_machine = Machine(self.client_name, self.commcell)

        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('copy_mount_path'):
            self.is_user_defined_copy_mp = True
        if self.tcinputs.get('copy_dedup_path'):
            self.is_user_defined_copy_dedup = True

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.ma_machine_1, 25*1024)
            self.ma_1_path = self.ma_machine_1.join_path(ma_1_drive, f'test_{self.id}')
        if not self.is_user_defined_copy_mp or not self.is_user_defined_copy_dedup:
            ma_2_drive = self.utility.get_drive(self.ma_machine_2, 25*1024)
            self.ma_2_path = self.ma_machine_2.join_path(ma_2_drive, f'test_{self.id}')

        client_drive = self.utility.get_drive(self.client_machine, 25*1024)
        self.client_path = self.client_machine.join_path(client_drive, f'test_{self.id}')
        self.content_path = self.client_machine.join_path(self.client_path, 'Content')

        self.subclient_name = f'{self.id}_SC'
        self.backupset_name = f'{self.id}_BS_{self.ma_1_name}'
        self.storage_pool_1_name = f'{self.id}_Src_Pool_{self.ma_1_name}'
        self.storage_pool_2_name = f'{self.id}_Dest_Pool_{self.ma_1_name}'
        self.storage_policy_name = f'{self.id}_SP_{self.ma_1_name}'
        self.copy_name = f'{self.id}_Copy'

        if not self.is_user_defined_mp:
            self.mount_path_1 = self.ma_machine_1.join_path(self.ma_1_path, 'MP1')
        else:
            self.log.info("custom mount_path supplied: %s", self.tcinputs.get('mount_path'))
            self.mount_path_1 = self.ma_machine_1.join_path(
                self.tcinputs.get('mount_path'), f'test_{self.id}', 'MP1')

        if not self.is_user_defined_mp:
            self.mount_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'MP2')
        else:
            self.log.info("custom copy mount_path supplied: %s", self.tcinputs.get('mount_path'))
            self.mount_path_2 = self.ma_machine_2.join_path(
                self.tcinputs.get('mount_path'), f'test_{self.id}', 'MP2')

        if self.is_user_defined_dedup:
            self.ddb_1_path = self.tcinputs.get("dedup_path")
            self.log.info("custom dedup path supplied: %s", self.ddb_1_path)
        else:
            if "unix" in self.ma_machine_1.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_1_path = self.ma_machine_1.join_path(self.ma_1_path, "DDBs")

        if self.is_user_defined_copy_dedup:
            self.ddb_2_path = self.tcinputs.get("copy_dedup_path")
            self.log.info("custom copy dedup path supplied: %s", self.ddb_2_path)
        else:
            if "unix" in self.ma_machine_2.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_2_path = self.ma_machine_2.join_path(self.ma_2_path, "CopyDDBs")

        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def cleanup(self):
        """CleansUp the Entities"""
        self.log.info('************************ Clean Up Started *********************************')
        try:
            self.log.info('Deleting BackupSet if exists')
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            self.log.info('Deleting Storage Policies if exists')
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.get(self.storage_policy_name).reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)

            self.log.info('Deleting Storage Pools if exists')
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_1_name):
                self.commcell.storage_pools.delete(self.storage_pool_1_name)
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_2_name):
                self.commcell.storage_pools.delete(self.storage_pool_2_name)
        except Exception as exe:
            self.log.warning('CleanUp Failed: ERROR: %s', str(exe))

    def initial_setup(self):
        """Initial setting Up of Storage Pool, Storage policies, SubClients"""

        self.log.info("Configuring source and destination storage pools")
        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_1_name):
            part1_path = self.ma_machine_1.join_path(self.ddb_1_path, 'part1')
            part2_path = self.ma_machine_1.join_path(self.ddb_1_path, 'part2')
            if not self.ma_machine_1.check_directory_exists(part1_path):
                self.ma_machine_1.create_directory(part1_path)
            if not self.ma_machine_1.check_directory_exists(part2_path):
                self.ma_machine_1.create_directory(part2_path)
            self.storage_pool_1 = self.commcell.storage_pools.add(self.storage_pool_1_name, self.mount_path_1,
                                                                  self.ma_1_name, self.ma_1_name, part1_path)
            engine = self.commcell.deduplication_engines.get(
                self.storage_pool_1.global_policy_name, self.storage_pool_1.copy_name)
            engine.get(engine.all_stores[0][0]).add_partition(part2_path, self.ma_1_name)
        else:
            self.storage_pool_1 = self.commcell.storage_pools.get(self.storage_pool_1_name)
        self.log.info(f'Storage Pool: {self.storage_pool_1_name} configured')

        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_2_name):
            part1_path = self.ma_machine_2.join_path(self.ddb_2_path, 'part1')
            part2_path = self.ma_machine_2.join_path(self.ddb_2_path, 'part2')
            if not self.ma_machine_2.check_directory_exists(part1_path):
                self.ma_machine_2.create_directory(part1_path)
            if not self.ma_machine_2.check_directory_exists(part2_path):
                self.ma_machine_2.create_directory(part2_path)
            self.storage_pool_2 = self.commcell.storage_pools.add(self.storage_pool_2_name, self.mount_path_2,
                                                                  self.ma_2_name, self.ma_2_name, part1_path)
            engine = self.commcell.deduplication_engines.get(
                self.storage_pool_2.global_policy_name, self.storage_pool_2.copy_name)
            engine.get(engine.all_stores[0][0]).add_partition(part2_path, self.ma_2_name)
        else:
            self.storage_pool_2 = self.commcell.storage_pools.get(self.storage_pool_2_name)
        self.log.info(f'Storage Pool: {self.storage_pool_2_name} configured')

        self.storage_policy = self.dedupe_helper.configure_dedupe_storage_policy(
            self.storage_policy_name,
            storage_pool_name=self.storage_pool_1_name, is_dedup_storage_pool=True)
        self.primary_copy = self.storage_policy.get_copy('Primary')

        self.storage_policy.create_secondary_copy(self.copy_name, global_policy=self.storage_pool_2_name)
        self.secondary_copy = self.storage_policy.get_copy(self.copy_name)
        self.log.info("Disable Space Optimization, remove System Created AutoCopy Schedule association and"
                      " disable mmconfig to Copy first full for new SubClient")
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.copy_name)
        self.secondary_copy.space_optimized_auxillary_copy = False
        self.mm_helper.update_mmconfig_param('MMCONFIG_AUXCOPY_COPY_FIRST_FULL_FOR_NEW_SUBCLIENT', 0, 0)

        self.log.info('Setting the max Chunk Size on Copies to 100 MB')
        query = f'''update mdp
                set	ChunkSizeMB = 100
                from MMDataPath mdp
                    inner join archGroupCopy agc on mdp.CopyId = agc.id
                where	agc.archGroupId in ({self.storage_policy.storage_policy_id},
                        {self.storage_pool_1.storage_pool_id},{self.storage_pool_2.storage_pool_id})'''
        self.utility.update_commserve_db(query)

        self.mm_helper.configure_backupset(self.backupset_name)
        self.subclient = self.mm_helper.configure_subclient(self.backupset_name, self.subclient_name,
                                                            self.storage_policy_name, self.content_path)
        self.log.info("Setting number of streams to 1")
        self.subclient.data_readers = 1

        self.log.info("Running 5 Full Backups to the SubClient")
        self.backup_jobs = []
        for index in range(5):
            self.utility.create_uncompressable_data(self.client_machine,
                                                    self.client_machine.join_path(self.content_path, f'Data'),
                                                    size=1, num_of_folders=1, delete_existing=True)
            job = self.subclient.backup('Full')
            self.log.info("Job %s(Id:%s) started. Waiting for completion", index+1, job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    f"Backup job {job.job_id} didn't complete. status: {job.status}, JPR: {job.delay_reason}")
            time.sleep(10)
            self.log.info("Job %s completed", job.job_id)
            self.backup_jobs.append(job.job_id)

    def validate_pick_data_from_running_backup_jobs(self):
        """
        Validates whether chunk level auxcopy is working as expected
        Returns:
            bool - (True/False) whether the validation passed or failed respectively
        """
        self.log.info(
            "******** TEST VALIDATION 1: Copy Property - Pick Data from running backups (Chunk Level AuxCopy) ********")
        query = f'''update archGroupCopy
                set extendedFlags = extendedFlags|32768
                where id = {self.secondary_copy.copy_id}'''
        self.log.info("Enabling Pick Data from running Backups on Secondary Copy.")
        self.utility.update_commserve_db(query)
        self.log.info("Disabling MMConfigs to pick new data for SRA AuxCopy job")
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_AUXCOPY_PICK_NEW_BACKUP_DATA', 0, 0)

        self.utility.create_uncompressable_data(self.client_machine,
                                                self.client_machine.join_path(self.content_path, f'Data'),
                                                size=5, num_of_folders=1, delete_existing=True)

        self.log.info("Start Backup and wait for it to write multiple chunks before launching AuxCopy")
        backup_job = self.subclient.backup('Full')
        self.log.info("Backup Job (Id:%s) started. Waiting for multiple chunks to be written", backup_job.job_id)
        wait_time, timeout = 0, 600
        backup_chunks = []
        while wait_time < timeout:
            result = self.mm_helper.get_chunks_for_job(
                backup_job.job_id, copy_id=self.primary_copy.copy_id, log_query=True)
            if len(result) > 2:
                backup_chunks = [int(chunk[3]) for chunk in result]
                break
            wait_time += 2
            time.sleep(2)
        if wait_time > timeout:
            raise Exception("Timeout waiting for Backup to write multiple chunks")
        self.log.info('Backup wrote multiple chunks. Starting AuxCopy immediately')

        auxcopy_job = self.storage_policy.run_aux_copy()
        self.log.info("AuxCopy Job (Id:%s) started. Waiting for populating chunks for copy", auxcopy_job.job_id)
        wait_time, timeout = 0, 600
        query = f'''select ArchChunkId from ArchChunkToReplicate where AdminJobId = {auxcopy_job.job_id}
                union
                select ArchChunkId from ArchChunkToReplicateHistory where AdminJobId = {auxcopy_job.job_id}'''
        self.log.info("Query: %s", query)
        populated_chunks = []
        while wait_time < timeout:
            time.sleep(30)
            wait_time += 30
            self.csdb.execute(query)
            result = self.csdb.fetch_all_rows()
            self.log.info("Result - Populated chunks: %s", str(result))
            if len(result) > 2:
                populated_chunks = [int(chunk[0]) for chunk in result]
                break
        if wait_time > timeout:
            raise Exception("Timeout waiting for AuxCopy to write populate chunks")

        if backup_job.is_finished:
            raise Exception(
                f"Backup Job {backup_job.job_id} completed before AuxCopy Job {auxcopy_job.job_id} populated Data."
                f" So Chunk level auxcopy validation would be invalid")
        else:
            self.log.info("Backup Job is still running. So proceeding with validation")

        self.log.info("*** Validation: Check if any chunks of running jobs are populated for AuxCopy ***")
        validation = False
        for chunk in backup_chunks:
            if chunk in populated_chunks:
                self.log.info("Result - Pass : Chunk %s from running Backup is populated for AuxCopy", chunk)
                validation = True
        if not validation:
            self.log.error("Result - Fail : No Chunks from running Backup are populated for AuxCopy")

        self.log.info("Waiting for backup, aux jobs to complete")
        if not auxcopy_job.wait_for_completion():
            raise Exception(
                f"AuxCopy job {auxcopy_job.job_id} failed with JPR: {auxcopy_job.delay_reason}")
        self.log.info("AuxCopy Job %s completed", auxcopy_job.job_id)
        if not backup_job.wait_for_completion():
            raise Exception(
                f"Backup job {backup_job.job_id} failed with JPR: {backup_job.delay_reason}")
        self.log.info("Backup Job %s completed", backup_job.job_id)
        self.backup_jobs.append(backup_job.job_id)

        return validation

    def validate_pick_new_data_for_sra_auxcopy(self):
        """
        Validates whether auxcopy is picking new backup data written after it is launched
        Returns:
            bool - (True/False) whether the validation passed or failed respectively
        """
        self.log.info("*** Test Validation 2: MM Config - Pick new data for SRA AuxCopy Job")
        self.log.info("Setting MMConfigs to pick new data and minimum interval for new data population to 10 mins")
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_AUXCOPY_PICK_NEW_BACKUP_DATA', 0, 1)
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_AUXCOPY_CHUNK_POPULATE_INTERVAL_MINS', 5, 10)

        query = f'''update archGroupCopy
                set extendedFlags = extendedFlags&~32768
                where id = {self.secondary_copy.copy_id}'''
        self.log.info("Disabling Pick Data from running Backups on Secondary Copy.")
        self.utility.update_commserve_db(query)
        self.log.info('Seal store, Pick Jobs for recopy and set network throttle bandwidth on Secondary Copy')
        engine = self.commcell.deduplication_engines.get(
            self.storage_pool_2.global_policy_name, self.storage_pool_2.copy_name)
        store = engine.get(engine.all_stores[0][0])
        store.seal_deduplication_database()
        self.secondary_copy.recopy_jobs(self.backup_jobs)
        self.secondary_copy.network_throttle_bandwidth = 10000

        self.utility.create_uncompressable_data(self.client_machine,
                                                self.client_machine.join_path(self.content_path, f'Data'),
                                                size=0.2, num_of_folders=1, delete_existing=True)
        auxcopy_job = self.storage_policy.run_aux_copy(streams=1)
        self.log.info("AuxCopy Job (Id:%s) started. Sleeping for 30 seconds before starting backup", auxcopy_job.job_id)
        self.log.info("We will check for data population after 20 mins. Backup job should be completed by that time")

        time.sleep(30)
        start_time = int(time.time())
        backup_job = self.subclient.backup('Full')
        self.log.info("Backup Job (Id:%s) started. Waiting 10 mins for completion", backup_job.job_id)
        if not backup_job.wait_for_completion(timeout=10):
            raise Exception(
                f"Backup job {backup_job.job_id} failed with JPR: {backup_job.delay_reason}")
        self.log.info("Backup Job %s completed. Sleeping the remaining time left in 20 min interval.", backup_job.job_id)
        end_time = int(time.time())
        time.sleep(1200-(end_time-start_time))

        self.log.info('Fetching chunks populated by AuxCopy Job and chunks written by new Backup job')
        query = f'''select ArchChunkId from ArchChunkToReplicate where AdminJobId = {auxcopy_job.job_id}
                union
                select ArchChunkId from ArchChunkToReplicateHistory where AdminJobId = {auxcopy_job.job_id}'''
        self.log.info("Query for AuxCopy Populated Chunks: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info("Result - Populated chunks: %s", str(result))
        populated_chunks = [int(chunk[0]) for chunk in result]
        result = self.mm_helper.get_chunks_for_job(
            backup_job.job_id, copy_id=self.primary_copy.copy_id, log_query=True)
        backup_chunks = [int(chunk[3]) for chunk in result]

        self.log.info("*** Validation: Check if chunks of new backup job are populated for AuxCopy ***")
        validation = False
        for chunk in backup_chunks:
            if chunk in populated_chunks:
                self.log.info("Result - Pass : Chunk %s from new Backup is populated for AuxCopy", chunk)
                validation = True
        if not validation:
            self.log.error("Result - Fail : No Chunks from new Backup are populated for AuxCopy")

        self.log.info("Waiting for AuxCopy job to complete")
        if not auxcopy_job.wait_for_completion():
            raise Exception(
                f"Backup job {auxcopy_job.job_id} failed with JPR: {auxcopy_job.delay_reason}")
        self.log.info("AuxCopy Job %s completed", auxcopy_job.job_id)

        return validation

    def run(self):
        """Run Function of this case"""
        self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
        self.cleanup()
        try:
            self.initial_setup()
            failures = []
            if not self.validate_pick_data_from_running_backup_jobs():
                failures.append("Chunk level auxcopy validation failed")
            if not self.validate_pick_new_data_for_sra_auxcopy():
                failures.append("Pick new data for auxcopy validation failed")
            if failures:
                raise Exception(str(failures))
            self.log.info("*** All validations in the test case completed ***")
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('EXCEPTION Occurred : %s', str(exe))

    def tear_down(self):
        """Tear Down Function of this case"""
        self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED. Cleaning Up the Entities')
        else:
            self.log.warning('Test Case FAILED. Please review the TC and Commcell logs. Cleaning Up the Entities')
        self.cleanup()
