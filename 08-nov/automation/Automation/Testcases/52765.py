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

    run()                   --  Main function for testcase execution

"""

# Test suite Imports
from cvpysdk.workflow import WorkFlow
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.serverhelper import ServerTestCases
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.Forms.forms import Forms


class TestCase(CVTestCase):
    """Class for valiating this testcase"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Workflow - Validate qscript to hide/show workflow in Commcell GUI"
        self.machine = None
        self.workflow = None
        self.workflow_id = None
        self.admin_console = None
        self.tcinputs = {
            'ScriptLocation': None
        }

    def setup(self):
        """Setup function of this testcase"""
        self.machine = Machine(self.commcell.commserv_name, self.commcell)
        if not self.machine.check_file_exists(self.tcinputs['ScriptLocation'] + "/WorkflowVisibility.sqle"):
            raise Exception("Script file 'WorkflowVisibility.sqle' is not present in script location")

    def run(self):
        """Main function for testcase execution"""
        try:
            self.log.info("Querying CommServDB to fetch the hidden workflow")
            query = "select TOP 1 WorkflowId,Name from WF_Definition with (nolock) where flags&16>0"
            self.csdb.execute(query)
            self.workflow_id = self.csdb.fetch_one_row()[0]
            self.workflow = self.csdb.fetch_one_row()[1]
            self.log.info("Processing for hidden workflow [%s]", self.workflow)
            if self.commcell.workflows.has_workflow(self.workflow):
                raise Exception("Hidden workflow [{0}] shouldnt be shown in GET Workflow API response".
                                format(self.workflow))
            self.log.info("Hidden workflow isnt shown in GET Workflow API response as expected")
            wf_obj = WorkFlow(self.commcell, self.workflow, self.workflow_id)
            self.log.info("Version of Hidden workflow [%s] (pre-script execution) is %s", self.workflow, wf_obj.version)
            script_location = self.tcinputs['ScriptLocation'] + "/WorkflowVisibility.sqle"
            show_command = r"qscript -f '" + script_location + "' -i '" + self.workflow + "' show"
            self.machine.execute_command(show_command)
            self.commcell.refresh()
            if not self.commcell.workflows.has_workflow(self.workflow):
                raise Exception("Post execution of WorkflowVisibility qscript, workflow [{0}] is not visible".
                                format(self.workflow))
            self.log.info("Post execution of WorkflowVisibility qscript, workflow [%s] is visible as expected",
                          self.workflow)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword']
            )
            self.admin_console.navigator.navigate_to_workflows()
            forms = Forms(self.admin_console)
            forms.open_workflow(self.workflow)
            self.log.info("Workflow [%s] is listing in forms application correctly", self.workflow)
            forms.close_form()
            self.log.info("Reverting back the visibility change")
            hide_command = r"qscript -f '" + script_location + "' -i '" + self.workflow + "' hide"
            self.machine.execute_command(hide_command)

        except Exception as excp:
            self.log.error("Exception raise : %s", str(excp))
            ServerTestCases(self).fail(excp)

        finally:
            if self.admin_console:
                AdminConsole.logout_silently(self.admin_console)
                Browser.close_silently(self.browser)
