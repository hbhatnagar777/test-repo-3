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

    init_tc()                                    --  Initial configuration for the testcase

    run()           --  run function of this test case

    create_inventory()                           --  Create an inventory with a nameserver

    create_plan()                                --  Creates a plan

    create_fso_client()                          --  Creates FSO client

    perform_cleanup()                            --  Runs cleanup

    run()                                        --  Main function for test case execution

TestCase Input: The target folder should have a folder named Text in which only text files should be present

"""

import time
import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.utils.activateutils import ActivateUtils


class TestCase(CVTestCase):
    """Basic acceptance test case for FSO in Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File Monitoring: Verify File Monitoring for netApp filer using FSO"
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "AccessNode": None,
            "FSOClientName": None
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
        self.navigator = None
        self.wait_time = 60

    def init_tc(self):
        """Initial Configuration for testcase"""
        try:
            self.file_server_display_name = f"{self.id}_test_file_server_fso"
            self.inventory_name = f"{self.id}_inventory_fso"
            self.plan_name = f"{self.id}_plan_fso"
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
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
            self.tcinputs['FSOClientName'],
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
            self.gdpr_obj.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], 'Host name', self.file_server_display_name, self.country_name,
                self.tcinputs['FileServerDirectoryPath'], user_name=self.tcinputs['FileServerUserName'],
                password=self.tcinputs['FileServerPassword'], live_crawl=False, enable_monitoring=True,
                access_node=self.tcinputs['AccessNode'])
            if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete Datasource scan.")
            self.log.info("Sleeping for: '%d' seconds" % self.wait_time)
            time.sleep(self.wait_time)
            self.log.info("Navigating to File Monitoring report page of the datasource")
            self.admin_console.navigator.navigate_to_governance_apps()
            self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
            self.fso_helper.fso_obj.select_details_action(self.tcinputs['FSOClientName'])
            self.fso_helper.fso_client_details.select_datasource(self.file_server_display_name)
            self.gdpr_obj.data_source_discover_obj.select_details()
            self.fso_helper.verify_file_monitoring(self.tcinputs['FileServerDirectoryPath'],
                                                   self.tcinputs['FileServerUserName'],
                                                   self.tcinputs['FileServerPassword'])
            self.perform_cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
