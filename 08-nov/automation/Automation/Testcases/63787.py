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

    setup()         --  setup function of this test case

    create_cloud_storage()  -- To create a new cloud storage

    validate_storage_creation() -- Validates if the cloud storage is created

    validate_mp_creation_for_db()   -- Validates if the cloud storage is being created with set mount path attributes

    add_container()         -- Adds a new container to an already existing cloud storage

    validate_auto_ma_share() -- Validates whether the mount paths are being auto shared with correct access type

    configure_entities()    --  Configure required entities for this test case

    run_full_backup()       --  Run a full backup job

    check_mp1_max_writers()  -- Checks the number of maximum concurrent writers for mp1

    check_mp1_prevent data() -- Checks is the attribute is being set correct for mp1 after retirement

    retire_container()      -- Retire a container

    run_incremental_backup()   -- Run an incremental backup job

    delete_controller()  --  Deletes MA1 on MP2

    run_backup_synthetic_full() -- Run a synthetic full backup job

    restore()           --  Run a restore job for all the previous backup jobs

    delete_entities()   -- Delete all the entities created for this test case

    validate_controller_and_access_type()   --  Validates the number of controllers and their access types

    validate_delete_container()         --  Validates if a particular container is deleted or not

    delete_container1()      -- Deletes container1

    validate_delete_cloud()     --  Validates if a particular cloud storage is deleted or not

    delete_cloud_storage()      -- Deletes cloud storage

    run()           --  run function of this test case

User should have the following permissions:
        Library Management on Library Entity
        Storage Policy Management on MA Entity
        View on CommCell Entity
        Media Agent Management on Library Entity
        Administrative Management on Global level
        Execute and edit on Workflow Entity

Sample Input:
"63787": {
                        "AgentName": "File System",
                        "ClientName": "client_name",
                        "CloudContainer1": "cloud_container_1",
                        "CloudContainer2": "cloud_container_2",
                        "CloudServerName": "cloud_server_name",
                        "CloudServerType": "cloud_server_type",
                        "MediaAgent1": "media_agent_1",
                        "MediaAgent2": "media_agent_2",
                        "SavedCredential": "saved_credential",
                        "CloudRegion": "cloud_region"
                        }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Storage.CloudStorage import CloudStorage
from Web.AdminConsole.Components.table import Rtable


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.__cloud = None
        self.__navigator = None
        self._table = None
        self._props = None
        self.job_obj = None
        self.subclient_obj = None
        self.bkpset_obj = None
        self.ma_machine = None
        self.content_path = None
        self.storage_policy_name = None
        self.client_system_drive = None
        self.restore_path = None
        self.backupset_name = None
        self.subclient_name = None
        self.dedup_helper = None
        self.mmhelper = None
        self.name = "Command Center - CRUD - Cloud Storage configuration"
        self.browser = None
        self.admin_console = None
        self.storage_helper = None
        self.client_machine = None
        self.ma1_machine = None
        self.storage_pool_name = None
        self.backup_location = None
        self.mp1_id = None
        self.ddb_location = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent1": None,
            "MediaAgent2": None,
            "CloudContainer1": None,
            "CloudContainer2": None,
            "CloudServerName": None,
            "CloudServerType": None,
            "SavedCredential": None,
        }

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.__navigator = self.admin_console.navigator
            self.__cloud = CloudStorage(self.admin_console)
            self._table = Rtable(self.admin_console, id='cloud-overview-grid')
            self._props = self.admin_console.props
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup(self):
        """ To perform cleanup operation """

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
                # To delete cloud storage if exists
                self.log.info('Deletes storage %s', self.storage_pool_name)
                self.storage_helper.delete_cloud_storage(self.storage_pool_name)

            self.commcell.storage_pools.refresh()
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.init_tc()
        self.storage_helper = StorageMain(self.admin_console)
        options_selector = OptionsSelector(self.commcell)
        self.mmhelper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        ma_name = self.tcinputs.get("MediaAgent1")
        self.log.info(f"MACHINE MA NAME {ma_name}")
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent1'])
        self.client_machine = options_selector.get_machine_object(self.tcinputs['ClientName'])
        self.storage_pool_name = '%s_Cloud' % str(self.id)

        # To select drive with space available in MA1 machine
        self.log.info('Selecting drive in the MA machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=30 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.ddb_location = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')
        self.storage_policy_name = '%s_Dedupe_SP' % str(self.id)
        self.client_system_drive = options_selector.get_drive(self.client_machine, 10 * 1024)
        self.content_path = self.client_machine.join_path(self.client_system_drive, str(self.id))
        self.restore_path = self.client_machine.join_path(self.client_system_drive, str(self.id), 'restore_path')
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"

    def _get_mountpath_id_mp(self, storage_pool_name):
        """
        Get a first Mountpath id from Storage Pool Name
            Args:
                storage_pool_name (str)  --  Storage Pool Name

            Returns:
                First Mountpath id for the given Storage Pool name
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
                    ORDER BY  MMP.MountPathId """.format(storage_pool_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != ['']:
            return cur[0]
        self.log.error("No entries present")
        raise Exception("Invalid Storage Pool Name.")

    @test_step
    def create_cloud_storage(self):
        """ To create a new cloud storage"""

        self.log.info("Adding a new cloud storage: %s", self.storage_pool_name)
        ma_name = self.commcell.clients.get(self.tcinputs['MediaAgent1']).display_name
        self.storage_helper.add_cloud_storage(self.storage_pool_name, ma_name,
                                              self.tcinputs['CloudServerType'],
                                              self.tcinputs['CloudServerName'],
                                              self.tcinputs['CloudContainer1'],
                                              storage_class=self.tcinputs.get('CloudStorageClass'),
                                              saved_credential_name=self.tcinputs['SavedCredential'],
                                              deduplication_db_location=self.ddb_location,
                                              region=self.tcinputs['CloudRegion'],
                                              auth_type='Access key and Account name')
        self.log.info('successfully created cloud storage: %s', self.storage_pool_name)
        self.mp1_id = self._get_mountpath_id_mp(self.storage_pool_name)
        self.commcell.storage_pools.refresh()

    @test_step
    def validate_storage_creation(self):
        """Validates if the cloud storage is created or not"""

        storage_list = self.storage_helper.list_cloud_storage()

        if self.storage_pool_name in storage_list:
            self.log.info("Created cloud storage is being shown on web page")
        else:
            raise Exception('Created cloud storage is not being shown on web page')

    @test_step
    def validate_mp_creation_for_db(self):
        """Validates if the cloud storage is being created with set mount path attributes"""

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
        if (bit & 8) and (bit & 32):
            self.log.info('MP attribute is set with 8(MNTPTH_ATTRIB_DATA_PRUNING),'
                          '32(MNTPTH_ATTRIB_ENABLE_CLOUD_PRUNING)')
        else:
            raise Exception("Default Mount Path Attribute is not being set")
        if cur[1] != '1000':
            raise Exception("Default Max Concurrent Writers is not being set")
        self.log.info("Library is created with default values")

    @test_step
    def add_container(self):
        """Adds a new container to an already existing cloud storage"""

        ma2_name = self.commcell.clients.get(self.tcinputs['MediaAgent2']).display_name
        self.storage_helper.add_cloud_container(
            self.storage_pool_name,
            ma2_name,
            self.tcinputs['CloudServerName'],
            self.tcinputs['CloudContainer2'],
            storage_class=self.tcinputs.get('CloudStorageClass'),
            saved_credential_name=self.tcinputs['SavedCredential'],
            auth_type='Access key and Account name')
        self.log.info('Successfully added container: %s', self.tcinputs['CloudContainer2'])
        container = "[%s] %s" % (ma2_name,  self.tcinputs['CloudContainer2'])

        container_list = self.storage_helper.list_cloud_containers(self.storage_pool_name)
        if container not in container_list:
            raise Exception("Failed to add Container")

    @test_step
    def validate_auto_ma_share(self):
        """Validates whether the mount paths are being auto shared with correct access type"""

        query = """SELECT DISTINCT MMP.MountPathId,AC.displayName, MMDC.DeviceAccessType, MMDC.DeviceControllerId 
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
                    ORDER BY MMP.MountPathId, MMDC.DeviceControllerId
                """.format(self.storage_pool_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self.log.info("RESULT: %s", cur)
        if len(cur) != 4:
            raise Exception("NOT AUTO SHARED")
        if not (cur[0][1] == self.tcinputs["MediaAgent1"] and cur[0][2] == '14'
                and cur[1][1] == self.tcinputs["MediaAgent2"] and cur[1][2] == '14'):
            raise Exception("NOT AUTO SHARED")
        if not (cur[2][1] == self.tcinputs["MediaAgent2"] and cur[2][2] == '14'
                and cur[3][1] == self.tcinputs["MediaAgent1"] and cur[3][2] == '14'):
            raise Exception("NOT AUTO SHARED")
        self.log.info("MA2 is being auto shared to MP1 and vice versa")

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
        content_path = self.client_machine.join_path(self.content_path, str('initial_backup'))
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", content_path)
            self.client_machine.remove_directory(content_path)
        self.client_machine.create_directory(content_path)
        self.log.info("Configuring Subclient [%s]", self.subclient_name)
        self.log.info(f"Generating data at {content_path}")
        if not self.client_machine.generate_test_data(content_path, dirs=1, file_size=(300 * 1024),
                                                      files=2):
            self.log.error(f"Unable to generate data at {content_path}")
            raise Exception(f"unable to Generate Data at {content_path}")
        self.log.info(f"Generated data at {content_path}")
        self.subclient_obj = (self.mmhelper.configure_subclient(
            self.backupset_name, self.subclient_name, self.storage_policy_name, content_path))
        self.log.info("Successfully configured Subclient [%s]", self.subclient_name)

    @test_step
    def run_full_backup(self):
        """Run a full backup job"""

        job_obj = self.subclient_obj.backup("Full")
        self.log.info("Successfully initiated a FULL backup job on subclient [%s] with job id [%s]",
                        self.subclient_obj.subclient_name, job_obj.job_id)
        if not job_obj.wait_for_completion():
            raise Exception("Failed to run backup job with error: {0}".format(
                    job_obj.delay_reason))
        self.log.info("Backup job: %s completed successfully", job_obj.job_id)

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

    def check_mp1_prevent_data(self):
        """Checks is the attribute is being set correct for mp1 after retirement"""

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
    def retire_container(self):
        """Retire a container"""

        container1 = "[%s] %s" % (self.tcinputs["MediaAgent1"], self.tcinputs['CloudContainer1'])
        self.storage_helper.disable_cloud_container_for_future_backups(self.storage_pool_name, container1)
        self.check_mp1_max_writers()
        self.storage_helper.enable_retire_cloud_container(self.storage_pool_name, container1)
        self.check_mp1_prevent_data()

    @test_step
    def run_incremental_backup(self):
        """Run an incremental backup job"""

        content_path = self.client_machine.join_path(self.content_path, str('incremental'))
        subclient_name = self.subclient_obj.subclient_name
        self.mmhelper.configure_subclient(self.backupset_name, subclient_name, self.storage_policy_name,
                                          content_path)
        if not self.client_machine.generate_test_data(content_path, dirs=1, file_size=(100 * 1024),
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
                    ORDER BY MMP.MountPathId, MMDC.DeviceControllerId
                """.format(self.storage_pool_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self.log.info("RESULT: %s", cur)
        if len(cur) != 3:
            raise Exception("Either controllers are more or have extra access.")
        if not (cur[0][1] == self.tcinputs["MediaAgent1"] and cur[0][2] == '14'
                and cur[1][1] == self.tcinputs["MediaAgent2"] and cur[1][2] == '14'):
            raise Exception("Controllers are less or do not have the right access")
        if not (cur[2][1] == self.tcinputs["MediaAgent1"] and cur[2][2] == '14'):
            raise Exception("Controllers are less or do not have the right access")

    @test_step
    def delete_controller(self):
        """Deletes MA1 on certain MP2"""

        container2 = "[%s] %s" % (self.tcinputs["MediaAgent1"], self.tcinputs['CloudContainer1'])
        self.storage_helper.delete_cloud_access_path(self.storage_pool_name, container2, self.tcinputs["MediaAgent2"])
        self.validate_controller_and_access_type()

    def add_controller(self):
        """Add the deleted controller from previous step before restore"""

        container2 = "[%s] %s" % (self.tcinputs["MediaAgent1"], self.tcinputs['CloudContainer1'])
        self.storage_helper.add_media_agent_cloud_storage(
            self.storage_pool_name,
            container2, [self.tcinputs['MediaAgent2']]
            )

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
    def restore(self):
        """
        Run a restore job for all the previous backup jobs
        """
        try:
            # jobs_list = self.get_jobs_for_subclient(self.subclient_obj_list[num-1])
            self.log.info("Content path being restored: %s", self.content_path)
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
    def validate_delete_container(self):
        """Validates if a particular container is deleted or not"""

        container_list = self.storage_helper.list_cloud_containers(self.storage_pool_name)

        if self.tcinputs['CloudContainer1'] in container_list:
            raise Exception('Container is not deleted')
        else:
            self.log.info('Container %s deleted successfully', self.tcinputs['CloudContainer1'])

    @test_step
    def delete_container1(self):
        """Try to delete container and verify deletion being not allowed as valid data is present"""

        container_label = "[%s] %s" % (self.tcinputs["MediaAgent1"], self.tcinputs['CloudContainer1'])
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(self.storage_pool_name)
        self.admin_console.access_tab(self._props['label.backupLocations'])
        self._table.access_action_item(container_label, self.admin_console.props['label.globalActions.delete'])
        self.validate_delete_string()

    def validate_delete_string(self):
        """Verify whether we are displaying 'Force delete with data loss' string or not"""

        modal_title = 'Confirm delete'
        rdialog = RModalDialog(admin_console=self.admin_console, title=modal_title)
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

    def validate_delete_cloud(self):
        """Validates if a particular cloud storage is deleted or not"""

        cloud_list = self.storage_helper.list_cloud_storage()
        if self.storage_pool_name in cloud_list:
            raise Exception('Cloud storage is not deleted')
        else:
            self.log.info('Cloud storage %s deleted successfully', self.storage_pool_name)

    @test_step
    def delete_cloud_storage(self):
        """Deletes cloud storage"""

        self.storage_helper.delete_cloud_storage(self.storage_pool_name)
        self.validate_delete_cloud()
        self.commcell.storage_pools.refresh()

    def run(self):
        try:
            self.cleanup()
            self.create_cloud_storage()
            self.validate_storage_creation()
            self.validate_mp_creation_for_db()
            self.add_container()
            self.validate_auto_ma_share()
            self.configure_entities()
            self.run_full_backup()
            self.retire_container()
            self.run_incremental_backup()
            self.delete_controller()
            self.run_backup_synthetic_full()
            self.add_controller()
            self.restore()
            self.delete_entities()
            self.delete_container1()
            self.delete_cloud_storage()
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)
