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

    navigate_to_datasource_review()              -- Navigates to the datasource review page
    
    init_tc()                                    -- Initial configuration for the testcase

    create_plan()                                -- Creates a plan

    create_sdg_project()                         -- Creates a project and runs analysis

    review_setretention_action_filesystem()      -- Verifies that retention is getting set on files

    cleanup()                                    -- Runs cleanup

    teardown()                                   -- Final teardown

    run()                                        -- Run function for this testcase
"""
import os
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.constants import PASSED
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure,
                                   CVWebAutomationException)
from Web.Common.page_object import TestStep, handle_testcase_exception

from cvpysdk.job import Job


class TestCase(CVTestCase):
    """Class for executing set retention action for files with local path in Review page in SDG"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "set retention action for files with local path in Review page in SDG"
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
        self.rehydrator = None
        self.is_plan_created = None
        self.is_project_created = None

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        activateutils = ActivateUtils()
        partial_path = os.path.splitdrive(
            self.local_path)[1]
        activateutils.sensitive_data_generation(
            self.source_machine.get_unc_path(partial_path), number_files=50)

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
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.rehydrator = Rehydrator(self.id)
            self.is_plan_created = self.rehydrator.bucket("plan_created")
            self.is_project_created = self.rehydrator.bucket("project_created")
            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                commcell_object=self.commcell)
            if not self.is_project_created.get():
                self.generate_sensitive_data()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=username, password=password)
            self.navigator = self.admin_console.navigator
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)
            if self.rehydrator.store_exists():
                self.log.info("Performing the cleanup")
                self.cleanup()
            else:
                self.log.info("Last run was a success.")
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_plan(self):
        """
            Creates a plan
        """
        if self.is_plan_created.get():
            self.log.info("Using the plan that was created in the last run.")
        else:
            self.navigator.navigate_to_plan()
            self.gdpr_base.plans_obj.create_data_classification_plan(self.plan_name, self.tcinputs[
                'IndexServerName'], self.tcinputs['ContentAnalyzer'], None, select_all=True)
        self.is_plan_created.set(True)

    @test_step
    def create_sdg_project(self):
        """
            Creates a project and runs analysis
        """
        self.gdpr_base.testdata_path = self.local_path
        self.gdpr_base.data_source_name = self.file_server_display_name
        path = self.tcinputs['HostNameToAnalyze']+"\\"+self.local_path
        if self.is_project_created.get():
            self.log.info(
                "Using the project which was created in the last run.")
        else:
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
                raise CVTestStepFailure(
                    "Could not complete the datasource scan.")
            self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
            time.sleep(cs.ONE_MINUTE)
        self.is_project_created.set(True)

    @test_step
    def review_setretention_action_filesystem(self):
        """
        Verifies that retention is getting set on files in the review page
        """
        try:
            # Note down the details of the last run job
            job_details = self.gdpr_base.get_latest_job_by_operation(
                cs.SET_RETENTION)
            # Perform set retention review action
            self.navigate_to_datasource_review()
            status = self.gdpr_base.data_source_review_obj.review_set_retention_action(
                '', cs.ONE_MONTH, all_items_in_page=True
            )
            if not status:
                raise CVTestStepFailure("Set retention review action failed.")
            running_job_details = self.gdpr_base.get_latest_job_by_operation(
                cs.SET_RETENTION)
            self.log.info(f"Running job details {running_job_details}")
            if (job_details and running_job_details[cs.ID] == job_details[cs.ID]):
                raise CVWebAutomationException(
                    "No set retention remediation action job was launched ")
            job = Job(self.commcell, running_job_details[cs.ID])
            self.log.info("Waiting for the job to complete.")
            job_finished = job.wait_for_completion()

            self.log.info(f"Job finished status {job_finished}")
            if not job_finished:
                raise CVWebAutomationException("Job wasn't successful.")
            risk_present = True
            # Refresh the page
            self.admin_console.refresh_page()
            # Verify that the action is getting applied only on intended files
            reviewed_files = self.gdpr_base.data_source_review_obj.get_file_names()
            all_files = self.source_machine.get_files_in_path(
                self.local_path)
            self.log.info(
                f"Files present in the review page are {reviewed_files}")
            for file in all_files:
                # Check that the action didn't get applied on an unintended file
                filename = os.path.basename(file)
                if filename not in reviewed_files:
                    self.log.info(f"Checking for risks in file {filename}")
                    self.gdpr_base.data_source_review_obj.search_file(filename)
                    if self.gdpr_base.data_source_review_obj.get_total_records() > 0:
                        risk_present = self.gdpr_base.data_source_review_obj.risks_present(
                            filename, [cs.RETENTION_NOT_SET])
                        if not risk_present:
                            raise CVWebAutomationException(
                                "Retention got applied on an unchosen file")

        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f"Set retention action failed: {error_status}"
            raise CVTestStepFailure(
                f"Set retention review action failed - {str(error_status)}")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.log.info(f"Does the plan exists? {self.is_plan_created.get()}")
        self.log.info(f"Does the project exists? {self.is_project_created.get()}")
        self.log.info(f"Does the pseudo client exists? {self.is_project_created.get()}")
        plan_name = None if self.is_plan_created.get() else self.plan_name
        project_name = None if self.is_project_created.get() else self.project_name
        pseudo_client_name = None if self.is_project_created.get(
        ) else self.file_server_display_name
        self.gdpr_base.cleanup(project_name,
                               plan_name=plan_name, pseudo_client_name=pseudo_client_name)

    @test_step
    def teardown(self):
        """
        Final teardown
        """
        if self.status == PASSED:
            self.rehydrator.cleanup()

    def run(self):
        try:
            self.init_tc()
            self.create_plan()
            self.create_sdg_project()
            self.review_setretention_action_filesystem()
            self.cleanup()
            self.teardown()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
