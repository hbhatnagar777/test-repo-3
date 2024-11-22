# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] [MSP] :  Plan name is given with Custom package and register with domain user

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Test case class for validating
    [Laptop Install] [MSP] :  Plan name is given with Custom package and register with domain user"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop Install] [MSP] :  Plan name is given with Custom package and register with domain user"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell
        # - Assign 'Subscribe plan' security permission to a tenant domain user to a non* default laptop plan
        # - Also 'associate' this domain user to another laptop plan (default/ or non default any)

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1', ['UserSubscribedPlan']))
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])
            self.tcinputs['Plan'] = self.tcinputs['UserSubscribedPlan']

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                1. Set default plan for Tenant Company
                2. Create a custom package with plan name specified in the plan
                3. Install custom package <InstallationPackage>.exe /silent /install /silent
                4. Validate if the activation user got associated to the plan specified in the custom package
                    and validate following:
                        - Check client readiness succeeds
                        - Session->nchatterflag is off in registry for clients
                        - FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                        - Plan and company's client group associations for activated client
                        - Client ownership is set to the activating user
            """, 200)

            self.refresh()
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.custompackage_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'client_groups': ['Laptop Clients', self.tcinputs['Tenant_company'], self.tcinputs['Plan'] + ' clients']
        }

        self.custompackage_kwargs = {
            'SubClientPlan': self.tcinputs['Plan']
        }