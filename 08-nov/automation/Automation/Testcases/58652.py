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
    "<testcase_ID>": {
            "sdkPath":"<path of pythonsdk on client>",
            "whichPython":"full path of which python to use",
            "UserName": "<client machine user id>",
            "Password": "<client machine user password>",
            "AgentName": "File System",
            "ClientName": "<client machine name>",
            "StoragePolicyName": "<storage policy name>",
    }
"""
import json
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.ibmicvc import IBMiCVC
from FileSystem.FSUtils.fshelper import ScanType


class TestCase(CVTestCase):
    """Class for executing
        IBMi: Run cvc operations from IBMi command line
            Step1, cvc login to CS and generate a token file
            step2: create backupSet without CVC
            step3: On client, create a library CVC58652 with 10 objects
            step4: create subclient from IBMi using CVC
            step5: start full backup from IBMi using CVC and verify the backup data after deleting filtered content from disk.
            step6: Start restore and verify if only valid data with filters is backedup.
            step7: Update SC with new filters without overwriting the old filter content
            step8: start full backup from IBMi using CVC and verify the backup data after adding new filters.
            step9: Start restore and verify if only valid data with filters is backedup.
            step10: Update SC with new content and add new filters with overwrite option
            step11: start full backup from IBMi using CVC and verify the backup data after overwriting with new content and filters.
            step12: Restore and verify only new content with new filters is saved and filtered content is not backedup
            step13: cleanup the data on client machine
            step14: Logoff from CS though CVC
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Validate update subclient overwrite option from IBMi command line through CVC."
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
        self.cvc = None
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
            full_lib = "CVC{0}".format(self.id)
            self.destlib = "RST{0}".format(self.id)
            backupset_name = "backupset_{0}".format(self.id)

            self.log.info("*** STARTING validation of CVC from IBMi command line **")
            self.log.info("Step1, cvc login to CS and generate a token file")

            sec_args = {'tokenfile': "TC{0}".format(self.id),
                        'security_key': "IBMiAUTOMATIONTC"}
            self.cvc.login(**sec_args)

            self.log.info("step2: create backupSet without CVC")
            self.helper.create_backupset(name=backupset_name, delete=True)

            self.log.info("step3: On client, create a library {0} with 10 objects".format(full_lib))
            self.client_machine.populate_lib_with_data(library_name=full_lib, tc_id=self.id, count=5, prefix="A")
            omit = ['SRCPF1', 'SRCPF2']
            omit_path = []
            for each in omit:
                self.client_machine.create_sourcepf(library=full_lib, object_name=each)
                omit_path.append("{0}/{1}.FILE".format(self.client_machine.lib_to_path(full_lib),
                                                       each))

            self.log.info("step4: create subclient from IBMi using CVC")
            self.cvc.create_sc(subclient_name=self.subclient_name,
                               content=[self.client_machine.lib_to_path(full_lib)],
                               storage_policy=self.storage_policy,
                               backupset_name=backupset_name,
                               exception_content=[omit_path[0]],
                               **sec_args)

            self.log.info("step5: start full backup from IBMi using CVC and verify the backup data after "
                          "deleting filtered content from disk.")
            job = self.cvc.start_backup(subclient_name=self.subclient_name,
                                        backupset_name=backupset_name,
                                        backup_type="full",
                                        wait=True,
                                        **sec_args)
            self.client_machine.delete_file_object(library=full_lib, object_name=omit[0])
            self.log.info("step6: Start restore and verify if only valid data with filters is backedup.")
            self.cvc.start_restore(source_paths=[self.client_machine.lib_to_path(full_lib)],
                                         backupset_name=backupset_name,
                                         destination_path=self.client_machine.lib_to_path(self.destlib),
                                         subclient_name=self.subclient_name,
                                         wait=True,
                                         **sec_args)
            self.helper.compare_ibmi_data(source_path=self.client_machine.lib_to_path(full_lib),
                                          destination_path=self.client_machine.lib_to_path(self.destlib))
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)
            self.log.info("step7: Update SC with new filters without overwriting the old filter content ")
            self.client_machine.create_sourcepf(library=full_lib, object_name=omit[0])
            omit1 = ['NOTOVER', 'NOTOVER1']
            omit_path = []
            for each in omit1:
                self.client_machine.create_sourcepf(library=full_lib, object_name=each)
                omit_path.append("{0}/{1}.FILE".format(self.client_machine.lib_to_path(full_lib), each))
            self.cvc.update_sc(subclient_name=self.subclient_name,
                               backupset_name=backupset_name,
                               exception_content=[omit_path[0]],
                               overwrite=False,
                               **sec_args)

            self.log.info("step8: start full backup from IBMi using CVC and verify the backup data after "
                          "adding new filters.")
            job = self.cvc.start_backup(subclient_name=self.subclient_name,
                                        backupset_name=backupset_name,
                                        backup_type="full",
                                        wait=True,
                                        **sec_args)
            self.client_machine.delete_file_object(library=full_lib, object_name=omit[0])
            self.client_machine.delete_file_object(library=full_lib, object_name=omit1[0])
            self.log.info("step9: Start restore and verify if only valid data with filters is backedup.")
            self.cvc.start_restore(source_paths=[self.client_machine.lib_to_path(full_lib)],
                                   backupset_name=backupset_name,
                                   destination_path=self.client_machine.lib_to_path(self.destlib),
                                   subclient_name=self.subclient_name,
                                   wait=True,
                                   **sec_args)

            self.helper.compare_ibmi_data(source_path=self.client_machine.lib_to_path(full_lib),
                                          destination_path=self.client_machine.lib_to_path(self.destlib))
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)

            self.log.info("step10: Update SC with new content and add new filters with overwrite option")
            inc_lib = "CVC{0}1".format(self.id)
            self.client_machine.populate_lib_with_data(library_name=inc_lib, tc_id=self.id, count=5, prefix="I")
            omit = ['NEWCNT', 'NEWCNT1']
            omit_path = []
            for each in omit:
                self.client_machine.create_sourcepf(library=inc_lib, object_name=each)
                omit_path.append("{0}/{1}.FILE".format(self.client_machine.lib_to_path(inc_lib),each))

            self.cvc.update_sc(subclient_name=self.subclient_name,
                               content=[self.client_machine.lib_to_path(inc_lib)],
                               backupset_name=backupset_name,
                               exception_content=omit_path,
                               overwrite=True,
                               **sec_args)
            self.log.info("step11: start full backup from IBMi using CVC and verify the backup data after "
                          "overwriting with new content and filters.")
            job = self.cvc.start_backup(subclient_name=self.subclient_name,
                                        backupset_name=backupset_name,
                                        backup_type="full",
                                        wait=True,
                                        **sec_args)
            for each in omit:
                self.client_machine.delete_file_object(library=inc_lib, object_name=each)
            self.log.info("step12: Restore and verify only new content with new filters is saved and "
                          "filtered content is not backedup")
            self.cvc.start_restore(source_paths=[self.client_machine.lib_to_path(inc_lib)],
                                   backupset_name=backupset_name,
                                   destination_path=self.client_machine.lib_to_path(self.destlib),
                                   subclient_name=self.subclient_name,
                                   wait=True,
                                   **sec_args)
            self.helper.compare_ibmi_data(source_path=self.client_machine.lib_to_path(inc_lib),
                                          destination_path=self.client_machine.lib_to_path(self.destlib))
            self.log.info("step13: cleanup the data on client machine")
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)
            self.client_machine.manage_library(operation='delete', object_name=full_lib)
            self.client_machine.manage_library(operation='delete', object_name=inc_lib)
            self.log.info("step14: Logoff from CS though CVC")
            self.cvc.logout(**sec_args)

            self.log.info("step15: Verification of SC update with and without overwrite is completed.")
            self.log.info("**CVC SC Overwrite option verification from IBMi has completed successfully**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED