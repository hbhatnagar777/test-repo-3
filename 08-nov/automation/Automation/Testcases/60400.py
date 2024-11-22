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
    init_tc()                           --  initializes browser and testcase related objects
    pre_cleanup()                       --  perform Cleanup Operation for older test case runs
    create_index_server()               --  Creates an Index Server.
    create_inventory()                  --  Creates an inventory.
    create_plan()                       --  Creates a DC Plan for FSO.
    create_fso_client()                 --  Create FSO client
    create_fso_project()                --  Create FSO data source and start crawl job.
    validate_crawled_items()            --  Validates the crawled items count with the source count.
    backup_default_subclient()          --  Runs full backup of the default subclient for the host machine.
    config_and_run_backup()             --  Configures and Runs the backup of the given index server for a given role.
    recreate_index_server()             --  Stops the Index Server, deletes the required data source core,
                                            deletes the index directory of data source core, starts the Index Server
    index_server_core_restore()         --  do in-place restore of the required index server core and fetch data using
                                            data source handler
    run_crawl_job()                     --  Runs the FSO crawl job for a given client and datasource
    delete_subclients()                 --  Deletes the subclients created for the test case
    post_cleanup()                      --  perform Cleanup Operations for current test case run
    run()                               --  run function of this test case
"""

import time
import calendar

from cvpysdk.datacube.constants import IndexServerConstants as index_constants

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.Performance.Utils.constants import Binary
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.utils import constants

WAIT_TIME = 2 * 60


class TestCase(CVTestCase):
    """Verify inplace restore of DA role for multinode index server"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify inplace restore of DA role for multinode index server"
        self.tcinputs = {
            "IndexServerNodes": None,
            "StoragePolicyName": None,
            "HostNameToAnalyze": None
        }
        self.file_server_display_name = None
        self.timestamp = None
        self.index_server_name = None
        self.inventory_name = None
        self.plan_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.fso_helper = None
        self.navigator = None
        self.machines = []
        self.index_directories = []
        self.index_server_helper = None
        self.backup_job_id = None
        self.options_obj = None
        self.dest_clients = []
        self.ds_helper = None

    def init_tc(self):
        """Initial Configuration for testcase"""
        try:
            self.index_server_name = f"{self.id}_index_server"
            self.file_server_display_name = f"{self.id}_test_file_server_fso"
            self.inventory_name = f"{self.id}_inventory_fso"
            self.plan_name = f"{self.id}_plan_fso"
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.log.info("Login completed successfully.")
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.gdpr_obj.data_source_name = self.file_server_display_name
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.fso_helper.data_source_name = self.file_server_display_name
            self.options_obj = OptionsSelector(self.commcell)
            self.ds_helper = DataSourceHelper(self.commcell)

            for node in self.tcinputs["IndexServerNodes"]:
                machine_obj = Machine(node, self.commcell)
                self.machines.append(machine_obj)
                dest_client_obj = self.commcell.clients.get(node)
                self.dest_clients.append(dest_client_obj)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def pre_cleanup(self):
        """Perform Cleanup Operation for older test case runs"""
        self.fso_helper.fso_cleanup(
            self.tcinputs["HostNameToAnalyze"],
            self.file_server_display_name,
            pseudo_client_name=self.file_server_display_name)
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name,
                              plan_name=self.plan_name)

        self.log.info(f"Checking if Index Server - {self.index_server_name} already exists")
        if self.commcell.index_servers.has(self.index_server_name):
            self.log.info(f"Deleting Index Server - {self.index_server_name}")
            self.commcell.index_servers.delete(self.index_server_name)
        self.log.info(f"Sleeping for: {WAIT_TIME/2} seconds")
        time.sleep(WAIT_TIME / 2)

    @test_step
    def create_index_server(self):
        """Creates an Index Server."""
        for machine_obj in self.machines:
            self.timestamp = calendar.timegm(time.gmtime())
            index_directory = f"{self.options_obj.get_drive(machine_obj)}{self.id}{self.timestamp}"
            machine_obj.create_directory(index_directory, force_create=True)
            self.index_directories.append(index_directory)

        self.log.info(f"Creating Index Server - {self.index_server_name} having node(s) "
                      f"{self.tcinputs['IndexServerNodes']}"
                      f"having role {index_constants.ROLE_DATA_ANALYTICS} "
                      f"at index directories - {self.index_directories} respectively")

        self.commcell.index_servers.create(index_server_name=self.index_server_name,
                                           index_server_node_names=self.tcinputs['IndexServerNodes'],
                                           index_directory=self.index_directories,
                                           index_server_roles=[index_constants.ROLE_DATA_ANALYTICS])

        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)

    @test_step
    def create_inventory(self):
        """
        Create Inventory
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server_name)

    @test_step
    def create_plan(self):
        """
        Create Data Classification Plan
        """
        self.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.index_server_name, "",
            content_search=False, content_analysis=False, target_app='fso')

    @test_step
    def create_fso_client(self):
        """Create FSO client """
        self.navigator.navigate_to_governance_apps()
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
        time.sleep(WAIT_TIME*3)

    @test_step
    def validate_crawled_items(self):
        """Validates the crawled items count."""
        self.log.info("Getting the count of files from the FSO Dashboard")
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.select_details_action(self.tcinputs["HostNameToAnalyze"])
        self.fso_helper.fso_client_details.select_datasource(self.file_server_display_name)
        ui_count = self.fso_helper.fso_data_source_discover.fso_dashboard_entity_count("Files")
        ui_count = int(ui_count.replace(',', ''))
        self.log.info(f"UI_COUNT : {ui_count}")

        self.log.info("Getting the count of files from the backed up data of the host")
        client_obj = self.commcell.clients.get(self.tcinputs["HostNameToAnalyze"])
        agent_obj = client_obj.agents.get("File System")
        backupset_obj = agent_obj.backupsets.get("defaultBackupSet")
        source_count = backupset_obj.backed_up_files_count()
        self.log.info(f"Source Count : {source_count}")
        if source_count != ui_count:
            raise Exception(f"Crawled Items Validation Failed. Total Documents Count Mismatched"
                            f"Actual Documents Count - {source_count} , UI Documents Count - {ui_count}")
        self.log.info(f"Crawled Items Validation Successful, Count : {ui_count}")

    @test_step
    def backup_default_subclient(self):
        """Runs full backup of the default subclient for the host machine"""
        data_source_helper_obj = DataSourceHelper(self.commcell)
        client_obj = self.commcell.clients.get(self.tcinputs["HostNameToAnalyze"])
        agent_obj = client_obj.agents.get("File System")
        backupset_obj = agent_obj.backupsets.get("defaultBackupSet")
        subclient_obj = backupset_obj.subclients.get("default")
        subclient_obj.storage_policy = self.tcinputs['StoragePolicyName']
        job_obj = subclient_obj.backup("Full")
        data_source_helper_obj.monitor_crawl_job(job_obj.job_id)

    @test_step
    def config_and_run_backup(self):
        """Configures and Runs the backup of the given index server for a given role."""
        self.index_server_helper = IndexServerHelper(self.commcell, self.index_server_name)
        self.index_server_helper.init_subclient()
        self.log.info("Make sure default subclient has all roles in backup content")
        self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['StoragePolicyName'],
                                                                role_content=[index_constants.ROLE_DATA_ANALYTICS])
        self.backup_job_id = self.index_server_helper.run_full_backup()

    @test_step
    def recreate_index_server(self):
        """Stops the Index Server, deletes the required data source core,
         recreates the index directory of data source core, starts the Index Server"""

        for machine_obj in self.machines:
            analytics_dir = machine_obj.get_registry_value(key=constants.ANALYTICS_REG_KEY,
                                                           value=constants.ANALYTICS_DIR_REG_KEY)
            self.log.info(f"The Analytics Directory - {analytics_dir}")
            cores, _ = self.index_server_helper.get_cores_for_role(index_constants.ROLE_DATA_ANALYTICS,
                                                                machine_obj.machine_name)
            filtered_cores, _ = self.index_server_helper.filter_cores(cores)
            process_name = f"{Binary.DATA_CUBE['Unix']}{machine_obj.instance}"
            process_id = machine_obj.get_process_id(process_name)
            self.log.info(f"Killing the process {process_name} on the"
                          f" destination client {machine_obj.machine_name} having process ID - {process_id[0]}")
            machine_obj.kill_process(process_id=process_id[0])
            time.sleep(WAIT_TIME / 2)

            for core in filtered_cores:
                index_dir = f"{analytics_dir}/{core}"
                machine_obj.remove_directory(index_dir)

        self.log.info(f"Restarting the Services on the destination clients {self.tcinputs['IndexServerNodes']}")

        for dest_client in self.dest_clients:
            dest_client.restart_service()
        time.sleep(WAIT_TIME * 3)

    @test_step
    def index_server_core_restore(self):
        """do in-place restore of the required index server"""

        self.log.info(f"Going to do in-place restore of index server for role {index_constants.ROLE_DATA_ANALYTICS}")
        for node in self.tcinputs["IndexServerNodes"]:
            self.log.info(f"Restoring node - {node}")
            job_obj = self.index_server_helper.subclient_obj.do_restore_in_place(
                roles=[index_constants.ROLE_DATA_ANALYTICS], client=node)
            self.index_server_helper.monitor_restore_job(job_obj=job_obj)

    @test_step
    def run_crawl_job(self):
        """Runs the FSO crawl job for a given client and datasource"""

        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.select_details_action(self.tcinputs["HostNameToAnalyze"])
        self.fso_helper.fso_client_details.select_details_action(self.file_server_display_name)
        self.gdpr_obj.data_source_discover_obj.start_data_collection_job('full')
        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete Datasource scan.")

        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)

    @test_step
    def delete_subclients(self, subclients_list, backupset_obj):
        """Deletes the subclients created for the test case
        Args -
                subclients_list (List)      : List of names of all the subclients created
                backupset_obj (Object)      : The object of the default backupset.
        """

        self.log.info("Deleting all the test case generated subclients")
        for subclient in subclients_list:
            backupset_obj.subclients.delete(subclient)

    @test_step
    def post_cleanup(self):
        """Perform Cleanup Operation for current test case run"""
        self.pre_cleanup()
        self.log.info("Removing Index Directories")
        for machine_obj in self.machines:
            self.log.info(f"Removing Directory - {self.index_directories[0]}")
            machine_obj.remove_directory(self.index_directories[0])
            del self.index_directories[0]

    def run(self):
        """Run function of this test case"""

        try:
            self.init_tc()
            self.pre_cleanup()
            self.log.info("Running Data Aging in order to remove aged data from the backed up data of the host.")
            self.commcell.run_data_aging()
            self.create_index_server()
            crawl_job_helper = CrawlJobHelper(self)
            subclients_list, backupset_obj = \
                crawl_job_helper.create_subclients(client_name=self.tcinputs["HostNameToAnalyze"],
                                                   number_of_subclients=len(self.tcinputs['IndexServerNodes'])*12,
                                                   number_of_files_per_subclient=100,
                                                   storage_policy_name=self.tcinputs['StoragePolicyName'])
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
            self.create_fso_project()
            self.validate_crawled_items()
            self.config_and_run_backup()
            self.recreate_index_server()
            self.index_server_core_restore()
            self.validate_crawled_items()
            self.backup_default_subclient()
            self.run_crawl_job()
            self.delete_subclients(subclients_list=subclients_list, backupset_obj=backupset_obj)
            self.post_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
