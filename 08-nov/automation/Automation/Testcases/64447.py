# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase classcd

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    run_backup()    --  runs a backup job by generating new content

    get_active_files_store() -- Returns active store object for files iDA

    update_max_afs_and_extd_flags() -- Method to update ExtendedFlags in idxSIDBStore

    update_extd_flags_for_store() -- Method to update ExtendedFlags in idxSIDBStore

    get_max_afs_and_extd_flags() -- Query CSDB and get MaxNumOfAFsInSecFile and ExtendedFlags values for store

    simulate_and_validate_compaction_process() -- Method to verify that compaction is working as expected

    run_recon_and_validate() -- Mark store for recovery, start full recon and validate primary and sec record count

    compact_ddb()   --  runs sidb compact command for all partitions on store

    clean_test_environment() -- cleans up test environment by deleting associated entities

    configure_tc_environment() -- Configure testcase environment - storage pool, storage policy, backupset, subclient



Steps:
	1. Create resources, DDBs with 3 partitions
	2. Update IdxSIDBSubStore to have MaxNumOfAFsInSecFile=16 and set extendedFlags = 0 in both idxSIDBStore
	    and IdxSIDbSubStore tables
	3. Run  backups
	4. Make sure ddb process is not running
		a. Get DDB MA for the given DDB Store
		b. Wait till SIDB is down
		c. Check extendedFlags and MaxNumOfAFsInSecFiles flags
	5. Compact DDB
		a. Make sure that store is set to 1 AF per secondary after compacting
		b. Run more backups after compaction
		c. Wait 150 secs for IdxSIDBUsageHistory table updates to happen
		d. Note primary and secondary recs count
	6. Check if SIDB is running for DDB ma and partition
	7. Run recon
		a. Mark one of the partition substore for recovery
		b. Start Full recon
		c. Poll ddb reconstruction -> wait for completion
		d. Check no failed attempts in Add records phase
		e. Get primary and sec records count
	8. Validate both are same
    9. Run data aging to minimize space consumption

Input json:

    "64447": {
                    "AgentName": "File System",
                    "ClientName": "client",
                    "MediaAgentName": "Name of Media Agent",
                    "SqlSaPassword": "sql password for sa user",
					"dedup_path" (optional): "path where dedup store to be created"
					"mount_path" (optional): "path where the data is to be stored"
            }
            [for linux MediaAgents, User must explicitly provide a dedup path that is inside a Logical Volume.
             (LVM support required for DDB)]
"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Recon case for compacted DDB with multiple partitions - 16 AF per secondary"
        self.tcinputs = {
            "MediaAgentName": None,
            "SqlSaPassword": None
        }
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.path = None
        self.content_path_list = []
        self.ddb_path = None
        self.mount_path = None
        self.dedupehelper = None
        self.mmhelper = None
        self.client_machine = None
        self.db_password = None
        self.storage_policy_list = []
        self.backupset = None
        self.subclient_list = []
        self.copy = None
        self.store = None
        self.utility = None
        self.ma_path = None
        self.client_path = None
        self.ma_machine = None
        self.primary_recs_before_recon = None
        self.secondary_recs_before_recon = None
        self.primary_recs_after_recon = None
        self.secondary_recs_after_recon = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.ma_name = None
        self.storage_pool_name = None
        self.store_obj = None
        self.storage_pool = None
        self.ddbma_dict = {}
        self.result_string = ""
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        self.utility = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine = Machine(
            self.tcinputs['MediaAgentName'], self.commcell)
        self.ma_name = self.tcinputs.get('MediaAgentName')
        client_drive = self.utility.get_drive(
            self.client_machine, size=20*1024)
        self.client_path = self.client_machine.join_path(
            client_drive, 'test_' + str(self.id))
        self.subclient_name = '%s%s' % (str(self.id), "_SC")
        self.backupset_name = '%s%s%s' % (str(self.id), "_BS_",
                                          str(self.tcinputs["MediaAgentName"]))
        self.storage_pool_name = f"StoragePool_TC_{self.id}_{self.ma_name}"
        self.storage_policy_name = '%s%s%s' % (str(self.id), "_SP_",
                                               str(self.tcinputs["MediaAgentName"]))

        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.ma_machine, size=20*1024)
            self.ma_path = self.ma_machine.join_path(
                ma_1_drive, 'test_', str(self.id))

        if not self.is_user_defined_mp:
            self.mount_path = self.ma_machine.join_path(self.ma_path, "MP")
        else:
            self.mount_path = self.ma_machine.join_path(
                self.tcinputs['mount_path'], 'test_' + self.id, 'MP')

        if not self.is_user_defined_dedup and "unix" in self.ma_machine.os_info.lower():
            self.log.error(
                "LVM enabled dedup path must be input for Unix MA!..")
            raise Exception(
                "LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.ma_machine.join_path(self.tcinputs["dedup_path"],
                                                      'test_' + self.id, "DDB")
        else:
            self.ddb_path = self.ma_machine.join_path(self.ma_path, "DDB")
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        self.db_password = self.tcinputs['SqlSaPassword']

    def get_active_files_store(self):
        """Returns active store object for files iDA"""

        self.commcell.deduplication_engines.refresh()
        dedup_engines_obj = self.commcell.deduplication_engines
        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(
                self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])
                self.log.info(
                    f"Disabling Garbage Collection on DDB Store == {str(dedup_store[0])}")
                self.store_obj.enable_garbage_collection = False
                self.store_obj.enable_journal_pruning = False

    @test_step
    def clean_test_environment(self):
        """
        Clean up test environment
        """
        try:
            self.log.info("** STEP: Cleaning up test environment **")
            if self.content_path_list:
                if self.client_machine.check_directory_exists(self.content_path_list[-1]):
                    self.log.info(
                        "Deleting already existing content directory [%s]", self.content_path_list[-1])
                    self.client_machine.remove_directory(self.content_path_list[-1])

            # check for sp with same name if pre-existing with mark and sweep enabled
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("deleting storage policy: %s",
                              self.storage_policy_name)
                sp_obj = self.commcell.storage_policies.get(
                    self.storage_policy_name)
                sp_obj.reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info("deleting storage pool: %s",
                              self.storage_pool_name)
                self.commcell.storage_pools.delete(self.storage_pool_name)

            self.commcell.refresh()

            self.log.info("cleanup completed")

        except Exception as excp:
            self.log.warning(f"***Failure in Cleanup with error {excp}***")

    @test_step
    def configure_tc_environment(self):
        """
        Configure testcase environment - storage pool, storage policy, backupset, subclient
        """
        self.log.info("** STEP: Configuring Testcase environment **")

        self.log.info(self.name)

        # Create storage pool, storage policy and associate to subclient
        self.storage_pool, self.storage_policy_list, self.content_path_list, self.subclient_list = \
            self.dedupehelper.configure_mm_tc_environment(self.ma_machine,
                                                          self.ma_name,
                                                          self.mount_path,
                                                          self.ddb_path,
                                                          num_partitions=3)

        # get active files store and disable garbage collection and journal pruning on that store
        self.get_active_files_store()

        # Set copy retention
        self.copy = self.storage_policy_list[-1].get_copy('Primary')
        self.copy.copy_retention = (1, 0, 1)

        self.store = self.dedupehelper.get_sidb_ids(self.storage_policy_list[-1].storage_policy_id,
                                                    'Primary', multi_part=True)

        # update extended flags for store
        self.update_extd_flags_for_store()

        # update 16 AFs per secondary
        self.update_max_afs_and_extd_flags()

    def update_max_afs_and_extd_flags(self):
        """
        Method to update MaxNumOfAFsInSecFile and ExtendedFlags in idxSIDBSubStore
        """
        if len(self.store) == 3:
            self.log.info(
                "Setting MaxNumOfAFsInSecFile=16 on the three IdxSidbSubStores...")
            query = f"""
                                IF NOT EXISTS (SELECT 1 FROM idxsidbsubstore WHERE maxnumofafsinsecfile=16
                                AND sidbstoreid={self.store[0][0]})
                                BEGIN
                                UPDATE IdxSidbSubStore
                                SET 
                                MaxNumOfAFsInSecFile = 16,
                                extendedFlags = 0
                                WHERE SIDBStoreId = {self.store[0][0]}
                                END"""
            self.log.info("QUERY: %s", query)
            self.utility.update_commserve_db(query)
        else:
            raise Exception("expecting a store with three partitions")

    def update_extd_flags_for_store(self):
        """
        Method to update ExtendedFlags in idxSIDBStore
        """
        if len(self.store) == 3:
            self.log.info(
                "Setting Extended flags to 2 (default flag) on IdxSidbStores...")
            query = f"""
                                BEGIN
                                UPDATE IdxSidbStore
                                SET
                                extendedFlags = extendedFlags&~2
                                WHERE SIDBStoreId = {self.store[0][0]}
                                END"""
            self.log.info("QUERY: %s", query)
            self.utility.update_commserve_db(query)
        else:
            raise Exception("expecting a store with three partitions")

    def get_max_afs_and_extd_flags(self):
        """
        Query CSDB and get MaxNumOfAFsInSecFile and ExtendedFlags values for store

        returns:
            cur (str)   -- max num of AFs and extended Flags values
        """
        self.log.info(
            "make sure that store is set to 1 AF per secondary after compacting")
        query = f"""SELECT MaxNumOfAFsInSecFile, extendedFlags
                    FROM IdxSIDBSubStore
                    WHERE SIDBStoreId= {self.store[0][0]}"""
        self._log.info("QUERY : %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self._log.info("RESULT: %s", str(cur))
        return cur

    @test_step
    def simulate_and_validate_compaction_process(self):
        """
        Method to verify that compaction is working as expected
        """
        self.log.info("** STEP: Simulate and Validate Compaction Process **")
        # run backups
        for _ in range(6):
            self.run_backup('FULL', size=0.5)

        # Make sure that ddb process is not running
        # STEP:Get DDB MA for the given DDB Store
        self.ddbma_dict = self.dedupehelper.get_ddb_partition_ma(
            self.store[0][0])

        for partition in self.ddbma_dict:
            ddbma_obj = self.ddbma_dict[partition]
            self.log.info("Check if SIDB is running on %s for engine id %s partition %s",
                          self.ddbma_dict[partition].client_name,
                          self.store[0][0], partition)
            if not self.dedupehelper.wait_till_sidb_down(self.store[0][0], ddbma_obj):
                self.log.error(
                    "SIDBEngine is not down even after timeout of 600 seconds")
                raise Exception(
                    "SIDBEngine not down even after timeout. Returning Failure.")

        # checking flags
        maf_ext = self.get_max_afs_and_extd_flags()
        self.log.info(f"The Max AFs and extended flags before compaction are: "
                      f"Substore {self.store[0][1]}, {maf_ext[0]}; "
                      f"{self.store[1][1]}, {maf_ext[1]}; "
                      f"{self.store[2][1]}, {maf_ext[2]} ")

        # Compact ddb
        self.compact_ddb(self.store[0][0])
        res = self.get_max_afs_and_extd_flags()
        self.log.info(f"The Max AFs and extended flags after compaction are: Substore {self.store[0][1]}, {res[0]}"
                      f"; {self.store[1][1]}, {res[1]}; {self.store[2][1]}, {res[2]} ")

        for idx in range(3):
            if int(res[idx][0]) != 1:
                raise Exception(
                    f"SubStore {self.store[idx][1]} is not set to 1 AF per secondary, value {res[idx][0]}.")
            else:
                self.log.info(
                    f"SubStore {self.store[idx][1]} correctly set to 1 AF per secondary.")

    @test_step
    def run_recon_and_validate(self):
        """
        Mark store for recovery, start full recon and validate primary and sec record count
        """
        self.log.info(
            "** STEP: Run full recon and validate primary and sec record count")
        # run more backups after compaction
        for _ in range(3):
            self.run_backup('FULL', size=0.7)

        self.log.info(
            "Waiting for 150 secs for IdxSIDBUsageHistory table updates to happen")
        time.sleep(150)

        # Note primary and secondary recs count
        self.primary_recs_before_recon = self.dedupehelper.get_primary_recs_count(
            self.store[0][0], self.db_password)
        self.secondary_recs_before_recon = self.dedupehelper.get_secondary_recs_count(
            self.store[0][0], self.db_password)

        # Mark store for recovery
        self.log.info("marking store[%s] substore[%s] for recovery",
                      self.store[0][0], self.store[0][1])
        self.storage_policy_list[-1].mark_for_recovery(self.store[0][0], self.store[0][1],
                                                       self.tcinputs['MediaAgentName'], self.ddb_path)
        # Start full recon job
        self.log.info("Starting Full recon...")
        response_recon = self.storage_policy_list[-1].run_recon('Primary',
                                                                self.storage_pool_name,
                                                                self.store[0][0], full_reconstruction=1)
        self._log.info(str(response_recon))
        job_id = self.dedupehelper.poll_ddb_reconstruction(self.storage_pool_name,
                                                           'Primary')
        attempts_info = job_id.attempts
        if len(attempts_info) > 3:
            if attempts_info[2]['phase'] == 2 and attempts_info[2]['status'] == 'Failed':
                self.log.error("** FAILURE : Add Records Phase failed **")
                raise Exception(
                    "Recon job failed in Add Records phase! Check logs")

        self.log.info(
            "Waiting for 150 secs for IdxSIDBUsageHistory table updates to happen")
        time.sleep(150)

        self.primary_recs_after_recon = self.dedupehelper.get_primary_recs_count(
            self.store[0][0], self.db_password)
        self.secondary_recs_after_recon = self.dedupehelper.get_secondary_recs_count(
            self.store[0][0], self.db_password)

        self.log.info("validate: pri_before:%s = pri_after:%s", self.primary_recs_before_recon,
                      self.primary_recs_after_recon)
        if self.primary_recs_before_recon == self.primary_recs_after_recon:
            self.log.info("Pass")
        else:
            self.log.error("Fail!")
            raise Exception(
                "primary records before and after full recon - do not match")

        self.log.info("validate: sec_before:%s = sec_after:%s",
                      self.secondary_recs_before_recon, self.secondary_recs_after_recon)
        if self.secondary_recs_before_recon == self.secondary_recs_after_recon:
            self.log.info("Pass")
        else:
            self.log.error("Fail!")
            raise Exception(
                "secondary records before and after full recon - do not match")

    def run_backup(self, backup_type="FULL", size=1.0):
        """
        this function runs backup by generating new content to get unique blocks for dedupe backups
        Args:
            backup_type (str): type of backup to run
            size (float): size of backup content to generate

        Returns:
        (object) -- returns job object to backup job
        """
        # add content
        self.client_machine.remove_directory(self.content_path_list[-1])
        self.mmhelper.create_uncompressable_data(self.tcinputs["ClientName"],
                                                 self.content_path_list[-1], size)
        self._log.info("Running %s backup...", backup_type)
        job = self.subclient_list[-1].backup(backup_type)
        self._log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                f"Failed to run {backup_type} backup with error: {job.delay_reason}"
            )
        self._log.info("Backup job completed.")
        return job

    def compact_ddb(self, store):
        """
        this method runs sidb compact command for each partition on store
        Args:
            store: store id where sidb command needs to be run

        """
        # STEP:Get DDB MA for the given DDB Store
        ddbma_dict = self.dedupehelper.get_ddb_partition_ma(store)

        # Run sidb compact CLI for each partition for given SP
        for partition in ddbma_dict:
            self.log.info("Following DDB MA has been chosen for executing sidb2 compact %s",
                          ddbma_dict[partition].client_name)
            ddbma_obj = ddbma_dict[partition]
            # Note: Make sure that SIDB2 process with this engine_id is not running
            self.dedupehelper.execute_sidb_command('compactfile secondary',
                                                   store, partition, ddbma_obj)
        self.log.info("done running sidb compact!")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            self.clean_test_environment()
            self.configure_tc_environment()
            self.simulate_and_validate_compaction_process()
            self.run_recon_and_validate()
            # run data aging to keep the sp from consuming more space
            try:
                self.mmhelper.submit_data_aging_job(
                    'Primary', self.storage_policy_name)
            except Exception:
                pass

        except Exception as exp:
            self._log.error(
                'Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        # clean up > remove content
        try:
            self.clean_test_environment()
        except Exception as exe:
            self.log.error(
                'ERROR in TearDown Might need to cleanup manually: %s', exe)
