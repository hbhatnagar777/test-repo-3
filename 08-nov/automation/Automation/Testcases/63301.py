# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    create_resources    --  create all the resources required

    generate_backup_data    -- generate unique content

    run_auxilary_copy   -- run aux copy job

    run_backups      -- run backups

    run_data_aging      -- run data aging job

    verify_volume_pruned  -- verify that Volume in sidb are marked aged

    verify_mmdeletedaf   -- verify that MMDeletedAF is cleaned for the given sidbs store

    verify_sidbstore_pruned   -- verify that SIDB Store is pruned successfully

    verify_sidb_marked        -- verify sidb is marked for pruning

    update_createtime   --  update createtime for the given store id

    delete_jobs --  delete backup jobs and run data aging

    run()           --  run function of this test case

Design Steps:
1. Create a backupset.
2. Create n storagepools.
3. Create n//2 storage policies with 2 Copies, each copy pointing to a seprate storage pool.
4. Run backup on all SP.
5. Run Aux copy job.
6. Seal the SIDB Stores.
7. Delete all jobs on stores.
8. Run Data Aging
9. Verify MMVolume entries pruned.
10. Verify flag&256 should be marked to 256 in IdxSidbStore table.
11. Verify entries from IdxSIDBStore, IdxAccessPathId, IdxCacheId for these stores should be removed.

Sample Input:
    "63301": {
                "ClientName": "client name",
                "MediaAgentName": "media agent name",
                "AgentName": "File System",
                
            }
    **optional input - 
        "dedup_path" : "deduplication path"
        "LibraryName" :  "LibraryName"
"""

import time
import threading
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = 'Macro Pruning and Cleanup of Sealed SIDB Store'
        self.storage_pool_name = None
        self.storage_pool_name2 = None
        self.storage_pool1 = None
        self.storage_pool2 = None
        self.primary_copy = None
        self.secondary_copy = None
        self.dedup_path = None
        self.storage_policy_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.disk_mount_path = None
        self.disk_mount_path2 = None
        self.ma_machine = None
        self.ma_client = None
        self.client_machine = None
        self.dedup_helper = None
        self.mm_helper = None
        self.option_selector = None
        self.ddb_path = None
        self.ddb_path2 = None
        self.content_path = None
        self.MediaAgent = None

        self.subclient_list = None
        self.content_path_list = None
        self.sp_list = None
        self.sidb_list = None
        self.sidb_copy_list = None
        self.backup_job_list = None
        self.storage_pool_list = None
        self.prune_process_interval = None
        self.maintainence_process_interval = None

        self.is_user_defined_dedup = None

        self.tcinputs = {
            "MediaAgentName": None
        }

    def setup(self):
        """Setup function of this test case"""

        # Storage Policy
        self.MediaAgent = self.tcinputs.get("MediaAgentName")
        self.storage_pool_name = '%s_storage_pool_%s' % (str(self.id), self.MediaAgent)
        self.storage_pool_name2 = '%s_storage_pool2_%s' % (str(self.id), self.MediaAgent)
        self.storage_policy_name = '%s_storage_policy_%s' % (str(self.id), self.MediaAgent)
        self.backupset_name = '%s_backupset_%s' % (str(self.id), self.MediaAgent)
        self.subclient_name = '%s_subclient_%s' % (str(self.id), self.MediaAgent)

        self.subclient_list = []
        self.content_path_list = []
        self.sp_list = []
        self.sidb_list = []
        self.backup_job_list = []
        self.storage_pool_list = []

        self.prune_process_interval = 2
        self.maintainence_process_interval = 5
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        else:
            self.is_user_defined_dedup = False

        # Machine & Client object creation
        self.option_selector = OptionsSelector(self.commcell)
        self.dedup_helper = DedupeHelper(self)
        self.mm_helper = MMHelper(self)

        # Machine Objects
        self.client_machine = self.option_selector.get_machine_object(
            self.tcinputs['ClientName'])
        self.ma_machine = self.option_selector.get_machine_object(
            self.tcinputs['MediaAgentName'])

        # Client Drive and Content Path
        # select drive in client machine
        self.log.info(
            'Selecting drive in the client machine based on space available')
        client_drive = self.option_selector.get_drive(
            self.client_machine, size=20 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data on client")

        self.log.info(
            'Selecting drive in the MA machine based on space available')
        ma_drive = self.option_selector.get_drive(
            self.ma_machine, size=20 * 1024)
        if ma_drive is None:
            raise Exception("No free space for generating data on MA")
        self.log.info('selected drive: %s', ma_drive)

        # Clean up
        self._cleanup()

        # Create paths.
        self.content_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata')

        # DDB Path
        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.tcinputs["dedup_path"]
            self.ddb_path2 = self.tcinputs["dedup_path"] + "2"
        else:
            if "unix" in self.ma_machine.os_info.lower():
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_path = self.ma_machine.join_path(
                ma_drive, 'Automation',
                str(self.id), 'DDBPath'
            )
            self.ddb_path2 = self.ma_machine.join_path(
                ma_drive, 'Automation',
                str(self.id), 'DDBPath2'
            )

        # Library Mount Path for first storage pool
        self.disk_mount_path = self.ma_machine.join_path(ma_drive,
                                                         'Automation', str(self.id), 'diskMP')

        # Library Mount Path for second storage pool
        self.disk_mount_path2 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'diskMP2')

    def create_resources(self):
        """Create all the resources required to run backups"""

        # Creating a BackupSet.
        self.log.info("Creating BackupSet %s", self.backupset_name)
        backup_set_obj = self.mm_helper.configure_backupset(self.backupset_name)

        # Create Storage Pool
        self.storage_pool1 = self.commcell.storage_pools.add(self.storage_pool_name, self.disk_mount_path,
                                                             self.MediaAgent, self.MediaAgent, self.ddb_path)
        self.log.info(f'---Successfully configured Storage Pool - {self.storage_pool_name}')
        self.storage_pool_list.append(self.storage_pool1)

        # Creating Storage Policy.
        self.log.info("Configuring Dependent Storage Policy ==> %s", self.storage_policy_name)
        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            storage_policy_obj = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                    library=self.storage_pool_name,
                                                                    media_agent=self.MediaAgent,
                                                                    global_policy_name=self.storage_pool_name,
                                                                    dedup_media_agent=self.MediaAgent,
                                                                    dedup_path=self.ddb_path)
        else:
            storage_policy_obj = self.commcell.storage_policies.get(self.storage_policy_name)

        self.sp_list.append(storage_policy_obj)

        self.log.info("Setting Copy Retention for Primary Copy of [%s] to 0 days 1 cycles", self.storage_policy_name)
        self.primary_copy = storage_policy_obj.get_copy("Primary")
        retention = (0, 1, 1)
        self.primary_copy.copy_retention = retention

        # Get sidb id for primary copy
        sp_id = storage_policy_obj.storage_policy_id
        storeid = self.dedup_helper.get_sidb_ids(str(sp_id), 'Primary')[0]  # Primary Global

        # Update Create Time for this SIDBStore
        self.update_createtime(storeid)
        self.sidb_list.append(storeid)

        # Create Storage Pool for Secondary Copy
        self.storage_pool2 = self.commcell.storage_pools.add(self.storage_pool_name2, self.disk_mount_path2,
                                                             self.MediaAgent, self.MediaAgent,
                                                             self.ddb_path2)
        self.log.info(f'---Successfully configured Storage Pool - {self.storage_pool_name2}')
        self.storage_pool_list.append(self.storage_pool2)

        copy_name = 'SecondaryCopy'
        storage_policy_obj.create_secondary_copy(copy_name, global_policy=self.storage_pool_name2)
        self.secondary_copy = storage_policy_obj.get_copy(copy_name)

        self.log.info("Setting Copy Retention for Secondary Copy of [%s] to 0 day 1 cycles", copy_name)
        retention = (0, 1, 1)
        self.secondary_copy.copy_retention = retention

        # get sidb id for secondary copy
        sp_id = self.secondary_copy.storage_policy_id
        storeid = self.dedup_helper.get_sidb_ids(str(sp_id), 'SecondaryCopy')[0]

        # Update CreateTime for this SIDBStore
        self.update_createtime(storeid)
        self.sidb_list.append(storeid)

        # Removing association with System Created Automatic Auxcopy schedule
        self.log.info("Removing association with System Created Autocopy schedule on above created copy")
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, "Primary")
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, "SecondaryCopy")

        # Creating Subclient
        self.log.info("Configuring subclient %s for storage policy %s", self.subclient_name, self.storage_policy_name)
        self.content_path_list.append(self.content_path)
        if not backup_set_obj.subclients.has_subclient(self.subclient_name):
            self.subclient_list.append(self.mm_helper.configure_subclient(self.backupset_name,
                                                                          self.subclient_name,
                                                                          self.storage_policy_name,
                                                                          self.content_path))
        else:
            self.subclient_list.append(backup_set_obj.subclients.get(self.subclient_name))

    def generate_backup_data(self, index):
        """
        Generates 250MB of uncompressable data

        Args:
                index   (int)
        Returns:
                none
        """
        # 250MB uncompressable and unique data
        self.option_selector.create_uncompressable_data(
            client=self.tcinputs['ClientName'],
            path=self.content_path_list[index - 1],
            size=0.25
        )

    def run_auxilary_copy(self):
        """
        run aux copy job on all the storage policy copies in sp_list
        """
        aux_job_list = []
        for storage_policy in self.sp_list:
            self.log.info(f"Starting aux copy job for {storage_policy}")
            auxcopy_job = storage_policy.run_aux_copy()
            self.log.info("Auxcopy job [%s] has started.", auxcopy_job.job_id)
            aux_job_list.append(auxcopy_job)

        for aux_job in aux_job_list:
            if not aux_job.wait_for_completion():
                self.log.error(
                    "Auxcopy job [%s] has failed with %s.", aux_job.job_id, aux_job.delay_reason)
                raise Exception(
                    "Auxcopy job [{0}] has failed with {1}.".format(aux_job.job_id, aux_job.delay_reason))
            self.log.info(
                "Auxcopy job [%s] has completed.", aux_job.job_id)

    def run_backups(self):
        """
        Run backups on subclients
        """
        thread_pool = []
        for num in range(1, len(self.subclient_list) + 1):
            current_thread = threading.Thread(target=self.generate_backup_data, args=(num,))
            current_thread.start()
            self.log.info("Started Backup data generation thread for subclient [%s]", self.subclient_list[num - 1])
            thread_pool.append(current_thread)

            if num % 8 == 0:
                self.log.info("Waiting for Backup data generation threads to complete")
                for current_thread in thread_pool:
                    current_thread.join()
                self.log.info("Starting Backup data generation for remaining subclients")
                thread_pool = []

        # If number is not divisible by 4
        if thread_pool != []:
            self.log.info("Waiting for Backup data generation threads to complete")
            for current_thread in thread_pool:
                current_thread.join()
        backup_jobs = []
        for num in range(1, len(self.subclient_list) + 1):
            self.log.info("Starting backup on subclient %s", self.subclient_list[num - 1].name)
            backup_jobs.append(self.subclient_list[num - 1].backup("Full"))
            self.log.info("Backup Job on Subclient [%s] ==> [%s]", self.subclient_list[num - 1].name,
                          backup_jobs[num - 1].job_id)
            self.backup_job_list.append(backup_jobs[num - 1].job_id)

        # wait for jobs to complete.
        for job in backup_jobs:
            self.log.info(f"Waiting for backup job {job.job_id} to complete!")
            if not job.wait_for_completion():
                raise Exception(f"Failed to run backup with error: {job.delay_reason}")
            self.log.info(f"Backup job {job.job_id} completed.")

    def run_data_aging(self, copy_name, sp_name):
        """
        Run data aging job
        Args:
                copy_name   (str)
                sp_name (str)
        """
        data_aging_job = self.mm_helper.submit_data_aging_job(copy_name=copy_name, storage_policy_name=sp_name,
                                                              is_granular=True, include_all=False,
                                                              include_all_clients=True,
                                                              select_copies=True, prune_selected_copies=True)
        self.log.info(
            "Data Aging job [%s] has started.", data_aging_job.job_id)
        if not data_aging_job.wait_for_completion():
            self.log.error(
                "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
            raise Exception(
                "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                   data_aging_job.delay_reason))
        self.log.info(
            "Data Aging job [%s] has completed.", data_aging_job.job_id)

    def verify_volume_pruned(self):
        """
        Verify that Volume in sidb are marked aged.

        Returns:
                verifyvolpruned (bool)
        """
        self.log.info(f"Validating MMVolume table for {self.sidb_list}")
        verifyvolpruned = True
        sidb_ids = ', '.join(self.sidb_list)
        query = f"""select count(VolumeId) from mmvolume where sidbstoreid  in  ({sidb_ids})"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT: {res}")
        if int(res) != 0:
            self.log.info("MMVolume entries are not pruned for all stores!")
            verifyvolpruned = False
        else:
            self.log.info("MMVolume entries pruned successfully!")
        return verifyvolpruned

    def verify_mmdeletedaf(self):
        """
        Verify that MMDeletedAF has no jobs.
        """
        self.log.info(f"Validating MMDeletedAF table for {self.sidb_list}")
        sidb_ids = ', '.join(self.sidb_list)
        query = f"""select count(archFileId) from MMDeletedAF where SIDBStoreId in ({sidb_ids})"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT: {res}")
        if int(res) != 0:
            raise Exception("MMDeletedAF entries are not pruned for all stores!")
        self.log.info("MMDeletedAF entries pruned successfully")

    def verify_sidbstore_pruned(self):
        """
        Verify that SIDB Store is pruned successfully.

        Returns:
                (bool) bool on whether store was successfully removed from idxsidbstore table
        """
        self.log.info(f"Validating SIDBStore for {self.sidb_list}")
        sidb_ids = ', '.join(self.sidb_list)
        query1 = f"""select count(sidbstoreid) from idxsidbstore where sidbstoreid in ({sidb_ids})"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT QUERY1: {res}")
        if int(res) != 0:
            self.log.info("IdxSIDBStore entries are not pruned for all stores!")
            return False

        query2 = f"""select count(IdxAccessPathId) from IdxAccessPath where idxaccesspathid in 
        (select idxaccesspathid from IdxSIDBSubStore where sidbstoreid in ({sidb_ids}))"""
        self.log.info("Query: %s", query2)
        self.csdb.execute(query2)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT QUERY2: {res}")
        if int(res) != 0:
            self.log.info("IdxAccessPath entries are not pruned for all stores!")
            return False

        query3 = f"""select count(IdxCacheId) from IdxCache where IdxCacheId in 
        (select IdxCacheId from IdxSIDBSubStore where sidbstoreid in ({sidb_ids}))"""
        self.log.info("Query: %s", query3)
        self.csdb.execute(query3)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT QUERY3: {res}")
        if int(res) != 0:
            self.log.info("IdxSIDBSubStore entries are not pruned for all stores!")
            return False
        self.log.info("SIDB Store Pruned Successful!")
        return True

    def verify_sidb_marked(self):
        """
        verify store is marked aged with the 256 bit in the idxsidbstore table
        """
        self.log.info(f"Validating SIDBStore for {self.sidb_list}")
        sidb_ids = ', '.join(self.sidb_list)
        query = f"""select flags&256 from idxsidbstore where sidbstoreid in ({sidb_ids})"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")
        flag_list = [x[0] for x in res]
        self.log.info(f"RESULT: {flag_list}")
        for obj in flag_list:
            if obj not in ("", '256'):
                raise Exception("SIDB Store is not marked!")
        self.log.info("SIDB Store flag validation complete!")

    def update_createtime(self, sidbid):
        """
        Update create time for the given SIDB store.
        Args:
            sidbid  (int)   store id
        """
        query1 = f"""select CreatedTime from idxsidbstore where sidbstoreid = {sidbid}"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        created_time = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"RESULT: {created_time}")
        backdated_created_time = created_time - 86400
        self.log.info("1 Day Backed CreatedTime for SIDB store %s is %s", sidbid, backdated_created_time)
        query2 = f"""update IdxSIDBStore SET CreatedTime={backdated_created_time}  where SIDBStoreId={sidbid}"""
        self.log.info("Query: %s", query2)
        self.option_selector.update_commserve_db(query2)
        self.log.info(f"Successfully Updated CreateTime for {sidbid}")

    def delete_jobs(self, data_aging_iterations=1):
        """
        Delete the jobs in job_list and run data aging.

        Args:
            data_aging_iterations   (int)   -   How many times data aging job should be run
        Returns:
                verify_volume_pruned    (bool)  - method that returns a bool on whether vols
                                                    are removed from mmvol table or not
        """
        for idx in range(len(self.backup_job_list)):
            delete_job = self.backup_job_list[idx]
            self.log.info('Deleting backup job [%s] on Primary Copy', delete_job)
            self.primary_copy.delete_job(str(delete_job))
            self.log.info('Deleting backup job [%s] on Secondary Copy', delete_job)
            self.secondary_copy.delete_job(str(delete_job))

        for _ in range(0, data_aging_iterations):
            self.run_data_aging(copy_name=self.primary_copy.copy_name, sp_name=self.storage_policy_name)
            time.sleep((self.prune_process_interval + 1) * 60)
            self.run_data_aging(copy_name=self.secondary_copy.copy_name, sp_name=self.storage_policy_name)
            time.sleep((self.prune_process_interval + 1) * 60)

        return self.verify_volume_pruned()

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("CREATING RESOURCES")
            self.create_resources()
            self.log.info("STARTING BACKUPS")
            self.run_backups()
            self.log.info("STARTING AUXILLARY COPY")
            self.run_auxilary_copy()

            self.log.info("Updating Prune Process Interval.")
            self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS',
                                                 self.prune_process_interval, self.prune_process_interval)
            self.log.info("Updating Maintainence Thread Interval to 5 mins")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES',
                                                 self.maintainence_process_interval,
                                                 self.maintainence_process_interval)

            # Seal DDBs.
            self.log.info("STARTING CASE1: Macropruning by Deleting Jobs!")
            for idx in range(len(self.storage_pool_list)):
                storage_pool_name = self.storage_pool_list[idx].global_policy_name
                storeid = self.sidb_list[idx]
                copy_name = self.storage_pool_list[idx].copy_name
                self.log.info(
                    f"Sealing SIDB Store for storage policy {storage_pool_name} Primary Copy with storeid {storeid}")
                self.dedup_helper.seal_ddb(
                    storage_policy_name=storage_pool_name,
                    copy_name=copy_name,
                    store_id=int(storeid)
                )

            self.log.info("STARTING DELETING JOBS")
            if self.delete_jobs(3):
                self.log.info(f"Volumes entries removed from MMVolume and moved to MMDeletedAF")
            else:
                raise Exception("Volume entries not pruned MMVolume")

            # Verify MMDeletedAF.
            self.verify_mmdeletedaf()

            # verify SIDBStore marked pruneable.
            self.verify_sidb_marked()

            # Verify SIDBStore pruned.
            flag = True
            for _ in range(3):
                if not self.verify_sidbstore_pruned():
                    self.log.info("Starting Data Aging Job.")
                    self.run_data_aging(copy_name=self.primary_copy.copy_name, sp_name=self.storage_policy_name)
                    self.run_data_aging(copy_name=self.secondary_copy.copy_name, sp_name=self.storage_policy_name)
                    self.log.info(f"Sleeping for {self.maintainence_process_interval + 1} min")
                    time.sleep((self.maintainence_process_interval + 1) * 60)
                else:
                    self.log.info("SIDBStore Prune Validation Complete!")
                    flag = False
            if flag:
                raise Exception("SIDBStore Prune Validation Failed.")
            self.log.info("CASE 1: Completed!!")

            # Get new SIDBStore IDs for each store.
            self.sidb_list = []
            for storage_policy_obj in self.sp_list:
                sp_id = storage_policy_obj.storage_policy_id
                primary_storeid = self.dedup_helper.get_sidb_ids(str(sp_id), 'Primary')[0]
                secondary_storeid = self.dedup_helper.get_sidb_ids(str(sp_id), 'SecondaryCopy')[0]
                self.update_createtime(primary_storeid)
                self.update_createtime(secondary_storeid)
                self.sidb_list.append(primary_storeid)
                self.sidb_list.append(secondary_storeid)

            self.log.info(f"New SIDB Store Id List: {self.sidb_list}")

            # Run Backup and aux copy.
            self.log.info("STARTING BACKUPS")
            self.run_backups()
            self.log.info("STARTING AUXILLARY COPY")
            self.run_auxilary_copy()

            self.log.info("STARTING CASE2: Macropruning by Deleting Store")

            self._cleanup()

            # Verify MMVolume Deleted
            volume_pruned = False
            for _ in range(3):
                self.run_data_aging(copy_name=self.primary_copy.copy_name, sp_name=self.storage_policy_name)
                time.sleep((self.prune_process_interval + 1) * 60)
                self.run_data_aging(copy_name=self.secondary_copy.copy_name, sp_name=self.storage_policy_name)
                time.sleep((self.prune_process_interval + 1) * 60)
                if self.verify_volume_pruned():
                    volume_pruned = True
                    break
            if not volume_pruned:
                raise Exception("MMVolume Entries not pruned!")

            # Verify MMDeletedAF.
            self.verify_mmdeletedaf()

            # Verify SIDBStore pruned.
            flag = True
            for _ in range(3):
                if not self.verify_sidbstore_pruned():
                    self.log.info("Starting Data Aging Job.")
                    self.run_data_aging(copy_name=self.primary_copy.copy_name, sp_name=self.storage_policy_name)
                    self.run_data_aging(copy_name=self.secondary_copy.copy_name, sp_name=self.storage_policy_name)
                    self.log.info(f"Sleeping for {self.maintainence_process_interval + 1} min")
                    time.sleep((self.maintainence_process_interval + 1) * 60)
                else:
                    self.log.info("SIDBStore Prune Validation Complete!")
                    flag = False
            if flag:
                raise Exception("SIDBStore Prune Validation Failed.")
            self.log.info("CASE 2: Completed!!")

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def _cleanup(self):
        """Tear down function of this test case"""
        self.log.info(
            "********************** CLEANUP STARTING *************************")
        try:
            # Deleting Content Path
            self.log.info("Deleting content path: %s if exists", self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted content path: %s", self.content_path)

            # Deleting Backupsets
            self.log.info("Deleting BackupSet if exists")
            if self._agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("BackupSet[%s] exists, deleting that", self.backupset_name)
                self._agent.backupsets.delete(self.backupset_name)

            # Deleting Storage Policies
            self.log.info("Deleting Storage Policies if exists")
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Storage Policy[%s] exists, deleting that", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            # Delete Storage Pools.
            self.log.info("Deleting Storage Pools if exists")
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name2):
                self.commcell.storage_pools.delete(self.storage_pool_name2)
                self.log.info(f'Storage pool {self.storage_pool_name2} deleted')
            else:
                self.log.info("Storage pool does not exist.")

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.commcell.storage_pools.delete(self.storage_pool_name)
                self.log.info(f'Storage pool {self.storage_pool_name} deleted')
            else:
                self.log.info("Storage pool does not exist.")
            self.commcell.disk_libraries.refresh()

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception(
                "Error encountered during cleanup: {0}".format(str(exp)))
        self.log.info(
            "********************** CLEANUP COMPLETED *************************")

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("In tear down method ...")

        try:
            self.log.info("Cleaning up the test environment ...")
            self._cleanup()
            self.log.info("Updating Prune Process Interval to Default")
            self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)
            self.log.info("Moving MM Admin Thread Interval back to 15 minutes")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 15, 15)

        except Exception as exp:
            self.log.info("Cleanup failed even after successful execution - %s", str(exp))
