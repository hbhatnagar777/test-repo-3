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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Reports.utils import TestCaseUtils
from Server.JobManager.jobmanager_helper import JobManager
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from dynamicindex.utils.activateutils import ActivateUtils
import dynamicindex.utils.constants as cs


class TestCase(CVTestCase):
    """Class For executing basic acceptance test of GDPR Feature"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "SDG Advance Search - using Exchange Server as Data Source"
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "TestDataSQLiteDBPath": None,
            "SensitiveMailAPI": None,
            "ClientName": None,
            "EntitiesList": None,
            "MetaDataColList": None,
            "QueriesPerEntity": None
        }
        # Test Case constants
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.exchange_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.gdpr_obj = None
        self.navigator = None
        self.test_case_error = None
        self.wait_time = 2 * 60
        self.job_manager = None

    def init_tc(self):
        """Initial Configuration For Testcase"""
        try:
            self.exchange_server_display_name = f'{self.id}_test_exchange_server'
            self.inventory_name = f'{self.id}_inventory_exchange'
            self.plan_name = f'{self.id}_plan_exchange'
            self.project_name = f'{self.id}_project_exchange'
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.gdpr_obj.advance_column_names = self.tcinputs['MetaDataColList'].split(',')
            self.gdpr_obj.advance_entity_names = self.tcinputs['EntitiesList'].split(',')
            self.gdpr_obj.queries_per_entity = int(self.tcinputs["QueriesPerEntity"])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Nameserver
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])

    @test_step
    def create_plan(self):
        """
        Create Data Classification Plan
        """
        self.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
            self.tcinputs['ContentAnalyzer'], select_all=True)

    @test_step
    def create_sda_project(self):
        """
        Create SDA Project And Run Analysis
        """
        self.country_name = cs.USA_COUNTRY_NAME
        self.gdpr_obj.data_source_name = self.exchange_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name, self.inventory_name
        )

    @test_step
    def add_exchange_datasource(self):
        """
        Add Exchange DataSource
        """
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source(data_source_type=cs.EXCHANGE)
        self.gdpr_obj.file_server_lookup_obj.add_exchange_server(
            self.tcinputs["ClientName"],
            "Client name",
            self.exchange_server_display_name,
            self.country_name
        )

    @test_step
    def review_exchange_data_source(self):
        """
        Review Added Exchange DataSource, Advance
        Search
        """
        self.gdpr_obj.verify_data_source_name()
        status = self.gdpr_obj.verify_advance_search(
            self.tcinputs['TestDataSQLiteDBPath'], data_source=cs.EXCHANGE)
        if not status:
            self.test_case_error = "Please check logs for failed queries. Advance Search failed"

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.gdpr_obj.cleanup(self.project_name,
                              self.inventory_name,
                              self.plan_name,
                              pseudo_client_name=self.exchange_server_display_name)

    def run(self):
        """Run Function For Test Case Execution"""

        try:
            self.activate_utils.run_data_generator(self.tcinputs["SensitiveMailAPI"], cs.EXCHANGE)
            self.job_manager = JobManager(commcell=self.commcell)
            self.log.info("Starting Backup JOB")
            self.job_manager.job = self.subclient.backup()
            self.job_manager.wait_for_state('completed', retry_interval=60, time_limit=45)
            self.log.info("Backup Job Completed Successfully for all mailboxes in subclient!!")
            self.init_tc()
            self.perform_cleanup()

            self.create_inventory()
            self.create_plan()
            self.create_sda_project()
            self.add_exchange_datasource()

            if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.exchange_server_display_name):
                raise Exception("Could Not Complete Data Source Scan")
            self.log.info(f"Sleeping for {str(self.wait_time)} Seconds")
            time.sleep(self.wait_time)

            self.gdpr_obj.file_server_lookup_obj.select_data_source(
                self.exchange_server_display_name)
            self.gdpr_obj.data_source_discover_obj.select_review()
            self.review_exchange_data_source()
            if self.test_case_error is not None:
                raise CVTestStepFailure(self.test_case_error)
            self.perform_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)