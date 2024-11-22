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
    run_incremental_backup()                    --  Runs the Incremental Backup from Command Center for the given
                                                    Index Server
    recreate_index_server()                     --  Stops the Index Server, deletes the required data source cores,
                                                    recreates the index directory of data source cores, starts the Index
                                                    Server.
    index_server_core_restore()                 --  Do in-place restore of the required index server cores and fetch
                                                    data from the index server cores using data source handler
    validate_data()                             --  Validates if the data before backup and data after restore matches
                                                    for index servers core via handler
    post_cleanup()                              --  perform Cleanup Operation for the test case
                                                    and deletes the Index Server.
    run()                                       --  run function of this test case
"""

import calendar
import time

from cvpysdk.datacube.constants import IndexServerConstants as index_constants

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.Index_Server import IndexServer
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils import constants

WAIT_TIME = 2 * 60


class TestCase(CVTestCase):
    """Class for verifying In-Place Restore for the cores backed up via Incremental Backup for SOLR Index Server"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "Verifying In-Place Restore for the cores backed up via "
        self.show_to_user = False
        self.tcinputs = {
            "Index_Server_Node": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "IndexDirPath": None,
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
        self.index_servers_obj = None
        self.fso_helper = None
        self.index_servers_obj_sdk = None
        self.client_obj = None
        self.handler_obj = None
        self.ds_helper = None
        self.data_after_restore_dict = None
        self.core_list = None
        self.handler_obj_dict = None
        self.data_before_backup_dict = None
        self.ds_list = None

    def setup(self):
        """Setup function of this test case"""
        self.index_server_name = f'{self.id}_index_server'
        self.inventory_name = f'{self.id}_inventory'
        self.new_inventory_name = f'new_{self.id}_inventory'
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
        self.index_servers_obj = IndexServer(self.admin_console)
        self.fso_helper = FSO(self.admin_console)
        self.now_time = calendar.timegm(time.gmtime())
        self.index_directory = f"{self.tcinputs['IndexDirPath']}{self.id}{self.now_time}"
        self.ds_helper = DataSourceHelper(self.commcell)

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

        self.index_server_helper = IndexServerHelper(self.commcell, self.index_server_name)
        self.index_server_helper.manage_index_server_access_control(disable=True)

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
            directory_path=self.tcinputs["FileServerDirectoryPath"],
            agent_installed=True,
            live_crawl=True
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

        self.index_server_helper.init_subclient()
        self.log.info("Make sure default subclient has all roles in backup content")
        self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['Storage_Policy_Name'],
                                                                role_content=[index_constants.ROLE_DATA_ANALYTICS])
        backup_job_id = self.index_server_helper.run_full_backup()

    @test_step
    def recreate_index_server(self):
        """Stops the Index Server, deletes the required data source core,
         recreates the index directory of data source core, starts the Index Server"""
        self.ds_list = [self.file_server_display_name, self.inventory_name,
                        self.new_inventory_name, f"{constants.EDISCOVERYLDAP}{self.inventory_name}"]
        self.data_before_backup_dict = {}
        self.core_list = []
        self.index_servers_obj_sdk = self.index_servers_obj_sdk.get(self.index_server_name)
        for ds in self.ds_list:
            ds_name = self.ds_helper.get_data_source_starting_with_string(ds)
            ds_object = self.commcell.datacube.datasources.get(ds_name)
            core_name = ds_object.computed_core_name
            self.core_list.append(core_name)
            self.log.info(f"The computed core name for {ds_name} is {core_name}")
            data_before_backup = self.index_servers_obj_sdk.execute_solr_query(
                core_name=core_name, op_params=constants.QUERY_100_ROWS)[constants.RESPONSE_PARAM]
            self.log.info(f"Before Backup Core Data  : {str(data_before_backup)}")
            self.data_before_backup_dict[core_name] = data_before_backup

        analytics_dir = self.machine_obj.get_registry_value(key=constants.ANALYTICS_REG_KEY,
                                                            value=constants.ANALYTICS_DIR_REG_KEY)
        self.log.info(f"The Analytics Directory - {analytics_dir}")
        self.log.info("Killing the Data Analytics Service on index node.")
        self.client_obj.stop_service(constants.ANALYTICS_SERVICE_NAME)
        time.sleep(WAIT_TIME)
        for core in self.core_list:
            dir_to_remove = f"{analytics_dir}/{core}"
            self.log.info("Remove the index dir of the data source core : %s", dir_to_remove)
            self.machine_obj.remove_directory(dir_to_remove)
        self.log.info("Starting the Data Analytics Service")
        self.client_obj.start_service(constants.ANALYTICS_SERVICE_NAME)
        time.sleep(WAIT_TIME)

    @test_step
    def index_server_core_restore(self):
        """do in-place restore of the required index server core and fetch data from the index server
         core using data source handler"""

        self.log.info(f"Going to do in-place restore of index server for role {index_constants.ROLE_DATA_ANALYTICS},"
                      f" - open data source cores {self.core_list}")
        core_restore = [f"{index_constants.ROLE_DATA_ANALYTICS}/{core}" for core in self.core_list]
        job_obj = self.index_server_helper.subclient_obj.do_restore_in_place(
            core_name=core_restore)
        self.index_server_helper.monitor_restore_job(job_obj=job_obj)
        self.data_after_restore_dict = {}
        for core_name in self.core_list:
            data_after_restore = self.index_servers_obj_sdk.\
                execute_solr_query(core_name=core_name, op_params=constants.QUERY_100_ROWS)[constants.RESPONSE_PARAM]
            self.data_after_restore_dict[core_name] = data_after_restore
            self.log.info(f"After Restore Core Data  : {str(data_after_restore)}")

    @test_step
    def validate_data(self):
        """validates if the data before backup and data after restore matches for a index server core via handler"""
        self.log.info("Going to cross verify data before backup and after restore for this data source")
        for core in self.core_list:
            is_data_valid = self.ds_helper.validate_data_from_handler_response\
                (source_data=self.data_before_backup_dict[core], dest_data=self.data_after_restore_dict[core])
            if not is_data_valid:
                raise Exception(f"Documents not matched after index server restore for the datasource {core}."
                                f" Please check logs")

    @test_step
    def run_incremental_backup(self):
        """Runs the Incremental Backup from Command Center for the given Index Server"""
        self.admin_console.navigator.navigate_to_index_servers()
        inc_job_id = self.index_servers_obj.backup_index_server(self.index_server_name)

    @test_step
    def delete_docs_from_core(self):
        """Delete all the docs from the given core name on index server"""

        cores, _ = self.index_servers_obj_sdk.get_all_cores()
        core_name = None
        for core in cores:
            if not (isinstance(core, str)):
                raise Exception("Input data type is not valid")
            if self.file_server_display_name in core:
                core_name = core
                break
        self.index_servers_obj_sdk.delete_docs_from_core(core_name)

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
            self.add_name_server_to_inventory()
            self.create_inventory(self.new_inventory_name)
            self.delete_docs_from_core()
            self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
            time.sleep(WAIT_TIME)
            self.run_incremental_backup()
            self.recreate_index_server()
            self.index_server_core_restore()
            self.validate_data()
            self.post_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            pass
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
