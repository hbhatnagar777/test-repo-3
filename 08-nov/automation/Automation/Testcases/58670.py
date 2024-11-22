# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] - [MSP] - [Cloud Laptop] - Install with /authcode

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Test case class for validating [Laptop Install] - [MSP] - [Cloud Laptop] - Install with /authcode"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [MSP] - [Cloud Laptop] - Install with /authcode"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell

    def setup(self):
        """ Setup test case inputs from config template """
        common_inputs = ["CloudLaptopPlan", "CloudUser", "CloudUserPassword"]
        testcase_inputs = LaptopHelper.set_inputs(self, 'Company1', common_inputs)
        self.tcinputs.update(testcase_inputs)
        self.tcinputs['Activation_User'] = testcase_inputs['CloudUser']
        self.tcinputs['Activation_Password'] = testcase_inputs['CloudUserPassword']
        self.tcinputs['Plan'] = testcase_inputs['CloudLaptopPlan']

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'], plan=self.tcinputs['Plan'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                a. Associate a tenant user to a Cloud Laptop Plan [ Storage should be Cloud library ]
                    Do not set this plan as default plan. [To validate activation for user association]
                b. Install Custom package on client with authcode
                c. Auto activation
                    - Validate Storage Accelerator package is installed on the client
                d. Backup Validation
                    - Validate automatic triggered first full backup
                    - Validate incremental automatic schedule triggered backup
                e. Validation
                    - Validate all registry keys
                    - Check client readiness
                    - Verify Session->nchatterflag is off in registry for clients
                    - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                    - Verify Plan and company's client group associations for activated client
                    - Validate client ownership is set to the activating user
            """, 200)

            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': True,
            'org_set_default_plan': False
        }

        self.install_kwargs = {
            'install_with_authcode': True,
            'execute_simcallwrapper': False,
            'check_client_activation': True,
            'cloud_laptop': True,
            'client_groups': ['Laptop Clients', self.tcinputs['Tenant_company'], self.tcinputs['Plan'] + ' clients']
        }
