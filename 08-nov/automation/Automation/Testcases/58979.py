# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify overview dashboard page loading without any errors."""
from cvpysdk.organization import Organizations
from cvpysdk.security.user import Users
from cvpysdk.commcell import Commcell

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.metallic_helper import MetallicMain

from Reports.utils import TestCaseUtils

class TestCase(CVTestCase):
    """Test case to verify Linking and Unlinking of metallic services in on-prem CS"""
    test_step = TestStep()

    def __init__(self):
        super().__init__()
        self.name = "Linking and Unlinking of metallic services in on-prem CS"
        self.tcinputs = {
            "OnPremCS": None,
            "OnPremUserName": None,
            "OnPremPassword": None
        }
        self.browser = None
        self.admin_console = None
        self.company_name = None
        self.company_email = None
        self.company_contactname = None
        self.company_alias = None
        self.company_admin_user = None
        self.onprem_user = None
        self.companies_obj = None
        self.onprem_cs_obj = None
        self.strong_password = None
        self.metallic_helper_obj = None
        self.solutions_marked_completed = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # Test Case constants
        self.company_name = f'{self.id}_company'
        self.company_email = f'{self.id}@domain.com'
        self.company_contactname = f'{self.id}_contactName'
        self.company_alias = f'{self.id}_alias'
        self.company_admin_user = f'{self.company_alias}\\{self.id}'
        self.onprem_user = f"{self.company_alias}\\{self.tcinputs['OnPremUserName']}"
        self.strong_password = '#####'

    def login_to_metallic_cs(self, logout_first=False):
        """Login to Metallic CS"""
        if logout_first:
            self.admin_console.logout()
        self.admin_console = AdminConsole(self.browser,
                                          self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                 password=self.inputJSONnode['commcell']['commcellPassword'])

    def login_to_on_prem_cs(self, logout_first=False):
        """Login to OnpremCS"""
        if logout_first:
            self.admin_console.logout()
        self.admin_console = AdminConsole(self.browser,
                                          self.tcinputs['OnPremCS'])
        self.admin_console.login(username=self.tcinputs['OnPremUserName'],
                                 password=self.tcinputs['OnPremPassword'])

    def init_tc(self):
        """Initialize browser and redirect to page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.login_to_on_prem_cs()
            self.companies_obj = Organizations(self.commcell)
            self.onprem_cs_obj = Commcell(self.tcinputs['OnPremCS'],
                                          self.tcinputs['OnPremUserName'],
                                          self.tcinputs['OnPremPassword'])
            self.metallic_helper_obj = MetallicMain(self.admin_console)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def cleanup(self):
        """Cleanup function to run before and after test steps"""
        self.metallic_helper_obj.getting_started.navigate_to_metallic()
        if self.metallic_helper_obj.getting_started.get_metallic_link_status():
            self.metallic_helper_obj.getting_started.unlink_metallic_account()
        if not self.metallic_helper_obj.getting_started.get_metallic_link_status():
            if self.companies_obj.has_organization(self.company_name):
                self.companies_obj.delete(self.company_name)
        self.metallic_helper_obj.delete_additional_settings(self.onprem_cs_obj)

    def pre_requisites_tc(self):
        """Pre requisites before the test steps begin"""
        self.companies_obj.add(self.company_name, self.company_email, self.company_contactname,
                           self.company_alias)
        company_admin_user = Users(self.commcell).get(self.company_admin_user)
        company_admin_user.update_user_password(self.strong_password,
                                                self.inputJSONnode['commcell']['commcellPassword'])
        self.metallic_helper_obj.add_additional_settings(
            self.onprem_cs_obj, self.inputJSONnode['commcell']['webconsoleHostname'])

    def mark_solutions_complete_for_company(self):
        """Marks all available solutions as complete"""
        self.admin_console.navigator.switch_company_as_operator(self.company_name)
        self.solutions_marked_completed = self.metallic_helper_obj.mark_solutions_complete()

    @test_step
    def compare_solutions(self):
        """Compares the solutions obtained to that of configured solutions for the company"""
        self.admin_console.navigator.navigate_to_metallic()
        if not self.metallic_helper_obj.compare_solutions(self.solutions_marked_completed):
            raise CVTestStepFailure("Solutions configured in the company do not match")

    @test_step
    def verify_solutions_redirect(self):
        """Verifies if solutions got redirected to Metallic"""
        if not self.metallic_helper_obj.verify_solutions_redirect(
            self.solutions_marked_completed,
            hostname=self.inputJSONnode['commcell']['webconsoleHostname'],
            username=self.onprem_user,
            service_commcell_name=self.metallic_helper_obj.metallic_name):
            raise CVTestStepFailure("Solutions redirect validation failed")

    @test_step
    def register_to_metallic(self):
        """Register to metallic services"""
        self.metallic_helper_obj.getting_started.navigate_to_metallic()
        self.metallic_helper_obj.getting_started.link_metallic_account(
            self.company_admin_user, self.strong_password)

    @test_step
    def unregister_to_metallic(self):
        """Unregister to metallic services"""
        self.metallic_helper_obj.getting_started.unlink_metallic_account()

    def run(self):
        try:
            self.init_tc()
            self.cleanup()
            self.pre_requisites_tc()
            self.login_to_metallic_cs(logout_first=True)
            self.mark_solutions_complete_for_company()
            self.login_to_on_prem_cs(logout_first=True)
            self.register_to_metallic()
            self.compare_solutions()
            self.verify_solutions_redirect()
            self.unregister_to_metallic()
            self.cleanup()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
