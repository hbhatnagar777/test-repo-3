# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""

Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

Input Example:

    "testCases":
            {
                "60621":
                 {
                     "user_name": "user name",
                     "ClientName": "Name of the Client to run Sendlogs"
                 }
            }


"""
import time
import datetime
import os
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Reports.SendLog.utils import SendLogUtils

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """This test case verifies basic sendlogfiles feature"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.browser = None
        self.admin_console = None
        self.send_log = None
        self.info_list = None
        self.jobid = None
        self.file_server = None
        self.commserv_client = None
        self.send_log_utils = None
        self.name = "Sendlogs validation for negative cases"
        self.tcinputs = {
            "user_name": None,
            "ClientName": None
        }
        self.path = None
        self.client_machine = None
        self.commserv_machine = None
        self.job_start_timestamp = None
        self.send_log_utils = None
        self.machine = None
        self.download_directory = None

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.commserv_client = self.commcell.commserv_client
            self.local_machine = Machine()
            self.client_machine = Machine(self.client.client_name, self.commcell)
            self.commserv_machine = Machine(machine_name=self.commserv_client.client_name,
                                            commcell_object=self.commcell)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.file_server = FileServers(self.admin_console)
            self.send_log = SendLogs(self.admin_console)
            self.send_log_utils = SendLogUtils(self, self.local_machine)
            self.info_list = self.send_log.Informationlist
            self.download_directory = self.send_log_utils.create_directory_for_given_path("TC60621")

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log_for_client(self, wait_for_completion=False):
        """Running SendLog job
        Returns:
            Job object and job id of sendlog job
        """
        self.admin_console.navigator.navigate_to_file_servers()
        self.admin_console.wait_for_completion()
        time.sleep(5)
        self.file_server.action_sendlogs(self.tcinputs["ClientName"])
        datetime_obj = datetime.datetime.now()
        job_start_timestamp = datetime_obj.strftime("%m/%d %H:%M")
        self.subject = 'Sendlogs job' + ' - ' + job_start_timestamp
        self.send_log.email([self.tcinputs['user_name']], None, self.subject)
        self.send_log.disable_self_email_notification()
        jobid = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(jobid)
        self.log.info(f" SendLog Job submitted with Job id {[jobid]}")
        datetime_obj = datetime.datetime.now()
        self.job_start_timestamp = datetime_obj.strftime("%m/%d %H:%M")
        if wait_for_completion:
            job_obj.wait_for_completion()
        return job_obj, jobid

    @test_step
    def kill_send_log_for_client(self, job_obj, jobid):
        """ Kills send log job"""
        time.sleep(10)
        job_obj.kill()
        self.log.info(f"Kill request submitted for SendLog job id {[jobid]}")
        job_obj.wait_for_completion()

    @test_step
    def verify_log_files_cleaned_up(self, job_obj):
        """ Verify SendLog Files and Folders get cleaned up for killed job"""
        self.log.info("Verifing files & folders are cleaned up at Client side")
        self.verify_support_dir_deleted(self.client_machine, self.client)
        self.verify_sendlogs_files_deleted(self.client_machine, self.client)
        self.log.info("Verifing files & folders are cleaned up at CS side")
        self.verify_support_dir_deleted(self.commserv_machine, self.commserv_client)
        self.verify_sendlogs_files_deleted(self.commserv_machine, self.commserv_client)
        self.log.info("Verified that SendLog Files and Folders are cleaned up when job is killed")

    @staticmethod
    def verify_support_dir_deleted(machine, client):
        """Verifying that support directory is deleted from job results folder"""
        job_results_directory = client.job_results_directory
        if "windows" in machine.os_info.lower():
            sl_staging_directory = os.path.join(job_results_directory, "sendLogStagingFolder")
        else:
            sl_staging_directory = f"{job_results_directory}/sendLogStagingFolder"
        folders = machine.get_folders_in_path(folder_path=sl_staging_directory, recurse=False)
        for folder in folders:
            if "support" in folder.lower():
                raise CVTestStepFailure(
                    f" Directory  {folder} created as part of the send logs job is not deleted"
                )

    @staticmethod
    def verify_sendlogs_files_deleted(machine, client):
        """Verifying that sendlogs file is deleted from job results folder"""
        job_results_directory = client.job_results_directory
        if "windows" in machine.os_info.lower():
            sl_staging_directory = os.path.join(job_results_directory, "sendLogStagingFolder")
        else:
            sl_staging_directory = f"{job_results_directory}/sendLogStagingFolder"
        files = machine.get_files_in_path(folder_path=sl_staging_directory)
        for file in files:
            if "sendlogfiles" in file.lower():
                raise CVTestStepFailure(
                    f" File  {file} created as part of the send logs job is not deleted"
                )

    @test_step
    def verify_client_cvd_log(self):
        """Verifying commvault cvd logs for kill request"""
        self.log.info('Verifying client cvd log for kill request')
        log_file_name = 'CVD.log'
        cvd_log_path = self.client_machine.join_path(self.client.log_directory, log_file_name)
        if not self.client_machine.is_file(cvd_log_path):
            raise CVTestStepFailure(f"Log file {log_file_name} doesn't exist")
        expected_pattern = "gatherInfoNLogs() - Exception: sendlogfiles on CS side stopped, quit collection."
        self.log.info("reading cvd log file %s", cvd_log_path)
        log_content = self.client_machine.read_file(cvd_log_path)
        last_match_index = log_content.rfind(expected_pattern)
        if last_match_index >= 0:
            log_timestamp_index = log_content[:last_match_index].rfind(':')
            log_timestamp = log_content[log_timestamp_index - 11:log_timestamp_index]
            time_diff = (datetime.datetime.strptime(log_timestamp, "%m/%d %H:%M")) >= (
                datetime.datetime.strptime(self.job_start_timestamp, "%m/%d %H:%M"))
            if time_diff:
                self.log.info("cvd logs show the kill request of send logs job")
            else:
                self.log.error(f"Kill request expected after timestamp {self.job_start_timestamp}")
                self.log.error(f"Kill request found at timestamp {log_timestamp}")
                raise CVTestStepFailure(
                    f"Couldn't find kill request of send logs job in CVD.log after Job Start time "
                    f"{self.job_start_timestamp}")
        else:
            self.log.error("Couldn't find kill request of send logs job in CVD.log")
            raise CVTestStepFailure("Couldn't find kill request of send logs job in CVD.log")

    @test_step
    def stop_client_services(self):
        """ Stop services on given client"""
        self.log.info(" Stopping CVD services on client")
        self.client.stop_service(service_name='GxCVD(Instance001)')
        self.log.info("Services are stopped on client")

    @test_step
    def start_client_services(self):
        """ Start services on given client"""
        self.log.info(" Starting CVD services on client")
        client_machine = Machine(self.client.client_hostname,
                                 commcell_object=None,
                                 username=self.tcinputs["UserName"],
                                 password=self.tcinputs["Password"])
        command_list = ['start-Service -Name "GxCVD(Instance001)"',
                        'start-Service -Name "GxClMgrS(Instance001)"',
                        'start-Service -Name "GXMMM(Instance001)"']
        for command in command_list:
            client_machine.execute_command(command)
        self.log.info("Services are Started on client")

    @test_step
    def validate_job_failed(self, jobid):
        """ Validate the status of Job is failed"""
        job_obj = self.commcell.job_controller.get(jobid)
        job_obj.wait_for_completion()
        job_details = job_obj.details['jobDetail']['clientStatusInfo']['clientStatus'][0]
        failure_reason = job_details['jMFailureReasonStatus']
        if not job_obj.summary['status'] == 'Failed' and failure_reason == 'Failed to collect logs':
            self.log.info(f"Expected status:'Failed' & Failure reason:'Failed to collect logs'")
            self.log.info(f"Actual status : {[job_obj.summary['status']]} and Failure reason :"
                          f" {[failure_reason]} ")
            raise CVTestStepFailure(
                f"Send log job status is {[job_obj.summary['status']]} "
                f"and Failure reason displayed is, "
                f" {[failure_reason]} when services are down"
            )
        self.log.info(f"Send logs job status is Failed and Job Reason is {failure_reason}")

    @test_step
    def verify_offline_client_email(self):
        """ validate offline client in the email"""
        self.send_log_utils.verify_email(self.download_directory, self.subject)
        file_list = self.local_machine.get_files_in_path(self.download_directory)
        client_found = False
        client_offline_message = "Offline Client(s): " + self.tcinputs['ClientName']
        for file_name in file_list:
            with open(os.path.join(self.download_directory, file_name), errors="ignore") as email_html:
                lines = email_html.readlines()
                for line in lines:
                    if client_offline_message in line:
                        client_found = True
                        break
            if not client_found:
                raise CVTestStepFailure(
                    f" offline client {self.tcinputs['ClientName']} not present in the email"
                )

    @test_step
    def verify_send_log(self, sendlogs_job_id):
        """Verify SendLog job output """
        logs_path = self.send_log_utils.get_uncompressed_path(sendlogs_job_id)
        self.log.info("logs path " + logs_path)
        logs_path = os.path.join(logs_path, self.tcinputs['ClientName'])
        file_name = "cvd.log"
        self.log.info(f'Opening client folder {logs_path} and checking logs: {file_name} ')
        file_list = self.local_machine.get_files_in_path(logs_path, recurse=False)
        found = False
        for file in file_list:
            if file_name in file:
                found = True
                break
        if not found:
            raise CVTestStepFailure(
                f" client cvd log is missing in the sendlogs bundle"
            )

    def run(self):
        """Run function of this test case to Run backup """
        try:
            self.init_tc()
            self.log.info("Validate that log files are cleaned up when job is killed")
            job_obj, jobid = self.run_send_log_for_client()
            self.kill_send_log_for_client(job_obj, jobid)
            self.verify_client_cvd_log()
            self.log.info("Waiting for 10 minutes before validating support/sendlogs folder cleared")
            time.sleep(600)
            self.verify_log_files_cleaned_up(job_obj)
            self.log.info("Validate that Send log job is failed when services on client is down")
            self.stop_client_services()
            job_obj, jobid = self.run_send_log_for_client()
            self.validate_job_failed(jobid)
            self.verify_offline_client_email()
            self.start_client_services()
            self.log.info("Validate that send log bundle is uploaded from CS, if client can't access the http site")
            self.client_machine.add_host_file_entry(_STORE_CONFIG.Reports.SENDLOGS_HTTP_UPLOAD, '172.8.8.8')
            job_obj, jobid = self.run_send_log_for_client(wait_for_completion=True)
            self.log.info('Waiting for 15 mins to check file present at location '
                          + _STORE_CONFIG.Reports.uncompressed_logs_path +
                          ' for send log job id ' + jobid)
            time.sleep(900)
            self.verify_send_log(jobid)
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.client_machine.remove_host_file_entry(_STORE_CONFIG.Reports.SENDLOGS_HTTP_UPLOAD)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
