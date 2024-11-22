""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  Setup function to initialize the variables

    run()           --  Executes test case

    tear down()     --  Clears all the entities created

    Input Example:

    "58663":
    {
        "ClientName":"ClusterCLCS",
        "ClusteName":"Mega1",
        "Nodes"	:["ClusterCL2"],
        "Agents":["File System", "MediaAgent", "MediaAgent Core"],
        "JobResultsDirectory":"G:\\"
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
        self.name = "Update a Cluster Client by Removing a Node"
        self.tcinputs = {
            "ClientName": None,
            "ClusterName": None,
            "Nodes": None,
            "Agents": None,
            "JobResultsDirectory": None
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
    def edit_cluster_nodes(self):
        """ Edits the list of cluster nodes(Adding Node) """
        self.navigator_obj.navigate_to_servers()
        self.helper.open_cluster_client(self.tcinputs['ClusterName'])
        self.helper.switch_to_configuration_tab()
        self.helper.edit_clustergroup(nodes=self.tcinputs['Nodes'], delete=True)

    @test_step
    def validate_cluster_properties(self, properties):
        """
        Verifying Cluster client properties
        """
        agents = self.helper.validate_agents(properties, self.tcinputs['Agents'])
        nodes = self.helper.validate_nodes(properties, self.tcinputs['Nodes'])
        job_dir = self.helper.validate_job_dir(properties, self.tcinputs['JobResultsDirectory'])

        if agents and job_dir and not nodes:
            self.log.info("Successfully verified Agents, Nodes, Job directory")
        else:
            raise CVTestStepFailure("properties not set correctly")

    def run(self):
        """Executes test case"""
        try:
            self.init_tc()
            self.edit_cluster_nodes()
            self.admin_console.logout()
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            properties = self.helper.get_cluster_properties(self.tcinputs['ClusterName'])
            self.validate_cluster_properties(properties)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)