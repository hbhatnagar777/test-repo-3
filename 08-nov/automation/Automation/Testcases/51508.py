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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case
"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Forms.forms import Forms
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Reports.storeutils import StoreUtils


class TestCase(CVTestCase):
    """WORKFLOW - V1,V2 forms validation"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "WORKFLOW - V1,V2 forms validation"
        self.workflow_name = "WF_V1V2"
        self.browser = None
        self.webconsole = None
        self.factory = None
        self.driver = None
        self.forms = None
        self.web_adapter = None
        self.wf_helper = None
        self.machine = None
        self.url = None
        self.workflow_ID = None

    def validate_v1_form(self):
        """Function to validate V1 forms"""
        self.log.info("Checking for V1 forms")
        if not self.forms.is_v1_form_open(self.workflow_name):
            raise Exception("Workflow Input Window is not loaded for v1 form")
        self.forms.set_textbox_value_for_v1_form(label='Data', value='testcase')
        self.forms.submit_v1_form()
        if not self.forms.is_v1_form_open("Popping up"):
            raise Exception("Popup window is not loaded for v1 form")
        self.forms.click_action_button_in_v1_form("Ok")
        if not self.forms.is_v1_form_open("INFO"):
            raise Exception("Information window is not loaded for v2 form")
        self.forms.click_action_button_in_v1_form("Ok")
        self.webconsole.wait_till_load_complete()

    def submit_v1_form_interaction(self):
        self.forms.submit_interaction("Testcase_validation")
        self.webconsole.wait_till_load_complete()
        self.forms.click_action_button_in_v1_form("Yes")
        self.webconsole.wait_till_load_complete()

    def validate_v2_form(self):
        """Function to validate V2 forms"""
        if not self.forms.is_form_open(self.workflow_name):
            raise Exception("Workflow Input Window is not loaded for v2 form")
        self.forms.set_textbox_value(label="Data", value="testcase")
        self.forms.submit()
        if not self.forms.is_form_open("Popping up"):
            raise Exception("Popup window is not loaded for v2 form")
        self.forms.set_textbox_value(label="Press_Ok", value="testcase")
        self.forms.click_action_button("Ok")
        if not self.forms.is_form_open("INFO"):
            raise Exception("Information window is not loaded for v2 form")
        self.forms.click_action_button("Ok")
        self.webconsole.wait_till_load_complete()

    def submit_v2_form_interaction(self):
        self.forms.submit_interaction("Testcase_validation")
        self.webconsole.wait_till_load_complete()
        self.forms.click_action_button("Yes")
        self.webconsole.wait_till_load_complete()

    def setup(self):
        """Setup function of this test case"""
        self.machine = Machine(commcell_object=self.commcell)
        self.wf_helper = WorkflowHelper(self, wf_name=self.workflow_name)
        self.storeutils = StoreUtils(self)

    def login_and_load(self):
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
        self.driver = self.webconsole._driver
        self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                              self.inputJSONnode['commcell']['commcellPassword'])
        self.webconsole.wait_till_load_complete()
        self.workflow_ID = self.commcell.workflows.get(self.workflow_name).workflow_id
        self.webconsole.goto_forms()
        self.forms = Forms(self.webconsole)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.login_and_load()
            self.forms.open_workflow(self.workflow_name)
            self.validate_v2_form()
            self.submit_v2_form_interaction()
            self.url = "{0}?tab=0&workflowName={1}&workflowId={2}&v1=true"\
                .format(self.driver.current_url, self.workflow_name, self.workflow_ID)
            self.driver.get(self.url)
            self.validate_v1_form()
            interaction_id = self.wf_helper.user_interactions(
                username='admin')[0]['interactionId']
            self.url = "{0}?tab=1&interactionId={1}&v1=true"\
                .format(self.driver.current_url, interaction_id)
            self.driver.get(self.url)
            self.webconsole.wait_till_load_complete()
            self.forms.click_action_button_in_v1_form("Yes")
            self.webconsole.wait_till_load_complete()
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            self.machine.create_registry(
                key='WebConsole', value='useV2Forms', data='false')
            OptionsSelector(self.commcell).sleep_time()
            self.login_and_load()
            self.forms.open_workflow(self.workflow_name)
            self.validate_v1_form()
            self.submit_v1_form_interaction()

        except Exception as excp:
            self.storeutils.handle_testcase_exception(excp)

        finally:
            self.wf_helper.delete(self.workflow_name)
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            self.machine.remove_registry(key='WebConsole', value='useV2Forms')
