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

from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi LFS Data Protection - Full,Incremental with addition and removal of filters
        Step1,  Create backupset for this testcase if it doesn't exist
        Step2,  Create subclient for the scan type.
                    Enable object level backups.
        Step3,  Create all the libraries on IBMi client and add files that will be filtered.
        Step4,  Creating filter list and updating subclient.
        Step5,  Run a full backup for the subclient and verify it completes without failures.
        Step6,  Check backup logs to confirm SAVLIB was used.
        Step7,  Run a restore of the full backup data
                    and verify correct data is restored.
        Step8,  Run a find operation for the full job and verify the results.
        Step9,  Remove some filters
        Step10, Run an incremental job for the subclient and verify it completes without failures.
        Step11, Check backup logs to confirm SAVOBJ was used.
        Step12, Run a restore and verify correct data is restored.
        Step13, Run a find operation and verify the returned results.
        Step14, Add all the filters back.
        Step15, Add new data for incremental
        Step16, Run an incremental job for the subclient and verify it completes without failures.
        ​​​​​​​Step17, Run a restore and verify correct data is restored.
        Step18, Run a find operation and verify the returned results.
    """
    def __init__(self):
        """
        Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "LFS Object level backup with addition and removal of filters"
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
            scan_type (ScanType(Enum))  :   Scan type of this test run.

        Returns:
            None
        """
        # Create the subclient content paths
        self.subclient_name = "subclient_{0}_{1}_LFS".format(self.id, scan_type.name.lower())
        self.subclient_content = self.helper.get_subclient_content(self.test_path,
                                                                   self.slash_format,
                                                                   self.subclient_name)
        self.tmp_path = "{0}{1}REST{2}.LIB".format(self.test_path,
                                                   self.slash_format,
                                                   self.id)
        # Create the subclient
        self.helper.create_subclient(name=self.subclient_name,
                                     storage_policy=self.storage_policy,
                                     content=self.subclient_content,
                                     scan_type=scan_type,
                                     delete=True)

        self.log.info("Enable object level backup IBMi.")
        self.helper.set_object_level_backup(True)
        self.client_machine.num_empty_files = 0

    def run(self):
        """
        Main function for test case execution
        """
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

            self.log.info("Step3, Create all the libraries on IBMi client,"
                          " And add files that will be filtered.")
            for content in self.subclient_content:
                self.log.info("Adding data under path: %s", content)
                self.client_machine.generate_test_data(content)
                deque(map(lambda obj, cont=content:
                          self.client_machine.create_one_object(cont, obj),
                          ["FILTER", "WILDCARD", "TYPEKNOWN"]))

            self.log.info("Step4, Creating filter list and updating subclient")
            filter_list = [self.client_machine.join_path(content, item)
                           for item in ["FILTER.DTAARA", "WILD*", "TYPEKNOW*.DTAARA"]
                           for content in self.subclient_content]

            self.log.info("Adding %s filters: %s", len(filter_list), filter_list)
            self.helper.update_filter_and_exception(filter_content=filter_list)

            self.log.info("Step5, Run a full backup for the subclient "
                          "and verify it completes without failures.")
            job1 = self.helper.run_backup_verify(scan_type, "Full")[0]

            self.log.info("Step6, Check backup logs to confirm SAVOBJ was used.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=job1.job_id,
                                        expectedvalue='SAVOBJ')

            self.log.info("Step7, Run a restore of the full backup data"
                          " and verify correct data is restored.")
            for content in self.subclient_content:
                self.helper.run_restore_verify(self.slash_format, content, self.tmp_path, "")

            self.log.info("Step8, Run a find operation for the full job and verify the results.")
            for content in self.subclient_content:
                self.helper.run_find_verify(content)

            self.log.info("Step9, Remove some filters: %s", str(filter_list[1:]))
            new_filter_list = filter_list[:1]
            self.helper.update_filter_and_exception(filter_content=new_filter_list)

            self.log.info("Step10, Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            job2 = self.helper.run_backup_verify(scan_type, "Incremental")[0]

            self.log.info("Step11, Check backup logs to confirm SAVOBJ was used.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=job2.job_id,
                                        expectedvalue='SAVOBJ')

            self.log.info("Step12, Run a restore and verify correct data is restored.")
            for content in self.subclient_content:
                self.helper.run_restore_verify(self.slash_format, content, self.tmp_path, "")

            self.log.info("Step13, Run a find operation and verify the returned results.")
            for content in self.subclient_content:
                self.helper.run_find_verify(content)

            self.log.info("Step14, Add all the filters back.")
            self.helper.update_filter_and_exception(filter_content=filter_list)

            self.log.info("Step15, Add new data for incremental")
            for content in self.subclient_content:
                self.log.info("Adding incremental data under path: %s", content)
                self.helper.add_new_data_incr(content, self.slash_format, scan_type)

            self.log.info("Step16, Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            _ = self.helper.run_backup_verify(scan_type, "Incremental")[0]

            self.log.info("Step17, Run a restore and verify correct data is restored.")
            for content in self.subclient_content:
                self.helper.run_restore_verify(self.slash_format, content, self.tmp_path, "")

            self.log.info("Step18, Run a find operation and verify the returned results.")
            for content in self.subclient_content:
                self.helper.run_find_verify(content)

            for content in self.subclient_content:
                self.client_machine.remove_directory(content)

            self.log.info("**%s SCAN RUN COMPLETED SUCCESSFULLY**", scan_type.name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
