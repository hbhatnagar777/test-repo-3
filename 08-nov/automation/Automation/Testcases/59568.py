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
    __init__()              --  initialize TestCase class

    run()                   --  run function of this test case

    init_browser()          --  inits browser related objects

    init_tc()               --  Initial performance Configuration for testcase

    create_inventory()      --  Creates inventory with give name server

    create_plan()           --  Creates data classification plan for FSO app

    create_fso_client()     --  Creates FSO client

    perform_cleanup()       --  Perform Cleanup Operation for older test case runs

    perform_search()        --  performs basic searches on data source

    create_fso_project()    --  Create FSO data source and start crawl job


"""

import time
import calendar
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.Performance.performance_monitor import PerformanceMonitor
from AutomationUtils.Performance.Utils.performance_helper import PerformanceHelper
from AutomationUtils.Performance.reportbuilder import ReportBuilder
from AutomationUtils.Performance.Utils.constants import JobTypes
from AutomationUtils.Performance.Utils.constants import GeneralConstants
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.har_helper import HarHelper
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.GovernanceAppsPages.FileStorageOptimization import FileStorageOptimization
from Web.AdminConsole.GovernanceAppsPages.DataSourceDiscover import DataSourceDiscover
from Web.AdminConsole.adminconsole import AdminConsole
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
import dynamicindex.utils.constants as cs


_CONFIG_DATA = get_config().DynamicIndex.PerformanceStats


class TestCase(CVTestCase):
    """Class for executing scale job for FSO quick scan"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Activate Performance Automation - FSO full crawl job for backup data from CI'ed Client"
        self.tcinputs = {
            "IndexServerName": None,
            "FsoClientName": None,
            "FsoClientDispName": None,
            "Searches": None,
            "SearchEngineClients": None
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
        self.error_dict = {}
        self.test_case_error = None
        self.job_id = None
        self.data_source_name = None
        self.build_id = str(calendar.timegm(time.gmtime()))
        self.perf_monitor = None
        self.perf_helper = None
        self.monitor_config = None

    def init_browser(self):
        """inits browser related objects"""

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login()
        self.navigator = self.admin_console.navigator
        self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
        self.country_name = cs.USA_COUNTRY_NAME
        self.gdpr_obj.data_source_name = self.file_server_display_name
        self.fso_helper = FSO(self.admin_console, self.commcell)
        self.fso_helper.data_source_name = self.file_server_display_name
        self.discover_obj = DataSourceDiscover(self.admin_console)

    def init_tc(self):
        """Initial performance Configuration for testcase"""
        try:
            self.file_server_display_name = f"{self.id}_Performance_fso_backup_fullscan_Import"
            self.inventory_name = f"{self.id}_inventory_fso"
            self.plan_name = f"{self.id}_plan_fso"
            self.perf_monitor = PerformanceMonitor(commcell_object=self.commcell, build_id=self.build_id)
            self.perf_helper = PerformanceHelper(commcell_object=self.commcell)
            self.monitor_config = self.perf_helper.form_fso_monitor_param(
                index_server=self.tcinputs['IndexServerName'],
                job_type=JobTypes.FSO_BACKUP_FULL_SCAN_SOURCE_CI,
                search_engine=list(
                    self.tcinputs['SearchEngineClients'].split(",")))
            self.perf_monitor.push_configurations(config_data=self.monitor_config)
            self.init_browser()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

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
        Create Data Classification Plan for FSO app
        """
        self.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
            "",
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
        Perform Cleanup Operation for older test case runs
        """
        self.fso_helper.fso_cleanup(
            self.tcinputs['FsoClientDispName'], self.file_server_display_name)
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name, plan_name=self.plan_name)

    @test_step
    def perform_search(self):
        """Performs basic searches on data source"""
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.select_details_action(self.tcinputs['FsoClientDispName'])
        self.fso_helper.fso_client_details.select_datasource(self.file_server_display_name)
        self.fso_helper.fso_data_source_discover.select_fso_review_tab()
        for word in self.tcinputs['Searches']:
            self.log.info("Performing search for keyword : %s", word)
            self.gdpr_obj.data_source_review_obj.search_file(file_name=word, is_fso=True)
            time.sleep(30)

    @test_step
    def create_fso_project(self):
        """Create FSO data source and start crawl job"""
        try:
            self.init_tc()
            self.perform_cleanup()
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
            self.gdpr_obj.file_server_lookup_obj.add_file_server(
                self.tcinputs['FsoClientName'], 'Client name',
                self.file_server_display_name, self.country_name,
                agent_installed=True, backup_data_import=True,
                fso_server=True, crawl_type='Full')
            self.log.info("Going to get job id for the created data source")
            self.job_id = self.discover_obj.get_running_job_id()
            ds_helper = DataSourceHelper(self.commcell)
            self.data_source_name = ds_helper.get_data_source_starting_with_string(
                start_string=self.file_server_display_name)
            self.log.info("DataSource name : %s", self.data_source_name)
        except Exception as exp:
            if self.test_case_error is not None and len(self.error_dict.keys()) > 0:
                self.log.info("***Following Error Occurred in the Automation Testcase during Project Creation******")
                for key, value in self.error_dict.items():
                    self.log.info('{%s}  {%s} \n' % (key, value))
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def run(self):
        """Main function for test case execution"""

        # Create FSO project and start crawl job
        self.create_fso_project()

        # Monitor the job performance
        self.perf_monitor.start_monitor(job_id=self.job_id,
                                        job_type=JobTypes.FSO_BACKUP_FULL_SCAN_SOURCE_CI,
                                        config=self.monitor_config,
                                        push_to_data_source=True,
                                        **{GeneralConstants.DATA_SOURCE_NAME_PARAM: self.data_source_name,
                                           GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME: "FullScan_Import_CI_Scale_Data",
                                           GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE: "30Million"})

        # Do searches on data source and record API details
        try:
            self.init_browser()
            self.perform_search()
            har = HarHelper(commcell_object=self.commcell)
            har_csv = har.export_har(cvbrowser=self.browser, build_id=self.build_id)
            har.upload_har_report(csv_file=har_csv, index_server_name=_CONFIG_DATA.Index_Server)
        except Exception as exp:
            if self.test_case_error is not None and len(self.error_dict.keys()) > 0:
                self.log.info("***Following Error Occurred in the Automation Testcase during Search & Report******")
                for key, value in self.error_dict.items():
                    self.log.info('{%s}  {%s} \n' % (key, value))
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

        # Generate performance report for this job
        report_helper = ReportBuilder(commcell_object=self.commcell,
                                      job_id=self.job_id,
                                      job_type=JobTypes.FSO_BACKUP_FULL_SCAN_SOURCE_CI,
                                      build_id=self.build_id,
                                      use_data_source=True)
        report_helper.generate_report(
            send_mail=True,
            receivers=self.inputJSONnode[GeneralConstants.EMAIL_NODE_NAME][GeneralConstants.RECEIVER_NODE_VALUE])
