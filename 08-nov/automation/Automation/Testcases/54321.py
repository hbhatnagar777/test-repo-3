# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] - [MSP- User Centric] - Reinstall client with auth code of same company

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelperUserCentric

class TestCase(CVTestCase):
    """Test case class for [Laptop Install] - [MSP- User Centric] - Reinstall client with auth code of same company"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [MSP- User Centric] - Reinstall client with auth code of same company"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Company should be created on commcell
        # - A Plan should be created on commcell which could be associated to the company as default plan.

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
                            REINSTALL WITH AUTHCODE FOR SAME COMPANY - TAKEOVER
                - Create a custom package that uses "Do not require end user interaction", *without
                    auth code, and download the package from cloud.

                1. Enable shared laptop, authcode and set default plan for Tenant Company and install custom package
                2. Install with /authcode ###### option
                3. Wait for osc backup, change subclient content and execute backup/restore
                4. Do client validation. Validate backed up user profile for each activated user.
                5. Uninstall client locally
                6. Install custom package again on the client with authcode of same company
                7. Validate backed up user profile for each activated user
                8. Disable shared laptop at company level and clenaup the client
            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            self.install_kwargs['delete_client'] = False
            self.install_kwargs['authcode'] = laptop_helper.company.auth_code
            self.install_kwargs['skip_osc'] = True
            self.install_kwargs['check_num_of_devices'] = False
            self.install_kwargs['wait_for_reinstalled_client'] = True
            self.config_kwargs['org_enable_auth_code'] = False
            laptop_helper.company.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            laptop_helper.cleanup(self.tcinputs)

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
            'org_enable_auth_code': True,
            'org_set_default_plan': True
        }

        self.install_kwargs = {
            'install_with_authcode': True,
            'execute_simcallwrapper': False,
        }
