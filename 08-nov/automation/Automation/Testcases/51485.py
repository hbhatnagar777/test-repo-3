# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51485

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
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validating SQl login cases"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate SQl login cases"
        self._workflow = None
        self.workflow_name = 'WF_SqlQuery'

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)
        self._utility = OptionsSelector(self.commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:

            workflow_sql_config = self._workflowhelper.workflow_config.SQL
            sapass = workflow_sql_config.sa
            sqladmin_cvpass = self._utility.get_paccess_passwd()
            noncsdb = workflow_sql_config.NonCsDb
            winauthuser = workflow_sql_config.WinAuthUser
            winauthpass = workflow_sql_config.WinAuthPass

            _ = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                    'saPass': sapass,
                    'sqladmin_cvPass' : sqladmin_cvpass,
                    'Noncsdb': noncsdb,
                    'WinAuthUser': winauthuser,
                    'WinAuthPass': winauthpass

                })

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
