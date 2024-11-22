# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This testcase will verify [Laptop Install]: Auto Activation from a Laptop from a deleted domain user

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
from Server.Security.userhelper import UserHelper

class TestCase(CVTestCase):
    """Test case class for [Laptop Install]: Auto Activation from a Laptop from a deleted domain user"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install]: Auto Activation from a Laptop from a deleted domain user"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        # PRE-REQUISITES OF THE TESTCASE
        # - A laptop Plan should be created on commcell which should be associated to the commcell

    def setup(self):
        """ Setup test case inputs from config template """
        common_inputs = ["DeletedDomainUser", "DeletedDomainUserPassword"]
        self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1', common_inputs, []))

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                1. Delete a domain user. [ Domain user deleted entry should be present in Database ]
                2. Have active session on the client with this domain user
                3. Install a client using authcode and see if auto-activation call is triggered.
                4. Client should be activated with existing deleted user's id.

                Source:
                https://updatecenter.commvault.com/Form.aspx?BuildID=1100080&FormID=72275
            """, 200)

            self.refresh()
            self.tcinputs['Activation_User'] = self.tcinputs['DeletedDomainUser']
            self.tcinputs['Activation_Password'] = self.tcinputs['DeletedDomainUserPassword']
            user = self.tcinputs['Activation_User']
            password = self.tcinputs['Activation_Password']
            user_helper = UserHelper(self.commcell)
            user_helper.create_user(user_name=user, full_name=user, email='test@commvault.com', password=password)
            user_helper.delete_user(user_name=user, new_user='admin')
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)
        finally:
            user_helper.delete_user(user_name=self.tcinputs['DeletedDomainUser'], new_user='admin')

    def refresh(self):
        """ Refresh the dicts
        """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': True,
            'org_set_default_plan': True
        }

        self.install_kwargs = {
            'install_with_authcode': True,
            'execute_simcallwrapper': False
        }
