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
    create_request()                    --  Creates a request in request manager
    configure_request()                 --  Configures a request in request manager
    review_request()                    --  Reviews a request in request manager
    validate_request_operations()       --  Validates post request approval operations
    run()                               --  run function of this test case
    tear_down()                         --  tear down function of this test case
"""
import time
import shutil
import os

from AutomationUtils.constants import FAILED
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.GovernanceAppsPages.RequestManager import RequestManager
from Web.AdminConsole.GovernanceAppsPages.ReviewRequest import ReviewRequest
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.Common.page_object import handle_testcase_exception, TestStep, CVTestStepFailure
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.utils.activateutils import ActivateUtils
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
        self.name = "Data Classifier - Validate request manager newly created classifier in file system data source"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyserCloudName": None,
            "HostNameToAnalyze": None,
            "ModelDataZipFile": None,
            "ClassifierDocumentCountExpected": None,
            "Requester": None,
            "Approver": None,
            "Reviewer": None,
            "RequestFileName": None

        }
        self.activateutils = ActivateUtils()
        self.request_name = None
        self.sensitive_file = None
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
        self.app = None
        self.review = None
        self.request_manager = None
        self.explict_wait = 1 * 60
        self.file_count_before_review = None
        self.test_case_error = None

    def setup(self):
        """Setup function of this test case"""
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.data_source_name = "DataSource%s" % self.id
        self.project_name = "TestProject_%s" % self.id
        self.inventory_name = "TestInventory_%s" % self.id
        self.plan_name = "TestPlan_%s" % self.id
        self.classifier_name = "Auto_%s" % self.id
        self.index_server_name = self.tcinputs['IndexServerName']
        self.request_name = "TestRequest_%s" % self.id
        self.sensitive_file = self.tcinputs['RequestFileName']

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
        self.app = GovernanceApps(self.admin_console)
        self.review = ReviewRequest(self.admin_console)
        self.request_manager = RequestManager(self.admin_console)

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
        self.file_count_before_review = self.gdpr_obj.data_source_discover_obj. \
            get_total_number_after_crawl()

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
                                                            zip_file=self.tcinputs['ModelDataZipFile'],
                                                            extract_file_count=1)
        machine_obj = Machine(machine_name=self.tcinputs['HostNameToAnalyze'], commcell_object=self.commcell)
        file_path = f"{self.crawl_path}\\TestData.txt"
        os.makedirs(self.crawl_path)
        file_ptr = open(file_path, "w")
        file_ptr.write("hello Sample")
        file_ptr.close()
        machine_obj.copy_from_local(local_path=self.crawl_path, remote_path=self.crawl_path)
        shutil.rmtree(self.crawl_path)

    @test_step
    def verify_classifier_legend(self):
        """gets classifier legend from the data source review page and validates it"""
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
                if int(doc_count) >= int(self.tcinputs['ClassifierDocumentCountExpected']):
                    self.log.info(
                        "Expected Criteria Matched. Classified docs greater than : %s",
                        self.tcinputs['ClassifierDocumentCountExpected'])
                    classified = True
            index = index + 1
        if not classified:
            raise Exception("Documents are missing classification. Please check")

    @test_step
    def create_request(self):
        """Create a request in request manager"""
        _nsuccess = False
        self.admin_console.navigator.navigate_to_governance_apps()
        self.app.select_request_manager()
        requester = self.tcinputs['Requester']
        entity_type = self.classifier_name
        request_type = self.request_manager.constants.DELETE
        _nsuccess = self.request_manager.create.add_request(self.request_name, requester,
                                                            entity_type,
                                                            "",
                                                            request_type)
        if not _nsuccess:
            raise CVTestStepFailure(f"Request {self.request_name} creation failed")

    @test_step
    def configure_request(self):
        """Configure a request in request manager"""
        _nsuccess = False
        approver = self.tcinputs['Approver']
        reviewer = self.tcinputs['Reviewer']
        project_name = self.project_name
        _nsuccess = self.request_manager.configure.assign_reviewer_approver(self.request_name,
                                                                            approver,
                                                                            reviewer, project_name)
        if not _nsuccess:
            if not _nsuccess:
                raise CVTestStepFailure(f"Could not configure request {self.request_name}")

    @test_step
    def review_request(self):
        """Review a request in request manager"""
        user = self.inputJSONnode['commcell']['commcellUsername']
        password = self.inputJSONnode['commcell']['commcellPassword']
        self.gdpr_obj.validate_review_request(request_name=self.request_name,
                                              reviewer=self.tcinputs['Reviewer'],
                                              reviewer_password=password,
                                              owner_user=user,
                                              owner_password=password,
                                              approver=self.tcinputs['Approver'],
                                              approver_password=password,
                                              files=[self.sensitive_file])

    @test_step
    def validate_request_operations(self):
        """
            Validate post request approval operations
        """
        latest_job_id = self.gdpr_obj.fetch_latest_gdpr_wrkflow_job_id()
        self.log.info(f"Workflow job id : {latest_job_id}")
        self.log.info("Waiting for delete operation workflow job to complete")
        self.commcell.job_controller.get(latest_job_id).wait_for_completion()
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.search_for_project(self.project_name)
        self.gdpr_obj.data_source_discover_obj.navigate_to_project_details(self.project_name)
        self.gdpr_obj.file_server_lookup_obj.select_data_source(self.data_source_name)
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
            raise Exception("Could not complete Data Source Scan")
        self.log.info("Sleeping for: '[%s]' seconds", self.explict_wait)
        time.sleep(self.explict_wait)
        file_count_after_review = self.gdpr_obj.data_source_discover_obj. \
            get_total_number_after_crawl()
        if (int(self.file_count_before_review) - 1) != int(file_count_after_review):
            self.log.info(
                "Number of files before review [%s], "
                "Number of files after review [%s]", self.file_count_before_review,
                file_count_after_review)
            self.test_case_error = \
                ("Number of files before review [%s], number of files after review [%s]. "
                 "File deletion failed.", self.file_count_before_review, file_count_after_review)
        else:
            self.log.info(
                "Number of files before review [%s], "
                "Number of files after review [%s]", self.file_count_before_review,
                file_count_after_review)
            self.test_case_error = ""

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
            self.create_request()
            self.configure_request()
            self.review_request()
            self.validate_request_operations()
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
