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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.access_control import AccessControl
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import TestStep, handle_testcase_exception
from cvpysdk.organization import Organization
from cvpysdk.commcell import Commcell


class TestCase(CVTestCase):
    """Test for setting automatic owner assignment to all AD users, Commcell-disabled, Company1-option1, Company2-
    disabled, such that owners should be set honoring the chosen options"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Laptop] [Admin Console]: Test for setting automatic owner assignment to all AD users,\
        Commcell-disabled, Company1-option1, Company2-disabled, such that owners should be set honoring the chosen\
        options"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.access_control_obj = None
        self.table = None
        self.company_details = None
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
        self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))

    @test_step
    def select_option_for_commcell(self, option=""):
        """
            select the second option for automatic ownership assignment
        """

        self.log.info("Select automatic ownership assignment at commcell level")
        self.navigator.navigate_to_devices()
        self.access_control_obj = AccessControl(self.admin_console)
        self.access_control_obj.toggle_automatic_ownership_assignment(option=option)

    @test_step
    def select_option_for_company(self, option):
        """
            select the second option for automatic ownership assignment
        """
        self.navigator.navigate_to_companies()
        self.table = Table(self.admin_console)
        self.table.access_link(self.tcinputs['Tenant_company'])
        self.company_details = CompanyDetails(self.admin_console)
        self.company_details.edit_laptop_ownership(option)

    @test_step
    def verify_owner_assignment_config_for_commcell(self, want_ownership_type=1):

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
    def verify_owner_assignment_config_for_company(self, company_id, want_ownership_type):

        """
        Verify that the ownership assignments settings are configured and set properly for company
        """

        try:
            self.log.info("verifying autoClientOwnerAssignmentType from company properties.")
            Organization(self.commcell, organization_id=company_id).verify_owner_assignment_config(
                want_ownership_type)
        except:
            self.log.error("Failed to verify ownership assignment configuration")
        else:
            self.log.info(f"autoClientOwnerAssignmentType is correctly set.")

    @test_step
    def install_and_activate_with_user(self, with_org=False, company=1):
        """
            install and activate laptop with domain user
        """
        laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])
        self.refresh(with_org=with_org, install_with_authcode=True, company=company)
        laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

    def run(self):
        laptop_helper = LaptopHelper(self)
        try:
            self.log.info("Set automatic ownership assignment for commcell")
            self.select_option_for_commcell(self.admin_console.props['label.allUserProfiles'])
            self.verify_owner_assignment_config_for_commcell(want_ownership_type=1)

            self.log.info("Set automatic ownership assignment to All logged in Active Directory users for company 1")
            self.select_option_for_company(self.admin_console.props['label.allUserProfiles'])
            self.verify_owner_assignment_config_for_company(company_id=self.tcinputs["Company1_id"], want_ownership_type=1)
            self.install_and_activate_with_user(with_org=True, company=1)

            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company2'))

            self.log.info("Set automatic ownership assignment to The first user to login for company 2")
            self.select_option_for_company(self.admin_console.props['label.firstUser'])
            self.verify_owner_assignment_config_for_company(company_id=self.tcinputs["Company2_id"], want_ownership_type=2)
            self.install_and_activate_with_user(with_org=True, company=2)
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            handle_testcase_exception(self, excp)
            laptop_helper.cleanup(self.tcinputs)

    def tear_down(self):
        try:
            self.access_control_obj.toggle_automatic_ownership_assignment("All logged in Active Directory users")

        except Exception as e:
            handle_testcase_exception(self, e)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def refresh(self, install_with_authcode=False, with_org=False, company=1):
        """ Refresh the dicts
        Args:
            install_with_authcode: Flag to identify for installation with or without authcode
            authcode (str): Authcode for commcell
            with_org: Flag to identify values of config_kwargs
            ownership_enabled (int): Flag to check if expected_owners key needs to be populated

        """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': with_org & install_with_authcode,
            'org_set_default_plan': with_org,
        }

        self.install_kwargs = {
            'install_with_authcode': install_with_authcode,
            'execute_simcallwrapper': not install_with_authcode,
            'check_num_of_devices': False,
            'client_groups': [self.tcinputs['Default_Plan'] + ' clients', 'Laptop clients'],
            'skip_osc': True
        }

        if company == 1:
            self.install_kwargs["expected_owners"] = self.tcinputs["Expected_ADUsers_As_Owners"]