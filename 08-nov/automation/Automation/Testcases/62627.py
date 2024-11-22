# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class
    init_tc()                       --  initial Configuration for testcase
    navigate_to_review_page()       --  Navigates to the datasource review page
    create_inventory()              --  Create Inventory With Given Name server
    create_plan()                   --  Create Data Classification Plan
    move_review_actions_fso()       --  Verify move review action for FSO
    review_delete_fso_action()      --  Verify delete review action for FSO
    review_archive_fso_action()     --  Verify Archive review action for FSO
    create_fso_client()             --  Create FSO client
    verify_review_actions_fso()     --  Verifies that moved, deleted & archived items are not picked up during re-crawl
    delete_request()                --  Deletes a request
    perform_cleanup()               --  Perform Cleanup Operation
    run()                           --  run function of this test case
"""

import os
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.utils.activateutils import ActivateUtils
RM_CONFIG_DATA = get_config().DynamicIndex.RequestManager


class TestCase(CVTestCase):
    """Basic acceptance test case for FSO Request Manager in Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "FSO: Basic Acceptance case for Review actions (Delete, Move, Archive) along with request manager."
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "TestDataSQLiteDBPath": None,
            "MoveDestinationPath": None,
            "MoveMachineUserName": None,
            "MoveMachinePassword": None,
            "FSOClient": None,
            "ArchivePlan": None
        }
        # Test Case constants
        self.file_server_display_name = None
        self.inventory_name = None
        self.plan_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.fso_helper = None
        self.navigator = None
        self.test_case_error = None
        self.wait_time = 60
        self.error_dict = {}
        self.test_case_error = None
        self.move_request_name = None
        self.delete_request_name = None
        self.archive_request_name = None
        self.jobs_obj = None
        self.source_machine = None
        self.file_server_unc_path = None
        self.file_count_before_review = 10

    def init_tc(self):
        """Initial Configuration for testcase"""
        try:
            self.file_server_display_name = f"{self.id}_test_file_server_fso"
            self.inventory_name = f"{self.id}_inventory"
            self.plan_name = f"{self.id}_plan_fso"
            self.move_request_name = f'{self.id}_request_move'
            self.delete_request_name = f'{self.id}_request_delete'
            self.archive_request_name = f'{self.id}_request_archive'
            self.source_machine = Machine(machine_name=self.tcinputs['HostNameToAnalyze'],
                                          commcell_object=self.commcell)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.gdpr_obj.data_source_name = self.file_server_display_name
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.jobs_obj = Jobs(self.admin_console)
            self.fso_helper.data_source_name = self.file_server_display_name
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def navigate_to_review_page(self):
        """
        Navigates to the datasource review page
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.select_details_action(self.tcinputs['FSOClient'])
        self.fso_helper.fso_client_details.select_datasource(
            self.file_server_display_name
        )
        self.fso_helper.fso_data_source_discover.select_fso_review_tab()

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Name server
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])

        self.gdpr_obj.inventory_details_obj.add_asset_name_server(
            self.tcinputs['NameServerAsset'])
        if not self.gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete Asset Scan")

    @test_step
    def create_plan(self):
        """
        Create Data Classification Plan
        """
        self.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
            content_search=False, content_analysis=False, target_app='fso')

    @test_step
    def move_review_actions_fso(self, filepath):
        """
        Verify move review action for FSO
        Args:
            filepath    (str):  path of the file to be moved
        """
        exp_flag = False
        move_action_status = None
        filename = filepath[filepath.rindex('\\') + 1:]
        destination_path = self.tcinputs['MoveDestinationPath']
        try:
            operation_type = cs.MOVE_FILES
            self.navigator.navigate_to_jobs()
            job_details = self.jobs_obj.get_latest_job_by_operation(operation_type)
            self.navigate_to_review_page()
            move_action_status = self.gdpr_obj.data_source_review_obj.review_move_action(
                filename, destination_path, self.tcinputs['MoveMachineUserName'], self.tcinputs['MoveMachinePassword'],
                is_fso=True, review_request=True, reviewer=RM_CONFIG_DATA.Reviewer,
                request_name=self.move_request_name, approver=RM_CONFIG_DATA.Approver)
            self.gdpr_obj.validate_review_request(request_name=self.move_request_name,
                                                  reviewer=RM_CONFIG_DATA.Reviewer,
                                                  reviewer_password=RM_CONFIG_DATA.ReviewerPassword,
                                                  owner_user=self.inputJSONnode['commcell']['commcellUsername'],
                                                  owner_password=self.inputJSONnode['commcell']['commcellPassword'],
                                                  approver=RM_CONFIG_DATA.Approver,
                                                  approver_password=RM_CONFIG_DATA.ApproverPassword,
                                                  is_fso=True)
            # Track the job
            self.navigator.navigate_to_jobs()
            running_job_details = self.jobs_obj.get_latest_job_by_operation(operation_type)
            job_status = running_job_details["Status"]
            if running_job_details == job_details or job_status != "Completed":
                raise CVWebAutomationException("Job wasn't successful.")
        except CVWebAutomationException as error:
            self.error_dict[f'Move File Action Failure: {filepath}'] = str(error)
            self.test_case_error = str(error)
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            exp_flag = True
        if not move_action_status and not exp_flag:
            self.error_dict[f'Move Actions Failed {filepath}'] = "File still found in review page"
            self.test_case_error = "File still found in review page"

        if os.path.exists(os.path.join(destination_path, filename)) \
                and not os.path.exists(filepath):
            self.log.info("Successfully moved %s to %s" % (filename, destination_path))
        else:
            self.log.info("Failed to move %s to %s" % (filename, destination_path))
            self.error_dict['File Move action failed'] = filepath

    @test_step
    def review_delete_fso_action(self, filepath):
        """
        Verify delete review action for FSO
        Args:
            filepath    (str):  path of the file to be deleted
        """
        delete_action_status = None
        exp_flag = False
        file_name = filepath[filepath.rindex("\\") + 1:]
        try:
            operation_type = cs.DELETE_FILES
            self.navigator.navigate_to_jobs()
            job_details = self.jobs_obj.get_latest_job_by_operation(operation_type)
            self.navigate_to_review_page()
            delete_action_status = \
                self.gdpr_obj.data_source_review_obj.review_delete_action(
                    file_name, is_fso=True, review_request=True, reviewer=RM_CONFIG_DATA.Reviewer,
                    request_name=self.delete_request_name, approver=RM_CONFIG_DATA.Approver,
                    data_source_type=cs.FILE_SYSTEM)
            self.gdpr_obj.validate_review_request(request_name=self.delete_request_name,
                                                  reviewer=RM_CONFIG_DATA.Reviewer,
                                                  reviewer_password=RM_CONFIG_DATA.ReviewerPassword,
                                                  owner_user=self.inputJSONnode['commcell']['commcellUsername'],
                                                  owner_password=self.inputJSONnode['commcell']['commcellPassword'],
                                                  approver=RM_CONFIG_DATA.Approver,
                                                  approver_password=RM_CONFIG_DATA.ApproverPassword,
                                                  is_fso=True)
            # Track the job
            self.navigator.navigate_to_jobs()
            running_job_details = self.jobs_obj.get_latest_job_by_operation(operation_type)
            job_status = running_job_details["Status"]
            if running_job_details == job_details or job_status != "Completed":
                raise CVWebAutomationException("Job wasn't successful.")
        except CVWebAutomationException as error_status:
            self.error_dict[f'Review Delete Files Actions : {filepath}'] = str(error_status)
            self.test_case_error = str(error_status)
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            exp_flag = True
        if not delete_action_status and not exp_flag:
            self.error_dict[f'Review Delete Files Actions : {filepath}'] = \
                'File still found in review page'
            self.test_case_error = "File still found in review page"
        if not os.path.exists(filepath):
            self.log.info("Successfully deleted file from given path: %s" % filepath)
        else:
            self.error_dict["File deletion failed"] = filepath

    @test_step
    def review_archive_fso_action(self, filepath, archive_plan):
        """
        Verify Archive review action for FSO
        Args:
            filepath        (str):  path of the file to be archived
            archive_plan    (str):  Archive plan name
        """
        archive_action_status = None
        exp_flag = False
        file_name = filepath[filepath.rindex("\\") + 1:]
        try:
            operation_type = cs.ARCHIVE_FILES
            self.navigator.navigate_to_jobs()
            job_details = self.jobs_obj.get_latest_job_by_operation(operation_type)
            self.navigate_to_review_page()
            archive_action_status = \
                self.gdpr_obj.data_source_review_obj.review_archive_action(
                    file_name, archive_plan=archive_plan, is_fso=True, review_request=True,
                    reviewer=RM_CONFIG_DATA.Reviewer, request_name=self.archive_request_name,
                    approver=RM_CONFIG_DATA.Approver, data_source_type=cs.FILE_SYSTEM)
            self.gdpr_obj.validate_review_request(request_name=self.archive_request_name,
                                                  reviewer=RM_CONFIG_DATA.Reviewer,
                                                  reviewer_password=RM_CONFIG_DATA.ReviewerPassword,
                                                  owner_user=self.inputJSONnode['commcell']['commcellUsername'],
                                                  owner_password=self.inputJSONnode['commcell']['commcellPassword'],
                                                  approver=RM_CONFIG_DATA.Approver,
                                                  approver_password=RM_CONFIG_DATA.ApproverPassword,
                                                  is_fso=True)
            # Track the job
            self.navigator.navigate_to_jobs()
            running_job_details = self.jobs_obj.get_latest_job_by_operation(operation_type)
            job_status = running_job_details["Status"]
            if running_job_details == job_details or job_status != "Completed":
                raise CVWebAutomationException("Job wasn't successful.")
        except CVWebAutomationException as error_status:
            self.error_dict[f'Review Delete Files Actions : {filepath}'] = str(error_status)
            self.test_case_error = str(error_status)
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            exp_flag = True
        if not archive_action_status and not exp_flag:
            self.error_dict[f'Review Archive Files Actions : {filepath}'] = \
                'File still found in review page'
            self.test_case_error = "File still found in review page"
        if not os.path.exists(filepath):
            self.log.info("Successfully Archived file from given path: %s" % filepath)
        else:
            self.error_dict["File Archive failed"] = filepath

    @test_step
    def create_fso_client(self):
        """Create FSO client """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(
            self.inventory_name, self.plan_name
        )

    @test_step
    def verify_review_actions_fso(self, archived_file, deleted_file, moved_file):
        """
        Verifies that moved, deleted & archived items are not picked up during re-crawl
        Args:
            archived_file   (str):  Archived file name
            deleted_file (str): Deleted file name
            moved_file (str): Moved file name
        """
        archived_file = archived_file[archived_file.rindex("\\") + 1:]
        deleted_file = deleted_file[deleted_file.rindex("\\") + 1:]
        moved_file = moved_file[moved_file.rindex("\\") + 1:]
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.select_details_action(self.tcinputs['FSOClient'])
        self.fso_helper.fso_client_details.select_details_action(self.file_server_display_name)
        self.log.info("Starting a full re-crawl of the datasource [%s]", self.file_server_display_name)
        self.gdpr_obj.data_source_discover_obj.start_data_collection_job('full')
        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete Datasource scan.")
        self.log.info("Sleeping for: '[%s]' seconds", self.wait_time)
        time.sleep(self.wait_time)
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        file_reviewed_count = self.fso_helper.get_duplicate_file_count_db(deleted_file) \
            + self.fso_helper.get_duplicate_file_count_db(moved_file) \
            + self.fso_helper.get_duplicate_file_count_db(archived_file)
        try:
            self.fso_helper.analyze_client_details(
                self.tcinputs['FSOClient'],
                self.file_server_display_name,
                self.file_count_before_review - file_reviewed_count,
                self.plan_name
            )
        except Exception as err_status:
            self.error_dict["Analyze Client Details Page"] = str(err_status)
            self.test_case_error = str(err_status)

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.fso_helper.fso_cleanup(
            self.tcinputs['FSOClient'],
            self.file_server_display_name,
            self.tcinputs['MoveDestinationPath'],
            pseudo_client_name=self.file_server_display_name,
            review_request=[self.archive_request_name, self.move_request_name, self.delete_request_name])
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name,
                              plan_name=self.plan_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.perform_cleanup()
            self.activate_utils.create_new_directory(self.tcinputs["MoveDestinationPath"])
            local_path = os.path.splitdrive(self.tcinputs['FileServerDirectoryPath'])[1]
            self.file_server_unc_path = self.source_machine.get_unc_path(local_path)
            self.activate_utils.sensitive_data_generation(
                self.file_server_unc_path,
                number_files=self.file_count_before_review)
            self.activate_utils.create_fso_metadata_db(
                self.file_server_unc_path,
                self.tcinputs['TestDataSQLiteDBPath'],
                target_machine_name=self.tcinputs['HostNameToAnalyze']
            )
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
            self.fso_helper.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])
            self.fso_helper.test_data_path = self.tcinputs['FileServerDirectoryPath']
            self.fso_helper.file_server_lookup.add_file_server(
                self.tcinputs['HostNameToAnalyze'], 'Host name', self.file_server_display_name, cs.USA_COUNTRY_NAME,
                self.tcinputs['FileServerDirectoryPath'], agent_installed=True, live_crawl=True)
            if not self.fso_helper.file_server_lookup.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete Datasource scan.")
            self.log.info("Sleeping for: '%d' seconds" % self.wait_time)
            time.sleep(self.wait_time)
            files_list = self.fso_helper.fetch_fso_files_db(3)
            self.move_review_actions_fso(files_list[0])
            self.review_delete_fso_action(files_list[1])
            self.review_archive_fso_action(files_list[2], self.tcinputs['ArchivePlan'])
            self.verify_review_actions_fso(files_list[2], files_list[1], files_list[0])
            if self.test_case_error is not None:
                raise CVTestStepFailure(str(self.error_dict))
            self.perform_cleanup()

        except Exception as exp:
            if self.test_case_error is not None and len(self.error_dict.keys()) > 0:
                self.log.info("****Following Error Occurred in the Automation Testcase*****")
                for key, value in self.error_dict.items():
                    self.log.info('%s %s' % (key, value))
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
