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
    create_subclient()                  --  Creates a subclient and perform it's backup for the testcase
    create_inventory()                  --  Creates an inventory.
    create_plan()                       --  Creates a DC Plan for FSO.
    create_fso_client()                 --  Create FSO client
    create_fso_project()                --  Create FSO data source and start crawl job.
    run_index_server_backup()           --  Once we get some documents in solr core, starts index server backup job and
                                            validates job completion
    validate_fso_job_completion()       --  Validates FSO crawl job completion
    validate_crawled_items()            --  Validates the crawled items count with the source count.
    validate_doc_count()                --  Validate crawled documents count.
    index_server_core_restore()         --  do in-place restore of the required index server core and fetch data using
                                            data source handler
    run_crawl_job()                     --  Runs the FSO crawl job for a given client and datasource
    post_cleanup()                      --  perform Cleanup Operations for current test case run
    run()                               --  run function of this test case
"""

import time
import calendar

from cvpysdk.datacube.constants import IndexServerConstants as index_constants
from cvpysdk.index_server import IndexServer
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.utils import constants

WAIT_TIME = 2 * 60


class TestCase(CVTestCase):
    """Validate index server backup while running crawl job"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validate index server backup while running crawl job"
        self.tcinputs = {
            "IndexServerNodes": None,
            "StoragePolicyName": None,
            "HostNameToAnalyze": None,
            "SubclientContentDataPath": None
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
        self.options_obj = None
        self.doc_count_before_backup = None
        self.crawl_job_final_doc_count = None
        self.doc_count_after_restore = None
        self.select_dict = None
        self.is_obj = None
        self.core_name = None
        self.subclient_name = None
        self.ds_helper = None
        self.backupset_obj = None

    def init_tc(self):
        """Initial Configuration for testcase"""
        try:
            self.index_server_name = f"{self.id}_index_server"
            self.file_server_display_name = f"{self.id}_file_server_fso"
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

            client_obj = self.commcell.clients.get(self.tcinputs["HostNameToAnalyze"])
            agent_obj = client_obj.agents.get(constants.FILE_SYSTEM_IDA)
            self.backupset_obj = agent_obj.backupsets.get(constants.DEFAULT_BACKUPSET)

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
    def create_subclient(self):
        """Creates a subclient and perform it's backup for the testcase

        Returns the backupset object of the created subclient"""
        self.subclient_name = f"subclient_{self.timestamp}"
        subclient_obj = self.backupset_obj.subclients.add(subclient_name=self.subclient_name,
                                                          storage_policy=self.tcinputs['StoragePolicyName'])
        subclient_obj.content = [self.tcinputs["SubclientContentDataPath"]]
        job_obj = subclient_obj.backup("Full")
        self.ds_helper.monitor_crawl_job(job_obj.job_id)

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

    @test_step
    def run_index_server_backup(self):
        """Once we get some documents in solr core, starts index server backup job and validates job completion"""

        ds_name = self.ds_helper.get_data_source_starting_with_string(self.file_server_display_name)
        ds_object = self.commcell.datacube.datasources.get(ds_name)
        ds_id = ds_object.datasource_id
        self.log.info(f"Data Source Name : {ds_name} , Data Source ID : {ds_id}")
        self.core_name = ds_object.computed_core_name
        print(f"The computed core name for {ds_name} is {self.core_name}")
        self.select_dict = {"IsFile": 1, "data_source": ds_id}
        self.doc_count_before_backup = 0
        self.is_obj = IndexServer(self.commcell, self.index_server_name)

        while self.doc_count_before_backup < 1:
            self.doc_count_before_backup = \
                (self.is_obj.execute_solr_query(self.core_name, select_dict=self.select_dict))['response']['numFound']

        self.log.info(f"Documents count before backup : {self.doc_count_before_backup}")
        backup_job_id = self.index_server_helper.run_full_backup()

    @test_step
    def validate_fso_job_completion(self):
        """Validates FSO crawl job completion"""

        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete Datasource scan.")

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
        source_count = self.backupset_obj.backed_up_files_count()
        self.log.info(f"Source Count : {source_count}")
        if source_count != ui_count:
            raise Exception(f"Crawled Items Validation Failed. Total Documents Count Mismatched"
                            f"Actual Documents Count - {source_count} , UI Documents Count - {ui_count}")
        self.log.info(f"Crawled Items Validation Successful, Count : {ui_count}")
        self.crawl_job_final_doc_count = ui_count

    @test_step
    def validate_doc_count(self):
        """Validates if the Final Documents Count of crawl job is greater than Documents Count After cvsolr Restore
        is greater than Documents Count Before cvsolr Backup or not"""

        self.doc_count_after_restore = \
            (self.is_obj.execute_solr_query(self.core_name, select_dict=self.select_dict))['response']['numFound']

        if self.crawl_job_final_doc_count > self.doc_count_after_restore > self.doc_count_before_backup:
            self.log.info(f"Successfully Validated Final Documents Count of crawl job: {self.crawl_job_final_doc_count}"
                          f" is greater than Documents Count After Restore : {self.doc_count_after_restore}"
                          f" is greater than Documents Count Before Backup : {self.doc_count_before_backup}")

        else:
            raise Exception(f"Validation Failed Final document count of crawl job :{self.crawl_job_final_doc_count}"
                            f" Documents Count After Restore : {self.doc_count_after_restore}"
                            f" Documents Count Before Backup : {self.doc_count_before_backup}")

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
    def post_cleanup(self):
        """Perform Cleanup Operation for current test case run"""
        self.pre_cleanup()
        self.log.info(f"Deleting the subclient {self.subclient_name}")
        self.backupset_obj.subclients.delete(self.subclient_name)
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
            self.create_subclient()
            self.create_inventory()
            self.create_plan()
            self.index_server_helper = IndexServerHelper(self.commcell, self.index_server_name)
            self.index_server_helper.init_subclient()
            self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['StoragePolicyName'],
                                                                    role_content=["Data Analytics"])
            self.create_fso_client()
            self.create_fso_project()
            self.run_index_server_backup()
            self.validate_fso_job_completion()
            self.validate_crawled_items()
            self.index_server_core_restore()
            self.validate_doc_count()
            self.post_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
