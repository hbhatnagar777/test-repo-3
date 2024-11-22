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

    run()                   --  run function of this test case
"""

from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper
from datetime import datetime


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Validate default values for advanced SC options of subclient created through CVC.
        Step1: cvc login to CS and generate a token file
        step2: create backupSet without CVC
        step3: create subclient from IBMi using CVC
        step4: On client, create a library with 10 objects
        step5: start full backup from IBMi using CVC
        Step6: step6: Check full backup logs to verify default options are set properly or not.
        step7: Update subclient from IBMi using CVC
        step8: start incremental  backup from IBMi using CVC
        step9: Check inc backup logs to verify default options are set properly or not.
        step10: start differential  backup from IBMi using CVC
        step11: Check diff backup logs to verify default options are set properly or not.
        step12: delete subclient from IBMi using CVC
        step13: Logout from CS from IBMi command line using CVC
        Step14: Cleanup the libraries from client disk.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Validate default values for advanced SC options of subclient created through CVC."
        # Other attributes which will be initialized in FSHelper.populate_tc_inputs
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.subclient_name = "CVC{0}".format(self.id)
            srclib = "CVC{0}".format(self.id)
            content = [self.client_machine.lib_to_path(srclib)]

            backupset_name = "backupset_{0}".format(self.id)

            self.log.info("*** STARTING RUN TO VALIDATE SC DEFAULT VALUES FOR ADDITIONAL OPTIONS ***")
            self.log.info("Step1, cvc login to CS and generate a token file")

            sec_args = {'tokenfile': "TC{0}".format(self.id),
                        'security_key': "IBMiAUTOMATIONTC"}

            self.log.info("security arguments are {0}".format(sec_args))

            self.cvc.login(**sec_args)

            self.log.info("step2: create backupSet without CVC")
            self.helper.create_backupset(name=backupset_name, delete=True)

            self.log.info("step3: create subclient from IBMi using CVC")
            self.cvc.create_sc(subclient_name=self.subclient_name,
                               content=content,
                               storage_policy=self.storage_policy,
                               backupset_name=backupset_name,
                               exception_content=None,
                               **sec_args)

            self.log.info("step4: On client, create a library {0} with 10 objects".format(srclib))
            self.client_machine.populate_lib_with_data(library_name=srclib, tc_id=self.id, count=5, prefix="A")

            self.log.info("step5: start full backup from IBMi using CVC")
            job = self.cvc.start_backup(subclient_name=self.subclient_name,
                                        backupset_name=backupset_name,
                                        backup_type="full",
                                        wait=True,
                                        **sec_args)

            self.log.info("step6: Check full backup logs to verify default options are set properly or not.")
            self.helper.verify_sc_defaults(job=job.get('id'))

            self.log.info("step7: Update subclient from IBMi using CVC")
            inc_lib = "{0}1".format(srclib)
            self.client_machine.populate_lib_with_data(library_name=inc_lib, tc_id=self.id, count=5, prefix="I")
            self.client_machine.create_sourcepf(library=inc_lib, object_name='INCOBJ1')
            self.client_machine.create_sourcepf(library=inc_lib, object_name='INCOBJ2')
            filter1 = ["{0}/INCOBJ1.FILE".format(self.client_machine.lib_to_path(inc_lib))]

            self.cvc.update_sc(subclient_name=self.subclient_name,
                               content=[self.client_machine.lib_to_path(inc_lib)],
                               backupset_name=backupset_name,
                               exception_content=filter1,
                               overwrite=False,
                               **sec_args)

            self.log.info("step8: start incremental  backup from IBMi using CVC")
            job = self.cvc.start_backup(subclient_name=self.subclient_name,
                                        backupset_name=backupset_name,
                                        backup_type="incremental",
                                        wait=True,
                                        **sec_args)
            self.log.info("step9: Check inc backup logs to verify default options are set properly or not.")
            self.helper.verify_sc_defaults(job=job.get('id'))

            self.log.info("step10: start differential backup from IBMi using CVC")
            job = self.cvc.start_backup(subclient_name=self.subclient_name,
                                        backupset_name=backupset_name,
                                        backup_type="differential",
                                        wait=True,
                                        **sec_args)
            self.log.info("step11: Check inc backup logs to verify default options are set properly or not.")
            self.helper.verify_sc_defaults(job=job.get('id'))

            self.log.info("step12: delete subclient from IBMi using CVC")
            self.cvc.delete_sc(subclient_name=self.subclient_name,
                               backupset_name=backupset_name,
                               **sec_args)

            self.log.info("step13: Logout from CS from IBMi command line using CVC")
            self.cvc.logout(**sec_args)

            self.log.info("Step14: Cleanup libraries from client disk")
            self.client_machine.manage_library(operation='delete', object_name=srclib)
            self.client_machine.manage_library(operation='delete', object_name=inc_lib)

            self.log.info("**%s SCAN RUN VALIDATION OF SC OPTIONS COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED