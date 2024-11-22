
""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  Setup function to initialize the variables

    run()           --  Executes test case

    tear down()     --  Clears all the entities created

    Input Example:

    "58666":
    {
        "ClientName":"ClusterCLCS",
        "ClusterName":"Mega1",
        "Username":"domain\\username",
        "Password":"password",
        "Node":"#####"
    }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.ClusterClients_helper import ClusterMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

class TestCase(CVTestCase):
    """Class for executing Basic acceptance of cluster client test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.utils = TestCaseUtils(self)
        self.name = "Hard Delete GxClusterPlugin Service and recreate Client"
        self.tcinputs = {
            "ClientName": None,
            "ClusterName": None,
            "Username": None,
            "Password": None,
            "Node": None
        }

    @test_step
    def init_tc(self):
        """ function to initialize the variables """
        try:
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()

            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.navigator_obj = self.admin_console.navigator
            self.helper = ClusterMain(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def login_to_node(self):
        """ Login to one of the cluster nodes and hard delete plugin """
        status = self.helper.hard_delete_GxClusPlugin(self.tcinputs['Node'], self.tcinputs['Username'], self.tcinputs['Password'])
        self.log.info(status)

    @test_step
    def edit_cluster_groups(self):
        """ Enable toggle Force sync configuration on remote nodes """
        self.navigator_obj.navigate_to_servers()
        self.helper.open_cluster_client(self.tcinputs['ClusterName'])
        self.helper.switch_to_configuration_tab()
        self.helper.edit_clustergroup(force_sync=True)

    @test_step
    def verify_plugin(self):
        """ Verify if plugin is reconfigured or not """
        status = self.helper.verify_plugin(self.tcinputs['Node'], self.tcinputs['Username'], self.tcinputs['Password'])
        self.log.info(status)

    def run(self):
        """Executes test case"""
        try:
            self.init_tc()
            self.login_to_node()
            self.edit_cluster_groups()
            self.verify_plugin()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)