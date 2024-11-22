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
    __init__()                                   --  Initializes TestCase class

    generate_sensitive_data()                    --  Generates sensitive files with PII entities

    validate_review_action()                     -- Validates whether the file got ignored

    navigate_to_request_manager()                -- Navigates to Request Manager

    navigate_to_ds_review()                      -- Navigates to the datasource review page

    init_tc()                                    --  Initial configuration for the testcase

    create_plan()                                --  Creates a plan

    create_sdg_project()                         --  Creates a project and runs analysis

    review_request()                             -- Reviews a request in request manager

    validate_move_action()                       -- Validates the delete operation

    review_request_delete_action_filesystem()    -- Deletes a file with review request

    review_delete_action_full_crawl_filesystem() -- Verifies the delete operation by running a full crawl

    cleanup()                                    -- Runs cleanup

    run()                                        -- Run function for this testcase
"""
import os
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.config import get_config
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
    """Class for executing delete action for multiple file with review request"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Delete action for mulitple files with local path with review request"
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
        self.file_count_before_review = 0
        self.local_path = None

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        partial_path = os.path.splitdrive(
            self.local_path)[1]
        partial_path = partial_path.removeprefix(os.path.sep)
        self.activateutils.sensitive_data_generation(
            self.source_machine.get_unc_path(partial_path))

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

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            self.owner_username = self.inputJSONnode['commcell']['commcellUsername']
            self.owner_password = self.inputJSONnode['commcell']['commcellPassword']
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
                username=self.owner_username, password=self.owner_password)
            self.request_manager = RequestManager(self.admin_console)
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
        self.gdpr_base.file_server_lookup_obj.select_add_data_source()
        self.gdpr_base.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], cs.HOST_NAME,
            self.file_server_display_name, cs.USA_COUNTRY_NAME,
            self.local_path, agent_installed=True, live_crawl=True
        )
        self.log.info(f"Sleeping for: {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise CVTestStepFailure("Could not complete the Datasource scan.")
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        self.file_count_before_review = int(self.gdpr_base.data_source_discover_obj.
                                            get_total_number_after_crawl())

    @test_step
    def validate_delete_action(self):
        """
        Validates the delete operation
        """
        data_dir = self.local_path
        count_reviewed_files = len(self.reviewed_files)
        files_after_review = self.source_machine.get_files_in_path(
            data_dir)
        file_count_after_review = len(files_after_review)
        self.log.info(
            f"No. of files present in the source path before the delete operation: {self.file_count_before_review}")
        self.log.info(
            f"No. of files left in the source path after the delete operation: {file_count_after_review}")
        count_files_left = self.file_count_before_review - count_reviewed_files
        if file_count_after_review == count_files_left:
            self.log.info(f"Successfully deleted all the files")
        else:
            raise CVTestStepFailure(
                f"Delete action failed for {file_count_after_review-count_files_left} files")

    @test_step
    def review_request_delete_action_filesystem(self):
        """
        Performs delete action with review request on files
        """

        approver = RM_CONFIG_DATA.Approver
        reviewer = RM_CONFIG_DATA.Reviewer
        approver_password = RM_CONFIG_DATA.ApproverPassword
        reviewer_password = RM_CONFIG_DATA.ReviewerPassword
        jobs = Jobs(self.admin_console)
        try:
            # Note down the details of an already running job
            self.navigator.navigate_to_jobs()
            job_details = jobs.get_latest_job_by_operation(cs.DELETE_FILES)
            self.navigate_to_ds_review()
            self.reviewed_files = self.gdpr_base.data_source_review_obj.get_file_names()
            # Perform delete review action
            status = self.gdpr_base.data_source_review_obj.review_delete_action(
                '', all_items_in_page=True, review_request=True, request_name=self.request_name, reviewer=reviewer,
                approver=approver)

            self.gdpr_base.validate_review_request(request_name=self.request_name,
                                                   reviewer=reviewer,
                                                   reviewer_password=reviewer_password,
                                                   owner_user=self.owner_username,
                                                   owner_password=self.owner_password,
                                                   approver=approver,
                                                   approver_password=approver_password, files=self.reviewed_files)

            self.navigator.navigate_to_jobs()
            running_job_details = jobs.get_latest_job_by_operation(
                cs.DELETE_FILES)
            job_status = running_job_details[cs.STATUS]
            if not status or job_details and running_job_details[cs.ID] == job_details[cs.ID] \
                    or job_status != cs.COMPLETED:
                raise CVTestStepFailure("Job wasn't successful.")
        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f'Delete action failed:- {str(error_status)}'
            raise CVTestStepFailure(
                f'Delete action failed:- {str(error_status)}')

    @test_step
    def review_request(self):
        """Review a request in request manager"""
        review_obj = ReviewRequest(self.admin_console)
        review_obj.review_approve_request(
            self.request_name, self.reviewed_files)

    @test_step
    def review_delete_action_full_crawl_filesystem(self):
        """
        Verifies that the deleted files are not getting picked during a full crawl
        """
        self.navigate_to_ds_review()
        self.gdpr_base.data_source_discover_obj.select_details()
        self.log.info(
            f"Starting a full re-crawl of the datasource {self.file_server_display_name}")
        self.gdpr_base.data_source_discover_obj.start_data_collection_job(
            'full')
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.navigate_to_project_details(
            self.project_name)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete the Datasource scan.")
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        file_count_after_review = int(self.gdpr_base.data_source_discover_obj.
                                      get_total_number_after_crawl())
        self.log.info(
            f"Number of files before the delete operation {self.file_count_before_review}, "
            f"Number of files after the delete operation {file_count_after_review}")
        if len(self.reviewed_files) != self.file_count_before_review - file_count_after_review:
            self.test_case_error = ("Delete operation failed.")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.gdpr_base.cleanup(
            self.project_name,
            plan_name=self.plan_name, pseudo_client_name=self.file_server_display_name,
            review_request=[self.request_name])

    def navigate_to_request_manager(self):
        self.navigator.navigate_to_governance_apps()
        self.app.select_request_manager()

    def run(self):
        try:
            self.init_tc()
            self.generate_sensitive_data()
            self.create_plan()
            self.create_sdg_project()
            self.review_request_delete_action_filesystem()
            self.review_delete_action_full_crawl_filesystem()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
