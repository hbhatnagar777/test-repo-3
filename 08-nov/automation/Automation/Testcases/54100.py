# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initialize TestCase class

    setup()                 --  create fshelper object

    configure_test_case()   --  Handles subclient creation, and any special configurations.

    run()                   --  run function of this test case
"""

from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
import time
from FileSystem.FSUtils import tdfshelper


class TestCase(CVTestCase):
    """Class for executing

            """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "3dfs ACL group and user test"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False
        self.tcinputs = {
            "TestPath": None,
            "acl_username1": None,
            "acl_username2": None,
            "acl_groupname": None,
            "acl_password": None,
            "tdfsserver": None,
            "StoragePolicyName": None


        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.subclient_content = None
        self.tmp_path = None

    def setup(self):
        self.helper = FSHelper(self)

    def configure_test_case(self):
        """
        Function that handles subclient creation, and any special configurations


        Returns:
            None
        """

        self.log.info("Step 2.1, Create subclient for the test case ")
        subclient_content = list()

        subclient_name = "subclient_{0}".format(self.id)

        subclient_content.append(
            '{}{}{}'.format(
                self.test_path,
                self.slash_format,
                subclient_name))

        self.helper.create_subclient(name=subclient_name, storage_policy=self.storage_policy,
                                     content=subclient_content)

        self.log.info("Step 2.2 ,Enable CatalogACL on subclient")

        # Need to add code to enable acl

        self.helper.update_subclient(catalog_acl=True)

        self.log.info("Catalog ACL is enabled on the subclient")

        return subclient_content

    def run(self):
        """Main function for test case execution
            This test case does the following:
                Step1, Create backupset for this testcase if it doesn't exist
                Step2, Configure test case
                    Step2.1, Create subclient for the test case
                    Step 2.2, Enable Catalog ACL on it
                Step3, Add full data for the current run and set ace for user
                Step4, Giving access of both the files to user
                Step5, Run a full backup for the subclient
                        and verify it completes without failures
                Step6, Create 3dfs share for the subclient
                Step7, Start validation of ACLs
                Step8, Add Ace for group and change permsision to deny for user
                Step9, Run a Incremental backup for the subclient
                       and verify it completes without failures.
                Step 10, Validate changed ACLs
                Step11, Remove u2 deny permission and run incremental backup
                Step12, Run a Incremental backup for the subclient
                        and verify it completes without failures

                Step13, Validate changed ACLs





        """
        tdfs_obj = tdfshelper.TDfsServerUtils(self, self.tcinputs['tdfsserver'])
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            username1 = self.tcinputs.get('acl_username1')
            username2 = self.tcinputs.get('acl_username2')
            password = self.tcinputs.get('acl_password')
            groupname = self.tcinputs.get('acl_groupname')

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)

            self.log.info("Step1, Create backupset for this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(backupset_name, delete=True)

            self.log.info("Step2, Configure test case")

            permission = 'ReadAndExecute'
            subclient_content = self.configure_test_case()[0]

            self.client_machine.remove_directory(subclient_content)
            self.client_machine.create_directory(subclient_content)

            self.log.info("Step3, Add full data for the current run and set ace for user")

            Folder_path = "{}{}subFolder".format(subclient_content, self.slash_format)
            File_path = "{}{}testfile".format(subclient_content, self.slash_format)

            self.log.info("Adding data under %s" % (subclient_content))
            self.client_machine.modify_ace(username1, subclient_content, permission, 'Allow', True)
            self.client_machine.modify_ace(username2, subclient_content, permission, 'Allow', True)
            self.client_machine.create_directory(Folder_path)
            self.client_machine.create_file(File_path, content="Hello")

            self.log.info(
                "Step4, Setting allow read for username {} and {}".format(
                    username1, username2))
            self.client_machine.modify_ace(username1, Folder_path, permission, 'Allow', True)
            self.client_machine.modify_ace(username2, Folder_path, permission, 'Allow', True)
            self.client_machine.modify_ace(username1, File_path, permission, "Allow")
            self.client_machine.modify_ace(username2, File_path, permission, "Allow")

            self.log.info("Step5, Run a full backup for the subclient "
                          "and verify it completes without failures.")
            _ = self.helper.run_backup_verify(backup_level="Full")[0]

            self.log.info("Step6, Create 3dfs share for the subclient")

            subclient_name = self.helper.testcase.subclient.subclient_name
            options = {"subclientName": subclient_name,
                       "enable_acl": "1"
                       }
            share_name = tdfs_obj.create_3dfs_share(backupset_name, options)

            self.log.info("Step7, Start validation of ACLs ")
            tdfs_Folder_path = "\\\\{}\\{}\\C$\\{}\\subFolder".format(
                tdfs_obj.get_tdfs_ip(), share_name, subclient_name)
            tdfs_File_path = "\\\\{}\\{}\\C$\\{}\\testfile".format(
                tdfs_obj.get_tdfs_ip(), share_name, subclient_name)
            self.client_machine._get_client_ip()

            user_obj1 = machine.Machine(
                self.client_machine._ip_address,
                username=username1,
                password=password)
            tdfs_obj.compare_ace(Folder_path, tdfs_Folder_path, username1, user_obj1)
            tdfs_obj.compare_ace(Folder_path, tdfs_Folder_path, username2, user_obj1)
            tdfs_obj.compare_ace(File_path, tdfs_File_path, username1, user_obj1)
            tdfs_obj.compare_ace(File_path, tdfs_File_path, username2, user_obj1)
            tdfs_obj.validate_user_folder_permission(
                "Allow", user_obj1, permission, tdfs_Folder_path)
            tdfs_obj.validate_user_file_permission("Allow", user_obj1, permission, tdfs_File_path)

            user_obj2 = machine.Machine(self.client_machine._ip_address, username=username2,
                                        password=password)
            tdfs_obj.validate_user_folder_permission(
                "Allow", user_obj2, permission, tdfs_Folder_path)
            tdfs_obj.validate_user_file_permission("Allow", user_obj2, permission, tdfs_File_path)

            self.log.info(
                "Step8, Add Ace for group %s and change permsision to deny for user %s" %
                (groupname, username2))

            self.client_machine.modify_ace(username1, Folder_path, 'Write', 'Allow', True)
            test_path = "{}\\testfile".format(Folder_path)
            self.client_machine.create_file(test_path, content="Hello")

            self.client_machine.modify_ace(groupname, Folder_path, permission, 'Allow', True)
            self.client_machine.modify_ace(groupname, File_path, permission, "Allow")

            self.client_machine.modify_ace(username2, Folder_path, permission, "Allow", True, True)
            self.client_machine.modify_ace(username2, File_path, permission, "Allow", False, True)

            self.client_machine.modify_ace(username2, Folder_path, permission, "Deny", True)
            self.client_machine.modify_ace(username2, File_path, permission, "Deny")

            self.log.info("Step9, Run a Incremental backup for the subclient "
                          "and verify it completes without failures.")
            _ = self.helper.run_backup_verify()[0]

            self.log.info("Test case will sleep for 60 seconds for forever share")
            time.sleep(60)

            self.log.info("Step10, Validate changed ACLs")

            user_obj1 = machine.Machine(
                self.client_machine._ip_address,
                username=username1,
                password=password)
            tdfs_obj.compare_ace(Folder_path, tdfs_Folder_path, username1, user_obj1)
            tdfs_obj.compare_ace(Folder_path, tdfs_Folder_path, username2, user_obj1)
            tdfs_obj.compare_ace(Folder_path, tdfs_Folder_path, groupname, user_obj1)
            tdfs_obj.compare_ace(File_path, tdfs_File_path, username1, user_obj1)
            tdfs_obj.compare_ace(File_path, tdfs_File_path, username2, user_obj1)
            tdfs_obj.compare_ace(File_path, tdfs_File_path, groupname, user_obj1)

            tdfs_obj.validate_user_folder_permission(
                "Allow", user_obj1, permission, tdfs_Folder_path)
            tdfs_obj.validate_user_file_permission("Allow", user_obj1, permission, tdfs_File_path)

            user_obj2 = machine.Machine(self.client_machine._ip_address, username=username2,
                                        password=password)

            tdfs_obj.validate_user_folder_permission(
                "Deny", user_obj2, permission, tdfs_Folder_path)
            tdfs_obj.validate_user_file_permission("Deny", user_obj2, permission, tdfs_File_path)

            self.log.info("Step11, Remove u2 deny permission and run incremental backup")
            self.client_machine.modify_ace(username1, Folder_path, 'Write', 'Allow', True)
            test_path = "{}\\testfile1".format(Folder_path)
            self.client_machine.create_file(test_path, content="Hello")
            self.client_machine.modify_ace(username1, File_path, 'Write', 'Allow', True)
            self.client_machine.append_to_file(File_path, content="Cvappend")
            self.client_machine.modify_ace(username2, Folder_path, permission, "Deny", True, True)
            self.client_machine.modify_ace(username2, File_path, permission, "Deny", False, True)
            self.log.info("Step12, Run a Incremental backup for the subclient "
                          "and verify it completes without failures.")
            _ = self.helper.run_backup_verify()[0]

            self.log.info("Test case will sleep for 60 seconds for forever share")
            time.sleep(60)

            self.log.info("Step 13, Validate changed ACLs")

            user_obj1 = machine.Machine(
                self.client_machine._ip_address,
                username=username1,
                password=password)
            tdfs_obj.compare_ace(Folder_path, tdfs_Folder_path, username1, user_obj1)
            tdfs_obj.compare_ace(Folder_path, tdfs_Folder_path, groupname, user_obj1)

            tdfs_obj.compare_ace(File_path, tdfs_File_path, username1, user_obj1)
            tdfs_obj.compare_ace(File_path, tdfs_File_path, groupname, user_obj1)
            tdfs_obj.validate_user_file_permission("Allow", user_obj1, permission, tdfs_File_path)
            tdfs_obj.validate_user_folder_permission(
                "Allow", user_obj1, permission, tdfs_Folder_path)

            user_obj2 = machine.Machine(self.client_machine._ip_address, username=username2,
                                        password=password)

            tdfs_obj.validate_user_folder_permission(
                "Allow", user_obj2, permission, tdfs_Folder_path)
            tdfs_obj.validate_user_file_permission("Allow", user_obj2, permission, tdfs_File_path)
            tdfs_obj.delete_3dfs_share(share_name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            tdfs_obj.cleanup_3dfs()
            self.result_string = str(excp)
            self.status = constants.FAILED
