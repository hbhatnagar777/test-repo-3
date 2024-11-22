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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import time
import json
import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.GovernanceAppsPages.RequestManager import RequestManager
from Web.AdminConsole.GovernanceAppsPages.ReviewRequest import ReviewRequest
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from dynamicindex.utils.activateutils import ActivateUtils


class TestCase(CVTestCase):
    """Class For executing basic acceptance test of GDPR Feature"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = ("Delete Request Test for One Drive files \
        using  Request Manager in AdminConsole")
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "TestDataSQLiteDBPath": None,
            "SubclientList": None,
            "ClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "SubclientName": None,
            "OneDriveAPI": None,
            "Approver": None,
            "Reviewer": None,
            "Requester": None,
            "ReviewColumn": None
        }
        # Test Case constants
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.onedrive_server_display_name = None
        self.country_name = None
        self.request_name = None
        self.sensitive_entity = None
        self.sensitive_file = None
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.gdpr_obj = None
        self.request_manager = None
        self.review = None
        self.navigator = None
        self.app = None
        self.table = None
        self.test_case_error = None
        self.wait_time = 2 * 60
        self.error_dict = {}
        self.entity_delimiter = "****"
        self.entities_list = list()

    def get_sensitive_file_details(self):
        """
            Get the sensitive file with entity
        """
        self.sensitive_file, self.sensitive_entity = \
            self.activate_utils.get_sensitive_content_details(
                cs.ONE_DRIVE,
                self.gdpr_obj.entities_list[0],
                self.tcinputs["TestDataSQLiteDBPath"],
                cs.DB_ENTITY_DELIMITER
            )
        if self.sensitive_file.__eq__(""):
            raise CVTestStepFailure('Test DB does not contain any row with [%s] entity',
                                    self.gdpr_obj.entities_list[0])
        self.sensitive_file = self.sensitive_file.replace(':', '_')
        self.sensitive_file = self.sensitive_file.replace('\\', '_')
        self.log.info(f"Sensitive file selected {self.sensitive_file}")
        self.log.info(f"Sensitive entity for file {self.sensitive_entity}")

    def init_tc(self):
        """Initial Configuration For Testcase"""
        try:
            self.onedrive_server_display_name = f'{self.id}_test_onedrive_server'
            self.inventory_name = f'{self.id}_inventory_onedrive'
            self.plan_name = f'{self.id}_plan_onedrive'
            self.project_name = f'{self.id}_project_onedrive'
            self.request_name = '{}_request_onedrive'.format(self.id)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.request_manager = RequestManager(self.admin_console)
            self.review = ReviewRequest(self.admin_console)
            self.app = GovernanceApps(self.admin_console)
            self.table = Table(self.admin_console)
            entities_list_map = json.loads(self.tcinputs['EntitiesListMap'].replace("'", '"'))
            self.entities_list = list(entities_list_map.keys())
            self.gdpr_obj.entities_list = list(entities_list_map.values())
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Nameserver
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
            self.tcinputs['ContentAnalyzer'], self.entities_list)

    @test_step
    def create_sda_project(self):
        """
        Create SDA Project And Run Analysis
        """
        self.country_name = 'United States'
        self.gdpr_obj.data_source_name = self.onedrive_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name, self.inventory_name
        )

    @test_step
    def add_onedrive_datasource(self):
        """
        Add OneDrive DataSource
        """
        subclient_list = self.tcinputs['SubclientList'].split(',')
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source(data_source_type=cs.ONE_DRIVE)
        self.gdpr_obj.file_server_lookup_obj.add_one_drive_server(
            self.tcinputs["ClientName"],
            "Client name",
            self.onedrive_server_display_name,
            self.country_name,
            subclient_list=subclient_list
        )

    @test_step
    def create_request(self):
        """Create a request in request manager"""
        _nsuccess = False
        self.navigator.navigate_to_governance_apps()
        self.app.select_request_manager()
        requester = self.tcinputs['Requester']
        entity_type = self.request_manager.constants.entities_list[2]
        entity = self.sensitive_entity
        request_type = self.request_manager.constants.DELETE
        _nsuccess = self.request_manager.create.add_request(self.request_name, requester,
                                                            entity_type,
                                                            entity,
                                                            request_type)
        if not _nsuccess:
            raise CVTestStepFailure(f"Request {self.request_name} creation failed")

    @test_step
    def configure_request(self):
        """Configure a request in request manager"""
        _nsuccess = False
        approver = self.tcinputs['Approver']
        reviewer = self.tcinputs['Reviewer']
        project_name = self.project_name
        _nsuccess = self.request_manager.configure.assign_reviewer_approver(self.request_name,
                                                                            approver,
                                                                            reviewer, project_name)
        if not _nsuccess:
            raise CVTestStepFailure(f"Could not configure request {self.request_name}")

    @test_step
    def review_request(self):
        """Review a request in request manager"""
        self.review.review_approve_request(self.request_name, self.sensitive_file, cs.ONE_DRIVE)

    @test_step
    def validate_request_operations(self):
        """
            Validate post request approval operations
        """
        status = self.gdpr_obj.validate_request_operations(
            cs.ONE_DRIVE,
            self.sensitive_file,
            self.project_name,
            self.tcinputs['ReviewColumn']
        )
        if not status:
            self.test_case_error = ("File deletion request failed!! File found in review page [%s]",
                                    self.sensitive_file)

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.navigator.navigate_to_governance_apps()
        self.app.select_request_manager()
        self.request_manager.delete.delete_request(self.request_name)
        self.gdpr_obj.cleanup(self.project_name,
                              self.inventory_name,
                              self.plan_name,
                              pseudo_client_name=self.onedrive_server_display_name)

    def run(self):
        """Run Function For Test Case Execution"""

        try:
            self.init_tc()
            self.perform_cleanup()
            self.activate_utils.run_data_generator(self.tcinputs["OneDriveAPI"], cs.ONE_DRIVE)
            self.get_sensitive_file_details()
            self.create_inventory()
            self.create_plan()
            self.create_sda_project()
            self.add_onedrive_datasource()

            if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.onedrive_server_display_name):
                raise Exception("Could Not Complete Data Source Scan")
            self.log.info(f"Sleeping for {str(self.wait_time)} Seconds")
            time.sleep(self.wait_time)
            self.gdpr_obj.file_server_lookup_obj.select_data_source(
                self.onedrive_server_display_name)
            self.gdpr_obj.data_source_discover_obj.select_review()
            self.gdpr_obj.data_source_review_obj.search_file(
                self.sensitive_file, data_source_type=cs.ONE_DRIVE
            )
            column_list = self.table.get_column_data(self.tcinputs['ReviewColumn'])
            if len(column_list) == 0:
                raise CVTestStepFailure("Selected Sensitive File Not Found in review Page")
            self.create_request()
            self.configure_request()
            self.review_request()
            self.validate_request_operations()
            if self.test_case_error is not None:
                raise CVTestStepFailure(self.test_case_error)
            self.perform_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
