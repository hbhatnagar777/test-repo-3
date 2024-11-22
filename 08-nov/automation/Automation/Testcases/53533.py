# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 53533

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validating QSDKsession timeout value"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate QSDKSession timeout value"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_Email'
        self._utility = OptionsSelector(self._commcell)
        self.sqlobj = None

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)
        self.machine = Machine(self.commcell.commserv_name, self._commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:

            self.log.info("set qsdksession timeout value in registry")
            self.machine.create_registry('WFEngine', 'qsdkTokenTimeout', 120, "DWord")

            _ = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                    'email_id': self._workflowhelper.email
                })

            self.log.info("Check qsdksession timeout value from DB ")
            query = 'select TOP 1 timeout,created from UMQSDKSessions where consoleType = 18 order by created DESC'
            res = self._utility.exec_commserv_query(query)
            timeout_value_set = res[0][0]

            if timeout_value_set != '120':
                raise Exception("timeoutvalue is not set as per the registry")


        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self.machine.remove_registry('WFEngine', 'qsdkTokenTimeout')
            self._workflowhelper.cleanup()
