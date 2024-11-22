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

import json
import time
import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from dynamicindex.utils.activateutils import ActivateUtils


class TestCase(CVTestCase):
    """Class For executing basic acceptance test of GDPR Feature"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = ("Basic Acceptance Test for Sensitive Data Analysis\
        using Database as Data Source")
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "DbInstanceName": None,
            "DatabaseAPI": None,
            "TestDataSQLiteDBPath": None
        }
        # Test Case constants
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.database_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.gdpr_obj = None
        self.navigator = None
        self.test_case_error = None
        self.wait_time = 2 * 60
        self.entities_list = list()
        self.sensitive_files = list()
        self.error_dict = dict()

    def init_tc(self):
        """Initial Configuration For Testcase"""
        try:
            self.database_server_display_name = f'{self.id}_test_database_server'
            self.inventory_name = f'{self.id}_inventory_database'
            self.plan_name = f'{self.id}_plan_database'
            self.project_name = f'{self.id}_project_database'
            self.country_name = cs.USA_COUNTRY_NAME
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            entities_list_map = json.loads(self.tcinputs['EntitiesListMap'].replace("'", '"'))
            self.entities_list = list(entities_list_map.keys())
            self.gdpr_obj.entities_list = list(entities_list_map.values())
            self.gdpr_obj.entities_list_map = entities_list_map
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
            self.tcinputs['ContentAnalyzer'], self.entities_list)

    @test_step
    def create_sda_project(self):
        """
        Create SDA Project And Run Analysis
        """

        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name, self.inventory_name
        )

    @test_step
    def add_database_datasource(self):
        """
        Add DataBase DataSource
        """
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source(data_source_type=cs.DATABASE)
        self.gdpr_obj.file_server_lookup_obj.add_database_server(
            self.tcinputs["ClientName"],
            "Client name",
            self.database_server_display_name,
            self.tcinputs["DbInstanceName"],
            self.country_name
        )

    @test_step
    def review_database_datasource(self):
        """
        Review Added Database DataSource
        """
        self.gdpr_obj.verify_data_source_name()
        self.sensitive_files = self.activate_utils.db_get_sensitive_columns_list(
            cs.DATABASE,
            self.gdpr_obj.entities_list,
            self.tcinputs["TestDataSQLiteDBPath"]
        )
        self.log.info(f"Sensitive Files from Database are {self.sensitive_files}")

        for filepath in self.sensitive_files:
            if not self.gdpr_obj.compare_entities(filepath, cs.DATABASE):
                self.test_case_error = "Entities Value Mismatched"
                self.error_dict[f'Entity Matching Failed: {filepath}'] = self.test_case_error

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.gdpr_obj.cleanup(self.project_name,
                              self.inventory_name,
                              self.plan_name,
                              pseudo_client_name=self.database_server_display_name)

    def run(self):
        """Run Function For Test Case Execution"""

        try:
            self.init_tc()
            self.perform_cleanup()
            self.activate_utils.run_data_generator(self.tcinputs["DatabaseAPI"], cs.DATABASE)
            self.create_inventory()
            self.create_plan()
            self.gdpr_obj.data_source_name = self.database_server_display_name
            self.create_sda_project()
            self.add_database_datasource()
            if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.database_server_display_name):
                raise Exception("Could Not Complete Data Source Scan")
            self.log.info(f"Sleeping for {str(self.wait_time)} Seconds")
            time.sleep(self.wait_time)
            self.gdpr_obj.file_server_lookup_obj.select_data_source(self.database_server_display_name)
            self.gdpr_obj.data_source_discover_obj.select_review()
            self.gdpr_obj.create_sqlite_db_connection(self.tcinputs["TestDataSQLiteDBPath"])
            self.review_database_datasource()
            if self.test_case_error is not None:
                raise CVTestStepFailure(self.test_case_error)
            self.perform_cleanup()
        except Exception as exp:
            if self.test_case_error is not None and len(self.error_dict.keys()) > 0:
                self.log.info("************Following Error Occurred in the Automation Testcase***********")
                for key, value in self.error_dict.items():
                    self.log.info(f'{key}  {value} \n')
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
