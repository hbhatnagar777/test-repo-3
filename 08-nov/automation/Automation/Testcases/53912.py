# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for [Laptop Install] - [Plans] - Blacklisting with auto activation without active user session -
    ["Always activate with default plan"]

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
from Install.client_installation import Installation
from Server.Security.securityhelper import OrganizationHelper

class TestCase(CVTestCase):
    """Test case class for [Laptop Install] - [Plans] - Always activate with default plan"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [Plans] - ["Always activate with default plan"] property for Commcell"""
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
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            laptop_helper = LaptopHelper(self)

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                - Set default Plan for the Commcell
                - User should be logged in already with domain user
                - Add this domain user to blacklisted user group on the commcell
                - Set a tenant property :
                    qoperation execscript -sn SetCompanySetting.sql -si "Commcell"
                        -si "Always activate with default plan" -si 1
                - Create a custom package with (No Edge Monitor to be launched)
                - Silent install custom package with authcode
                - Validate no owner is set but due to Tenant property set , client should be activated.
                - Validate all client properties post activation
            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            orghelper = OrganizationHelper(self.commcell)
            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']
            install_authcode = Installation(self.tcinputs, self.commcell).commcell_install_authcode()
            self.refresh(install_authcode)

            # Set Commcell property to always activate with default plan
            orghelper.set_tenant_property("Always activate with default plan", "1", "Commcell" )
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )
            client_obj = self.commcell.clients.get(self.tcinputs['Machine_host_name'])
            self.log.info("Client owners : [{0}]".format(client_obj.owners))
            assert client_obj.owners is None, "Client ownership validation failed"

            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)
        finally:
            orghelper.set_tenant_property("Always activate with default plan", "0", "Commcell" )

    def refresh(self, authcode):
        """ Refresh the dicts
        Args:
            authcode (str): Commcell authcode
        """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.custompackage_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }

        self.install_kwargs = {
            'LaunchEdgeMonitor': "false",
            'install_with_authcode': True,
            'authcode': authcode,
            'execute_simcallwrapper': False,
            'check_num_of_devices': False,
            'blacklist_user': self.tcinputs['Activation_User'],
            'expected_owners': []
        }
        # Do not show Edge monitor app
        self.custompackage_kwargs = {
            'backupMonitor': "false",
            'hideApps': "false"
        }
