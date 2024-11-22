# -*- coding: utf-8 -*-
from Laptop.CloudLaptop import cloudlaptophelper

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] - [MSP] - Install and register from tenant user

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
from Laptop.CloudLaptop import cloudlaptophelper
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Test case class for validating [Laptop Install] - [MSP] - [CloudLaptop] -Scale test-  Install and register from tenant user"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [MSP] - [CloudLaptop] - Validate scaletest for  bulk laptops backups and restores"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.utility = OptionsSelector(self._commcell)
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.tcinputs = {
            'numfiles': None,
            'numfolders': None,
            'receivers': None,
            'testdatapath':None,
            'filesize':None,
            'OperationType':None,
            'levels':None
            }

        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell

    def setup(self):
        """ Setup test case inputs from config template """
        platform_inputs = [
            "NetworkPath",
            "NetworkUser",
            "NetworkPassword"
        ]

        testcase_inputs = LaptopHelper.set_inputs(
             self, 'Company1', [], platform_inputs
        )
        testcase_inputs['Machine_host_name'] = self.tcinputs['Machine_host_name']
        testcase_inputs['Machine_user_name'] = self.tcinputs['Machine_user_name']
        testcase_inputs['Machine_password'] = self.tcinputs['Machine_password']

        self.tcinputs.update(testcase_inputs)

    def run(self):
        """ Main function for test case execution."""
        try:

            laptop_helper = LaptopHelper(self)
            cloudlaptop_helper = cloudlaptophelper.CloudLaptopHelper(self)

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                a. Associate a tenant user to a Cloud Laptop Plan [ Storage should be Cloud library ]
                    Do not set this plan as default plan. [To validate activation for user association]
                b. Install Custom package on client
                c. Register with SimCallWrapper
                    - Validate Storage Accelerator package is installed on the client
                d. Backup Validation
                    - Validate automatic triggered first full backup
                    - Validate incremental automatic schedule triggered backup
                    - Create Scale test data basing on the inpus given
                    - Validate backup, restore, synthfull backups.
                e. Validation
                    - Validate all registry keys
                    - Check client readiness
                    - Verify Session->nchatterflag is off in registry for clients
                    - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                    - Verify Plan and company's client group associations for activated client
                    - Validate client ownership is set to the activating user
            """, 200)

            self.refresh()
            self.tcinputs['Skip_RDP_Users'] = [self.tcinputs['Activation_User']]
            if not (self.commcell.clients.has_client(self.tcinputs['Machine_client_name']) and self.tcinputs['OperationType'] == "DataOperations"):
                laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            """ Create scale test data and validate backup and restore"""

            cloudlaptop_helper.scaletest(self.tcinputs)

            if self.tcinputs['Machine_object'].os_info.lower() == "windows":
                laptop_helper.copy_client_logs(self.tcinputs['Machine_object'])

            self.testcase_status = "PASSED"

            laptop_helper.sendemail_scaletest(self.tcinputs, self.testcase_status)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            # laptop_helper.cleanup(self.tcinputs)
            self.testcase_status = "FAILED"
            laptop_helper.sendemail_scaletest(self.tcinputs, self.testcase_status)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'check_client_activation': True,
            'cloud_laptop': True
        }
