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
    """Class for executing
            IBMi LFS Data Protection - Full,Incremental, SyntheticFull
            This test case does the following
            Step1,  Create backupset for this testcase if it doesn't exist.
            Step2,  Create subclient for the RECURSIVE and OPTIMIZED SCAN if it doesn't exist.
            Step3,  Add full data for the current run.
            Step4,  Run a full backup for the subclient
                        and verify it completes without failures.
                        Verify size of application.
            Step5,  Run a find operation for the full job
                        and verify the returned results.
            Step6,  Add new data for the incremental
            Step7,  Run an incremental backup for the subclient
                        and verify it completes without failures.
                        Verify size of application.
            Step8, Run a find operation for the complete data
                        and verify the returned results.
            """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify size of application for various IBMi backups"
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = ""
        self.slash_format = ""
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.subclient_content = None
        self.tmp_path = ""
        self.IBMiMode = None

    def configure_test_case(self, scan_type):
        """
        Function that handles subclient creation, and any special configurations

        Args:
            scan_type (ScanType(Enum)) : Scan type of this test run.

        Returns:
            None
        """
        self.client_machine.reset_file_counts()
        # We will add just 2 libraries
        if self.client_machine.num_libraries != 2:
            self.log.info("Changing the number of libraries to 2")
            self.client_machine.num_libraries = 2

        self.client_machine.num_savf_files = 2
        self.client_machine.savf_file_size = 5*1024 # 5MB files

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

        self.helper.set_savf_file_backup(True)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)

            scans = [ScanType.RECURSIVE]
            runs = 1
            if self.IBMiMode == "NON-VTL":
                scans.append(ScanType.OPTIMIZED)
                runs = 2

            for scan_type in scans:
                for run_number in range(runs):
                    self.log.info("Step1, Create backupset for this testcase if it doesn't exist")
                    backupset_name = "backupset_{0}_{1}".format(self.id,self.IBMiMode)
                    self.helper.create_backupset(backupset_name, delete=True)
                    self.log.info("**STARTING RUN FOR %s SCAN**", scan_type.name)
                    self.log.info("Step2, Create subclient for the scan type "
                                  "%s if it doesn't exist.", scan_type.name)
                    self.configure_test_case(scan_type)
                    if self.IBMiMode == "VTLParallel":
                        self.log.info("Enable multiple drives option for VTL Backup")
                        self.helper.set_vtl_multiple_drives()

                    if run_number == 1:
                        if scan_type == ScanType.OPTIMIZED:
                            self.log.info("Enabling synclib")
                            self.helper.enable_synclib()
                        elif self.IBMiMode == "NON-VTL":
                            self.log.info("Enable object level backup")
                            self.helper.set_object_level_backup()

                    self.log.info("Step3, Add full data for the current run.")
                    for content in self.subclient_content:
                        self.log.info("Adding data under path: %s", content)
                        self.client_machine.generate_test_data(content)

                    self.log.info("Step4, Run a full backup for the subclient "
                                  "and verify it completes without failures.")
                    job_full = self.helper.run_backup_verify(scan_type, "Full")[0]

                    self.log.info("Step5, Run a find operation for the full job"
                                  " and verify the returned results.")
                    expected_data_full = self.client_machine.num_libraries * \
                                         (self.client_machine.num_savf_files-1) * \
                                         self.client_machine.savf_file_size * 1024
                    self.log.info("Size of application %d, expected data backed up %d",
                                  job_full.size_of_application,
                                  expected_data_full)
                    assert job_full.size_of_application >= expected_data_full, "Size of application is less than " \
                                                                               "expected "

                    for content in self.subclient_content:
                        self.helper.run_find_verify(content)

                    self.log.info("Step6, Add new data for the incremental")
                    for content in self.subclient_content:
                        self.log.info("Adding data under path: %s", content)
                        incr_diff_data_path = content
                        add_extra_data = (self.subclient_content.index(content) == 0)
                        self.helper.add_new_data_incr(incr_diff_data_path,
                                                      self.slash_format,
                                                      scan_type,
                                                      increment_count=add_extra_data)

                    self.log.info("Step7, Run an incremental job for the subclient"
                                  " and verify it completes without failures.")
                    job_incr = self.helper.run_backup_verify(scan_type, "Incremental")[0]

                    expected_data_incr = self.client_machine.num_libraries * \
                                         (self.client_machine.num_savf_files-1) * \
                                         self.client_machine.savf_file_size * 1024 - expected_data_full
                    self.log.info("Size of application %d, expected data backed up %d",
                                  job_incr.size_of_application,
                                  expected_data_incr)
                    assert job_incr.size_of_application >= expected_data_incr, "Size of application is less than " \
                                                                               "expected "

                    self.log.info("Step8, Run a find operation and verify the returned results.")
                    for content in self.subclient_content:
                        self.helper.run_find_verify(content)

                    for content in self.subclient_content:
                        self.client_machine.remove_directory(content)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            import traceback
            self.log.info("%s", traceback.format_exc())
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
