# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
	__init__()             --  Initialize TestCase class

	  run()                  --  run function of this test case


"""
import re
from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper
from FileSystem.FSUtils import cvchelper

class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Full,Incremental, for backup and CVC browse,
        find for nested mount points
        This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
        Step2, For each of the allowed scan type
                do the following on the backupset
            Step2.1,  Create subclient for the scan type if it doesn't exist.
                Step2.2, Add full data for the current run.
                Step2.3, Run a full backup for the subclient
                            and verify it completes without failures.
                Step2.4, As user run browse and
                 Validate the files and directories based on permission are shown correctly
                Step2.5, Run incremental job
                Step2.6, Run Synthetic Full job
                Step 2.7, Run browse and validate the files/directories

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "CVC browse for nested mount points "
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "UserName": None
        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.verify_dc = None
        self.skip_classic = None
        self.client_machine = None
        self.acls = None
        self.should_wait = None

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize test case inputs
            cvc_obj = cvchelper.Cvchelper(
                self.tcinputs.get('ClientName'), self.commcell, self.client)
            FSHelper.populate_tc_inputs(self)
            test_path = self.test_path
            client_name = self.client.client_name
            cvc_user_name = self.tcinputs.get('UserName')
            slash_format = self.slash_format
            helper = self.helper

            machine = self.client_machine
            cvc_obj.username = cvc_user_name
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy
            dir_level = 2

            self.log.info("Setting global param "
                          "EnforceUnixUserPermissionsOnRestore")
            self.commcell.add_additional_setting("CommServDB.GxGlobalParam",
                                                "EnforceUnixUserPermissionsOnRestore",
                                                 "INTEGER", "1")
            self.log.info("Step1, Create backupset for "
                          "this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            helper.create_backupset(backupset_name)

            self.log.info("Step2, Executing steps for all the allowed scan type")
            scan_type = ScanType.RECURSIVE
            self.log.info("**STARTING RUN FOR {0} SCAN**".format(str(scan_type.name)))

            self.log.info("Step2.1, Create subclient for the scan type {0} "
                          "if it doesnt exists".format(str(scan_type.name)))

            subclient_name = ("subclient_{0}_"
                              "{1}".format(str(self.id), str(scan_type.name)))
            subclient_content = []
            subclient_content.append(test_path
                                     + slash_format
                                     + subclient_name)
            tmp_path = ("{0}{1}cvauto_tmp{2}{3}{4}".format(test_path,slash_format,
                                                           slash_format,subclient_name,
                                                           slash_format))

            run_path = (subclient_content[0]
                        + slash_format
                        + str(self.runid))

            full_data_path = "{0}{1}full".format(run_path, slash_format)

            helper.create_subclient(name=subclient_name,
                                    storage_policy=storage_policy,
                                    content=subclient_content,
                                    scan_type=scan_type,
                                    catalog_acl=True)
            self.log.info("Step 2.2 Adding data under path: "
                          "{0}".format(full_data_path))
            # Data creation script expects the parent path to be present
            if machine.check_directory_exists(full_data_path):
                self.log.info("Data path exists. Using the same")
            else:
                self.log.info("Data Path doesnt exist. "
                              "Creating the parent Full "
                              "path.{0}".format(full_data_path))
                machine.create_directory(full_data_path)

            cvc_obj.data_creation(full_data_path, 0, 1, 1, dir_level)

            self.log.info("Step2.3,  Run a full backup for the subclient "
                          "and verify it completes without failures.")
            helper.run_backup_verify(scan_type, "Full")[0]
            sleep(self.WAIT_TIME)

            self.log.info("Logging into cvc as {0}".format(cvc_user_name))
            login_status = cvc_obj.login()
            self.log.info(login_status)

            self.log.info("Validate browse operation ")
            
            cvc_obj.browse(client_name, backupset_name,
                           subclient_name, full_data_path, 0, dir_level, 1, 1)
            self.log.info("Add incremental data")
            incr_data_path = ("{0}{1}incr_data".format(run_path,slash_format))
           
            machine.create_directory(incr_data_path)
            cvc_obj.data_creation(incr_data_path, 0,1, 1, 1)
            self.log.info("Step 2.5 Run incremental backup for the subclient")
            helper.run_backup_verify(scan_type, "Incremental")[0]
            self.log.info("Step 2.6 Run synthfull backup")
            helper.run_backup_verify(scan_type, "Synthetic_full")
            self.log.info("Step 2.7Validate browse operation for incremental data")
            cvc_obj.browse(client_name, backupset_name,
                           subclient_name, full_data_path, 0, dir_level, 1, 1)
            self.log.info("Cleaning up the data path")
            machine.remove_directory(test_path)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: {0}'.format(str(excp)))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        self.log.info("Removing additional setting "
                      "EnforceUnixUserPermissionsOnRestore")
        self.commcell.delete_additional_setting("CommServDB.GxGlobalParam",
                                                "EnforceUnixUserPermissionsOnRestore")
