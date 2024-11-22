# -*- coding: utf-8 -*-

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
    __init__()                         --  Initializes test case class object

    setup()                            --  Setup function of this test case

    get_ddb_backup_subclient()         --  Gets the ddb_backup_subclient for the MA of our testcase

    reassociate_ddb_backup_subclient() --  Re-associates DDB Backup SubClient to common sp and runs a DDB Backup

    clean_up()                  --  Cleans Up the Created Entities

    create_resources()          --  Creates the required resources/ defines paths for this testcase

    create_content_sc()         --  Generates and Sets content for the subclient

    get_active_files_store()    --  Returns active store object for files iDA

    select_chunks_to_alter()    --  Selects Chunks at random that need to be altered

    validate_csdb_info()        --  Runs the CSDB Validation

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this test case

TcInputs to be passed in JSON File:
    "53910": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "MediaAgentName": Name of a MediaAgent - we create Libraries here
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "library_name"  : Name of Existing Library to be Used
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
        "num_subclients_tc" : Number of SubClients to be created
        "test_case_factor"  : Scale Factor for Content Size of SubClients
    }

Steps:

1: CleanUp older Run Entities and create New Entities: Library, SP, SubClient(s). Disable Ransomware Protection on MA

2: Run Backups for SubClients and Wait for Completion of Jobs

3: Add Random data to DDB Path(for backup to run longer) and Run 2 DDB Backup Jobs(j1,j2)

5: Verify that the idxsidbsidbsubstore and idxsidbsubstorebackupinfo are set to  j2, j1 respectively

6: Get the chunks created by 2nd(Latest) DDB Backup Job and delete few of them

7: Wait for SIDB to go down and mark store for recovery. Run Recon Job

8: Make sure that Recon Job failed

9: Verify that the idxsidbsidbsubstore and idxsidbsubstorebackupinfo are updated to j1 and '' respectively

10: Run Recon Job and wait for completion of job

11: Verify that the idxsidbsidbsubstore and idxsidbsubstorebackupinfo are set to j1 and '' respectively

12: If all Validations Passed, cleanup the entities
"""


from MediaAgents.MAUtils import mahelper
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Retain multiple DDB backup jobs - corrupt chunks for latest ddb backup"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.mount_path = None
        self.content_path = None
        self.dedup_store_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None

        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None

        self.mm_helper = None
        self.dedup_helper = None

        self.client_machine = None
        self.media_agent_machine = None
        self.ransomware_initial_status = True

        self.store = None
        self.library = None
        self.storage_policy = None
        self.backup_set = None
        self.subclients = None
        self.ddbbackup_subclient = None

        self.is_user_defined_lib = False
        self.is_user_defined_mount_path = False
        self.is_user_defined_dedup = False

        self.num_subclients = None
        self.test_case_factor = None
        self.ma_name = None

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mount_path = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.ma_name = self.tcinputs["MediaAgentName"]
        suffix = f'{self.tcinputs.get("MediaAgentName")[::-1]}{self.tcinputs.get("ClientName")[::-1]}'

        self.backupset_name = f"{self.id}_BS_{suffix}"
        self.subclient_name = f"{self.id}_SC_{suffix}"
        self.storage_policy_name = f"{self.id}_SP_{suffix}"

        self.num_subclients = int(self.tcinputs.get("num_subclients_tc", "1"))
        self.test_case_factor = int(self.tcinputs.get("test_case_factor", "1"))

        self.client_machine = machine.Machine(self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(self.tcinputs.get("MediaAgentName"), self.commcell)

        self.mm_helper = mahelper.MMHelper(self)
        self.dedup_helper = mahelper.DedupeHelper(self)

        drive_path_client = self.dedup_helper.option_selector.get_drive(self.client_machine, 25*1024)
        drive_path_media_agent = self.dedup_helper.option_selector.get_drive(self.media_agent_machine, 25*1024)
        self.testcase_path_client = self.client_machine.join_path(drive_path_client, f'test_{self.id}')
        self.testcase_path_media_agent = self.media_agent_machine.join_path(drive_path_media_agent, f'test_{self.id}')

        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = f'{self.id}_Lib_{suffix}'
            if not self.is_user_defined_mount_path:
                self.mount_path = self.media_agent_machine.join_path(self.testcase_path_media_agent, 'MP')
            else:
                self.log.info("custom mount_path supplied")
                self.mount_path = self.media_agent_machine.join_path(
                    self.tcinputs.get('mount_path'), f'test_{self.id}', 'MP')

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs.get("dedup_path"),
                                                                       f'test_{self.id}', "DDB")
        else:
            if "unix" in self.media_agent_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.dedup_store_path = self.media_agent_machine.join_path(self.testcase_path_media_agent, "DDB")

    def get_ddb_backup_subclient(self):
        """Gets the ddb_backup_subclient for the MA of our testcase"""

        # check if DDBBackup subclient exists, if it doesn't fail the testcase
        default_backup_set = self.commcell.clients.get(
            self.tcinputs.get("MediaAgentName")).agents.get("File System").backupsets.get("defaultBackupSet")

        if not default_backup_set.subclients.has_subclient("DDBBackup"):
            raise Exception("DDBBackup SubClient does not exist:FAILED")

        self.log.info("DDBBackup subclient exists")
        self.log.info("Storage policy associated with the DDBBackup subclient is %s",
                      default_backup_set.subclients.get("DDBBackup").storage_policy)
        return default_backup_set.subclients.get("DDBBackup")

    def reassociate_ddb_backup_subclient(self):
        """Re-associates DDB Backup SubClient to common sp and runs a DDB Backup
        """
        mount_path = self.media_agent_machine.join_path(self.testcase_path_media_agent,
                                                        f"ddb_cases_common_files_{self.ma_name}",
                                                        f"mount_path_common_lib_{self.ma_name}")
        dedup_store_path = self.media_agent_machine.join_path(self.testcase_path_media_agent,
                                                              f"ddb_cases_common_files_{self.ma_name}",
                                                              f"dedup_path_common_sp_{self.ma_name}")

        # create common library
        self.log.info("creating common lib, sp and re-associating the ddb subclient")
        self.library = self.mm_helper.configure_disk_library(
            f"common_lib_ddb_cases_{self.ma_name}", self.tcinputs.get("MediaAgentName"), mount_path)

        # create common SP
        self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
            f"common_sp_ddb_cases_{self.ma_name}", f"common_lib_ddb_cases_{self.ma_name}",
            self.tcinputs.get("MediaAgentName"),
            dedup_store_path, self.tcinputs.get("MediaAgentName"))

        self.ddbbackup_subclient.storage_policy = f"common_sp_ddb_cases_{self.ma_name}"
        self.log.info("running ddb backup job")
        cleanup_backup_job = self.ddbbackup_subclient.backup("FULL")
        self.log.info("DDB Backup job: %s", str(cleanup_backup_job.job_id))
        if not cleanup_backup_job.wait_for_completion():
            raise Exception(f"Job[{cleanup_backup_job.job_id}] Failed. JPR [{cleanup_backup_job.delay_reason}]")
        self.log.info("DDB Backup job [%s] completed", cleanup_backup_job.job_id)

    def clean_up(self):
        """Cleans Up the Created Entities"""
        self.log.info("********* Clean up Started **********")
        try:
            self.log.info("Deleting BackupSet if Exists")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("BackupSet[%s] deleted", self.backupset_name)

            # in case the storage policy of this testcase gets associated to the DDB SubClient
            # will cause error in clean up
            # create a new common policy - leave it behind - delete the testcase storage policy

            self.ddbbackup_subclient = self.get_ddb_backup_subclient()
            if self.ddbbackup_subclient.storage_policy == self.storage_policy_name:
                self.log.info("DDB Backup subclient is associated to TC SP. Trying to re-associate it")
                self.reassociate_ddb_backup_subclient()

            self.log.info("Deleting Storage Policy If Exists")
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Storage policy[%s] deleted", self.storage_policy_name)

            if not self.is_user_defined_lib:
                self.log.info("Deleting Library If Exists")
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
                    self.log.info("Library[%s] deleted", self.library_name)

            self.log.info("********* Clean up Completed **********")
        except Exception as exp:
            self.log.warning("********* Clean up Failed. Error[%s] **********", str(exp))

    def create_resources(self):
        """Creates the required resources/ defines paths for this testcase"""
        self.log.info("Deleting Content Path Directory if already exists(from older runs)")
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.log.info("Creating Content Path Directory for this run")
        self.client_machine.create_directory(self.content_path)

        # create Library, SP, SC
        if self.is_user_defined_lib:
            self.library = self.commcell.disk_libraries.get(self.tcinputs.get("library_name"))
        else:
            self.library = self.mm_helper.configure_disk_library(
                library_name=self.library_name, ma_name=self.tcinputs.get("MediaAgentName"), mount_path=self.mount_path)

        self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
            storage_policy_name=self.storage_policy_name,
            library_name=self.library_name, ma_name=self.tcinputs.get("MediaAgentName"),
            ddb_path=self.dedup_store_path, ddb_ma_name=self.tcinputs.get("MediaAgentName"))

        # create backupset
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)

        # create subclient list
        self.subclients = []
        for index in range(self.num_subclients):
            subclient = self.mm_helper.configure_subclient(backupset_name=self.backupset_name,
                                                           subclient_name=f'{self.subclient_name}_{index}',
                                                           storage_policy_name=self.storage_policy_name)
            self.subclients.append(subclient)

    def create_content_sc(self, size, subclient):
        """Generates and Sets content for the subclient
        Args:
            size        (float)     :   data needed in GB (float)

            subclient   (SubClient) :   subclient object
        """
        if self.dedup_helper.option_selector.create_uncompressable_data(
                self.client_machine,
                self.client_machine.join_path(self.content_path, subclient.name), size * self.test_case_factor, 1):
            self.log.info("Data Generation Completed")
        else:
            raise Exception("Couldn't generate data")

        self.log.info("Set SubClient Content to the generated Data: %s", subclient.name)
        subclient.content = [self.client_machine.join_path(self.content_path, subclient.name)]

    def get_active_files_store(self):
        """Returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.storage_policy_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def select_chunks_to_alter(self, chunk_list):
        """Selects Chunks at random that need to be altered

        Args:
            chunk_list (list): List of chunks
        Returns:
            (set):  Set of indices of the chunks on which alterations will be done
        """
        limit = 5
        effected_chunks = set()
        log_line = ''
        for index in range(len(chunk_list)):
            if index not in effected_chunks:
                effected_chunks.add(index)
                log_line += f'{chunk_list[index][0]}, '
            if len(effected_chunks) >= limit:
                break
        self.log.info('Effected Chunks : %s', log_line)
        return effected_chunks

    def validate_csdb_info(self, prior_recon, ddb_job_1, ddb_job_2):
        """Runs the CSDB Validation

        Args:
            prior_recon (int):  Stage of Validation. (0: Prior Recon/ 1: Post Recon 1/ 2: Post Recon 2)

            ddb_job_1   (Job):  Job Object of 1st DDB Backup Job

            ddb_job_2   (Job):  Job Object of 2nd DDB Backup Job
        """
        self.log.info("*** Running CSDB Validation ***")
        query = f"select LastSnapJobId from IdxSIDBSubStore where SubStoreId = {self.store.all_substores[0][0]}"
        self.log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        last_snap_job_id = self.csdb.fetch_one_row()[0]
        self.log.info("LastSnapJobId: {%s}", str(last_snap_job_id))

        query = f"select distinct LastSnapJobId from IdxSIDBSubStoreBackupInfo " \
                f"where SubStoreId = {self.store.all_substores[0][0]} " \
                f"order by LastSnapJobId desc"
        self.log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        other_ddb_bkp_job_id = self.csdb.fetch_one_row()[0]
        self.log.info("Result: {%s}", str(other_ddb_bkp_job_id))

        if prior_recon == 0 and (int(last_snap_job_id) == int(ddb_job_2.job_id))\
                and (int(other_ddb_bkp_job_id) == int(ddb_job_1.job_id)):
            self.log.info("Validation PASS: Prior to recon, values are set correctly")
            self.log.info("Latest DDB Bkp Job: {%s}, IdxSidbSubStore LastSnapJobId: {%s}",
                          ddb_job_2.job_id, last_snap_job_id)
            self.log.info("Older DDB Bkp Job: {%s}, IdxSidbSubStoreBackupInfo LastSnapJobId: {%s}",
                          ddb_job_1.job_id, other_ddb_bkp_job_id)
        elif prior_recon == 1 and (int(last_snap_job_id) == int(ddb_job_1.job_id))\
                and (other_ddb_bkp_job_id == ''):
            self.log.info("Validation PASS: Post recon job 1, values are set correctly")
            self.log.info("Older DDB Bkp Job: {%s}, IdxSidbSubStore LastSnapJobId: {%s}",
                          ddb_job_1.job_id, last_snap_job_id)
            self.log.info("IdxSidbSubStoreBackupInfo LastSnapJobId: {%s}", other_ddb_bkp_job_id)
        elif prior_recon == 2 and (int(last_snap_job_id) == int(ddb_job_1.job_id))\
                and (other_ddb_bkp_job_id == ''):
            self.log.info("Validation PASS: Post recon job 2, values are set correctly")
            self.log.info("Older DDB Bkp Job: {%s}, IdxSidbSubStore LastSnapJobId: {%s}",
                          ddb_job_1.job_id, last_snap_job_id)
            self.log.info("IdxSidbSubStoreBackupInfo LastSnapJobId: {%s}", other_ddb_bkp_job_id)
        else:
            raise Exception("Validation FAIL: The Backup Info is not set correctly in CSDB")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Update MMConfig to retain multiple DDB Backups to 1")
            self.mm_helper.update_mmconfig_param('MMCONFIG_RETAIN_NO_OF_DDB_BACKUPS', 1, 1)

            self.log.info("Update MMConfig and disable Ransomware Protection on MA")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)
            media_agent_obj = self.commcell.media_agents.get(self.tcinputs.get("MediaAgentName"))
            self.ransomware_initial_status = self.mm_helper.ransomware_protection_status(media_agent_obj.media_agent_id)
            media_agent_obj.set_ransomware_protection(False)
            self.log.info("Completed disabling Ransomware Protection")
            # clean up previous run config, Create resources.
            self.clean_up()
            self.create_resources()

            self.log.info("Getting Store, DDB subclient objects")
            self.store = self.get_active_files_store()
            self.ddbbackup_subclient = self.get_ddb_backup_subclient()
            self.log.info("Re-Associating DDB Backup subclient to [%s]", self.storage_policy_name)
            self.ddbbackup_subclient.storage_policy = self.storage_policy_name

            self.log.info("Update MMConfig and retain multiple DDB Backups to 4")
            self.mm_helper.update_mmconfig_param('MMCONFIG_RETAIN_NO_OF_DDB_BACKUPS', 1, 4)
            self.log.info("Generate content and Run Full Backup Jobs on SubClients")
            jobs = []
            for subclient in self.subclients:
                self.create_content_sc(size=1.5, subclient=subclient)
                job = subclient.backup("FULL")
                self.log.info("Backup Job[%s] started", job.job_id)
                jobs.append(job)
            self.log.info("Backup Jobs initiated. Wait for Jobs to complete")
            for job in jobs:
                if not job.wait_for_completion():
                    raise Exception(f'Backup Job[{job.job_id}] Failed. JPR[{job.delay_reason}]')
                self.log.info('Backup Job[%s] Completed', job.job_id)

            self.log.info('Adding random data to DDB Path for DDB Backup to last longer')
            dummy_data_dir = self.media_agent_machine.join_path(
                self.store.all_substores[0][1], 'CV_SIDB', '2', str(self.store.store_id), 'Split00', 'dummy_data_dir')
            self.media_agent_machine.create_directory(dummy_data_dir)
            self.dedup_helper.option_selector.create_uncompressable_data(
                client=self.media_agent_machine, path=dummy_data_dir, size=5.0,
                num_of_folders=0, suffix=".idx", delete_existing=True)

            self.log.info("Starting DDB Backup Job 1")
            ddb_backup_job1 = self.ddbbackup_subclient.backup("FULL")
            self.log.info("DDB Backup Job 1[%s] started", ddb_backup_job1.job_id)
            if not ddb_backup_job1.wait_for_completion():
                raise Exception(f'DDB Backup Job 1[{ddb_backup_job1.job_id}] Failed.'
                                f' JPR[{ddb_backup_job1.delay_reason}]')
            self.log.info("DDB Backup Job 1[%s] completed", ddb_backup_job1.job_id)

            self.log.info("Starting DDB Backup Job 2")
            ddb_backup_job2 = self.ddbbackup_subclient.backup("FULL")
            self.log.info("DDB Backup Job 2[%s] Started", ddb_backup_job2.job_id)
            if not ddb_backup_job2.wait_for_completion():
                raise Exception(f'DDB Backup Job 2[{ddb_backup_job2.job_id}] Failed.'
                                f' JPR[{ddb_backup_job2.delay_reason}]')
            self.log.info("DDB Backup Job 2[%s] completed", ddb_backup_job2.job_id)

            self.validate_csdb_info(0, ddb_backup_job1, ddb_backup_job2)

            self.log.info("Fetching the Chunks for 2nd DDB Backup Job from the DB")
            chunks = self.mm_helper.get_chunks_for_job(ddb_backup_job2.job_id,
                                                       self.storage_policy.get_copy('Primary').copy_id,
                                                       order_by=6)
            chunk_paths = []
            for row in chunks:
                chunk_paths.append((row[3], self.media_agent_machine.join_path(row[0], row[1], 'CV_MAGNETIC',
                                                                               row[2], f'CHUNK_{row[3]}')))

            effected_chunks = self.select_chunks_to_alter(chunk_paths)
            # identify volumes and remove delete deny rule on folders
            volume_paths = set()
            for index in effected_chunks:
                volume_paths.add(chunk_paths[index][1].split(f'{self.media_agent_machine.os_sep}CHUNK')[1])
            for volume in volume_paths:
                self.media_agent_machine.modify_ace('Everyone', volume, 'DeleteSubdirectoriesAndFiles',
                                                    'Deny', remove=True, folder=True)
                self.media_agent_machine.modify_ace('Everyone', volume, 'Delete',
                                                    'Deny', remove=True, folder=True)
            self.log.info("Deleting Chunks")
            for index in effected_chunks:
                self.media_agent_machine.remove_directory(chunk_paths[index][1])

            self.log.info("Making sure that SIDB Process is down")
            if not self.dedup_helper.wait_till_sidb_down(
                    str(self.store.store_id), self.commcell.clients.get(self.tcinputs.get("MediaAgentName")), timeout=300):
                raise Exception("Timeout waiting for SIDB process to go down")
            self.log.info("SIDB Process is down on MA")

            self.log.info("Updating MM Admin thread interval to 1 hr, for it to not start a recon automatically")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 60)
            self.log.info("Marking the Store for Recovery")
            substore_obj = self.store.get(self.store.all_substores[0][0])
            substore_obj.mark_for_recovery()
            self.log.info(
                f"-marked store[{substore_obj.store_id}]: substore[{substore_obj.substore_id}] for recovery")

            self.log.info("*** VALIDATION 2: Starting a Reconstruction Job. Expecting it to Fail ***")
            recon_job = self.store.recover_deduplication_database(full_reconstruction=False)
            self.log.info("DDB Reconstruction Job[%s] started. Waiting for job to finish.", recon_job.job_id)
            if not recon_job.wait_for_completion() and recon_job.status.lower() == 'failed':
                self.log.info('Validation Result: PASS: DDB Reconstruction Job[%s] Failed as expected. JPR[%s]',
                              recon_job.job_id, recon_job.delay_reason)
            else:
                raise Exception(f"Validation Result: FAIL: DDB Reconstruction Job[{recon_job.job_id}] hasn't failed")

            self.validate_csdb_info(1, ddb_backup_job1, ddb_backup_job2)
            self.log.info('*** VALIDATION 4: Starting another Recon Job. Expecting it to Complete Successfully ***')
            recon_job = self.store.recover_deduplication_database(full_reconstruction=False)
            self.log.info("DDB Reconstruction Job[%s] started. Waiting for job to complete.", recon_job.job_id)
            if not recon_job.wait_for_completion():
                raise Exception(f'Validation Result: FAIL: DDB Reconstruction Job[{recon_job.job_id}] Failed.'
                                f' JPR[{recon_job.delay_reason}]')
            self.log.info("Validation Result: PASS: DDB Reconstruction Job[%s] completed", recon_job.job_id)

            self.validate_csdb_info(2, ddb_backup_job1, ddb_backup_job2)
            self.log.info("*** Finished all validations in TC ***")
        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error('Failed to execute test case with error: %s', self.result_string)

    def tear_down(self):
        """Tear Down Function of this case"""
        try:
            self.log.info("Deleting the content if exists")
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            self.log.info("Deleting dummy data created inside DDB Path")

            dummy_data_dir = self.media_agent_machine.join_path(
                self.store.all_substores[0][1], 'CV_SIDB', '2', str(self.store.store_id), 'Split00', 'dummy_data_dir')
            if self.media_agent_machine.check_directory_exists(dummy_data_dir):
                self.media_agent_machine.remove_directory(dummy_data_dir)

            self.log.info("Reverting MM Admin thread interval to default 15 mins")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 15)

            if self.status == constants.FAILED:
                self.log.warning("TC Failed. Cleaning up Entities. Please check logs for debugging")
            else:
                self.log.info("TC Passed. Cleaning up Entities")
            self.log.info("Update MMConfig to retain multiple DDB Backups to 1")
            self.mm_helper.update_mmconfig_param('MMCONFIG_RETAIN_NO_OF_DDB_BACKUPS', 1, 1)
            self.clean_up()

            if self.ransomware_initial_status:
                self.log.info("Enabling back Ransomware Protection on MA")
                media_agent_obj = self.commcell.media_agents.get(self.tcinputs.get("MediaAgentName"))
                media_agent_obj.set_ransomware_protection(True)
                self.log.info("Completed enabling Ransomware Protection")
        except Exception as exp:
            self.log.warning("Clean up not successful. Might need to cleanup Manually")
            self.log.error("Error: [%s]", str(exp))
