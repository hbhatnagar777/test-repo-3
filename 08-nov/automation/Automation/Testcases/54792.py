# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for [Laptop Install] - [MSP] - Install with /authcode and validate blacklisted user do not become owner
    with missing LaptopAdmins client group

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Test case class for validating blacklisted user do not become owner of the client with missing Laptop Admins
        user group"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install]-[MSP]-/authcode.  Blacklisted user should not become client owner with
                        missing Laptop Admins client group"""
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
            common_inputs = ["Activation_User1", "Activation_Password1"]
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1', common_inputs, ["Blacklist_User"]))
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])
            laptop_helper.organization.delete_blacklisted_group(blacklist_group="Laptop Admins")

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            BLACKLIST USER AND INSTALL WITH AUTHCODE
                - Delete Blacklisted USer Group "Laptop Admins"
                1. Enable authcode and set default plan for Tenant Company and install custom package
                2. Blacklist user1 and install with user2
                3. Install with /authcode ###### option
                4. Wait for osc backup, change subclient content and execute backup/restore
                5. Make sure blacklisted user1 does not become the owner of the client
                6. Validate client installation
            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)
        finally:
            laptop_helper.organization.create_blacklisted_group(blacklist_group="Laptop Admins")

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
            'blacklist_user': self.tcinputs['Blacklist_User'],
            'activation_time_limit': 12
        }
