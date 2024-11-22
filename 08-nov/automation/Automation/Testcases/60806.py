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
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    configure_machine_inputs()      --  Configure Inputs for machine according to machines configuration

    generate_sensitive_data()       --  Generate sensitive files with PII entities

    create_inventory()              --  Create an inventory with a nameserver

    create_plan()                   --  Creates a plan

    create_fso_client()             --  Creates FSO client

    create_fso_project()            --  Create FSO data source and start crawl job

    create_index_server()           --  Create an Index Server

    delete_index_server()           --  Delete an Index server and remove index directories

    cleanup()                       --  Runs cleanup

    run()                           --  run function of this test case

    tear_down()                     --  tear down function of this test case
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.Index_Server import IndexServer
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.constants import USA_COUNTRY_NAME, FILE_STORAGE_OPTIMIZATION, CLIENT_NAME, INDEX_STORE, WINDOWS
from dynamicindex.content_analyzer_helper import ContentAnalyzerHelper
from dynamicindex.vm_manager import VmManager


_CONFIG_DATA = get_config().DynamicIndex.WindowsHyperV
NUM_FILE_TO_CREATE = 100


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
                tcinputs        (dict)      --  test case inputs with input name as dict key and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "Verify Fresh installation of Index Store package on Windows machine & verify creation of Index " \
                    "Server with FSO crawl job"
        self.tcinputs = {
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "IndexServerNodeNames": None,
            "FileServerDirectoryPath": None
        }
        self.activateutils = None
        self.vm_names = None
        self.index_server_name = None
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.file_server_display_name = None
        self.index_directory = []
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.gdpr_base = None
        self.fso_helper = None
        self.explict_wait = 120
        self.index_servers_obj = None
        self.ca_helper_obj = None
        self.hyperv_obj = None
        self.vm_helper = None

    def setup(self):
        """Setup function of this test case"""
        try:
            self.activateutils = ActivateUtils()
            self.index_server_name = f'{self.id}_IS'
            self.file_server_display_name = f"{self.id}_FSO_IS_Verify"
            self.inventory_name = f'{self.id}_Inv_Test'
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.vm_helper = VmManager(self)
            self.ca_helper_obj = ContentAnalyzerHelper(self)
            self.vm_names = self.tcinputs['IndexServerNodeNames']
            self.log.info("Reverting Snaps to Fresh VM")
            for vm_name in self.vm_names:
                self.vm_helper.check_client_revert_snap(
                    hyperv_name=_CONFIG_DATA.HyperVName,
                    hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                    hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                    snap_name=_CONFIG_DATA.SnapName,
                    vm_name=vm_name)
            self.log.info("Revert snap is successful")
            client_list = [self.commcell.commserv_name, self.inputJSONnode['commcell']['webconsoleHostname']]
            # Creating Connection between vm(s) & Clients by Populating VM IP on clients
            for vm_name in self.vm_names:
                _CONFIG_DATA_COPY = _CONFIG_DATA._replace(VmName=vm_name)
                self.vm_helper.populate_vm_ips_on_client(config_data=_CONFIG_DATA_COPY, clients=client_list)

        except Exception as except_setup:
            self.log.exception(except_setup)
            self.result_string = str(except_setup)
            self.status = constants.FAILED
            raise Exception("Test case setup(Reverting snap to Plain OS failed). Please check")

    def configure_machine_inputs(self, node_names):
        """
        Configure Inputs for machine according to machines configuration.

        Args:
             node_names (list):  name of the machine/node.
        """
        for node in node_names:
            self.log.info(f'Forming index directory on the node {node}')
            self.index_directory.append(IndexServerHelper.get_new_index_directory(
                                        self.commcell, node, int(time.time())))

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        self.activateutils.sensitive_data_generation(self.tcinputs['FileServerDirectoryPath'],
                                                     number_files=NUM_FILE_TO_CREATE)

    @test_step
    def create_inventory(self):
        """
            Create an inventory with a nameserver
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_inventory_manager()
        self.gdpr_base.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server_name)
        self.gdpr_base.inventory_details_obj.add_asset_name_server(
            self.tcinputs["NameServerAsset"])
        self.admin_console.log.info(f"Sleeping for {self.explict_wait}")
        time.sleep(self.explict_wait)
        if not self.gdpr_base.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete the asset scan.")

    @test_step
    def create_plan(self):
        """
            Creates a plan
        """

        self.navigator.navigate_to_plan()
        self.gdpr_base.plans_obj.create_data_classification_plan(self.plan_name, self.index_server_name,
                                                                 content_search=False, content_analysis=False,
                                                                 target_app='fso', select_all=True)

    @test_step
    def create_fso_client(self):
        """Create FSO client """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(
            self.inventory_name, self.plan_name
        )

    @test_step
    def create_fso_project(self):
        """Create FSO data source and start crawl job"""
        try:
            self.gdpr_base.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], CLIENT_NAME,
                self.file_server_display_name, USA_COUNTRY_NAME,
                directory_path=self.tcinputs['FileServerDirectoryPath'],
                agent_installed=True, live_crawl=True)
            if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise CVTestStepFailure("Could not complete the Datasource scan.")
            self.log.info(f"Sleeping for: {self.explict_wait} seconds")
            time.sleep(self.explict_wait)
            self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['HostNameToAnalyze'])
            total_files_count = int(self.gdpr_base.data_source_discover_obj.get_total_number_after_crawl())
            if total_files_count != NUM_FILE_TO_CREATE:
                raise Exception(f"Total Files Mismatch. Expected Count = {NUM_FILE_TO_CREATE} "
                                f"& Actual Count = {total_files_count}")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    @test_step
    def create_index_server(self):
        """
            create an index server
        """

        self.navigator.navigate_to_index_servers()
        self.log.info('Deleting Index Server if already exists')
        index_server_exist = self.index_servers_obj.is_index_server_exists(self.index_server_name)
        if index_server_exist:
            self.delete_index_server()
        self.index_servers_obj.create_index_server(
            index_server_name=self.index_server_name,
            index_directory=self.index_directory,
            solutions=[FILE_STORAGE_OPTIMIZATION],
            index_server_node_names=self.tcinputs['IndexServerNodeNames'])

    @test_step
    def delete_index_server(self):
        """
            delete an Index server and remove index directories
        """
        self.navigator.navigate_to_index_servers()
        self.index_servers_obj.delete_index_server(index_server_name=self.index_server_name)
        index = 0
        for node in self.tcinputs['IndexServerNodeNames']:
            machine_obj = Machine(node, self.commcell)
            self.log.info(f'Removing Index directory for node {node}')
            machine_obj.remove_directory(self.index_directory[index])
            index += 1

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.fso_helper.fso_cleanup(self.tcinputs['HostNameToAnalyze'], self.file_server_display_name)
        self.gdpr_base.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name)
        self.delete_index_server()

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("*************** Install Index Store Package starts ****************")
            self.ca_helper_obj.install_content_analyzer(
                machine_name=self.vm_names,
                user_name=_CONFIG_DATA.VmUsername,
                password=_CONFIG_DATA.VmPassword,
                platform="Windows",
                pkg=INDEX_STORE)
            self.log.info("Refreshing client list as we installed new client with Index Store package")
            self.commcell.clients.refresh()
            self.log.info("*************** Install Index Store Package ends *****************")
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.index_servers_obj = IndexServer(self.admin_console)
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)
            self.gdpr_base.data_source_name = self.file_server_display_name
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.fso_helper.data_source_name = self.file_server_display_name
            self.configure_machine_inputs(self.tcinputs['IndexServerNodeNames'])
            self.create_index_server()
            self.generate_sensitive_data()
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
            self.create_fso_project()
            self.cleanup()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status != constants.FAILED:
                self.log.info("Going to delete Index Store clients")
                for vm_name in self.vm_names:
                    client_obj = self.commcell.clients.get(vm_name)
                    job_obj = client_obj.retire()
                    job_obj.wait_for_completion()
                self.log.info(f"Index Store clients deleted successfully : {self.vm_names}")
                self.log.info(f"Going to Shutdown the vms : {self.vm_names}")
                for vm_name in self.vm_names:
                    self.vm_helper.vm_shutdown(hyperv_name=_CONFIG_DATA.HyperVName,
                                               hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                                               hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                                               vm_name=vm_name)
                self.log.info("Power off vm successful")
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
