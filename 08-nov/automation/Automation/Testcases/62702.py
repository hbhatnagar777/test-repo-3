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

    validate_review_action()                      -- Validates whether retention got set

    navigate_to_request_manager()                -- Navigates to Request Manager

    navigate_to_ds_review()                      -- Navigates to the datasource review page 

    init_tc()                                    -- Initial configuration for the testcase

    create_inventory()                           -- Create an inventory with a nameserver

    create_plan()                                -- Creates a plan

    create_sdg_project()                         -- Creates a project and runs analysis

    review_setretention_action_filesystem()      -- Applies retention on files with review request

    cleanup()                                    -- Runs cleanup

    run()                                        -- Run function for this testcase
"""
import os
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.config import get_config
from AutomationUtils.constants import AUTOMATION_BIN_PATH
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.GovernanceAppsPages.RequestManager import RequestManager
from Web.AdminConsole.GovernanceAppsPages.ReviewRequest import ReviewRequest
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure,
                                   CVWebAutomationException)
from Web.Common.page_object import TestStep, handle_testcase_exception

RM_CONFIG_DATA = get_config().DynamicIndex.RequestManager


class TestCase(CVTestCase):
    """Class for executing set retention action for file with review request in SDG"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Set retention action with review request for file with local path"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerLocalDirectoryPath": None

        }
        # Testcase constants
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.file_server_display_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.test_case_error = None
        self.gdpr_base = None
        self.local_path = None
        self.activateutils = None

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        partial_path = os.path.splitdrive(
            self.local_path)[1]
        partial_path = partial_path.removeprefix(os.path.sep)
        self.activateutils.sensitive_data_generation(
            self.source_machine.get_unc_path(partial_path), number_files=50)

    def navigate_to_request_manager(self):
        """Navigates to Request Manager"""
        self.navigator.navigate_to_governance_apps()
        self.app.select_request_manager()

    def navigate_to_ds_review(self):
        """Navigates to the datasource review page"""
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.search_for_project(
            self.project_name)
        self.gdpr_base.file_server_lookup_obj.navigate_to_project_details(
            self.project_name)
        self.gdpr_base.file_server_lookup_obj.select_data_source(
            self.file_server_display_name)
        self.gdpr_base.data_source_discover_obj.select_review()

    def get_sensitive_file_details(self):
        """
            Get the sensitive file with entity
        """
        filename = os.path.join(AUTOMATION_BIN_PATH)
        database_file_path = f"{filename}\\Entity.db"
        self.sensitive_file, self.entity_value = self.activateutils.get_sensitive_content_details(cs.FILE_SYSTEM,
                                                                                                  cs.ENTITY_EMAIL,
                                                                                                  database_file_path,
                                                                                                  cs.DB_ENTITY_DELIMITER)
        self.sensitive_file = os.path.basename(self.sensitive_file)
        if self.sensitive_file.__eq__(""):
            raise CVTestStepFailure(
                'Test DB does not contain any row with email entity')

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            self.owner_user = self.inputJSONnode['commcell']['commcellUsername']
            self.owner_password = self.inputJSONnode['commcell']['commcellPassword']
            self.activateutils = ActivateUtils()
            self.inventory_name = f'{self.id}_inventory'
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.request_name = f'{self.id}_request'
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                commcell_object=self.commcell)
            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.generate_sensitive_data()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.owner_user, password=self.owner_password)
            self.request_manager = RequestManager(self.admin_console)
            self.review_obj = ReviewRequest(self.admin_console)
            self.app = GovernanceApps(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)
            self.cleanup()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_inventory(self):
        """
            Create an inventory with a nameserver
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_inventory_manager()
        self.gdpr_base.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])

        self.gdpr_base.inventory_details_obj.add_asset_name_server(
            self.tcinputs["NameServerAsset"])
        self.admin_console.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds.")
        time.sleep(cs.ONE_MINUTE)
        if not self.gdpr_base.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete the asset scan.")

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
        self.gdpr_base.file_server_lookup_obj.select_add_data_source()
        self.gdpr_base.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], cs.HOST_NAME,
            self.file_server_display_name, cs.USA_COUNTRY_NAME,
            self.local_path, agent_installed=True, live_crawl=True,
            inventory_name = self.inventory_name
        )
        self.log.info(f"Sleeping for: {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise CVTestStepFailure("Could not complete the datasource scan.")
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)

    @test_step
    def review_setretention_action_filesystem(self):
        """
        Applies retention action with review request
        """
        try:
            approver = RM_CONFIG_DATA.Approver
            reviewer = RM_CONFIG_DATA.Reviewer
            approver_password = RM_CONFIG_DATA.ApproverPassword
            reviewer_password = RM_CONFIG_DATA.ReviewerPassword
            jobs = Jobs(self.admin_console)
            # Note down the details of an already running job
            self.navigator.navigate_to_jobs()
            job_details = jobs.get_latest_job_by_operation(cs.SET_RETENTION)
            # Perform set retention review action
            self.navigate_to_ds_review()
            status = self.gdpr_base.data_source_review_obj.review_set_retention_action(
                self.sensitive_file, cs.ONE_MONTH, review_request=True, request_name=self.request_name, reviewer=reviewer,
                approver=approver
            )

            self.gdpr_base.validate_review_request(request_name=self.request_name,
                                                   reviewer=reviewer,
                                                   reviewer_password=reviewer_password,
                                                   owner_user=self.owner_user,
                                                   owner_password=self.owner_password,
                                                   approver=approver,
                                                   approver_password=approver_password, files=[self.sensitive_file])
            self.navigator.navigate_to_jobs()
            running_job_details = jobs.get_latest_job_by_operation(
                cs.SET_RETENTION)
            job_status = running_job_details[cs.STATUS]
            if not status or job_details and running_job_details[cs.ID] == job_details[cs.ID] \
                    or job_status != cs.COMPLETED:
                raise CVTestStepFailure("Job wasn't successful.")

        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f"Set retention action failed: {error_status}"
            raise CVTestStepFailure(
                f'Set retention action failed:- {str(error_status)}')

    @test_step
    def validate_review_action(self):
        """Validates whether retention got applied
        Raises:
            Exception:
                If the retention risk is present
        """
        self.navigate_to_ds_review()
        # Check that the action got applied on an intended file

        risk_present = self.gdpr_base.data_source_review_obj.risks_present(
            self.sensitive_file, [cs.SET_RETENTION])

        if risk_present:
            raise CVWebAutomationException(
                "Retention didn't get applied on the chosen file")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.gdpr_base.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name, pseudo_client_name=self.file_server_display_name,
            review_request=[self.request_name])

    def run(self):
        try:
            self.init_tc()
            self.get_sensitive_file_details()
            self.create_inventory()
            self.create_plan()
            self.create_sdg_project()
            self.review_setretention_action_filesystem()
            self.validate_review_action()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
