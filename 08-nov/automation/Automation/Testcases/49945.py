# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this testcase

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()              --  Initializes test case class object

    setup()                 --  Setup function of the test case

    button_validation()     --  Validates custom button

    run()                   --  Main function for testcase execution

"""

# Test suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.Forms.forms import Forms
from Server.JobManager.jobmanager_helper import JobManager
from Server.Workflow.workflowhelper import WorkflowHelper

_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for valiating this testcase"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Wizard block test through pop-up input activities"
        self.browser = None
        self.admin_console = None
        self.forms = None
        self.show_to_user = False
        self._workflow = None
        self.workflow_name = 'WF_WIZARD_BLOCK'

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name)

    def button_validation(self, expected_buttons):
        """Validates the available action button on the input window
        Args:
            expected_button     (list)  --  Expected Action button in window

        Returns:
            Boolean

            true    -- expected button available

            false   -- expected button may missing or additional button available
        """
        available_buttons = self.forms.get_action_button_labels()
        available_buttons.sort()
        expected_buttons.sort()
        return available_buttons == expected_buttons

    def run(self):
        """Main function for testcase execution"""
        try:
            flag = False
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword']
            )
            self.admin_console.navigator.navigate_to_workflows()
            self.forms = Forms(self.admin_console)
            self.forms.open_workflow(self.workflow_name)
            if self.forms.is_form_open(self.workflow_name):
                self.forms.set_textbox_value('Provide email id for sending reports : ', _CONFIG.email.email_id)
                self.forms.submit()
                flag = True
                self.admin_console.wait_for_completion()
                self.forms.is_form_open('Popup Input Window - 1')
                if not self.button_validation(['NEXT', 'CANCEL']):
                    raise Exception("Expected Action button is not available in First popup window of wizard block")
                self.forms.set_textbox_value('Enter Input1', 'AutomationInput1')
                self.forms.click_action_button('Next')
                self.admin_console.wait_for_completion()
                self.forms.is_form_open('Popup Input Window - 2')
                self.forms.click_action_button('Back')
                self.admin_console.wait_for_completion()
                if not self.forms.is_form_open('Popup Input Window - 1'):
                    raise Exception("Previous popup window isnt open in Wizard block validation")
                self.log.info("Validated the back button")
                self.forms.click_action_button('Next')
                self.admin_console.wait_for_completion()
                self.forms.is_form_open('Popup Input Window - 2')
                if not self.button_validation(['BACK', 'NEXT', 'CANCEL']):
                    raise Exception("Expected Action button is not available in Second popup window of wizard block")
                self.forms.set_textbox_value('Enter Input2', 'AutomationInput2')
                self.forms.click_action_button('Next')
                self.admin_console.wait_for_completion()
                self.forms.is_form_open('Popup Input Window - 3')
                if not self.button_validation(['BACK', 'FINISH', 'CANCEL']):
                    raise Exception("Expected Action button is not available in final popup window of wizard block")
                self.forms.set_textbox_value('Enter Input3', 'AutomationInput3')
                self.forms.click_action_button('Finish')
                self._workflow.workflow_job_status(self.workflow_name)
                flag = False
            else:
                raise Exception("Workflow Input Window isnt loaded")
        except Exception as excp:
            self._workflow.test.fail(excp)
            if flag and 'validation failed' not in str(excp):
                job = self._workflow.workflow_job_status(self.workflow_name, wait_for_job=False)
                job_manager = JobManager(job, self._commcell)
                job_manager.modify_job('kill')
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self._workflow.cleanup()
