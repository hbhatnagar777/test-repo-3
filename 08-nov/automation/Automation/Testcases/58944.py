"""
    Test Case for getting performance load time of
    navigation elements in the admin console

    TestCase is the only class defined in this file.

    TestCase: Class for executing this test case

    TestCase:
        __init__()      --  initialize TestCase class

        run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.performance_helper import PerformanceHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser


class TestCase(CVTestCase):
    """
        Test Case class for obtaining performance output
    """

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Test Case for admin console load time performance"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.utils = TestCaseUtils(self)
        self.comp_obj = None
        self.tcinputs = {
            'email_receiver': "",
            "controllerHostName": "",
            "controllerUserName": "",
            "controllerPassword": "",
            "rmUsername": "",
            "rmPassword": ""
        }
        self.per_helper_obj = None
        self.email_receiver = None
        self.mailer = None
        self.admin_console = None
        self.browser = None
        self.driver = None

    def run(self):
        """
            run function of the test case
        """
        rm_host_name = self.inputJSONnode['commcell']['webconsoleHostname']
        commcell_username = self.inputJSONnode['commcell']['commcellUsername']
        email_receiver = self.tcinputs["email_receiver"]

        rm_uname = self.tcinputs['rmUsername']
        rm_pwd = self.tcinputs['rmPassword']

        try:

            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, rm_host_name)

            self.admin_console.login(commcell_username, self.inputJSONnode['commcell']['commcellPassword'])
            self.driver = self.browser.driver

            per_helper_obj = PerformanceHelper(self.commcell, self.admin_console, self.driver)
            per_helper_obj.get_ac_performance(rm_uname, rm_pwd, email_receiver)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
