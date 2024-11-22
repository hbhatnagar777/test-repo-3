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

    setup()                         --  sets up the variables required for running the testcase

    run()                           --  run function of this test case

    tear_down()                      --  tears down the activate created entities for running the testcase

    create_inventory()              --  Creates a new Inventory

    create_plan()                   --  Creates new Data Classification Plan

    create_sda_project()            --  Create SDA Project And Run Analysis

    add_sharepoint_datasource()     --  Adds SharePoint DataSource

    review_actions_sharepoint()     --  Performs review actions on newly added Share Point DataSource

    perform_cleanup()               --  Performs Cleanup Operation

"""

import time
import json
from dynamicindex.utils import constants as cs
from dynamicindex.utils.activateutils import ActivateUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils import constants
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole

_SHAREPOINT_CONFIG_DATA = get_config().DynamicIndex.Activate.SharePoint


class TestCase(CVTestCase):
    """Class For Review actions support for Share point  v2 Express Configuration\
        data source using Activate SDG in AdminConsole"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = ("Review actions support for Share point  v2 Express Configuration\
        data source using Activate SDG in AdminConsole")
        self.activate_utils = ActivateUtils()
        # Test Case constants
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.sharepoint_server_display_name = None
        self.index_server = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.navigator = None
        self.test_case_error = None
        self.wait_time = 2 * 60
        self.error_dict = {}

    def setup(self):
        """Initial Configuration For Testcase"""
        try:
            self.sharepoint_server_display_name = f'{self.id}_test_sharepoint_server'
            self.inventory_name = f'{self.id}_inventory_sharepoint'
            self.plan_name = f'{self.id}_plan_sharepoint'
            self.project_name = f'{self.id}_project_sharepoint'
            self.index_server = _SHAREPOINT_CONFIG_DATA.IndexServerName
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=_SHAREPOINT_CONFIG_DATA.UserName,
                                              password=_SHAREPOINT_CONFIG_DATA.Password)
            self.admin_console.login(username=_SHAREPOINT_CONFIG_DATA.UserName,
                                     password=_SHAREPOINT_CONFIG_DATA.Password)
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
        except Exception as exception:
            self.status = constants.FAILED
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Nameserver
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server)

    @test_step
    def create_plan(self):
        """
        Create Data Classification Plan
        """
        entities_list_map = json.loads(_SHAREPOINT_CONFIG_DATA.EntitiesListMap.replace("'", '"'))
        entities_list = list(entities_list_map.keys())
        self.gdpr_obj.entities_list = list(entities_list_map.values())
        self.gdpr_obj.entities_list_map = entities_list_map
        self.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.index_server,
            _SHAREPOINT_CONFIG_DATA.ContentAnalyzer, entities_list)

    @test_step
    def create_sda_project(self):
        """
        Create SDA Project And Run Analysis
        """
        self.gdpr_obj.data_source_name = self.sharepoint_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name
        )

    @test_step
    def add_sharepoint_datasource(self):
        """
        Add SharePoint DataSource
        """
        list_of_sites = f"{_SHAREPOINT_CONFIG_DATA.V2.ClientName.Express.lower()}," \
                        f"{_SHAREPOINT_CONFIG_DATA.V2.ListOfSites}"
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source(data_source_type=cs.SHAREPOINT)
        self.gdpr_obj.file_server_lookup_obj.add_share_point_server(
            _SHAREPOINT_CONFIG_DATA.V2.ClientName.Express,
            cs.CLIENT_NAME,
            self.sharepoint_server_display_name,
            cs.USA_COUNTRY_NAME,
            backupset=_SHAREPOINT_CONFIG_DATA.V2.BackupsetName,
            sites=list_of_sites,
            inventory_name = self.inventory_name
        )

    @test_step
    def review_actions_sharepoint(self):
        """
        Perform Given Actions Review for Share Point Review Page
        """
        sensitive_files = self.activate_utils.db_get_sensitive_columns_list(
            cs.SHAREPOINT,
            self.gdpr_obj.entities_list,
            _SHAREPOINT_CONFIG_DATA.TestDataSQLiteDBPath
        )
        file1 = sensitive_files[0]
        file1 = file1.split('\\')[-1]
        file2 = sensitive_files[1]
        file2 = file2.split('\\')[-1]

        exp_flag = False
        ignore_risks_action_status = None
        set_retention_action_status = None
        ignore_files_action_status = None
        try:
            ignore_risks_action_status = \
                self.gdpr_obj.data_source_review_obj.review_ignore_risks_actions(
                    file1,
                    _SHAREPOINT_CONFIG_DATA.RiskList.split(","),
                    data_source_type=cs.SHAREPOINT
                )
        except CVWebAutomationException as error_status:
            self.test_case_error = f'Ignore Risks Actions Failed:- {str(error_status)}'
            self.error_dict[f'Review Ignore Risks Actions : {file1}'] = self.test_case_error
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            exp_flag = True
        if not ignore_risks_action_status and not exp_flag:
            self.test_case_error = 'Ignore Risks Actions Failed:- Risks Not Ignored'
            self.error_dict[f'Review Ignore Risks Actions : {file1}'] = self.test_case_error
        if not exp_flag and ignore_risks_action_status:
            self.log.info(f'Review:Ignore Risk Actions on file: [{file1}] completed successfully')

        exp_flag = False
        try:
            set_retention_action_status = \
                self.gdpr_obj.data_source_review_obj.review_set_retention_action(
                    file2, 1, data_source_type=cs.SHAREPOINT
                )
        except CVWebAutomationException as error_status:
            self.test_case_error = f'Set Retention Action Failed:- {str(error_status)}'
            self.error_dict[f'Review Retention Actions : {file2}'] = self.test_case_error
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            exp_flag = True
        if not set_retention_action_status and not exp_flag:
            self.test_case_error = 'Set Retention Action Failed:- Retention Not Set'
            self.error_dict[f'Review Retention Actions : {file2}'] = self.test_case_error
        if not exp_flag and set_retention_action_status:
            self.log.info(f'Review: Set Retention Actions on file: [{file2}] completed successfully')

        exp_flag = False
        try:
            ignore_files_action_status = \
                self.gdpr_obj.data_source_review_obj.review_ignore_files_action(
                    file1, data_source_type=cs.SHAREPOINT
                )
        except CVWebAutomationException as error_status:
            self.test_case_error = f"Ignore Files Action Failed:- {str(error_status)}"
            self.error_dict[f'Review Ignore Files Actions : {file1}'] = self.test_case_error
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            exp_flag = True
        if not ignore_files_action_status and not exp_flag:
            self.test_case_error = 'Ignore Files Action Failed:- File not ignored'
            self.error_dict[f'Review Ignore Files Actions : {file1}'] = self.test_case_error
        if not exp_flag and ignore_files_action_status:
            self.log.info(f'Review: Ignore Files action on file: [{file1}] completed successfully')

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.cleanup(self.project_name,
                              self.inventory_name,
                              self.plan_name,
                              pseudo_client_name=self.sharepoint_server_display_name)

    def run(self):
        """Run Function For Test Case Execution"""

        try:
            self.perform_cleanup()
            self.activate_utils.run_data_generator(_SHAREPOINT_CONFIG_DATA.SharePointAPI, cs.SHAREPOINT)
            self.gdpr_obj.create_sqlite_db_connection(_SHAREPOINT_CONFIG_DATA.TestDataSQLiteDBPath)
            self.create_inventory()
            self.create_plan()
            self.create_sda_project()
            self.add_sharepoint_datasource()

            if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.sharepoint_server_display_name, timeout=120):
                raise Exception("Could Not Complete Data Source Scan")
            self.log.info(f"Sleeping for {str(self.wait_time)} Seconds")
            time.sleep(self.wait_time)
            self.gdpr_obj.file_server_lookup_obj.select_data_source(
                self.sharepoint_server_display_name)
            self.gdpr_obj.data_source_discover_obj.select_review()
            # Review actions - Ignore Risks, Ignore files, Set Retention
            self.review_actions_sharepoint()
            if self.test_case_error is not None:
                raise CVTestStepFailure(self.test_case_error)

        except Exception as exp:
            self.status = constants.FAILED
            if self.test_case_error is not None and len(self.error_dict.keys()) > 0:
                self.log.info("************Following Error Occurred"
                              " in the Automation Testcase***********")
                for key, value in self.error_dict.items():
                    self.log.info(f'{key}  {value} \n')
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            if self.status != constants.FAILED:
                self.perform_cleanup()
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
