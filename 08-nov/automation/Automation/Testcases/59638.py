"""Test Case for SharePoint v2 Client creation with Multiple Node and Express configuration

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages import constants as o365_constants
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception

class TestCase(CVTestCase):

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = ("SharePoint v2 Pseudo Client : Client creation with Multiple Access Node and Express configuration" 
                    "and Modification of Configuration")
        self.browser = None
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
            self.tcinputs['MaxStreams'] = o365_constants.SharePointOnline.MAX_STREAMS_COUNT.value
            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = Office365Apps.AppType.share_point_online
            self.sharepoint = Office365Apps(tcinputs=self.tcinputs,
                                            admin_console=self.admin_console,
                                            is_react=True)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        try:
            self.sharepoint.create_office365_app()
            self.sharepoint.verify_app_config_values()
            self.sharepoint.modify_app_config_values(new_server_plan=self.tcinputs['NewServerPlan'],
                                                     new_stream_count=self.tcinputs['NewStreamCount'],
                                                     new_shared_path=self.tcinputs['NewUNCPath'],
                                                     new_user_account=self.tcinputs['NewUserAccount'],
                                                     new_password=self.tcinputs['NewUserAccPwd'])
            self.sharepoint.verify_app_config_values()
            self.sharepoint.is_app_associated_with_plan()
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