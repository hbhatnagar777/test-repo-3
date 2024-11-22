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
    __init__()                          --  initialize TestCase class

    setup()                             --  setup function of this test case

    init_tc()                           --  initializes browser and testcase related objects

    cleanup()                           --  perform Cleanup Operation for older test case runs

    create_plan()                       --  Creates data classification plan for SDG app

    create_inventory()                  --  Creates inventory with give name server

    create_project_add_file_server()    --  Creates SDG project and add a datasource to it

    perform_search()                    --  performs basic searches on data source

    run()                               --  run function of this test case

"""


import time
import datetime
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.utils.constants import INDIA_COUNTRY_NAME
from AutomationUtils.constants import FAILED
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.Performance.Utils.performance_helper import PerformanceHelper
from AutomationUtils.Performance.performance_monitor import PerformanceMonitor
from AutomationUtils.Performance.Utils.constants import JobTypes, GeneralConstants
from AutomationUtils.Performance.reportbuilder import ReportBuilder
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.har_helper import HarHelper
from Web.Common.page_object import handle_testcase_exception, TestStep, CVTestStepFailure


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Performance testcase - SDG backed up FS without CI job"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyserCloudName": None,
            "HostNameToAnalyze": None,
            "Searches": None,
            "MediaAgent": None
        }
        self.index_server_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.plan_name = None
        self.commcell_password = None
        self.data_source_name = None
        self.project_name = None
        self.inventory_name = None
        self.har_helper = None
        self.perf_helper = None
        self.perf_monitor = None
        self.build_id = None
        self.perf_config = None
        self.job_id = None
        self.ca_client_name = None
        self.ds_client_name = None

    def setup(self):
        """Setup function of this test case"""
        self.build_id = str(datetime.datetime.now().timestamp())
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.data_source_name = "DataSource%s" % self.id
        self.project_name = "TestProject_%s" % self.id
        self.inventory_name = "TestInventory_%s" % self.id
        self.plan_name = "TestPlan_%s" % self.id
        self.index_server_name = self.tcinputs['IndexServerName']
        self.har_helper = HarHelper(self.commcell)
        self.perf_helper = PerformanceHelper(self.commcell)
        self.perf_monitor = PerformanceMonitor(self.commcell, self.build_id)

    def init_tc(self):
        """ Initial configuration for the test case. """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                          username=self.commcell.commcell_username,
                                          password=self.commcell_password)
        self.admin_console.login(username=self.commcell.commcell_username,
                                 password=self.commcell_password)
        self.log.info('Logged in through web automation')
        self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)

    def cleanup(self):
        """cleanup the testcase created entities"""
        self.gdpr_obj.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name,
            pseudo_client_name=self.data_source_name
        )

    @test_step
    def create_plan(self):
        """creates a data classification plan"""
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.index_server_name,
            self.tcinputs['ContentAnalyserCloudName'], entities_list=['Date'])
        self.log.info("Checking if DC plan is created or not")
        self.commcell.plans.refresh()
        if not self.commcell.plans.has_plan(self.plan_name):
            self.log.error("DC not created")
            raise CVTestStepFailure("DC not created")
        self.log.info("DC is created: %s" % self.plan_name)

    @test_step
    def create_inventory(self):
        """creates an inventory"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server_name)

    @test_step
    def create_project_add_file_server(self):
        """Creates a project and adds file server to it"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source()
        self.gdpr_obj.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], 'Client name',
            self.data_source_name, INDIA_COUNTRY_NAME,
            agent_installed=True,
            backup_data_import=True,
            inventory_name=self.inventory_name)

    @test_step
    def perform_search(self):
        """Performs basic searches on data source"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.navigate_to_project_details(self.project_name)
        self.gdpr_obj.file_server_lookup_obj.select_data_source(self.data_source_name)
        self.gdpr_obj.data_source_discover_obj.select_review()
        for word in self.tcinputs['Searches']:
            self.log.info("Performing search for keyword : %s", word)
            self.gdpr_obj.data_source_review_obj.search_file(file_name=word)
            time.sleep(30)

    def run(self):
        """Run function of this test case"""
        try:
            ca_obj = self.commcell.content_analyzers.get(self.tcinputs['ContentAnalyserCloudName'])
            self.ca_client_name = self.commcell.clients.get(ca_obj.client_id).name
            self.perf_config = self.perf_helper.form_sdg_fs_monitor_param(
                job_type=JobTypes.FILE_SYSTEM_BACKUP_INDEX_EXTRACTION,
                index_server=self.index_server_name,
                media_agent=self.tcinputs['MediaAgent'],
                access_node=self.tcinputs['HostNameToAnalyze'],
                content_analyzer=self.ca_client_name
            )
            self.perf_monitor.push_configurations(self.perf_config)
            self.init_tc()
            self.cleanup()
            self.create_plan()
            self.create_inventory()
            self.create_project_add_file_server()
            self.commcell.datacube.datasources.refresh()
            ds_helper = DataSourceHelper(self.commcell)
            self.ds_client_name = ds_helper.get_data_source_starting_with_string(self.data_source_name)
            self.job_id = ds_helper.get_running_job_id(self.ds_client_name)
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
        try:
            self.perf_monitor.start_monitor(
                job_id=self.job_id,
                job_type=JobTypes.FILE_SYSTEM_BACKUP_INDEX_EXTRACTION,
                config=self.perf_config,
                DataSourceName=self.ds_client_name
            )
            self.init_tc()
            self.perform_search()
            self.har_helper.analyze_all_request(cvbrowser=self.browser, build_id=self.build_id)
            self.log.info("Report uploaded")
            report_builder = ReportBuilder(self.commcell, job_id=self.job_id,
                                           job_type=JobTypes.FILE_SYSTEM_BACKUP_INDEX_EXTRACTION,
                                           build_id=self.build_id,
                                           use_data_source=True)
            report_builder.generate_report(
                send_mail=True,
                receivers=self.inputJSONnode[GeneralConstants.EMAIL_NODE_NAME][GeneralConstants.RECEIVER_NODE_VALUE])
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
