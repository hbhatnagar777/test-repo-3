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

    delete_files_in_folder()                     -- Traverses the folder to delete all the files present

    navigate_to_datasource()                     -- Navigates to the datasource panel

    init_tc()                                    -- Initial configuration for the testcase

    create_plan()                                -- Creates a plan

    create_sdg_project()                         -- Creates a project and runs analysis

    review_move_action_filesystem()              -- Moves a file from a FS datasource and verifies the operation

    review_move_action_full_crawl_filesystem()   -- Verifies the move operation by running a full crawl

    cleanup()                                    -- Runs cleanup

    run()                                        -- Run function for this testcase
"""
import os
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure,
                                   CVWebAutomationException)
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing move action in review page for all files with local path present on a page"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Move action for all files with local path in a review page in SDG"
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
        self.count_before_review = 0
        self.local_path = None

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        partial_path = os.path.splitdrive(
            self.local_path)[1]
        self.activateutils.sensitive_data_generation(
            self.source_machine.get_unc_path(partial_path), number_files=50)

    def delete_files_in_folder(self, destination_path):
        """Traverses the destination path to delete all the files present"""
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
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']
            self.activateutils = ActivateUtils()
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                commcell_object=self.commcell)
            self.generate_sensitive_data()
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
    def create_sdg_project(self):
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
        self.count_before_review = int(self.gdpr_base.data_source_discover_obj.
                                       get_total_number_after_crawl())
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)

    @test_step
    def review_move_action_filesystem(self):
        """
        Verifies that the file is moved to the destination path correctly after move operation
        """
        count_after_move = 0
        source_file_present = False
        destination_path = self.tcinputs["DestinationPath"]
        username = self.tcinputs["DestinationPathUserName"]
        password = self.tcinputs["DestinationPathPassword"]
        # Get the machine name from the shared folder path
        first_sep_index = destination_path.index(os.path.sep)
        machine_name = destination_path[2:first_sep_index]
        destination_machine = Machine(machine_name,
                                      username=self.tcinputs["DestinationPathUserName"],
                                      password=self.tcinputs["DestinationPathPassword"])
        jobs = Jobs(self.admin_console)

        try:
            self.log.info(f"Destination machine name is {machine_name}")
            self.navigator.navigate_to_jobs()
            job_details = jobs.get_latest_job_by_operation(cs.MOVE_FILES)

            self.navigate_to_datasource()
            self.gdpr_base.file_server_lookup_obj.select_review(
                self.file_server_display_name)
            self.admin_console.access_tab(
                self.admin_console.props['label.review'])
            reviewed_files = self.gdpr_base.data_source_review_obj.get_file_names()
            self.count_reviewed_files = len(reviewed_files)
            # Perform move review action
            status = self.gdpr_base.data_source_review_obj.review_move_action(
                '', destination_path, username, password, all_items_in_page=True)

            # Get the details of the latest job
            self.navigator.navigate_to_jobs()
            running_job_details = jobs.get_latest_job_by_operation(
                cs.MOVE_FILES)
            job_status = running_job_details[cs.STATUS]
            if not status or job_details and running_job_details[cs.ID] == job_details[cs.ID] \
                    or job_status != cs.COMPLETED:
                raise CVTestStepFailure("Job wasn't successful.")

            # Check that the moved file is not present in the source path
            source_files = self.source_machine.get_files_in_path(
                self.local_path)
            self.log.info(
                f"List of files present in the source path {source_files}")
            for file in source_files:
                if any(file in rfile for rfile in reviewed_files):
                    source_file_present = True
                    raise CVTestStepFailure(
                        f"File {file} is present in the source path")
            # Check if the moved file is present in the destination path
            destination_path_files = destination_machine.get_files_in_path(
                destination_path)
            destination_path_filenames = []
            for file in destination_path_files:
                filename = os.path.basename(file)
                destination_path_filenames.append(filename)

            self.log.info("Files present in the destination path")
            self.log.info(destination_path_filenames)
            if destination_path_filenames.sort() != reviewed_files.sort():
                raise CVTestStepFailure(
                    f"Files present in the destination path don't match with the list of files reviewed.")

            count_after_move = len(destination_path_files)
            self.log.info(
                f"List of files present in the destination path {destination_path_files}")
            self.log.info(
                f"No. of files present in the destination path after the move operation: {count_after_move}")
            # Check that the destination path's file count is increased
            if count_after_move == self.count_reviewed_files and (not source_file_present):
                self.log.info(
                    f"Successfully moved all the {self.count_reviewed_files} files to {destination_path}")
            else:
                raise CVTestStepFailure(
                    f"Move action was taken on {self.count_reviewed_files} but destination has {count_after_move} files")
        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f'Move action failed:- {str(error_status)}'
            raise CVTestStepFailure("Move action failed.")

    @test_step
    def review_move_action_full_crawl_filesystem(self):
        """
        Verifies that the moved file is not getting picked during a full crawl
        """
        self.log.info(
            f"Starting a full re-crawl of the datasource {self.file_server_display_name}")
        self.navigate_to_datasource()
        self.gdpr_base.file_server_lookup_obj.start_data_collection(
            self.file_server_display_name, 'full')
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete the Datasource scan.")
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        count_after_review = int(
            self.gdpr_base.data_source_discover_obj.get_total_number_after_crawl())
        self.log.info(
            f"Number of files chosen for review action {self.count_reviewed_files}"
            f"Number of files before the move operation {self.count_before_review}"
            f"Number of files after the move operation {count_after_review}")
        if self.count_reviewed_files != self.count_before_review - count_after_review:
            self.test_case_error = ("Move operation failed.")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.delete_files_in_folder(self.tcinputs["DestinationPath"])
        self.gdpr_base.cleanup(
            self.project_name,
            plan_name=self.plan_name, pseudo_client_name=self.file_server_display_name)

    def run(self):
        try:

            self.init_tc()
            self.create_plan()
            self.create_sdg_project()
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
