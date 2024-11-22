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
import time


class TestCase(CVTestCase):
    """Class for executing

            """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "3dfs Backupset share test"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION

        self.tcinputs = {
            "TestPath": None,
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

    def configure_test_case(self, refresh=False):
        """
        Function that handles subclient creation, and any special configurations


        Returns:
            None
        """

        self.log.info("Create subclient for the test case ")
        subclient_content = list()
        if not refresh:
            subclient_name = "subclient_{0}_1".format(self.id)
        else:
            subclient_name = "subclient_{0}_2".format(self.id)

        subclient_content.append(
            '{}{}{}'.format(
                self.test_path,
                self.slash_format,
                subclient_name))

        self.helper.create_subclient(
            name=subclient_name,
            storage_policy=self.storage_policy,
            content=subclient_content)

        return subclient_content

    def run(self):
        """Main function for test case execution


            This test case does the following:
                Step1, Create backupset for this testcase.If it exist, delete it
                Step2, Create 3dfs share for the backupset
                Step3, Configure test case
                Step4, Adding test data for the subclient
                Step5, Run a full backup for first subclient
                        and verify it completes without failures.
                Step6, Compare source and share data
                Step7, Creating second subclient for the testcase
                Step8, Adding test data for the subclient
                Step9, Run a full backup for second subclient
                Step10, Compare source and share data

        """

        try:

            self.log.info("***TESTCASE: %s***", self.name)
            self.log.info("Creating tdfsserver object")
            tdfs_obj = tdfshelper.TDfsServerUtils(
                self, self.tcinputs.get('tdfsserver'))
            # Initialize test case inputs
            self.helper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)

            self.log.info(
                "Step1, Create backupset for this testcase.If it exist, delete it")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(backupset_name, delete=True)

            self.log.info("Step2, Create 3dfs share for the backupset")

            share_name = tdfs_obj.create_3dfs_share(backupset_name)

            self.log.info("Step3, Configure test case")
            self.log.info("Creating first subclient for the testcase")

            subclient_content = self.configure_test_case()[0]

            self.log.info("Creating subclient content %s" % subclient_content)
            self.client_machine.create_directory(subclient_content, True)
            mountpoint = f"{tdfs_obj.tdfs_machine_obj.os_sep}{str(share_name)}"

            self.log.info("Mount the share to %s" % mountpoint)
            tdfs_obj.tdfs_machine_obj.mount_nfs_share(
                mountpoint,
                tdfs_obj.get_tdfs_ip(),
                tdfs_obj.tdfs_machine_obj.os_sep +
                share_name)

            self.log.info("Step4, Adding test data for the subclient")
            self.client_machine.generate_test_data(
                subclient_content, dirs=5, files=20, file_size=50, sparse=False)
            self.log.info("Step5, Run a full backup for first subclient "
                          "and verify it completes without failures.")
            _ = self.helper.run_backup_verify(backup_level="Full")[0]

            self.log.info(
                "Test case will sleep for 60 seconds for forever share")
            time.sleep(60)

            self.log.info("Step6, Compare source and share data")
            if tdfs_obj.data_copy_compare(
                    self.client_machine,
                    mountpoint,
                    subclient_content):
                self.log.info("Items in Source and destination match")
            else:
                raise Exception("Source and Destination differ")

            self.log.info("Step7, Creating second subclient for the testcase")
            subclient_content = self.configure_test_case(True)[0]

            self.log.info("Removing subclient content %s" % subclient_content)
            self.client_machine.remove_directory(subclient_content)
            self.log.info("Creating subclient content %s" % subclient_content)
            self.client_machine.create_directory(subclient_content)

            self.log.info("Step8, Adding test data for the subclient")
            self.client_machine.generate_test_data(
                subclient_content, dirs=5, files=20, file_size=50, sparse=False)

            self.log.info("Step9, Run a full backup for second subclient "
                          "and verify it completes without failures.")
            _ = self.helper.run_backup_verify(backup_level="Full")[0]

            self.log.info(
                "Test case will sleep for 60 seconds for forever share")
            time.sleep(60)
            self.log.info("Step10, Compare source and share data")

            if tdfs_obj.data_copy_compare(
                    self.client_machine,
                    mountpoint,
                    subclient_content):
                self.log.info("Items in Source and destination match")
            else:
                raise Exception("Source and Destination differ")
            self.log.info("Step12, Cleanup the share and mount point")
            tdfs_obj.tdfs_machine_obj.unmount_path(mountpoint)
            tdfs_obj.delete_3dfs_share(share_name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            try:
                tdfs_obj.cleanup_3dfs()
                tdfs_obj.tdfs_machine_obj.unmount_path(mountpoint)
            except NameError:
                self.log.info("Share and mount point removed")
            self.result_string = str(excp)
            self.status = constants.FAILED
