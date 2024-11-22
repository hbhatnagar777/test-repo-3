from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils.machine import Machine
from Install.install_helper import InstallHelper
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for push installing ipv6 client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.factory = None
        self.browser = None
        self.driver = None
        self.admin_console = None
        self.deployment_helper = None
        self.unix_client = None
        self.config_json = None
        self.install_helper = None

    def setup(self):
        self.config_json = config.get_config()
        self.unix_client = Machine(
            self.config_json.Install.unix_client.machine_host,
            username=self.config_json.Install.unix_client.machine_username,
            password=self.config_json.Install.unix_client.machine_password)
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)

    def run(self):
        self.install_helper = InstallHelper(self.commcell, self.unix_client)
        self.log.info("Push install of client using ipv6")
        job_obj = self.install_helper.install_software(
            client_computers = [self.config_json.Install.unix_client.ip6address],
            install_flags = {"preferredIPFamily": 2})

        if not job_obj.wait_for_completion():
            self.log.info("Install job failed. Please check logs")
            raise Exception("Install job failed")

        self.log.info("Validating install")
        self.deployment_helper.validate_install(
            client_name=self.config_json.Install.unix_client.client_name)
        self.log.info("Install validation completed successfully")





