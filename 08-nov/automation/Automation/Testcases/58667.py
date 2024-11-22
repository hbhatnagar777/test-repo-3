""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  Setup function to initialize the variables

    run()           --  Executes test case

    tear down()     --  Clears all the entities created

    Input Example:

    "58667":
    {
        "ClientName":"ClusterCLCS",
        "ClusterName":"Mega1"
    }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.ClusterClients_helper import ClusterMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance of cluster client test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.utils = TestCaseUtils(self)
        self.name = "Deconfigure Cluster Client"
        self.tcinputs = {
            "ClientName": None,
            "ClusterName": None
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
    def get_configured_nodes(self):
        """ Gets all the configured nodes of a cluster client """
        self.cluster_groups = self.helper.get_cluster_properties(self.tcinputs['ClusterName'])
        return self.cluster_groups['Nodes'].split(' , ')

    @test_step
    def deconfigure_cluster_nodes(self, nodes):
        """ Deconfigure cluster nodes """
        self.helper.deconfigure_cluster(nodes)

    @test_step
    def verify_if_deconfigured(self):
        """ Verifying Cluster client properties """
        cluster_groups = self.helper.get_cluster_properties(self.tcinputs['ClusterName'])
        cluster_nodes = cluster_groups['Nodes'].split(' , ')
        status_text = [self.admin_console.props['label.noNodes']]
        if cluster_nodes == status_text:
            self.log.info('Successfully deconfigured cluster client')
        else:
            raise CVTestStepFailure("Failed to deconfigure cluster client Nodes")

    def run(self):
        """Executes test case"""
        try:
            self.init_tc()
            nodes = self.get_configured_nodes()
            self.deconfigure_cluster_nodes(nodes)
            self.admin_console.logout()
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.verify_if_deconfigured()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)