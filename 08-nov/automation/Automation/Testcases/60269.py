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

    navigate_to_datasource_review()              -- Navigates to the datasource review page 
    
    init_tc()                                    -- Initial configuration for the testcase

    create_plan()                                -- Creates a plan

    create_sdg_project()                         -- Creates a project and runs analysis

    review_setretention_action_filesystem()      -- Verifies that retention is getting set on a file

    cleanup()                                    -- Runs cleanup

    teardown()                                   -- Final teardown

    run()                                        -- Run function for this testcase
"""
import os
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.constants import AUTOMATION_BIN_PATH, PASSED
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
    """Class for executing set retention action for a single file with local path in Review page in SDG"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Set retention action for a single file with local path in Review page in SDG"
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
        self.activateutils = None
        self.rehydrator = None
        self.is_plan_created = None
        self.is_project_created = None

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        partial_path = os.path.splitdrive(
            self.local_path)[1]
        self.activateutils.sensitive_data_generation(
            self.source_machine.get_unc_path(partial_path), number_files=15)

    def get_sensitive_file_details(self):
        """
            Get the sensitive file with entity
        """
        filename = os.path.join(AUTOMATION_BIN_PATH)
        database_file_path = "{0}\\Entity.db".format(filename)
        self.sensitive_file, _ = self.activateutils.get_sensitive_content_details(cs.FILE_SYSTEM,
                                                                                  cs.ENTITY_EMAIL,
                                                                                  database_file_path,
                                                                                  cs.DB_ENTITY_DELIMITER)
        self.sensitive_file = os.path.basename(self.sensitive_file)
        if self.sensitive_file.__eq__(""):
            raise CVTestStepFailure(
                'Test DB does not contain any row with email entity')

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
            self.activateutils = ActivateUtils()
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.rehydrator = Rehydrator(self.id)
            self.is_plan_created = self.rehydrator.bucket("plan_created")
            self.is_project_created = self.rehydrator.bucket("project_created")
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
            self.log.info("Using the plan which was created in the last run.")
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
        if self.is_project_created.get():
            self.log.info(
                "Using the project which was created in the last run.")
        else:
            path = self.tcinputs['HostNameToAnalyze']+"\\"+self.local_path
            self.navigator.navigate_to_governance_apps()
            self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
            self.gdpr_base.file_server_lookup_obj.add_project(
                self.project_name, self.plan_name,)
            self.gdpr_base.file_server_lookup_obj.select_add_data_source()
            self.gdpr_base.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], cs.HOST_NAME,
                self.file_server_display_name, cs.USA_COUNTRY_NAME,
                path, agent_installed=True, live_crawl=True
            )
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
        Verifies that retention is getting set on a file in the review page
        """
        try:
            # Note down the details of the last run job
            job_details = self.gdpr_base.get_latest_job_by_operation(
                cs.SET_RETENTION)
            # Perform set retention review action
            self.navigate_to_datasource_review()
            status = self.gdpr_base.data_source_review_obj.review_set_retention_action(
                self.sensitive_file, cs.ONE_MONTH
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
            self.get_sensitive_file_details()
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