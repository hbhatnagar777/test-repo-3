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
            step1: cvc login to CS and generate a token file with security key
            step2: use the token file to create a SC without providing the security key.
            step3: Validate that creating SC has failed as security key is not provided.
            step4: Now create a SC with security key and validate that SC is created.
            step5: Now delete the SC with security key and validate that SC is deleted.
            step6: Try to perform cvc logout without security key and verify its failure.
            step7: Try to perform cvc logout with security key and verify its success.
            Step8: cvc login to CS and generate a token file without security key
            step9: use the token file to create a SC by providing the security key.
            step10: Validate that creating SC has failed as security key is provided.
            step11: Now create a SC without security key and validate that SC is created.
            step12: Now delete the SC with security key and validate that SC is deleted.
            step13: Try to perform cvc logout with security key and verify its failure.
            step14: Try to perform cvc logout without security key and verify its success.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = " 	IBMi - CVC security key validation for IBMi command line."
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
            self.log.info("Step1: cvc login to CS and generate a token file with security key")
            sec_args_key = {'tokenfile': "TC{0}".format(self.id),
                        'security_key': "IBMiAUTOMATIONTC"}
            sec_args_nokey = {'tokenfile': "TC{0}".format(self.id)}
            self.log.info("create backupSet without CVC")
            self.helper.create_backupset(name=backupset_name, delete=True)
            self.cvc.login(**sec_args_key)

            self.log.info("step2: use the token file to create a SC without providing the security key.")
            status = self.cvc.create_sc(subclient_name=self.subclient_name,
                                        content=content,
                                        storage_policy=self.storage_policy,
                                        backupset_name=backupset_name,
                                        exception_content=None,
                                        validate=False,
                                        **sec_args_nokey)
            self.log.info("status output is {0}".format(status))
            self.log.info("step3: Validate that creating SC has failed as security key is not provided.")
            if "Login info cannot be loaded" not in status:
                raise Exception("CVC Security key validation had failed as CVC command "
                                "worked without key while login is performed with key")

            self.log.info("step4: Now create a SC with security key and validate that SC is created.")
            self.cvc.create_sc(subclient_name=self.subclient_name,
                                        content=content,
                                        storage_policy=self.storage_policy,
                                        backupset_name=backupset_name,
                                        exception_content=None,
                                        validate=True,
                                        **sec_args_key)
            self.log.info("step5: Now delete the SC with security key and validate that SC is deleted.")
            self.cvc.delete_sc(subclient_name=self.subclient_name,
                               backupset_name=backupset_name,
                               validate=True,
                               **sec_args_key)

            self.log.info("step6: Try to perform cvc logout without security key and verify its failure.")
            status = self.cvc.logout(validate=False, **sec_args_nokey)
            self.log.info("status output is {0}".format(status))
            if "Login info cannot be loaded" not in status:
                raise Exception("CVC Security key validation had failed as CVC command "
                                "worked without key while login is performed with key")

            self.log.info("step7: Try to perform cvc logout with security key and verify its success.")
            self.cvc.logout(validate=True, **sec_args_key)

            self.log.info("Step8: cvc login to CS and generate a token file without security key")
            self.cvc.login(**sec_args_nokey)
            self.log.info("step9: use the token file to create a SC by providing the security key.")
            status = self.cvc.create_sc(subclient_name=self.subclient_name,
                                        content=content,
                                        storage_policy=self.storage_policy,
                                        backupset_name=backupset_name,
                                        exception_content=None,
                                        validate=False,
                                        **sec_args_key)
            self.log.info("status output is {0}".format(status))
            self.log.info("step10: Validate that creating SC has Login info cannot be loaded as security key is provided.")
            if "Login info cannot be loaded" not in status:
                raise Exception("CVC Security key validation had failed as CVC command "
                                "worked with key while login is performed without key")
            self.log.info("step11: Now create a SC without security key and validate that SC is created.")
            self.cvc.create_sc(subclient_name=self.subclient_name,
                                        content=content,
                                        storage_policy=self.storage_policy,
                                        backupset_name=backupset_name,
                                        exception_content=None,
                                        validate=True,
                                        **sec_args_nokey)
            self.log.info("step12: Now delete the SC with security key and validate that SC is deleted.")
            self.cvc.delete_sc(subclient_name=self.subclient_name,
                               backupset_name=backupset_name,
                               validate=True,
                               **sec_args_nokey)
            self.log.info("step13: Try to perform cvc logout with security key and verify its failure.")
            status = self.cvc.logout(validate=False, **sec_args_key)
            self.log.info("status output is {0}".format(status))
            if "Login info cannot be loaded" not in status:
                raise Exception("CVC Security key validation had failed as CVC command "
                                "worked with key while login is performed without key")
            self.log.info("step14: Try to perform cvc logout without security key and verify its success.")
            self.cvc.logout(validate=True, **sec_args_nokey)

            self.log.info("**CVC execution from IBMi has completed successfully**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED

