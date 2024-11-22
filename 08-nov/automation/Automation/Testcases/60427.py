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

    add_data_source_to_project()    --  adds a new Exchange data source to the project

    verify_exchange_review()        --  validates the review report entities with the DB

    perform_cleanup()               --  performs AdminConsole cleanup operations

    close_browser()                 --  logs out of Admin console and closes the CvBrowser

    cleanup()                       --  performs cleanup

    run()                           --  run function of this test case

    create_commcell_entities()      --  creates all the commcell entities required for the testcase

    do_admin_console_operations()   --  performs all the admin console operations required for the testcase

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from cvpysdk.datacube.constants import IndexServerConstants
from dynamicindex.utils.constants import INDIA_COUNTRY_NAME, HOST_NAME, ENTITY_EMAIL, ENTITY_IP, \
    EXCHANGE_IDA, USER_MAILBOX_BACKUPSET, USER_MAILBOX_SUBCLIENT, EXCHANGE
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.utils.activateutils import ActivateUtils
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.GDPRHelper import GDPR

EXCHANGE_CONFIG = get_config().DynamicIndex.ExchangeClientDetails


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
        self.name = "Import index job on a Exchange data source"
        self.tcinputs = {
            "ExchangeClientName": None,
            "IndexServerNodeName": None,
            "DomainName": None,
            "CAName": None,
            "UserName": None,
            "Password": None,
            "TestDBPath": None,
            "SensitiveMailAPI": None
        }
        self.index_server_name = None
        self.index_directory = None
        self.index_server_roles = None
        self.index_node_name = None
        self.browser = None
        self.adminconsole = None
        self.gdpr_helper = None
        self.project_name = None
        self.plan_name = None
        self.inventory_name = None
        self.navigator = None
        self.activate_utils = None
        self.entities_list = None
        self.content_analyzer_name = None
        self.exchange_data_source_display_name = None
        self.username = None
        self.password = None
        self.name_server_asset = None
        self.exchange_mailbox_client_name = None
        self.wait_time = None
        self.job_timeout = None
        self.job_manager = None

    def setup(self):
        """Setup function of this test case"""
        self.index_server_name = "IndexServer%s" % self.id
        self.exchange_data_source_display_name = "exchange_data_source_%s" % self.id
        self.plan_name = "Plan%s" % self.id
        self.project_name = "Project%s" % self.id
        self.inventory_name = "Inventory%s" % self.id
        self.entities_list = [ENTITY_IP, ENTITY_EMAIL]
        self.index_server_roles = [IndexServerConstants.ROLE_DATA_ANALYTICS,
                                   IndexServerConstants.ROLE_EXCHANGE_INDEX]

        self.index_node_name = self.tcinputs['IndexServerNodeName']
        self.exchange_mailbox_client_name = self.tcinputs['ExchangeClientName']
        self.content_analyzer_name = self.tcinputs['CAName']
        self.username = self.tcinputs['UserName']
        self.password = self.tcinputs['Password']
        self.name_server_asset = self.tcinputs['DomainName']
        self.activate_utils = ActivateUtils()
        self.wait_time = 15 * 60
        self.job_timeout = 5 * 60
        self.index_directory = IndexServerHelper.get_new_index_directory(self.commcell,
                                                                         self.index_node_name, self.id)

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
            self.gdpr_helper.entities_list = self.entities_list
            self.gdpr_helper.data_source_name = self.exchange_data_source_display_name
            self.gdpr_helper.create_sqlite_db_connection(self.tcinputs['TestDBPath'])

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
        self.gdpr_helper.file_server_lookup_obj.select_add_data_source(data_source_type='Exchange')
        self.gdpr_helper.file_server_lookup_obj.add_exchange_server(
            search_name=self.exchange_mailbox_client_name,
            search_category=HOST_NAME, display_name=self.exchange_data_source_display_name,
            country_name=INDIA_COUNTRY_NAME,
            inventory_name = self.inventory_name
        )
        self.gdpr_helper.file_server_lookup_obj.select_data_source(self.exchange_data_source_display_name)
        self.gdpr_helper.data_source_discover_obj.select_details()
        job_id = self.gdpr_helper.data_source_discover_obj.get_running_job_id()
        self.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_helper.file_server_lookup_obj.navigate_to_project_details(self.project_name)
        if not self.gdpr_helper.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.exchange_data_source_display_name, timeout=self.job_timeout):
            raise Exception("Could not complete Data Source Scan")
        if not CrawlJobHelper.is_index_import_job(self.commcell, int(job_id)):
            self.log.info("Crawl job invoked was not an Index import job")
            raise Exception("Crawl job invoked was not an Index import job")
        self.log.info("Index import job completed successfully")
        self.log.info(f"Sleeping for: '{self.wait_time}' seconds")
        time.sleep(self.wait_time)

    @teststep
    def verify_exchange_review(self):
        """Validates the data source crawled entities data"""
        self.gdpr_helper.file_server_lookup_obj.select_data_source(self.exchange_data_source_display_name)
        self.gdpr_helper.data_source_discover_obj.select_review()
        self.gdpr_helper.verify_data_source_name()
        db_sensitive_mail_subject_list = self.activate_utils.db_get_sensitive_columns_list(
            "Exchange",
            self.gdpr_helper.entities_list,
            self.tcinputs["TestDBPath"])
        self.log.info(f"Sensitive Mail Subject List {db_sensitive_mail_subject_list}")
        for subject in db_sensitive_mail_subject_list:
            if not self.gdpr_helper.compare_entities(subject, "Exchange"):
                raise Exception("Entities Value Mismatched")

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
            index_server_name=self.index_server_name
        )

    @teststep
    def create_commcell_entities(self):
        """Creates all the required entities for the testcase"""
        self.log.info(f"Creating new Index Server {self.index_server_name}")
        self.commcell.index_servers.create(self.index_server_name, [self.index_node_name],
                                           self.index_directory, self.index_server_roles)
        self.log.info(f"Index server {self.index_server_name} created")

    @teststep
    def do_admin_console_operations(self):
        """Creates all the required entities from adminconsole"""
        self.init_browser()
        self.create_plan()
        self.create_inventory()
        self.create_project()
        self.add_data_source_to_project()
        self.verify_exchange_review()
        self.close_browser()

    def run(self):
        """Run function of this test case"""
        try:
            self.client = self.commcell.clients.get(self.exchange_mailbox_client_name)
            self.agent = self.client.agents.get(EXCHANGE_IDA)
            self.backupset = self.agent.backupsets.get(USER_MAILBOX_BACKUPSET)
            self.subclient = self.backupset.subclients.get(USER_MAILBOX_SUBCLIENT)
            self.activate_utils.run_data_generator(self.tcinputs["SensitiveMailAPI"], EXCHANGE)
            self.log.info("Starting Backup JOB")
            backup_job_id = self.subclient.backup()
            if not CrawlJobHelper.monitor_job(self.commcell, backup_job_id):
                raise Exception("Backup job failed for exchange usermailbox subclient")
            self.log.info("Backup Job Completed Successfully for all mailboxes in subclient!!")
            self.log.info("Starting Content Indexing JOB")
            ci_job_id = self.subclient.subclient_content_indexing()
            if not CrawlJobHelper.monitor_job(self.commcell, ci_job_id):
                raise Exception("Content Indexing job failed for exchange usermailbox subclient")
            self.log.info("Content Indexing Job Completed Successfully for all mailboxes in subclient!!")
            self.cleanup()
            self.create_commcell_entities()
            self.do_admin_console_operations()
            self.cleanup()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.close_browser()
