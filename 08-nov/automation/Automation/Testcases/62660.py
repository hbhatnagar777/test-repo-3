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

    delete_files_in_folder()                     -- Traverses the folder to delete all the files present

    navigate_to_ds_review()                      -- Navigates to the datasource review page

    init_tc()                                    -- Initial configuration for the testcase

    create_plan()                                -- Creates a plan

    create_sdg_project()                         -- Creates a project and runs analysis

    review_request()                             -- Reviews a request in request manager

    validate_move_action()                       -- Validates the move operation

    review_move_action_filesystem()              -- Moves a file from a FS datasource

    review_move_action_full_crawl_filesystem()   -- Verifies the move operation by running a full crawl

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
    """Class for executing Move action in Review page for a single file with local path"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Move action for a single file with local path in Review page in SDG"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "HostNameToAnalyze": None,
            "FileServerLocalDirectoryPath": None,
            "DestinationPathUserName": None,
            "DestinationPathPassword": None,
            "DestinationPath": None

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
            self.source_machine.get_unc_path(partial_path), number_files=50)

    def get_sensitive_file_details(self):
        """
            Get the sensitive file with entity
        """
        filename = os.path.join(AUTOMATION_BIN_PATH)
        database_file_path = f"{filename}\\Entity.db"
        self.sensitive_file, _ = self.activateutils.get_sensitive_content_details(cs.FILE_SYSTEM,
                                                                                  cs.ENTITY_EMAIL,
                                                                                  database_file_path,
                                                                                  cs.DB_ENTITY_DELIMITER)
        if self.sensitive_file.__eq__(""):
            raise CVTestStepFailure(
                'Test DB does not contain any row with email entity')
        self.sensitive_file = os.path.basename(self.sensitive_file)

    def delete_files_in_folder(self, destination_path):
        """Traverses the destination path to delete all the files present"""
        for root, dirs, files in os.walk(destination_path):
            for file in files:
                os.remove(os.path.join(root, file))

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
            self.owner_user = self.inputJSONnode['commcell']['commcellUsername']
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
    def review_request(self):
        """Reviews a request in request manager"""
        self.review_obj.review_approve_request(
            self.request_name, [self.sensitive_file])

    @test_step
    def validate_move_action(self):
        """
        Validates the move operation
        """
        destination_path = self.tcinputs["DestinationPath"]
        username = self.tcinputs["DestinationPathUserName"]
        password = self.tcinputs["DestinationPathPassword"]
        count_after_move = 0
        source_file_present = False

        # Get the machine name from the shared folder path
        machine_name = destination_path.removeprefix(os.path.sep*2).split(os.path.sep)[0]
        try:
            self.log.info(f"Destination machine name is {machine_name}")
            destination_machine = Machine(machine_name,
                                          username=username,
                                          password=password)
            # Check if the moved file is present in the source path
            source_files = self.source_machine.get_files_in_path(
                self.local_path)
            self.log.info(
                f"List of files present in the source path {source_files}")
            for file in source_files:
                if self.sensitive_file in file:
                    source_file_present = True
            # Check if the moved file is present in the destination path
            destination_files = destination_machine.get_files_in_path(
                destination_path)
            count_after_move = len(destination_files)
            self.log.info(
                f"List of files in the destination path {destination_files}")
            self.log.info(
                f"Number of files present in the destination path after the operation: {count_after_move}")
            # Check that the destination path's file count is increased
            destination_file = os.path.basename(destination_files[0])
            if count_after_move == 1 and \
               self.sensitive_file == destination_file and (not source_file_present):
                self.log.info(
                    f"Successfully moved {self.sensitive_file} to {destination_path}")
            else:
                raise CVTestStepFailure("Count doesn't match")
        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f'Move action failed:- {str(error_status)}'
            raise CVTestStepFailure(
                f'Move action failed:- {str(error_status)}')

    @test_step
    def review_move_action_filesystem(self):
        """
        Applies move action on the files 
        """

        destination_path = self.tcinputs["DestinationPath"]
        username = self.tcinputs["DestinationPathUserName"]
        password = self.tcinputs["DestinationPathPassword"]
        approver = RM_CONFIG_DATA.Approver
        reviewer = RM_CONFIG_DATA.Reviewer
        approver_password = RM_CONFIG_DATA.ApproverPassword
        reviewer_password = RM_CONFIG_DATA.ReviewerPassword
        jobs = Jobs(self.admin_console)

        try:

            # Note down the details of an already running job
            self.navigator.navigate_to_jobs()
            job_details = jobs.get_latest_job_by_operation(cs.MOVE_FILES)
            self.navigate_to_ds_review()
            self.reviewed_files = self.gdpr_base.data_source_review_obj.get_file_names()

            # Perform move review action
            status = self.gdpr_base.data_source_review_obj.review_move_action(
                self.sensitive_file, destination_path, username, password, review_request=True,
                request_name=self.request_name, reviewer=reviewer,
                approver=approver)

            self.gdpr_base.validate_review_request(request_name=self.request_name,
                                                   reviewer=reviewer,
                                                   reviewer_password=reviewer_password,
                                                   owner_user=self.owner_user,
                                                   owner_password=self.owner_password,
                                                   approver=approver,
                                                   approver_password=approver_password,
                                                   files=[self.sensitive_file])

            self.navigator.navigate_to_jobs()
            running_job_details = jobs.get_latest_job_by_operation(
                cs.MOVE_FILES)
            job_status = running_job_details[cs.STATUS]
            if not status or job_details and running_job_details[cs.ID] == job_details[cs.ID] \
                    or job_status != cs.COMPLETED:
                raise CVTestStepFailure("Job wasn't successful.")

        except (CVWebAutomationException) as error_status:
            self.test_case_error = f'Move action failed:- {str(error_status)}'
            raise CVTestStepFailure(
                f'Move action failed:- {str(error_status)}')

    @test_step
    def review_move_action_full_crawl_filesystem(self):
        """
        Verifies that the moved file is not getting picked during a full crawl
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
            f"Number of files before the Move operation {self.file_count_before_review}"
            f"Number of files after the Move operation {file_count_after_review}")
        if self.file_count_before_review - 1 != file_count_after_review:
            self.test_case_error = ("Move operation failed.")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.delete_files_in_folder(self.tcinputs["DestinationPath"])
        self.gdpr_base.cleanup(
            self.project_name,
            plan_name=self.plan_name, pseudo_client_name=self.file_server_display_name,
            review_request=[self.request_name])

    def run(self):
        try:
            self.init_tc()
            self.generate_sensitive_data()
            self.get_sensitive_file_details()
            self.create_plan()
            self.create_sdg_project()
            self.review_move_action_filesystem()
            self.review_move_action_full_crawl_filesystem()
            self.validate_move_action()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)