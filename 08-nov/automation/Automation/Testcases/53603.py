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
        IBMi LFS Data Protection - Full,Incremental with libraries added from
        subclient content. This test case does the following
        Step1,  Create backupset for this testcase if it doesn't exist.
        Step2,  Create subclient if it doesn't exist.
        Step3,  Create all the libraries on IBMi client,
                 including libraries that will be added later to subclient.
        Step4,  Run a full backup for the subclient
                    and verify it completes without failures.
        Step5,  Run a restore of the complete backup data
                    and verify correct data is restored.
        Step5,  Run a find operation for the full job
                    and verify the returned results.
        Step7,  Update subclient to use one more library
        Step8,  Add new data for incremental
        Step9,  Run an incremental job for the subclient
                    and verify it completes without failures.
        Step10, Run a restore of the newly added libraries
                    and verify correct data is restored.
        Step11, Run a find operation and verify the returned results.
        Step12, Update subclient to use wildcard as content
        Step13, Add new data for incremental
        Step14, Run an incremental job for the subclient
                    and verify it completes without failures.
        Step15, Run a restore of the newly added libraries
                  and verify correct data is restored.
        Step16, Run a find operation and verify the returned results.
        Step17, Run complete restore of data under /QSYS.LIB
                    and verify results
    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("Adding libraries into subclient content before "
                     " incremental backups with regular scan.")
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
        self.subclient_name = None
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
        self.subclient_name = "subclient_{0}_{1}_LFS".format(self.id, scan_type.name.lower())
        self.subclient_content = self.helper.get_subclient_content(
            self.test_path,
            self.slash_format,
            self.subclient_name
        )
        self.tmp_path = "{0}{1}REST{2}.LIB".format(self.test_path,
                                                   self.slash_format,
                                                   self.id,
                                                   )
        # Create the subclient
        self.helper.create_subclient(
            name=self.subclient_name,
            storage_policy=self.storage_policy,
            content=self.subclient_content,
            scan_type=scan_type,
            delete=True
        )

        self.client_machine._num_libraries = self.client_machine._num_libraries + 2

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)

            scan_type = ScanType.RECURSIVE

            self.log.info("Step1, Create backupset for this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(backupset_name, delete=True)

            self.log.info("**STARTING RUN FOR %s SCAN**", scan_type.name)
            self.log.info("Step2, Create subclient for the scan type "
                          "%s if it doesn't exist.", scan_type.name)
            self.configure_test_case(scan_type)

            self.log.info("Subclient content has %s libraries. Client has %s libraries",
                          len(self.subclient_content),
                          self.client_machine.num_libraries
                          )
            libraries_on_disk = self.helper.get_subclient_content(self.test_path,
                                                                  self.slash_format,
                                                                  self.subclient_name)

            self.log.info("Step3, Create all the libraries on IBMi client, "
                          "including libraries that will be added later to subclient")

            # Add data for all libraries, but SC has only a few libraries
            # subclient_content_old has 2 fewer libraries than on disk.
            # One gets added to SC before next incremental, while another one should
            # be backed up when wildcard is introduced.
            for content in libraries_on_disk:
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

            # Introduce another library in the SC.
            subclient_content_old = self.subclient_content
            self.subclient_content = libraries_on_disk[:-1]
            new_library_list = [library for library in self.subclient_content if
                                library not in subclient_content_old]

            self.log.info("Step7, Update subclient to use %s libraries as well",
                          new_library_list)
            self.helper.update_subclient(content=self.subclient_content)

            self.log.info("Step8, Add new data for incremental")
            for content in subclient_content_old:
                self.log.info("Adding incremental data under path: %s", content)
                self.helper.add_new_data_incr(content, self.slash_format, scan_type)

            self.log.info("Step9, Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            _ = self.helper.run_backup_verify(scan_type, "Incremental")[0]

            self.log.info("Step10, Run a restore of the newly added libraries "
                          "and verify correct data is restored.")
            for content in new_library_list:
                self.helper.run_restore_verify(self.slash_format, content, self.tmp_path, "")

            self.log.info("Step11, Run a find operation and verify the returned results.")
            for content in self.subclient_content:
                self.helper.run_find_verify(content)

            subclient_content_old = self.subclient_content
            self.subclient_content = libraries_on_disk
            wildcard_subclient_content = [self.helper.get_wildcard_content(self.subclient_content[0])]

            self.log.info("Step12, Update subclient to use %s wildcard as content.",
                          wildcard_subclient_content)
            self.helper.update_subclient(content=wildcard_subclient_content)

            new_library_list = [library for library in self.subclient_content if
                                library not in subclient_content_old]

            self.log.info("There are %s libraries on disk, new libraries %s",
                          len(libraries_on_disk),
                          new_library_list)

            self.log.info("Step13, Add new data for incremental")
            for content in subclient_content_old:
                self.log.info("Adding incremental data under path: %s", content)
                self.helper.add_new_data_incr(content, self.slash_format, scan_type)

            self.log.info("Step14, Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            _ = self.helper.run_backup_verify(scan_type, "Incremental")[0]

            self.log.info("Step15, Run a restore of the newly added libraries "
                          "and verify correct data is restored.")
            for content in new_library_list:
                self.helper.run_restore_verify(self.slash_format, content, self.tmp_path, "")

            self.log.info("Step16, Run a find operation and verify the returned results.")
            for content in self.subclient_content:
                self.helper.run_find_verify(content)

            self.log.info("Step17, Run complete restore of data under /QSYS.LIB "
                          "and verify results")
            self.helper.run_complete_restore_verify(self.subclient_content)

            for content in self.subclient_content:
                self.client_machine.remove_directory(content)

            self.log.info("**%s SCAN RUN COMPLETED SUCCESSFULLY**", scan_type.name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
