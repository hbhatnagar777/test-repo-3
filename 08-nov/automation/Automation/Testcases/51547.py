# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51547

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from cvpysdk.workflow import WorkFlow
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.machine import Machine

class TestCase(CVTestCase):

    """Class for validating qscript to fix duplicate workflows"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate the qscript to fix duplicate workflows which have duplicate GUID"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_EMAIL'
        self._utility = OptionsSelector(self._commcell)
        self.tcinputs = {
            'script_location': None,
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name, deploy=False)
        _CS_CONFIG = get_config()
        db_uname = _CS_CONFIG.Schedule.db_uname
        db_password = _CS_CONFIG.Schedule.db_password
        self.sqlobj = MSSQL(self.commcell.commserv_name + r'\commvault', db_uname, db_password, "commserv")
        self.machine = Machine(self.commcell.commserv_name, self._commcell)
        if not self.machine.check_file_exists(self.tcinputs['script_location'] + "/FixDuplicateWorkflowGuids.sqle"):
            raise Exception("Script file is not present in script location")

    def run(self):
        """Main function of this testcase execution"""
        try:

            self._workflowhelper.deploy()
            self._workflow = WorkFlow(commcell_object=self.commcell, workflow_name=self.workflow_name)
            workflow_definition = self._workflow._get_workflow_definition()
            workflow_uniqueguid = workflow_definition['uniqueGuid']

            # Clone the workflow
            self._workflowhelper.clone("clonewf", self.workflow_name)
            self._cloneworkflowhelper = WorkflowHelper(self, "clonewf", deploy=False)
            self._cloneworkflowhelper.deploy()
            self._cloneworkflow = WorkFlow(commcell_object=self.commcell, workflow_name="clonewf")

            cloneworkflow_definition = self._cloneworkflow._get_workflow_definition()
            cloneworkflow_uniqueguid = cloneworkflow_definition['uniqueGuid']

            if workflow_uniqueguid != cloneworkflow_uniqueguid:
                self.log.info("Unique GUID's are not same. Setting the it to same in DB")
                query = "update WF_definition SET uniqueguid= '{}' where name like '%clonewf%'".format(workflow_uniqueguid)
                self.sqlobj.execute(query)
            else:
                raise Exception("GUID for workflows is same after cloning")

            script_location = self.tcinputs['script_location'] + "/FixDuplicateWorkflowGuids.sqle"
            self.log.info("Running the qscript to fix duplicate guids")
            command = r"qscript -f '" + script_location + "'"
            self.machine.execute_command(command)

            if workflow_uniqueguid == cloneworkflow_uniqueguid:
                raise Exception("GUID's are same even after running the script")


            self._workflowhelper.execute(
                {
                    'INP_EMAIL_ID': self._workflowhelper.email,
                    'INP_WORKFLOW_NAME': self.workflow_name}, wait_for_job=False
            )

            if workflow_uniqueguid == cloneworkflow_uniqueguid:
                raise Exception("GUID's are same even after running the workflow")

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
            self._cloneworkflowhelper.cleanup()
