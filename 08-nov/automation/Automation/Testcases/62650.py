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

    get_sensitive_file_details()                 --  Gets a sensitive file with an entity

    init_tc()                                    --  Initial configuration for the testcase

    create_inventory()                           --  Create an inventory with a nameserver

    create_plan()                                --  Creates a plan

    create_sda_project()                         --  Creates a project and runs analysis

    review_request_delete_action_filesystem()    -- Deletes a file for a FS datasource and verifies this operation

    review_delete_action_full_crawl_filesystem() -- Verifies the delete operation by running a full crawl

    cleanup()                                    -- Runs cleanup

    run()                                        --  Run function for this testcase
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
    """Class for executing delete action in for a single file with RM"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Delete action for a single file with local path with request manager in SDG"
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
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.username, password=self.password)
            self.request_manager = RequestManager(self.admin_console)
            self.review_obj = ReviewRequest(self.admin_console)
            self.app = GovernanceApps(self.admin_console)
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)
            self.review = ReviewRequest(self.admin_console)
            self.navigator = self.admin_console.navigator
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

    @test_step
    def review_request_delete_action_filesystem(self):
        """
        Performs delete action on a file with RM and verifies that the file is deleted
        """
        file_count_after_review = 0
        approver = RM_CONFIG_DATA.Approver
        reviewer = RM_CONFIG_DATA.Reviewer
        approver_password = RM_CONFIG_DATA.ApproverPassword
        reviewer_password = RM_CONFIG_DATA.ReviewerPassword
        jobs = Jobs(self.admin_console)
        try:
            # Note down the details of an already running job
            self.navigator.navigate_to_jobs()
            job_details = jobs.get_latest_job_by_operation(cs.DELETE_FILES)
            self.log.info(f"Sensitive data is available at: {self.local_path}")
            self.log.info(f"File to be deleted: {self.sensitive_file}")
            files_before_review = self.source_machine.get_files_in_path(
                self.local_path)
            self.file_count_before_review = len(files_before_review)
            # Create a review request
            self.create_request()
            self.configure_request()
            self.admin_console.logout()
            # Review the request
            self.admin_console.login(
                username=reviewer, password=reviewer_password)
            self.navigate_to_request_manager()
            self.review_request()
            self.admin_console.logout()
            # Request approval
            self.admin_console.login(
                username=self.username, password=self.password)
            self.navigate_to_request_manager()
            self.request_manager.select_request_by_name(self.request_name)
            self.review_obj.request_approval()
            self.admin_console.logout()
            # Approve the request
            self.admin_console.login(
                username=approver, password=approver_password)
            self.navigate_to_request_manager()
            self.review_obj.approve_request(self.request_name)
            self.admin_console.logout()
            self.admin_console.login(
                username=self.username, password=self.password)
            # Track the job
            self.navigator.navigate_to_jobs()
            running_job_details = jobs.get_latest_job_by_operation(
                cs.DELETE_FILES)
            job_status = running_job_details[cs.STATUS]
            if job_details and running_job_details[cs.ID] == job_details[cs.ID] \
                    or job_status != cs.COMPLETED:
                raise CVTestStepFailure("Job wasn't successful.")
            files_after_review = self.source_machine.get_files_in_path(
                self.local_path)
            # Checking if the delete file is present in the source directory
            if self.sensitive_file in (files_after_review):
                self.log.info(
                    f"Deleted file {self.sensitive_file} is present in the source directory")
                raise CVTestStepFailure
            file_count_after_review = len(files_after_review)
            self.log.info(
                f"Number of files before the delete operation: {self.file_count_before_review}")
            self.log.info(
                f"Number of files after the delete operation: {file_count_after_review}")
            if file_count_after_review == self.file_count_before_review - 1:
                self.log.info(
                    f"Successfully deleted {self.sensitive_file} from {self.local_path}")
            else:
                raise CVTestStepFailure
        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f'Delete action failed:- {str(error_status)}'
            raise CVTestStepFailure(
                f'Delete action failed:- {str(error_status)}')

    @test_step
    def create_request(self):
        """Create a request in request manager"""
        _nsuccess = False
        self.navigator.navigate_to_governance_apps()
        self.app.select_request_manager()
        requester = RM_CONFIG_DATA.Requester
        entity_type = cs.ENTITY_EMAIL
        request_type = self.admin_console.props['label.taskmanager.type.delete'].upper(
        )
        _nsuccess = self.request_manager.create.add_request(self.request_name, requester,
                                                            entity_type,
                                                            self.entity_value,
                                                            request_type)
        if not _nsuccess:
            raise CVTestStepFailure(
                f"Request {self.request_name} creation failed")

    @test_step
    def configure_request(self):
        """Configure a request in request manager"""
        _nsuccess = False
        project_name = self.project_name
        approver = RM_CONFIG_DATA.Approver
        reviewer = RM_CONFIG_DATA.Reviewer
        _nsuccess = self.request_manager.configure.assign_reviewer_approver(self.request_name,
                                                                            approver,
                                                                            reviewer, project_name)
        if not _nsuccess:
            if not _nsuccess:
                raise CVTestStepFailure(
                    f"Could not configure request {self.request_name}")

    @test_step
    def review_request(self):
        """Review a request in request manager"""
        self.review_obj.review_approve_request(
            self.request_name, [self.sensitive_file])

    @test_step
    def review_delete_action_full_crawl_filesystem(self):
        """
        Verifies that the deleted file is not getting picked during a full crawl
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.search_for_project(
            self.project_name)
        self.gdpr_base.data_source_discover_obj.navigate_to_project_details(
            self.project_name)
        self.gdpr_base.file_server_lookup_obj.select_data_source(
            self.file_server_display_name)
        self.log.info(
            f"Starting a full re-crawl of the datasource {self.file_server_display_name}")
        self.gdpr_base.data_source_discover_obj.select_details()
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
        if self.file_count_before_review - 1 != file_count_after_review:
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
            self.get_sensitive_file_details()
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
