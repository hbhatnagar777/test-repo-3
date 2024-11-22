"""
Test case to verify Edge app - Login/Logout.
"""
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from Mobile import EdgeManager


class TestCase(CVTestCase):
    """
    Initiates test case.
    """
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Edge app - Login/Logout"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.MOBILECONSOLE
        self.show_to_user = False
        self.log = logger.get_log()

    def setup(self):
        self.edge = EdgeManager.EdgeFactory.create_app_object(no_reset=False, full_reset=True)

    def initial_configuration(self):
        """
        Skips welcome screen, and gets login object.
        """
        self.edge.skip_welcome_screen()
        self.login_window = self.edge.access_login()

    def verify_login(self):
        """
        Verify login.
        """
        self.log.info("Verifying login")
        self.login_window.login(server=self.inputJSONnode['commcell']["webconsoleHostname"])
        if self.edge.is_auto_upload_shown():
            self.edge.enable_auto_upload()  # Auto upload will be turned off.
        self.log.info("login is verified")

    def verify_logout(self):
        """
        Verify Logout.
        """
        self.log.info("Verifying logout")
        self.edge.logout()
        if self.login_window.is_logged_in() is True:
            raise Exception("Failed to logout!")
        self.log.info("Logout is verified")

    def run(self):
        try:
            self.initial_configuration()
            self.verify_login()
            self.verify_logout()
            self.status = constants.PASSED
        except Exception as exp:
            self.log.exception('Test Case failed with\n ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Closing driver."""
        self.edge.quit_driver()
        self.log.info("Test case status:%s", str(self.status))