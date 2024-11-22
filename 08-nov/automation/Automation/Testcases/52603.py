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

from datetime import datetime, timedelta
import pytz
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.idautils import CommonUtils


class TestCase(CVTestCase):

    """Workflow - Job Management"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Workflow - Job Management"
        self.workflow_name_job = "WF_JOB_MGMT"
        self.workflow_name_api = "WF_API_MODE"
        self.wf_helper_job = None
        self.wf_helper_api = None
        self.workflow_obj = None
        self.tc = None
        self.machine = None
        self.command = None
        self.option_selector = None
        self.paccess = None
        self.pexecaccess = None
        self.instance = None
        self.tcinputs = {
            "MachineHostName": None,
            "CustomInstallationPath": None,
            "WorkflowEngineName": None,
            "ScriptLocation": None
        }

    def validate_user_interaction(self):
        """ Method to validate user interaction activity"""
        self.wf_helper_job.workflow_job_status(
            wf_name=self.workflow_name_job, expected_state='waiting')
        interaction = self.wf_helper_job.user_interactions(username='admin')[0]
        self.wf_helper_job.submit_interaction(
            interaction=interaction, input_xml="", action='Submit')
        self.log.info("Validated user interaction activity")

    def validate_suspend_activity(self):
        """ Method to validate suspend job activity"""
        self.wf_helper_job.workflow_job_status(
            wf_name=self.workflow_name_job, expected_state='suspended')
        self.wf_helper_job.workflow_job_status(
            wf_name=self.workflow_name_job)
        self.log.info("Validated suspend activity")

    def validate_resume_activity(self, job):
        """ Method to validate resume job activity"""
        self.wf_helper_job.workflow_job_status(
            wf_name=self.workflow_name_job, expected_state='suspended')
        job.resume()
        self.wf_helper_job.workflow_job_status(wf_name=self.workflow_name_job)
        self.log.info("Validated resume activity")

    def validate_kill_activity(self, job):
        """ Method to validate kill job activity"""
        self.wf_helper_job.workflow_job_status(
            wf_name=self.workflow_name_job, expected_state='suspended')
        job.kill()
        self.wf_helper_job.workflow_job_status(
            wf_name=self.workflow_name_job, expected_state='killed')
        self.log.info("Validated kill activity")

    def validate_scheduled_job(self):
        """ Method to validate scheduled job activity"""
        self.wf_helper_job.schedule_workflow(
            schedule_pattern={
                "freq_type": 'one_time',
                "active_start_time": (datetime.today().astimezone(pytz.utc)
                                      + timedelta(minutes=1)).strftime("%H:%M"),
                "time_zone": "UTC"
            },
            workflow_json_input={
                "UserInput": self.workflow_name_job
            })
        self.option_selector.sleep_time(_time=90)
        self.validate_user_interaction()
        self.validate_suspend_activity()
        self.log.info("Validated scheduled job activity")

    def validate_api_execution(self):
        """ Method to validate API mode execution"""
        custom_str = self.option_selector.get_custom_str()
        self.wf_helper_api.execute(workflow_json_input={"InputString": custom_str},
                                   wait_for_job=False)
        self.option_selector.sleep_time()
        log_output = self.machine.read_file(self.machine.join_path(
            self.machine.client_object.log_directory, 'WorkflowCustom.log'), search_term=custom_str)
        if custom_str not in log_output:
            raise Exception('Workflow did not execute in API mode')
        self.log.info("Validated API mode execution")

    def validate_api_scheduler(self):
        """ Method to validate api mode scheduled task"""
        custom_str = self.option_selector.get_custom_str()
        self.wf_helper_api.schedule_workflow(
            schedule_pattern={
                "freq_type": 'one_time',
                "active_start_time": (datetime.today().astimezone(pytz.utc)
                                      + timedelta(minutes=1)).strftime("%H:%M"),
                "time_zone": "UTC"
            },
            workflow_json_input={
                "InputString": custom_str
            })
        self.option_selector.sleep_time(_time=120)
        log_output = self.machine.read_file(self.machine.join_path(
            self.machine.client_object.log_directory, 'WorkflowCustom.log'), search_term=custom_str)
        if custom_str not in log_output:
            raise Exception('Workflow did not execute as scheduled in API mode')
        self.log.info("Validated API mode scheduled execution")

    def validate_delete_instance(self):
        """Method to validate deletion of second instance while job in progress"""
        self.wf_helper_job = WorkflowHelper(self, wf_name=self.workflow_name_job, deploy=False)
        self.wf_helper_job.import_workflow()
        self.wf_helper_job.workflow_obj =\
            self.commcell.workflows.get(self.workflow_name_job)
        self.command = "{0}\\WinX64\\Setup.exe /silent /play {0}\\install.xml". \
            format(self.tcinputs["CustomInstallationPath"])
        self.log.info("Starting installation")
        self.machine.execute_command(command=self.command)
        self.wf_helper_job.deploy_workflow(workflow_engine=self.tcinputs["WorkflowEngineName"])
        self.commcell.workflows.refresh()
        self.wf_helper_job.is_deployed(self.workflow_name_job)
        custom_str = self.option_selector.get_custom_str()
        job = self.wf_helper_job.execute(workflow_json_input={"UserInput": custom_str},
                                         wait_for_job=False)
        self.commcell.clients.refresh()
        job_ = self.commcell.clients.get(self.tcinputs["WorkflowEngineName"]).uninstall_software()
        JobManager(job_, self.commcell).wait_for_state()
        job.kill(wait_for_job_to_kill=False)
        self.option_selector.sleep_time(_time=30)
        if not job.is_finished:
            self.log.info("Job not killed, Running Qscript RemoveStaleWorkflowJob.sqle")
            command = "Qscript -f {0}\\RemoveStageWorkflowJob.sqle -i {1}".format(
                self.tcinputs["ScriptLocation"], job.job_id)
            self.machine.execute_command(command=command)
        self.log.info("Validated kill job after instance deletion")

    def setup(self):
        """Setup function of this test case"""
        self.wf_helper_job = WorkflowHelper(self, wf_name=self.workflow_name_job)
        self.wf_helper_api = WorkflowHelper(self, wf_name=self.workflow_name_api)
        self.tc = CommonUtils(self)
        self.option_selector = OptionsSelector(self.commcell)
        self.machine = Machine(machine_name=self.tcinputs["MachineHostName"],
                               commcell_object=self.commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:
            custom_str = self.option_selector.get_custom_str()
            self.wf_helper_job.execute(workflow_json_input={"UserInput": custom_str},
                                       wait_for_job=False)
            self.validate_user_interaction()
            self.validate_suspend_activity()
            custom_str = self.option_selector.get_custom_str()
            job = self.wf_helper_job.execute(workflow_json_input={"UserInput": custom_str},
                                             wait_for_job=False)
            self.validate_user_interaction()
            self.validate_resume_activity(job)
            self.validate_scheduled_job()
            custom_str = self.option_selector.get_custom_str()
            job = self.wf_helper_job.execute(workflow_json_input={"UserInput": custom_str},
                                             wait_for_job=False)
            self.validate_user_interaction()
            self.validate_kill_activity(job)
            custom_str = self.option_selector.get_custom_str()
            job = self.wf_helper_job.execute(workflow_json_input={"UserInput": custom_str},
                                             wait_for_job=False)
            self.validate_user_interaction()
            self.wf_helper_job.delete(self.workflow_name_job)
            job.kill()
            if job.wait_for_completion():
                raise Exception("Job was not killed after workflow deletion")
            self.log.info("Validated kill job after workflow deletion")
            self.validate_api_execution()
            self.validate_api_scheduler()
            self.wf_helper_job.cleanup()
            self.validate_delete_instance()

        except Exception as exp:
            self.wf_helper_job.test.fail(exp)

        finally:
            self.wf_helper_job.cleanup()
            self.wf_helper_api.cleanup()
            self.commcell.clients.refresh()
            if self.commcell.clients.has_client(self.tcinputs["WorkflowEngineName"]):
                job = self.commcell.clients.get(
                    self.tcinputs["WorkflowEngineName"]).uninstall_software()
                JobManager(job, self.commcell).wait_for_state()
            self.tc.cleanup_jobs()
