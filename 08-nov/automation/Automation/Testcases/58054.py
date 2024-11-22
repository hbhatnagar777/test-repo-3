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
import json
import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVWebAutomationException
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
        self.name = ("Review Actions Test for GDPR\
        using Google Drive as Data Source")
        self.activate_utils = ActivateUtils(self.commcell)
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "TestDataSQLiteDBPath": None,
            "ClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "SubclientName": None,
            "SDGAPI": None,
            "RiskList": None,
            "EntitiesListMap": None
        }
        # Test Case constants
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.googledrive_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.gdpr_obj = None
        self.backup_job_obj = None
        self.navigator = None
        self.test_case_error = None
        self.wait_time = 2 * 60
        self.error_dict = {}
        self.sensitive_files = list()
        self.risks_list = list()
        self.entities_list = list()

    def init_tc(self):
        """Initial Configuration For Testcase"""
        try:
            self.googledrive_server_display_name = f'{self.id}_test_googledrive_server'
            self.inventory_name = f'{self.id}_inventory_googledrive'
            self.plan_name = f'{self.id}_plan_googledrive'
            self.project_name = f'{self.id}_project_googledrive'
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
            self.risks_list = self.tcinputs['RiskList'].split(",")
            self.gdpr_obj.entities_list = list(entities_list_map.values())
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
        self.country_name = cs.USA_COUNTRY_NAME
        self.gdpr_obj.data_source_name = self.googledrive_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name, self.inventory_name
        )

    @test_step
    def add_googledrive_datasource(self):
        """
        Add OneDrive DataSource
        """
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source(data_source_type=cs.GOOGLE_DRIVE)
        self.gdpr_obj.file_server_lookup_obj.add_gdrive_server(
            self.tcinputs["ClientName"],
            "Client name",
            self.googledrive_server_display_name,
            self.country_name)

    @test_step
    def review_actions_googledrive(self):
        """
        Perform Given Actions Review for One Drive Review Page
        Returns:

        """
        self.sensitive_files = self.activate_utils.db_get_sensitive_columns_list(
            cs.GOOGLE_DRIVE,
            self.gdpr_obj.entities_list,
            self.tcinputs["TestDataSQLiteDBPath"]
        )
        file1 = self.sensitive_files[0]
        file2 = self.sensitive_files[1]
        exp_flag = False
        ignore_risks_action_status = None
        ingore_files_action_status = None
        try:
            ignore_risks_action_status = \
                self.gdpr_obj.data_source_review_obj.review_ignore_risks_actions(
                    file1,
                    self.risks_list,
                    data_source_type=cs.GOOGLE_DRIVE
                )
        except CVWebAutomationException as error_status:
            self.test_case_error = f'Ignore Risks Actions Failed:- {str(error_status)}'
            self.error_dict[f'Review Ignore Risks Actions : {file1}'] = self.test_case_error
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            exp_flag = True
        if not ignore_risks_action_status and not exp_flag:
            self.test_case_error = 'Ignore Risks Actions Failed:- Risks Not Ignored'
            self.error_dict[f'Review Ignore Risks Actions : {file1}'] = self.test_case_error

        exp_flag = False
        try:
            ingore_files_action_status = \
                self.gdpr_obj.data_source_review_obj.review_ignore_files_action(
                    file2, data_source_type=cs.GOOGLE_DRIVE
                )
        except CVWebAutomationException as error_status:
            self.test_case_error = f"Ignore Files Action Failed:- {str(error_status)}"
            self.error_dict[f'Review Ignore Files Actions : {file2}'] = self.test_case_error
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            exp_flag = True
        if not ingore_files_action_status and not exp_flag:
            self.test_case_error = f'Ignore Files Action Failed:- File not ignored'
            self.error_dict[f'Review Ignore Files Actions : {file2}'] = self.test_case_error

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.gdpr_obj.cleanup(self.project_name,
                              self.inventory_name,
                              self.plan_name,
                              pseudo_client_name=self.googledrive_server_display_name)

    def run(self):
        """Run Function For Test Case Execution"""

        try:
            self.init_tc()
            self.perform_cleanup()
            self.activate_utils.run_data_generator(self.tcinputs["SDGAPI"], cs.GOOGLE_DRIVE)
            self.activate_utils.run_backup(self.subclient)
            self.create_inventory()
            self.create_plan()
            self.create_sda_project()
            self.gdpr_obj.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])
            self.add_googledrive_datasource()

            if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.googledrive_server_display_name):
                raise Exception("Could Not Complete Data Source Scan")
            self.log.info(f"Sleeping for {str(self.wait_time)} Seconds")
            time.sleep(self.wait_time)

            self.gdpr_obj.file_server_lookup_obj.select_data_source(
                self.googledrive_server_display_name)
            self.gdpr_obj.data_source_discover_obj.select_review()
            self.review_actions_googledrive()
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
