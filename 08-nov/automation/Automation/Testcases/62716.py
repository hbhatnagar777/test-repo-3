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
    __init__()                                   -- Initializes TestCase class

    generate_sensitive_data()                    -- Generates sensitive files with PII entities

    get_sensitive_file_details()                 -- Gets a sensitive file with an entity

    navigate_to_request_manager()                -- Navigates to Request Manager

    navigate_to_datasource_review()              -- Navigates to the datasource review page 

    init_tc()                                    -- Initial configuration for the testcase

    create_plan()                                -- Creates a plan

    create_sdg_project()                         -- Creates a project and runs analysis

    validate_review_action()                     -- Verifies the edge cases for review actions with RM

    cleanup()                                    -- Runs cleanup

    run()                                        -- Run function for this testcase
"""
import os
import time

from AutomationUtils.config import get_config
from AutomationUtils.constants import AUTOMATION_BIN_PATH
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.constants import (CRITERIA, DB_ENTITY_DELIMITER,
                                          ENTITY_EMAIL, FILE_SYSTEM, HOST_NAME,
                                          USA_COUNTRY_NAME, DETAILS)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.GovernanceAppsPages.RequestManager import RequestManager
from Web.AdminConsole.GovernanceAppsPages.ReviewRequest import ReviewRequest
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure,
                                   CVWebAutomationException)
from Web.Common.page_object import TestStep, handle_testcase_exception

WAIT_TIME = 1 * 60
RM_CONFIG_DATA = get_config().DynamicIndex.RequestManager


class TestCase(CVTestCase):
    """Class for executing edge cases for review action requests"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Edge cases for review action requests"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "HostNameToAnalyze": None,
            "FileServerLocalDirectoryPath": None
        }
        # Testcase constants
        self.plan_name = None
        self.project_name = None
        self.file_server_display_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.test_case_error = None
        self.gdpr_base = None
        self.local_path = None

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        partial_path = os.path.splitdrive(self.local_path)[1]
        self.activateutils.sensitive_data_generation(
            self.source_machine.get_unc_path(partial_path), number_files=15)

    def get_sensitive_file_details(self):
        """
            Get the sensitive file with entity
        """
        filename = os.path.join(AUTOMATION_BIN_PATH)
        database_file_path = "{0}\\Entity.db".format(filename)
        self.sensitive_file, self.entity_value = self.activateutils.get_sensitive_content_details(FILE_SYSTEM,
                                                                                                  ENTITY_EMAIL,
                                                                                                  database_file_path,
                                                                                                  DB_ENTITY_DELIMITER)
        self.sensitive_file = os.path.basename(self.sensitive_file)
        if self.sensitive_file.__eq__(""):
            raise CVTestStepFailure(
                'Test DB does not contain any row with email entity')

    def navigate_to_request_manager(self):
        """Navigates to Request Manager"""
        self.navigator.navigate_to_governance_apps()
        self.app.select_request_manager()

    def navigate_to_datasource_review(self):
        """Navigates to the datasource review page"""
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.search_for_project(
            self.project_name)
        self.gdpr_base.file_server_lookup_obj.navigate_to_project_details(
            self.project_name)
        self.gdpr_base.file_server_lookup_obj.select_data_source_panel()
        self.gdpr_base.file_server_lookup_obj.select_review(
            self.file_server_display_name)
        self.admin_console.access_tab(
            self.admin_console.props['label.review'])

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            self.username = self.inputJSONnode['commcell']['commcellUsername']
            self.password = self.inputJSONnode['commcell']['commcellPassword']
            self.activateutils = ActivateUtils()
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.request_name = f'{self.id}_request'
            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                commcell_object=self.commcell)
            self.generate_sensitive_data()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.username, password=self.password)
            self.request_manager = RequestManager(self.admin_console)
            self.review_obj = ReviewRequest(self.admin_console)
            self.app = GovernanceApps(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)
            self.cleanup()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_plan(self):
        """
            Creates a plan
        """
        self.navigator.navigate_to_plan()
        self.gdpr_base.plans_obj.create_data_classification_plan(self.plan_name, self.tcinputs[
            'IndexServerName'], self.tcinputs['ContentAnalyzer'], None, select_all=True)

    @test_step
    def create_sdg_project(self):
        """
            Creates a project and runs analysis
        """
        self.gdpr_base.testdata_path = self.local_path
        self.gdpr_base.data_source_name = self.file_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)
        path = self.tcinputs['HostNameToAnalyze']+"\\"+self.local_path
        self.gdpr_base.file_server_lookup_obj.select_add_data_source()
        self.gdpr_base.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], HOST_NAME,
            self.file_server_display_name, USA_COUNTRY_NAME,
            path, agent_installed=True, live_crawl=True
        )
        self.log.info(f"Sleeping for: {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise CVTestStepFailure("Could not complete the datasource scan.")
        self.log.info(f"Sleeping for {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)

    @test_step
    def validate_review_action(self):
        """
        Checks edge cases for ignore files review request
        """
        try:
            approver = RM_CONFIG_DATA.Approver
            reviewer = RM_CONFIG_DATA.Reviewer
            reviewer_password = RM_CONFIG_DATA.ReviewerPassword

            self.navigate_to_datasource_review()
            # Perform ignore files review action
            self.gdpr_base.data_source_review_obj.review_ignore_files_action(
                self.sensitive_file, review_request=True, request_name=self.request_name, reviewer=reviewer,
                approver=approver
            )

            try:
                self.gdpr_base.data_source_review_obj.review_ignore_files_action(
                    self.sensitive_file, review_request=True, request_name=self.request_name, reviewer=reviewer,
                    approver=approver
                )
            except:
                self.log.info("A request with the given name already exists")
            self.admin_console.refresh_page()
            self.log.info("Deleting the already existing request.")
            self.navigate_to_request_manager()
            self.request_manager.delete.delete_request(self.request_name)
            try:
                self.navigate_to_datasource_review()
                self.gdpr_base.data_source_review_obj.review_ignore_files_action(
                    self.sensitive_file, review_request=True, request_name=self.request_name, reviewer=reviewer,
                    approver=approver
                )
            except:
                raise CVTestStepFailure("Can't add a new request")
            self.admin_console.logout()
            # Review the request
            self.admin_console.login(
                username=reviewer, password=reviewer_password)
            self.navigate_to_request_manager()
            self.request_manager.click_request_action(self.request_name, DETAILS)
            files_list = RPanelInfo(
                self.admin_console, CRITERIA).get_overflow_items()
            files_list.sort()
            self.log.info(f"Files present in the criteria {files_list}")
            self.log.info(f"Sensitive files chosen {self.sensitive_file}")
            if(files_list != [self.sensitive_file]):
                raise CVWebAutomationException("Criteria doesn't match")
            self.navigate_to_request_manager()
            self.request_manager.select_request_by_name(self.request_name) 
            num_files = len(
                self.review_obj.get_file_names())
            if(num_files) != 1:
                raise CVTestStepFailure(
                    "Review request contains more number of files than added")

        except CVWebAutomationException as error_status:
            self.test_case_error = f"Ignore files action failed: {error_status}"
            raise CVTestStepFailure("Ignore files review action failed.")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.gdpr_base.cleanup(
            self.project_name,
            plan_name=self.plan_name, pseudo_client_name=self.file_server_display_name,
            review_request=[self.request_name])

    def run(self):
        try:
            self.init_tc()
            self.get_sensitive_file_details()
            self.create_plan()
            self.create_sdg_project()
            self.validate_review_action()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)