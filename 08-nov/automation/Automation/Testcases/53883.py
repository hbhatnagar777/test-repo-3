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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Inputs:

    KMIPServer      --  Name of the server for KMIP

    KMIPPort        --  Port for the KMS

    Passphrase      --  Passphrase for the KMS

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.Helper.StorageHelper import StorageMain


class TestCase(CVTestCase):
    """Class for configuring KMIP server in Admin Console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "KMIP server configuration and usage from Adminconsole"
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.storage = None
        self.backupset = None
        self.subclient = None
        self.commcell_machine = None
        self.client_machine = None
        self.ma_machine = None
        self.certificate_path = None
        self.test_data_path = None
        self.media_agent = None
        self.ma_drive = None
        self.client_drive = None
        self.options_selector = None
        self.tcinputs = {
            "KMIPServer": None,
            "KMIPPort": None,
            "Passphrase": None
        }

    def _cleanup(self, flag=True):
        """
        To perform cleanup operation before setting the environment and after testcase completion

        Args:
            flag        (str)       -- raises Exception if failed to delete an entity if set True

        """
        # To delete backupset if exists
        self.log.info('Deletes backupset KMIP_Backupset if exists')
        if self.agent.backupsets.has_backupset('KMIP_Backupset'):
            self.agent.backupsets.delete('KMIP_Backupset')
            self.log.info('Successfully deleted backupset: KMIP_Backupset')

        # To delete the storage policy if exists
        self.log.info('Deletes storage policy KMIP_Policy if exists')
        self.storage.delete_storage_policy('KMIP_Policy', flag)

        # To delete the system created subclient if exists
        self.log.info('Deletes system created subclient KMIP_Pool_SystemCreatedSP if exists')
        backupset = self.commcell.clients.get(
            self.media_agent).agents.get('File System').backupsets.get('defaultBackupSet')
        if backupset.subclients.has_subclient('DDBBackup'):
            if backupset.subclients.get('DDBBackup').storage_policy == 'KMIP_Pool_SystemCreatedSP':
                backupset.subclients.delete('DDBBackup')
                self.log.info('Successfully deleted system created subclient')
            self.log.info('Not deleting subclient as it is associated to another storage policy')

        # To delete the system created storage policy if exists
        self.log.info('Deletes system created storage policy KMIP_Pool_SystemCreatedSP if exists')
        self.storage.delete_storage_policy('KMIP_Pool_SystemCreatedSP', False)

        # To delete storage pool if exists
        self.log.info('Deletes storage pool KMIP_Pool if exists')
        self.storage.delete_storage_pool('KMIP_Pool', flag)

        # To delete the Key management server if exists
        self.log.info('Deletes Key management server KMIP_53883 if exists')
        self.storage.delete_kms('KMIP_53883', flag)

        # To clear the generated test data if any
        self.log.info('Removes Test data directory if exists')
        if self.client_machine.check_directory_exists(self.test_data_path):
            self.client_machine.remove_directory(self.test_data_path)
            self.log.info("Test Data directory removed successfully")

        # To clear certificate path of KMIP server if exists
        self.log.info('Removes KMIP certificate path if exists')
        if self.commcell_machine.check_directory_exists(self.certificate_path):
            self.commcell_machine.remove_directory(self.certificate_path)
            self.log.info("KMIP Certificate directory removed successfully")

        # To remove storage pool path if exists
        self.log.info('Removes Disk storage pool path if exists')
        if self.ma_machine.check_directory_exists(f'{self.ma_drive}KMIP_PartitionPath'):
            self.ma_machine.remove_directory(f'{self.ma_drive}KMIP_PartitionPath')
            self.log.info("GDSP_53887 Pool path removed successfully")

        # To remove storage pool partition path if exists
        self.log.info('Removes Disk storage pool partition path if exists')
        if self.ma_machine.check_directory_exists(f'{self.ma_drive}KMIP_Pool'):
            self.ma_machine.remove_directory(f'{self.ma_drive}KMIP_Pool')
            self.log.info("GDSP_53887 partition path removed successfully")

    def _run_backup(self, backup_type='Incremental'):
        """
        Initiates backup job and waits for completion

        Args:
            backup_type     (str)   -- Backup type to be run
                                        default: Incremental

        Returns:
            None

        """
        job = self.subclient.backup(backup_type)
        self.log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )

        self.log.info("Successfully finished %s backup job", backup_type)

    def _run_restore(self, paths):
        """
        Initiates restore job and waits for completion

        Args:
            paths     (list)   -- list of full paths of files/folders to restore

        Returns:
            None

        """
        job = self.subclient.restore_in_place(paths)
        self.log.info("Started in place restore with Job ID: %s", str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(f"Failed to run restore job with error: {job.delay_reason}")

        self.log.info("Successfully finished in place restore job")

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.log.info("Creating the self.login object")
        self.login_obj = LoginMain(self.driver, self.csdb)
        self.login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
                             self.inputJSONnode['commcell']['commcellPassword']
                             )

        self.options_selector = OptionsSelector(self.commcell)

        # To initialize the helper file
        self.storage = StorageMain(self)
        self.log.info('Successfully initiated storage helper')

        # To create a machine class object for client machine
        self.log.info("Create Machine class object for client machine: %s", self.client.client_name)
        self.client_machine = Machine(self.client.client_name, self.commcell)

        # To create a machine class object for commcell machine
        self.log.info("Create Machine class object for commcell machine: %s", self.commcell.commserv_name)
        self.commcell_machine = Machine(self.commcell.commserv_name, self.commcell)

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        self.client_drive = self.options_selector.get_drive(self.client_machine, size=50)
        if self.client_drive is None:
            raise Exception("No free space to generate test data")
        self.log.info('selected drive: %s', self.client_drive)

        # To select the media agent which is ready
        self.media_agent = self.options_selector.get_ma()
        self.log.info('selected media agent: %s', self.media_agent)

        # To create a machine class object for    machine: %s", self.media_agent)
        self.ma_machine = Machine(self.media_agent, self.commcell)

        # To select drive with space available in Media agent machine
        self.log.info('Selecting drive in the Media agent machine based on space available')
        self.ma_drive = self.options_selector.get_drive(self.ma_machine, size=50)
        if self.ma_drive is None:
            raise Exception("No free space to generate test data")
        self.log.info('selected drive: %s', self.ma_drive)

        # Path to generate test data
        self.test_data_path = f'{self.client_drive}TestData'

        # Path for KMIP certificate
        self.certificate_path = f'{self.ma_drive}Certificate_53883'

        # To perform cleanup operations
        self._cleanup(flag=False)

    def run(self):
        """Main function for test case execution"""

        try:
            # To create certificate path if not exists
            if not self.commcell_machine.check_directory_exists(self.certificate_path):
                self.commcell_machine.create_directory(self.certificate_path)

            # To add new KMIP server
            self.storage.add_kmip_server(
                name='KMIP_53883',
                key_length='128',
                server=self.tcinputs.get('KMIPServer'),
                port=self.tcinputs.get('KMIPPort'),
                passphrase=self.tcinputs.get('Passphrase'),
                certificate=self.certificate_path,
                certificate_key=self.certificate_path,
                ca_certificate=self.certificate_path)
            self.log.info('Successfully created a new KMIP server: KMIP_53883')

            # To add a new Disk/Cloud storage pool
            self.storage.add_disk_cloud_storage_pool(
                pool_name='KMIP_Pool',
                media_agent=self.media_agent,
                storage_target=None,
                username=None,
                password=None,
                path=f'{self.ma_drive}KMIP_Pool',
                partition_media_agent=self.media_agent,
                partition_path=f'{self.ma_drive}KMIP_PartitionPath')
            self.log.info('Successfully created a new storage pool: KMIP_Pool')

            # To associate KMIP server with the storage pool
            self.storage.encrypt_storage(
                pool_name='KMIP_Pool',
                cipher='AES',
                key_length='128',
                key_management_server='KMIP_53883')
            self.log.info('Successfully associated the storage pool KMIP_Pool with the KMIP server')

            # To create a storage policy
            self.storage.add_storage_policy(
                policy_name='KMIP_Policy',
                storage_pool='KMIP_Pool')
            self.log.info('Successfully created a new storage policy: KMIP_Policy')

            # To create a new backupset
            self.backupset = self.agent.backupsets.add('KMIP_Backupset')
            self.log.info('Successfully created a new Backupset: KMIP_Backupset')

            # To create a new subclient
            self.subclient = self.backupset.subclients.add('KMIP_Subclient', 'KMIP_Policy')
            self.log.info('Successfully created a new subclient: KMIP_Subclient')

            # To read subclients contents
            self.log.info("Read subclient content")
            self.log.info("Subclient Content: %s", self.subclient.content)

            # To add test data generated to subclient's contents
            self.log.info("Add test data path to subclient content")
            self.subclient.content += [self.test_data_path]

            # To Generate data for backup
            self.log.info("Generating test data at: %s", self.test_data_path)
            self.client_machine.generate_test_data(self.test_data_path)

            # Get hash of the files/folder generated
            before_restore = self.client_machine.get_folder_hash(self.test_data_path)

            # To run Full backup and restore
            self._run_backup('FULL')
            self._run_restore([self.test_data_path])

            # Get hash of the files/folders after restore
            after_restore = self.client_machine.get_folder_hash(self.test_data_path)

            # To validate restore
            self.storage.validate_restore(before_restore, after_restore)

            # To Generate data for backup
            self.log.info("Generating test data at: %s", self.test_data_path)
            self.client_machine.generate_test_data(self.test_data_path)

            # Get hash of the files/folder generated
            before_restore = self.client_machine.get_folder_hash(self.test_data_path)

            # To run Incremental backup and restore
            self._run_backup('INCREMENTAL')
            self._run_restore([self.test_data_path])

            # Get hash of the files/folders after restore
            after_restore = self.client_machine.get_folder_hash(self.test_data_path)

            # To validate restore
            self.storage.validate_restore(before_restore, after_restore)

        except Exception as exp:
            self.browser.close()
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """To clean-up the test case environment created"""
        self._cleanup(flag=True)
        self.browser.close()
