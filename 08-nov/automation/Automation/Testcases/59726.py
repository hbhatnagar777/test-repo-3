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
    delete_classifier()                 --  Deletes classifier from commcell and checks for ML/Train data exists or not
    content_extractor_svc_operations()  --  Starts/Stops content extractor service on CA client
    run()                               --  run function of this test case
    tear_down()                         --  tear down function of this test case
"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.Performance.Utils.constants import Binary, Platforms
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
        self.name = "Data Classifier [Negative] - Validate stale thread deleting dangling classifiers"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyserCloudName": None,
            "ModelDataZipFile": None

        }
        self.index_server_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.commcell_password = None
        self.classifier_name = None
        self.ca_helper = None
        self.classifier_info = None

    def setup(self):
        """Setup function of this test case"""
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
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
        self.ca_helper = ContentAnalyzerHelper(self)

    def cleanup(self):
        """cleanup the testcase created entities"""
        self.gdpr_obj.cleanup(
            None,
            None,
            None,
            classifier_name=[self.classifier_name]
        )

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
        result, self.classifier_info = self.ca_helper.is_classifier_model_data_exists(name=self.classifier_name)
        if not result:
            raise Exception("Classifier model data doesn't exists. Please check")
        self.log.info("Classifier Model data exists. Proceed with Deletion")

    @test_step
    def content_extractor_svc_operations(self, stop=False):
        """Start/Stop content extractor service on Content Analyzer client

            Args:

                stop            (bool)      --      Boolean to denote whether to stop or start service

        """
        client_id = self.commcell.content_analyzers.get(self.tcinputs['ContentAnalyserCloudName']).client_id
        client_obj = self.commcell.clients.get(client_id)
        machine_obj = Machine(machine_name=client_obj, commcell_object=self.commcell)
        self.log.info(f"Going to stop Content Extractor service on Content Analyzer machine")
        self.log.info(f"Client os type : {machine_obj.os_info}")
        if stop:
            if machine_obj.os_info.lower() == dynamic_constants.UNIX.lower():
                # first kill cvlaunchd process which does auto service restart in case of crash or kill
                pid = machine_obj.get_process_id(process_name=dynamic_constants.CVLAUNCH_PROCESS_NAME)
                self.log.info(f"Cvlaunchd process id : {pid}")
                machine_obj.kill_process(process_id=pid[0])
                self.log.info("Successfully Stopped cvlaunchd in Unix client")
                # kill only cvpreview process to validate classifier deletion
                pid = machine_obj.get_process_id(process_name=Binary.CONTENT_EXTRACTOR[Platforms.Unix])
                self.log.info(f"CE process id : {pid}")
                machine_obj.kill_process(process_id=pid[0])
                self.log.info("Successfully Stopped CE Service alone in Unix client")
            else:
                client_obj.stop_service(service_name=dynamic_constants.CE_SERVICE_NAME)
                self.log.info("Service Stop finished")
        else:
            if machine_obj.os_info.lower() == dynamic_constants.UNIX.lower():
                client_obj.restart_services()
                self.log.info("Successfully restarted all service in Unix client")
            else:
                client_obj.start_service(service_name=dynamic_constants.CE_SERVICE_NAME)
                self.log.info("Service Start finished")

    @test_step
    def delete_classsifier(self):
        """Deletes classifier from commcell and checks for ML/Train data exists or not"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_entity_manager(sub_type=1)
        self.gdpr_obj.classifier_obj.delete_classifier(name=self.classifier_name)
        result, info = self.ca_helper.is_classifier_model_data_exists(
            name=self.classifier_name, model_info=self.classifier_info, skip_solr=True)
        if not result:
            raise Exception("Model data does not exists even though content extractor service is down. Please check")
        self.log.info("Classifier model data exists")

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()
            self.cleanup()
            self.create_classifier()
            self.content_extractor_svc_operations(stop=True)
            self.delete_classsifier()
            self.content_extractor_svc_operations(stop=False)
            self.log.info("Wait for 5 Mins to make sure stale thread got invoked on content analyzer client")
            time.sleep(300)
            result, info = self.ca_helper.is_classifier_model_data_exists(
                name=self.classifier_name, model_info=self.classifier_info)
            if result:
                raise Exception(
                    "Model data exists even though content extractor service is brought up. Please check")
            self.log.info("Classifier model data does not exists. Consider as stale thread success")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        pass
