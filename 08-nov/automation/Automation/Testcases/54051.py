# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initializes test case class object

    setup()         --  setup function of this test case

    download_workflow() -- method to download workflow

    deploy_workflow()   -- method to deploy workflow

    execute_workflow()  -- method to execute workflow

    tear_down() -- tear down method

    run()           --  run function of this test case

Example input:
    "54051": {
        "hanaPseudoClientName": "HanaPseudoClient",
        "instanceName": "instance",
        "restoreTimeInUTC": "Restore time in UTC",
        "emailId": "email@id.com"
        }
"""

from time import sleep
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import TEMP_DIR, FAILED
from AutomationUtils.machine import Machine
from Server.Workflow.workflowhelper import WorkflowHelper
_STORE_CONFIG = get_config()

class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Install,Execute Workflow 'Check HANA Restore Possibility'"
        self.workflow = "CheckHANARestorePossibility"
        self.workflow_file_name = "Check HANA Restore Possibility"
        self.tcinputs = {
            "hanaPseudoClientName": None,
            "instanceName": None,
            "restoreTimeInUTC": None,
            "emailId": None
        }
        self.workflow_obj = None
        self.controller_obj = None
        self.pkg_file_path = None

    def setup(self):
        try:
            self.workflow_obj = WorkflowHelper(self, self.workflow, deploy=False)
            self.controller_obj = Machine()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def download_workflow(self):
        """method to download the workflow"""
        self.pkg_file_path = self.controller_obj.join_path(TEMP_DIR, "workflow")
        self.workflow_obj.download_workflow_from_store(self.workflow_file_name, self.pkg_file_path, _STORE_CONFIG.Cloud.username, _STORE_CONFIG.Cloud.password)
        i = 0
        while not self.controller_obj.check_file_exists(self.controller_obj.join_path(self.pkg_file_path, f"{self.workflow_file_name}.xml")):
            self._LOG.info("Please wait for download to finish")
            sleep(5)
            i += 1
            if i == 20:
                raise CVTestStepFailure("Download failed due to timeout")

    @test_step
    def deploy_workflow(self):
        """delete workflow if exists and deploy latest workflow"""
        if self.workflow_obj.has_workflow(self.workflow):
            self.workflow_obj.delete(self.workflow)
        self.workflow_obj.import_workflow(workflow_xml=self.controller_obj.join_path(self.pkg_file_path, f"{self.workflow_file_name}.xml"))
        self.workflow_obj.deploy_workflow(workflow=self.workflow)


    @test_step
    def execute_workflow(self):
        """method to execute workflow """
        self.workflow_obj.execute(
            {
                'HANA_Pseudo_Client_Name': self.tcinputs['hanaPseudoClientName'],
                'Instance_Name': self.tcinputs['instanceName'],
                'Restore_Time_In_UTC': self.tcinputs['restoreTimeInUTC'],
                'Email': self.tcinputs['emailId']
            })

    def tear_down(self):
        """tear down for this testcase"""
        self.workflow_obj.delete(self.workflow)
        self.controller_obj.remove_directory(self.pkg_file_path)

    def run(self):
        try:
            self.download_workflow()
            self.deploy_workflow()
            self.execute_workflow()

        except Exception as err:
            self.log.error('Failed with error: %s', err)
            self.status = FAILED
