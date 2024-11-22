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
    review_tag_files_action_fso()   --  Perform tag review action for FSO
    create_fso_client()             --  Create FSO client
    verify_tag_files_action_fso()   --  Verifies tag review action for FSO
    perform_cleanup()               --  Perform Cleanup Operation
    run()                           --  run function of this test case
"""

import os
import time

import dynamicindex.utils.constants as cs
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.utils.activateutils import ActivateUtils

RM_CONFIG_DATA = get_config().DynamicIndex.RequestManager


class TestCase(CVTestCase):
    """Basic Acceptance Test case for FSO tag review action along with request manager"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "FSO: Basic Acceptance Test case for tag review action along with request manager"
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "TestDataSQLiteDBPath": None,
            "FSOClient": None,
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
        self.tag_request_name = None
        self.source_machine = None
        self.file_server_unc_path = None
        self.file_count_before_review = 50

    def init_tc(self):
        """Initial Configuration for testcase"""
        try:
            self.file_server_display_name = f"{self.id}_test_file_server_fso"
            self.inventory_name = f"{self.id}_inventory"
            self.plan_name = f"{self.id}_plan_fso"
            self.tag_request_name = f'{self.id}_request_tag'
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
    def review_tag_files_action_fso(self, filepath):
        """
        Performing Tag Files review action for FSO
        Args:
            filepath (str): path of the file
        """
        filename = filepath[filepath.rindex('\\') + 1:]
        try:
            operation_type = cs.TAG_FILES
            jobs = Jobs(self.admin_console)
            self.navigator.navigate_to_jobs()
            job_details = jobs.get_latest_job_by_operation(operation_type)
            self.navigate_to_review_page()
            tag_action_status = self.gdpr_obj.data_source_review_obj.review_tag_files_action(
                filename, RM_CONFIG_DATA.Tag, is_fso=True, data_source_type=cs.FILE_SYSTEM, all_items_in_page=False,
                review_request=True, reviewer=RM_CONFIG_DATA.Reviewer, request_name=self.tag_request_name,
                approver=RM_CONFIG_DATA.Approver)
            if not tag_action_status:
                raise CVWebAutomationException("Failed to create review request for tag action")
            self.gdpr_obj.validate_review_request(request_name=self.tag_request_name,
                                                  reviewer=RM_CONFIG_DATA.Reviewer,
                                                  reviewer_password=RM_CONFIG_DATA.ReviewerPassword,
                                                  owner_user=self.inputJSONnode['commcell']['commcellUsername'],
                                                  owner_password=self.inputJSONnode['commcell']['commcellPassword'],
                                                  approver=RM_CONFIG_DATA.Approver,
                                                  approver_password=RM_CONFIG_DATA.ApproverPassword,
                                                  is_fso=True)
            # Track the job
            self.navigator.navigate_to_jobs()
            running_job_details = jobs.get_latest_job_by_operation(operation_type)
            job_status = running_job_details["Status"]
            if running_job_details == job_details or job_status != "Completed":
                raise CVWebAutomationException("Job wasn't successful.")
        except CVWebAutomationException as error_status:
            self.error_dict[f'Review Tag Files Actions'] = str(error_status)
            self.test_case_error = str(error_status)
            self.gdpr_obj.data_source_review_obj.close_action_modal()

    @test_step
    def create_fso_client(self):
        """Create FSO client """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(
            self.inventory_name, self.plan_name
        )

    @test_step
    def verify_tag_files_action_fso(self, tag_name, filepath):
        """
        Verify Tag Files review action for FSO
        Args:
            filepath (str): path of the file
            tag_name (str): name of the tag to be applied
        """
        filename = filepath[filepath.rindex('\\') + 1:]
        self.log.info("Name of the file retrieved from filepath: %s" % filename)

        self.navigate_to_review_page()
        tagged_file = self.gdpr_obj.data_source_review_obj.get_tagged_file_names(tag_name)
        self.log.info("Name of the file retrieved from tag filter: %s" % tagged_file[0])
        if tagged_file[0] == filename:
            self.log.info("Successfully verified the file name for the applied tag: %s" % tag_name)
        else:
            raise CVTestStepFailure("Validation of the file name failed for the tag: %s" % tag_name)
        if len(tagged_file) != 1:
            raise CVTestStepFailure(f"Tagging happened on more files than selected: {len(tagged_file)}")

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.fso_helper.fso_cleanup(
            self.tcinputs['FSOClient'],
            self.file_server_display_name,
            pseudo_client_name=self.file_server_display_name,
            review_request=[self.tag_request_name])
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name,
                              plan_name=self.plan_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.perform_cleanup()
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
            self.fso_helper.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
            self.fso_helper.test_data_path = self.tcinputs['FileServerDirectoryPath']
            self.fso_helper.file_server_lookup.add_file_server(
                self.tcinputs['HostNameToAnalyze'], cs.HOST_NAME, self.file_server_display_name, cs.USA_COUNTRY_NAME,
                self.tcinputs['FileServerDirectoryPath'], agent_installed=True, live_crawl=True)
            if not self.fso_helper.file_server_lookup.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete Datasource scan.")
            self.log.info("Sleeping for: '%d' seconds" % self.wait_time)
            time.sleep(self.wait_time)
            files_list = self.fso_helper.fetch_fso_files_db(2)
            self.review_tag_files_action_fso(files_list[1])
            self.verify_tag_files_action_fso(RM_CONFIG_DATA.Tag, files_list[1])
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
