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
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from dynamicindex.utils.activateutils import ActivateUtils


class TestCase(CVTestCase):
    """Class For executing basic acceptance test of GDPR Feature"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "SDG Advanced search using File System as Data Source"
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "IndexServerName": None,
            "AccessNode": None,
            "ContentAnalyzer": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "TestDataSQLiteDBPath": None,
            "EntitiesList": None,
            "MetaDataColList": None,
            "QueriesPerEntity": None,
            "FileCount": None
        }
        # Test Case constants
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.file_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.gdpr_obj = None
        self.navigator = None
        self.test_case_error = None
        self.wait_time = 2 * 60

    def init_tc(self):
        """Initial Configuration For Testcase"""
        try:
            self.file_server_display_name = f'{self.id}_test_file_server'
            self.inventory_name = f'{self.id}_inventory_filesystem'
            self.plan_name = f'{self.id}_plan_filesystem'
            self.project_name = f'{self.id}_project_filesystem'
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.gdpr_obj.advance_column_names = self.tcinputs['MetaDataColList'].split(',')
            self.gdpr_obj.advance_entity_names = self.tcinputs['EntitiesList'].split(',')
            self.gdpr_obj.queries_per_entity = int(self.tcinputs["QueriesPerEntity"])
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
            self.tcinputs['ContentAnalyzer'], select_all=True)

    @test_step
    def create_sda_project(self):
        """
        Create SDA Project And Run Analysis
        """
        self.country_name = 'United States'
        self.gdpr_obj.data_source_name = self.file_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name, self.inventory_name
        )

    @test_step
    def add_filesystem_datasource(self):
        """
        Add File System DataSource
        """
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source()
        self.gdpr_obj.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], 'Host name',
            self.file_server_display_name, self.country_name,
            self.tcinputs['FileServerDirectoryPath'],
            username=self.tcinputs['FileServerUserName'],
            password=self.tcinputs['FileServerPassword'],
            access_node=self.tcinputs['AccessNode'])

    @test_step
    def review_filesystem_advance_search(self):
        """
        Review Added File System DataSource, Advance
        Search
        """
        self.gdpr_obj.verify_data_source_name()
        status = self.gdpr_obj.verify_advance_search(
            self.tcinputs['TestDataSQLiteDBPath'])
        if not status:
            self.test_case_error = 'Advance Search Verification failed Please check logs for failed queries'

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.gdpr_obj.cleanup(self.project_name,
                              self.inventory_name,
                              self.plan_name,
                              pseudo_client_name=self.file_server_display_name)

    def run(self):
        """Run Function For Test Case Execution"""

        try:
            self.init_tc()
            self.perform_cleanup()
            self.activate_utils.sensitive_data_generation(
                self.tcinputs['FileServerDirectoryPath'],
                number_files=self.tcinputs['FileCount'])
            self.create_inventory()
            self.create_plan()
            self.create_sda_project()
            self.add_filesystem_datasource()

            if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could Not Complete Data Source Scan")
            self.log.info(f"Sleeping for {str(self.wait_time)} Seconds")
            time.sleep(self.wait_time)

            self.gdpr_obj.file_server_lookup_obj.select_data_source(
                self.file_server_display_name)
            self.gdpr_obj.data_source_discover_obj.select_review()
            self.review_filesystem_advance_search()
            if self.test_case_error is not None:
                raise CVTestStepFailure(self.test_case_error)
            self.perform_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
