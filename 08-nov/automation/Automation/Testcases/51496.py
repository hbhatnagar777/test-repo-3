# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51496

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.Forms.forms import Forms
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):

    """Class for validating testcase"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate the value set for Hidden input"
        self.browser = None
        self.adminconsole = None
        self.forms = None
        self.show_to_user = False
        self._workflow = None
        self.workflow_name = 'WF_HIDDEN_INPUT'
        self.tcinputs = {
            'InputString': None
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name)

    def init_tc(self):
        """Opens the webconsole application"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.adminconsole = AdminConsole(
            self.browser,
            self.commcell.webconsole_hostname
        )
        self.adminconsole.login(
            self.inputJSONnode['commcell']['commcellUsername'],
            self.inputJSONnode['commcell']['commcellPassword']
        )
        self.adminconsole.wait_for_completion()

    def init_forms(self):
        """Access the forms application"""
        self.adminconsole.navigator.navigate_to_workflows()
        self.forms = Forms(self.adminconsole)

    def start_step1(self):
        """Performs the steps
        1. Open the workflow form
        2. Validate the window
        3. Set values in the input window
        4. Checks whether the hidden input not displaying
        5. Submit the window
        """
        self.forms.open_workflow(self.workflow_name)
        if self.forms.is_form_open(self.workflow_name):
            self.adminconsole.wait_for_completion()
            self.forms.set_textbox_value('INP_STRING', self.tcinputs['InputString'])
            try:
                self.forms.set_textbox_value('INP_HIDDEN_STRING', self.tcinputs['InputString'])
                raise Exception(
                    "Hidden Input [INP_HIDDEN_STRING] is listing in the input window")
            except Exception as excp:
                if 'Unable to locate element' in str(excp):
                    self.log.info("Hidden Input [INP_HIDDEN_STRING] is not listing in"
                                  "input window as expected")
                else:
                    raise Exception(
                        "Validation of workflow {0} failed with exception {1}"
                        .format(self.workflow_name, excp))
            self.forms.submit()
            self.adminconsole.wait_for_completion()
        else:
            self.log.info("Workflow Input window isnt loaded")
            raise Exception("Workflow Input Window isnt loaded")

    def start_step2(self):
        """Performs the steps
        1. Validate the window
        2. Set values in the opened pop-up input window
        3. Checks whether the hidden input not displaying
        4. Submit the window
        """
        self.forms.is_form_open('Hidden Input Validation - 1 (Popup)')
        self.forms.set_textbox_value('INP_POP_STRING', self.tcinputs['InputString'])
        try:
            self.forms.set_textbox_value('INP_POP_HIDDEN_STRING', self.tcinputs['InputString'])
            raise Exception(
                "Hidden Input [INP_POP_HIDDEN_STRING] is listing in the popup window")
        except Exception as excp:
            if 'Unable to locate element' in str(excp):
                self.log.info("Hidden Input [INP_HIDDEN_STRING] is not listing in"
                              "popup window as expected")
            else:
                raise Exception("Validation of workflow {0} failed with exception {1}"
                                .format(self.workflow_name, excp))
        self.forms.submit()
        self.adminconsole.wait_for_completion()

    def start_step3(self):
        """Performs the steps
        1. Validate the window
        2. Validate the content displayed in information message
        This is to ensure the hidden input's value is accessible
        3. Submit the window
        """
        self.forms.is_form_open('Hidden Input Validation - 2 (Info)')
        value = self.forms.informational_message()
        self.log.info("Informational message returned %s", format(value))
        if value == self.workflow_name:
            self.log.info("Hidden string value displayed in informational"
                          "message window correctly")
        else:
            raise Exception("Hidden string value is not displayed in"
                            "informational message window")
        self.forms.submit()

    def start_step4(self):
        """Performs the steps
        1. Submit Open interaction
        2. Set values in the userinput window
        3. Check whether hidden input not displaying
        4. Submit the window
        """
        self.forms.submit_interaction('Hidden Input Validation - 3 (UserInput)')
        self.forms.set_textbox_value('INP_USER_STRING', self.tcinputs['InputString'])
        try:
            self.forms.set_textbox_value('INP_USER_HIDDEN_STRING', self.tcinputs['InputString'])
            raise Exception("Hidden input [INP_USER_HIDDEN_STRING] is listing in the "
                            "userinput window")
        except Exception as excp:
            if 'Unable to locate element' in str(excp):
                self.log.info("Hidden Input [INP_USER_HIDDEN_STRING] is not listing in"
                              "userinput window as expected")
            else:
                raise Exception("Validation of workflow {0} failed with exception {1}"
                                .format(self.workflow_name, excp))
        self.forms.submit()

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.init_forms()
            self.start_step1()
            self.start_step2()
            self.start_step3()
            self.start_step4()
            self._workflow.workflow_job_status(self.workflow_name)
        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)
        finally:
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)
            self._workflow.delete(self.workflow_name)
