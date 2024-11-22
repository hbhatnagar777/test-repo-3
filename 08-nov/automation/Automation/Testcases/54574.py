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
    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    _cleanup()                  --  Cleanup the entities created

    validate_wf_run()           --  Validate whether applied throttling was successful or not

    install_workflow()          --  Install the workflow if it is not installed

    open_workflow()             --  When clicked on Open, workflow form should open

    create_entities()           --  create required entities for workflow execution

    run_workflow()              --  Populates all the required inputs to run workflow based on optype

    Input Example:
    "54574": {
        "MediaAgentName": "maName",
        "CloudServerType": "Microsoft Azure Storage",
        "CloudMountPath": "containername",
        "CloudPassword": "password",
        "CloudUserName": "blob.core.windows.net@1//username",
        "ServiceHost"  : "blob.core.windows.net"
    }

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.config import get_config
from AutomationUtils.constants import TEMP_DIR
from MediaAgents.MAUtils.mahelper import MMHelper
from Web.Common.cvbrowser import (Browser, BrowserFactory)
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure)
from Web.Common.page_object import (TestStep, handle_testcase_exception)
from Web.WebConsole.Forms.forms import Forms
from Web.AdminConsole.adminconsole import AdminConsole
from Server.Workflow.workflowhelper import WorkflowHelper

import time

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Software store workflow Cloud Upload and Download Throttling Control"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate Cloud Upload and Download Throttling Control"
        self.tcinputs = {
            "MediaAgentName": None,
            "CloudServerType": None,
            "CloudMountPath": None,
            "CloudPassword": None,
            "CloudUserName": None,
            "ServiceHost": None
        }
        self.browser = None
        self.admin_console = None
        self.forms = None
        self.workflow_helper = None
        self.workflow = "Cloud Upload and Download Throttling Control"
        self.cloud_library = None
        self.client_group = None
        self.ma_machine = None

    def _cleanup(self):
        """Cleanup the entities created"""
        self.log.info("********************** CLEANUP STARTING **************************")
        try:
            # Delete Client Group
            self.log.info("Deleting client group: %s if exists", self.client_group)
            if self.commcell.client_groups.has_clientgroup(self.client_group):
                self.commcell.client_groups.delete(self.client_group)
                self.log.info("Deleted client group: %s", self.client_group)

            # Delete Cloud Library
            self.log.info("Deleting library: %s if exists", self.cloud_library)
            if self.commcell.disk_libraries.has_library(self.cloud_library):
                self.commcell.disk_libraries.delete(self.cloud_library)
                self.log.info("Deleted library: %s", self.cloud_library)
        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))
        self.log.info("********************** CLEANUP COMPLETED *************************")
        
    def validate_wf_run(self, entity, run_seq_num):
        """
            Validate whether applied throttling was successful or not based on the run sequence number
            Args:
                entity(str)     --  Name of the entity on which throttling was applied
                run_seq_num(int)    -- Run sequence number to verify the applied throttling
        """
        if entity == "Service Host of Cloud Library":
            reg_path = self.ma_machine.join_path("MediaAgent", "CloudThrottle", self.tcinputs['ServiceHost'])
            upload_reg_key = "nCloudMaxSendMBPerHour"
            download_reg_key = "nCloudMaxRecvMBPerHour"
        else:
            reg_path = "MediaAgent"
            upload_reg_key = "nCloudGlobalMaxSendMBPerHour"
            download_reg_key = "nCloudGlobalMaxRecvMBPerHour"
            
        retry_count = 0
        while True:
            if run_seq_num == 1:
                if self.ma_machine.check_registry_exists(reg_path, upload_reg_key):
                    if self.ma_machine.get_registry_value(reg_path, upload_reg_key) == '51200':
                        self.log.info("Verified upload throttling was set to 51200 MB/HR")
                        if self.ma_machine.check_registry_exists(reg_path, download_reg_key):
                            if self.ma_machine.get_registry_value(reg_path, download_reg_key) == '102400':
                                self.log.info("Verified download throttling was set to 102400 MB/HR")
                                break
                            else:
                                self.log.error("Failed to set download throttling to 102400 MB/HR")
                                raise Exception("Failed to set download throttling to 102400 MB/HR")
                        else:
                            self.log.error("Failed to set download throttling")
                            raise Exception("Failed to set download throttling")
                    else:
                        self.log.error("Failed to set upload throttling to 51200 MB/HR")
                        retry_count = retry_count + 1
                        if retry_count >= 10:
                            raise Exception("Failed to set upload throttling to 51200 MB/HR")
                        self.log.info("Sleep for 60 sec")
                        time.sleep(60)
                else:
                    self.log.error("Failed to set upload throttling")
                    retry_count = retry_count + 1
                    if retry_count >= 10:
                        raise Exception("Failed to set upload throttling")
                    self.log.info("Sleep for 60 sec")
                    time.sleep(60)

            if run_seq_num == 2:
                if self.ma_machine.check_registry_exists(reg_path, upload_reg_key):
                    if self.ma_machine.get_registry_value(reg_path, upload_reg_key) == '204800':
                        self.log.info("Verified upload throttling was modified to 204800 MB/HR")
                        if self.ma_machine.check_registry_exists(reg_path, download_reg_key):
                            self.log.error("Failed to remove download throttling")
                            raise Exception("Failed to remove download throttling")
                        else:
                            self.log.info("Verified download throttling was removed")
                            break
                    else:
                        self.log.error("Failed to modify upload throttling to 204800 MB/HR")
                        retry_count = retry_count + 1
                        if retry_count >= 10:
                            raise Exception("Failed to modify upload throttling to 204800 MB/HR")
                        self.log.info("Sleep for 60 sec")
                        time.sleep(60)
                else:
                    self.log.error("Failed to modify upload throttling")
                    retry_count = retry_count + 1
                    if retry_count >= 10:
                        raise Exception("Failed to modify upload throttling")
                    self.log.info("Sleep for 60 sec")
                    time.sleep(60)

            if run_seq_num == 3:
                if self.ma_machine.check_registry_exists(reg_path, upload_reg_key):
                    self.log.error("Failed to remove upload throttling")
                    retry_count = retry_count + 1
                    if retry_count >= 10:
                        raise Exception("Failed to remove upload throttling")
                    self.log.info("Sleep for 60 sec")
                    time.sleep(60)
                else:
                    self.log.info("Verified upload throttling was removed")
                    if self.ma_machine.check_registry_exists(reg_path, download_reg_key):
                        if self.ma_machine.get_registry_value(reg_path, download_reg_key) == '309600':
                            self.log.info("Verified download throttling was set to 309600 MB/HR")
                            break
                        else:
                            self.log.error("Failed to set download throttling to 309600 MB/HR")
                            raise Exception("Failed to set download throttling to 309600 MB/HR")
                    else:
                        self.log.error("Failed to set download throttling")
                        raise Exception("Failed to set download throttling")

            if run_seq_num == 4:
                if self.ma_machine.check_registry_exists(reg_path, upload_reg_key):
                    if self.ma_machine.get_registry_value(reg_path, upload_reg_key) == '51200':
                        self.log.info("Verified upload throttling was set to 51200 MB/HR")
                        if self.ma_machine.check_registry_exists(reg_path, download_reg_key):
                            if self.ma_machine.get_registry_value(reg_path, download_reg_key) == '102400':
                                self.log.info("Verified download throttling was set to 102400 MB/HR")
                                break
                            else:
                                self.log.error("Failed to modify download throttling to 102400 MB/HR")
                                raise Exception("Failed to modify download throttling to 102400 MB/HR")
                        else:
                            self.log.error("Failed to modify download throttling")
                            raise Exception("Failed to modify download throttling")
                    else:
                        self.log.error("Failed to set upload throttling to 51200 MB/HR")
                        retry_count = retry_count + 1
                        if retry_count >= 10:
                            raise Exception("Failed to set upload throttling to 51200 MB/HR")
                        self.log.info("Sleep for 60 sec")
                        time.sleep(60)
                else:
                    self.log.error("Failed to set upload throttling")
                    retry_count = retry_count + 1
                    if retry_count >= 10:
                        raise Exception("Failed to set upload throttling")
                    self.log.info("Sleep for 60 sec")
                    time.sleep(60)
            
            if run_seq_num == 5:
                if self.ma_machine.check_registry_exists(reg_path, upload_reg_key):
                    self.log.error("Failed to remove upload throttling")
                    retry_count = retry_count + 1
                    if retry_count >= 10:
                        raise Exception("Failed to remove upload throttling")
                    self.log.info("Sleep for 60 sec")
                    time.sleep(60)
                else:
                    self.log.info("Verified upload throttling was removed")
                    if self.ma_machine.check_registry_exists(reg_path, download_reg_key):
                        self.log.error("Failed to remove download throttling")
                        raise Exception("Failed to remove download throttling")
                    else:
                        self.log.info("Verified download throttling was removed")
                        break

    def init_tc(self):
        """Login to store"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def install_workflow(self):
        """Install the workflow if it is not installed"""
        if self.workflow_helper.has_workflow(self.workflow):
            self.workflow_helper.delete(self.workflow)

        controller = Machine()
        self.log.info("Downloading workflow %s from store", self.workflow)
        self.workflow_helper.download_workflow_from_store(self.workflow, controller.join_path(TEMP_DIR, "workflow"),
                                                          _STORE_CONFIG.Cloud.username, _STORE_CONFIG.Cloud.password)
        wait_time = 0
        while not controller.check_file_exists(controller.join_path(TEMP_DIR, "workflow", f"{self.workflow}.xml")):
            self.log.info("Please wait for download to finish")
            time.sleep(5)
            wait_time += 5
            if wait_time == 60:
                raise CVTestStepFailure("Download failed due to timeout")
        self.log.info("Installing workflow %s", self.workflow)
        self.workflow_helper.import_workflow(controller.join_path(TEMP_DIR, "workflow", f"{self.workflow}.xml"))
        self.log.info("Deploying workflow %s", self.workflow)
        self.workflow_helper.deploy_workflow(workflow=self.workflow)

    @test_step
    def run_workflow(self, optype):
        """
            Populates all the required inputs to run workflow based on optype
            Args:
                optype(str)     --  Operation Type of the workflow run
        """
        if optype == "Service Host of Cloud Library":
            entity_label = "Cloud Libraries"
            entity_value = self.cloud_library
        elif optype == "MediaAgent":
            entity_label = "MediaAgents"
            entity_value = self.tcinputs['MediaAgentName']
        else:
            entity_label = "Client Computer Groups"
            entity_value = self.client_group

        # 1st Run - To set both upload and download throttle
        self.log.info("Workflow run on %s entity - 1st Run - To set both upload and download throttle" % optype)
        self.forms.open_workflow(self.workflow)
        self.forms.select_radio_value("Perform Throttling On", optype)
        self.forms.select_dropdown_list_value(entity_label, [entity_value])
        self.forms.set_textbox_value("Throttle Network Upload Bandwidth (MB/HR)", 51200)
        self.forms.set_textbox_value("Throttle Network Download Bandwidth (MB/HR)", 102400)
        self.forms.click_action_button("OK")

        # sleep for 10 sec to wait for workflow job to submit
        time.sleep(10)
        self.workflow_helper.workflow_job_status(self.workflow, expected_state="completed")
        self.validate_wf_run(optype, 1)

        # 2nd Run - To modify upload and remove download throttle
        self.log.info("Workflow run on %s entity - 2nd Run - To modify upload and remove download throttle" % optype)
        self.forms.open_workflow(self.workflow)
        self.forms.select_radio_value("Perform Throttling On", optype)
        self.forms.select_dropdown_list_value(entity_label, [entity_value])
        self.forms.set_textbox_value("Throttle Network Upload Bandwidth (MB/HR)", 204800)
        self.forms.set_boolean("Remove Throttling on Network Download Bandwidth", "true")
        self.forms.click_action_button("OK")
        # sleep for 10 sec to wait for workflow job to submit
        time.sleep(10)
        self.workflow_helper.workflow_job_status(self.workflow, expected_state="completed")
        self.validate_wf_run(optype, 2)

        # 3rd Run - To remove upload and set download throttle
        self.log.info("Workflow run on %s entity - 3rd Run - To remove upload and set download throttle" % optype)
        self.forms.open_workflow(self.workflow)
        self.forms.select_radio_value("Perform Throttling On", optype)
        self.forms.select_dropdown_list_value(entity_label, [entity_value])
        self.forms.set_boolean("Remove Throttling on Network Upload Bandwidth", "true")
        self.forms.set_textbox_value("Throttle Network Download Bandwidth (MB/HR)", 309600)
        self.forms.click_action_button("OK")
        # sleep for 10 sec to wait for workflow job to submit
        time.sleep(10)
        self.workflow_helper.workflow_job_status(self.workflow, expected_state="completed")
        self.validate_wf_run(optype, 3)

        # 4th Run - To set upload and modify download throttle
        self.log.info("Workflow run on %s entity - 4th Run - To set upload and modify download throttle" % optype)
        self.forms.open_workflow(self.workflow)
        self.forms.select_radio_value("Perform Throttling On", optype)
        self.forms.select_dropdown_list_value(entity_label, [entity_value])
        self.forms.set_textbox_value("Throttle Network Upload Bandwidth (MB/HR)", 51200)
        self.forms.set_textbox_value("Throttle Network Download Bandwidth (MB/HR)", 102400)
        self.forms.click_action_button("OK")
        # sleep for 10 sec to wait for workflow job to submit
        time.sleep(10)
        self.workflow_helper.workflow_job_status(self.workflow, expected_state="completed")
        self.validate_wf_run(optype, 4)

        # 5th Run - To remove both upload and download throttle
        self.log.info(
            "Workflow run on %s entity - 5th Run - To remove both upload and download throttle" % optype)
        self.forms.open_workflow(self.workflow)
        self.forms.select_radio_value("Perform Throttling On", optype)
        self.forms.select_dropdown_list_value(entity_label, [entity_value])
        self.forms.set_boolean("Remove Throttling on Network Upload Bandwidth", "true")
        self.forms.set_boolean("Remove Throttling on Network Download Bandwidth", "true")
        self.forms.click_action_button("OK")
        # sleep for 10 sec to wait for workflow job to submit
        time.sleep(10)
        self.workflow_helper.workflow_job_status(self.workflow, expected_state="completed")
        self.validate_wf_run(optype, 5)

    def create_entities(self):
        """create required entities for workflow execution"""
        self._log.info("Adding ClientGroup %s..." % self.client_group)
        self.commcell.client_groups.add(self.client_group, self.tcinputs['MediaAgentName'])

        MMHelper(self).configure_cloud_library(self.cloud_library, self.tcinputs['MediaAgentName'],
                                                                    self.tcinputs["CloudMountPath"],
                                                                    self.tcinputs["CloudUserName"],
                                                                    self.tcinputs["CloudPassword"],
                                                                    self.tcinputs["CloudServerType"])

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        self.cloud_library = '%s_CloudLib-MA(%s)' % (str(self.id), self.tcinputs['MediaAgentName'])
        self.client_group = '%s_ClientGroup' % str(self.id)
        self._cleanup()
        self.ma_machine = Machine(self.tcinputs['MediaAgentName'], self.commcell)
        self.forms = Forms(self.admin_console)
        self.workflow_helper = WorkflowHelper(self, self.workflow, deploy=False)

    def run(self):
        """Main function for test case execution"""
        try:
            self.create_entities()
            self.install_workflow()
            self.admin_console.navigator.navigate_to_workflows()
            self.run_workflow("Service Host of Cloud Library")
            self.run_workflow("MediaAgent")
            self.run_workflow("Client Computer Group")

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.admin_console.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
