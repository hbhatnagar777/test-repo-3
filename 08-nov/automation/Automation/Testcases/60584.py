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

    init_browser()                  --  initializes the CvBrowser class and logs into the AdminConsole

    create_inventory()              --  creates a new Inventory

    create_project()                --  creates a new SDG project

    create_plan()                   --  creates a new DC plan

    add_data_source_to_project()    --  adds a new file system data source to the project

    verify_data_source_discover()   --  validates the discover report with the DB

    perform_cleanup()               --  performs AdminConsole cleanup operations

    close_browser()                 --  logs out of Admin console and closes the CvBrowser

    cleanup()                       --  performs cleanup

    run()                           --  run function of this test case

    create_commcell_entities()      --  creates all the commcell entities required for the testcase

    do_admin_console_operations()   --  performs all the admin console operations required for the testcase

    run_backup_and_ci()             --  runs a file system subclient backup and Content indexing job


"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils.constants import HOST_NAME, INDIA_COUNTRY_NAME, ENTITY_IP, ENTITY_EMAIL, FILE_SYSTEM_IDA
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.search_engine_util import SearchEngineHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.GDPRHelper import GDPR


class TestCase(CVTestCase):
    """Class for executing this test case"""
    teststep = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Activate SDG : v1 Import index job on File system data source"
        self.tcinputs = {
            "SearchEngineClientName": None,
            "IndexServerName": None,
            "MediaAgentName": None,
            "CAName": None,
            "DomainName": None,
            "ClientName": None,
            "DataPath": None,
            "TestDBPath": None,
            "UserName": None,
            "Password": None
        }
        self.search_engine_client_name = None
        self.subclient_obj = None
        self.subclient_name = None
        self.backupset_name = None
        self.index_server_name = None
        self.fs_agent_object = None
        self.subclient_content = None
        self.browser = None
        self.adminconsole = None
        self.gdpr_helper = None
        self.project_name = None
        self.plan_name = None
        self.inventory_name = None
        self.navigator = None
        self.activate_utils = None
        self.content_analyzer_name = None
        self.file_server_display_name = None
        self.db_path = None
        self.username = None
        self.password = None
        self.client_name = None
        self.name_server_asset = None
        self.entities_list = None
        self.wait_time = None
        self.job_timeout = None
        self.storage_policy_name = None
        self.media_agent_name = None
        self.library_name = None
        self.mount_path = None
        self.search_engine_util = None

    def setup(self):
        """Setup function of this test case"""
        self.file_server_display_name = "file_server_%s" % self.id
        self.subclient_name = "Subclient%s" % self.id
        self.backupset_name = "BackupSet%s" % self.id
        self.plan_name = "Plan%s" % self.id
        self.project_name = "Project%s" % self.id
        self.inventory_name = "Inventory%s" % self.id
        self.storage_policy_name = "StoragePolicy%s" % self.id
        self.library_name = "Library%s" % self.id

        self.index_server_name = self.tcinputs['IndexServerName']
        self.search_engine_client_name = self.tcinputs['SearchEngineClientName']
        self.subclient_content = self.tcinputs['DataPath'].split(',')
        self.content_analyzer_name = self.tcinputs['CAName']
        self.db_path = self.tcinputs['TestDBPath']
        self.username = self.tcinputs['UserName']
        self.password = self.tcinputs['Password']
        self.client_name = self.tcinputs['ClientName']
        self.name_server_asset = self.tcinputs['DomainName']
        self.media_agent_name = self.tcinputs['MediaAgentName']

        self.activate_utils = ActivateUtils()
        self.search_engine_util = SearchEngineHelper(self)
        self.fs_agent_object = self.client.agents.get(FILE_SYSTEM_IDA)
        self.entities_list = [ENTITY_IP, ENTITY_EMAIL]
        self.wait_time = 15 * 60
        self.job_timeout = 5 * 60
        drive_letter = OptionsSelector(self.commcell).get_drive(
            Machine(machine_name=self.media_agent_name, commcell_object=self.commcell))
        self.mount_path = f"{drive_letter}Library_{self.id}"

    def init_browser(self):
        """Initializes the browser object and login to adminconsole"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                             username=self.username,
                                             password=self.password)
            self.adminconsole.login(username=self.username, password=self.password)
            self.navigator = self.adminconsole.navigator
            self.gdpr_helper = GDPR(admin_console=self.adminconsole, commcell=self.commcell, csdb=self.csdb)
            self.gdpr_helper.create_sqlite_db_connection(self.db_path)
            self.gdpr_helper.testdata_path = self.tcinputs['DataPath']
            self.gdpr_helper.entities_list = self.entities_list
            self.gdpr_helper.data_source_name = self.file_server_display_name

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @teststep
    def create_inventory(self):
        """Create Inventory With Given Nameserver"""
        self.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_inventory_manager()
        self.gdpr_helper.inventory_details_obj.add_inventory(self.inventory_name, self.index_server_name,
                                                             name_server=self.name_server_asset)
        if not self.gdpr_helper.inventory_details_obj.wait_for_asset_status_completion(self.name_server_asset):
            raise Exception("Could not complete Asset Scan")
        self.log.info(f"Sleeping for: '{self.wait_time}' seconds")
        time.sleep(self.wait_time)

    @teststep
    def create_plan(self):
        """Create Data Classification Plan"""
        self.navigator.navigate_to_plan()
        self.gdpr_helper.plans_obj.create_data_classification_plan(
            plan=self.plan_name, index_server=self.index_server_name, content_analyzer=self.content_analyzer_name,
            entities_list=self.entities_list)

    @teststep
    def create_project(self):
        """Create a new SDG project"""
        self.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_helper.file_server_lookup_obj.add_project(self.project_name, self.plan_name)

    @teststep
    def add_data_source_to_project(self):
        """Adds a file system data source to the SDG project"""
        self.gdpr_helper.file_server_lookup_obj.select_add_data_source()
        self.gdpr_helper.file_server_lookup_obj.add_file_server(
            search_name=self.client_name,
            search_category=HOST_NAME,
            display_name=self.file_server_display_name,
            country_name=INDIA_COUNTRY_NAME,
            agent_installed=True,
            backup_data_import=True,
            inventory_name = self.inventory_name
        )
        self.gdpr_helper.file_server_lookup_obj.select_data_source(self.file_server_display_name)
        self.gdpr_helper.data_source_discover_obj.select_details()
        job_id = self.gdpr_helper.data_source_discover_obj.get_running_job_id()
        self.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_helper.file_server_lookup_obj.navigate_to_project_details(self.project_name)
        if not self.gdpr_helper.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=self.job_timeout):
            raise Exception("Could not complete Data Source Scan")
        if not CrawlJobHelper.is_index_import_job(self.commcell, int(job_id)):
            self.log.info("Crawl job invoked was not an Index import job")
            raise Exception("Crawl job invoked was not an Index import job")
        self.log.info("Index import job completed successfully")
        self.log.info(f"Sleeping for: '{self.wait_time}' seconds")
        time.sleep(self.wait_time)

    @teststep
    def verify_data_source_discover(self):
        """Validates the data source crawled entities data"""
        self.gdpr_helper.file_server_lookup_obj.select_data_source(self.file_server_display_name)
        self.gdpr_helper.verify_data_source_discover()
        self.gdpr_helper.data_source_discover_obj.select_review()
        self.gdpr_helper.verify_data_source_review()

    def perform_cleanup(self):
        """Performs Admin console Cleanup Operation"""
        self.gdpr_helper.cleanup(project_name=self.project_name,
                                 plan_name=self.plan_name,
                                 inventory_name=self.inventory_name)

    def close_browser(self):
        """Closes the CvBrowser"""
        self.adminconsole.logout()
        self.browser.close_silently()

    @teststep
    def cleanup(self):
        """Perform Cleanup Operation"""
        self.init_browser()
        self.perform_cleanup()
        self.close_browser()
        self.activate_utils.activate_cleanup(
            commcell_obj=self.commcell,
            client_name=self.client_name,
            backupset_name=self.backupset_name,
            storage_policy_name=self.storage_policy_name
        )

    @teststep
    def create_commcell_entities(self):
        """Creates all the required entities for the testcase"""
        self.log.info(f"Creating new Library {self.library_name}")
        self.commcell.disk_libraries.add(self.library_name, self.media_agent_name, self.mount_path)
        self.log.info(f"Library {self.library_name} created")
        self.log.info(f"Creating new storage policy {self.storage_policy_name}")
        self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                           library=self.library_name, media_agent=self.media_agent_name)
        self.log.info(f"Storage policy {self.storage_policy_name} created")
        self.log.info(f"Enabling Content indexing on the storage policy {self.storage_policy_name}")
        self.commcell.storage_policies.get(self.storage_policy_name).enable_content_indexing(
            cloud_id=self.search_engine_util.get_cloud_id(client_name=self.search_engine_client_name)
        )
        self.log.info(f"Content indexing enabled on the storage policy {self.storage_policy_name}")
        self.log.info(f"Enabling Content indexing on the client {self.client_name}")
        self.client.enable_content_indexing()
        self.log.info(f"Content indexing enabled on the client {self.client_name}")
        self.log.info(f"Creating new backupset {self.backupset_name}")
        self.fs_agent_object.backupsets.add(self.backupset_name)
        self.log.info(f"Backupset {self.backupset_name} created")
        self.log.info(f"Adding new subclient {self.subclient_name} to backupset {self.backupset_name}")
        self.subclient_obj = self.fs_agent_object.backupsets.get(
            self.backupset_name).subclients.add(self.subclient_name, self.storage_policy_name)
        self.log.info(f"Subclient {self.subclient_name} added")
        self.log.info("Adding content to subclient")
        self.subclient_obj.content = self.subclient_content
        self.log.info(f"Content added to subclient {self.subclient_content}")

    @teststep
    def do_admin_console_operations(self):
        """Creates all the required entities from adminconsole"""
        self.init_browser()
        self.create_plan()
        self.create_inventory()
        self.create_project()
        self.add_data_source_to_project()
        self.verify_data_source_discover()
        self.close_browser()

    @teststep
    def run_backup_and_ci(self):
        """Runs a backup job on subclient and then content indexing on the CI policy"""
        backup_job = self.subclient_obj.backup()
        if not CrawlJobHelper.monitor_job(self.commcell, backup_job):
            raise Exception("Backup job failed to completed successfully")
        self.log.info("Backup job got completed successfully")
        self.log.info("Now running CI job")
        ci_job = self.commcell.storage_policies.get(self.storage_policy_name).run_content_indexing()
        if not CrawlJobHelper.monitor_job(self.commcell, ci_job):
            raise Exception("Content Indexing job failed to complete")
        self.log.info("Content indexing job completed successfully")

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.create_commcell_entities()
            self.run_backup_and_ci()
            self.do_admin_console_operations()
            self.cleanup()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.close_browser()
