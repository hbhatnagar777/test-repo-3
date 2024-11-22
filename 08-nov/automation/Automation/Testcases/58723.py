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
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.Helper.FSOHelper import FSO
from dynamicindex.utils.activateutils import ActivateUtils
import dynamicindex.utils.constants as cs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """Basic acceptance test case for FSO in Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "FSO basic acceptance test for UNC crawled data"
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "UserName": None,
            "Password": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "TestDataSQLiteDBPath": None,
            "AccessNode": None
        }
        # Test Case constants
        self.client_name = None
        self.file_server_display_name = None
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.fso_helper = None
        self.navigator = None
        self.test_case_error = None
        self.wait_time = 60
        self.error_dict = {}
        self.entities_list = None

    def init_tc(self):
        """Initial Configuration for testcase"""
        try:
            self.file_server_display_name = f"{self.id}_test_file_server_fso"
            self.inventory_name = f"{self.id}_inventory_fso"
            self.plan_name = f"{self.id}_plan_fso"
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.country_name = cs.USA_COUNTRY_NAME
            self.gdpr_obj.data_source_name = self.file_server_display_name
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.fso_helper.data_source_name = self.file_server_display_name
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
            self.tcinputs['ContentAnalyzer'],
            content_search=False, content_analysis=False, target_app='fso')

    @test_step
    def create_fso_client(self):
        """Create FSO client """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(
            self.inventory_name, self.plan_name
        )

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.fso_helper.fso_cleanup(
            self.file_server_display_name,
            self.file_server_display_name,
            pseudo_client_name=self.file_server_display_name)
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name,
                              plan_name=self.plan_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.perform_cleanup()
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
            self.fso_helper.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])
            self.fso_helper.test_data_path = self.tcinputs['FileServerDirectoryPath']

            self.fso_helper.file_server_lookup.add_file_server(
                self.tcinputs['HostNameToAnalyze'], 'Host name',
                self.file_server_display_name, self.country_name,
                self.tcinputs['FileServerDirectoryPath'],
                username=self.tcinputs['FileServerUserName'],
                password=self.tcinputs['FileServerPassword'],
                access_node=self.tcinputs['AccessNode'],
                inventory_name=self.inventory_name)
            self.fso_helper.fso_obj.select_details_action(
                self.file_server_display_name
            )
            self.fso_helper.fso_client_details.select_details_action(
                self.file_server_display_name
            )
            if not self.fso_helper.file_server_lookup.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete Datasource scan.")
            self.log.info("Sleeping for: '%d' seconds" % self.wait_time)
            time.sleep(self.wait_time)
            self.navigator.navigate_to_governance_apps()
            self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
            self.fso_helper.analyze_client_expanded_view(self.file_server_display_name)
            try:
                self.fso_helper.analyze_client_details(
                    self.file_server_display_name,
                    self.file_server_display_name,
                    self.fso_helper.get_fso_file_count_db(),
                    self.plan_name
                )
            except Exception as err_status:
                self.error_dict["Analyze Client Details Page"] = str(err_status)
                self.test_case_error = str(err_status)
            self.fso_helper.fso_client_details.select_datasource(self.file_server_display_name)
            self.gdpr_obj.verify_data_source_name()
            self.fso_helper.fso_data_source_discover.load_fso_dashboard()
            try:
                self.fso_helper.review_size_distribution_dashboard()
            except Exception as exp:
                self.error_dict['Size Distribution Dashboard'] = str(exp)
                self.test_case_error = str(exp)

            try:
                self.fso_helper.review_file_duplicates_dashboard()
            except Exception as exp:
                self.error_dict['Duplicates Dashboard'] = str(exp)
                self.test_case_error = str(exp)
            try:
                self.fso_helper.review_fso_file_ownership_dashboard()
            except Exception as exp:
                self.error_dict['Ownership Dashboard'] = str(exp)
                self.test_case_error = str(exp)

            try:
                self.fso_helper.review_fso_file_security_dashboard()
            except Exception as exp:
                self.error_dict['Security Dashboard'] = str(exp)
                self.test_case_error = str(exp)

            try:
                self.fso_helper.verify_fso_time_data()
            except Exception as exp:
                self.error_dict['Access/Modified/Created Time'] = str(exp)
                self.test_case_error = str(exp)

            if self.test_case_error is not None:
                raise CVTestStepFailure(str(self.error_dict))
            self.perform_cleanup()

        except Exception as exp:
            if self.test_case_error is not None and len(self.error_dict.keys()) > 0:
                self.log.info("**Following Error Occurred in the Automation Testcase****")
                for key, value in self.error_dict.items():
                    self.log.info("%s %s" % (key, value))
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
