# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This testcase will verify [Laptop Install] - [Plans] - "Always activate with default plan" property for Commcell
for new Domain

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
    """Test case class for [Laptop Install]-[Plans]-Always activate with default plan property for
         Commcell for new Domain"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install]-[Plans]-Always activate with default plan property for a new domain"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}
        self._restricted_users = None
        self._restricted_user = None
        # PRE-REQUISITES OF THE TESTCASE
        # - A laptop Plan should be created on commcell which should be associated to the commcell

    def setup(self):
        """ Setup test case inputs from config template """
        common_inputs = ["NewDomainUser", "NewDomainUser_Password"]
        test_inputs = LaptopHelper.set_inputs(self, 'Commcell', common_inputs)
        self.tcinputs.update(test_inputs)
        self.tcinputs['Activation_User'] = self.tcinputs['NewDomainUser']
        self.tcinputs['Activation_Password'] = self.tcinputs['NewDomainUser_Password']
        self.tcinputs['Activation_User1'] = self.tcinputs['Machine_user_name']
        self.tcinputs['Activation_Password1'] = self.tcinputs['Machine_password']

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelper(self)
            user = self.tcinputs['Activation_User']
            laptop_helper.organization.is_domain_user(user)
            domain = user.split('\\')[0]
            commcell = self.commcell
            assert not commcell.domains.has_domain(domain), "Domain [{0}] already exists on commcell".format(domain)
            assert not commcell.users.has_user(user), "User [{0}] already exists on commcell".format(user)
            # Don't delete domain here. User might need it. Let user delete it

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                Need a client machine in a domain thats not already created in the CS.
                Need a tenant property set:
                qoperation execscript -sn SetCompanySetting.sql
                    -si "Commcell" -si "Always activate with default plan" -si 1
                Create a custom package for registerme but without edge monitor
                Install this package silently with authcode on command line.
                custompackage.exe /silent /install /silent /authcode #####
                Verify activation
                Login with a domain user
                Restart services
                Verify umdsprovider row is created for the domain and ownercompanyid of the authcode
                Verify user is created
            """, 200)

            #Get commcell's authcode
            orghelper = OrganizationHelper(self.commcell)
            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']
            install_authcode = Installation(self.tcinputs, self.commcell).commcell_install_authcode()
            self.refresh(install_authcode)

            # Set Commcell property to always activate with default plan
            orghelper.set_tenant_property("Always activate with default plan", "1", "Commcell" )

            # Skip opening RDP session for activation user and install with NT Authority / System user
            self.tcinputs['Skip_RDP_Users'] = [self.tcinputs['Activation_User']]
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )

            # Create RDP session for domain user and validate domain gets created
            if self.tcinputs['Machine_object'].has_active_session(self.tcinputs['Activation_User']):
                session_id = self.tcinputs['Machine_object'].get_login_session_id(self.tcinputs['Activation_User'])
                if session_id:
                    self.tcinputs['Machine_object'].logoff_session_id(session_id)
            self.tcinputs['Skip_RDP_Users'] = []
            laptop_helper.create_rdp_sessions(self.tcinputs)

            # Restart client services.
            laptop_helper.utils.restart_services([self.tcinputs['Machine_host_name']])

            # Wait for domain creation to go through from the CVD thread.
            laptop_helper.utility.sleep_time(30)
            laptop_helper.organization.validate_client_owners(self.tcinputs['Machine_host_name'],
                                                              expected_owners=[self.tcinputs['Activation_User']])

            # Validate domain and user got created
            assert commcell.domains.has_domain(domain), "Domain not created automatically."
            assert commcell.users.has_user(user), "User not created post client installation."
            user_id = commcell.users.get(user).user_id
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)
        finally:
            orghelper.set_tenant_property("Always activate with default plan", "0", "Commcell" )
            laptop_helper.organization.delete_domain(domain)
            laptop_helper.utility.update_commserve_db("delete from umusers where id="+str(user_id))

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
            'expected_owners': []
        }

        # Do not show Edge monitor app
        self.custompackage_kwargs = {
            'backupMonitor': "false",
            'hideApps': "false"
        }
