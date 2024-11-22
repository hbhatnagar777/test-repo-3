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

    strip_parent_path()     --  Function that strips 2 level of parent paths.

    run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi LFS Data Protection - Restore of single and multiple objects with Optimized scan
        Step1,  Create backupset for this testcase if it doesn't exist
        Step2,  Create subclient for the scan type
                    Enable synclib option.
        Step3,  Add full data for the current run.
        Step4,  Run a full backup for the subclient and verify it completes without failures.
        Step5,  Add incremental data for the current run.
        Step6,  Run a incremental backup verify it completes without failures.
        Step7,  Restore multiple objects and verify
        Step8,  Restore single object and verify
    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Synclib: Restore of single and multiple objects for regular scan"
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

    def configure_test_case(self, scan_type, synclib=True):
        """
        Function that handles subclient creation, and any special configurations

        Args:
            scan_type (ScanType(Enum)) : Scan type of this test run.

            synclib   (bool)           : True if the subclient has to be created with synclib
                default: True

        Returns:
            None
        """
        self.client_machine.num_libraries = 2

        # Create the subclient content paths
        subclient_name = "subclient_{0}_{1}_LFS".format(self.id, scan_type.name.lower())
        self.subclient_content = self.helper.get_subclient_content(
            self.test_path,
            self.slash_format,
            subclient_name
        )

        # Create the subclient
        self.helper.create_subclient(
            name=subclient_name,
            storage_policy=self.storage_policy,
            content=self.subclient_content,
            scan_type=scan_type,
            delete=True
        )

        if synclib:
            self.helper.enable_synclib()

    @staticmethod
    def strip_parent_path(list_of_path):
        """
        Function that strips top 2 level of parents for a path so that out of place comparisons
        can be done.

        Args:
            list_of_path        (list)  : List of objects/members in path

        Returns:
            list:   List of updated paths
        """
        return ['/'.join(path.split('/')[3:]) for path in list_of_path]

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
            self.configure_test_case(scan_type, synclib=True)

            self.client_machine.reset_file_counts()
            self.client_machine.num_data_areas = 2

            self.log.info("Step3, Add full data for the current run.")
            for content in self.subclient_content:
                self.log.info("Adding data under path: %s", content)
                self.client_machine.generate_test_data(content)
                self.client_machine.create_one_object(content, "TOT1{0}".format(self.id))
                self.client_machine.create_one_object(content, "TOT2{0}".format(self.id))

            self.log.info("Step4, Run a full backup for the subclient "
                          "and verify it completes without failures.")
            _ = self.helper.run_backup_verify(scan_type, "Full")[0]

            self.log.info("Step5, Add incremental data for the current run.")
            for content in self.subclient_content:
                self.log.info("Adding data under path: %s", content)
                self.helper.add_new_data_incr(content, self.slash_format, scan_type)
                self.client_machine.create_one_object(content, "INC1{0}".format(self.id))
                self.client_machine.create_one_object(content, "INC2{0}".format(self.id))

            self.log.info("Step6, Run a incremental backup "
                          "and verify it completes without failures.")
            _ = self.helper.run_backup_verify(scan_type, "Incremental")[0]

            content = self.subclient_content[0]
            machine_items = self.client_machine.get_items_list(content,
                                                               include_parents=False,
                                                               sorted_output=True)
            restore_path = "/QSYS.LIB/REST{0}.LIB".format(self.id)
            multiple_restore_items = [item for item in machine_items if "TOT" not in item]

            self.log.info("Step7, Restore multiple objects and verify. From: %s To: %s",
                          content,
                          restore_path)
            self.log.info("Restore object list %s", str(multiple_restore_items))
            self.client_machine.remove_directory(restore_path)
            self.helper.restore_out_of_place(destination_path=restore_path,
                                             paths=multiple_restore_items,
                                             from_time=None,
                                             to_time=None)
            restore_destination_items = self.client_machine.get_items_list(restore_path,
                                                                           include_parents=False,
                                                                           sorted_output=True)

            self.log.info("Comparing source and destination entries")
            if self.helper.compare_lists(self.strip_parent_path(multiple_restore_items),
                                         self.strip_parent_path(restore_destination_items)):
                self.log.info("Restore of multiple objects successful")
                self.client_machine.remove_directory(restore_path)
            else:
                raise Exception("Items in source and destination don't match")

            single_restore_item = [item for item in multiple_restore_items if "INC" not in item]
            single_restore_item = single_restore_item[:1]

            self.log.info("Step8, Restore single object and verify. From: %s To: %s", content,
                          restore_path)
            self.log.info("Restore object list %s", str(single_restore_item))
            self.helper.restore_out_of_place(destination_path=restore_path,
                                             paths=single_restore_item,
                                             from_time=None,
                                             to_time=None)
            restore_destination_items = self.client_machine.get_items_list(restore_path,
                                                                           include_parents=False,
                                                                           sorted_output=True)
            self.log.info("Comparing source and destination entries")
            if self.helper.compare_lists(self.strip_parent_path(single_restore_item),
                                         self.strip_parent_path(restore_destination_items)):
                self.log.info("Restore of single object successful")
                self.client_machine.remove_directory(restore_path)
            else:
                raise Exception("Items in source and destination don't match")

            for content in self.subclient_content:
                self.client_machine.remove_directory(content)

            self.log.info("**%s SCAN RUN COMPLETED SUCCESSFULLY**", scan_type.name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
