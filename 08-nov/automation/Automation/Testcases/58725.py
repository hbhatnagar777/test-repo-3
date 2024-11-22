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
    """Class for executing basic acceptance test of FSO feature"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "FSO basic acceptance test for backed up data(FULL Scan)"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "UserName": None,
            "Password": None,
            "HostNameToAnalyze": None,
            "FileServerLocalTestDataPath": None,
            "TestDataSQLiteDBPath": None,
            "StoragePolicy": None,
            "FsoClientName": None,
            "NameServerAsset": None
        }
        # Test Case constants
        self.file_server_display_name = None
        self.inventory_name = None
        self.plan_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.fso_helper = None
        self.activate_utils = None
        self.navigator = None
        self.wait_time = 60
        self.error_dict = {}
        self.test_case_error = None

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
            self.activate_utils = ActivateUtils(commcell=self.commcell)
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
            self.id, [self.tcinputs['FsoClientName']],
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
            self.tcinputs['FsoClientName'], self.file_server_display_name)
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name, plan_name=self.plan_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.run_subclient_backups(self.create_subclient_obj())
            self.perform_cleanup()
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
            self.fso_helper.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])

            self.fso_helper.file_server_lookup.add_file_server(
                self.tcinputs["HostNameToAnalyze"], cs.HOST_NAME,
                self.file_server_display_name, self.country_name,
                agent_installed=True, backup_data_import=True,
                fso_server=True, crawl_type='Full', inventory_name=self.inventory_name)
            if not self.fso_helper.file_server_lookup.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete Data Source Scan")
            self.log.info("Sleeping for: '%d' seconds" % self.wait_time)
            time.sleep(self.wait_time)
            self.navigator.navigate_to_governance_apps()
            self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
            self.fso_helper.analyze_client_expanded_view(self.tcinputs['FsoClientName'])
            try:
                self.fso_helper.analyze_client_details(
                    self.tcinputs['FsoClientName'],
                    self.file_server_display_name,
                    self.fso_helper.get_fso_file_count_db(),
                    self.plan_name,
                    is_backed_up=True
                )
            except Exception as error_status:
                self.error_dict['Analyze client details page'] = str(error_status)
                self.test_case_error = str(error_status)
            self.fso_helper.fso_client_details.select_datasource(self.file_server_display_name)
            self.gdpr_obj.verify_data_source_name()
            self.fso_helper.fso_data_source_discover.load_fso_dashboard()
            try:
                self.fso_helper.review_size_distribution_dashboard(crawl_type='Backup')
            except Exception as exp:
                self.error_dict['Size Distribution Dashboard'] = str(exp)
                self.test_case_error = str(exp)

            try:
                self.fso_helper.review_file_duplicates_dashboard()
            except Exception as exp:
                self.error_dict['Duplicates Dashboard'] = str(exp)
                self.test_case_error = str(exp)
            try:
                self.fso_helper.review_fso_file_ownership_dashboard(crawl_type='Backup')
            except Exception as exp:
                self.error_dict['Ownership Dashboard'] = str(exp)
                self.test_case_error = str(exp)

            try:
                self.fso_helper.review_fso_file_security_dashboard()
            except Exception as exp:
                self.error_dict['Security Dashboard'] = str(exp)
                self.test_case_error = str(exp)

            try:
                self.fso_helper.verify_fso_time_data(crawl_type='Backup')
            except Exception as exp:
                self.error_dict['Access/Modified/Created Time'] = str(exp)
                self.test_case_error = str(exp)

            if self.test_case_error is not None:
                raise CVTestStepFailure(str(self.error_dict))
            self.perform_cleanup()

        except Exception as exp:
            if self.test_case_error is not None and len(self.error_dict.keys()) > 0:
                self.log.info("Following Error Occurred in Automation ")
                for key, value in self.error_dict.items():
                    self.log.info("%s %s" % (key, value))
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
