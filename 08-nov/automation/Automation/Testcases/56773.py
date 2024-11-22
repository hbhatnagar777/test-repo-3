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

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.content_analyzer_helper import ContentAnalyzerHelper
from dynamicindex.vm_manager import VmManager
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception, TestStep

_CONFIG_DATA = get_config().DynamicIndex.WindowsHyperV


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
        self.name = "Validation of entity extraction in GDPR project"
        self.tcinputs = {
            "EntityName": None,
            "EntityRegex": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "HostNameToAnalyze": None,
            "IndexServerNodeName": None,
            "TestDBPath": None
        }
        self.ca_helper_obj = None
        self.crawl_job_helper = None
        self.option_selector = None
        self.data_source_name = None
        self.index_server_name = None
        self.ca_cloud_name = None
        self.handler_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.country_name = None
        self.vm_name = None
        self.index_directory = None
        self.index_serer_node_machine = None
        self.vm_manager = None
        self.commcell_password = None
        self.hyperv_name = None
        self.hyperv_username = None
        self.hyperv_password = None
        self.vm_name = None
        self.vm_username = None
        self.vm_password = None
        self.snap_name = None

    def setup(self):
        """Setup function of this test case"""
        self.hyperv_name = _CONFIG_DATA.HyperVName
        self.hyperv_username = _CONFIG_DATA.HyperVUsername
        self.hyperv_password = _CONFIG_DATA.HyperVPassword
        self.vm_name = _CONFIG_DATA.VmName
        self.vm_username = _CONFIG_DATA.VmUsername
        self.vm_password = _CONFIG_DATA.VmPassword
        self.snap_name = _CONFIG_DATA.SnapName
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.ca_helper_obj = ContentAnalyzerHelper(self)
        self.crawl_job_helper = CrawlJobHelper(self)
        self.vm_manager = VmManager(self)
        self.option_selector = OptionsSelector(self.commcell)
        self.index_serer_node_machine = Machine(self.tcinputs['IndexServerNodeName'], self.commcell)
        drive_letter = self.option_selector.get_drive(self.index_serer_node_machine)
        self.index_directory = "%sIndexDirectory_%s" % (drive_letter, self.id)
        self.index_server_name = "IndexServer_%s" % self.id
        self.data_source_name = "FreshCAClient_%s" % self.id
        self.ca_cloud_name = "%s_ContentAnalyzer" % self.vm_name
        self.project_name = "TestProject_%s" % self.id
        self.inventory_name = "TestInventory_%s" % self.id
        self.plan_name = "TestPlan_%s" % self.id
        self.country_name = "India"
        self.vm_manager.check_client_revert_snap(
            hyperv_name=self.hyperv_name,
            hyperv_user_name=self.hyperv_username,
            hyperv_user_password=self.hyperv_password,
            snap_name=self.snap_name,
            vm_name=self.vm_name
        )
        self.log.info("Revert is successful")

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
        self.gdpr_obj.testdata_path = self.tcinputs['FileServerDirectoryPath']
        self.gdpr_obj.entities_list = [self.tcinputs['EntityName']]
        self.gdpr_obj.data_source_name = self.data_source_name
        self.gdpr_obj.create_sqlite_db_connection(
            self.tcinputs['TestDBPath']
        )

    def cleanup(self):
        """cleanup the testcase created entities"""
        self.gdpr_obj.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name,
            pseudo_client_name=self.data_source_name
        )
        self.ca_helper_obj.validate_tppm_setup(index_server=self.index_server_name,
                                               content_analyzer=self.ca_cloud_name,
                                               exists=False)

    @test_step
    def create_inventory(self):
        """creates an inventory"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server_name)

    @test_step
    def create_plan(self):
        """creates a data classification plan"""
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.index_server_name,
            self.ca_cloud_name, [self.tcinputs['EntityName']])
        self.ca_helper_obj.validate_tppm_setup(index_server=self.index_server_name,
                                               content_analyzer=self.ca_cloud_name)

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
            self.data_source_name, self.country_name,
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
            raise Exception("Could not complete Data Source Scan")

    @test_step
    def validate_job_output(self):
        """Validates the extracted sensitive data"""
        self.gdpr_obj.file_server_lookup_obj.select_data_source(
            self.data_source_name)
        self.gdpr_obj.verify_data_source_discover()
        self.gdpr_obj.data_source_discover_obj.select_review()
        self.gdpr_obj.verify_data_source_review()

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("*************** Install content Analyzer client starts ****************")
            self.ca_helper_obj.install_content_analyzer(
                machine_name=self.vm_name,
                user_name=self.vm_username,
                password=self.vm_password,
                platform="Windows")
            self.log.info("Check whether python process is up and running on CA machine : %s", self.vm_name)
            self.log.info("Refreshing client list as we installed new client with CA package")
            self.commcell.clients.refresh()
            client_obj = self.commcell.clients.get(self.vm_name)
            self.ca_helper_obj.check_all_python_process(client_obj=client_obj)
            self.log.info("*************** Install content Analyzer client ends *****************")
            self.log.info("Going to get CA cloud details for : %s", self.ca_cloud_name)
            ca_cloud_obj = self.commcell.content_analyzers.get(self.ca_cloud_name)
            self.log.info("CA cloud URL : %s", ca_cloud_obj.cloud_url)
            if self.commcell.index_servers.has(self.index_server_name):
                self.log.info("Deleting existing index server")
                self.commcell.index_servers.delete(self.index_server_name)
            self.index_serer_node_machine.remove_directory(self.index_directory, 0)
            self.log.info("Creating Index Server: %s" % self.index_server_name)
            self.commcell.index_servers.create(self.index_server_name,
                                               [self.tcinputs['IndexServerNodeName']],
                                               self.index_directory,
                                               ['Data Analytics'])
            if not self.commcell.activate.entity_manager().has_entity(self.tcinputs['EntityName']):
                self.log.info("Creating a custom entity : %s" % self.tcinputs['EntityName'])
                self.commcell.activate.entity_manager().add(self.tcinputs['EntityName'],
                                                  self.tcinputs['EntityRegex'], '', 5)
            self.init_tc()
            self.cleanup()
            self.create_inventory()
            self.create_plan()
            self.create_project_add_file_server()
            self.wait_for_data_source_status_completion()
            self.validate_job_output()
            self.cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.log.info("Going to delete custom entity")
            self.commcell.activate.entity_manager().delete(self.tcinputs['EntityName'])
            self.log.info("Custom entity deleted successfully : %s", self.tcinputs['EntityName'])
            self.log.info("Going to delete CA cloud pseudoclient")
            self.commcell.clients.delete(self.ca_cloud_name)
            self.log.info("CA Cloud pseudoclient deleted successfully : %s", self.ca_cloud_name)
            self.log.info("Going to delete CA client")
            self.commcell.clients.delete(self.vm_name)
            self.log.info("CA client deleted successfully : %s", self.vm_name)
            self.log.info("Going to delete index server")
            self.commcell.index_servers.delete(self.index_server_name)
            self.log.info("Index server deleted successfully : %s", self.index_server_name)
            self.index_serer_node_machine.remove_directory(self.index_directory, 0)
