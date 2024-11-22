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

    configure_test_case()   --  Handles subclient creation, and any special configurations.

    run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper


class TestCase(CVTestCase):
    """
    Class for executing
        IBMi LFS Data Protection - Full,Incremental, SyntheticFull with regular scan.
        This test case does the following
        Step1,  Create backupset for this testcase if it doesn't exist.
        Step2,  Create subclient for the REGULAR SCAN if it doesn't exist.
        Step3,  Add full data for the current run.
        Step4,  Run a full backup for the subclient
                    and verify it completes without failures.
        Step5,  Run a restore of the complete backup data
                    and verify correct data is restored.
        Step6,  Run a find operation for the full job
                    and verify the returned results.
        Step7,  Add new data for the incremental
        Step8,  Run an incremental backup for the subclient
                    and verify it completes without failures.
        Step9,  Run a restore of the complete backup data
                    and verify correct data is restored.
        Step10, Run a find operation for the complete data
                    and verify the returned results.
        Step11, Add one object
        Step12, Run an incremental backup for the subclient
                    and verify it completes without failures.
        Step13, Run a restore of the single object
                    and verify correct data is restored.
        Step14, Run a find operation for the single object
                    and verify the returned results.
        Step15, Add new data for the incremental
        Step16, Run a synthfull job
        Step17, Run an incremental backup after
                    synthfull for the subclient and
                    verify it completes without failures.
        Step18, Run a restore of the complete backup data
                    and verify correct data is restored.
        Step19, Run a find operation for the complete job
                    and verify the returned results.
        Step20, Run complete restore of data under /QSYS.LIB and verify results
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "LFS backup cycle with Full, Incrementals and Synthfull"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "TestPath": None,
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

    def configure_test_case(self, scan_type):
        """
        Function that handles subclient creation, and any special configurations

        Args:
            scan_type (ScanType(Enum)) : Scan type of this test run.

        Returns:
            None
        """
        # Create the subclient content paths
        subclient_name = "subclient_{0}_{1}_LFS".format(self.id, scan_type.name.lower())
        self.subclient_content = self.helper.get_subclient_content(
            self.test_path,
            self.slash_format,
            subclient_name
        )
        self.tmp_path = "{0}{1}REST{2}.LIB".format(self.test_path,
                                                   self.slash_format,
                                                   self.id,
                                                   )
        # Create the subclient
        self.helper.create_subclient(
            name=subclient_name,
            storage_policy=self.storage_policy,
            content=self.subclient_content,
            scan_type=scan_type
        )

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)

            self.log.info("Step1, Create backupset for this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(backupset_name, delete=True)

            scan_type = ScanType.RECURSIVE

            self.log.info("**STARTING RUN FOR %s SCAN**", scan_type.name)
            self.log.info("Step2, Create subclient for the scan type "
                          "%s if it doesn't exist.", scan_type.name)
            self.configure_test_case(scan_type)

            self.log.info("Step3, Add full data for the current run.")
            for content in self.subclient_content:
                self.log.info("Adding data under path: %s", content)
                self.client_machine.generate_test_data(content)

            self.log.info("Step4, Run a full backup for the subclient "
                          "and verify it completes without failures.")
            _ = self.helper.run_backup_verify(scan_type, "Full")[0]

            self.log.info("Step5, Run a restore of the full backup data"
                          " and verify correct data is restored.")
            for content in self.subclient_content:
                self.helper.run_restore_verify(self.slash_format, content, self.tmp_path, "")

            self.log.info("Step6, Run a find operation for the full job"
                          " and verify the returned results.")
            for content in self.subclient_content:
                self.helper.run_find_verify(content)

            self.log.info("Step7, Add new data for the incremental")
            for content in self.subclient_content:
                self.log.info("Adding data under path: %s", content)
                incr_diff_data_path = content
                self.helper.add_new_data_incr(incr_diff_data_path, self.slash_format, scan_type)

            self.log.info("Step8, Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            _ = self.helper.run_backup_verify(scan_type, "Incremental")[0]

            self.log.info("Step9, Run a restore of the complete backup data "
                          "and verify correct data is restored.")
            for content in self.subclient_content:
                self.helper.run_restore_verify(self.slash_format, content, self.tmp_path, "")

            self.log.info("Step10, Run a find operation  and verify the returned results.")
            for content in self.subclient_content:
                self.helper.run_find_verify(content)

            self.log.info("Step11, Add one object")
            for content in self.subclient_content:
                self.client_machine.create_one_object(content, "SINGLE")

            self.log.info("Step12, Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            job_incr1 = self.helper.run_backup_verify(scan_type, "Incremental")[0]

            self.log.info("Step13, Run a restore of the object "
                          "and verify correct data is restored.")
            for content in self.subclient_content:
                self.helper.run_restore_verify(
                    self.slash_format,
                    content,
                    self.tmp_path,
                    "SINGLE.DTAARA",
                    job=job_incr1
                )

            self.log.info("Step14, Run a find operation and verify the returned results.")
            for content in self.subclient_content:
                self.helper.run_find_verify('{0}/SINGLE.DTAARA'.format(content))

            self.log.info("Step15, Add new data for the incremental")
            for content in self.subclient_content:
                self.helper.add_new_data_incr(content, self.slash_format, scan_type)

            self.log.info("Step16, Run a synthfull job")
            self.helper.run_backup_verify(scan_type, "Synthetic_full")

            self.log.info("Step17, Run an incremental backup after synthfull for the subclient"
                          " and verify it completes without failures.")
            _ = self.helper.run_backup_verify(scan_type, "Incremental")[0]

            self.log.info("Step18, Run a restore of the backup data"
                          " and verify correct data is restored.")
            for content in self.subclient_content:
                self.helper.run_restore_verify(self.slash_format, content, self.tmp_path, "")

            self.log.info("Step19, Run a find operation and verify the returned results.")
            for content in self.subclient_content:
                self.helper.run_find_verify(content)

            self.log.info("Step20, Run complete restore of data under /QSYS.LIB "
                          "and verify results")
            self.helper.run_complete_restore_verify(self.subclient_content)

            for content in self.subclient_content:
                self.client_machine.remove_directory(content)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
