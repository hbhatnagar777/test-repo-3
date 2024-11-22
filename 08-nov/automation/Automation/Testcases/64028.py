from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Metallic.MirageHelper import MirageTrialHelper, MirageApiHelper
from Web.AdminConsole.Helper.adminconsoleconstants import ConsoleTypes

class TestCase(CVTestCase):
    """Class for executing the hybrid user flow test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes the test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Mirage]: Hybrid user flow"
        self.tcinputs = {
            "CommcellName": "",
        }
        self.admin_console = None
        self.browser = None

    def setup(self):
        """Performs setup before running the test case"""
        pass

    def run(self):
        """Runs the main steps of the test case"""
        try:
            
            MirageApiHelper(commcell=self.commcell).retry_function_execution(func=self.validate_hybrid_user_flow)

            self.log.info('Test case validation completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Performs the tear down steps after running the test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def __open_browser(self):
        """Opens the browser and initializes the admin console object"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, console_type=ConsoleTypes.CLOUD_CONSOLE.value)

    @test_step
    def validate_hybrid_user_flow(self):
        """Validates the software only user flow"""
        self.__open_browser()
        MirageTrialHelper(self.admin_console, self.commcell, self.tcinputs['CommcellName']).perform_mirage_trial(hybrid_account=True)