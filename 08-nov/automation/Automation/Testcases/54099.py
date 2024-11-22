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
from FileSystem.FSUtils import tdfshelper


class TestCase(CVTestCase):
    """Class for executing

            """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "3dfs ACL acceptance test"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False
        self.tcinputs = {
            "TestPath": None,
            "acl_username": None,
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

        subclient_name = "subclient_{0}_3dfsACL".format(self.id)

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
                    Step 2.1, Create subclient for the test case
                    Step 2.2 ,Enable CatalogACL on subclient
                Step3, Add full data for the current run and set ace for user
                Step4, Run a full backup for the subclient
                       and verify it completes without failures.
                Step5, Create 3dfs share for the subclient
                Step6, Validation for ACLs


        """
        tdfs_obj = tdfshelper.TDfsServerUtils(self, self.tcinputs.get('tdfsserver'))
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            self.helper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)

            self.log.info("Step1, Create backupset for this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(backupset_name, delete=True)

            self.log.info("Step2, Configure test case")

            subclient_content = self.configure_test_case()[0]

            Folder_name = ['ReadAndExecute', 'Write', 'Modify']
            username = self.tcinputs.get('acl_username')
            password = self.tcinputs.get('acl_password')

            self.client_machine.remove_directory(subclient_content)
            self.client_machine.create_directory(subclient_content)
            self.log.info("Step3, Add full data for the current run and set ace for user")
            self.client_machine.modify_ace(
                username,
                subclient_content,
                "Read",
                "Allow",
                True,
                inheritance="1")
            for folder in Folder_name:
                test_path = "{}{}{}".format(subclient_content, self.slash_format, folder)
                Folder_path = "{}{}subFolder".format(test_path, self.slash_format)
                File_path = "{}{}testfile".format(test_path, self.slash_format)
                self.log.info("Adding data under %s" % (test_path))
                self.client_machine.create_directory(Folder_path)
                self.client_machine.create_file(File_path, content="Hello")
                self.client_machine.modify_ace(username, Folder_path, folder, 'Allow', True)
                self.client_machine.modify_ace(username, File_path, folder, "Allow")
                if folder == 'Write':
                    self.client_machine.modify_ace(username, File_path, 'ReadAndExecute', "Allow")
                    self.client_machine.modify_ace(
                        username, Folder_path, 'ReadAndExecute', 'Allow', True)
                if folder == 'Modify':
                    self.client_machine.modify_ace(username, File_path, 'Delete', "Allow")
                    self.client_machine.modify_ace(
                        username, Folder_path, 'DeleteSubdirectoriesAndFiles', "Allow")
                self.log.info("Data is added and ACE is set for folder %s" % folder)

            self.log.info("Step4, Run a full backup for the subclient "
                          "and verify it completes without failures.")
            _ = self.helper.run_backup_verify(backup_level="Full")[0]

            self.log.info("Step5, Create 3dfs share for the subclient")

            subclient_name = self.helper.testcase.subclient.subclient_name

            options = {"subclientName": subclient_name,
                       "enable_acl": "1",
                       "refresh_on_backup": "0"}

            share_name=tdfs_obj.create_3dfs_share(backupset_name, options)

            tdfs_share_path = r"\\\\{}\{}\C$\{}".format(
                tdfs_obj.get_tdfs_ip(), share_name, subclient_name)
            self.log.info("Step6, Validation for ACLs")

            self.client_machine._get_client_ip()
            user_obj = machine.Machine(
                self.client_machine._ip_address,
                username=username,
                password=password)
            for folder in Folder_name:
                Folder_path = "{}{}{}{}subfolder".format(
                    subclient_content, self.slash_format, folder, self.slash_format)
                File_path = "{}{}{}{}testfile".format(
                    subclient_content, self.slash_format, folder, self.slash_format)
                tdfs_Folder_path = "{}{}{}{}subfolder".format(
                    tdfs_share_path, self.slash_format, folder, self.slash_format)
                tdfs_File_path = "{}{}{}{}testfile".format(
                    tdfs_share_path, self.slash_format, folder, self.slash_format)
                tdfs_obj.compare_ace(Folder_path, tdfs_Folder_path, username, user_obj)
                tdfs_obj.compare_ace(File_path, tdfs_File_path, username, user_obj)
                tdfs_obj.validate_user_folder_permission(
                    "Allow", user_obj, folder, tdfs_Folder_path)
                tdfs_obj.validate_user_file_permission("Allow", user_obj, folder, tdfs_File_path)
                self.log.info("ACLs validation is successful for %s " % folder)

            tdfs_obj.delete_3dfs_share(share_name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            tdfs_obj.cleanup_3dfs()
            self.result_string = str(excp)
            self.status = constants.FAILED
