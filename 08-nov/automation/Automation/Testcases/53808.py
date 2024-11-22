# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating
    [Laptop Install] - [MSP] - Reinstall and register with new client name and new owner  - New Client Activation

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop import laptopconstants
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Test case class for validating
        [Laptop Install] - [MSP] - Reinstall and register with new client name and new owner  - New Client Activation"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [MSP] - Reinstall and register with new client name and new owner
                            - New Client Activation"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Company should be created on commcell
        # - A Plan should be created on commcell which could be associated to the company as default plan.

    def run(self):
        """ Main function for test case execution."""
        try:
            test_inputs = LaptopHelper.set_inputs(self, 'Company1', ['Activation_User1', 'Activation_Password1'])
            self.tcinputs.update(test_inputs)
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            REINSTALL WITH DIFFERENT USER AND DIFFERENT CLIENT NAME - NEW CLIENT
                1. Set default plan for Tenant Company and install custom package
                2. Execute SimCallWrapper and register the client with user [user1]
                3. Wait for osc backup, change subclient content and execute backup/restore
                4. Do client validation.
                5. Uninstall client locally
                6. Install custom package again on the client with new name and register with the user [user2]
            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            self.install_kwargs['delete_client'] = False
            self.install_kwargs['blacklist_user'] = self.tcinputs['Activation_User']
            self.install_kwargs['expected_owners'] = [self.tcinputs['Activation_User1']]
            self.tcinputs['Activation_User'] = self.tcinputs['Activation_User1']
            self.tcinputs['Activation_Password'] = self.tcinputs['Activation_Password1']
            client = self.tcinputs['Machine_client_name']
            self.install_kwargs['new_client_name'] = client + laptopconstants.REINSTALL_NAME
            self.install_kwargs['register_with_new_name'] = True
            self.install_kwargs['wait_for_reinstalled_client'] = True
            laptop_helper.company.refresh()

            # Reinstall laptop and validate
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
            'org_enable_auth_code': False,
            'org_set_default_plan': True
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True
        }
