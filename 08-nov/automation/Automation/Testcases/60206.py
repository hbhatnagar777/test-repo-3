# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
from Server.Security.securityhelper import OrganizationHelper
from AutomationUtils.idautils import CommonUtils
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.access_control import AccessControl
from Web.Common.page_object import TestStep, handle_testcase_exception
import time
from cvpysdk.commcell import Commcell
from AutomationUtils.windows_machine import WindowsMachine
import re


class TestCase(CVTestCase):
    """Test for setting automatic owner assignment to the first user to login by first logging in as Administrator and
    install and activate as domain user 1 and later login as domain user 2 and restart services, both should become the
    owners"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Laptop] [Admin Console]: Test for setting automatic owner assignment to the first user to login\
         by first logging in as Administrator and install and activate as domain user 1 and later login as domain\
         user 2 and restart services, both should become the owners"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.access_control_obj = None
        self.tcinputs = {}
        self.install_kwargs = {}
        self.config_kwargs = {}

    def setup(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)

        self.navigator = self.admin_console.navigator
        common_inputs = ["Activation_User2", "Activation_Password2", "Activation_User3", "Activation_Password3", "Activation_User4", "Activation_Password4"]
        self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell', common_inputs))

    @test_step
    def select_option_two(self):
        """
            select the second option for automatic ownership assignment
        """
        self.navigator.navigate_to_devices()
        self.access_control_obj = AccessControl(self.admin_console)
        self.access_control_obj.toggle_automatic_ownership_assignment(self.admin_console.props['label.firstUser'])

    @test_step
    def verify_owner_assignment_config(self, want_ownership_type=0):

        """
        Verify that the ownership assignments settings are configured and set properly
        """
        try:
            self.log.info("verifying autoClientOwnerAssignmentType from commcell properties.")
            ownership_type = Commcell(self.inputJSONnode['commcell']['webconsoleHostname'],
                                      self.inputJSONnode['commcell']['commcellUsername'],
                                      self.inputJSONnode['commcell']['commcellPassword']
                                      ).verify_owner_assignment_config()["commCellInfo"]["generalInfo"][
                "autoClientOwnerAssignmentType"]
            if ownership_type != want_ownership_type:
                self.log.error(
                    f"autoClientOwnerAssignmentType value not set correctly. Found: {ownership_type}, Expected: {want_ownership_type}")
            else:
                self.log.info(
                    f"autoClientOwnerAssignmentType is correctly set. Found: {ownership_type}, Expected: {want_ownership_type}")
        except:
            self.log.error("Failed to verify ownership assignment configuration")

    @test_step
    def install_and_activate_with_user_1(self):
        """
            install and activate laptop with user 1
        """
        laptop_helper = LaptopHelper(self)
        orghelper = OrganizationHelper(self.commcell)
        orghelper.commcell_default_plan = self.tcinputs['Default_Plan']
        self.refresh()
        client_machine = WindowsMachine(self.tcinputs['Machine_host_name'], self.commcell)
        user_sessions = client_machine.execute_command("quser").formatted_output
        session_regex = re.compile(r"{0}(\s*)(\d)".format(self.tcinputs['Activation_User'].split('\\')[1]))
        if session_regex.search(user_sessions) is not None:
            client_machine.execute_command(f"logoff {int(session_regex.search(user_sessions).group(2))}")
        session_regex = re.compile(r"{0}(\s*)(\d)".format(self.tcinputs['Activation_User2'].split('\\')[1]))
        if session_regex.search(user_sessions) is not None:
            client_machine.execute_command(f"logoff {int(session_regex.search(user_sessions).group(2))}")
        session_regex = re.compile(r"{0}(\s*)(\d)".format(self.tcinputs['Activation_User3'].split('\\')[1]))
        if session_regex.search(user_sessions) is not None:
            client_machine.execute_command(f"logoff {int(session_regex.search(user_sessions).group(2))}")
        self.tcinputs["Skip_RDP_Users"] = [self.tcinputs["Activation_User"], self.tcinputs["Activation_User2"], self.tcinputs["Activation_User3"]]
        laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

    @test_step
    def login_with_user_2_and_restart(self):
        """
            login with domain user 2 and restart
        """
        laptop_helper = None
        try:
            laptop_helper = LaptopHelper(self)
            orghelper = OrganizationHelper(self.commcell)
            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']

            self.tcinputs["Skip_RDP_Users"] = [self.tcinputs["Activation_User"], self.tcinputs["Activation_User3"], self.tcinputs["Activation_User4"]]
            machine_object = laptop_helper.utility.get_machine_object(
                self.tcinputs['Machine_host_name'], self.tcinputs['Machine_user_name'],
                self.tcinputs['Machine_password']
            )

            laptop_helper.create_rdp_sessions(self.tcinputs, machine_object)

            CommonUtils(self.commcell).restart_services([self.tcinputs["Machine_host_name"]])
            expected_owners = [self.tcinputs["Activation_User"], self.tcinputs["Activation_User2"]]
            orghelper.validate_client_owners(self.tcinputs['Machine_host_name'], expected_owners=expected_owners)

        except Exception as err:
            laptop_helper.tc.fail(str(err))
            self.log.error("Testcase failed with exception [{0}]".format(str(err)))
            laptop_helper.cleanup(self.tcinputs)
            handle_testcase_exception(err)

    def run(self):
        laptop_helper = LaptopHelper(self)
        try:
            self.select_option_two()
            time.sleep(3)
            self.verify_owner_assignment_config(want_ownership_type=2)
            self.install_and_activate_with_user_1()
            self.login_with_user_2_and_restart()
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            handle_testcase_exception(self, excp)
            laptop_helper.cleanup(self.tcinputs)

    def tear_down(self):
        try:
            self.access_control_obj.toggle_automatic_ownership_assignment(self.admin_console.props['label.allUserProfiles'])

        except Exception as e:
            handle_testcase_exception(self, e)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def refresh(self, install_with_authcode=False, authcode=None):
        """ Refresh the dicts
        Args:
            authcode (str): Authcode for commcell

        """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False,
        }

        self.install_kwargs = {
            'install_with_authcode': install_with_authcode,
            'execute_simcallwrapper': not install_with_authcode,
            'check_num_of_devices': False,
            'client_groups': [self.tcinputs['Default_Plan'] + ' clients', 'Laptop clients']
        }

        if install_with_authcode: self.install_kwargs["authcode"] = authcode