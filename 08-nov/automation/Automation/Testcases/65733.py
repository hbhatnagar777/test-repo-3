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

    __init__()                                   --  initialize TestCase class

    setup()                                      --  Initial configuration for the testcase

    create_plan()                                --  Creates a plan

    create_fso_client()                          --  Creates FSO client

    create_fso_datasource()                      --  Create FSO data source and start crawl job

    download_csv()                               --  Downloads the CSV from the passed dashboard & returns the csv_path

    cleanup()                                    --  Runs cleanup

    run()                                        --  run function of this test case

    tear_down()                                  --  Tear Down tasks
"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.utils.constants import USA_COUNTRY_NAME, CLIENT_NAME
from dynamicindex.Datacube.data_source_helper import DataSourceHelper


class TestCase(CVTestCase):
    """Class for executing this Testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Validation of Export to CSV for Size Distribution Dashboard"
        self.tcinputs = {
            "HostNameToAnalyze": None,
            "IndexServer": None,
            "FileServerDirectoryPath": None
        }
        # Testcase Constants
        self.index_server_name = None
        self.plan_name = None
        self.file_server_display_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.gdpr_base = None
        self.fso_helper = None
        self.explict_wait = 120
        self.total_files = 200
        self.machine_obj = None
        self.utils = None
        self.datasource_helper = None
        self.downloads_directory = None

    def setup(self):
        """ Initial configuration for the test case"""

        try:
            self.index_server_name = self.tcinputs['IndexServer']
            self.file_server_display_name = f"{self.id}_Automation_DS"
            self.plan_name = f'{self.id}_plan'
            self.utils = TestCaseUtils(self)
            self.machine_obj = Machine()
            self.downloads_directory = self.utils.get_temp_dir()
            self.machine_obj.clear_folder_content(self.downloads_directory)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.downloads_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)
            self.gdpr_base.data_source_name = self.file_server_display_name
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.datasource_helper = DataSourceHelper(self.commcell)
            self.fso_helper.data_source_name = self.file_server_display_name

        except Exception:
            raise Exception("init tc failed")

    @test_step
    def create_plan(self):
        """
            Creates a plan
        """

        self.navigator.navigate_to_plan()
        self.gdpr_base.plans_obj.create_data_classification_plan(self.plan_name, self.index_server_name,
                                                                 content_search=False, content_analysis=False,
                                                                 target_app='fso', select_all=True)

    @test_step
    def create_fso_client(self):
        """Create FSO client """

        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(plan_name=self.plan_name, inventory_name=None)

    @test_step
    def create_fso_datasource(self):
        """Create FSO data source and start crawl job"""

        try:
            self.gdpr_base.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], CLIENT_NAME,
                self.file_server_display_name, USA_COUNTRY_NAME,
                directory_path=self.tcinputs['FileServerDirectoryPath'],
                agent_installed=True, live_crawl=True)
            if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise CVTestStepFailure("Could not complete the Datasource scan.")
            self.log.info(f"Sleeping for: {self.explict_wait} seconds")
            time.sleep(self.explict_wait)
            self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['HostNameToAnalyze'])
            total_files_count = int(self.gdpr_base.data_source_discover_obj.get_total_number_after_crawl())
            if total_files_count != self.total_files:
                raise Exception(f"Total Files Mismatch. Expected Count = {self.total_files} "
                                f"& Actual Count = {total_files_count}")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    @test_step
    def download_csv(self):
        """
            Downloads the CSV from the passed dashboard & returns the csv_path
        """
        self.fso_helper.navigate_to_datasource_details(self.tcinputs['HostNameToAnalyze'],
                                                       self.file_server_display_name)
        self.fso_helper.fso_data_source_discover.select_fso_dashboard(
            self.admin_console.props['reports.sizeDistribution'])
        self.fso_helper.fso_data_source_discover.download_csv_from_report_actions()
        self.log.info("Wait 3 minutes for CSV Download")
        time.sleep(180)
        csv_path = self.fso_helper.get_csv_file_from_machine(self.downloads_directory)
        return csv_path[0]

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """

        self.fso_helper.fso_cleanup(self.tcinputs['HostNameToAnalyze'], self.file_server_display_name)
        self.gdpr_base.cleanup(plan_name=self.plan_name)

    def run(self):
        try:
            self.cleanup()
            self.create_plan()
            self.create_fso_client()
            self.create_fso_datasource()
            csv_path = self.download_csv()
            attributes = {"AccessTime", "CreatedTime", "FileName", "ModifiedTime", "Size", "Url", "AllowWriteUsername",
                          "AllowModifyUsername", "AllowFullControlUsername", "OwnerName", "Department"}
            parameters = {"start": 0, "rows": self.total_files}
            solr_json_response = self.datasource_helper.get_data_from_solr(self.tcinputs['HostNameToAnalyze'],
                                                                           self.file_server_display_name, attributes,
                                                                           parameters)
            self.datasource_helper.validate_csv_data_with_solr(csv_path, solr_json_response)
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)