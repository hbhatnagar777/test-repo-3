# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for global encryption KMS case
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample input json
"60828": {
            "MediaAgentName": "ma-name",
            "ClientName": "client-name",
            "AwsAccessKey": "access key",
            "AwsSecretKey": "secret key"    <--- NOT base64 encoded
         }
"""
import base64
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.AdminConsolePages.key_management_servers import KeyManagementServers
from AutomationUtils import commonutils, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Test class for global encryption KMS

    1. Disable global encryption

    2. Create AWS KMS from SDK / Command Center

    3. Create disk storage from Command Center

    4. Associate KMS <2.> with storage pool <3.>

    5. Access the disk storage that was created from Command Center

    6. In the Configuration tab, verify the encryption details

    7. Backup, restore, verify

    """

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for global encryption KMS"
        self.result_string = ""
        self.ma_name = ""
        self.tcinputs = {
            "MediaAgentName": None,
            "ClientName": None,
            "AwsAccessKey": None,
            "AwsSecretKey": None
        }
        self.successful = False
    
    def create_machine_dirs(self, machine_name, machine_dirs, machine_min_storage):
        """Creates machine obj and directories

            Args:
                machine_name        (str)   --  Name of the machine

                machine_dirs        (list)  --  List of directory names to create

                machine_min_storage (int)   --  Min required free storage in GB to check
            
            Returns:
                machine (obj)   --  The machine object created

                dirs    (list)  --  The list of full directory paths created

        """
        machine = self.options_selector.get_machine_object(machine_name)
        
        # drive selection setup
        self.log.info(f'Selecting drive in the client machine {machine_name} based on space available')
        drive = self.options_selector.get_drive(machine, size=machine_min_storage * 1024)
        self.log.info(f'selected drive: {drive}')
        
        created_dirs = []
        for dir in machine_dirs:
            path = machine.join_path(drive, 'Automation', str(self.id), dir)
            if machine.check_directory_exists(path):
                machine.remove_directory(path)
            machine.create_directory(path)
            created_dirs.append(path)
        
        return machine, created_dirs
        

    def setup(self):
        """Initializes test case variables"""
        self.log.info(f"setup {self.id}")

        # general helpers
        self.options_selector = OptionsSelector(self.commcell)
        self.mmhelper_obj = MMHelper(self)

        # name inputs
        self.client_name = self.tcinputs['ClientName']
        self.ma_name = self.tcinputs['MediaAgentName']

        # KMS settings
        self.kms_manager = self.commcell.key_management_servers
        self.kms_name = f"{self.id}_kms"
        self.kms_region = "Asia Pacific (Mumbai)"
        self.kms_access_key = self.tcinputs['AwsAccessKey']
        self.kms_secret_key = self.tcinputs['AwsSecretKey']

        # Commcell storage entitites
        self.client = self.commcell.clients.get(self.client_name)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.storage_pool_name = f"{self.id}_storage"
        self.backupset_name = f"{self.id}_backupset"
        self.subclient_name = f"{self.id}_subclient"
        self.storage_policy_name = f"{self.id}_policy"
        
        # delete CS entities
        self.cleanup()

        # the data size in GB to create
        self.data_gb = 10

        # client machine setup
        machine, dirs = self.create_machine_dirs(self.client_name, ['Testdata', 'Restoredata'], self.data_gb*2)
        self.client_machine = machine
        self.content_path = dirs[0]
        self.restore_dest_path = dirs[1]

        # MA machine setup
        machine, dirs = self.create_machine_dirs(self.ma_name, ['Lib'], self.data_gb)
        self.ma_machine = machine
        self.backup_path = dirs[0]
        
        # admin console setup
        self.username = self.inputJSONnode['commcell']['commcellUsername']
        self.password = self.inputJSONnode['commcell']['commcellPassword']
        self.setup_admin_console()

        # encryption settings
        self.encryption_cipher = 'AES'
        self.encryption_key_length = 128
        self.cipher_conf = f"{self.encryption_cipher}_{self.encryption_key_length}"
    
    def setup_admin_console(self):
        """Initializes the admin console and logs in"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.driver = self.admin_console.driver
            self.admin_console.login(self.username,
                                     self.password)
            self.storage_helper = StorageMain(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info("Test case successful. Cleaning up")
            self.cleanup()
            self.cleanup_dir_path(self.client_machine, self.content_path)
            self.cleanup_dir_path(self.client_machine, self.restore_dest_path)
            self.cleanup_dir_path(self.ma_machine, self.backup_path)
        else:
            self.status = constants.FAILED
    
    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:
                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason
    
    def cleanup_dir_path(self, machine, path):
        """Clears the directory path

            Args:
                machine (obj)   -- The machine object
                
                path    (str)   -- The dir path to delete
        """
        client_name = machine.client_object.client_name
        if machine.check_directory_exists(path):
            machine.remove_directory(path)
            self.log.info(f"Cleared {path} on {client_name}")
        else:
            self.log.info(f"Already cleared {path} on {client_name}")
    
    def enable_encryption_on_copy(self):
        """Enable encryption on storage pool copy"""
        self.commcell.storage_policies.refresh()
        storage_policy = self.commcell.storage_policies.get(self.storage_pool_name)
        primary_copy = storage_policy.get_primary_copy()
        copy_name = primary_copy._copy_name

        self.log.info(f"Now setting {self.kms_name} KMS to {self.storage_pool_name}/{copy_name}")
        primary_copy.set_key_management_server(self.kms_name)
        
        self.log.info(f"Now setting {self.cipher_conf} to {self.storage_pool_name}/{copy_name}")
        primary_copy.copy_reencryption = (True, self.encryption_cipher, self.encryption_key_length, True)
    
    def disable_encryption(self):
        """Disables global encryption"""
        self.mmhelper_obj.disable_global_encryption()

    def create_policy(self, storage_pool_name):
        """Creates a storage policy for data backup/restore"""
        storage_pool_obj = self.commcell.storage_pools.get(storage_pool_name)
        storage_pool_details = storage_pool_obj.storage_pool_properties['storagePoolDetails']

        library_details = storage_pool_details['libraryList'][0]
        library_name = library_details['library']['libraryName']

        policy_obj = self.mmhelper_obj.configure_storage_policy(self.storage_policy_name, library_name, "mm-train-ma")
        return policy_obj
    
    def create_subclient(self):
        """Creates a subclient for data backup/restore"""
        self.mmhelper_obj.configure_backupset(self.backupset_name, self.agent)

        subclient = self.mmhelper_obj.configure_subclient(self.backupset_name, self.subclient_name,
                                                    self.storage_policy_name, self.content_path, self.agent)
        return subclient

    def parse_encryption_info(self, info):
        """
            Parses the encryption info from Command Center

            Args:
                info          (dict)    --  Encryption info from Command Center

            Returns:
                result      (bool)      --  Whether parsing was successful or not

        """
        key = 'Encrypt'
        if key not in info:
            reason = f"{key} key not found in encryption info"
            return self.fail_test_case(reason)
        cipher_enabled = False if info[key] == 'OFF' else True

        key = 'Cipher'
        if key not in info:
            reason = f"{key} key not found in encryption info"
            return self.fail_test_case(reason)
        
        cipher = info[key].split('-')
        cipher = [c.strip() for c in cipher]
        cipher_name = cipher[0]
        cipher_key_length = int(cipher[1])

        key = 'Key management server'
        if key not in info:
            reason = f"{key} key not found in encryption info"
            return self.fail_test_case(reason)
        kms_name = info[key]

        return {
            'enabled': cipher_enabled,
            'cipher': cipher_name,
            'key_length': cipher_key_length,
            'kms': kms_name
        }

    def verify_encryption_info(self, info):
        """
            Verifies the encryption info from Command Center

            Args:
                info    (dict)  --  Encryption info from Command Center

            Returns:
                result  (bool)  --  If verification succeeded or not

        """
        parsed = self.parse_encryption_info(info)
        # {'enabled': False, 'cipher': 'AES', 'key_length': 256, 'kms': 'MurtazaKeyProvider'}
        
        if not parsed:
            return False

        enabled = parsed['enabled']
        if not enabled:
            reason = f"Encryption toggle is not enabled"
            return self.fail_test_case(reason)
        
        cipher = parsed['cipher']
        if cipher.lower() != self.encryption_cipher.lower():
            reason = f"Encryption cipher - Expected: {self.encryption_cipher}, Got: {cipher}"
            return self.fail_test_case(reason)
        
        key_len = parsed['key_length']
        if key_len != self.encryption_key_length:
            reason = f"Encryption key length - Expected: {self.encryption_key_length}, Got: {key_len}"
            return self.fail_test_case(reason)
        
        kms_name = parsed['kms']
        if kms_name.lower() != self.kms_name.lower():
            reason = f"Encryption KMS name - Expected: {self.kms_name}, Got: {kms_name}"
            return self.fail_test_case(reason)

        return True

    def restore_verify(self, machine, src_path, dest_path):
        """
            Performs the verification after restore

            Args:
                machine          (object)    --  Machine class object.

                src_path         (str)       --  path on source machine that is to be compared.

                dest_path        (str)       --  path on destination machine that is to be compared.

            Raises:
                Exception - Any difference from source data to destination data

        """
        self.log.info("Comparing source:%s destination:%s", src_path, dest_path)
        diff_output = machine.compare_folders(machine, src_path, dest_path)

        if not diff_output:
            self.log.info("Checksum comparison successful")
        else:
            self.log.error("Checksum comparison failed")
            self.log.info("Diff output: \n%s", diff_output)
            raise Exception("Checksum comparison failed")

    def cleanup(self):
        """Cleanup the entities created"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete backupset
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            # Delete Storage Policy
            self.commcell.storage_policies.refresh()
            self.log.info("Deleting Storage Policy: %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted Storage Policy: %s", self.storage_policy_name)
            
            # Delete Storage Pool
            self.log.info("Deleting Storage Pool: %s if exists", self.storage_pool_name)
            if self.commcell.storage_policies.has_policy(self.storage_pool_name):
                self.commcell.storage_policies.delete(self.storage_pool_name)
                self.log.info("Deleted Storage Pool: %s", self.storage_pool_name)

            # Delete Library
            self.log.info("Deleting primary copy library: %s if exists", self.storage_pool_name)
            if self.commcell.disk_libraries.has_library(self.storage_pool_name):
                self.commcell.disk_libraries.delete(self.storage_pool_name)
                self.log.info("Deleted library: %s", self.storage_pool_name)
            
            # Delete KMS
            self.log.info("Deleting KMS: %s if exists", self.kms_name)
            self.kms_manager.refresh()
            if self.kms_manager.has_kms(self.kms_name):
                self.kms_manager.delete(self.kms_name)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def create_aws_kms_via_command_center(self):
        """Create AWS KMS via Command Center"""
        navigator = self.admin_console.navigator
        navigator.navigate_to_key_management_servers()
        kms_page = KeyManagementServers(self.admin_console)
        kms_page.add_aws_kmsp(self.kms_name, self.kms_region, self.kms_access_key, self.kms_secret_key)
    
    def create_aws_kms_via_sdk(self):
        """Create AWS KMS via cvpysdk"""
        secret = self.kms_secret_key.encode('ascii')
        secret = base64.b64encode(secret)
        secret = secret.decode('ascii')
        self.kms_manager.add_aws_kms(self.kms_name, self.kms_access_key, secret, self.kms_region)

    def run(self):
        try:
            
            # 1. Enable/Disable global encryption
            self.disable_encryption()

            # 2. Create AWS KMS provider via Command Center
            # TODO: use this once https://engweb.commvault.com/defect/320377 is fixed
            # self.create_aws_kms_via_command_center()
            
            # 2. Create AWS KMS provider via SDK
            self.create_aws_kms_via_sdk()

            # 3. Create a storage pool
            self.storage_helper.add_disk_storage(self.storage_pool_name, self.ma_name, self.backup_path)
            
            # 4. Associate the KMS with the primary copy of the storage pool
            self.enable_encryption_on_copy()

            # 5. Get the encryption details related to this storage
            info = self.storage_helper.disk_encryption_info(self.storage_pool_name)

            # 6. Verify if the info match what was set in the first step
            result = self.verify_encryption_info(info)
            if not result:
                return
            self.log.info(f"Successfully verified the encryption info from Command Center with global settings")

            # 7. Create a storage policy
            self.create_policy(self.storage_pool_name)

            # 8. Create subclient / backupset
            subclient = self.create_subclient()

            # 9. Create data on client to backup
            self.mmhelper_obj.create_uncompressable_data(self.client_name, self.content_path, self.data_gb)

            # 10. Take backup
            self.log.info("Starting Backup")
            job_obj = subclient.backup("FULL")
            if job_obj.wait_for_completion():
                self.log.info("Job status %s", job_obj.status)
            else:
                reason = f"Backup failed: {job_obj.delay_reason}"
                return self.fail_test_case(reason)
            
            # 11. Restore out of place
            self.log.info("Starting Restore")
            job_obj = subclient.restore_out_of_place(self.client, self.restore_dest_path, [self.content_path])
            if job_obj.wait_for_completion():
                self.log.info("Job status %s", job_obj.status)
            else:
                reason = f"Restore failed: {job_obj.delay_reason}"
                return self.fail_test_case(reason)
            
            # 12. Verify restored data
            if self.client_machine.os_info == 'UNIX':
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '/')
            else:
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '\\')

            dest_path = self.client_machine.join_path(dest_path, 'Testdata')

            self.restore_verify(self.client_machine, self.content_path, dest_path)
            
            self.successful = True

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
