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
    __init__()      --  Initializes test case class object

    setup()         --  Setup function of this test case

    get_ddb_backup_subclient()         --  Gets the ddb_backup_subclient for the MA of our testcase

    reassociate_ddb_backup_subclient() --  Re-associates DDB Backup SubClient to common sp and runs a DDB Backup

    clean_up()          --  Cleans Up the Created Entities

    create_resources()  --  Creates the required resources/ defines paths for this testcase

    create_content_sc() --  Generates and Sets content for the subclient

    get_active_files_store()    --  Returns active store object for files iDA

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

TcInputs to be passed in JSON File:
    "50312": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "MediaAgentName": Name of a MediaAgent - we create Libraries here
        "MountPoint"    : MountPoint where DDB will be hosted
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "library_name"  : Name of Existing Library to be Used
        "mount_path"    : Path to be used as MP for Library
        "num_subclients_tc" : Number of SubClients to be created
        "test_case_factor"  : Scale Factor for Content Size of SubClients
    }

Steps:

1: Verify that provided path is actually a MountPoint

2: CleanUp older Run Entities and create New Entities: Library, SP, SubClient(s)

3: Run Backups for SubClients and Wait for Completion of Jobs

4: Run DDB Backup Job and wait for completion

5: Run the Validations
    i) Log validation for initiating Quiesce operation
    ii) Log validation for shadow set creation
    iii) Log validation for Mount Point recognition by DDB Backup job
    iv) Log validation for initiating UnQuiesce operation
    v) CSDB Validation: LastSnapJobId set in IdxSIDBSubStore

5: Wait for SIDB to go down and mark store for recovery

6: Initiate a Recon and wait for Completion

7: Validate that Recon Job run is Regular ReConstruction

8: If all Validations Passed, cleanup the entities
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
        self.name = "DDB Backup for DDB on mount point"
        self.tcinputs = {
            "MediaAgentName": None,
            "MountPoint": None
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

        self.store = None
        self.library = None
        self.storage_policy = None
        self.backup_set = None
        self.subclients = None
        self.ddbbackup_subclient = None

        self.is_user_defined_lib = False
        self.is_user_defined_mount_path = False

        self.num_subclients = None
        self.test_case_factor = None

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mount_path = True

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

        self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs.get("MountPoint"),
                                                                   f'test_{self.id}', "DDB")

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
                                                        "ddb_cases_common_files", "mount_path_common_lib")
        dedup_store_path = self.media_agent_machine.join_path(self.testcase_path_media_agent,
                                                              "ddb_cases_common_files", "dedup_path_common_sp")

        suffix = self.tcinputs.get("MediaAgentName")
        # create common library
        self.log.info("creating common lib, sp and re-associating the ddb subclient")
        self.library = self.mm_helper.configure_disk_library(
            f"common_lib_ddb_cases_{suffix}", self.tcinputs.get("MediaAgentName"), mount_path)

        # create common SP
        self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
            f"common_sp_ddb_cases_{suffix}",f"common_lib_ddb_cases_{suffix}", self.tcinputs.get("MediaAgentName"),
            dedup_store_path, self.tcinputs.get("MediaAgentName"))

        self.ddbbackup_subclient.storage_policy = f"common_sp_ddb_cases_{suffix}"
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
            self.log.info("Deleting the content if exists")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)

            self.log.info("Deleting BackupSet if Exists")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
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

            if not self.is_user_defined_lib:
                self.log.info("Deleting Library If Exists")
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)

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

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Pre-Requisite: Check Provided Path [%s] is a MountPoint", self.tcinputs.get('MountPoint'))
            command = f'''(Get-Item -literal '{self.tcinputs.get("MountPoint")}').LinkType
                          (Get-Item -literal '{self.tcinputs.get("MountPoint")}').Target'''
            output = self.media_agent_machine.execute_command(command)
            if 'junction' in output.formatted_output.lower() and 'volume' in output.formatted_output.lower():
                self.log.info("Pre-Requisite Met: Provided Path is a MountPoint")
            else:
                raise Exception("Pre-Requisite Not Met: Provided Path is not a MountPoint")

            self.log.info("Update MMConfig to retain multiple DDB Backups to 1")
            self.mm_helper.update_mmconfig_param('MMCONFIG_RETAIN_NO_OF_DDB_BACKUPS', 1, 1)

            # clean up previous run config, Create resources.
            self.clean_up()
            self.create_resources()

            self.log.info("Getting Store, DDB subclient objects")
            self.store = self.get_active_files_store()
            self.ddbbackup_subclient = self.get_ddb_backup_subclient()
            self.log.info("Re-Associating DDB Backup subclient to [%s]", self.storage_policy_name)
            self.ddbbackup_subclient.storage_policy = self.storage_policy_name

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

            self.log.info("Starting DDB Backup Job")
            ddb_backup_job = self.ddbbackup_subclient.backup("FULL")
            self.log.info("DDB Backup Job[%s] started. Waiting for completion", ddb_backup_job.job_id)

            if not ddb_backup_job.wait_for_completion():
                raise Exception(f'DDB Backup Job[{ddb_backup_job.job_id}] Failed. JPR[{ddb_backup_job.delay_reason}]')
            self.log.info("DDB Backup Job Completed")

            # Validations Start
            failed_validations = []
            self.log.info("*** Validation 1: Quiesce operation is initiated for the SIDB Engines ***")
            log_line = 'Quiescing SIDB engines for client'
            (matched_line, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs.get("MediaAgentName"), "clBackup.log", log_line,
                ddb_backup_job.job_id, escape_regex=False)
            if matched_string:
                self.log.info("Validation PASS: Quiescing is initiated for the SIDB engines")
            else:
                self.log.error("Validation FAIL: Quiescing is not done for the SIDB engines")
                failed_validations.append('Quiescing is not initiated for the SIDB engines')

            self.log.info("*** Validation 2: Shadow Set is created ***")
            log_line = 'Created shadow set'
            (matched_line, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs.get("MediaAgentName"), "clBackup.log", log_line,
                ddb_backup_job.job_id, escape_regex=False)
            if matched_string:
                shadow_set_id = matched_line[0].split('Created shadow set ')[1]
                self.log.info("Validation PASS: Got Shadow Set Id: [%s] ***", shadow_set_id)
            else:
                self.log.error("Validation FAIL: Unable to find Shadow Set Id created for DDB Backup")
                failed_validations.append('Unable to find Shadow Set Id created for DDB Backup')

            self.log.info("*** Validation 3: Mount Point is recognized by DDB Backup ***")
            log_line = f'Path [{self.tcinputs.get("MountPoint").upper()}] is a mount point'
            (matched_line, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs.get("MediaAgentName"), "clBackup.log", log_line,
                ddb_backup_job.job_id, escape_regex=True)
            if matched_string:
                self.log.info("Validation PASS: DDB Backup Job recognized the mount Point")
            else:
                self.log.error("Validation FAIL: DDB Backup Job didn't recognize the mount Point")
                failed_validations.append("DDB Backup Job didn't recognize the mount Point")

            self.log.info("*** Validation 4: UnQuiesce operation is initiated for the SIDB Engines ***")
            log_line = 'UnQuiescing SIDB engines'
            (matched_line, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs.get("MediaAgentName"), "clBackup.log", log_line,
                ddb_backup_job.job_id, escape_regex=False)
            if matched_string:
                self.log.info("Validation PASS: UnQuiescing is done for the SIDB engines")
            else:
                self.log.error("Validation FAIL: UnQuiescing is not done for the SIDB engines")
                failed_validations.append('UnQuiescing is not done for the SIDB engines')

            self.log.info("*** Validation 5: Verify LastSnapJobId == DDB Backup jobId ***")
            # if full recon is run, LastSnapJobId will be reset to 0
            query = f"select LastSnapJobId from IdxSIDBSubStore where SubStoreId = {self.store.all_substores[0][0]}"
            self.log.info("Executing Query: %s", query)
            self.csdb.execute(query)
            job_id = self.csdb.fetch_one_row()[0]
            self.log.info("LastSnapJobId: {%s}", str(job_id))
            if str(job_id) == ddb_backup_job.job_id:
                self.log.info("Validation PASS: LastSnapJobId is set to the ddb backup job id")
            else:
                self.log.error("Validation FAIL: LastSnapJobId is not updated")
                failed_validations.append("LastSnapJobId is not updated")

            self.log.info("Making sure that SIDB Process is down")
            if not self.dedup_helper.wait_till_sidb_down(
                    str(self.store.store_id),
                    self.commcell.clients.get(self.tcinputs.get("MediaAgentName")),timeout=300):
                raise Exception("Timeout waiting for SIDB process to go down")
            self.log.info("SIDB Process is down on MA")

            self.log.info("Marking the Store for Recovery")
            substore_obj = self.store.get(self.store.all_substores[0][0])
            substore_obj.mark_for_recovery()
            self.log.info(
                f"-marked store[{substore_obj.store_id}]: substore[{substore_obj.substore_id}] for recovery")

            self.log.info("Starting a Reconstruction Job")
            recon_job = self.store.recover_deduplication_database(full_reconstruction=False)
            self.log.info("DDB Reconstruction Job[%s] started. Waiting for job to complete.", recon_job.job_id)
            if not recon_job.wait_for_completion():
                self.log.info("DDB Reconstruction Job[%s] Failed. JPR[%s]", recon_job.job_id, recon_job.delay_reason)
                failed_validations.append(
                    f'DDB Reconstruction Job[{recon_job.job_id}] Failed. JPR[{recon_job.delay_reason}]')
            else:
                self.log.info("DDB Reconstruction Job[%s] completed", recon_job.job_id)

            self.log.info("***** Validation 6: is it a Regular recon job? *****")
            recon_type = self.dedup_helper.get_reconstruction_type(recon_job.job_id)
            if recon_type == "Regular Reconstruction":
                self.log.info("Validation PASS: Recon Job is a regular reconstruction job")
            else:
                self.log.error("Validation FAIL: Recon job is not a regular reconstruction job")
                failed_validations.append("Recon job is not a regular reconstruction job")

            if failed_validations:
                raise Exception(str(failed_validations))
            self.log.info("*** Finished all validations in TC ***")
        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error('Failed to execute test case with error: %s', self.result_string)

    def tear_down(self):
        """Tear Down Function of this case"""
        try:
            if self.status == constants.FAILED:
                self.log.warning("TC Failed. Cleaning up Entities. Please check logs for debugging")
            self.clean_up()
        except Exception as exp:
            self.log.warning("Clean up not successful. Might need to cleanup Manually")
            self.log.error("Error: [%s]", str(exp))
