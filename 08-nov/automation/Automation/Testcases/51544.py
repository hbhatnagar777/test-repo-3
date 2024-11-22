# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.Forms.forms import Forms
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    print("Inside Class")

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - (TR) - Validate the Searchable input in Interactive Activity"
        self.browser = None
        self.adminconsole = None
        self.show_to_user = False
        self._workflow = None
        self.workflow_name = 'WF_SEARCHABLE_INPUT'
        self.tcinputs = {
            'SearchableLabel': None,
            'SearchableValue': None,
            'SearchableLabelList1': None,
            'SearchableLabelList2': None,
            'SearchableValueList1': None,
            'SearchableValueList2': None,
            'SearchableUnicode': None,
            'StringValue': None

        }

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name)

    def run(self):
        try:
            flag = False
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
                forms.submit()
                self.adminconsole.wait_for_completion()
                flag = True
                job = self._workflow.workflow_job_status(self.workflow_name, wait_for_job=False)
                self.adminconsole.wait_for_completion()
                forms.is_form_open('Searchable Test window-1')
                forms.set_textbox_value('Enter String Input', self.tcinputs['StringValue'])
                forms.select_searchable_dropdown_value('Enter value for Searchable with Label',
                                                       self.tcinputs['SearchableLabel'])
                forms.select_searchable_dropdown_value('Enter value for Searchable with value',
                                                       self.tcinputs['SearchableValue'])
                forms.select_searchable_dropdown_value('Select list of values - based on label',
                                                       self.tcinputs['SearchableLabelList1'])
                forms.select_searchable_dropdown_value('Select list of values - based on label',
                                                       self.tcinputs['SearchableLabelList2'])
                forms.select_searchable_dropdown_value('Select list of values - based on value',
                                                       self.tcinputs['SearchableValueList1'])
                forms.select_searchable_dropdown_value('Select list of values - based on value',
                                                       self.tcinputs['SearchableValueList2'])
                forms.click_action_button('Next')
                self.adminconsole.wait_for_completion()
                forms.is_form_open('Searchable Test window-2')
                forms.select_searchable_dropdown_value('Select Unicode Character', self.tcinputs['SearchableUnicode'])
                forms.select_searchable_dropdown_value('INP_TEST', 'test_30')
                forms.click_action_button('Next')
                self.adminconsole.wait_for_completion()
                forms._driver.refresh()
                forms.submit_interaction('Searchable Test window-User Input')
                self.adminconsole.wait_for_completion()
                forms.set_textbox_value('Enter String Input', self.tcinputs['StringValue'])
                forms.select_searchable_dropdown_value('Enter value for searchable label',
                                                       self.tcinputs['SearchableLabel'])
                forms.select_searchable_dropdown_value('Enter value for searchable value',
                                                       self.tcinputs['SearchableValue'])
                forms.select_searchable_dropdown_value('Enter value for Searchable label list',
                                                       self.tcinputs['SearchableLabelList1'])
                forms.select_searchable_dropdown_value('Enter value for Searchable label list',
                                                       self.tcinputs['SearchableLabelList2'])
                forms.select_searchable_dropdown_value('Enter value for Searchable value list',
                                                       self.tcinputs['SearchableValueList1'])
                forms.select_searchable_dropdown_value('Enter value for Searchable value list',
                                                       self.tcinputs['SearchableValueList2'])
                forms.submit()
                self._workflow.workflow_job_status(self.workflow_name)
                flag = False

            else:
                raise Exception("Workflow Input Window isnt loaded")
        except Exception as excp:
            self._workflow.test.fail(excp)
            if flag and 'validation failed' not in str(excp):
                job_manager = JobManager(job, self._commcell)
                job_manager.modify_job('kill')

        finally:
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)
            self._workflow.delete(self.workflow_name)
