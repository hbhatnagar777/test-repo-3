from AutomationUtils.config import get_config

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.Helper.UserHelper import UserMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "[CC Acceptance] User: CRUD operations on user"
        self.browser = None
        self.admin_console = None
        self.config = None

    def setup(self):
        """Setup function of this test case"""
        self.config = get_config()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.user_helper = UserMain(self.admin_console, self.commcell)
        self.user_page = Users(self.admin_console)


    def run(self):
        """Run function of this test case"""
        try:
            self.user_helper.password = self.config.MSPCompany.tenant_password
            self.user_helper.add_new_local_user()

            self.user_helper.validate_company_filter()

            self.user_helper.delete_user()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            self.commcell.users.delete_user(self.user_helper.user_name)
        except:
            self.log.info("User already deleted; not deleting in tear down")
        self.browser.close()
