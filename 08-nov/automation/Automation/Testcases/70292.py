from AutomationUtils import logger
from AutomationUtils.config import get_config

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.GlobalConfigManager.Helper.gcm_tag_helper import GCMTagsHelper
from Web.AdminConsole.Helper.adminconsoleconstants import ConsoleTypes
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[GCM][UI]: Create Tags from cloud console and validate propagation to service commcells"
        self.browser = None
        self.admin_console = None
        self.config = None
        self.logger = logger.get_log()

    def setup(self):
        """Setup function of this test case"""
        self.config = get_config()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname, console_type=ConsoleTypes.CLOUD_CONSOLE.value)
        self.admin_console.login(self.config.GCM.cloud_user,
                                 self.config.GCM.cloud_user_password,
                                 saml=True)

    def run(self):
        """Run function of this test case"""
        try:
            gcm_helper_obj = GCMTagsHelper(self.admin_console)
            service_commcell_info = [i._asdict() for i in self.config.GCM.service_commcells]
            gcm_helper_obj.validate_create_propagation(service_commcell_info)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
