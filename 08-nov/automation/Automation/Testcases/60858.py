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
    setup()             --  Initialize TestCase attributes
    create_inventory()  --  Creates Activate Inventory
    create_plan()       --  Creates FSO DC Plan
    create_fso_client() --  Add new FSO Server
    perform_cleanup()   --  Perform cleanup related tasks
    run()               --  Run function of this test case
    tear_down()         --  Tear Down tasks

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.Helper.FSOHelper import FSO
import dynamicindex.utils.constants as cs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """FSO: Verify if we are reusing existing client when Data source is added"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "FSO : Verify if we are reusing Existing FSO clients"
        self.tcinputs = {
            "IndexServerName": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPathList": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "TestDataSQLiteDBPath": None,
            "AccessNode": None
        }
        # Test Case constants
        self.user_password = None
        self.fso_datasource_name_list = None
        self.inventory_name = None
        self.plan_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.fso_helper = None
        self.navigator = None
        self.wait_time = 60
        self.error_dict = {}
        self.path_list = None

    def setup(self):
        """Setup Configuration for Testcase"""
        try:
            self.user_password = self.inputJSONnode['commcell']['commcellPassword']
            self.fso_datasource_name_list = \
                [f"{self.id}_test_file_server_fso1", f"{self.id}_test_file_server_fso2"]
            self.path_list = self.tcinputs['FileServerDirectoryPathList'].split(',')
            self.inventory_name = f"{self.id}_inventory_fso"
            self.plan_name = f"{self.id}_plan_fso"
            self.country_name = cs.USA_COUNTRY_NAME
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.commcell.commcell_username,
                                              password=self.user_password)
            self.admin_console.login(username=self.commcell.commcell_username,
                                     password=self.user_password)
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.gdpr_obj.data_source_name = self.fso_datasource_name_list[1]
            self.fso_helper.data_source_name = self.fso_datasource_name_list[1]
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

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
            raise CVTestStepFailure("Could not complete Name Server Asset Scan")

    @test_step
    def create_plan(self):
        """
        Create FSO Data Classification Plan
        """
        self.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
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
        for ds in self.fso_datasource_name_list:
            self.fso_helper.fso_cleanup(
                self.fso_datasource_name_list[0],
                ds, pseudo_client_name=ds)
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name,
                              plan_name=self.plan_name)

    def run(self):
        """Run function for test case execution"""
        try:
            self.perform_cleanup()
            self.create_inventory()
            self.create_plan()
            self.fso_helper.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])

            for index, path in enumerate(self.path_list):
                self.create_fso_client()
                self.gdpr_obj.file_server_lookup_obj.add_file_server(
                    self.tcinputs['HostNameToAnalyze'], 'Host name',
                    self.fso_datasource_name_list[index], self.country_name,
                    path, username=self.tcinputs['FileServerUserName'],
                    password=self.tcinputs['FileServerPassword'],
                    access_node=self.tcinputs['AccessNode'])

                # Verify we have not created a new client for second data source
                if self.fso_helper.fso_obj.check_if_client_exists(self.fso_datasource_name_list[1]):
                    raise Exception(f"Testcase Failed: Created new client [{self.fso_datasource_name_list[1]}]")

                self.fso_helper.fso_obj.select_details_action(self.fso_datasource_name_list[0])
                self.fso_helper.fso_client_details.select_details_action(self.fso_datasource_name_list[index])

                if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                        self.fso_datasource_name_list[index]):
                    raise Exception(f"Could not complete Data source scan for {self.fso_datasource_name_list[index]}")
                self.log.info("Sleeping for: '%d' seconds" % self.wait_time)
                time.sleep(self.wait_time)

            # verify Quick-view for First client and validate data source added second time is present
            self.navigator.navigate_to_governance_apps()
            self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
            self.fso_helper.analyze_client_expanded_view(self.fso_datasource_name_list[0])

            # Verify Client details page w.r.t second data source
            try:
                self.fso_helper.analyze_client_details(
                    self.fso_datasource_name_list[0],
                    self.fso_datasource_name_list[1],
                    self.fso_helper.get_fso_file_count_db(),
                    self.plan_name
                )
            except Exception as err_status:
                self.error_dict["Analyze Client Details Page"] = str(err_status)
                self.status = constants.FAILED

            # verify data source name in data source dashboard page for second client
            self.fso_helper.fso_client_details.select_datasource(self.fso_datasource_name_list[1])
            self.gdpr_obj.verify_data_source_name()

            if self.status == constants.FAILED:
                raise CVTestStepFailure(str(self.error_dict))

        except Exception as exp:
            if len(self.error_dict) > 0:
                self.log.info("****Following Error Occurred in the Automation Testcase****")
                for key, value in self.error_dict.items():
                    self.log.info("%s %s" % (key, value))
                self.log.info("************************************************************")
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            if self.status != constants.FAILED:
                self.perform_cleanup()
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
