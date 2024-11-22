# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This testcase will verify [Laptop Install] - [Plans] - Install with commcell's authcode and default plan

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
import re

class TestCase(CVTestCase):
    "Test case class for [Laptop Install]-[MSP]-Modify Restricted users and validate activation with domain user"

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install]-[MSP]-Modify Restricted users and validate activation with domain user"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self._restricted_users = None
        self._restricted_user = None
        # PRE-REQUISITES OF THE TESTCASE
        # - A laptop Plan should be created on commcell which should be associated to the commcell

        # Cannot install with non administrator user as not able to figure out how local admin can launch installer
        # remotely by schtasks. Just does not have windows privledges.
        # and launching installer remotely does not launch EdgeMonitor app if not launched like schtasks by
        # impersonating NT AUTHORITY \ SYSTEM user.

    def setup(self):
        """ Setup test case inputs from config template """
        platform_inputs = ["Blacklist_User", "LocalUser", "LocalUser_Password"]
        self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1', [], platform_inputs))
        # Do not create RDP session for user yet.
        self.tcinputs['Activation_User1'] = self.tcinputs['LocalUser']
        self.tcinputs['Activation_Password1'] = self.tcinputs['LocalUser_Password']
        self.tcinputs['Skip_RDP_Users'] = [self.tcinputs['Activation_User']]
        self._restricted_user = self.tcinputs['LocalUser']
        self._restricted_users = "admin,administrator,administrador,root,"+self._restricted_user

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                Restricted users:

                By default, restricted users are as follows:  admin,administrator,administrador,root
                However, you can add more by adding a regkey.
                Gxglobalparam\\RestrictedLocalUserNames Value = admin,administrator,administrador,root,someuser
                You must include the old list plus the new user if you want to keep them all.

                1. Set gxlobalparam for a new local user: Gxglobalparam\\RestrictedLocalUserNames
                        Value = admin,administrator,administrador,root,admin2
                2. Install custom package when only localmachine\\admin2 user is logged in on the client
                3. Activation should fail with restricted user message
                4. Login as domain user and activation should succeed
            """, 200)

            # Add activation user to the restricted users list
            laptop_helper.utils.modify_additional_settings('RestrictedLocalUserNames', self._restricted_users)

            # Skip opening RDP session for activation user and open RDP session for restricted user only
            self.tcinputs['Skip_RDP_Users'] = [self.tcinputs['Activation_User']]
            self.refresh()
            try:
                laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
                raise Exception("Activation expected to fail. TestCase Failed.")
            except Exception as excp:
                if not re.search("Failed to activate", str(excp)):
                    raise Exception("Activation expected to fail. TestCase Failed.")
                self.log.info("Activation failed as expected: [{0}]".format(excp))

            # Create RDP session for domain user and check if activation goes through and validate.
            # If there's already an old session, create a new fresh session for the user.
            # Reason:
            # For future references
            # Edge Monitor is not launched when
            # -    There are active sessions for (###### OR <clientname>\administrator)  and ######,
            #       and (interactive Or silent)  installation is done from (###### OR <clientname>\administrator)
            # Edge Monitor is launched on ###### only if we log off and ‘sign out’ the ######,
            #  from the client and log back in again.
            try:
                session_id = self.tcinputs['Machine_object'].get_login_session_id(self.tcinputs['Activation_User'])
                if session_id:
                    self.tcinputs['Machine_object'].logoff_session_id(session_id)
            except Exception as excp:
                if not re.search("No session exists", str(excp)):
                    self.log.info("No active session exists for user [{0}]".format(self.tcinputs['Activation_User']))

            self.tcinputs['Skip_RDP_Users'] = []
            laptop_helper.create_rdp_sessions(self.tcinputs)
            _ = laptop_helper.organization.is_client_activated(
                self.tcinputs['Machine_client_name'],
                self.tcinputs['Default_Plan'],
                time_limit=8
            )
            laptop_helper.utility.sleep_time(5)
            laptop_helper.is_edge_monitor_running(self.tcinputs['Machine_object'])
            laptop_helper.utils.osc_backup_and_restore(self.tcinputs['Machine_object'], validate=True)
            laptop_helper.organization.validate_client(self.tcinputs['Machine_object'],
                                                       expected_owners=[self.tcinputs['Activation_User']])
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)
        finally:
            laptop_helper.utils.delete_additional_settings('RestrictedLocalUserNames')

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
            'blacklist_user': self.tcinputs['Blacklist_User']
        }

