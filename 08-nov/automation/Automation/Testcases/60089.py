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
    create_classifier()                 --  Creates classifier on commcell
    move_model_data()                   --  Moves model data to remote client
    verify_classifier_legend()          --  Validates classifier legend shows proper count for this data source
    validate_adv_search()               --  Validates advanced search for classifier on review page
    run()                               --  run function of this test case
    tear_down()                         --  tear down function of this test case
"""

from AutomationUtils.constants import FAILED
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.Common.page_object import handle_testcase_exception, TestStep, CVTestStepFailure
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.content_analyzer_helper import ContentAnalyzerHelper


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
        self.name = "Data Classifier - Validate advanced search on review page for newly created classifier in file system data source"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyserCloudName": None,
            "HostNameToAnalyze": None,
            "ModelDataZipFile": None,
            "ClassifierDocumentCountExpected": None

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
        self.classifier_name = None
        self.crawl_path = None
        self.classified_doc_count = 0
        self.total_doc_count = 0
        self.sensitive_doc_count = 0

    def setup(self):
        """Setup function of this test case"""
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.data_source_name = "DataSource%s" % self.id
        self.project_name = "TestProject_%s" % self.id
        self.inventory_name = "TestInventory_%s" % self.id
        self.plan_name = "TestPlan_%s" % self.id
        self.classifier_name = "Auto_%s" % self.id
        self.index_server_name = self.tcinputs['IndexServerName']

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
            pseudo_client_name=self.data_source_name,
            classifier_name=[self.classifier_name]
        )

    @test_step
    def create_plan(self):
        """creates a data classification plan"""
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.index_server_name,
            self.tcinputs['ContentAnalyserCloudName'], entities_list=[dynamic_constants.ENTITY_EMAIL],
            classifier_list=[self.classifier_name])
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
            self.data_source_name, dynamic_constants.USA_COUNTRY_NAME,
            agent_installed=True, live_crawl=True, directory_path=self.crawl_path,
            inventory_name=self.inventory_name)

        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.data_source_name):
            raise Exception("Could Not Complete Data Source crawl job")

    @test_step
    def create_classifier(self):
        """Creates new classifier on the commcell"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_entity_manager(sub_type=1)
        self.gdpr_obj.classifier_obj.create_classifier(name=self.classifier_name,
                                                       content_analyzer=self.tcinputs['ContentAnalyserCloudName'],
                                                       desc="Created by Automation",
                                                       model_zip_file_path=self.tcinputs['ModelDataZipFile'])
        self.gdpr_obj.monitor_classifier_training(status=dynamic_constants.TRAIN_STATUS_COMPLETED)

    @test_step
    def move_model_data(self):
        """Moves model data to remote client"""
        ca_helper = ContentAnalyzerHelper(self)
        self.crawl_path = ca_helper.move_zip_data_to_client(client_name=self.tcinputs['HostNameToAnalyze'],
                                                            zip_file=self.tcinputs['ModelDataZipFile'])

    @test_step
    def verify_classifier_legend(self):
        """gets classifier legend from the data source review page and validates it"""
        self.gdpr_obj.file_server_lookup_obj.select_data_source(
            self.data_source_name)
        self.total_doc_count = self.gdpr_obj.data_source_discover_obj.get_total_files()
        self.sensitive_doc_count = self.gdpr_obj.data_source_discover_obj.get_sensitive_files()
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        donut = viewer.DonutChart(dynamic_constants.DONUT_CHART_NAME)
        report_viewer.associate_component(donut)
        legend_value, legend_text = donut.get_chart_legend()
        index = 0
        classified = False
        for legend in legend_text:
            if self.classifier_name in legend:
                self.log.info("Analyzing Legend Text : %s", legend)
                doc_count = legend_value[index]
                self.classified_doc_count = int(doc_count)
                self.log.info("Total document classified for this : %s", doc_count)
                if int(doc_count) >= int(self.tcinputs['ClassifierDocumentCountExpected']):
                    self.log.info(
                        "Expected Criteria Matched. Classified docs greater than : %s",
                        self.tcinputs['ClassifierDocumentCountExpected'])
                    classified = True
            index = index + 1
        if not classified:
            raise Exception("Documents are missing classification. Please check")
        if self.sensitive_doc_count < self.classified_doc_count:
            raise Exception("Classified docs count are not considered for sensitive file count on dashboard")
        self.log.info(
            f"Sensitive file count contains classified doc count as well. Sensitive count : {self.sensitive_doc_count}"
            f" Classified count : {self.classified_doc_count} Total count : {self.total_doc_count}")

    @test_step
    def validate_adv_search(self):
        """Validates advanced search for classifier on review page"""
        self.gdpr_obj.data_source_discover_obj.select_review()
        output, adv_query = self.gdpr_obj.data_source_review_obj.do_advanced_search(selector_list=[
                                                                                    self.classifier_name])
        entity_query = f"(entity_{self.classifier_name.lower()}:*)"
        if entity_query != adv_query:
            raise Exception(f"Advanced search query formed for classifier is wrong. Formed query : {adv_query}")
        self.log.info(f"Advance search query verified successfully. Query validated : {adv_query}")
        table_doc_count = self.gdpr_obj.data_source_review_obj.get_total_records()
        self.log.info(f"Table record : {table_doc_count}  Classified record : {self.classified_doc_count}")
        if int(table_doc_count) != int(self.classified_doc_count):
            raise Exception("Table count not matched on review page after doing advance search")
        self.log.info(f"Table record matched with classified document count. Table records : {table_doc_count}"
                      f" Classified doc count : {self.classified_doc_count}")

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()
            self.cleanup()
            self.create_classifier()
            self.move_model_data()
            self.create_plan()
            self.create_inventory()
            self.create_project_add_file_server()
            self.verify_classifier_legend()
            self.validate_adv_search()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != FAILED:
            machine_obj = Machine(machine_name=self.tcinputs['HostNameToAnalyze'], commcell_object=self.commcell)
            machine_obj.remove_directory(directory_name=self.crawl_path)
            self.log.info("Deleted the crawl path from remote client : %s", self.crawl_path)
