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
    pre_cleanup()                               --  perform Cleanup Operation for older test case runs
    create_index_server()                       --  Creates an Index Server.
    create_inventory()                          --  Creates an Inventory
    create_plan()                               --  Creates a DC Plan for FSO.
    create_fso_client()                         --  Create FSO client
    create_fso_project()                        --  Create FSO data source and start crawl job.
    config_and_run_backup()                     --  Configures and Runs the Index Server backup
    add_name_server_to_inventory()              --  Adds the specified name server to the inventory.
    delete_docs_from_core(self)                 --  Delete all the docs from the given core name on index server
    create_db()                                 --  Creates metadata db for the cores present under the index directory
    run_incremental_backup()                    --  Runs the Incremental Backup from Command Center for the given
                                                    Index Server
    get_files_qualified_for_incremental()       --  Gets the files qualified for incremental by comparing the modified
                                                    time and created time of the files from the index directory
    get_files_from_index_server()               --  Gets the files from index server incremental backup browse
    post_cleanup()                              --  perform Cleanup Operation for the test case
                                                    and deletes the Index Server.
    run()                                       --  run function of this test case
"""

import calendar
import time

from cvpysdk.datacube.constants import IndexServerConstants as index_constants

from AutomationUtils.Performance.Utils.constants import Binary
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
from dynamicindex.utils import constants
from dynamicindex.utils.activateutils import ActivateUtils

WAIT_TIME = 2 * 60


class TestCase(CVTestCase):
    """Class for verifying Incremental Backup for SOLR Index Server"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "Verifying Incremental Backup for SOLR Index Server"
        self.show_to_user = False
        self.tcinputs = {
            "Index_Server_Node": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "IndexDirPath": None,
            "TestDataSQLiteDBPath": None,
            "Storage_Policy_Name": None,
            "NameServerAsset": None
        }
        # Test Case constants
        self.index_server_name = None
        self.inventory_name = None
        self.new_inventory_name = None
        self.plan_name = None
        self.file_server_display_name = None
        self.project_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.index_directory = None
        self.machine_obj = None
        self.index_server_helper = None
        self.now_time = None
        self.activate_utils = None
        self.index_servers_obj = None
        self.fso_helper = None
        self.inc_job_id = None
        self.db_path = None
        self.data_from_is_filtered = None
        self.files_qualified_for_inc_filtered = None
        self.index_servers_obj_sdk = None
        self.client_obj = None

    def setup(self):
        """Setup function of this test case"""
        self.index_server_name = f'{self.id}_index_server'
        self.inventory_name = f'{self.id}_inventory'
        self.new_inventory_name = f'{self.id}_inventory_new'
        self.plan_name = f'{self.id}_plan'
        self.project_name = f'{self.id}_project'
        self.file_server_display_name = f'{self.id}_file_server'
        self.index_servers_obj_sdk = self.commcell.index_servers
        self.client_obj = self.commcell.clients.get(self.tcinputs['Index_Server_Node'])

    def init_tc(self):
        """ Initial configuration for the test case. """
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login()
        self.log.info("Login completed successfully.")
        self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
        self.machine_obj = Machine(self.tcinputs['Index_Server_Node'], self.commcell)
        self.activate_utils = ActivateUtils()
        self.index_servers_obj = IndexServer(self.admin_console)
        self.fso_helper = FSO(self.admin_console)
        self.now_time = calendar.timegm(time.gmtime())
        self.index_directory = f"{self.tcinputs['IndexDirPath']}{self.id}{self.now_time}"
        self.db_path = self.tcinputs['TestDataSQLiteDBPath']
        self.data_from_is_filtered = {}
        self.files_qualified_for_inc_filtered = {}

    @test_step
    def pre_cleanup(self):
        """Perform Cleanup Operation for older test case runs"""

        self.gdpr_obj.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name,
            pseudo_client_name=self.file_server_display_name)

        self.gdpr_obj.cleanup(inventory_name=self.new_inventory_name)

        self.log.info(f"Checking if Index Server - {self.index_server_name} already exists")
        if self.commcell.index_servers.has(self.index_server_name):
            self.log.info(f"Deleting Index Server - {self.index_server_name}")
            self.commcell.index_servers.delete(self.index_server_name)

    @test_step
    def create_index_server(self):
        """Creates an Index Server."""
        self.machine_obj.create_directory(self.index_directory, force_create=True)

        self.commcell.index_servers.create(index_server_name=self.index_server_name,
                                           index_server_node_names=[self.tcinputs['Index_Server_Node']],
                                           index_directory=self.index_directory,
                                           index_server_roles=[index_constants.ROLE_DATA_ANALYTICS])

        self.machine_obj.create_registry(key='Analytics', value='bDisableAnalyticsAccessControl', data=1)

        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)

    @test_step
    def create_inventory(self, inventory_name):
        """Creates an Inventory."""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            inventory_name, self.index_server_name)

    @test_step
    def create_plan(self):
        """Creates a DC Plan"""
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.index_server_name, "",
            content_search=False, content_analysis=False, target_app='fso')

    @test_step
    def create_fso_client(self):
        """Create FSO client """
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(self.inventory_name, self.plan_name)

    @test_step
    def create_fso_project(self):
        """Create FSO data source and start crawl job"""
        self.gdpr_obj.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], 'Client name',
            self.file_server_display_name, constants.USA_COUNTRY_NAME,
            agent_installed=True,
            live_crawl=False
        )
        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete Datasource scan.")

        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME * 3)

    @test_step
    def add_name_server_to_inventory(self):
        """Adds the specified name server to the inventory"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.navigate_to_inventory_details(self.inventory_name)
        self.gdpr_obj.inventory_details_obj.add_asset_name_server(
            self.tcinputs["NameServerAsset"])
        self.admin_console.log.info(f"Sleeping for {WAIT_TIME}")
        time.sleep(WAIT_TIME)
        if not self.gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete the asset scan.")

    @test_step
    def config_and_run_backup(self):
        """Configures and Runs the backup"""

        self.index_server_helper = IndexServerHelper(self.commcell, self.index_server_name)
        self.index_server_helper.init_subclient()
        self.log.info("Make sure default subclient has all roles in backup content")
        self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['Storage_Policy_Name'],
                                                                role_content=[index_constants.ROLE_DATA_ANALYTICS])
        backup_job_id = self.index_server_helper.run_full_backup()

    @test_step
    def create_db(self):
        """Creates metadata db for the cores present under the index directory"""
        process_name = f"{Binary.DATA_CUBE['Windows']}"

        self.log.info("Killing the Data Analytics Service on index node so that core commits don't interfere with"
                      " db creation.")
        self.client_obj.stop_service(constants.ANALYTICS_SERVICE_NAME)
        self.activate_utils.create_fso_metadata_db(
            self.index_directory, self.db_path, target_machine_name=self.commcell.webconsole_hostname)
        self.log.info("Starting the Data Analytics Service")
        self.client_obj.start_service(constants.ANALYTICS_SERVICE_NAME)

    @test_step
    def run_incremental_backup(self):
        """Runs the Incremental Backup from Command Center for the given Index Server"""
        self.admin_console.navigator.navigate_to_index_servers()
        self.inc_job_id = self.index_servers_obj.backup_index_server(self.index_server_name)

    @test_step
    def get_files_qualified_for_incremental(self):
        """Gets the files qualified for incremental by comparing the modified time and created time of the files from
        the index directory"""
        self.fso_helper.create_sqlite_db_connection(self.db_path)
        fso_metadata = self.fso_helper.get_fso_time_metadata()
        self.files_qualified_for_inc_filtered = \
            self.index_server_helper.get_files_qualified_for_incremental(fso_metadata, self.now_time)
        self.log.info(f"Files Qualified For Incremental Filtered:- {self.files_qualified_for_inc_filtered}")

    @test_step
    def get_files_from_index_server(self):
        """Gets the files from index server incremental backup browse"""
        file_list, data_from_index_server = self.index_server_helper.get_backup_files_details_from_is(
            role_name=index_constants.ROLE_DATA_ANALYTICS, job_id=self.inc_job_id)

        # Filtering out the folders and only keeping the files
        self.data_from_is_filtered = \
            self.index_server_helper.filter_files_from_is_browse_response(data_from_index_server.items())

        self.log.info(f"Files From Index Server Incremental Backup {self.data_from_is_filtered}")

    @test_step
    def delete_docs_from_core(self):
        """Delete all the docs from the given core name on index server"""
        index_server_obj = self.index_servers_obj_sdk.get(self.index_server_name)
        cores, _ = index_server_obj.get_all_cores()
        core_name = None
        for core in cores:
            if not (isinstance(core, str)):
                raise Exception("Input data type is not valid")
            if self.file_server_display_name in core:
                core_name = core
                break
        index_server_obj.delete_docs_from_core(core_name)

    @test_step
    def post_cleanup(self):
        """Perform Cleanup Operation for the test case and deletes the Index Server"""

        self.pre_cleanup()
        self.log.info(f"Removing Index Directory {self.index_directory}")
        self.machine_obj.remove_directory(self.index_directory)
        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)

    def run(self):
        """Run function of this test case"""

        try:
            self.init_tc()
            self.pre_cleanup()
            self.create_index_server()
            self.create_inventory(self.inventory_name)
            self.create_plan()
            self.create_fso_client()
            self.create_fso_project()
            self.config_and_run_backup()
            self.now_time = calendar.timegm(time.gmtime())
            self.log.info(f" Now Time :- {self.now_time}")
            self.add_name_server_to_inventory()
            self.create_inventory(self.new_inventory_name)
            self.delete_docs_from_core()
            self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
            time.sleep(WAIT_TIME)
            self.run_incremental_backup()
            self.create_db()
            self.get_files_qualified_for_incremental()
            self.get_files_from_index_server()
            if self.files_qualified_for_inc_filtered == self.data_from_is_filtered:
                self.log.info("Incremental Backup Verified Successfully. The files from browse match the files"
                              "qualified for incremental")
            else:
                self.log.info("Failed to verify Incremental Backup")
                files_qualified_for_inc_filtered_set = set(self.files_qualified_for_inc_filtered.items())
                data_from_is_filtered_set = set(self.data_from_is_filtered.items())
                self.log.info(f"Files qualified for incremental but not found in browse or file size mismatch:-"
                              f" {files_qualified_for_inc_filtered_set - data_from_is_filtered_set}")
                self.log.info(f"Files found in browse but are not qualified for incremental or file size mismatch:-"
                              f" {data_from_is_filtered_set - files_qualified_for_inc_filtered_set}")
                raise Exception("Failed to verify Incremental Backup. The files from browse do not match the files"
                                "qualified for incremental")
            self.post_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
