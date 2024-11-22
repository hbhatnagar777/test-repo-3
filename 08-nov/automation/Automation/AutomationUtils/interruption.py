# -*- coding: utf-8 -*-
# pylint: disable=W0221

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing Interrupt operations on a Job.

This file consists of a class named: Interruption,

which can perform various interrupt operation on a Job.


Interruption:
=============

    __init__()                    --  initialize object of the class

    restart_client_services()     --  Restarts the commvault services of the client
    machine which is associated with the job

    create_operation_window()     --  Creates/deletes a operation window for the client

    ma_cvd_kill()                 --  Kills the CVD process in the MA associated with the job

    suspend_resume_job()          --  Suspends and resumes the job

    reboot_client()               --  reboots the client machine associated with the job

    random_process_kill()         --  Picks a random process from client machine and kills it

    wait_and_resume()             --  Waits for the job to get interrupted before resuming the job

    wait_for_job_run()            --  waits for job to come to running state before
    introducing interuption

    kill_process()                --  terminates a running process on the client machine with either
    the given process name or the process id


"""

import time
import json
import random
import os
from cvpysdk import operation_window
from AutomationUtils import database_helper, logger, machine, constants
from .script_generator import ScriptGenerator



class Interruption(object):
    """Class for performing Interruption operations on a Job."""

    def __init__(self, job_id, commcell):
        """Initializes instance of the Interrupt class.

            Args:
                job_id        (int)       --  job id of a backup job

                commcell      (object)    --  Comcell object relevant for the job

            Returns:

                object - instance of this class

        """
        self._job_id = job_id
        self._commcell_object = commcell
        self._commserver_database = database_helper.get_csdb()
        self._job = self._commcell_object.job_controller.get(job_id=self._job_id)
        self.log = logger.get_log()

        self._backup_set_name = self._job.backupset_name
        self._sub_client_name = self._job.subclient_name
        self._client_name = self._job.client_name
        self._instance_name = self._job.instance_name
        self._app_name = self._job.agent_name
        self._client = self._commcell_object.clients.get(self._client_name)

        self._media_agent_name = None

        query = "select MediaAgentName from JMBkpJobInfo where jobId={0}".format(
            self._job_id)
        self._commserver_database.execute(query)
        cur = self._commserver_database.fetch_one_row()
        if cur:
            self._media_agent_name = cur[0]
            self.log.info("Fetched MA Name: %s", self._media_agent_name)
        else:
            raise Exception("Failed to get the MA name from database")

    def restart_client_services(self):
        """Restarts the commvault service of the client machine associated with the job

        waits for the job to get interrupted and resumes the job once it is interrupted"""
        status = self.wait_for_job_run()
        if status == "running":
            self.log.info("Trying to restart Client services")
            self._client.restart_services(True)
            self.log.info(
                "Client services are restarted, backup job will suspend and resume in a while")
            self.wait_and_resume()

    def operation_window(self):
        """Creates a operation window for the client associated with the job

        waits for the job to get interrupted,

        delete the operation window so that the job can resume"""
        status = self.wait_for_job_run()
        if status == "running":
            op_window_object = operation_window.OperationWindow(self._client)
            op_window_rule_id = op_window_object.create_operation_window("created_from_automation")
            while True:
                time.sleep(10)
                status = self._job.status.lower()
                self.log.info("JobStatus is=%s", status)
                if status in ["suspended", "queued", "pending"] or "completed" in status:
                    self.log.info("Deleting operation window")
                    op_window_object.delete_operation_window(int(op_window_rule_id.rule_id))
                    self.log.info(
                        "Operation window is deleted, backup job will now resume")
                    break
            # try resuming the job only if the JOB is not already resumed
            status = self._job.status.lower()
            if(status not in ["running", "waiting"] and "completed" not in status):
                self._job.resume(True)

    def ma_cvd_kill(self):
        """Kills CVD of Media agent associated with the job

        waits for the job to get interrupted, resumes the

        job once it is interrupted"""
        status = self.wait_for_job_run()
        if status == "running":
            # check if MA and CS are the same
            if self._media_agent_name.strip() in \
            [self._commcell_object.commserv_name.strip(),\
            self._commcell_object.commserv_hostname.strip()]:
                self.log.info(
                    "MA and Comserver are the same machine, so skipping MA CVD process kill")
            elif self._media_agent_name == '':
                self.log.info("Media agent name is not populated, looks like job is completed")
                self.log.info("So skipping MA CVD process kill")
            else:
                self.log.info("Killing MA CVD process to suspend the JOB")
                ma_client_object = self._commcell_object.clients.get(self._media_agent_name)
                cvd_proc_name = "cvd"
                if "windows" in ma_client_object.os_info.lower():
                    cvd_proc_name = "cvd.exe"
                self.kill_process(
                    process_name=cvd_proc_name,
                    client_object=ma_client_object)
                self.log.info("CVD of MA is now Killed, the job will now suspend..!")
                self.wait_and_resume()

    def suspend_resume_job(self):
        """Suspends the job

        waits for the job to get suspended, resumes the job once it is Suspended"""
        status = self.wait_for_job_run()
        if status == "running":
            self.log.info("Suspending the job now")
            self._job.pause(True)
        self.log.info("Waiting for the job to suspend")
        self.wait_and_resume()

    def reboot_client(self):
        """Reboots the client machine associated with the job,

        waits for the machine to come back online,

        waits for the job to get interrupted,

        resumes the job once it is interrupted"""
        status = self.wait_for_job_run()
        if status == "running":
            self.log.info("Shutting down the client")
            command = 'shutdown /r /f'
            if "windows" not in self._client.os_info.lower():
                command = "reboot"
            output = self._client.execute_command(
                command,
                wait_for_completion=False)
            if output[0] != 0:
                raise Exception(
                    'Unable to reboot the machine.')
            self.log.info("Waiting for client to reboot")
            time.sleep(90)
            self.log.info("Waiting for the client to come back online")

            ##check if the client is back online
            while not self._client.is_ready:
                self.log.info("Waiting for client check readiness to pass")
                time.sleep(45)
            self.log.info("Client services are back online.")
            self.wait_and_resume()

    def random_process_kill(self):
        """Picks a random process launched in client which is associated with the job

        Kills the selected job from client machine,

        waits for the job to get interrupted, resumes the job once it is interrupted"""
        self.wait_for_job_run()
        machine_object = machine.Machine(
            self._client, self._commcell_object)
        process_list_json = self.get_commvault_process_list(machine_object)

        self.log.info(
            "Process names and PIDs of the client:%s",
            process_list_json)
        process_list = []
        # Put all process names in the list
        for proc in process_list_json:
            process_list.append(proc)
        process_count = len(process_list)
        random_number = random.randint(0, process_count - 1)
        # get the random process and its ID
        self.log.info(
            "Killing a process randomly: Killing the process %s",
            process_list[random_number])
        self.log.info(
            "Killing a process randomly: Killing the process %s", process_list[random_number])
        self.kill_process(process_id=process_list_json[process_list[random_number]])
        self.log.info(
            "Random process in the client is killed, JOB will now get interrupted")
        self.wait_and_resume()

    def get_commvault_process_list(self, machine_object):
        """ Returns the commvault process associted with the client

            Returns:
                JSON  -   Process names and PID in JSON format

        """
        script_generator = ScriptGenerator()
        # getting the instance name
        instance_name = self._client.instance
        self.log.info("Instance Name fetched is:%s", instance_name)
        cvd_log_path = self._client.log_directory
        cvd_log_path = machine_object.join_path(cvd_log_path, "cvd.log")
        self.log.info("CVD log Path:%s", cvd_log_path)
        if "unix" in machine_object.os_info.lower():
            script_generator.script = constants.UNIX_COMMVAULT_PROCESS_DETAILS
        else:
            script_generator.script = constants.WINDOWS_COMMVAULT_PROCESS_DETAILS

        data_input = {
            "INSTANCE_NAME": instance_name,
            "JOB_ID":self._job_id,
            "CVD_PATH":cvd_log_path
            }
        execute_script = script_generator.run(data_input)
        process_list_str = machine_object.execute(
            execute_script).formatted_output
        os.unlink(execute_script)
        process_list_json = json.loads(process_list_str)
        return process_list_json



    def wait_and_resume(self):
        """Waits for the interrupted jobs to go to suspend/pending state,

        interrupted jobs are then resumed"""
        status = None
        while True:
            time.sleep(20)
            status = self._job.status.lower()
            self.log.info("Job Status:%s", status)
            if status in ["suspended", "pending"] or "completed" in status:
                break
        self.log.info("Job is now interrupted")
        time.sleep(30)
        self.log.info("Resuming the interrupted JOB")
        # resume the job if the job is not in running or waiting state
        status = self._job.status.lower()
        self.log.info("Job is in %s state", status)
        if "completed" in status:
            self.log.info("Job is already completed")
            return
        if(status not in ["running", "waiting"]):
            while True:
                self._job.resume(True)
                time.sleep(40)
                self.log.info("Checking job status after 40 seconds")
                status = self._job.status.lower()
                self.log.info("Status is : %s", status)
                if "running" in status or "completed" in status:
                    break
                self.log.info("Trying to resume job again")
        self.log.info("interrupted job is now resumed..!")

    def wait_for_job_run(self):
        """Waits for job to come to running state before introducing interuption

            Returns:
                status  -   present status of the job

        """
        status = None
        while True:
            status = self._job.status.lower()
            if status != "running" and "completed" not in status:
                time.sleep(10)
                self.log.info(
                    "Waiting for job to come to Running state")
                if status == "pending":
                    self.log.info("Trying to resume the Job as job is in pending state.")
                    self._job.resume(True)
                    self.log.info("Wait for 30 secs before checking job status")
                    time.sleep(30)
                    status = self._job.status.lower()
                    if status == "pending":
                        raise Exception("Job is in pending state after resume. Check logs.")
                if status == "failed":
                    raise Exception("Job is FAILED. Check the logs.")
            else:
                break
        return status

    def kill_process(self, process_name=None, process_id=None, client_object=None):
        """Terminates a running process on the client machine with either the given
            process name or the process id.

        Args:
            process_name    (str)   --  name of the process to be terminate

            process_id      (str)   --  ID of the process ID to be terminated

            client_object   (obj)   --  client object

        Raises:
            Exception:
                if neither the process name nor the process id is given

                if failed to kill the process

        """
        if client_object is None:
            client_object = self._client
        command = ""

        if process_name:
            command = f"taskkill /f /t /im {process_name}"
            if "windows" not in self._client.os_info.lower():
                command = f'pkill -f {process_name}'
        elif process_id:
            command = f"taskkill /pid {process_id} /f"
            if "windows" not in self._client.os_info.lower():
                command = f'kill -9 {process_id}'
        else:
            raise Exception(
                'Please provide either the process Name or the process ID')

        output = client_object.execute_command(
            command,
            wait_for_completion=False)
        if output[0] != 0:
            raise Exception(
                'Unable to Kill the process')
