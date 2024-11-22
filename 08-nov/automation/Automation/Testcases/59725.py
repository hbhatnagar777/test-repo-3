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
    create_classifier()                 --  Creates classifier on commcell
    run()                               --  run function of this test case
    tear_down()                         --  tear down function of this test case
"""

import os
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils.constants import FAILED
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception, TestStep
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
        self.name = "Data Classifier [Negative] - Validate plan creation not showing not ready classifiers"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyserCloudName": None,
            "ModelDataZipFile": None

        }
        self.index_server_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.plan_name = None
        self.commcell_password = None
        self.classifier_name = None
        self.zip_files = None
        self.second_zip_files = None
        self.ca_helper = None
        self.second_classifier_name = None

    def setup(self):
        """Setup function of this test case"""
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.plan_name = "TestPlan_%s" % self.id
        self.classifier_name = "Auto_%s" % self.id
        self.second_classifier_name = "AutoTwo_%s" % self.id
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
        self.ca_helper = ContentAnalyzerHelper(self)

    def cleanup(self):
        """cleanup the testcase created entities"""
        self.gdpr_obj.cleanup(
            None,
            None,
            self.plan_name,
            classifier_name=[self.classifier_name, self.second_classifier_name]
        )

    @test_step
    def create_plan(self):
        """creates a data classification plan"""
        try:
            self.admin_console.navigator.navigate_to_plan()
            self.gdpr_obj.plans_obj.create_data_classification_plan(
                self.plan_name, self.index_server_name,
                self.tcinputs['ContentAnalyserCloudName'], entities_list=[dynamic_constants.ENTITY_EMAIL],
                classifier_list=[self.classifier_name])
            raise Exception("Plan got created with not ready classifiers. Please check")
        except NoSuchElementException:
            self.log.info("Classifier missing as required. - %s", self.classifier_name)

        try:
            self.admin_console.navigator.navigate_to_plan()
            self.gdpr_obj.plans_obj.create_data_classification_plan(
                self.plan_name, self.index_server_name,
                self.tcinputs['ContentAnalyserCloudName'], entities_list=[dynamic_constants.ENTITY_EMAIL],
                classifier_list=[self.second_classifier_name])
            raise Exception("Plan got created with not ready classifiers. Please check")
        except NoSuchElementException:
            self.log.info("Classifier missing as required. - %s", self.second_classifier_name)

    @test_step
    def create_classifier(self):
        """Creates new classifier on the commcell"""
        self.zip_files = self.ca_helper.split_zip_file(zip_file=self.tcinputs['ModelDataZipFile'], doc_count=45)
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_entity_manager(sub_type=1)
        self.gdpr_obj.classifier_obj.create_classifier(name=self.classifier_name,
                                                       content_analyzer=self.tcinputs['ContentAnalyserCloudName'],
                                                       desc="Created by Automation",
                                                       model_zip_file_path=self.zip_files[0])
        self.gdpr_obj.monitor_classifier_training(status=dynamic_constants.TRAIN_STATUS_FAILED)

        self.second_zip_files = self.ca_helper.split_zip_file(zip_file=self.tcinputs['ModelDataZipFile'], doc_count=65)
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_entity_manager(sub_type=1)
        self.gdpr_obj.classifier_obj.create_classifier(name=self.second_classifier_name,
                                                       content_analyzer=self.tcinputs['ContentAnalyserCloudName'],
                                                       desc="Created by Automation",
                                                       model_zip_file_path=self.second_zip_files[0])
        self.gdpr_obj.monitor_classifier_training(status=dynamic_constants.TRAIN_STATUS_NOT_READY)

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()
            self.cleanup()
            self.create_classifier()
            self.create_plan()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != FAILED:
            for zip_f in self.zip_files:
                self.log.info("Deleting Zip file : %s", zip_f)
                os.unlink(zip_f)
            for zip_f in self.second_zip_files:
                self.log.info("Deleting Zip file : %s", zip_f)
                os.unlink(zip_f)
