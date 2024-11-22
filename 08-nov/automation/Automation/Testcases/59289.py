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

    navigate_to_datasource()                     --  Navigates to the datasource panel

    init_tc()                                    --  Initial configuration for the testcase

    create_plan()                                --  Creates a plan

    create_sda_project()                         --  Creates a project and runs analysis

    review_delete_action_filesystem()            -- Deletes a file for a FS datasource and verifies this operation

    review_delete_action_full_crawl_filesystem() -- Verifies the delete operation by running a full crawl

    cleanup()                                    -- Runs cleanup

    run()                                        --  Run function for this testcase
"""
import os
import time

from cvpysdk.job import Job

import dynamicindex.utils.constants as cs
from AutomationUtils.constants import AUTOMATION_BIN_PATH
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure,
                                   CVWebAutomationException)
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing Delete action in Review page for a single file with local path"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Delete action for a single file with local path in Review page in SDG"
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
        self.sensitive_file = None
        self.file_count_before_review = 0
        self.file_count_after_review = 0

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        partial_path = os.path.splitdrive(self.local_path)[1]
        self.activateutils.sensitive_data_generation(
            self.source_machine.get_unc_path(partial_path), number_files=10)

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

    def navigate_to_datasource(self):
        """Navigates to the datasource panel"""
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.search_for_project(
            self.project_name)
        self.gdpr_base.file_server_lookup_obj.navigate_to_project_details(
            self.project_name)
        self.gdpr_base.file_server_lookup_obj.select_data_source_panel()

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']
            self.activateutils = ActivateUtils()
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                commcell_object=self.commcell)
            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=username, password=password)
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
    def create_sda_project(self):
        """
            Creates a project and runs analysis
        """
        self.gdpr_base.testdata_path = self.local_path
        self.gdpr_base.data_source_name = self.file_server_display_name
        path = self.tcinputs['HostNameToAnalyze']+"\\"+self.local_path
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)
        self.gdpr_base.file_server_lookup_obj.select_add_data_source()
        self.gdpr_base.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], cs.HOST_NAME,
            self.file_server_display_name, cs.USA_COUNTRY_NAME,
            path, agent_installed=True, live_crawl=True
        )
        self.log.info(f"Sleeping for: {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise CVTestStepFailure("Could not complete the Datasource scan.")
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)

    @test_step
    def review_delete_action_filesystem(self):
        """
        Performs delete action on a file for a FS datasource and verifies that the file is deleted
        """
        try:
            self.log.info(f"Sensitive data is available at: {self.local_path}")
            self.log.info(f"File to be deleted: {self.sensitive_file}")
            files_before_review = self.source_machine.get_files_in_path(
                self.local_path)
            self.file_count_before_review = len(files_before_review)
            # Note down the details of the last run job
            job_details = self.gdpr_base.get_latest_job_by_operation(
                cs.DELETE_FILES)
            # Perform delete review action
            self.navigate_to_datasource()
            self.gdpr_base.file_server_lookup_obj.select_review(
                self.file_server_display_name)
            self.admin_console.access_tab(
                self.admin_console.props['label.review'])

            status = self.gdpr_base.data_source_review_obj.review_delete_action(
                self.sensitive_file)

            if not status:
                raise CVTestStepFailure("Delete files review action failed.")
            running_job_details = self.gdpr_base.get_latest_job_by_operation(
                cs.DELETE_FILES)
            self.jobID = running_job_details.get("Id")
            self.log.info(f"Running job details {running_job_details}")
            if (job_details and running_job_details[cs.ID] == job_details[cs.ID]):
                raise CVWebAutomationException(
                    "No delete retention remediation action job was launched ")

            job = Job(self.commcell, running_job_details[cs.ID])
            self.log.info("Waiting for the job to complete.")
            job_finished = job.wait_for_completion()

            self.log.info(f"Job finished status {job_finished}")
            if not job_finished:
                raise CVTestStepFailure("Job wasn't successful.")
            files_after_review = self.source_machine.get_files_in_path(
                self.local_path)
            # Checking if the delete file is present in the source directory
            if self.sensitive_file in (files_after_review):
                self.log.info(
                    f"Deleted file {self.sensitive_file} is still present in the source directory {self.local_path}")
                raise CVTestStepFailure
            self.file_count_after_review = len(files_after_review)
            self.log.info(
                f"Number of files present before the delete operation: {self.file_count_before_review}")
            self.log.info(
                f"Number of files left after the delete operation: {self.file_count_after_review}")
            if self.file_count_after_review == self.file_count_before_review - 1:
                self.log.info(
                    f"Successfully deleted {self.sensitive_file} from {self.local_path}")
            else:
                raise CVTestStepFailure("Delete file count doesn't match")
        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f'Delete action failed:- {str(error_status)}'

    @test_step
    def review_delete_action_full_crawl_filesystem(self):
        """
        Verifies that the deleted file is not getting picked during a full crawl
        """
        self.log.info(
            f"Starting a full re-crawl of the datasource {self.file_server_display_name}")
        self.navigate_to_datasource()
        self.gdpr_base.file_server_lookup_obj.start_data_collection(self.file_server_display_name,
                                                                    'full')
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete the Datasource scan.")
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        self.file_count_after_review = int(self.gdpr_base.data_source_discover_obj.
                                           get_total_number_after_crawl())
        self.log.info(
            f"Number of files before the Delete operation {self.file_count_before_review}, "
            f"Number of files after the Delete operation {self.file_count_after_review}")
        if self.file_count_before_review - 1 != self.file_count_after_review:
            self.test_case_error = ("Delete operation failed.")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.gdpr_base.cleanup(
            self.project_name,
            plan_name=self.plan_name, pseudo_client_name=self.file_server_display_name)

    def run(self):
        try:
            self.init_tc()
            self.generate_sensitive_data()
            self.get_sensitive_file_details()
            self.create_plan()
            self.create_sda_project()
            self.review_delete_action_filesystem()
            self.review_delete_action_full_crawl_filesystem()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
