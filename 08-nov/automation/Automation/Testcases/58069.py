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

Json file template inputs for CVC testing
    "<testcase_id>": {
            "sdkPath":"<path of pythonsdk on client>",
            "whichPython":"full path of which python to use",
            "UserName": "<client machine user id>",
            "Password": "<client machine user password>",
            "AgentName": "File System",
            "ClientName": "<client machine name>",
            "StoragePolicyName": "<storage policy name>",
    }
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.ibmicvc import IBMiCVC
from FileSystem.FSUtils.fshelper import ScanType


class TestCase(CVTestCase):
    """Class for executing
        IBMi: Run cvc operations from IBMi command line
                Step1: cvc login to CS and generate a token file
                step2: create backupSet without CVC
                step3: create subclient from IBMi using CVC
                step4: On client, create a library with 10 objects
                step5: start full backup from IBMi using CVC
                step6: Update subclient from IBMi using CVC
                step7: start incremental  backup from IBMi using CVC
                step8: starting restore of full backup data using cvc
                step9: Starting restore of inc backup data using cvc
                step10: delete subclient from IBMi using CVC
                step11: Logout from CS from IBMi command line using CVC

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Verify CVC operations from IBMi command line"
        # Other attributes which will be initialized in FSHelper.populate_tc_inputs
        self.tcinputs = {
            "sdkPath": None,
            "whichPython": None,
            "UserName": None,
            "Password": None,
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.test_path = None
        self.slash_format = None
        self.helper = None

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
            self.destlib = "RST{0}".format(self.id)
            content = [self.client_machine.lib_to_path(srclib)]

            backupset_name = "backupset_{0}".format(self.id)

            self.log.info("*** STARTING RUN to CVC from IBMi command line **")
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

            inc_lib = "{0}1".format(srclib)
            self.client_machine.populate_lib_with_data(library_name=inc_lib, tc_id=self.id, count=5, prefix="I")
            self.client_machine.create_sourcepf(library=inc_lib, object_name='INCOBJ1')
            self.client_machine.create_sourcepf(library=inc_lib, object_name='INCOBJ2')
            filter1 = ["{0}/INCOBJ1.FILE".format(self.client_machine.lib_to_path(inc_lib))]

            self.log.info("step6: Update subclient from IBMi using CVC")
            self.cvc.update_sc(subclient_name=self.subclient_name,
                               content=[self.client_machine.lib_to_path(inc_lib)],
                               backupset_name=backupset_name,
                               exception_content=filter1,
                               overwrite=False,
                               **sec_args)

            self.log.info("step7: start incremental  backup from IBMi using CVC")
            job = self.cvc.start_backup(subclient_name=self.subclient_name,
                                        backupset_name=backupset_name,
                                        backup_type="incremental",
                                        wait=True,
                                        **sec_args)

            self.log.info("step8: starting restore of full backup data using cvc")
            job = self.cvc.start_restore(source_paths=[self.client_machine.lib_to_path(srclib)],
                                         backupset_name=backupset_name,
                                         destination_path=self.client_machine.lib_to_path(self.destlib),
                                         subclient_name=self.subclient_name,
                                         wait=True,
                                         **sec_args)

            self.log.info("Restore job#{0} to restore from full backup data "
                          "is {1}".format(job.get('id'), job.get('status')))
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)

            self.log.info("step9: Starting restore of inc backup data using cvc")
            job = self.cvc.start_restore(source_paths=[self.client_machine.lib_to_path(inc_lib)],
                                         backupset_name=backupset_name,
                                         destination_path=self.client_machine.lib_to_path(self.destlib),
                                         subclient_name=self.subclient_name,
                                         wait=True,
                                         **sec_args)
            self.log.info("Restore job#{0} to restore from incremental backup data "
                          "is {1}".format(job.get('id'), job.get('status')))
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)
            self.client_machine.manage_library(operation='delete', object_name=srclib)
            self.client_machine.manage_library(operation='delete', object_name=inc_lib)

            self.log.info("step10: delete subclient from IBMi using CVC")
            self.cvc.delete_sc(subclient_name=self.subclient_name,
                               backupset_name=backupset_name,
                               **sec_args)

            self.log.info("step11: Logout from CS from IBMi command line using CVC")
            self.cvc.logout(**sec_args)

            self.log.info("**CVC execution from IBMi has completed successfully**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
