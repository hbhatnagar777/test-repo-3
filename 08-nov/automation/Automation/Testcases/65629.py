from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from AutomationUtils import constants
from Metallic.MirageHelper import MirageApiHelper
from Web.AdminConsole.Helper.adminconsoleconstants import ConsoleTypes

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[GCM]: Basic Active Management Flow - Linux Service CommCell - Hybrid Customer"
        self.tcinputs = {
            "CommcellName": ""
        }
        self.browser = None
        self.admin_console = None

    def setup(self):
        """Setup function of this test case"""
        self.mirage_api_helper = MirageApiHelper(self.commcell)
        
    def run(self):
        """Run function of this test case"""
        try:
            
            self.mirage_api_helper.retry_function_execution(func=self.validate_active_mgmt_flow, max_retries=1)

            self.status = constants.PASSED
            self.result_string = f"Successfully validated active management on commcell: {self.tcinputs.get('CommcellName')}"
            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def __open_browser(self):
        """Opens the browser and initializes the admin console object"""
        # close the browser if already open
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, console_type=ConsoleTypes.CLOUD_CONSOLE.value)

    @test_step
    def validate_active_mgmt_flow(self):
        """Validates the AM flow for hybrid user on linux commcell"""
        self.__open_browser()
        self.mirage_api_helper.perform_active_management_and_do_validation(service_commcell_name=self.tcinputs['CommcellName'],
                                                            admin_console=self.admin_console,
                                                            windows_cs=False,
                                                            negative_validation=False,
                                                            hybrid=True
                                                            )
