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
    __init__()                                  --  initialize TestCase class
    setup()                                     --  setup function of this test case
    init_tc()                                   --  initializes browser and testcase related objects
    cleanup()                                   --  perform Cleanup Operation for older test case runs
    create_index_server()                       --  Creates an Index Server.
    create_inventory()                          --  Creates inventory with give name server
    create_plan()                               --  Creates a DC Plan for.
    add_sdg_proj()                              --  Creates SDG project and add a datasource to it
    verify_crawl_job()                          --  Verifies the crawl job by matching the number of files.
    config_and_run_backup()                     --  Configures and Runs the Index Server backup
    verify_backup_and_validate_data_with_src()  --  Does browse and makes sure all items got backed up and validates
                                                    size between browse core data and source index server core data
                                                    matches or not
    delete_index_server()                       --  perform Cleanup Operation for the test case
                                                    and deletes the Index Server.
    run()                                       --  run function of this test case
"""

import time
import calendar

from cvpysdk.datacube.constants import IndexServerConstants as index_constants
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils import constants
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole

WAIT_TIME = 2 * 60


class TestCase(CVTestCase):
    """Class for verifying Linux Index Server backup of single node"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "Verifying Index Server(Linux) backup of a single node"
        self.show_to_user = False
        self.tcinputs = {
            "Index_Server_Node": None,
            "Storage_Policy_Name": None,
            "HostNameToAnalyze": None,
            "ContentAnalyzer": None,
            "FileServerDirectoryPath": None,
            "TestDataSQLiteDBPath": None
        }
        # Test Case constants
        self.index_server_name = None
        self.inventory_name = None
        self.plan_name = None
        self.entities_list = None
        self.project_name = None
        self.file_server_display_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.index_directory = None
        self.machine_obj = None
        self.options_obj = None
        self.backup_job_id = None
        self.index_server_helper = None
        self.timestamp = None

    def setup(self):
        """Setup function of this test case"""
        self.timestamp = calendar.timegm(time.gmtime())
        self.index_server_name = f'{self.id}_index_server'
        self.inventory_name = f'{self.id}_inventory'
        self.plan_name = f'{self.id}_plan'
        self.entities_list = [constants.ENTITY_EMAIL, constants.ENTITY_IP]
        self.project_name = f'{self.id}_project'
        self.file_server_display_name = f'{self.id}_file_server'

    def init_tc(self):
        """ Initial configuration for the test case. """
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login()
        self.log.info("Login completed successfully.")
        self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
        self.gdpr_obj.create_sqlite_db_connection(
            self.tcinputs['TestDataSQLiteDBPath']
        )
        self.gdpr_obj.testdata_path = self.tcinputs['FileServerDirectoryPath']
        self.gdpr_obj.entities_list = self.entities_list
        self.gdpr_obj.data_source_name = self.file_server_display_name
        self.machine_obj = Machine(self.tcinputs['Index_Server_Node'], self.commcell)
        self.options_obj = OptionsSelector(self.commcell)
        self.index_directory = f"{self.options_obj.get_drive(self.machine_obj)}{self.id}{self.timestamp}"

    @test_step
    def cleanup(self):
        """Perform Cleanup Operation for older test case runs"""
        self.gdpr_obj.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name,
            pseudo_client_name=self.file_server_display_name)

        if self.commcell.index_servers.has(self.index_server_name):
            self.commcell.index_servers.delete(self.index_server_name)
        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME/2)

    @test_step
    def create_index_server(self):
        """Creates an Index Server."""
        self.machine_obj.create_directory(self.index_directory, force_create=True)

        self.commcell.index_servers.create(index_server_name=self.index_server_name,
                                           index_server_node_names=[self.tcinputs['Index_Server_Node']],
                                           index_directory=self.index_directory,
                                           index_server_roles=[index_constants.ROLE_DATA_ANALYTICS])

        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)

    @test_step
    def create_inventory(self):
        """Creates an Inventory."""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server_name)

    @test_step
    def create_plan(self):
        """Creates a DC Plan"""
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.index_server_name,
            self.tcinputs['ContentAnalyzer'], self.entities_list)

    @test_step
    def add_sdg_proj(self):
        """Creates a SDG Project and adds a File Server to it."""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)

        self.gdpr_obj.file_server_lookup_obj.select_add_data_source()
        self.gdpr_obj.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], constants.CLIENT_NAME,
            self.file_server_display_name, constants.USA_COUNTRY_NAME,
            self.tcinputs['FileServerDirectoryPath'],
            agent_installed=True, live_crawl=True,
            inventory_name = self.inventory_name)

        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete Data Source Scan")
        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)

    @test_step
    def verify_crawl_job(self):
        """ Verifies the crawl Job"""
        self.gdpr_obj.file_server_lookup_obj.select_data_source(
            self.file_server_display_name)
        self.gdpr_obj.verify_data_source_discover()

    @test_step
    def config_and_run_backup(self):
        """Configures and Runs the backup"""
        self.index_server_helper = IndexServerHelper(self.commcell, self.index_server_name)
        self.index_server_helper.init_subclient()
        self.log.info("Make sure default subclient has all roles in backup content")
        self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['Storage_Policy_Name'],
                                                                role_content=[index_constants.ROLE_DATA_ANALYTICS])
        self.backup_job_id = self.index_server_helper.run_full_backup()

    @test_step
    def verify_backup_and_validate_data_with_src(self):
        """Does browse and makes sure all items got backed up and validates
         size between browse core data and source index server core data matches or not"""

        self.log.info("Going to cross verify data size vs browse size for DA role")
        is_success = self.index_server_helper.validate_backup_file_sizes_with_src_unix(
            role_name=index_constants.ROLE_DATA_ANALYTICS, job_id=int(self.backup_job_id))
        if not is_success:
            raise Exception("Source Core size and browse core size mismatched for DA role. Please check logs")

    @test_step
    def delete_index_server(self):
        """Perform Cleanup Operation for the test case and deletes the Index Server"""

        self.cleanup()
        self.log.info(f"Removing Index Directory {self.index_directory}")
        self.machine_obj.remove_directory(self.index_directory)
        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)

    def run(self):
        """Run function of this test case"""

        try:
            self.init_tc()
            self.cleanup()
            self.create_index_server()
            self.create_inventory()
            self.create_plan()
            self.add_sdg_proj()
            self.verify_crawl_job()
            self.config_and_run_backup()
            self.verify_backup_and_validate_data_with_src()
            self.delete_index_server()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
