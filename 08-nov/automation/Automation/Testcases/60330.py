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

    navigate_to_datasource()                     --  Navigates to the datasource panel

    init_tc()                                    --  Initial configuration for the testcase

    create_inventory()                           --  Create an inventory with a nameserver

    create_plan()                                --  Creates a plan

    create_sdg_project()                         --  Creates a project and runs analysis

    review_delete_action_filesystem()            --  Deletes files on a page and verifies the operation

    review_delete_action_full_crawl_filesystem() --  Verifies the delete operation by running a full crawl

    cleanup()                                    --  Runs cleanup

    run()                                        --  Run function for this testcase
"""
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
    """Class for executing delete action in review page for files on a page"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Delete action for files with UNC path in the review page in SDG"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "AccessNode": None

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
        self.file_count_before_review = 0
        self.file_count_after_review = 0

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        self.activateutils.sensitive_data_generation(self.dir_path,
                                                     number_files=15)

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
            self.username = self.inputJSONnode['commcell']['commcellUsername']
            self.password = self.inputJSONnode['commcell']['commcellPassword']
            self.inventory_name = f'{self.id}_inventory'
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.dir_path = self.tcinputs['FileServerDirectoryPath']
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                username=self.tcinputs['FileServerUserName'], password=self.tcinputs['FileServerPassword'])
            self.generate_sensitive_data()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.username, password=self.password)
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
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

        country_name = cs.USA_COUNTRY_NAME
        self.gdpr_base.testdata_path = self.dir_path
        self.gdpr_base.data_source_name = self.file_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)
        self.gdpr_base.file_server_lookup_obj.select_add_data_source()
        self.gdpr_base.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], cs.HOST_NAME,
            self.file_server_display_name, country_name,
            self.dir_path,
            username=self.tcinputs['FileServerUserName'],
            password=self.tcinputs['FileServerPassword'], access_node=self.tcinputs['AccessNode'], inventory_name=self.inventory_name)
        self.log.info(f"Sleeping for: {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise CVTestStepFailure("Could not complete the datasource scan.")
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)

    @test_step
    def review_delete_action_filesystem(self):
        """
        Performs and verifies delete action on the files present in review page
        """
        try:
            jobs = Jobs(self.admin_console)
            files_before_review = self.source_machine.get_files_in_path(
                self.tcinputs["FileServerDirectoryPath"])
            self.file_count_before_review = len(files_before_review)
            # Note the details of an already running job if any
            self.navigator.navigate_to_jobs()
            job_details = jobs.get_latest_job_by_operation(cs.DELETE_FILES)

            self.navigate_to_datasource()
            self.gdpr_base.file_server_lookup_obj.select_review(
                self.file_server_display_name)
            self.admin_console.access_tab(
                self.admin_console.props['label.review'])
            reviewed_files = self.gdpr_base.data_source_review_obj.get_file_names()
            self.count_reviewed_files = len(reviewed_files)
            status = self.gdpr_base.data_source_review_obj.review_delete_action(
                file_name="", all_items_in_page=True)

            # Get the details of the latest job
            self.navigator.navigate_to_jobs()
            running_job_details = jobs.get_latest_job_by_operation(
                cs.DELETE_FILES)
            job_status = running_job_details[cs.STATUS]
            if not status or job_details and running_job_details[cs.ID] == job_details[cs.ID] \
                    or job_status != cs.COMPLETED:
                raise CVTestStepFailure("Job wasn't successful.")

            files_after_review = self.source_machine.get_files_in_path(
                self.tcinputs["FileServerDirectoryPath"])
            self.file_count_after_review = len(files_after_review)
            self.log.info(
                f"No. of files present in the source path before the delete operation: {self.file_count_before_review}")
            self.log.info(
                f"No. of files left in the source path after the delete operation: {self.file_count_after_review}")
            if self.file_count_after_review == self.file_count_before_review - self.count_reviewed_files:
                self.log.info(f"Successfully deleted all the files")
            else:
                raise CVTestStepFailure(
                    f"Deleted {self.count_reviewed_files} but {self.file_count_after_review} files are present")
        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f'Delete action failed:- {str(error_status)}'
            raise CVTestStepFailure("Delete action failed.")

    @test_step
    def review_delete_action_full_crawl_filesystem(self):
        """
        Verifies that the deleted files are not getting picked during a full crawl
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
        self.file_count_after_review = int(self.gdpr_base.data_source_discover_obj.
                                           get_total_number_after_crawl())
        self.log.info(
            f"Number of files before the delete operation {self.file_count_before_review}, "
            f"Number of files after the delete operation {self.file_count_after_review}")
        if self.count_reviewed_files != self.file_count_before_review - self.file_count_after_review:
            self.test_case_error = ("Delete operation failed.")

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        self.gdpr_base.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name, pseudo_client_name=self.file_server_display_name)

    def run(self):
        try:
            self.init_tc()
            self.create_inventory()
            self.create_plan()
            self.create_sdg_project()
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
