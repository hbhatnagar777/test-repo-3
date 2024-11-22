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

    navigate_to_ds_review()                      --  Navigates to the datasource review page 

    create_commcell_entities()                   --  Creates the commcell entities required

    run_backup                                   --  Runs a file system subclient backup

    init_tc()                                    --  Initial configuration for the testcase

    create_plan()                                --  Creates a plan

    create_sdg_project()                         --  Creates a project and runs analysis

    review_delete_from_backup_action_filesystem()--  Deletes from backup files on a page and verifies the operation

    cleanup()                                    --  Runs cleanup

    run()                                        --  Run function for this testcase
"""
import os
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure,
                                   CVWebAutomationException)
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing delete from backup action in review page for files on a page"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Delete from backup action for files in the review page in SDG"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "HostNameToAnalyze": None,
            "FileServerLocalDirectoryPath": None,
            "MediaAgentName": None,
            "ClientName": None,
            "StoragePool": None


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
        self.subclient_obj = None
        self.activateutils = None
        self.source_machine = None

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        partial_path = os.path.splitdrive(
            self.local_path)[1]
        self.activateutils.sensitive_data_generation(
            self.source_machine.get_unc_path(partial_path), number_files=50)

    @test_step
    def create_commcell_entities(self):
        """Gets the subclient object initialized"""

        self.subclient_obj = self.activateutils.create_commcell_entities(
            self.commcell, self.tcinputs['MediaAgentName'], self.client, self.local_path, id=self.id)

    @test_step
    def run_backup(self):
        """Runs a backup job on subclient"""
        backup_job = self.subclient_obj.backup()
        if not CrawlJobHelper.monitor_job(self.commcell, backup_job):
            raise Exception("Backup job failed to completed successfully")
        self.log.info("Backup job got completed successfully")

    def navigate_to_ds_review(self):
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
            self.activateutils = ActivateUtils()
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.file_server_display_name = f'{self.id}_file_server'
            self.source_machine = Machine(
                machine_name=self.tcinputs['HostNameToAnalyze'],
                commcell_object=self.commcell)
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']
            self.local_path = self.tcinputs['FileServerLocalDirectoryPath']
            self.generate_sensitive_data()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=username, password=password)
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
            'IndexServerName'], self.tcinputs['ContentAnalyzer'], None, select_all=True, 
            storage_pool = self.tcinputs['StoragePool'])

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
        path = self.tcinputs['HostNameToAnalyze']+"\\"+self.local_path
        self.gdpr_base.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], cs.HOST_NAME,
            self.file_server_display_name, cs.USA_COUNTRY_NAME,
            path, agent_installed=True, live_crawl=True,
            backup_data_import=True
        )
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds.")
        time.sleep(cs.ONE_MINUTE)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise CVTestStepFailure("Could not complete the datasource scan.")
        self.log.info(f"Sleeping for {cs.ONE_MINUTE} seconds")
        time.sleep(cs.ONE_MINUTE)

    @test_step
    def review_delete_from_backup_action_fs(self):
        """
        Performs and verifies delete from backup review action on the files
        """
        try:
            self.navigate_to_ds_review()
            reviewed_files = self.gdpr_base.data_source_review_obj.get_file_names()
            self.log.info(reviewed_files)
            jobs = Jobs(self.admin_console)
            self.navigator.navigate_to_jobs()
            job_details = jobs.get_latest_job_by_operation(cs.DELETE_FILES)
            # Perform delete from backup review action
            self.navigate_to_ds_review()
            status = self.gdpr_base.data_source_review_obj.review_delete_action(
                file_name="", delete_from_backup=True, all_items_in_page=True)

            self.navigator.navigate_to_jobs()
            running_job_details = jobs.get_latest_job_by_operation(
                cs.DELETE_FILES)
            job_status = running_job_details[cs.STATUS]
            if not status or job_details and running_job_details[cs.ID] == job_details[cs.ID] \
                    or job_status != cs.COMPLETED:
                raise CVWebAutomationException(
                    "Delete from backup job wasn't successful.")

            # Checking if the delete file is present in the review page
            self.navigate_to_ds_review()
            for filename in reviewed_files:
                self.gdpr_base.data_source_review_obj.search_file(
                    filename)
                review_page_file_list = self.gdpr_base.data_source_review_obj.get_file_names()
                if len(review_page_file_list) == 0:
                    raise CVTestStepFailure(
                        f"Deleted file {filename} is not present in the review page.")

            for filename in reviewed_files:
                self.log.info(
                    f"Checking if the file {filename} is present in the backup")
                file, _ = self.subclient_obj.find(file_name=filename)
                if len(file) >= 1:
                    raise CVTestStepFailure(
                        f"Deleted file is present in the backup")
        except (CVWebAutomationException, CVTestStepFailure) as error_status:
            self.test_case_error = f'Delete from backup action failed:- {str(error_status)}'
            raise CVTestStepFailure(
                f'Delete from backup action failed:- {str(error_status)}')

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """
        storage_policy_name = f"{self.id}_storagepolicy"
        library_name = f"{self.id}_library"
        backupset_name = f"{self.id}_backupset"
        self.gdpr_base.cleanup(
            self.project_name,
            plan_name=self.plan_name, pseudo_client_name=self.file_server_display_name)
        self.activateutils.activate_cleanup(
            commcell_obj=self.commcell,
            client_name=self.tcinputs['ClientName'],
            backupset_name=backupset_name,
            storage_policy_name=storage_policy_name,
            library_name=library_name
        )

    def run(self):
        try:
            self.init_tc()
            self.create_commcell_entities()
            self.run_backup()
            self.create_plan()
            self.create_sdg_project()
            self.review_delete_from_backup_action_fs()
            self.cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
