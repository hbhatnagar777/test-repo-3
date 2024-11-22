"""
Test case to verify Edge app - Verify Client list.
"""
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from Mobile import EdgeManager

from AutomationUtils import config
CONSTANTS = config.get_config()


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Edge App - Verify client list"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.MOBILECONSOLE
        self.show_to_user = False
        self.edge = None
        self.laptop_client = None

        self.log = logger.get_log()

    def setup(self):
        self.edge = EdgeManager.EdgeFactory.create_app_object()
        self.laptop_client = self.tcinputs["client_name"]

    def _initial_configuration(self):
        """
        Login to app, skip auto upload if screen is displayed.
        """
        self.edge.skip_welcome_screen()
        login_window = self.edge.access_login()
        login_window.login(server=self.inputJSONnode['commcell']["webconsoleHostname"])
        if self.edge.is_auto_upload_shown():
            self.edge.enable_auto_upload()  # Auto upload will be turned off.

    def run(self):
        try:
            self._initial_configuration()
            self.log.info("Comparing list of devices from db and app")
            devices_in_app = self.edge.get_devices()
            if self.laptop_client not in devices_in_app:
                raise Exception("Expected [%s] but found [%s]" % (self.laptop_client,
                                                                  devices_in_app))
        except Exception as exp:
            self.log.exception('TC failed with\n ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Closing driver."""
        self.edge.quit_driver()
        self.log.info("Test case status:%s", str(self.status))
