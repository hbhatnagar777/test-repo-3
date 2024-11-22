# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for
    [Laptop Install]-[Plans]- [Takeover] - Reinstall client with admin user
        with reg keys  dAllowLaptopRepurposeByAdmin and dForceClientOverride

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
from Server.Security.securityhelper import OrganizationHelper

class TestCase(CVTestCase):
    """Test case class for validating Reinstall client with admin user with reg keys
        dAllowLaptopRepurposeByAdmin and dForceClientOverride"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] [Plans] [TAKEOVER] - Reinstall client with admin user and reg keys
                            dAllowLaptopRepurposeByAdmin and dForceClientOverride set"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - A Laptop Plan should be created on commcell

    def setup(self):
        """ Setup test case inputs from config template """
        self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell', ["User_admin", "Password_admin"], []))
        self.tcinputs['Skip_RDP_Users'] = [self.tcinputs['User_admin']]

    def run(self):
        """ Main function for test case execution."""
        try:

            laptop_helper = LaptopHelper(self)

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            REINSTALL WITH ADMIN USER - OLD CLIENT TAKEOVER
                1. Set default plan for commcell and install custom package
                2. Execute SimCallWrapper and register the client with user [user1]
                3. Wait for osc backup, change subclient content and execute backup/restore
                4. Do client validation.
                5. Uninstall client locally
                6. Set reg keys dAllowLaptopRepurposeByAdmin and dForceClientOverride
                6. Install custom package again on the client and register with the admin user [admin]
                7. Ownership should not change from the original user and client gets activated with same name.
            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            orghelper = OrganizationHelper(self.commcell)
            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']
            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            # Reinstall laptop and perform validation
            self.install_kwargs['delete_client'] = False
            self.install_kwargs['expected_owners'] = [self.tcinputs['Activation_User'],
                                                      self.tcinputs['User_admin']]
            self.tcinputs['Activation_User'] = self.tcinputs['User_admin']
            self.tcinputs['Activation_Password'] = self.tcinputs['Password_admin']
            self.install_kwargs['skip_osc'] = True
            laptop_helper.utils.modify_additional_settings('dAllowLaptopRepurposeByAdmin', "1", 'CommServe', 'INTEGER')
            laptop_helper.utils.modify_additional_settings('dForceClientOverride', "1", 'CommServe', 'INTEGER')
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)
        finally:
            laptop_helper.utils.delete_additional_settings('dAllowLaptopRepurposeByAdmin', 'CommServe')
            laptop_helper.utils.delete_additional_settings('dForceClientOverride', 'CommServe')

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
            'wait_for_device_association': True,
            'check_num_of_devices': False
        }
