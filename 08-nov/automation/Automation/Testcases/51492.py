# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.windows_machine import WindowsMachine
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):

    """Class for validating Workflow - (TR) - Validate ExecuteCommand Activity Output with Form feed characters"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Workflow - (TR) - Validate ExecuteCommand Activity Output with Form feed characters"
        self.workflow_name = "WF_FORMFEED_STACKTRACE"
        self.wf_helper = None
        self.custom_name = None
        self.win_machine = None
        self.job = None
        self.log_output = None
        self.form_feed_char_name = None

    def setup(self):
        """Setup function of this test case"""
        self.wf_helper = WorkflowHelper(self, wf_name=self.workflow_name)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.custom_name = OptionsSelector(self.commcell).get_custom_str()
            self.form_feed_char_name = '♀{0}♀'.format(self.custom_name)
            self.log.info("Creating a dummy xml without root")
            xml = "<body>value</body><tail>value</tail>"
            self.log.info("passing the xml %s to the WF, WF is expected to trace the error", xml)
            self.job = self.wf_helper.execute(workflow_json_input=
                                              {"args": self.form_feed_char_name,
                                               "xml": xml,
                                               "client": self.commcell.commserv_client.client_name},
                                              wait_for_job=False)
            self.win_machine = WindowsMachine(machine_name=self.commcell.commserv_client.client_name,
                                              commcell_object=self.commcell)
            if JobManager(_job=self.job, commcell=self.commcell).wait_for_state():
                self.log_output = self.win_machine.get_logs_for_job_from_file(
                    job_id=self.job.job_id, log_file_name="WorkflowCustom.log")
                if '♀' in self.log_output[0] or self.custom_name not in self.log_output[0]:
                    raise Exception("Validation failed as Form Feed Character not trimmed "
                                    "or Workflow did not execute as expected")
                if 'Exception' not in self.log_output[1]:
                    raise Exception("Validation failed as Stack Trace Error not shown in logs")
                self.log.info("Validation successful for activity output with form feed characters")

            else:
                raise Exception("Job failed")

        except Exception as exp:
            self.wf_helper.test.fail(exp)

        finally:
            self.wf_helper.delete(self.workflow_name)
