# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] - [MSP- User Centric] -
                    Install and register from tenant user

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelperUserCentric

class TestCase(CVTestCase):
    """Test case class for validating [Laptop Install] - [MSP- User Centric] - Install and register from tenant user"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop Install] - [MSP- User Centric] - Install and register from tenant user"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell
        # - Please make sure to keep a session active for the client with the user that should be the owner
        #    of the client. [Activation_User]. Same for mac.

    def setup(self):
        """ Setup test case inputs from config template """
        common_inputs = [
            "Activation_User1",
            "Activation_Password1",
            "Activation_User2",
            "Activation_Password2"
        ]

        test_inputs = LaptopHelperUserCentric.set_inputs(self, 'Company2', common_inputs)

        # Generate User map
        test_inputs['user_map'] = LaptopHelperUserCentric.create_pseudo_map(test_inputs)
        self.log.info("User map: [{0}]".format(test_inputs['user_map']))
        self.tcinputs.update(test_inputs)
        self.tcinputs['Activation_User'] = self.tcinputs['Activation_User1']
        self.tcinputs['Activation_Password'] = self.tcinputs['Activation_Password1']

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelperUserCentric(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                1. Set default plan for Tenant Company
                    Make sure to Enable Shared Laptop Usage is enabled for the Company

                2. Create a custom package that uses "Do not require end user interaction", *without
                    auth code, and download the package from cloud.

                3. Install custom package *without authcode with options:
                        <InstallationPackage>.exe /silent /install /silent
                        Run Simcalwrapper to register the client

                4. Make sure backup jobs are triggered for two pseudo clients

                5. Validation
                        - Verify if 3 clients are created in the CS. One physical client and two pseudo client
                        - Check client readiness succeeds
                        - Verify Session->nchatterflag is off in registry for physical client
                        - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the physical client
                        - Verify Plan and company's client group associations for pseudo client
                        - Pseudo Client is visible in Company's devices
                        - Validate client ownership is set to the activating user on pseudo client
                6. Validate backed up user profile for each activated user
                7. Disable shared laptop at company level
                8.Uninstall client and delete from commcell

            """, 200)

            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
        finally:
            laptop_helper.cleanup_user_centric(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': True,
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
        }
