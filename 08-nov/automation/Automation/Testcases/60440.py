# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                                   --  initialize TestCase class

    setup()                                      --  Initial configuration for the testcase

    configure_machine_inputs()                   --  Configure Inputs for machine according to machines configuration

    create_inventory()                           --  Create an inventory with a nameserver

    create_sdg_plan()                            --  Creates a SDG plan

    create_fso_plan()                            --  Creates a FSO plan

    create_fso_client()                          --  Creates FSO client

    create_fso_project()                         --  Create FSO data source and start crawl job

    create_sdg_project()                         --  Create SDG project and add data source and start crawl job

    create_index_server()                        --  Create an Index Server

    delete_index_server()                        --  Delete an Index Server

    cleanup()                                    --  Runs cleanup

    run()                                        --  run function of this test case

    tear_down()                                  --  Tear Down tasks
"""
import time
from AutomationUtils.cvtestcase import CVTestCase
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
from dynamicindex.utils.constants import USA_COUNTRY_NAME, CLIENT_NAME
from dynamicindex.utils.constants import FILE_STORAGE_OPTIMIZATION, SENSITIVE_DATA_GOVERNANCE


class TestCase(CVTestCase):
    """Class for executing this Testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Create index Server with multiple solutions and verify it using FSO"
        self.tcinputs = {
            "ContentAnalyzer": None,
            "HostNameToAnalyze": None,
            "IndexServerNodeNames": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None
        }
        # Testcase Constants
        self.activateutils = None
        self.index_server_name = None
        self.inventory_name = None
        self.fso_plan_name = None
        self.sdg_plan_name = None
        self.sdg_project_name = None
        self.sdg_file_server_display_name = None
        self.fso_file_server_display_name = None
        self.index_directory = []
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.gdpr_base = None
        self.fso_helper = None
        self.explict_wait = 120
        self.index_servers_obj = None
        self.num_file_to_create = 100

    def setup(self):
        """ Initial configuration for the test case"""
        try:
            self.activateutils = ActivateUtils()
            self.index_server_name = f'{self.id}_IS'
            self.fso_file_server_display_name = f"{self.id}_FSO_IS_Verify"
            self.inventory_name = f'{self.id}_Inv'
            self.fso_plan_name = f'{self.id}_fso_plan'
            self.sdg_plan_name = f'{self.id}_sdg_plan'
            self.sdg_project_name = f'{self.id}_sdg_project'
            self.configure_machine_inputs(self.tcinputs['IndexServerNodeNames'])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.index_servers_obj = IndexServer(self.admin_console)
            self.navigator.navigate_to_governance_apps()
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)
            self.gdpr_base.data_source_name = self.fso_file_server_display_name
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.fso_helper.data_source_name = self.fso_file_server_display_name

        except Exception:
            raise Exception("init tc failed")

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

    @test_step
    def create_inventory(self):
        """
            Create an inventory with a nameserver
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_inventory_manager()
        self.gdpr_base.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server_name)

    @test_step
    def create_sdg_plan(self):
        """
            Creates a plan
        """

        self.navigator.navigate_to_plan()
        self.gdpr_base.plans_obj.create_data_classification_plan(
            self.sdg_plan_name, self.index_server_name, self.tcinputs['ContentAnalyzer'], None, select_all=True)

    @test_step
    def create_fso_plan(self):
        """
            Creates a plan
        """

        self.navigator.navigate_to_plan()
        self.gdpr_base.plans_obj.create_data_classification_plan(self.fso_plan_name, self.index_server_name,
                                                                 content_search=False, content_analysis=False,
                                                                 target_app='fso', select_all=True)

    @test_step
    def create_fso_client(self):
        """Create FSO client """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(
            self.inventory_name, self.fso_plan_name
        )

    @test_step
    def create_fso_project(self):
        """Create FSO data source and start crawl job"""
        try:
            self.gdpr_base.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], CLIENT_NAME,
                self.fso_file_server_display_name, USA_COUNTRY_NAME,
                directory_path=self.tcinputs['FileServerDirectoryPath'],
                agent_installed=True, live_crawl=True,
                inventory_name=self.inventory_name)
            if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.fso_file_server_display_name):
                raise CVTestStepFailure("Could not complete the Datasource scan.")
            self.log.info(f"Sleeping for: {self.explict_wait} seconds")
            time.sleep(self.explict_wait)
            self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['HostNameToAnalyze'])
            total_files_count = int(self.gdpr_base.data_source_discover_obj.get_total_number_after_crawl())
            if total_files_count != self.num_file_to_create:
                raise Exception(f"Total Files Mismatch. Expected Count = {self.num_file_to_create} "
                                f"& Actual Count = {total_files_count}")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    @test_step
    def create_sdg_project(self):
        """
            Creates a project and runs analysis
        """
        self.sdg_file_server_display_name = '{}_SDG_IS_Verify'.format(self.id)
        country_name = USA_COUNTRY_NAME
        self.gdpr_base.testdata_path = self.tcinputs['FileServerDirectoryPath']
        self.gdpr_base.data_source_name = self.sdg_file_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.add_project(
            self.sdg_project_name, self.sdg_plan_name)
        self.gdpr_base.file_server_lookup_obj.select_add_data_source()
        self.gdpr_base.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], CLIENT_NAME,
            self.sdg_file_server_display_name, country_name,
            self.tcinputs['FileServerDirectoryPath'],
            username=self.tcinputs['FileServerUserName'],
            password=self.tcinputs['FileServerPassword'], agent_installed=True, live_crawl=True,
            inventory_name=self.inventory_name)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.sdg_file_server_display_name):
            raise CVTestStepFailure("Could not complete the Datasource scan.")
        self.log.info(f"Sleeping for: {self.explict_wait} seconds")
        time.sleep(self.explict_wait)
        total_files_count = int(self.gdpr_base.data_source_discover_obj.get_total_number_after_crawl())
        if total_files_count != self.num_file_to_create:
            raise Exception(f"Total Files Mismatch. Expected Count = {self.num_file_to_create} "
                            f"& Actual Count = {total_files_count}")

    @test_step
    def create_index_server(self):
        """
            create an index server
        """

        self.navigator.navigate_to_index_servers()
        self.index_servers_obj.create_index_server(
            index_server_name=self.index_server_name,
            index_directory=self.index_directory,
            solutions=[FILE_STORAGE_OPTIMIZATION, SENSITIVE_DATA_GOVERNANCE],
            index_server_node_names=self.tcinputs['IndexServerNodeNames'])

    @test_step
    def delete_index_server(self):
        """
            delete an Index server and remove index directories
        """
        self.navigator.navigate_to_index_servers()
        index_server_exist = self.index_servers_obj.is_index_server_exists(self.index_server_name)
        if index_server_exist:
            self.index_servers_obj.delete_index_server(self.index_server_name)
            index = 0
            for node in self.tcinputs['IndexServerNodeNames']:
                self.machine_obj = Machine(node, self.commcell)
                self.log.info(f'Removing Index directory for node {node}')
                self.machine_obj.remove_directory(self.index_directory[index])
                index += 1

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.fso_helper.fso_cleanup(self.tcinputs['HostNameToAnalyze'], self.fso_file_server_display_name)
        self.gdpr_base.cleanup(plan_name=self.fso_plan_name)
        self.gdpr_base.cleanup(
            self.sdg_project_name,
            self.inventory_name,
            self.sdg_plan_name, pseudo_client_name=self.sdg_file_server_display_name)
        self.delete_index_server()

    def run(self):
        try:
            self.cleanup()
            self.create_index_server()
            self.create_inventory()
            self.create_fso_plan()
            self.create_fso_client()
            self.create_fso_project()
            self.create_sdg_plan()
            self.create_sdg_project()
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
