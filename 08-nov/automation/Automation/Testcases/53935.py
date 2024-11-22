# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for [Laptop Install] - [MSP] - Set Tenant property ["Always activate with default plan"]
    and activate client

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Test case class for [Laptop Install] - [MSP] - Set Tenant property
        ["Always activate with default plan"] and activate client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop Install] - [MSP] - Set Tenant property [Always activate with default plan] and activate"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Default_Plan should be created on commcell

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(
                LaptopHelper.set_inputs(
                    self, 'Company1', ['Activation_User1', 'Activation_Password1'], ["Blacklist_User"]
                )
            )
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                - Enable Authcode and set default plan for the Tenant Company
                - User should have active user session on the client with domain user1 and user2
                - Add domain user1 to blacklisted usergroup on the commcell
                - Set a tenant property :
                    qoperation execscript -sn SetCompanySetting.sql -si "Tenant Company name"
                        -si "Always activate with default plan" -si 1
                - Create a custom package with (No Edge Monitor to be launched)
                - Silent install custom package with authcode
                - Client should be activated as user2 as owner of the client.
                - Validate all client properties post activation
            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            self.refresh()

            # Set Commcell property to always activate with default plan
            laptop_helper.organization.set_tenant_property(
                "Always activate with default plan", "1", self.tcinputs['Tenant_company']
            )
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)
        finally:
            laptop_helper.organization.set_tenant_property(
                "Always activate with default plan", "0", self.tcinputs['Tenant_company']
            )


    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.custompackage_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': True,
            'org_set_default_plan': True
        }

        self.install_kwargs = {
            'LaunchEdgeMonitor': "false",
            'install_with_authcode': True,
            'execute_simcallwrapper': False,
            'blacklist_user': self.tcinputs['Blacklist_User'],
        }

        # Do not launch Edge monitor app
        self.custompackage_kwargs = {
            'backupMonitor': "false",
            'hideApps': "false"
        }
