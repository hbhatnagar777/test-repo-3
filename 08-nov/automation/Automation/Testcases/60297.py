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
    __init__()                          --  initialize TestCase class
    setup()                             --  setup function of this test case
    init_tc()                           --  initializes browser and testcase related objects
    pre_cleanup()                       --  perform Cleanup Operations for older test case runs
    create_index_server()               --  Creates an Index Server.
    create_inventory()                  --  Creates an inventory
    create_plan()                       --  Creates a DC Plan for.
    add_sdg_proj()                      --  Creates SDG project and add a datasource to it
    verify_crawl_job()                  --  Verifies the crawl job by matching the number of files.
    config_and_run_backup()             --  Configures and Runs the backup of the given index server for a given role..
    recreate_index_server()             --  Stops the Index Server, deletes the required data source core,
                                            recreates the index directory of data source core, starts the Index Server
    index_server_core_restore()         --  Do in-place restore of the required index server core and fetch data from
                                            the index server core using data source handler
    validate_data()                     --  Validates if the data before backup and data after restore matches for
                                            a index server core via handler
    run_crawl_job()                     --  Runs the SDG crawl job for given project name and makes sure it completes.
    post_cleanup()                      --  perform Cleanup Operations for current test case run
    run()                               --  run function of this test case
"""

import time
import calendar

from cvpysdk.datacube.constants import IndexServerConstants as index_constants
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.Performance.Utils.constants import Binary
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils import constants


WAIT_TIME = 2 * 60


class TestCase(CVTestCase):
    """Class for Verify inplace restore of single core for Linux Index Server"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "Verify inplace restore of single core for Linux Index Server"
        self.show_to_user = False
        self.tcinputs = {
            "Index_Server_Node": None,
            "Storage_Policy_Name": None,
            "HostNameToAnalyze": None,
            "ContentAnalyzer": None,
            "FileServerDirectoryPath": None,
            "TestDataSQLiteDBPath": None
        }
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
        self.index_server_helper = None
        self.ds_helper = None
        self.core_name = None
        self.data_before_backup = None
        self.data_after_restore = None
        self.handler_obj = None
        self.timestamp = None
        self.dest_client_obj = None

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
        self.ds_helper = DataSourceHelper(self.commcell)
        self.dest_client_obj = self.commcell.clients.get(self.tcinputs['Index_Server_Node'])
        options_obj = OptionsSelector(self.commcell)
        self.index_directory = f"{options_obj.get_drive(self.machine_obj)}{self.id}{self.timestamp}"

    @test_step
    def pre_cleanup(self):
        """Perform Cleanup Operation for older test case runs"""
        self.gdpr_obj.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name,
            pseudo_client_name=self.file_server_display_name)

        self.log.info(f"Checking if Index Server - {self.index_server_name} already exists")
        if self.commcell.index_servers.has(self.index_server_name):
            self.log.info(f"Deleting Index Server - {self.index_server_name}")
            self.commcell.index_servers.delete(self.index_server_name)
        self.log.info(f"Sleeping for: {WAIT_TIME/2} seconds")
        time.sleep(WAIT_TIME/2)

    @test_step
    def create_index_server(self):
        """Creates an Index Server."""
        self.machine_obj.create_directory(self.index_directory, force_create=True)

        self.log.info(f"Creating Index Server - {self.index_server_name} having node(s) "
                      f"{[self.tcinputs['Index_Server_Node']]}"
                      f"having role {index_constants.ROLE_DATA_ANALYTICS} at index directory - {self.index_directory}")
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
        """Configures and Runs the backup of the given index server for a given role."""
        self.index_server_helper = IndexServerHelper(self.commcell, self.index_server_name)
        self.index_server_helper.init_subclient()
        self.log.info("Make sure default subclient has all roles in backup content")
        self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['Storage_Policy_Name'],
                                                                role_content=[index_constants.ROLE_DATA_ANALYTICS])
        backup_job_id = self.index_server_helper.run_full_backup()

    @test_step
    def recreate_index_server(self):
        """Stops the Index Server, deletes the required data source core,
         recreates the index directory of data source core, starts the Index Server"""
        ds_name = self.ds_helper.get_data_source_starting_with_string(self.file_server_display_name)
        ds_object = self.commcell.datacube.datasources.get(ds_name)
        self.core_name = ds_object.computed_core_name
        self.log.info(f"The computed core name for {ds_name} is {self.core_name}")
        handler_name = f"Handler_{self.timestamp}"
        ds_object.ds_handlers.add(handler_name, search_query=['*'])
        self.handler_obj = ds_object.ds_handlers.get(handler_name)
        self.data_before_backup = self.handler_obj.get_handler_data(handler_filter="rows=100")
        self.log.info(f"Before Backup Handler Data  : {str(self.data_before_backup)}")
        analytics_dir = self.machine_obj.get_registry_value(key=constants.ANALYTICS_REG_KEY,
                                                            value=constants.ANALYTICS_DIR_REG_KEY)
        self.log.info(f"The Analytics Directory - {analytics_dir}")
        process_name = f"{Binary.DATA_CUBE['Unix']}{self.machine_obj.instance}"
        process_id = self.machine_obj.get_process_id(process_name)
        self.log.info(f"Killing the process {process_name} on the"
                      f" destination client {self.machine_obj.machine_name} having process ID - {process_id[0]}")
        self.machine_obj.kill_process(process_id=process_id[0])
        time.sleep(WAIT_TIME)
        dir_to_remove = f"{analytics_dir}/{self.core_name}"
        self.log.info("Remove the index dir of the data source core : %s", dir_to_remove)
        self.machine_obj.remove_directory(dir_to_remove)
        self.log.info(f"Restarting the Services on the destination client {self.tcinputs['Index_Server_Node']}")
        self.dest_client_obj.restart_service()
        time.sleep(WAIT_TIME)

    @test_step
    def index_server_core_restore(self):
        """do in-place restore of the required index server core and fetch data from the index server
         core using data source handler"""

        self.log.info(f"Going to do in-place restore of index server for role {index_constants.ROLE_DATA_ANALYTICS},"
                      f" - open data source core {self.core_name}")
        job_obj = self.index_server_helper.subclient_obj.do_restore_in_place(
            core_name=[f"{index_constants.ROLE_DATA_ANALYTICS}/{self.core_name}"])
        self.index_server_helper.monitor_restore_job(job_obj=job_obj)
        self.data_after_restore = self.handler_obj.get_handler_data(
            handler_filter=constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info(f"After Restore Handler Data  : {str(self.data_after_restore)}")

    @test_step
    def validate_data(self):
        """validates if the data before backup and data after restore matches for a index server core via handler"""
        self.log.info("Going to cross verify data before backup and after restore for this data source")
        is_data_valid = self.ds_helper.validate_data_from_handler_response(source_data=self.data_before_backup,
                                                                           dest_data=self.data_after_restore)
        if not is_data_valid:
            raise Exception("Documents not matched after index server restore. Please check logs")

    @test_step
    def run_crawl_job(self):
        """Runs the SDG crawl job for the given project name and makes sure it completes"""

        self.gdpr_obj.data_source_discover_obj.select_details()
        self.gdpr_obj.data_source_discover_obj.start_data_collection_job(job_type="full")
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.navigate_to_project_details(
            self.project_name)
        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete Data Source Scan")
        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)

    @test_step
    def post_cleanup(self):
        """Perform Cleanup Operation for current test case run"""
        self.pre_cleanup()
        self.log.info(f"Removing Index Directory {self.index_directory}")
        self.machine_obj.remove_directory(self.index_directory)

    def run(self):
        """Run function of this test case"""

        try:
            self.init_tc()
            self.pre_cleanup()
            self.create_index_server()
            self.create_inventory()
            self.create_plan()
            self.add_sdg_proj()
            self.verify_crawl_job()
            self.config_and_run_backup()
            self.recreate_index_server()
            self.index_server_core_restore()
            self.validate_data()
            self.run_crawl_job()
            self.post_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
