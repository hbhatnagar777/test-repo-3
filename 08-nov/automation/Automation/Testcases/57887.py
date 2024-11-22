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

    navigate_to_datasource()                     -- Navigates to the datasource panel

    init_tc()                                    -- Initial configuration for the testcase

    create_plan()                                -- Creates a plan

    create_sda_project()                         -- Creates a project and runs analysis

    review_move_action_filesystem()              -- Moves a file from a FS datasource and verifies the operation

    review_move_action_full_crawl_filesystem()   -- Verifies the move operation by running a full crawl

    cleanup()                                    -- Runs cleanup

    run()                                        -- Run function for this testcase
"""
import os
import time

from cvpysdk.job import Job

import dynamicindex.utils.constants as cs
from AutomationUtils.constants import AUTOMATION_BIN_PATH
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure,
                                   CVWebAutomationException)
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing Move action in Review page for a file"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance test for Move action in Review page in AdminConsole"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "DestinationPath": None,
            "AccessNode": None,
            "Inventory": None
        }
        # Testcase constants
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.file_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.test_case_error = None
        self.gdpr_base = None
        self.sensitive_file = None
        self.file_count_before_review = 0

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        self.activateutils.sensitive_data_generation(
            self.tcinputs['FileServerDirectoryPath'], number_files=10)

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
        self.sensitive_file = os.path.basename(self.sensitive_file)
        if self.sensitive_file.__eq__(""):
            raise CVTestStepFailure(
                'Test DB does not contain any row with email entity')

    def delete_files_in_folder(self, destination_path):
        for root, dirs, files in os.walk(destination_path):
            for file in files:
                os.remove(os.path.join(root, file))

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
            self.activateutils = ActivateUtils()
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.inventory_name = self.tcinputs['Inventory']
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
            'IndexServerName'], self.tcinputs['ContentAnalyzer'],
            None, select_all=True)

    @test_step
    def create_sda_project(self):
        """
            Creates a project and runs analysis
        """
        self.gdpr_base.testdata_path = self.tcinputs['FileServerDirectoryPath']
        self.gdpr_base.data_source_name = self.file_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)
        self.gdpr_base.file_server_lookup_obj.select_add_data_source()
        self.gdpr_base.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], cs.HOST_NAME,
            self.file_server_display_name, cs.USA_COUNTRY_NAME,
            self.tcinputs['FileServerDirectoryPath'],
            username=self.tcinputs['FileServerUserName'],
            password=self.tcinputs['FileServerPassword'], access_node=self.tcinputs['AccessNode'], inventory_name=self.inventory_name)
        self.log.info(f"Sleeping for: {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise CVTestStepFailure("Could not complete Data Source scan.")
        self.log.info(f"Sleeping for: {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        self.file_count_before_review = int(self.gdpr_base.data_source_discover_obj.
                                            get_total_number_after_crawl())

    @test_step
    def review_move_action_filesystem(self):
        """
        Performs move action on a file for a FS datasource and verifies that the file is moved to the destination path
        """
        file_count_destination = 0
        destination_path = self.tcinputs["DestinationPath"]
        try:
            # Note down the details of the last run job
            job_details = self.gdpr_base.get_latest_job_by_operation(
                cs.MOVE_FILES)
            # Perform move review action
            self.navigate_to_datasource()
            self.gdpr_base.file_server_lookup_obj.select_review(
                self.file_server_display_name)
            self.admin_console.access_tab(
                self.admin_console.props['label.review'])

            status = self.gdpr_base.data_source_review_obj.review_move_action(
                self.sensitive_file, destination_path, credentials=self.tcinputs['Credentials'])

            if not status:
                raise CVTestStepFailure("Move files review action failed.")
            running_job_details = self.gdpr_base.get_latest_job_by_operation(
                cs.MOVE_FILES)
            self.jobID = running_job_details.get("Id")
            self.log.info(f"Running job details {running_job_details}")
            if (job_details and running_job_details[cs.ID] == job_details[cs.ID]):
                raise CVWebAutomationException(
                    "No move retention remediation action job was launched ")

            job = Job(self.commcell, running_job_details[cs.ID])
            self.log.info("Waiting for the job to complete.")
            job_finished = job.wait_for_completion()

            self.log.info(f"Job finished status {job_finished}")
            if not job_finished:
                raise CVTestStepFailure("Job wasn't successful.")

            file_count_destination = sum([len(files)
                                          for r, d, files in os.walk(destination_path)])
            self.log.info(
                f"Number of files left after the move operation {file_count_destination}")
            if file_count_destination == 1:
                self.log.info(
                    f"Successfully moved {self.sensitive_file} to {destination_path}")
            else:
                raise CVTestStepFailure("Move file count doesn't match")
        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f'Move action failed:- {str(error_status)}'

    @test_step
    def review_move_action_full_crawl_filesystem(self):
        """
        Verifies that the moved file is not getting picked during a full crawl
        """
        self.log.info("Starting a full re-crawl of the datasource [%s]",
                      self.file_server_display_name)
        self.navigate_to_datasource()
        self.gdpr_base.file_server_lookup_obj.start_data_collection(
            self.file_server_display_name, 'full')
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete Datasource scan.")
        self.log.info(f"Sleeping for: {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        file_count_after_review = int(self.gdpr_base.data_source_discover_obj.
                                      get_total_number_after_crawl())
        if self.file_count_before_review - 1 != file_count_after_review:
            self.log.info(
                f"Number of files before move operation {self.file_count_before_review}, "
                f"Number of files after move operation {file_count_after_review}")
            self.test_case_error = (
                f"Number of files before move operation {self.file_count_before_review}, number of files after move operation {file_count_after_review}."
                "Move operation failed.")
        else:
            self.log.info(
                f"Number of files before performing Move operation {self.file_count_before_review}, "
                f"Number of files after performing Move operation {file_count_after_review}"
            )

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.gdpr_base.cleanup(
            self.project_name,
            plan_name=self.plan_name, pseudo_client_name=self.file_server_display_name)
        self.delete_files_in_folder(self.tcinputs["DestinationPath"])

    def run(self):
        try:
            self.init_tc()
            self.generate_sensitive_data()
            self.get_sensitive_file_details()
            self.create_plan()
            self.create_sda_project()
            self.review_move_action_filesystem()
            self.review_move_action_full_crawl_filesystem()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
