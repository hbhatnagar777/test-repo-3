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

    StorageTarget   -- storage target to be used for tape storage pool

"""
from cvpysdk.policies.storage_policies import StoragePolicies, StoragePolicy

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.Helper.StorageHelper import StorageMain


class TestCase(CVTestCase):
    """Class for SP creation and usage in Admin Console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Storage policy creation and usage from admin console"
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.storage = None
        self.policies = None
        self.policy = None
        self.primary_copy = None
        self.selective_copy = None
        self.synchronous_copy = None
        self.ma_machine = None
        self.client_machine = None
        self.test_data_path = None
        self.media_agent = None
        self.ma_drive = None
        self.client_drive = None
        self.options_selector = None
        self.backupset = None
        self.subclient = None
        self.tcinputs = {
            "StorageTarget": None
        }

    def _cleanup(self, flag=True):
        """
        To perform cleanup operation before setting the environment and after testcase completion

        Args:
            flag        (str)       -- raises Exception if failed to delete an entity if set True

        """
        # To delete backupset if exists
        self.log.info('Deletes backupset backupset_53887 if exists')
        if self.agent.backupsets.has_backupset('backupset_53887'):
            self.agent.backupsets.delete('backupset_53887')
            self.log.info('Successfully deleted backupset: backupset_53887')

        # To delete the storage policy if exists
        self.log.info('Deletes storage policy GDSP_Policy if exists')
        self.storage.delete_storage_policy('GDSP_Policy', flag)

        # To delete the system created subclient if exists
        self.log.info('Deletes system created subclient for storage pool if exists')
        backupset = self.commcell.clients.get(
            self.media_agent).agents.get('File System').backupsets.get('defaultBackupSet')
        if backupset.subclients.has_subclient('DDBBackup'):
            if backupset.subclients.get('DDBBackup').storage_policy == 'GDSP_53887_SystemCreatedSP':
                backupset.subclients.delete('DDBBackup')
                self.log.info('Successfully deleted system created subclient')
            self.log.info('Not deleting subclient as it is associated to another storage policy')

        # To delete the system created storage policy if exists
        self.log.info('Deletes system created storage policy GDSP_53887_SystemCreatedSP if exists')
        self.storage.delete_storage_policy('GDSP_53887_SystemCreatedSP', False)

        # To delete the system created subclient if exists
        self.log.info('Deletes system created subclient for storage pool if exists')
        backupset = self.commcell.clients.get(
            self.media_agent).agents.get('File System').backupsets.get('defaultBackupSet')
        if backupset.subclients.has_subclient('DDBBackup'):
            if backupset.subclients.get('DDBBackup').storage_policy == 'GDSP2_53887_SystemCreatedSP':
                backupset.subclients.delete('DDBBackup')
                self.log.info('Successfully deleted system created subclient')
            self.log.info('Not deleting subclient as it is associated to another storage policy')

        # To delete the system created storage policy if exists
        self.log.info('Deletes system created storage policy GDSP2_53887_SystemCreatedSP if exists')
        self.storage.delete_storage_policy('GDSP2_53887_SystemCreatedSP', False)

        # To delete disk storage pool if exists
        self.log.info('Deletes storage pool GDSP_53887 if exists')
        self.storage.delete_storage_pool('GDSP_53887', flag)

        # To delete disk storage pool if exists
        self.log.info('Deletes storage pool GDSP2_53887 if exists')
        self.storage.delete_storage_pool('GDSP2_53887', flag)

        # To delete tape storage pool if exists
        self.log.info('Deletes storage pool GACP_53887 if exists')
        self.storage.delete_storage_pool('GACP_53887', flag)

        # To clear the generated test data if any
        self.log.info('Removes Test data directory if exists')
        if self.client_machine.check_directory_exists(self.test_data_path):
            self.client_machine.remove_directory(self.test_data_path)
            self.log.info("Test Data directory removed successfully")

        # To remove storage pool path if exists
        self.log.info('Removes GDSP_53887 partition path if exists')
        if self.ma_machine.check_directory_exists(f'{self.ma_drive}GDSP_Path'):
            self.ma_machine.remove_directory(f'{self.ma_drive}GDSP_Path')
            self.log.info("GDSP_53887 Pool path removed successfully")

        # To remove storage pool partition path if exists
        if self.ma_machine.check_directory_exists(f'{self.ma_drive}GDSP_PartitionPath'):
            self.ma_machine.remove_directory(f'{self.ma_drive}GDSP_PartitionPath')
            self.log.info("GDSP_53887 partition path removed successfully")

        # To remove storage pool path if exists
        self.log.info('Removes GDSP2_53887 partition path if exists')
        if self.ma_machine.check_directory_exists(f'{self.ma_drive}GDSP2_Path'):
            self.ma_machine.remove_directory(f'{self.ma_drive}GDSP2_Path')
            self.log.info("GDSP2_53887 Pool path removed successfully")

        # To remove Storage pool partition path if exists
        if self.ma_machine.check_directory_exists(f'{self.ma_drive}GDSP2_PartitionPath'):
            self.ma_machine.remove_directory(f'{self.ma_drive}GDSP2_PartitionPath')
            self.log.info("GDSP2_53887 partition path removed successfully")

    def _run_backup(self, backup_type='Incremental'):
        """
        Initiates backup job and waits for completion

        Args:
            backup_type     (str)   -- Backup type to be run

        Returns:
            object      -- Job class object

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

        return job

    def _run_restore(self, paths):
        """
        Initiates restore job and waits for completion

        Args:
            paths           (list)  -- list of full paths of files/folders to restore

        Returns:
            object      -- Job class object

        """
        job = self.subclient.restore_in_place(paths)
        self.log.info("Started in place restore with Job ID: %s", str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(f"Failed to run restore job with error: {job.delay_reason}")

        self.log.info("Successfully finished in place restore job")

        return job

    def _validate_primary_copy(
            self,
            copy_name=None,
            copy_id=None,
            encryption_type=None,
            key_length=None,
            retention_days=None,
            cycles=None):
        """
        To validate primary copy of the storage policy

        Args:
            copy_name       (str)   -- name of the storage copy

            copy_id         (str)   -- unique id of the storage copy

            encryption_type (str)   -- Encryption type set from admin console

            key_length      (str)   -- Key length set from admin console

            retention_days  (str)   -- retention days set from admin console

            cycles          (str)   -- number of cycles set form admin console

        """
        # Validating Encryption type and keylength
        self.log.info('Validating Encryption type and keylength for copy: %s', copy_name)
        self.storage.validate_copy_encryption(copy_name, copy_id, encryption_type, key_length)

        # Validate retention days and cycles
        self.log.info('Validating retention days and cycles for copy: %s', copy_name)
        self.storage.validate_copy_retention(copy_name, copy_id, retention_days, cycles)

        # Validate client side deduplication is enabled or not
        self.log.info('Validating is client side deduplication is set for copy: %s', copy_name)
        self.storage.validate_clientside_dedupe(copy_name, copy_id)

    def _validate_selective_copy(
            self,
            copy_name=None,
            copy_id=None,
            retention_days=None,
            cycles=None):
        """
        To validate selective GACP copy of the storage policy

        Args:
            copy_name       (str)   -- name of the storage copy

            copy_id         (str)   -- unique id of the storage copy

            retention_days  (str)   -- retention days set from admin console

            cycles          (str)   -- number of cycles set form admin console

        """
        # Validate retention days and cycles
        self.log.info('Validating retention days and cycles for copy: %s', copy_name)
        self.storage.validate_copy_retention(copy_name, copy_id, retention_days, cycles)

        # Validate if MUX is enabled or not
        self.log.info('Validating if MUX is enabled in copy: %s', copy_name)
        self.storage.validate_tape_mux(copy_name, copy_id)

    def _validate_synchronous_copy(
            self,
            copy_name=None,
            copy_id=None,
            encryption_type=None,
            key_length=None,
            retention_days=None,
            cycles=None):
        """
        To validate synchronous copy of the storage policy

        Args:
            copy_name       (str)   -- name of the storage copy

            copy_id         (str)   -- unique id of the storage copy

            encryption_type (str)   -- Encryption type set from admin console

            key_length      (str)   -- Key length set from admin console

            retention_days  (str)   -- retention days set from admin console

            cycles          (str)   -- number of cycles set form admin console

        """
        # Validating Encryption type and keylength
        self.log.info('Validating Encryption type and keylength for copy: %s', copy_name)
        self.storage.validate_copy_encryption(copy_name, copy_id, encryption_type, key_length)

        # Validate retention days and cycles
        self.log.info('Validating retention days and cycles for copy: %s', copy_name)
        self.storage.validate_copy_retention(copy_name, copy_id, retention_days, cycles)

        # Validate readless mode is enabled or not
        self.log.info('Validating whether readless mode is set for copy: %s', copy_name)
        self.storage.validate_readless_mode(copy_name, copy_id)

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
        self.storage = StorageMain(self)
        self.policies = StoragePolicies(self.commcell)

        # To create a machine class object for client machine
        self.log.info("Create Machine class object for client machine: %s", self.client.client_name)
        self.client_machine = Machine(self.client.client_name, self.commcell)

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        self.client_drive = self.options_selector.get_drive(self.client_machine, size=50)
        if self.client_drive is None:
            raise Exception("No free space to generate test data")
        self.log.info('selected drive: %s', self.client_drive)

        # To select the media agent which is ready
        self.media_agent = self.options_selector.get_ma()
        self.log.info('selected media agent: %s', self.media_agent)

        # To create a machine class object for Media Agent machine
        self.log.info("Create Machine class object for MA machine: %s", self.media_agent)
        self.ma_machine = Machine(self.media_agent, self.commcell)

        # To select drive with space available in Media agent machine
        self.log.info('Selecting drive in the Media agent machine based on space available')
        self.ma_drive = self.options_selector.get_drive(self.ma_machine, size=50)
        if self.ma_drive is None:
            raise Exception("No free space to generate test data")
        self.log.info('selected drive: %s', self.ma_drive)

        # Path to generate test data
        self.test_data_path = f'{self.client_drive}TestData'

        # To perform cleanup operations
        self._cleanup(flag=False)

    def run(self):
        """Main function for test case execution"""
        try:
            # To create a new Disk/Cloud storage pool
            self.storage.add_disk_cloud_storage_pool(
                pool_name='GDSP_53887',
                media_agent=self.media_agent,
                storage_target=None,
                username=None,
                password=None,
                path=f'{self.ma_drive}GDSP_Path',
                partition_media_agent=self.media_agent,
                partition_path=f'{self.ma_drive}GDSP_PartitionPath')
            self.log.info('Successfully created Disk storage pool: GDSP_53887')

            # To create a new Disk/Cloud storage pool
            self.storage.add_disk_cloud_storage_pool(
                pool_name='GDSP2_53887',
                media_agent=self.media_agent,
                storage_target=None,
                username=None,
                password=None,
                path=f'{self.ma_drive}GDSP2_Path',
                partition_media_agent=self.media_agent,
                partition_path=f'{self.ma_drive}GDSP2_PartitionPath')
            self.log.info('Successfully created Disk storage pool: GDSP2_53887')

            # To create a new Tape storage pool
            self.storage.add_tape_storage_pool(
                pool_name='GACP_53887',
                storage_target=self.tcinputs.get('StorageTarget'))
            self.log.info('Successfully created Tape storage pool: GACP_53887')

            # Setting Encryption for the created Disk storage pool
            self.storage.encrypt_storage(pool_name='GDSP_53887', cipher='AES', key_length='128')
            self.log.info('Successfully set encryption for storage pool: GDSP_53887')

            # Setting Encryption for the created Disk storage pool
            self.storage.encrypt_storage(pool_name='GDSP2_53887', cipher='AES', key_length='128')
            self.log.info('Successfully set encryption for storage pool: GDSP2_53887')

            # Setting encryption for the created Tape storage pool
            self.storage.encrypt_storage(pool_name='GACP_53887', cipher='AES', key_length='128')
            self.log.info('Successfully set encryption for storage pool: GACP_53887')

            # To create a new storage policy associated to the storage pool
            self.storage.add_storage_policy(
                policy_name='GDSP_Policy',
                storage_pool='GDSP_53887',
                retention='3')
            self.log.info('Successfully created a new storage policy: GDSP_Policy')

            # To Create a selective secondary copy for the created storage policy
            self.storage.add_storage_copy(
                storage_policy='GDSP_Policy',
                copy_name='GACP_Selective_Copy',
                storage_pool='GACP_53887',
                full_backup_frequency='Daily Fulls',
                throttle_network=None,
                data_aging=True,
                retention='2',
                all_backups=False,
                backup_selection=None,
                aux_copy=None)
            self.log.info(
                'Successfully created selective copy GACP_Selective_Copy for the storage policy GDSP_Policy')

            # To set retention days for Tape storage copy
            self.storage.edit_copy_retention(
                policy_name='GDSP_Policy',
                copy_name='GACP_Selective_Copy',
                retention='2')
            self.log.info('Successfully set retention days for Tape storage copy: GACP_Selective_Copy')

            # To create a standalone synchronous copy
            self.storage.add_storage_copy(
                storage_policy='GDSP_Policy',
                copy_name='GDSP_Synchronous_Copy',
                storage_pool='GDSP2_53887',
                full_backup_frequency=None,
                throttle_network=None,
                data_aging=True,
                retention='10',
                all_backups=False,
                backup_selection=None,
                aux_copy=None)
            self.log.info('Successfully created standalone synchronous copy GDSP_Synchronous_Copy')

            # To create a new backupset
            self.backupset = self.agent.backupsets.add('backupset_53887')
            self.log.info('Successfully created a new backupset: backupset_53887')

            # To create an new subclient
            self.subclient = self.backupset.subclients.add('subclient_53887', 'GDSP_Policy')
            self.log.info('Successfully created a new subclient: subclient_53887')

            # To read subclients contents
            self.log.info("Read subclient content")
            self.log.info("Subclient Content: %s", self.subclient.content)

            # To add test data generated to subclient's contents
            self.log.info("Add test data path to subclient content")
            self.subclient.content += [self.test_data_path]

            # To Generate data for backup
            self.log.info("Generating test data at: %s for client: %s", self.test_data_path, self.client.client_name)
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

            # To create copy objects for all the storage copies created
            self.policy = StoragePolicy(self.commcell, 'GDSP_Policy')
            self.primary_copy = self.policy.get_copy('Primary')
            self.selective_copy = self.policy.get_copy('GACP_Selective_Copy')
            self.synchronous_copy = self.policy.get_copy('GDSP_Synchronous_Copy')

            # To get the primary copy id
            primary_copy_id = self.primary_copy.get_copy_id()
            self.log.info('Primary copy ID: %s', primary_copy_id)

            # To get primary copy precedence
            primary_copy_precedence = self.storage.get_copy_precedence(primary_copy_id)
            self.log.info('Primary copy precedence: %s', primary_copy_precedence)

            # To get the selective copy id
            selective_copy_id = self.selective_copy.get_copy_id()
            self.log.info('selective copy ID: %s', selective_copy_id)

            # To get selective secondary copy precedence
            selective_copy_precedence = self.storage.get_copy_precedence(selective_copy_id)
            self.log.info('selective copy precedence: %s', selective_copy_precedence)

            # To get the synchronous copy id
            synchronous_copy_id = self.synchronous_copy.get_copy_id()
            self.log.info('synchronous copy ID: %s', synchronous_copy_id)

            # To get synchronous copy precedence
            synchronous_copy_precedence = self.storage.get_copy_precedence(synchronous_copy_id)
            self.log.info('synchronous copy precedence: %s', synchronous_copy_precedence)

            # To validate primary copy
            self._validate_primary_copy(
                copy_name='Primary',
                copy_id=primary_copy_id,
                encryption_type='AES',
                key_length='128',
                retention_days='3',
                cycles='1'
            )

            # To validate selective copy
            self._validate_selective_copy(
                copy_name='GACP_Selective_Copy',
                copy_id=selective_copy_id,
                retention_days='2',
                cycles='1',
            )

            # To validate synchronous copy
            self._validate_synchronous_copy(
                copy_name='GDSP_Synchronous_Copy',
                copy_id=synchronous_copy_id,
                encryption_type='AES',
                key_length='128',
                retention_days='10',
                cycles='1',
            )

        except Exception as exp:
            self.browser.close()
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """To clean-up the test case environment created"""
        self._cleanup(flag=True)
        self.browser.close()
