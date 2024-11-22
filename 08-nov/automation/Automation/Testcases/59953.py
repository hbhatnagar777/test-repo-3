"""Test Case for SharePoint v2 Pseudo Client  : Switch from basic to modern auth & vice versa validation and
configuration page general and connection settings GUI options validation

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Office365Pages.sharepoint import SharePoint
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "SharePoint v2 Pseudo Client  : Switch from basic to modern auth & vice versa validation and " \
                    "configuration page general and connection settings GUI options validation"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.sharepoint = None
        self.client_name = None

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.log.info("Creating a login object")
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = SharePoint.AppType.share_point_online
            self.sharepoint = SharePoint(self.tcinputs, self.admin_console, is_react=True)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def _verify_modern_auth_toggle(self):
        """Toggles modern auth toggle and verifies by creating an azure app"""
        self.sharepoint.disable_modern_auth_toggle(add_app_or_account=False)
        self.sharepoint.enable_modern_auth_toggle()

    @test_step
    def _verify_azure_apps_options(self):
        """Verifies azure apps options: Add, Edit, Authorize, Create principal and Delete"""
        self.sharepoint.add_azure_app_and_verify(express_config=False)
        self.sharepoint.edit_azure_app_and_verify()
        self.sharepoint.authorize_azure_app_and_verify()
        self.sharepoint.create_app_principal_for_sp_app_and_verify()
        self.sharepoint.delete_azure_app_and_verify()
        self.sharepoint.verify_azure_apps_connection()
        self.sharepoint.delete_azure_app_and_verify(delete_all=True)

    @test_step
    def _verify_global_admin_options(self):
        """Verifies global admin options: Edit, Delete and Add"""
        self.sharepoint.edit_global_admin()
        self.sharepoint.delete_global_admin()
        self.sharepoint.add_global_admin()

    @test_step
    def _verify_disable_modern_auth_and_add_service_account(self):
        """Verifies disabling modern auth and adding service account"""
        self.sharepoint.disable_modern_auth_toggle()
        self.sharepoint.delete_global_admin()

    @test_step
    def _verify_service_account_options(self):
        """Verifies service account options: Add, Edit and Delete"""
        self.sharepoint.add_service_account()
        self.sharepoint.add_service_account(express_config=False)
        self.sharepoint.edit_service_account()
        self.sharepoint.delete_service_account_and_verify()
        self.sharepoint.delete_service_account_and_verify(delete_all=True)

    def run(self):
        try:
            self.sharepoint.create_office365_app()
            self.navigator.navigate_to_office365()
            self.sharepoint.access_office365_app(self.tcinputs['Name'])
            self._verify_modern_auth_toggle()
            self._verify_azure_apps_options()
            self._verify_global_admin_options()
            self._verify_disable_modern_auth_and_add_service_account()
            self._verify_service_account_options()

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_office365()
                self.sharepoint.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
