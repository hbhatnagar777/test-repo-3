# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""[Automation] Test case for validating micro-pruning disabled DDB stores should not be picked for resync

Steps:
    1.  Configure resources
        A.  dedupe-Disk Storage with WORM
            i.  Active DDB (worm_active)
            ii. Sealed DDB (worm_sealed) -> Backup jobs will be run before sealing
        B.  dedupe-Disk Storage without WORM (worm_after_resync_bit_set)
        C.  dedupe-Disk Storage with corrupt partition (corrupt_partition)
        D.  dedupe-Disk Storage with all good and Micro-Pruning enabled (positive_validation)
        E.  Plans (one corresponding to each storage) with retention 1 day, 0 cycle
            Hint: sp_primary_copy_obj.copy_retention = (1, 0, 1)
        F.  Configure Backupset and Subclients (one for each plan)
    2.  Generate data and run backups on each Subclients
    3.  Move DDB CreatedTime back by 30 days
        Hint: UPDATE IdxSIDBStore SET CreatedTime = CreatedTime - (30*86400) WHERE SIDBStoreId={SIDBStoreId}
    4.  Seal store for worm_sealed
    5.  Mark stores for maintenance
        Hint: EXEC MMDDBSetMaintenanceStatus {SIDBStoreId}, 0, 11, 1
        A.  Resync Flag should be set for: "worm_after_resync_bit_set", "corrupt_partition", "positive_validation"
        B.  Resync Flag should not be set for: "worm_active", "worm_sealed"
    6.  Enable WORM on worm_after_resync_bit_set
    7.  Mark DDB partition corrupt for corrupt_partition
    8.  Check which stores are now picked for resync
        Hint: EXEC MMGetDDBResyncInfo 1
        A.  Stores to be picked for resync: "positive_validation"
        B.  Stores to be skipped: "worm_active", "worm_sealed", "worm_after_resync_bit_set", "corrupt_partition"
    9.  De-configure resources -> Disable SUBCLIENTS and then delete

TestCase: Class for executing this test case
TestCase:
    __init__()              --  initialize TestCase class

    _configure_resources()  --  Configure resources
    setup()                 --  setup function of this test case

    _run_backups()                      --  Generate data and run backups on each Subclients
    _update_store_creation_time()       --  Modify created time for the given SIDB store.
    _mark_stores_for_maintenance()      --  Mark stores for maintenance
    _validate_store_picked_for_resync() --  Check which stores are now picked for resync
    run()                               --  run function of this test case

    _cleanup()              --  Delete existing entities before/after running testcase
    tear_down()             --  tear down function of this test case


User should have the following permissions:
        [Execute Workflow] permission on [Execute Query] workflow


Sample Input:
"70597": {
    "ClientName": "Name of the Client",
    "AgentName": "File System",
    "MediaAgentName": "Name of the MediaAgent",
    "SqlSaPassword": "CSDB Password for executing update queries",
    *** optional ***
    "dedupe_path": "LVM enabled path for Unix MediaAgent",
}


NOTE:
    1. LVM enabled path must be supplied for Unix MA. Dedupe paths will be created inside this folder.
}
"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper

from cvpysdk import deduplication_engines


class TestCase(CVTestCase):
    """Test case for validating micro-pruning disabled DDB stores should not be picked for resync"""

    # Minimum free space required on the machine
    FREE_SPACE_REQUIRED = 25*1024

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name        (str)       --  name of this test case

                tcinputs    (dict)      --  test case inputs with input name as dict key
                                            and value as input type
        """
        super(TestCase, self).__init__()

        self.name = 'Test case for validating micro-pruning disabled DDB stores should not be picked for resync'
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None,
            "SqlSaPassword": None,
        }

        self.ma_name = None
        self.client_machine = None

        self.cases = [
            "worm_active",
            "worm_sealed",
            "worm_after_resync_bit_set",
            "corrupt_partition",
            "positive_validation"
        ]
        self.sidb_stores = {}    # Key = self.cases, Value = SIDBStore for storage pool corresponding to case

        # Content Path, Mount Path, DDB Paths
        self.content_path = None
        self.mount_path = None
        self.dedupe_path = None

        self.storage_pool_name = None
        self.plan_name = None
        self.backupset_name = None
        self.subclient_name = None

        self.backupset = None

        self.job_history = []

        self.mm_helper: MMHelper = None
        self.dedup_engines_helper = None
        self.options_selector: OptionsSelector = None

    def setup(self):
        """Setup function of this test case"""
        self.ma_name = self.tcinputs['MediaAgentName']

        self.options_selector = OptionsSelector(self.commcell)
        tcid = self.id
        path_prefix = f"test_{tcid}"

        self.client_machine = self.options_selector.get_machine_object(self.client.client_name)
        ma_machine = self.options_selector.get_machine_object(self.ma_name)

        client_drive = self.options_selector.get_drive(self.client_machine, size=self.FREE_SPACE_REQUIRED)
        ma_drive = self.options_selector.get_drive(ma_machine, size=self.FREE_SPACE_REQUIRED)

        self.content_path = self.client_machine.join_path(client_drive, path_prefix, f"Content(%s)")
        self.mount_path = ma_machine.join_path(ma_drive, path_prefix, f"MP(%s)")

        if 'unix' in ma_machine.os_info.lower():
            if 'dedupe_path' not in self.tcinputs:
                self.log.error('LVM enabled dedup path must be supplied for Unix MA')
                raise ValueError('LVM enabled dedup path must be supplied for Unix MA')
            self.dedupe_path = ma_machine.join_path(self.tcinputs["dedupe_path"], path_prefix, f"DDB(%s)")
        else:
            self.dedupe_path = ma_machine.join_path(ma_drive, path_prefix, f"DDB(%s)")

        self.storage_pool_name = f"{tcid}_disk_ma({self.ma_name})_cl({self.client.client_name})_subcl(%s)"
        self.plan_name = f"{tcid}_plan_ma({self.ma_name})_cl({self.client.client_name})_subcl(%s)"
        self.backupset_name = f"{tcid}_BS"
        self.subclient_name = f"{tcid}_subcl(%s)"

        self.mm_helper = MMHelper(self)
        self.dedup_engines_helper = deduplication_engines.DeduplicationEngines(self.commcell)

    def run(self):
        """Run function of this test case"""

        try:
            self._cleanup()

            # 1. Configure resources
            self._configure_resources()

            # 2. Generate data and run backups on each Subclients
            self._run_backups()

            # 3. Move DDB CreatedTime back by 30 days
            for sidb_store in self.sidb_stores.values():
                self._update_store_creation_time(sidb_store.store_id)

            # 4. Seal store for worm_sealed
            self.log.info("Sealing store corresponding to: %s", self.storage_pool_name % 'worm_sealed')
            self.sidb_stores['worm_sealed'].seal_deduplication_database()

            # 5. Mark stores for maintenance
            self.log.info("Marking stores for maintenance")
            if not self._mark_stores_for_maintenance():
                raise Exception("Validation failed, check logs for error message")

            # 6. Enable WORM on worm_after_resync_bit_set
            self.log.info("Enabling WORM on Storage Pool: %s", self.storage_pool_name % 'worm_after_resync_bit_set')
            self.commcell.storage_pools.get(self.storage_pool_name % 'worm_after_resync_bit_set').enable_worm_storage_lock(1)

            # 7. Mark DDB partition corrupt for corrupt_partition
            self.log.info("Corrupting the file Primary.Dat, delete Primary.idx, State.xml")
            ma_machine = self.options_selector.get_machine_object(self.ma_name)
            ddb_path = ma_machine.join_path(self.dedupe_path % 'corrupt_partition', 'CV_SIDB', '2',
                                            str(self.sidb_stores['corrupt_partition'].store_id), 'Split00')
            ma_machine.create_file(ma_machine.join_path(ddb_path, 'Primary.dat'), 'This file has been corrupted')
            ma_machine.delete_file(ma_machine.join_path(ddb_path, 'Primary.idx'))
            ma_machine.delete_file(ma_machine.join_path(ddb_path, 'State.xml'))
            ddb_verification_job = self.sidb_stores['corrupt_partition'].run_ddb_verification()
            self.log.info("Running DDB Verification job %s to mark store corrupt", ddb_verification_job.job_id)
            ddb_verification_job.wait_for_completion()
            self.log.info("DDB Verification job completed.")

            # 8. Check which stores are now picked for resync
            if not self._validate_store_picked_for_resync():
                raise Exception("Validation failed, check logs for error message")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            # Delete jobs by updating start date followed by data aging
            if len(self.job_history):
                for job in self.job_history:
                    self.mm_helper.move_job_start_time(job.job_id, 30)

            self._cleanup()
        except Exception as exp:
            self.log.error('Failed to tear down test case with error: %s', exp)

    def _cleanup(self):
        """Delete existing entities before/after running testcase"""
        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            for case in self.cases:
                if self.client_machine.check_directory_exists(self.content_path % case):
                    self.client_machine.remove_directory(self.content_path % case)

            # Delete backupset
            for _ in range(2):
                self.log.info("Deleting BackupSet: %s, if exists", self.backupset_name)
                if not self.agent.backupsets.has_backupset(self.backupset_name):
                    break   # Backup set has been deleted
                try:
                    self.backupset = self.agent.backupsets.get(self.backupset_name)
                    for case in self.cases:
                        subcl = self.subclient_name % case
                        if self.backupset.subclients.has_subclient(subcl):
                            self.log.info("Disabling backup on subclient: %s", subcl)
                            self.backupset.subclients.get(self.subclient_name % case).disable_backup()
                            self.log.info("Deleting subclient: %s", subcl)
                            self.backupset.subclients.delete(self.subclient_name % case)

                    data_aging_job = self.mm_helper.submit_data_aging_job()
                    self.log.info(f"Started data aging jobs: %s", data_aging_job.job_id)
                    if not data_aging_job.wait_for_completion():
                        raise Exception("Failed to run data aging job with error: %s", data_aging_job.delay_reason)
                    self.log.info("Completed data aging with Job ID: %s", data_aging_job.job_id)

                    # Delete backup set
                    self.agent.backupsets.delete(self.backupset_name)
                    self.log.info("Deleted BackupSet: %s", self.backupset_name)
                except Exception as exp:
                    self.log.error(exp)
                    self.log.info("Failed to delete backupset. Will retry again after data aging")

                    # Wait for some time before next data aging job
                    time.sleep(180)

            # Delete Plans
            for case in self.cases:
                plan_name = self.plan_name % case
                self.log.info("Deleting Plan: %s, if exists", plan_name)
                if self.commcell.plans.has_plan(plan_name):
                    self.commcell.plans.delete(plan_name)
                    self.log.info("Deleted Plan: %s", plan_name)

            # Delete Storage Pools
            for case in self.cases:
                storage_pool_name = self.storage_pool_name % case
                self.log.info("Deleting storage pool: %s, if exists" % storage_pool_name)
                if self.commcell.storage_pools.has_storage_pool(storage_pool_name):
                    self.commcell.storage_pools.delete(storage_pool_name)
                    self.log.info("Deleted storage pool: %s" % storage_pool_name)
        except Exception as exp:
            self.log.error(f"Error encountered during cleanup : {exp}")
            raise Exception(f"Error encountered during cleanup : {exp}")
        self.log.info("********************** CLEANUP COMPLETED *************************")

    def _configure_resources(self):
        """ Configure resources
            A.  dedupe-Disk Storage with WORM
                i.  Active DDB (worm_active)
                ii. Sealed DDB (worm_sealed) -> Backup jobs will be run before sealing
            B.  dedupe-Disk Storage without WORM (worm_after_resync_bit_set)
            C.  dedupe-Disk Storage with corrupt partition (corrupt_partition)
            D.  dedupe-Disk Storage with all good and Micro-Pruning enabled (positive_validation)
            E.  Plans (one corresponding to each storage) with retention 1 day, 0 cycle
                Hint: sp_primary_copy_obj.copy_retention = (1, 0, 1)
            F.  Configure Backupset and Subclients (one for each plan)
        """
        self.log.info("********************** CONFIGURE RESOURCES STARTED *************************")

        self.log.info("Configuring Backupset: %s", self.backupset_name)
        self.backupset = self.mm_helper.configure_backupset(backupset_name=self.backupset_name, agent=self.agent)
        self.log.info("Configured Backupset: %s", self.backupset_name)

        for case in self.cases:
            self.log.info("Configuring Storage Pool: %s", self.storage_pool_name % case)
            pool, _ = self.mm_helper.configure_storage_pool(
                storage_pool_name=self.storage_pool_name % case,
                mount_path=self.mount_path % case,
                media_agent=self.ma_name,
                ddb_path=self.dedupe_path % case,
                ddb_ma=self.ma_name,
            )
            self.log.info("Configured Storage Pool: %s", self.storage_pool_name % case)

            self.log.info("Configuring Plan: %s", self.plan_name % case)
            plan = self.commcell.plans.create_server_plan(
                plan_name=self.plan_name % case,
                backup_destinations={"storage_name": self.storage_pool_name % case},
            )
            self.log.info("Configured Plan: %s", self.plan_name % case)

            storage_policy = plan.storage_policy
            primary_copy = storage_policy.get_copy("Primary")
            self.log.info("Setting retention to 1 day, 0 cycle on Primary copy of Plan: %s", self.plan_name % case)
            primary_copy.copy_retention = (1, 0, 1)

            if case in ["worm_active", "worm_sealed"]:
                self.log.info("Enabling WORM on Storage Pool: %s", self.storage_pool_name % case)
                pool.enable_worm_storage_lock(1)

            self.log.info("Configuring Subclient: %s", self.subclient_name % case)
            self.mm_helper.configure_subclient(
                backupset_name=self.backupset_name,
                subclient_name=self.subclient_name % case,
                storage_policy_name=storage_policy.storage_policy_name,
                content_path=self.content_path % case,
                agent=self.agent,
            )
            self.log.info("Configured Subclient: %s", self.subclient_name % case)

        # Refresh all entities
        self.commcell.refresh()
        self.backupset.refresh()
        self.log.info("********************** CONFIGURE RESOURCES COMPLETED *************************")

    def _run_backups(self):
        """ Generate data and run backups on each Subclients """

        for backup_level in ['full', 'incremental', 'incremental', 'synthetic_full']:
            jobs = []
            self.log.info("Running %s backup for each Subclient in Backupset", backup_level)
            for case in self.cases:
                self.log.info("Generating data at content path: %s", self.content_path % case)
                self.mm_helper.create_uncompressable_data(
                    self.client,
                    self.client_machine.join_path(self.content_path % case, time.strftime("%H%M")),
                    0.1
                )
                self.log.info("Starting %s backup for sub client: %s", backup_level, self.subclient_name % case)
                job = self.backupset.subclients.get(self.subclient_name % case).backup(backup_level=backup_level)
                self.log.info(f"Started %s backup job: %s", backup_level, job.job_id)
                self.job_history.append(job)
                jobs.append(job)

            for job in jobs:
                if not job.wait_for_completion():
                    raise Exception("Failed to run %s backup job with error: %s", backup_level, job.delay_reason)
                self.log.info("Completed %s backup with Job ID: %s", backup_level, job.job_id)

        for case in self.cases:
            if self.dedup_engines_helper.has_engine(self.storage_pool_name % case, 'Primary'):
                dedup_engine = self.dedup_engines_helper.get(self.storage_pool_name % case, 'Primary')
                self.sidb_stores[case] = dedup_engine.get(dedup_engine.all_stores[0][0])
                self.log.info("Storage: %s, SIDBStoreId: %s", case, self.sidb_stores[case])
            else:
                raise Exception("Cannot find SIDB store corresponding to %s" % case)

    def _update_store_creation_time(self, SIDBStoreId):
        """ Modify created time for the given SIDB store.
            Args:
                SIDBStoreId     (int)   --  SIDB Store id for which creation time is to be modified.
        """
        query = f"""SELECT CreatedTime FROM IdxSIDBStore WHERE SIDBStoreId={SIDBStoreId}"""
        created_time = int(self.mm_helper.execute_select_query(query)[0][0])

        backdated_created_time = created_time - (30*86400)
        self.log.info("30 Day Backed CreatedTime for SIDB store %s is %s", SIDBStoreId, backdated_created_time)

        query = f"""UPDATE IdxSIDBStore SET CreatedTime = {backdated_created_time} WHERE SIDBStoreId={SIDBStoreId}"""
        self.mm_helper.execute_update_query(query)
        self.log.info(f"Successfully modified CreatedTime for {SIDBStoreId}")

    def _mark_stores_for_maintenance(self):
        """ Mark stores for maintenance
            Hint: EXEC MMDDBSetMaintenanceStatus {SIDBStoreId}, 0, 11, 1
            A.  Resync Flag should be set for: "worm_after_resync_bit_set", "corrupt_partition", "positive_validation"
            B.  Resync Flag should not be set for: "worm_active", "worm_sealed"
        """
        self.log.info("********************** Marking stores for maintenance *************************")

        should_be_set = ["worm_after_resync_bit_set", "corrupt_partition", "positive_validation"]
        should_not_be_set = ["worm_active", "worm_sealed"]

        validation_flag = True

        for case in self.cases:
            sidb_store_id = self.sidb_stores[case].store_id
            response, _ = self.mm_helper.execute_stored_proc("CommServ.dbo.MMDDBSetMaintenanceStatus",
                                                             (sidb_store_id, 0, 11, 1),
                                                             use_set_nocount=True)
            store_selected = int(response.rows[0][3])
            reason_string = response.rows[0][4]
            if store_selected == 0:
                self.log.info("SIDB store for case %s not marked for resync", case)
                self.log.info("Reason: %s", reason_string)
                if case in should_be_set:
                    self.log.error("Expected it to be marked for resync!")
                    validation_flag = False
            else:
                self.log.info("SIDB store for case %s marked for resync", case)
                if case in should_not_be_set:
                    self.log.error("Did not expect it to be marked for resync!")
                    validation_flag = False

        return validation_flag

    def _validate_store_picked_for_resync(self):
        """ Check which stores are now picked for resync
            Hint: EXEC MMGetDDBResyncInfo 1
            A.  Stores to be picked for resync: "positive_validation"
            B.  Stores to be skipped: "worm_active", "worm_sealed", "worm_after_resync_bit_set", "corrupt_partition"
        """
        self.log.info("********************** Check which stores are now picked for resync *************************")

        should_be_picked = ["positive_validation"]
        should_not_be_picked = ["worm_active", "worm_sealed", "worm_after_resync_bit_set", "corrupt_partition"]

        validation_flag = True

        response, _ = self.mm_helper.execute_stored_proc("CommServ.dbo.MMGetDDBResyncInfo", (10,), use_set_nocount=True)
        store_selected = {row[0]: row[3] for row in response.rows}
        reason_string = {row[0]: row[4] for row in response.rows}

        for case in self.cases:
            sidb_store_id = self.sidb_stores[case].store_id
            if sidb_store_id not in store_selected:
                self.log.info("SIDB store for case %s was not picked for resync", case)
                if case in should_be_picked:
                    self.log.error("Expected it to be picked for resync!")
                    validation_flag = False
            elif store_selected[sidb_store_id] == 0:
                self.log.info("SIDB store for case %s was not picked for resync", case)
                self.log.info("Reason: %s", reason_string[sidb_store_id])
                if case in should_be_picked:
                    self.log.error("Expected it to be picked for resync!")
                    validation_flag = False
            else:
                self.log.info("SIDB store for case %s was picked for resync", case)
                if case in should_not_be_picked:
                    self.log.error("Did not expect it to be picked for resync!")
                    validation_flag = False

        return validation_flag
