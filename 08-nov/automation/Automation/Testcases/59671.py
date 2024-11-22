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
    retrain()                           --  Retrains the classifier
    rerun_crawl()                       --  Reruns the crawl job for this SDG data source
    validate_sync_time()                --  Validates sync time between trained & sync CA
    run()                               --  run function of this test case
    tear_down()                         --  tear down function of this test case
"""
import json
import os
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
        self.name = "Data Classifier - Validate classification model sync by starting multiple training"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyserCloudName": None,
            "HostNameToAnalyze": None,
            "ModelDataZipFile": None,
            "ClassifierDocumentCountExpected": None,
            "ClassifierDocumentCountExpectedAfterTraining": None,
            "TrainContentAnalyserCloudName": None
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
        self.zip_files = None
        self.ca_helper = None
        self.accuracy = []
        self.older_train_time = None

    def setup(self):
        """Setup function of this test case"""
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.data_source_name = "DataSource%s" % self.id
        self.project_name = "TestProject_%s" % self.id
        self.inventory_name = "TestInventory_%s" % self.id
        self.plan_name = "TestPlan_%s" % self.id
        self.classifier_name = "Auto_%s" % self.id
        self.index_server_name = self.tcinputs['IndexServerName']
        self.ca_helper = ContentAnalyzerHelper(self)

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
        self.zip_files = self.ca_helper.split_zip_file(zip_file=self.tcinputs['ModelDataZipFile'],doc_count=275)
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_entity_manager(sub_type=1)
        self.gdpr_obj.classifier_obj.create_classifier(name=self.classifier_name,
                                                       content_analyzer=self.tcinputs['TrainContentAnalyserCloudName'],
                                                       desc="Created by Automation",
                                                       model_zip_file_path=self.zip_files[0])
        self.gdpr_obj.monitor_classifier_training(status=dynamic_constants.TRAIN_STATUS_COMPLETED)

    @test_step
    def move_model_data(self):
        """Moves model data to remote client"""
        self.crawl_path = self.ca_helper.move_zip_data_to_client(client_name=self.tcinputs['HostNameToAnalyze'],
                                                                 zip_file=self.tcinputs['ModelDataZipFile'])

    @test_step
    def verify_classifier_legend(self, expected_count):
        """gets classifier legend from the data source review page and validates it

                Args:

                    expected_count          (str)       :   Expected classifier document count

                Returns:

                    None
        """
        self.gdpr_obj.file_server_lookup_obj.select_data_source(
            self.data_source_name)
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
                self.log.info("Total document classified for this : %s", doc_count)
                if int(doc_count) >= int(expected_count):
                    self.log.info(
                        "Expected Criteria Matched. Classified docs greater than : %s",
                        expected_count)
                    self.accuracy.append(doc_count)
                    classified = True
            index = index + 1
        if not classified:
            raise Exception("Documents are missing classification. Please check")

    @test_step
    def retrain(self):
        """Re-trains the classifier"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_entity_manager(sub_type=1)
        self.gdpr_obj.classifier_obj.start_training(name=self.classifier_name, file_path=self.zip_files[1])
        self.gdpr_obj.monitor_classifier_training(status=dynamic_constants.TRAIN_STATUS_COMPLETED)

    @test_step
    def rerun_crawl(self):
        """Starts full crawl job on this data source"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.search_for_project(self.project_name)
        self.gdpr_obj.data_source_discover_obj.navigate_to_project_details(self.project_name)
        self.gdpr_obj.file_server_lookup_obj.select_data_source(self.data_source_name,
                                                                False, 0)
        self.log.info("Starting a full re-crawl of the datasource [%s]",
                      self.data_source_name)
        self.gdpr_obj.data_source_discover_obj.select_details()
        self.gdpr_obj.data_source_discover_obj.start_data_collection_job('full')
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.navigate_to_project_details(
            self.project_name)
        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.data_source_name):
            raise Exception("Could not complete Data Source crawl job")

    @test_step
    def validate_sync_time(self):
        """Validate sync time between trained & sync CA"""
        train_ca = self.ca_helper.get_classifier_info(name=self.classifier_name,
                                                      attribute=dynamic_constants.CLASSIFIER_ATTRIBUTE_CA_USED)
        sync_ca = self.ca_helper.get_classifier_info(name=self.classifier_name,
                                                     attribute=dynamic_constants.CLASSIFIER_ATTRIBUTE_SYNC_CA)
        train_ca = train_ca.replace("'", "\"")
        train_ca = json.loads(train_ca)
        sync_ca = sync_ca.replace("'", "\"")
        sync_ca = json.loads(sync_ca)
        # only one sync node. so access it using index
        sync_ca = sync_ca[dynamic_constants.CLASSIFIER_SYNC_CA_LIST_JSON_NODE][0]
        self.log.info(f"Trained CA - {train_ca} Sync CA - {sync_ca}")
        if dynamic_constants.CLASSIFIER_ATTRIBUTE_LAST_MODEL_TRAIN_TIME not in train_ca or\
                dynamic_constants.CLASSIFIER_ATTRIBUTE_LAST_MODEL_TRAIN_TIME not in sync_ca:
            raise Exception("Last model train time attribute missing. Please check")
        if int(sync_ca[dynamic_constants.CLASSIFIER_ATTRIBUTE_LAST_MODEL_TRAIN_TIME]) < int(
                train_ca[dynamic_constants.CLASSIFIER_ATTRIBUTE_LAST_MODEL_TRAIN_TIME]):
            raise Exception("Sync CA - Last model train time didn't updated properly in DB. Please check")
        # check with older training time stamp
        if not self.older_train_time:
            self.older_train_time = int(train_ca[dynamic_constants.CLASSIFIER_ATTRIBUTE_LAST_MODEL_TRAIN_TIME])
            self.log.info("Setting older train time as : %s", self.older_train_time)
        else:
            if int(self.older_train_time) >= int(
                    train_ca[dynamic_constants.CLASSIFIER_ATTRIBUTE_LAST_MODEL_TRAIN_TIME]):
                raise Exception("Last Model Train time not updated properly between trainings. Please check")
        self.log.info("Last Model Train Time criteria validated. Consider as success")

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
            self.verify_classifier_legend(self.tcinputs['ClassifierDocumentCountExpected'])
            self.validate_sync_time()
            self.retrain()
            self.rerun_crawl()
            self.verify_classifier_legend(self.tcinputs['ClassifierDocumentCountExpectedAfterTraining'])
            if self.accuracy[0] > self.accuracy[1]:
                raise Exception("Classification document count not increased after retraining. Please check")
            self.log.info("Classification happened fine after retraining. consider as success")
            self.log.info(f"Before training : [{self.accuracy[0]}] After training : [{self.accuracy[1]}]")
            self.validate_sync_time()

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
            for zip_f in self.zip_files:
                self.log.info("Deleting Zip file : %s", zip_f)
                os.unlink(zip_f)
