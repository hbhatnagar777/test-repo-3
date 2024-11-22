# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51515

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper
from Web.Common.cvbrowser import (
    Browser, BrowserFactory)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.Forms.forms import Forms,Actions

class TestCase(CVTestCase):

    """Class for validating Conditional Transitions"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Conditional Transitions"
        self._workflowhelper = None
        self.adminconsole = None
        self.browser = None
        self.workflow_name = 'WF_CONDITIONALTRANSITION'

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)

    def run(self):
        """Main function of this testcase execution"""
        try:
            _ = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                }, wait_for_job=False)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.adminconsole.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword']
            )
            self.adminconsole.wait_for_completion()
            self.adminconsole.navigator.navigate_to_workflows()
            forms = Forms(self.adminconsole)
            actions = Actions(self.adminconsole)
            actions.goto_Actions()
            actions.goto_Open_Actions()
            actions.open_Action('condition1')
            self.adminconsole.wait_for_completion()
            forms.click_action_button('OK')
            self.adminconsole.wait_for_completion()
            forms.click_action_button('OK')
            self._workflowhelper.workflow_job_status(self.workflow_name)

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)
