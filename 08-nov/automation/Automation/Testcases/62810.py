# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class
    init_tc()                       --  initial Configuration for testcase
    create_subclient()              --  Create FS Subclient objects for respective clients
    run_subclient_backups()         --  Run backup jobs for passed subclient list
    navigate_to_review_page()       --  Navigates to the datasource review page
    create_inventory()              --  Create Inventory With Given Name server
    create_plan()                   --  Create Data Classification Plan
    review_delete_fso_action()      --  Verify delete review action for FSO
    create_fso_client()             --  Create FSO client
    verify_delete_review_action()   --  Verifies that deleted items are not picked up during re-crawl
    perform_cleanup()               --  Perform Cleanup Operation
    run()                           --  run function of this test case
"""

import time
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.Helper.FSOHelper import FSO
from dynamicindex.utils.activateutils import ActivateUtils
import dynamicindex.utils.constants as cs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException
RM_CONFIG_DATA = get_config().DynamicIndex.RequestManager


class TestCase(CVTestCase):
    """Testcase for Delete review action on backed up datasource (FSO) with request manager"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance test for backed up data (Quick Scan) with request manager (delete from backup)"
        self.tcinputs = {
            "IndexServerName": None,
            "HostNameToAnalyze": None,
            "FileServerLocalTestDataPath": None,
            "FileServerDirectoryPath": None,
            "TestDataSQLiteDBPath": None,
            "StoragePolicy": None,
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
        self.subclient_object = None
        self.activate_utils = None
        self.navigator = None
        self.wait_time = 60
        self.error_dict = {}
        self.test_case_error = None
        self.file_count_before_review = 50
        self.delete_request_name = None

    def init_tc(self):
        """Initial Configuration for testcase"""
        try:
            self.file_server_display_name = f"{self.id}_test_file_server_fso"
            self.inventory_name = f"{self.id}_inventory_fso"
            self.plan_name = f"{self.id}_plan_fso"
            self.delete_request_name = f'{self.id}_request_delete'
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.activate_utils = ActivateUtils(commcell=self.commcell)
            self.gdpr_obj.data_source_name = self.file_server_display_name
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.fso_helper.data_source_name = self.file_server_display_name
            self.fso_helper.backup_file_path = self.tcinputs['FileServerLocalTestDataPath']
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def create_subclient_obj(self):
        """
        Create FS Subclient objects for respective clients.
        Return:
            List[(Object)] : Subclient object list
        """
        return self.activate_utils.create_fs_subclient_for_clients(
            self.id, [self.tcinputs['FSOClient']],
            [self.tcinputs['FileServerLocalTestDataPath']],
            self.tcinputs['StoragePolicy'],
            cs.FSO_SUBCLIENT_PROPS
        )

    def run_subclient_backups(self, subclient_obj_list):
        """
        Run backup jobs for passed subclient list
        Args:
            subclient_obj_list (list) : Subclient Object list to run backup jobs
        """
        self.activate_utils.run_backup(subclient_obj_list, backup_level='Full')

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
            find_properties = {'file_name': file_name}
            if len(self.subclient_object.find(find_properties)[0]) != 1:
                raise Exception('File is not present in backup media')
            operation_type = cs.DELETE_FILES
            jobs = Jobs(self.admin_console)
            self.navigator.navigate_to_jobs()
            job_details = jobs.get_latest_job_by_operation(operation_type)
            self.navigate_to_review_page()
            delete_action_status = \
                self.gdpr_obj.data_source_review_obj.review_delete_action(
                    file_name, delete_from_backup=True, is_fso=True, review_request=True,
                    reviewer=RM_CONFIG_DATA.Reviewer, request_name=self.delete_request_name,
                    approver=RM_CONFIG_DATA.Approver, data_source_type=cs.FILE_SYSTEM)
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
            running_job_details = jobs.get_latest_job_by_operation(operation_type)
            job_status = running_job_details["Status"]
            if running_job_details == job_details or job_status != "Completed":
                raise CVWebAutomationException("Job wasn't successful.")
        except CVWebAutomationException as error_status:
            self.error_dict[f'Review Delete Files Actions'] = str(error_status)
            self.test_case_error = str(error_status)
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            exp_flag = True
        if not delete_action_status and not exp_flag:
            self.error_dict[f'Review Delete Files Actions'] = 'Files still found in review page'
            self.test_case_error = "Files still found in review page"

    @test_step
    def create_fso_client(self):
        """Create FSO client """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(
            self.inventory_name, self.plan_name
        )

    @test_step
    def verify_delete_review_action(self, deleted_file):
        """
        Verifies that deleted items are not picked up during re-crawl
        Args:
            deleted_file (str): Deleted file name
        """
        deleted_file = deleted_file[deleted_file.rindex("\\") + 1:]
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
        file_reviewed_count = self.fso_helper.get_duplicate_file_count_db(deleted_file)
        try:
            self.fso_helper.analyze_client_details(
                self.tcinputs['FSOClient'],
                self.file_server_display_name,
                self.file_count_before_review - file_reviewed_count,
                self.plan_name
            )
            self.log.info("Checking if deleted file do not exist in the backup media")
            find_properties = {'file_name': deleted_file}
            if len(self.subclient_object.find(find_properties)[0]) != 0:
                raise Exception('File still present in backup media')
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
            review_request=[self.delete_request_name])
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name, plan_name=self.plan_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.perform_cleanup()
            self.activate_utils.sensitive_data_generation(
                self.tcinputs['FileServerDirectoryPath'],
                number_files=self.file_count_before_review)
            self.activate_utils.create_fso_metadata_db(
                self.tcinputs['FileServerDirectoryPath'],
                self.tcinputs['TestDataSQLiteDBPath'],
                target_machine_name=self.tcinputs['HostNameToAnalyze'])
            self.subclient_object = self.create_subclient_obj()[0]
            self.run_subclient_backups([self.subclient_object])
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
            self.fso_helper.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])
            self.fso_helper.file_server_lookup.add_file_server(
                self.tcinputs["FSOClient"], cs.CLIENT_NAME,
                self.file_server_display_name, cs.USA_COUNTRY_NAME,
                agent_installed=True, backup_data_import=True,
                fso_server=True, crawl_type='Quick')
            if not self.fso_helper.file_server_lookup.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete Data Source Scan")
            self.log.info("Sleeping for: '%d' seconds" % self.wait_time)
            time.sleep(self.wait_time)

            files_list = self.fso_helper.fetch_fso_files_db(2)
            self.review_delete_fso_action(files_list[1])
            self.verify_delete_review_action(files_list[1])
            if self.test_case_error is not None:
                raise CVTestStepFailure(str(self.error_dict))
            self.perform_cleanup()

        except Exception as exp:
            if self.test_case_error is not None and len(self.error_dict.keys()) > 0:
                self.log.info("***Following Error Occurred in the Automation Testcase******")
                for key, value in self.error_dict.items():
                    self.log.info('{%s}  {%s} \n' % (key, value))
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
