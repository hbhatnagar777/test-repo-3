from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Metallic.MirageHelper import MirageTrialHelper, MirageApiHelper
from Web.AdminConsole.Helper.adminconsoleconstants import ConsoleTypes

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes the test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Mirage]: Validate mirage pages and actions pre trial subscription"
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
            
            MirageApiHelper(commcell=self.commcell).retry_function_execution(func=self.perform_pretrial_validations)

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
    def perform_pretrial_validations(self):
        """Performs the pretrial validations"""
        self.log.info('Performing pretrial validations...')
        self.__open_browser()
        MirageTrialHelper(self.admin_console, self.commcell, self.tcinputs['CommcellName']).perform_mirage_trial(do_only_pretrial_validations=True)
        self.log.info('Pretrial validations completed.')