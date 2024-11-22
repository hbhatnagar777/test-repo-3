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
    __init__()                      --  initialize TestCase class
    init_tc()                       --  Initial configuration for the test case
    create_process_dump_file()      --  create process dump file with size 39 GB
    run_send_log_for_client()       --  run send logs job for client
    verify_send_log_dump_file()     --  verify dump file exists in the sendlogs bundle
    create_process_dump_file()      --  create process dump file with size 41 GB
    run_send_log_for_client()       --  run send logs job for the backup job
    verify_send_log_dump_file()     --  verify dump file is not collected in the sendlogs bundle
    run()                           --  run function of this test case

Input Example:

    "testCases":
            {
                "63751":
                        {
                            "ClientName": "Client Name",
                            "emails": ""
                        }
            } time


"""
import time
import os
from AutomationUtils.mailer import Mailer
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Reports.SendLog.utils import SendLogUtils
from Reports.utils import TestCaseUtils
from Web.Common.page_object import handle_testcase_exception
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from cvpysdk.license import LicenseDetails

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Sendlogs: Verify sendlogs feature"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.browser = None
        self.admin_console = None
        self.send_log = None
        self.utils = None
        self.commcell_id = None
        self.commcell_name = None
        self.machine = None
        self.path = None
        self.directory = None
        self.utils = TestCaseUtils(self)
        self.send_log_utils = None
        self.commserv_client = None
        self.sendlogs_job_id1 = None
        self.sendlogs_job_id2 = None
        self.sendlogs_job_status1 = None
        self.sendlogs_job_status2 = None
        self.jobid_list = []
        self.local_machine = None
        self.process_dump_file1 = 'cvd_TC63751_72GB.dmp'
        self.process_dump_file2 = 'cvd_TC63751_76GB.dmp'
        self.client_machine = None
        self.process_dump_file_path1 = None
        self.process_dump_file_path2 = None
        self.name = "Sendlogs: Verify Big Log Uploads"
        self.process_dump_file_exists = False
        self.logs_path1 = None
        self.logs_path2 = None
        self.html = None
        self.subject = None

    def init_tc(self):
        """
            Initial configuration for the test case
        """
        try:
            self.log.info("Initializing pre-requisites")
            self.commserv_client = self.commcell.commserv_client
            self.machine = Machine()
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.commcell_name = self.commcell.commserv_name
            self.local_machine = Machine()
            self.client_machine = Machine(self.client.client_name, self.commcell)
            licence = LicenseDetails(self.commcell)
            self.commcell_id = licence.commcell_id_hex
            self.process_dump_file_path1 = self.client_machine.join_path(self.client.log_directory,
                                                                         self.process_dump_file1)
            self.process_dump_file_path2 = self.client_machine.join_path(self.client.log_directory,
                                                                         self.process_dump_file2)
            self.commcell.add_additional_setting(category='CommServDB.GxGlobalParam',
                                                 key_name='SendLogsCurrentHTTPSite',
                                                 data_type='STRING',
                                                 value='https://logs.commvault.com/commandcenter')
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log_for_client(self, checkCWEStatus=False):
        """Create send logs job for the client"""
        xml = """<TMMsg_CreateTaskReq>
                <taskInfo>
                    <task taskType="1" initiatedFrom="1" policyType="0">
                    <taskFlags disabled="0" />
                    </task>
                    <subTasks>
                    <subTask subTaskType="1" operationType="5010" />
                    <options>
                    <adminOpts>
                        <sendLogFilesOption actionLogsEndJobId="0" collectRFC="0" jobid="0" 
                        tsDatabase="0" galaxyLogs="1" getLatestUpdates="0" 
                        actionLogsStartJobId="0" computersSelected="1" csDatabase="0" 
                        otherDatabases="0" crashDump="1" isNetworkPath="0" collectHyperScale="0" 
                        saveToFolderSelected="0" sendLogsOnJobCompletion="0" includeDCDB="0" 
                        notifyMe="1" includeJobResults="0" doNotIncludeLogs="1" 
                        machineInformation="0" scrubLogFiles="0" 
                        osLogs="0" allUsersProfile="1" splitFileSizeMB="512" actionLogs="0" 
                        includeIndex="0" databaseLogs="0" logFragments="0" collectUserAppLogs="0" 
                        uploadLogsSelected="1" useDefaultUploadOption="1" enableChunking="1">
                            <impersonateUser useImpersonation="0" />
                            <clients clientName=\"""" + self.tcinputs['ClientName'] + """\" />
                        </sendLogFilesOption>
                    </adminOpts>
                    </options></subTasks></taskInfo></TMMsg_CreateTaskReq>"""
        response = self.commcell.execute_qcommand_v2("qoperation execute", xml)
        if response:
            sendlogs_job_id = response.json()['jobIds'][0]
            self.log.info(f" Send log job id [{sendlogs_job_id}]")
            job_obj = self.commcell.job_controller.get(sendlogs_job_id)
            job_status = job_obj.wait_for_completion()
            if not job_status:
                raise CVTestStepFailure(
                    f"Send log job id [{sendlogs_job_id}] failed"
                )
            if checkCWEStatus:
                if job_obj.status != 'Completed w/ one or more errors':
                    raise CVTestStepFailure(
                        f"Send log job id [{sendlogs_job_id}] status is not CWE"
                    )
            return sendlogs_job_id, job_obj.status
        raise CVTestStepFailure("Failed to create sendlogs job with reason: %s" % response.content)

    @test_step
    def verify_process_dump_file(self, uncompressed_logs_path, process_dump_file, sendlogs_job_id, checkExists=True):
        """Verify SendLog job output """
        logs_path = uncompressed_logs_path
        if sendlogs_job_id == self.sendlogs_job_id1:
            self.logs_path1 = logs_path
        elif sendlogs_job_id == self.sendlogs_job_id2:
            self.logs_path2 = os.path.join(logs_path, 'skippedFileList.txt')

        file_list = self.local_machine.get_files_in_path(logs_path)
        found = False
        for file in file_list:
            if process_dump_file in file:
                found = True
                self.log.info(f'{process_dump_file} found in {file}')
                break
        if checkExists and not found:
            raise CVTestStepFailure(
                f" {process_dump_file} is missing in the sendlogs bundle"
            )
        else:
            self.process_dump_file_exists = True
        if not checkExists and found:
            raise CVTestStepFailure(
                f" large dump file {process_dump_file} "
                f" exists in the sendlogs bundle"
            )

    @test_step
    def create_process_dump_file(self, process_dump_file_path, file_size):
        """create process dump file """
        if self.client_machine.check_file_exists(process_dump_file_path):
            self.client_machine.delete_file(process_dump_file_path)
        self.client_machine.create_file(process_dump_file_path, content="hugefile",
                                        file_size=file_size)

    @test_step
    def generate_email(self):
        """ generate email to send status of send logs job with large process dump file """
        self.subject = f" Sendlogs Automation Test case - job with large process dump file "
        self.html = """<style>table{border-collapse: collapse;} th{
        background: #2c5e84; color: #fff; } th, td{ padding: 10px; } </style>"""

        if self.sendlogs_job_id1:
            self.html += f'<b><u>Sendlogs job details -  ' \
                         f'72 GB process dump file is collected and ' \
                         f'job status is Completed </u></b><br/>'
            self.html += f'CVD dump file name: <b>' + self.process_dump_file1 + '</b><br/>'
            self.html += f'CVD dump file size: <b>72 GB</b><br/>'
            self.html += f'Jobid: <b>' + self.sendlogs_job_id1 + '</b><br/>'
            self.html += f'Job status: <b>' + str(self.sendlogs_job_status1) + '</b><br/>'
            self.html += f'Unzipped Logs path: <b>' + self.logs_path1 + '</b><br/><br/>'
        if self.sendlogs_job_id2:
            self.html += f'<b><u>Sendlogs job details -  ' \
                         f'76 GB process dump file is not collected and ' \
                         f'job status is Completed w/ one or more errors  </u></b><br/>'
            self.html += f'CVD dump file name: <b>' + self.process_dump_file2 + '</b><br/>'
            self.html += f'CVD dump file size: <b>76 GB</b><br/>'
            self.html += f'Jobid: <b>' + self.sendlogs_job_id2 + '</b><br/>'
            self.html += f'Job status: <b>' + str(self.sendlogs_job_status2) + '</b><br/>'
            self.html += f'Skipped Files path: <b>' + self.logs_path2 + '</b><br/><br/>'
        self.html += f'<b><u>Setup </u></b><br/>'
        self.html += f'CS: <b>' + self.commcell.commserv_hostname + '</b><br/>'
        self.html += f'Client: <b>' + self.tcinputs['ClientName'] + '</b><br/>'

    @test_step
    def send_email(self):
        """ send email with sendlogs job details """
        mailer = Mailer(mailing_inputs={'receiver': self.tcinputs['emails']},
                        commcell_object=self.commcell)
        mailer.mail(body=self.html, subject=self.subject)

    def run(self):
        try:
            self.init_tc()
            file_size = int(72 * 1024 * 1024 * 1024)
            self.create_process_dump_file(self.process_dump_file_path1, file_size)
            self.sendlogs_job_id1, self.sendlogs_job_status1 = self.run_send_log_for_client()
            self.client_machine.delete_file(self.process_dump_file_path1)
            self.log.info('Waiting for 40 mins to check file present at location '
                          ' for send log job id ' + self.sendlogs_job_id1)
            time.sleep(2400)
            self.path = self.send_log_utils.get_uncompressed_path(self.sendlogs_job_id1)
            self.verify_process_dump_file(self.path, self.process_dump_file1, self.sendlogs_job_id1)
            file_size = int(76 * 1024 * 1024 * 1024)
            self.create_process_dump_file(self.process_dump_file_path2, file_size)
            self.sendlogs_job_id2, self.sendlogs_job_status2 = self.run_send_log_for_client(True)
            self.client_machine.delete_file(self.process_dump_file_path2)
            self.log.info('Waiting for 15 mins to check file present at location '
                          ' for send log job id ' + self.sendlogs_job_id2)
            time.sleep(900)
            self.path = self.send_log_utils.get_uncompressed_path(self.sendlogs_job_id2)
            self.verify_process_dump_file(self.path, self.process_dump_file2, self.sendlogs_job_id2, False)
            self.generate_email()
            self.send_email()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.send_log_utils.change_http_setting()
