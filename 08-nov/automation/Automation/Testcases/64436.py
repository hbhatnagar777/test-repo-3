from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Metallic.MirageHelper import MirageCCHelper, MirageApiHelper, MirageTrialHelper
from random import randint, sample
from Server.Security.userhelper import UserHelper
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
        self.name = "[Mirage 1.5]: Cloud Switcher validation for MSP and reseller"
        self.browser = None
        self.admin_console = None

    def setup(self):
        """Setup function of this test case"""
        self.username = self.inputJSONnode['commcell']['commcellUsername']
        self.password = self.inputJSONnode['commcell']['commcellPassword']

        self.user_helper = UserHelper(self.commcell)
        self.mirage_api_helper = MirageApiHelper(self.commcell)

        self.log.info('Fetching customer user groups details...')
        self.available_customer_user_groups = self.mirage_api_helper.get_customer_usergroups(self.csdb)
        self.commcell_customer_groups = [(name, id, company_id) for name, id, company_id in self.available_customer_user_groups if company_id == 0]

        self.log.info('Picking customer user groups for testing the cloud company switcher...')
        customer_user_groups_count = 3
        self.msp_user_groups = sample(self.available_customer_user_groups, customer_user_groups_count)
        self.reseller_user_groups = sample(self.commcell_customer_groups, customer_user_groups_count)
        self.log.info(f'MSP user groups: {self.msp_user_groups}')
        self.log.info(f'Reseller user groups: {self.reseller_user_groups}')

        self.log.info('Creating reseller user and adding to the reseller user groups...')
        self.reseller_user_name = f'reseller_user_{randint(0, 100000)}'
        self.commcell.users.add(self.reseller_user_name, f'{self.reseller_user_name}@reseller.test', password=self.password,
                                local_usergroups=[name for name, _, _ in self.reseller_user_groups])
        
        self.log.info('Setup completed.')
        
    def run(self):
        """Run function of this test case"""
        try:
            # validate switcher functionality as MSP
            self.mirage_api_helper.retry_function_execution(func=self.validate_cloud_switcher, 
                                                              user_name=self.username, password=self.password, 
                                                              customer_usergroups=self.msp_user_groups)

            # validate switcher functionality as Reseller
            self.mirage_api_helper.retry_function_execution(func=self.validate_cloud_switcher, 
                                                              user_name=self.reseller_user_name, password=self.password, 
                                                              customer_usergroups=self.reseller_user_groups)
            
            self.status = constants.PASSED
            self.result_string = ''
            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.user_helper.cleanup_users(marker='reseller_user_')

    def __open_browser(self):
        """Opens the browser and initializes the admin console object"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, console_type=ConsoleTypes.CLOUD_CONSOLE.value)

    @test_step
    def validate_cloud_switcher(self, user_name, password, customer_usergroups):
        """Validates the cloud company switcher functionality"""
        self.log.info(f'Validating cloud company switcher functionality for user: {user_name}...')
        self.__open_browser()
        MirageTrialHelper(self.admin_console, self.commcell).validate_cloud_company_switcher(user_name, password, customer_usergroups)