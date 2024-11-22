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

    is_test_step_complete()                      --  checks if a test step is complete

    set_test_step_complete()                     --  Sets the progress with a give test step value

    generate_sensitive_data()                    -- Generates sensitive files with PII entities

    navigate_to_datasource()                     -- Navigates to the datasource panel 

    init_tc()                                    -- Initial configuration for the testcase

    create_plan()                                -- Creates a plan

    create_sdg_project()                         -- Creates a project and runs analysis

    review_ignorerisks_action_filesystem()       -- Verifies that for files present on a review page in SDG risks gets ignored 

    cleanup()                                    -- Runs cleanup

    teardown()                                   -- Final teardown

    run()                                        -- Run function for this testcase
"""
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.constants import PASSED
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.constants import SDGTestSteps as sc
from dynamicindex.utils.constants import is_step_complete, set_step_complete
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure,
                                   CVWebAutomationException)
from Web.Common.page_object import TestStep, handle_testcase_exception

from cvpysdk.job import Job


class TestCase(CVTestCase):
    """Class for executing ignore risks action for files with UNC path present on a page in Review page in SDG"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.activateutils = ActivateUtils()
        self.testcaseutils = CVTestCase
        self.name = "Ignore risks action for files with UNC path present on a page in Review page in SDG"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "AccessNode": None,
            "Inventory": None,
            "RAEntityDBPath": None
        }
        # Testcase constants
        self.plan_name = None
        self.project_name = None
        self.file_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.test_case_error = None
        self.gdpr_base = None
        self.local_path = None
        self.rehydrator = None
        self.db_path = None

    def is_test_step_complete(self, step_enum):
        """
        Checks if a test step is complete
        Args:
            step_enum(SDGTestSteps)     --  enum representing the step
        Returns:
            bool                        --  Returns true if step is complete else false
        """
        return is_step_complete(self.test_progress, step_enum.value)

    def set_test_step_complete(self, step_enum):
        """
        Sets the progress with a give test step value
        Args:
            step_enum(SDGTestSteps)     --  enum representing the step
        """
        set_step_complete(self.test_progress, step_enum.value)

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        if self.is_test_step_complete(sc.GENERATE_SDG_DATA):
            self.log.info("Using the data which was created in the last run.")
        else:
            self.activateutils.sensitive_data_generation(
                self.tcinputs['FileServerDirectoryPath'], number_files=15,
                db_location=self.db_path)
        self.set_test_step_complete(sc.GENERATE_SDG_DATA)

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
            self.username = self.inputJSONnode['commcell']['commcellUsername']
            self.password = self.inputJSONnode['commcell']['commcellPassword']
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.db_path = self.tcinputs.get('RAEntityDBPath')
            self.rehydrator = Rehydrator(self.id)
            self.test_progress = self.rehydrator.bucket(
                cs.BUCKET_TEST_PROGRESS)
            self.test_progress.get(default=0)
            self.generate_sensitive_data()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.username, password=self.password)
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
        if self.is_test_step_complete(sc.CREATE_SDG_PLAN):
            self.log.info("Using the plan that was created in the last run.")
        else:
            self.navigator.navigate_to_plan()
            self.gdpr_base.plans_obj.create_data_classification_plan(self.plan_name, self.tcinputs[
                'IndexServerName'], self.tcinputs['ContentAnalyzer'], entities_list=cs.ENTITIES_LIST)
        self.set_test_step_complete(sc.CREATE_SDG_PLAN)

    @test_step
    def create_sdg_project(self):
        """
            Creates a project and runs analysis
        """
        country_name = cs.USA_COUNTRY_NAME
        self.gdpr_base.testdata_path = self.tcinputs['FileServerDirectoryPath']
        if self.is_test_step_complete(sc.CREATE_SDG_PROJECT):
            self.log.info(
                "Using the project which was created in the last run.")
        else:
            self.gdpr_base.data_source_name = self.file_server_display_name
            self.navigator.navigate_to_governance_apps()
            self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
            self.gdpr_base.file_server_lookup_obj.add_project(
                self.project_name, self.plan_name)
            self.gdpr_base.file_server_lookup_obj.select_add_data_source()
            self.gdpr_base.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], cs.HOST_NAME,
                self.file_server_display_name, country_name,
                self.tcinputs['FileServerDirectoryPath'],
                username=self.tcinputs['FileServerUserName'],
                password=self.tcinputs['FileServerPassword'],
                access_node=self.tcinputs['AccessNode'], inventory_name=self.tcinputs["Inventory"])
            self.log.info(f"Sleeping for: {cs.ONE_MINUTE} seconds")
            time.sleep(cs.ONE_MINUTE)
            if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name, timeout=60):
                raise CVTestStepFailure(
                    "Could not complete the Datasource scan.")
            self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
            time.sleep(cs.ONE_MINUTE)
        self.set_test_step_complete(sc.CREATE_SDG_PROJECT)

    @test_step
    def review_ignorerisks_action_filesystem(self):
        """
        Verifies that risk for all the files present on the current review page is getting ignored
        """
        try:
            # Note down the details of the last run job
            job_details = self.gdpr_base.get_latest_job_by_operation(
                cs.IGNORE_RISKS)
            # Perform ignore risks review action
            self.navigate_to_datasource()
            self.gdpr_base.file_server_lookup_obj.select_review(
                self.file_server_display_name)
            self.admin_console.access_tab(
                self.admin_console.props['label.review'])
            status = self.gdpr_base.data_source_review_obj.review_ignore_risks_actions(
                '', [cs.RETENTION_NOT_SET], all_items_in_page=True
            )
            if not status:
                raise CVTestStepFailure("Ignore risks review action failed.")
            running_job_details = self.gdpr_base.get_latest_job_by_operation(
                cs.IGNORE_RISKS)
            self.log.info(f"Running job details {running_job_details}")
            if (job_details and running_job_details[cs.ID] == job_details[cs.ID]):
                raise CVWebAutomationException(
                    "No ignore risks remediation action job was launched ")
            job = Job(self.commcell, running_job_details[cs.ID])
            self.log.info("Waiting for the job to complete.")
            job_finished = job.wait_for_completion()

            self.log.info(f"Job finished status {job_finished}")
            if not job_finished:
                raise CVTestStepFailure("Job wasn't successful.")
        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f"Ignore risks action failed: {error_status}"
            raise CVTestStepFailure("Ignore risks action failed.")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.log.info(
            f"Does the plan exists? {self.is_test_step_complete(sc.CREATE_SDG_PLAN)}")
        self.log.info(
            f"Does the project exists? {self.is_test_step_complete(sc.CREATE_SDG_PROJECT)}")
        self.log.info(
            f"Does the pseudo client exists? {self.is_test_step_complete(sc.CREATE_SDG_PROJECT)}")
        plan_name = None if self.is_test_step_complete(
            sc.CREATE_SDG_PLAN)else self.plan_name
        project_name = None if self.is_test_step_complete(
            sc.CREATE_SDG_PROJECT) else self.project_name
        pseudo_client_name = None if self.is_test_step_complete(
            sc.CREATE_SDG_PROJECT) else self.file_server_display_name
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
            self.review_ignorerisks_action_filesystem()
            self.cleanup()
            self.teardown()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
