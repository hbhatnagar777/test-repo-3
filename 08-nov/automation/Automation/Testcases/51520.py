# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51520

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
import glob
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.Forms.forms import Forms
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validating Edge activities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Edge activities"
        self.browser = None
        self.admin_console = None
        self.show_to_user = False
        self._workflow = None
        self.workflow_name = 'WF_EDGE'

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)

    def run(self):
        """Main function of this testcase execution"""
        try:
            workflow_edge_config = self._workflowhelper.workflow_config.EDGE
            shareuser = workflow_edge_config.shareuser
            shareEmail = workflow_edge_config.shareEmail
            sharePassword = self._workflowhelper.workflow_config.ComplexPasswords.CommonPassword
            files = [f for f in glob.glob(constants.WORKFLOW_DIRECTORY + "**/*.xml", recursive=True)]
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                shareuser,
                sharePassword
            )
            self.admin_console.wait_for_completion()
            self.admin_console.navigator.navigate_to_workflows()
            forms = Forms(self.admin_console)
            forms.open_workflow(self.workflow_name)
            if forms.is_form_open(self.workflow_name):
                self.admin_console.wait_for_completion()
                forms.select_file('INP_FILE', [files[0]])
                forms.set_textbox_value('shareuser', shareuser)
                forms.set_textbox_value('shareEmail', shareEmail)
                forms.submit()
                time.sleep(20)
                self._workflowhelper.workflow_job_status(self.workflow_name)

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self._workflowhelper.cleanup()
