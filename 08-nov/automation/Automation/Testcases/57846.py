# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.constants import FAILED
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception, TestStep, CVTestStepFailure


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
        self.name = "Standalone index server: DC plan creation"
        self.tcinputs = {
            "IndexServerNodeName": None,
            "ContentAnalyserCloudName": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None
        }
        self.index_server_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.plan_name = None
        self.index_directory = None
        self.index_server_node_machine = None
        self.commcell_password = None
        self.data_source_name = None
        self.project_name = None
        self.inventory_name = None

    def setup(self):
        """Setup function of this test case"""
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.data_source_name = "DataSource%s" % self.id
        self.project_name = "TestProject_%s" % self.id
        self.inventory_name = "TestInventory_%s" % self.id
        self.plan_name = "TestPlan_%s" % self.id
        self.index_server_name = "IS_%s" % self.tcinputs['IndexServerNodeName']
        self.index_server_node_machine = Machine(self.tcinputs['IndexServerNodeName'], self.commcell)
        drive_letter = OptionsSelector.get_drive(self.index_server_node_machine)
        self.index_directory = "%sIndexDirectory_%s" % (drive_letter, self.id)

    def init_tc(self):
        """ Initial configuration for the test case. """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                          username=self.commcell.commcell_username,
                                          password=self.commcell_password)
        self.admin_console.login(username=self.commcell.commcell_username,
                                 password=self.commcell_password)
        self.log.info('Logged in through web automation')
        self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)

    def cleanup(self):
        """cleanup the testcase created entities"""
        self.gdpr_obj.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name,
            pseudo_client_name=self.data_source_name
        )
        if self.commcell.index_servers.has(self.index_server_name):
            self.log.info("Deleting Index server")
            self.commcell.index_servers.delete(self.index_server_name)
        self.index_server_node_machine.remove_directory(self.index_directory, 0)

    @test_step
    def create_plan(self):
        """creates a data classification plan"""
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.index_server_name,
            self.tcinputs['ContentAnalyserCloudName'], ["Email"],
            create_index_server=True, node_name=self.tcinputs['IndexServerNodeName'],
            index_directory=self.index_directory)
        self.log.info("Checking if index server is created or not")
        self.commcell.index_servers.refresh()
        if not self.commcell.index_servers.has(self.index_server_name):
            self.log.error("Index server not created")
            raise CVTestStepFailure("Index server not created")
        self.log.info("Index server is created: %s" % self.index_server_name)
        self.log.info("Checking if DC plan is created or not")
        self.commcell.plans.refresh()
        if not self.commcell.plans.has_plan(self.plan_name):
            self.log.error("DC not created")
            raise CVTestStepFailure("DC not created")
        self.log.info("DC is created: %s" % self.plan_name)

    @test_step
    def create_inventory(self):
        """creates an inventory"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server_name)

    @test_step
    def create_project_add_file_server(self):
        """Creates a project and adds file server to it"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source()
        self.gdpr_obj.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], 'Client name',
            self.data_source_name, 'India',
            self.tcinputs['FileServerDirectoryPath'],
            username=self.tcinputs['FileServerUserName'],
            password=self.tcinputs['FileServerPassword'],
            agent_installed=True,
            live_crawl=True, inventory_name=self.inventory_name)

    @test_step
    def wait_for_data_source_status_completion(self):
        """Waits for data source status completion"""
        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.data_source_name):
            raise CVTestStepFailure("Could not complete Data Source Scan")

    @test_step
    def validate_job_output(self):
        """Verifies the crawled documents count"""
        crawl_job_helper = CrawlJobHelper(self)
        total_count = crawl_job_helper.get_docs_count(folder_path=self.tcinputs['FileServerDirectoryPath'],
                                                      machine_name=self.tcinputs['HostNameToAnalyze'],
                                                      include_folders=False)
        self.log.info("Expected crawled docs count: %s" % total_count)
        self.gdpr_obj.file_server_lookup_obj.select_data_source(self.data_source_name)
        crawled_count = int(self.gdpr_obj.data_source_discover_obj.get_total_files())
        self.log.info("Actual crawled docs count: %s" % crawled_count)
        if crawled_count != total_count:
            self.log.error("Actual crawled count not same as the expected count")
            raise CVTestStepFailure("Actual crawled count not same as the expected count")
        self.log.info("All docs crawled successfully")

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()
            self.cleanup()
            self.create_plan()
            self.create_inventory()
            self.create_project_add_file_server()
            self.wait_for_data_source_status_completion()
            self.validate_job_output()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != FAILED:
            self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
