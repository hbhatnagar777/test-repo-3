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
import glob
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.Forms.forms import Forms
from Server.JobManager.jobmanager_helper import JobManager
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):
    """Class for valiating this testcase"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - File upload Operations using UserInput/PopupInput"
        self.browser = None
        self.adminconsole = None
        self.show_to_user = False
        self._workflow = None
        self.workflow_name = 'WF_FILE_UPLOAD_OPERATIONS'

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name)

    def run(self):
        """Main function for testcase execution"""
        try:
            flag = False
            files = [f for f in glob.glob(constants.WORKFLOW_DIRECTORY + "**/*.xml", recursive=True)]
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
            self.adminconsole.navigator.navigate_to_workflows()
            forms = Forms(self.adminconsole)
            forms.open_workflow(self.workflow_name)
            if forms.is_form_open(self.workflow_name):
                self.adminconsole.wait_for_completion()
                forms.select_file('Upload File:', [files[0]])
                forms.submit()
                flag = True
                forms.is_form_open('Workflow Description')
                forms.submit()
                self.adminconsole.wait_for_completion()
                forms.is_form_open('Upload Files - Pop Up Activity')
                forms.select_file('Upload Files:', [files[1], files[2]])
                forms.select_file('Upload Single File:', [files[3]])
                forms.click_action_button('Submit')
                self.adminconsole.wait_for_completion()
                forms.submit_interaction('Upload Files - UserInput Activity')
                self.adminconsole.wait_for_completion()
                forms.is_form_open('Upload Files - UserInput Activity')
                forms.select_file('Upload Files:', [files[4], files[5]])
                forms.select_file('Upload Single File:', [files[6]])
                forms.click_action_button('Submit')
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
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)
            self._workflow.cleanup()
