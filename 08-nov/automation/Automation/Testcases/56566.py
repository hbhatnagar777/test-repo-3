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

    start_step1()           --  Opens the workflow and submit input window

    start_step2()           --  Fills the popup input window and submits

    start_step3()           --  Fills the User Interaction window and submits

    run()                   --  Main function for testcase execution

"""

# Test suite Imports
import glob
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import (
    handle_testcase_exception, TestStep
)
from Web.Common.exceptions import (
    CVTestStepFailure, CVTestCaseInitFailure
)
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.WebConsole.Forms.forms import Forms
from Server.JobManager.jobmanager_helper import JobManager
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):
    """Class for valiating this testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[WORKFLOW] Validate Workflows page in adminconsole"
        self.browser = None
        self.admin_console = None
        self.show_to_user = False
        self._workflow = None
        self.workflow_name = 'WF_FILE_UPLOAD_OPERATIONS'
        self.forms = None
        self.files = None
        self.flag = False

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name)

    @test_step
    def init_tc(self):
        """Naviagate the adminconsole"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword']
            )
            self.admin_console.navigator.navigate_to_workflows()
            self.forms = Forms(self.admin_console)
        except Exception as excp:
            raise CVTestCaseInitFailure(excp) from excp

    @test_step
    def start_step1(self):
        """Opens the workflow and submit input window"""
        self.forms.open_workflow(self.workflow_name)
        if not self.forms.is_form_open(self.workflow_name):
            raise CVTestStepFailure("Workflow Input Window isnt loaded")
        self.forms.select_file('Upload File:', [self.files[0]])
        self.forms.submit()
        self.flag = True
        self.forms.is_form_open('Workflow Description')
        self.forms.submit()

    @test_step
    def start_step2(self):
        """Fills the popup input window and submits"""
        self.forms.is_form_open('Upload Files - Pop Up Activity')
        self.forms.select_file('Upload Files:', [self.files[1], self.files[2]])
        self.forms.select_file('Upload Single File:', [self.files[3]])
        self.forms.click_action_button('Submit')

    @test_step
    def start_step3(self):
        """Fills the User Interaction window and submits"""
        self.forms.submit_interaction('Upload Files - UserInput Activity')
        self.forms.is_form_open('Upload Files - UserInput Activity')
        self.forms.select_file('Upload Files:', [self.files[4], self.files[5]])
        self.forms.select_file('Upload Single File:', [self.files[6]])
        self.forms.click_action_button('Submit')

    def run(self):
        """Main function for testcase execution"""
        try:
            self.init_tc()
            self.files = [f for f in glob.glob(constants.WORKFLOW_DIRECTORY + "**/*.xml", recursive=True)]
            self.start_step1()
            self.start_step2()
            self.start_step3()
            self._workflow.workflow_job_status(self.workflow_name)
            self.flag = False

        except Exception as err:
            handle_testcase_exception(self, err)
            if self.flag and 'validation failed' not in str(err):
                job = self._workflow.workflow_job_status(self.workflow_name, wait_for_job=False)
                job_manager = JobManager(job, self._commcell)
                job_manager.modify_job('kill')
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self._workflow.cleanup()
