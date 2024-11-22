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

    __init__()      --  initialize TestCase class

    _get_mountpath_id() --  To get first mount path id on specified storage pool

    _cleanup()      --  To perform cleanup operation before setting the environment and after testcase completion

    create_disk_storage()   --      Creates a new disk storage

    validate_storage_creation()     -- Validates if the disk is crated or not

    validate_mp_creation_for_db()   --  Validates if the disk is created wth set mount path attributes

    add_backup_location_negative()  -- Adds a new backup location to an already existing disk with incorrect credentials

    add_backup_location_positive()  -- Adds a new backup location to an already existing disk with correct credentials

    setup()         --  setup function of this test case

    validate_auto_ma_share()        -- Validates whether the mount paths are being auto shared with correct access type

    configure_entities()            -- Configure required entities for this test case

    run_backups()                   -- Run full backups for all subclients

    run_incremental_backup()        -- Run an incremental backup job

    run_backup_synthetic_full()     -- Run a synthetic full backup job

    delete_entities()               -- Delete all the entities created for this test case

    check_mp1_max_writers()         -- Checks the number of maximum concurrent writers for mp1

    retire_backup_location()        -- To retire a backup location

    check_mp1_prevent_data()        -- Checks if the attribute is being set correctly for mp1 after retirement

    delete_controller()             -- To delete MA2 on MP1

    validate_controller_and_access_type()   -- Validates the number of controllers and their access types

    restore()                       -- Run a restore job for all the previous backup jobs

    delete_backup_location()        -- Delete the backup location and validate if it is deleted

    delete_disk_storage()           -- Delete the created disk storage

    run()           --  run function of this test case

User should have the following permissions:
        Library Management on Library Entity
        Storage Policy Management on MA Entity
        View on CommCell Entity
        Media Agent Management on Library Entity
        Administrative Management on Global level
        Execute and edit on Workflow Entity

Sample Input:
"63752": {
                    "AgentName": "File System",
                    "ClientName": "client_name",
                    "MediaAgent1": "media_agent_1",
                    "MediaAgent2": "media_agent_2",
                    "NetworkPath": "network_path",
                    "DummySavedCredential": "incorrect_credentials",
                    "ActualSavedCredential": "correct_credentials"
                }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Storage.DiskStorage import DiskStorage


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.restore_path = None
        self.bkpset_obj = None
        self.storage_policy_name = None
        self.dedup_helper = None
        self.content_path = None
        self.client_system_drive = None
        self.subclient_name = None
        self.backupset_name = None
        self.mp1_id = None
        self.mmhelper = None
        self.name = "Command Center -CRUD - Disk Storage"
        self.browser = None
        self.admin_console = None
        self.storage_helper = None
        self.common_util = None
        self.client_machine = None
        self.ma1_machine = None
        self.storage_pool_name = None
        self.backup_location = None
        self.ddb_location = None
        self.network_location = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent1": None,
            "MediaAgent2": None,
            "NetworkPath": None,
            "DummySavedCredential": None,
            "ActualSavedCredential": None
        }

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self._props = self.admin_console.props
            self._table = Rtable(self.admin_console, title='Backup locations')
            self.__navigator = self.admin_console.navigator
            self.__disk = DiskStorage(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def _get_mountpath_id_mp(self, storage_pool_name):
        """
        Get a first Mount path id from storage pool name
            Args:
                storage_pool_name (str)  --  Storage Pool Name

            Returns:
                First Mount path id for the given Storage Pool name
        """

        query = """ SELECT MMP.MountPathId 
                    FROM archGroup AG WITH(NOLOCK), MMDataPath MMDP WITH(NOLOCK), MMDrivePool MMD WITH(NOLOCK),
                     MMMasterPool MP WITH(NOLOCK), MMLibrary MML WITH(NOLOCK), MMMountPath MMP WITH(NOLOCK)
                    WHERE MMDP.copyid = AG.defaultCopy
                    AND MMD.DrivePoolId = MMDP.DrivePoolId
                    AND MP.MasterPoolId = MMD.MasterPoolId
                    AND MML.LibraryId = MP.LibraryId
                    AND MMP.LibraryId = MML.LibraryId
                    AND AG.name = '{0}'
                    ORDER BY  MMP.MountPathId  """.format(storage_pool_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != ['']:
            return cur[0]
        self.log.error("No entries present")
        raise Exception("Invalid Storage Pool Name.")

    @test_step
    def cleanup(self):
        """To perform cleanup operation"""

        try:
            self.log.info('Check for backupset %s', self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                # To delete backupset if exists
                self.log.info('Deletes backupset %s', self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
            self.log.info('Check for storage policy %s', self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                # To delete storage policy if exists
                self.log.info('Deletes storage policy %s', self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info('Check for content path %s', self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                # To delete content path if exists
                self.client_machine.remove_directory(self.content_path)
                self.log.info('Removed directory...' + self.content_path)
            self.log.info('Check for restore path %s', self.restore_path)
            if self.client_machine.check_directory_exists(self.restore_path):
                # To delete restore path if exists
                self.client_machine.remove_directory(self.restore_path)
                self.log.info('Removed directory...' + self.restore_path)
            self.log.info('Check for storage %s', self.storage_pool_name)
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                # To delete disk storage if exists
                self.log.info('Deletes storage %s ', self.storage_pool_name)
                self.storage_helper.delete_disk_storage(self.storage_pool_name)
            self.commcell.storage_pools.refresh()
            if self.client_machine.check_directory_exists(self.restore_path):
                self.client_machine.remove_directory(self.restore_path)
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    @test_step
    def create_disk_storage(self):
        """Creates a new disk storage"""
        ma1_name = self.commcell.clients.get(self.tcinputs['MediaAgent1']).display_name
        self.storage_helper.add_disk_storage(
            self.storage_pool_name,
            ma1_name,
            self.backup_location,
            deduplication_db_location=self.ddb_location)
        self.log.info('Successfully created disk storage: %s', self.storage_pool_name)
        self.commcell.storage_pools.refresh()

    @test_step
    def validate_storage_creation(self):
        """Validates if the disk is being created or not"""

        storage_list = self.storage_helper.list_disk_storage()

        if self.storage_pool_name in storage_list:
            self.log.info("Created disk is being shown on web page")
        else:
            raise Exception('Created disk is not being shown on web page')

    @test_step
    def validate_mp_creation_for_db(self):
        """Validates if the disk is being created with set mount path attributes"""

        query = """ SELECT MMP.Attribute,MMP.MaxConcurrentWriters 
                    FROM archGroup AG WITH(NOLOCK), MMDataPath MMDP WITH(NOLOCK), MMDrivePool MMD WITH(NOLOCK), 
                    MMMasterPool MP WITH(NOLOCK), MMLibrary MML WITH(NOLOCK), MMMountPath MMP WITH(NOLOCK)
                    WHERE MMDP.copyid = AG.defaultCopy
                    AND MMD.DrivePoolId = MMDP.DrivePoolId
                    AND MP.MasterPoolId = MMD.MasterPoolId
                    AND MML.LibraryId = MP.LibraryId
                    AND MMP.LibraryId = MML.LibraryId
                    AND AG.name = '{0}'""".format(self.storage_pool_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        bit = int(cur[0])
        if (bit & 8) and (bit & 1024):
            self.log.info('MP attribute is set to 1160')
        else:
            raise Exception("Default Mount Path Attribute is not being set")
        if cur[1] != '1000':
            raise Exception("Default Max Concurrent Writers is not being set")
        self.log.info("Library is created with default values")

    @test_step
    def configure_entities(self):
        """Configure required entities for this test case"""

        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.dedup_helper.configure_dedupe_storage_policy(self.storage_policy_name,
                                                          storage_pool_name=self.storage_pool_name,
                                                          is_dedup_storage_pool=True)
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)
        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mmhelper.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", self.content_path)
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)
        self.log.info("Configuring Subclient [%s]", self.subclient_name)
        self.log.info(f"Generating data at {self.content_path}")
        if not self.client_machine.generate_test_data(self.content_path, dirs=1, file_size=(300 * 1024),
                                                      files=2):
            self.log.error(f"Unable to generate data at {self.content_path}")
            raise Exception(f"unable to Generate Data at {self.content_path}")
        self.log.info(f"Generated data at {self.content_path}")
        self.subclient_obj = (self.mmhelper.configure_subclient(
            self.backupset_name, self.subclient_name, self.storage_policy_name, self.content_path))
        self.log.info("Successfully configured Subclient [%s]", self.subclient_name)

    @test_step
    def run_backups(self):
        """Run full backups for all subclients"""

        job_obj = self.subclient_obj.backup("Full")
        self.log.info("Successfully initiated a FULL backup job on subclient [%s] with job id [%s]",
                      self.subclient_obj.subclient_name, job_obj.job_id)
        if not job_obj.wait_for_completion():
            raise Exception("Failed to run backup job with error: {0}".format(
                job_obj.delay_reason))
        self.log.info("Backup job: %s completed successfully", job_obj.job_id)

    @test_step
    def run_incremental_backup(self):
        """Run an incremental backup job"""

        if not self.client_machine.generate_test_data(self.content_path, dirs=1, file_size=(100 * 1024),
                                                      files=2):
            self.log.error(f"Unable to generate data at {self.content_path}")
            raise Exception(f"unable to Generate Data at {self.content_path}")
        job_obj = self.subclient_obj.backup("Incremental")
        self.log.info("Successfully initiated a INCREMENTAL backup job on subclient [%s] with job id [%s]",
                      self.subclient_obj.subclient_name,
                      job_obj.job_id)
        if not job_obj.wait_for_completion():
            raise Exception("Failed to run backup job with error: {0}".format(
                job_obj.delay_reason))
        self.log.info("Backup job: %s completed successfully", job_obj.job_id)

    @test_step
    def run_backup_synthetic_full(self):
        """Run a synthetic full backup job"""

        job_obj = self.subclient_obj.backup("SYNTHETIC_FULL")
        self.log.info("Successfully initiated a SYNTHETIC FULL backup job on subclient [%s] with job id [%s]",
                      self.subclient_obj.subclient_name,
                      job_obj.job_id)
        if not job_obj.wait_for_completion():
            raise Exception("Failed to run backup job with error: {0}".format(
                job_obj.delay_reason))
        self.log.info("Backup job: %s completed successfully", job_obj.job_id)

    @test_step
    def delete_entities(self):
        """Delete all the entities created for this test case"""

        self.log.info("Removing subclient if exists...")
        if self.bkpset_obj.subclients.has_subclient(self.subclient_name):
            self.bkpset_obj.subclients.delete(self.subclient_name)
            self.log.info("Removed subclient..." + self.subclient_name)
        self.log.info("Removing backupset if exists...")
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("Removed backupset..." + self.backupset_name)
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("Removed dedup storage policy..." + self.storage_policy_name)
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info('Removed directory...' + self.content_path)
        if self.client_machine.check_directory_exists(self.restore_path):
            self.client_machine.remove_directory(self.restore_path)
            self.log.info('Removed directory...' + self.restore_path)

    @test_step
    def add_backup_location_negative(self):
        """Adds a new backup location to an already existing disk with incorrect credentials"""

        ma2_name = self.commcell.clients.get(self.tcinputs['MediaAgent2']).display_name
        self.network_location = self.tcinputs['NetworkPath']
        saved_credentials = self.tcinputs['DummySavedCredential']
        try:
            self.storage_helper.add_disk_backup_location(
                self.storage_pool_name,
                ma2_name,
                self.network_location,
                saved_credentials)
        except CVWebAutomationException:
            self.log.info("As expected adding of backup location failed")

        network_location = "[%s] %s" % (ma2_name, self.network_location)

        backup_location_list = self.storage_helper.list_disk_backup_locations(self.storage_pool_name)
        if network_location in backup_location_list:
            raise Exception("Backup Location was added successfully with dummy credentials")
        else:
            self.log.info("As expected adding of backup location failed")

    @test_step
    def add_backup_location_positive(self):
        """Adds a new backup location to an already existing disk with correct credentials"""

        ma2_name = self.commcell.clients.get(self.tcinputs['MediaAgent2']).display_name
        self.network_location = self.tcinputs['NetworkPath']
        saved_credentials = self.tcinputs['ActualSavedCredential']
        self.storage_helper.add_disk_backup_location(
            self.storage_pool_name,
            ma2_name,
            self.network_location,
            saved_credentials)
        self.log.info('Successfully added backup location: %s', self.network_location)
        network_location = "[%s] %s" % (ma2_name, self.network_location)

        backup_location_list = self.storage_helper.list_disk_backup_locations(self.storage_pool_name)
        if network_location not in backup_location_list:
            raise Exception("Failed to add Backup Location with correct credentials")

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.init_tc()
        self.storage_helper = StorageMain(self.admin_console)
        self.mmhelper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        options_selector = OptionsSelector(self.commcell)
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.ma1_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent1'])
        self.client_machine = options_selector.get_machine_object(self.tcinputs['ClientName'])
        self.storage_pool_name = '%s_Dedupe_Disk' % str(self.id)
        self.storage_policy_name = '%s_Dedupe_SP' % str(self.id)

        # To select drive with space available in MA1 machine
        self.log.info('Selecting drive in the MA1 machine based on space available')
        ma1_drive = options_selector.get_drive(self.ma1_machine, size=30 * 1024)
        if ma1_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma1_drive)
        self.backup_location = self.ma1_machine.join_path(ma1_drive, 'Automation', str(self.id), 'MP')
        self.ddb_location = self.ma1_machine.join_path(ma1_drive, 'Automation', str(self.id), 'DDB')
        self.client_system_drive = options_selector.get_drive(self.client_machine, 10 * 1024)
        self.content_path = self.client_machine.join_path(self.client_system_drive, str(self.id))
        self.restore_path = self.client_machine.join_path(self.client_system_drive, str(self.id), 'restore_path')
        self.network_location = self.tcinputs['NetworkPath']

    @test_step
    def validate_auto_ma_share(self):
        """Validates whether the mount paths are being auto shared with correct access type"""

        query = """ SELECT DISTINCT MMP.MountPathId,AC.displayName, MMDC.DeviceAccessType, MMDC.DeviceControllerId
                    FROM archGroup AG WITH(NOLOCK), MMDataPath MMDP WITH(NOLOCK), MMDrivePool MMD WITH(NOLOCK), 
                       MMMasterPool MP WITH(NOLOCK), MMMountPath MMP WITH(NOLOCK), 
                       MMMountPathToStorageDevice MPSD WITH(NOLOCK), MMDeviceController MMDC WITH(NOLOCK),
                       APP_Client AC WITH(NOLOCK)
                    WHERE  MMDP.copyid = AG.defaultCopy
                        AND MMD.DrivePoolId = MMDP.DrivePoolId
                        AND MP.MasterPoolId = MMD.MasterPoolId
                        AND MMP.LibraryId =  MP.LibraryId
                        AND MPSD.MountPathId = MMP.MountPathId
                        AND MMDC.DeviceId = MPSD.DeviceId
                        AND AC.id = MMDC.ClientId
                        AND AG.name = '{0}'
                    ORDER BY MMP.MountPathId, MMDC.DeviceControllerId""".format(self.storage_pool_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self.log.info("RESULT: %s", cur)
        if not (cur[0][1] == self.tcinputs["MediaAgent1"] and cur[0][2] == "14"
                and cur[1][1] == self.tcinputs["MediaAgent2"]
                and cur[1][2] == "20"):
            raise Exception("NOT AUTO SHARED")
        if not (cur[2][1] == self.tcinputs["MediaAgent2"] and cur[2][2] == "14"
                and cur[3][1] == self.tcinputs["MediaAgent1"] and cur[3][2] == "6"):
            raise Exception("NOT AUTO SHARED")
        self.log.info("MA2 is being auto shared to MP1 and vice versa")

    def check_mp1_max_writers(self):
        """Checks the number of maximum concurrent writers for mp1"""

        self.mp1_id = self._get_mountpath_id_mp(self.storage_pool_name)
        query = """SELECT MaxConcurrentWriters FROM MMMountPath WITH(NOLOCK)
                   WHERE MountPathId = '{0}'""".format(self.mp1_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        if cur[0] != '0':
            raise Exception("MP1 is not being disabled for future backups")
        self.log.info("MP1 is disabled for future backups")

    @test_step
    def retire_backup_location(self):
        """Retire a backup location"""
        self.storage_helper.disable_disk_backup_location_for_future_backups(self.storage_pool_name,
                                                                            self.backup_location)
        self.check_mp1_max_writers()
        self.storage_helper.enable_retire_disk_backup_location(self.storage_pool_name, self.backup_location)
        self.check_mp1_prevent_data()

    @test_step
    def check_mp1_prevent_data(self):
        """Checks if the attribute is being set correctly for mp1 after retirement"""

        query = """SELECT Attribute&8192 FROM MMMountPath WITH(NOLOCK)
                   WHERE MountPathId = '{0}'""".format(self.mp1_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        if cur[0] != '8192':
            raise Exception("MP1 is not retired")
        self.log.info("MP1 is retired")

    @test_step
    def delete_controller(self):
        """Deletes MA2 on  MP1"""

        self.storage_helper.delete_disk_access_path(self.storage_pool_name, self.backup_location,
                                                    self.tcinputs["MediaAgent2"])
        self.validate_controller_and_access_type()

    def add_controller(self):
        """Add the deleted controller from previous step before restore"""

        backup_location = "[%s] %s" % (self.tcinputs['MediaAgent1'], self.backup_location)
        self.storage_helper.add_media_agent_disk_storage(self.storage_pool_name,
                                                         backup_location, [self.tcinputs['MediaAgent2']])

    @test_step
    def validate_controller_and_access_type(self):
        """Validates the number of controllers and their access types"""

        query = """SELECT DISTINCT MMP.MountPathId,AC.displayName, MMDC.DeviceAccessType, MMDC.DeviceControllerId
                    FROM archGroup AG WITH(NOLOCK), MMDataPath MMDP WITH(NOLOCK), MMDrivePool MMD WITH(NOLOCK), 
                       MMMasterPool MP WITH(NOLOCK), MMMountPath MMP WITH(NOLOCK), 
                       MMMountPathToStorageDevice MPSD WITH(NOLOCK), MMDeviceController MMDC WITH(NOLOCK),
                       APP_Client AC WITH(NOLOCK)
                    WHERE  MMDP.copyid = AG.defaultCopy
                        AND MMD.DrivePoolId = MMDP.DrivePoolId
                        AND MP.MasterPoolId = MMD.MasterPoolId
                        AND MMP.LibraryId = MP.LibraryId
                        AND MPSD.MountPathId = MMP.MountPathId
                        AND MMDC.DeviceId = MPSD.DeviceId
                        AND AC.id = MMDC.ClientId
                        AND AG.name = '{0}'
                    ORDER BY MMP.MountPathId, MMDC.DeviceControllerId""".format(self.storage_pool_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self.log.info("RESULT: %s", cur)
        if len(cur) != 3:
            raise Exception("Controllers have extra access.")
        if not (cur[0][1] == self.tcinputs["MediaAgent1"] and cur[0][2] == '14'):
            raise Exception("MP1's controllers have extra access")
        if not (cur[1][1] == self.tcinputs["MediaAgent2"] and cur[1][2] == '14'
                and cur[2][1] == self.tcinputs["MediaAgent1"]
                and cur[2][2] == '6'):
            raise Exception("MP2's controllers have extra access")
        self.log.info("MP1 has one controller and MP2 has two controllers")

    @test_step
    def restore(self):
        """
        Run a restore job for all the previous backup jobs
        """
        try:
            if self.client_machine.check_directory_exists(self.restore_path):
                self.log.info("Deleting already existing restore directory [%s]", self.restore_path)
                self.client_machine.remove_directory(self.restore_path)
            self.client_machine.create_directory(self.restore_path)
            self.log.info("Content path being restored : %s", self.content_path)
            restore_job = self.bkpset_obj.restore_out_of_place(client=self.tcinputs["ClientName"],
                                                               destination_path=self.restore_path,
                                                               paths=[self.content_path])
            self.log.info("Successfully initiated a RESTORE job  with job id [%s]",
                          str(restore_job.job_id))
            if restore_job.wait_for_completion():
                self.log.info("Restore by Job id: [%s] completed successfully", str(restore_job.job_id))
            else:
                raise Exception("Restore by Job id: [%s] failed/ killed", str(restore_job.job_id))

        except Exception as excp:
            raise Exception('Failed to start Restore with error : %s',
                            str(excp))

    @test_step
    def delete_backup_location(self):
        """Try to delete backup location and verify deletion being not allowed as valid data is present"""

        ma1_name = self.commcell.clients.get(self.tcinputs['MediaAgent1']).display_name
        backup_location = "[%s] %s" % (ma1_name, self.backup_location)
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(self.storage_pool_name)
        self.admin_console.access_tab(self._props['label.backupLocations'])
        self._table.access_action_item(backup_location, self.admin_console.props['label.globalActions.delete'])
        self.validate_delete_string()

    def validate_delete_string(self):
        """Verify whether we are displaying 'Force delete with data loss' string or not"""

        modal_title = 'Confirm delete'
        rdialog = RModalDialog(admin_console=self.admin_console,title=modal_title)
        delete_text_field_value = rdialog.get_input_details(input_id='confirmText-label')
        if len(delete_text_field_value.strip()) == 0:
            raise Exception("Error: User is not asked to fill string to accept force delete with data loss.")
        else:
            expected_string = 'Force delete with data loss'
            if expected_string in delete_text_field_value.strip():
                self.log.info("User is asked to fill string to accept force delete with data loss.")
            else:
                raise Exception("Error: User is not asked to fill string to accept force delete with data loss.")
        rdialog.click_cancel()

    @test_step
    def delete_disk_storage(self):
        """Delete the created disk storage"""

        self.storage_helper.delete_disk_storage(self.storage_pool_name)
        disk_storage_list = self.storage_helper.list_disk_storage()
        if self.storage_pool_name in disk_storage_list:
            raise Exception("Disk storage is not deleted")
        self.commcell.storage_pools.refresh()

    def run(self):
        """Main function for test case execution"""

        try:
            self.cleanup()
            self.create_disk_storage()
            self.validate_storage_creation()
            self.validate_mp_creation_for_db()
            self.add_backup_location_negative()
            self.add_backup_location_positive()
            self.validate_auto_ma_share()
            self.configure_entities()
            self.run_backups()
            self.retire_backup_location()
            self.run_incremental_backup()
            self.delete_controller()
            self.run_backup_synthetic_full()
            self.add_controller()
            self.restore()
            self.delete_entities()
            self.delete_backup_location()
            self.delete_disk_storage()
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)
