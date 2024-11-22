# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    setup()                --  create fshelper object

    run()                   --  run function of this test case

    This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
        Step2, Create subclient if it doesn't exist.
        Step3, Add full data for the current run.
        Step4, Run a full backup for the subclient
            and verify it completes without failures.
        Step5, Create share for the subclient
        Step6, Mount the share on nfs client
        Step7, Compare the data on nfs client with that of the source data
        Step8, Add new data for the incremental
        Step9,  Run an incremental job for the subclient
        Step10, Compare the data on nfs client with that of the source data
        Step11, Add new data for the Differentials
        Step12,  Run a differential job for the subclient
        Step13, Compare the data on nfs client with that of the source data
        Step14, Run a synthfull job
        Step15, Add new data for the Incremental
        Step16,  Run an incremental job for the subclient
        Step17, Compare the data on nfs client with that of the source data
    """
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper
from FileSystem.FSUtils import tdfshelper


class TestCase(CVTestCase):
    """Class for executing
     3DFS forever/Refresh on backup share for File System

     The Refresh on Backup is new feature for 3DFS which keeps the
     3DFS share always up to date with the most recent backup data.

     The share content is refreshed after every successful backup job
     operation on the subclient.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "3DFS for File System Test"

        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "tdfsserver": None

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

        self.dfsma = None
        self.sharename = None
        self.runid = None

    def setup(self):
        """Setup function"""
        self.helper = FSHelper(self)

    def run(self):
        # Main function for test case execution
        try:
            # Initialize test case inputs
            self.log.info("Creating tdfs object")
            tdfs_obj = tdfshelper.TDfsServerUtils(
                self, self.tcinputs.get('tdfsserver'))
            self.helper.populate_tc_inputs(self)

            self.log.info("Refresh on Backup for 3DFS File System Test")
            # creating backupset
            self.log.info("Step1, Create backupset for "
                          "this testcase if it doesn't exist")
            backupset_name = "backupset_{}".format(self.id)
            self.helper.create_backupset(backupset_name)
            # creating subclient

            self.log.info("Step2,  Create subclient for the test case ")

            subclient_name = f"subclient_{self.id}"

            subclient_content = []
            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            subclient_content.append(
                f"{self.test_path}{self.slash_format}{subclient_name}")

            self.client_machine.create_directory(subclient_content[0], True)

            full_data_path = f"{subclient_content[0]}{self.slash_format}full"

            self.helper.create_subclient(name=subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=subclient_content)

            self.log.info("Step3,  Add full data for the current run.")
            self.log.info("Adding data under path: %s", full_data_path)

            self.client_machine.generate_test_data(
                full_data_path, sparse=False)

            self.log.info("Step4,  Run a full backup for the subclient "
                          "and verify it completes without failures.")
            self.helper.run_backup_verify(backup_level="Full")[0]
            self.log.info(
                "Test case will sleep for 60 seconds for forever share")
            time.sleep(60)

            #self.log.info(" backupset name: " .format(backupset_name))
            self.log.info("Step5,Create share for the subclient")

            share_name = tdfs_obj.create_3dfs_share(
                backupset_name, extra_option={'subclientName': subclient_name})
            # mount share
            mountpoint_name = f"{tdfs_obj.tdfs_machine_obj.os_sep}{str(share_name)}"
            self.log.info("Step6, Mount the exported share")

            tdfs_obj.tdfs_machine_obj.mount_nfs_share(
                mountpoint_name,
                tdfs_obj.get_tdfs_ip(),
                tdfs_obj.tdfs_machine_obj.os_sep +
                share_name)

            # Comparing the data on the nfs mounted path and the source machine
            # path
            self.log.info("step7, Compare the share data "
                          "on nfs client with that of the source data")
            if tdfs_obj.data_copy_compare(
                    self.client_machine,
                    mountpoint_name,
                    subclient_content[0]):
                self.log.info("Items in Source and destination match")
            else:
                raise Exception("Source and Destination differ")

            # Incremental job
            self.log.info("Step8,  Add new data for the incremental")
            incr_diff_data_path = f"{subclient_content[0]}{self.slash_format}incr_diff"
            self.helper.add_new_data_incr(
                incr_diff_data_path, self.slash_format)

            self.log.info("Step9,  Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            # job_incr1 = \
            self.helper.run_backup_verify(backup_level="Incremental")
            self.log.info(
                "Test case will sleep for 60 seconds for forever share")
            time.sleep(60)
            # Comparing the data in the nfs mounted path and the source machine
            # path
            self.log.info(
                "step10, Compare the data on nfs client with that of the source data")

            if tdfs_obj.data_copy_compare(
                    self.client_machine,
                    mountpoint_name,
                    subclient_content[0]):
                self.log.info("Items in Source and destination match")
            else:
                raise Exception("Source and Destination differ")

            # Add new data for differential job
            self.log.info("Step11, Add new data for the differential")
            incr_new_diff_path = f"{subclient_content[0]}{self.slash_format}diff"

            self.client_machine.generate_test_data(
                incr_new_diff_path, acls=True, xattr=True, sparse=False)

            self.log.info("Step12,  Run an differential job for the subclient"
                          " and verify it completes without failures.")
            # job_incr1 = \
            self.helper.run_backup_verify(backup_level="Differential")
            self.log.info(
                "Test case will sleep for 60 seconds for forever share")
            time.sleep(60)
            # Comparing the data in the nfs mounted path and the source machine
            # path
            self.log.info(
                "step13, Compare the data on nfs client with that of the source data")

            if tdfs_obj.data_copy_compare(
                    self.client_machine,
                    mountpoint_name,
                    subclient_content[0]):
                self.log.info("Items in Source and destination match")
            else:
                raise Exception("Source and Destination differ")

            # Run Synthfull job
            self.log.info("Step14, Run a synthfull job")
            self.helper.run_backup_verify(backup_level="Synthetic_full")

            self.log.info(
                "Test case will sleep for 60 seconds for forever share")
            time.sleep(60)
            # Comparing the data in the nfs mounted path and the source machine
            # path
            self.log.info(
                "step15, Compare the data on nfs client with that of the source data")

            if tdfs_obj.data_copy_compare(
                    self.client_machine,
                    mountpoint_name,
                    subclient_content[0]):
                self.log.info("Items in Source and destination match")
            else:
                raise Exception("Source and Destination differ")
            # Incremental job
            self.log.info("Step16,  Add new data for the incremental")
            incr_diff_data_path = f"{subclient_content[0]}{self.slash_format}incr_synthfull"
            self.client_machine.generate_test_data(
                incr_diff_data_path, sparse=False)

            self.log.info("Step17,  Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            # job_incr1 = \
            self.helper.run_backup_verify(backup_level="Incremental")

            # Comparing the data in the nfs mounted path and the source machine
            # path
            self.log.info(
                "Test case will sleep for 60 seconds for forever share")
            time.sleep(60)
            # Comparing the data in the nfs mounted path and the source machine
            # path
            self.log.info(
                "step18, Compare the data on nfs client with that of the source data")

            if tdfs_obj.data_copy_compare(
                    self.client_machine,
                    mountpoint_name,
                    subclient_content[0]):
                self.log.info("Items in Source and destination match")
            else:
                raise Exception("Source and Destination differ")
            self.log.info("Umount and cleanup the share")
            tdfs_obj.tdfs_machine_obj.unmount_path(mountpoint_name)
            tdfs_obj.delete_3dfs_share(share_name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as excp:
            error_message = "Failed with error: {}".format(str(excp))
            try:
                tdfs_obj.cleanup_3dfs()
                tdfs_obj.tdfs_machine_obj.unmount_path(mountpoint_name)
            except NameError:
                self.log.info("Share and mount point removed")
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED
