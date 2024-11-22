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
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function for this TC.

    clean_up()              --  deletes all resources created during TC execution.

    create_storage_pool()   --  helper function to create global dedupe storage policy.

    create_resources()      --  generate all required resources for the TC

    generate_backup_data()  --  generate data for to run backup.

    run_backup_util()       --  utility function to generate backup data.

    run_backups()           --  to run backup on given subclient.

    run_data_aging()        -- run data aging job.

    verifyJobAged()         --  verify if the given jobs are maked aged.

    verifyVolumeFlags()     --  verify if volumeflags are marked.

    get_volume_ids()        --  fetch the volume written by the jobs.

    get_volume_pruned()     --  get the volume pruned from history DB.

    verifyMMDeletedAF()     --  verify if entries are pruned from MMDeletedAF.

    verifyMMVolume()        --  verify all volumes pruned from MMVolume table.

    verify_store_sealed()   -- verify given sidb store is selaed.

    verifySIDBStorePruned() --  verify SIDB store is pruned.

    seal_clean_store()      --  prune operation on WORM enabled Store.

    update_job_start_time() --  update the backup job timestamp.

    update_store_creation_time() -- update SIDB store creation time.

    update_max_wormtimestamp()  -- update max WORM timestamp.

    get_active_files_store()    --  returns active store object for files IDA

    run_space_reclaim_job()     -- run a space reclaimation job on the given store.

Design Steps:
    1. Create a library and storage pool
    2. Enable worm and set retention to 2 days and 1 cycle
    3. Create a dependent Storage Policy
    4. Run 4 FULL backups and the 2nd backup job with start new media option enabled.
    5. Change servstarttime in jmbkpstats of the first 3 backup job to 4 days before, so that the job is eligible for pruning
    6. Verify if the first 3 backup jobs are marked as aged.
    7. Run DA job and verify in MMDeletedAF table that volumes for Job1 have Flag 6, volumes for Job2/3 have flags 1.
    8. Run DA job.
    9. Verify entries in MMDeletedAF are pruned.

Sample Input:
           {
                "ClientName": "client name",
                "MediaAgentName": "media agent name",
                "AgentName": "File System",
                "LibraryName" :  "LibraryName" **optional
            }

 Additional Info:
    - If Library name is not provided, TC creates a disk library.
"""

import time
from AutomationUtils import constants
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = 'WORM enabled Store Pruning'
        self.worm_library_name = None
        self.library_name = None
        self.worm_storage_pool_name = None
        self.storage_pool_name = None
        self.worm_storage_policy_name = None
        self.storage_policy_name = None
        self.storage_policy_obj = None
        self.worm_storage_policy_obj = None
        self.worm_subclient_name = None
        self.subclient_name = None
        self.subclient_obj = None
        self.worm_subclient_obj = None
        self.backupset_name = None
        self.worm_disk_mount_path = None
        self.disk_mount_path = None

        self.ma_machine = None
        self.client_machine = None
        self.dedup_helper = None
        self.mm_helper = None
        self.common_util = None
        self.option_selector = None
        self.ddb_path = None
        self.content_path1 = None
        self.content_path2 = None
        self.MediaAgent = None

        self.sidbstoreId = None
        self.backup_job_list = None

        self.prune_process_interval = None
        self.maintainence_process_interval = None

        self.is_user_defined_dedup = None

        self.tcinputs = {
            "MediaAgentName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.MediaAgent = self.tcinputs.get("MediaAgentName")
        self.worm_storage_pool_name = '%s_WORM_storage_%s' % (str(self.id), self.MediaAgent)
        self.storage_pool_name = '%s_storage_%s' % (str(self.id), self.MediaAgent)
        self.worm_storage_policy_name = '%s_WORM_storage_policy_%s' % (str(self.id), self.MediaAgent)
        self.storage_policy_name = '%s_storage_policy_%s' % (str(self.id), self.MediaAgent)
        self.backupset_name = '%s_backupset_%s' % (str(self.id), self.MediaAgent)
        self.worm_subclient_name = '%s_WORM_subclient_%s' % (str(self.id), self.MediaAgent)
        self.subclient_name = '%s_subclient_%s' % (str(self.id), self.MediaAgent)
        self.worm_library_name = self.worm_storage_pool_name
        self.library_name = self.storage_pool_name

        self.backup_job_list = []
        self.backup_job_list2 = []
        self.prune_process_interval = 2
        self.maintainence_process_interval = 5
        if self.tcinputs.get("ddb_path"):
            self.is_user_defined_dedup = True
        else:
            self.is_user_defined_dedup = False

        # Machine & Client object creation
        self.option_selector = OptionsSelector(self.commcell)
        self.dedup_helper = DedupeHelper(self)
        self.mm_helper = MMHelper(self)
        self.common_util = CommonUtils(self)

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
            self.client_machine, size=10 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data on client")

        self.log.info(
            'Selecting drive in the MA machine based on space available')
        ma_drive = self.option_selector.get_drive(
            self.ma_machine, size=10 * 1024)
        if ma_drive is None:
            raise Exception("No free space for generating data on MA")
        self.log.info('selected drive: %s', ma_drive)

        # Create paths.
        self.content_path1 = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata1')
        self.content_path2 = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata2')
        # DDB Path
        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.tcinputs["ddb_path"]
        else:
            if "unix" in self.ma_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_path = self.ma_machine.join_path(
                ma_drive, 'Automation',
                str(self.id), 'partition_path'
            )

        # Library Mount Path
        self.worm_disk_mount_path = self.ma_machine.join_path(ma_drive,
                                                              'Automation', str(self.id), 'WORM_diskMP')
        self.disk_mount_path = self.ma_machine.join_path(ma_drive,
                                                         'Automation', str(self.id), 'diskMP')

    def create_storage_pool(self, storage_pool_name, mount_path, ddb):
        """Create global dedupe storage policy"""
        # Creating Storage Pool.
        if not self.commcell.storage_pools.has_storage_pool(storage_pool_name):
            self.log.info("Configuring Storage Pool ==> %s", storage_pool_name)
            storage_pool = self.commcell.storage_pools.add(
                storage_pool_name, mount_path,
                self.tcinputs['MediaAgentName'], self.tcinputs['MediaAgentName'],
                ddb
            )
            self.log.info("Storage pool configured sucessfully!")
        else:
            self.log.info(f"Configuring Storage Pool: {storage_pool_name} already exists")
            storage_pool = self.commcell.storage_pools.get(storage_pool_name)
        return storage_pool

    def create_resources(self):
        """Create all the resources required to run backups"""

        # Creating Storage Pool
        storage_pool = self.create_storage_pool(self.worm_storage_pool_name, self.worm_disk_mount_path, self.ddb_path)

        # Creating Storage Policy.
        self.log.info("Configuring Dependent Storage Policy ==> %s", self.worm_storage_policy_name)
        if not self.commcell.storage_policies.has_policy(self.worm_storage_policy_name):
            self.worm_storage_policy_obj = self.commcell.storage_policies.add(
                storage_policy_name=self.worm_storage_policy_name,
                library=self.worm_library_name,
                media_agent=self.tcinputs['MediaAgentName'],
                global_policy_name=self.worm_storage_pool_name,
                dedup_media_agent="",
                dedup_path="")
        else:
            self.worm_storage_policy_obj = self.commcell.storage_policies.get(self.worm_storage_policy_name)

        self.log.info("Setting Copy Retention for Primary Copy of [%s] to 2 days 1 cycles",
                      self.worm_storage_policy_name)
        copy_obj = self.worm_storage_policy_obj.get_copy("Primary")
        retention = (2, 1, -1)
        copy_obj.copy_retention = retention

        # Enable WORM On Storage Policy Copy.
        storage_pool.enable_worm_storage_lock(2)

        # Get sidb id for primary copy
        sp_id = self.worm_storage_policy_obj.storage_policy_id
        self.sidbstoreId = self.dedup_helper.get_sidb_ids(str(sp_id), 'Primary')[0]  # Primary Global

        # Create Secound storage Pool for pruning request
        self.create_storage_pool(self.storage_pool_name, self.disk_mount_path, self.ddb_path)
        # Creating dependent storage policy
        self.log.info("Configuring Dependent Storage Policy ==> %s", self.storage_policy_name)
        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            storage_policy_obj = self.commcell.storage_policies.add(
                storage_policy_name=self.storage_policy_name,
                library=self.library_name,
                media_agent=self.tcinputs['MediaAgentName'],
                global_policy_name=self.storage_pool_name,
                dedup_media_agent="",
                dedup_path="")
        else:
            storage_policy_obj = self.commcell.storage_policies.get(self.storage_policy_name)

        # Get primary copy object
        self.storage_policy_obj = storage_policy_obj.get_copy("Primary")

        # Creating a BackupSet.
        self.log.info("Creating BackupSet %s", self.backupset_name)
        backup_set_obj = self.mm_helper.configure_backupset(self.backupset_name)

        # Creating Subclient for WORM SP
        self.log.info("Configuring subclient %s for storage policy %s", self.worm_subclient_name,
                      self.worm_storage_policy_name)
        if not backup_set_obj.subclients.has_subclient(self.worm_subclient_name):
            self.worm_subclient_obj = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.worm_subclient_name,
                self.worm_storage_policy_name,
                self.content_path1)
        else:
            self.worm_subclient_obj = backup_set_obj.subclients.get(self.worm_subclient_name)

        # Create subclient for regular SP
        self.log.info("Configuring subclient %s for storage policy %s", self.subclient_name,
                      self.storage_policy_name)
        if not backup_set_obj.subclients.has_subclient(self.subclient_name):
            self.subclient_obj = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.subclient_name,
                self.storage_policy_name,
                self.content_path2)
        else:
            self.subclient_obj = backup_set_obj.subclients.get(self.subclient_name)

    def generate_backup_data(self, content_path):
        """
        Generates 500MB of uncompressable data
        Args:
            content_path    (str)   -- path where data is to be generated.
        """
        self.log.info(f"Creating 500 MB of data on {content_path}")
        self.option_selector.create_uncompressable_data(
            client=self.tcinputs['ClientName'],
            path=content_path,
            size=0.5
        )

    def run_backups_util(self, subclient, job_type, start_new_media=False):
        """
        run a backup job for the subclient specified in Testcase

        Args:
            subclient       (instance)  instance of subclient object
            job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)
            start_new_media (boolean)   flag to enable/disable start new media option for backup job

        returns job id(int)
        """
        job = subclient.backup(backup_level=job_type,
                               advanced_options={'mediaOpt': {'startNewMedia': start_new_media}})
        self.log.info("starting %s backup job %s...", job_type, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run backup job with error: {0}".format(job.delay_reason)
            )
        self.log.info("backup job: %s completed successfully", job.job_id)

        return job.job_id

    def run_backups(self):
        """ Run full backups on subclient"""
        for count in range(1, 5):
            # Create unique content
            self.log.info(f"Starting FULL Backup Job:- {count}")
            self.generate_backup_data(self.content_path1)
            # Perform Backup
            if count == 2:
                job_id = self.run_backups_util(self.worm_subclient_obj, 'Full', True)
            else:
                job_id = self.run_backups_util(self.worm_subclient_obj, 'Full')

            # Get Volumes written by these jobs.
            self.get_volume_ids(job_id)
            self.backup_job_list.append(job_id)

        # running Full backup on regular SP
        for _ in range(2):
            self.generate_backup_data(self.content_path2)
            job_id = self.run_backups_util(self.subclient_obj, 'Full', True)
            self.backup_job_list2.append(job_id)

    def run_data_aging(self):
        """Run data aging job"""
        data_aging_job = self.mm_helper.submit_data_aging_job()
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

    def verifyJobAged(self, job_list):
        """
        Verify that Jobs are Aged.
        Args:
            job_list    - (list) list of jobs to be verified.
        """
        self.log.info(f"Validating jmjobdatastats table for {job_list}")
        jobs_str = ','.join(job_list)
        query = f"""select agedBy from jmjobdatastats  where jobid in ({jobs_str})"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        aged_flags = [x[0] for x in res]
        self.log.info(f"RESULT: {aged_flags}")
        for flag in aged_flags:
            if flag != '512':
                self.log.info("All jobs are not aged yet!")
                return False
        self.log.info("All jobs are aged successfully!")
        return True

    def verifyVolumeFlags(self):
        """
        Verify that volumeflags for volumes in MMDeletedAF.
        """
        # fetch archFileIds from MMDeletedAF
        pruned_vol = self.get_vol_pruned()
        vol_string = ','.join(pruned_vol)
        # fetch volume flags for these deleted AFs.
        self.log.info(f"Fetching VolumeFlags for {self.sidbstoreId}")
        query = f"""select volumeFlags from mmvolume where volumeid in ({vol_string})"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        flags = [x[0] for x in res]
        self.log.info("Volume Flags: %s", flags)
        aged_counter = 0
        for vol_flag in flags:
            if vol_flag == '6':
                aged_counter += 1
        if aged_counter - len(flags) == 0:
            self.log.info("All Volume Flags are aged(6), no volume with flag(1)!!")
            return False
        self.log.info("Both Volume Flags are available 6 and 1")
        return True

    def get_volume_ids(self, job_id):
        """
        Fetches the Volumes and ArchFile written by a job.
        Args:
            job_id  - (str) job id for which volumes written are to be fetched.
        """
        self.log.info("Fetching volumes to which job have written chunks - [%s]", job_id)
        query = f"""select volumeid from mmvolume where volumeid in (select volumeid from archchunk where 
                id in (select archchunkid from archchunkmapping where jobid = {job_id}))"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        volume_ids = [x[0] for x in res]
        self.log.info(f"Volume written by job id {job_id} are: {volume_ids}")
        self.log.info(f"Fetching ArchFileIds for the jobs: {job_id}")
        query = f"""select archFileId from archChunkMapping where jobId = {job_id}"""
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        archFile = [x[0] for x in res]
        self.log.info(f"ArchFile written by job id {job_id} are: {archFile}")
        return volume_ids

    def get_vol_pruned(self):
        """
        Verify that MMDeletedAF entries for the jobs are pruned.
        """
        self.log.info(f"Getting volume Ids in MMDeletedAF for {self.sidbstoreId}")
        query = f"""select Distinct(VolumeId) from HistoryDB.dbo.MMDeletedAFPruningLogs where SIDBStoreId = {self.sidbstoreId}"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        volIds = [x[0] for x in res if x[0] != 0]
        self.log.info(f"ArchFiles in MMDeletedAF for store: {self.sidbstoreId} are: {volIds}")
        return volIds

    def verifyMMDeletedAF(self):
        """
        Verify that MMDeletedAF entries for the jobs are pruned.
        """
        self.log.info(f"Validating MMDeletedAF table for {self.sidbstoreId}")
        query = f"""select count(archFileId) from MMDeletedAF where SIDBStoreId = {self.sidbstoreId}"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT: {res}")
        if int(res) != 0:
            return False
        self.log.info("MMDeletedAF entries pruned successfully")
        return True

    def verifyMMVolume(self):
        """
        Verify all volumes in MMVolume table are pruned for the SIDB store.
        """
        self.log.info(f"Verifying all volumes are pruned from MMVolume table for {self.sidbstoreId}")
        query = f"select count(VolumeId) from MMVolume where SIDBStoreID = {self.sidbstoreId}"
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT: {res}")
        if int(res) != 0:
            self.log.info(f"There are still Volume entries in MMVolume for SIDBStore ID: {self.sidbstoreId}")
            return False
        return True

    def verify_store_sealed(self):
        """
        Verify if the sidb store is marked sealed.
        """
        self.log.info(f"Verifying store sealed for store Id: {self.sidbstoreId}")
        query = f"select sealedReason from IdxSIDBStore where SIDBStoreID = {self.sidbstoreId}"
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT: {res}")
        if int(res) == 0:
            return False
        self.log.info("SIDBStore sealed successfully")
        return True

    def verifySIDBStorePruned(self):
        """
        Verify that SIDB Store is pruned successfully.
        """
        self.log.info(f"Validating SIDBStore for {self.sidbstoreId}")
        query1 = f"""select count(sidbstoreid) from idxsidbstore where sidbstoreid = {self.sidbstoreId}"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT QUERY1: {res}")
        if int(res) != 0:
            self.log.info("IdxSIDBStore entries are not pruned!!")
            return False

        query2 = f"""select count(IdxAccessPathId) from IdxAccessPath where idxaccesspathid in 
        (select idxaccesspathid from IdxSIDBSubStore where sidbstoreid = {self.sidbstoreId})"""
        self.log.info("Query: %s", query2)
        self.csdb.execute(query2)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT QUERY2: {res}")
        if int(res) != 0:
            self.log.info("IdxAccessPath entries are not pruned!")
            return False

        query3 = f"""select count(IdxCacheId) from IdxCache where IdxCacheId in 
        (select IdxCacheId from IdxSIDBSubStore where sidbstoreid = {self.sidbstoreId})"""
        self.log.info("Query: %s", query3)
        self.csdb.execute(query3)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT QUERY3: {res}")
        if int(res) != 0:
            self.log.info("IdxSIDBSubStore entries are not pruned for all stores!")
            return False
        self.log.info("SIDB Store Pruned Successful!")
        return True

    def seal_clean_store(self, jobs_to_be_aged):
        """
        Perform pruning for WORM enabled SIDB Store.
        Args:
            jobs_to_be_aged     (list) -- list of jobs on WORM store to be aged.
        """
        self.log.info(f"Updating SIDB Store {self.sidbstoreId} First job Start Time!")
        self.update_store_creation_time(self.sidbstoreId)
        store_sealed = False
        for _ in range(3):
            time.sleep((self.prune_process_interval + 1) * 60)
            self.log.info(f"Waiting for Store ID: {self.sidbstoreId} to be sealed!!")
            if self.verify_store_sealed():
                store_sealed = True
                break
        if not store_sealed:
            raise Exception(f"SIDBStore ID: {self.sidbstoreId} was not sealed!!")
        # update the jobs start time.
        for job in jobs_to_be_aged:
            self.update_job_start_time(job)

        # Verify Job aged
        job_aged = False
        for _ in range(3):
            # Running Data Aging Job.
            self.run_data_aging()
            time.sleep((self.prune_process_interval + 1) * 60)
            if self.verifyJobAged(jobs_to_be_aged):
                job_aged = True
                break
        if not job_aged:
            raise Exception(f"Jobs are not pruned!")

        # Verify MMDeletedAF entries are pruned.
        # deleting a job to send pruning request
        job_id = self.backup_job_list2[1]
        self.log.info(f"Deleting Job ID: {job_id}")
        self.storage_policy_obj.delete_job(str(job_id))
        entries_pruned = False
        for _ in range(3):
            self.run_data_aging()
            self.log.info(f"Sleeping for {self.prune_process_interval + 1} mins")
            time.sleep((self.prune_process_interval + 1) * 60)
            if self.verifyMMDeletedAF():
                entries_pruned = True
                break
        if not entries_pruned:
            raise Exception("MMDeleted entried Volume Flag not invalid!")

        self.update_max_wormtimestamp()
        for _ in range(3):
            self.run_data_aging()
            time.sleep((self.maintainence_process_interval + 1) * 60)
            if self.verifyMMVolume():
                self.log.info(f"MMVolume entries are pruned for sidbstore store id: {self.sidbstoreId}")
                break

        # Verify SIDBStore pruned.
        flag = True
        for _ in range(3):
            if not self.verifySIDBStorePruned():
                self.log.info("Starting Data Aging Job.")
                self.run_data_aging()
                self.log.info(f"Sleeping for {self.maintainence_process_interval + 1} min")
                time.sleep((self.maintainence_process_interval + 1) * 60)
            else:
                self.log.info("SIDBStore Prune Validation Complete!")
                flag = False
        if flag:
            raise Exception("SIDBStore Prune Validation Failed.")

    def update_job_start_time(self, job_id):
        """
        Update create time for the given SIDB store.
        Args: 
            job_id      (int)   -- job if for which start time is to be updated. 
        """
        query1 = f"""select servStartDate from JMBkpStats where jobId = {job_id}"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        start_time = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"RESULT: {start_time}")
        start_time = start_time - 86400 * 4
        self.log.info("4 Day Backed Time for Job %s is %s", job_id, start_time)
        query2 = f"""update JMBkpStats set servStartDate = {start_time} where jobid = {job_id}"""
        self.log.info("Query: %s", query2)
        self.option_selector.update_commserve_db(query2)
        self.log.info(f"Successfully Updated start time for {job_id}")

    def update_store_creation_time(self, sidbId):
        """
        Update create time for the given SIDB store.
        Args:  
            sidbID      (int)   -- SIDB Store id for which creation time is to be updated. 
        """
        query1 = f"""select CreatedTime from idxsidbstore where sidbstoreid = {sidbId}"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        created_time = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"RESULT: {created_time}")
        backdated_created_time = created_time - (86400 * 20)
        self.log.info("20 Day Backed CreatedTime for SIDB store %s is %s", sidbId, backdated_created_time)
        query2 = f"""update IdxSIDBStore SET CreatedTime={backdated_created_time}  where SIDBStoreId={sidbId}"""
        self.log.info("Query: %s", query2)
        self.option_selector.update_commserve_db(query2)
        self.log.info(f"Successfully Updated CreateTime for {sidbId}")

    def update_max_wormtimestamp(self):
        """
        update the max wormtimestamp.
        """
        query1 = f"""select intVal, longlongVal from MMEntityProp where EntityId = {self.sidbstoreId} and propertyName = 'DDBMaxWORMLockTimestamp'"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        result = self.csdb.fetch_one_row()
        int_val, long_val = int(result[0]), int(result[1])
        if int_val == 0:
            self.log.info(f"RESULT: {long_val}")
            start_time = long_val - 86400 * 20
            update_query = f"""update MMEntityProp set longlongVal = {start_time} where EntityId = {self.sidbstoreId} and propertyName = 'DDBMaxWORMLockTimestamp'"""
        else:
            self.log.info(f"RESULT: {int_val}")
            start_time = int_val - 86400 * 20
            update_query = f"""update MMEntityProp set intVal = {start_time} where EntityId = {self.sidbstoreId} and propertyName = 'DDBMaxWORMLockTimestamp'"""

        self.log.info("4 Day Backed Time is %s", start_time)
        self.log.info("Query: %s", update_query)
        self.option_selector.update_commserve_db(update_query)
        self.log.info(f"Successfully Updated max worm timestamp for {self.sidbstoreId}")

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.worm_storage_pool_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def run_space_reclaim_job(self, store, with_ocl=False):
        """
        runs space reclaim job on the provided store object

        Args:
            store (object) - store object wher espace reclaim job needs to run

            with_ocl (bool) - set True if the job needs to run with OCL phase

        Returns:
            (object) job object for the space reclaim job
        """
        space_reclaim_job = store.run_space_reclaimation(level=4, clean_orphan_data=with_ocl)
        self.log.info("Space reclaim job with OCL[%s]: %s", with_ocl, space_reclaim_job.job_id)
        timer = 0
        while True and timer<300:
            status = space_reclaim_job.status.lower()
            self.log.info(f"Space reclaim Job Status: {status}")
            if status in ('pending', 'failed'):
                delay_reason = space_reclaim_job.delay_reason
                if 'as WORM storage lock is enabled' in delay_reason:
                    self.log.info("Case: Space reclaim job failed as expected on WORM Store!!")
                self.log.info("Negative Case: Failed to run DDB Space reclaim with error: {0}".format(
                    space_reclaim_job.delay_reason))
                if status == 'pending':
                    space_reclaim_job.kill()
                    self.log.info("Case: Job Killed Successfully")
                break
            if status == 'completed':
                self.log.info("Case: Job completed is not expected!!")
                raise Exception(
                    "Case: Test case failed for job {0}.".format(space_reclaim_job.job_id))
            time.sleep(5)
            timer+=5
        if timer == 300:
            raise Exception(f"Case: Job did not reach expected status even after 5 mins. Please check manually {space_reclaim_job.job_id}")
        return space_reclaim_job

    def get_jobs_to_prune(self):
        """
        Returns all jobs on WORM enabled store that needs to be pruned.
        """
        self.log.info(f"Getting jobs on store {self.sidbstoreId}")
        query = f"""select jobId from JMJobDataStats JMS
                join archGroupCopy AGC on AGC.Id = JMS.archGrpCopyId 
                where AGC.SIDBStoreId = {self.sidbstoreId}"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        job_ids = [x[0] for x in res if x[0] != 0 and x[0] not in self.backup_job_list]
        job_ids.append(self.backup_job_list[-1])
        self.log.info(f"Jobs on store left to be aged: {self.sidbstoreId} are: {job_ids}")
        return job_ids


    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("CLEANING UP PREVIOUS RUN")
            self._cleanup()
            self.log.info("CREATING RESOURCES")
            self.create_resources()
            self.log.info("STARTING BACKUPS")
            self.run_backups()
            store = self.get_active_files_store()
            all_jobs_to_prune = self.get_jobs_to_prune()

            # Update starttime of the jobs and validate if jobs are pruned.
            for index in range(3):
                job_id = self.backup_job_list[index]
                self.log.info(f"Updating Start Time for Job {job_id}")
                self.update_job_start_time(job_id)

            # Verify Jobs marked are aged and Volume Flags are set in MMDeletedAF.
            job_aged = False
            for _ in range(3):
                # Running Data Aging Job.
                self.run_data_aging()
                if self.verifyJobAged(self.backup_job_list[:3]):
                    self.log.info("All Jobs are aged!!")
                    job_aged = True
                    break

            if not job_aged:
                raise Exception(f"Jobs are not marked aged!!")

            # Update Prune Process Interval
            self.log.info("Updating Prune Process Interval to 15")
            self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS',
                                                 self.prune_process_interval,
                                                 self.prune_process_interval)

            # Update Maintainence Process Interval.
            self.log.info("Updating Maintainence Thread Interval to 5 mins")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES',
                                                 self.maintainence_process_interval,
                                                 self.maintainence_process_interval)

            # Verify MMDeletedAF entries are pruned.
            # deleting a job to send for pruning
            job_id = self.backup_job_list2[0]
            self.log.info(f"Deleting Job ID: {job_id}")
            self.storage_policy_obj.delete_job(str(job_id))
            entries_pruned = False
            for _ in range(3):
                self.run_data_aging()
                self.log.info(f"Sleeping for {self.prune_process_interval + 1} mins")
                time.sleep((self.prune_process_interval + 1) * 60)
                if self.verifyMMDeletedAF():
                    entries_pruned = True
                    break
            if not entries_pruned:
                self.log.error("MMDeletedAF entried pruned!!!!!")
                # raise Exception("MMDeleted entried Volume Flag not invalid!")

            # Verify Volume Flags for pruned volumes.
            if not self.verifyVolumeFlags():
                self.log.error(f"Volume Flag validation failure")
                raise Exception("MMVolume Flags validation failure!!")
            self.log.info("Verified Volume Flags")

            # Run Space reclaimation job on WORM Copy
            self.run_space_reclaim_job(store)

            # seal store and verify jobs are macropruned.
            self.seal_clean_store(all_jobs_to_prune)

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
            self.log.info("Deleting content path: %s if exists", self.content_path1)
            if self.client_machine.check_directory_exists(self.content_path1):
                self.client_machine.remove_directory(self.content_path1)
                self.log.info("Deleted content path: %s", self.content_path1)

            self.log.info("Deleting content path: %s if exists", self.content_path2)
            if self.client_machine.check_directory_exists(self.content_path2):
                self.client_machine.remove_directory(self.content_path2)
                self.log.info("Deleted content path: %s", self.content_path2)

            # Deleting Backupsets
            self.log.info(f"Deleting BackupSet {self.backupset_name}, if exists")
            if self._agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("BackupSet[%s] exists, deleting that", self.backupset_name)
                self._agent.backupsets.delete(self.backupset_name)

            # Deleting Storage Policies
            if self.commcell.storage_policies.has_policy(self.worm_storage_policy_name):
                self.log.info("Storage Policy[%s] exists, deleting that", self.worm_storage_policy_name)
                self.commcell.storage_policies.delete(self.worm_storage_policy_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Storage Policy[%s] exists, deleting that", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            # Delete Storage Pools.
            self.log.info("Deleting Storage Pools if exists")
            if self.commcell.storage_policies.has_policy(self.worm_storage_pool_name):
                self.log.info("Storage Policy[%s] exists, deleting that", self.worm_storage_pool_name)
                self.commcell.storage_policies.delete(self.worm_storage_pool_name)

            self.log.info("Deleting Storage Pools if exists")
            if self.commcell.storage_policies.has_policy(self.storage_pool_name):
                self.log.info("Storage Policy[%s] exists, deleting that", self.storage_pool_name)
                self.commcell.storage_policies.delete(self.storage_pool_name)

            # Delete Library If Created.
            self.commcell.refresh()
            if not self.tcinputs.get("LibraryName") and self.commcell.disk_libraries.has_library(
                    self.worm_library_name):
                self.commcell.disk_libraries.delete(self.worm_library_name)
                self.log.info("Deleted library: %s", self.worm_library_name)

            if not self.tcinputs.get("LibraryName") and self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
                self.log.info("Deleted library: %s", self.library_name)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))

        self.log.info(
            "********************** CLEANUP COMPLETED *************************")

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("In tear down method ...")

        try:
            if self.status != constants.FAILED:
                self.log.info("Testcase shows successful execution ...")
            else:
                self.log.warning("Testcase shows failure in execution, not cleaning up the test environment ...")
            self._cleanup()
            self.log.info("Updating Prune Process Interval to Default")
            self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)
            self.log.info("Moving MM Admin Thread Interval back to 15 minutes")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 15, 15)

        except Exception as exp:
            self.log.info("Failure in tear down function - %s", str(exp))
