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
    __init__()                --  initialize TestCase class
    init_tc()                 --  Initial configuration for the test case
    run_send_log_for_client() --  run send logs job for client
    verify_send_log()         --  verify send log job results
    run_backup()              --  run backup job
    run_send_log_for_job()    --  run send logs job for the backup job
    verify_send_log()         --  verify send log job results
    run_restore()              -- run restore job
    run_send_log_for_job()    --  run send logs job for the restore job
    verify_send_log()         --  verify send log job results
    run()                     --  run function of this test case

Input Example:

    "testCases":
            {
                "59008":
                        {
                            "ClientName": "Client Name",
                            "AgentName": "File System",
                            "BackupsetName": "Backup set",
                            "SubclientName": "subclient",
                            "InstanceName" : "instance",
                            "VMName": "vm name"
                        }
            } time


"""
import time
import os
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Reports.SendLog.utils import SendLogUtils
from Reports.utils import TestCaseUtils
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from VirtualServer.VSAUtils import  VirtualServerUtils, OptionsHelper, VirtualServerHelper



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
        self.file_server = None
        self.hypervisor = None
        self.job = None
        self.job_details = None
        self.sendlogs_job_id = None
        self.jobid_list = []
        self.backup_jobid = None
        self.local_machine = None
        self.vsa_subclient = None
        self.vsa_proxy_name = None
        self.restore_jobid = None
        self.name = "Sendlogs: Verify sendlogs feature"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.commserv_client = self.commcell.commserv_client
            self.machine = Machine()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.commcell_name = self.commcell.commserv_name
            self.file_server = FileServers(self.admin_console)
            self.send_log = SendLogs(self.admin_console)
            self.job = Jobs(self.admin_console)
            self.job_details = JobDetails(self.admin_console)
            self.local_machine = Machine()
            if self.tcinputs['AgentName'] == 'Virtual Server':
                self.hypervisor = Hypervisors(self.admin_console)
                self.vsa_subclient = VirtualServerUtils.subclient_initialize(self)
                self.vsa_proxy_name = self.vsa_subclient.auto_vsainstance.co_ordinator
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log_for_client(self):
        """Running SendLog job for the client"""
        if self.tcinputs['AgentName'] == 'File System':
            self.admin_console.navigator.navigate_to_file_servers()
            self.admin_console.wait_for_completion()
            self.file_server.action_sendlogs(self.tcinputs['ClientName'])
        elif self.tcinputs['AgentName'] == 'Virtual Server':
            self.admin_console.navigator.navigate_to_hypervisors()
            self.admin_console.wait_for_completion()
            self.hypervisor.action_send_logs(self.tcinputs['ClientName'])
        self.sendlogs_job_id = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sendlogs_job_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sendlogs_job_id}] failed"
            )

    @test_step
    def run_backup(self):
        """Run backup job """
        self.subclient = self.backupset.subclients.get(self.tcinputs['SubclientName'])
        backup_job = self.subclient.backup(backup_level="Full")
        backup_job.wait_for_completion()
        self.backup_jobid = backup_job.job_id

    @test_step
    def run_restore(self):
        """Run restore job """
        self.subclient = self.backupset.subclients.get(self.tcinputs['SubclientName'])
        if self.tcinputs['AgentName'] == 'File System':
            restore_job = self.subclient.restore_in_place(['C:\\TC59008_Content'])
        elif self.tcinputs['AgentName'] == 'Virtual Server':
            restore_job = self.subclient.full_vm_restore_out_of_place(self.tcinputs['VMName'])
        restore_job.wait_for_completion()
        self.restore_jobid = restore_job.job_id

    @test_step
    def run_send_log_for_job(self, job_id):
        """Running SendLog job for a job"""
        self.job.access_job_by_id(job_id)
        self.job_details.send_logs()
        advanced_list = self.send_log.Advancedlist
        self.send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        info_list = self.send_log.Informationlist
        self.send_log.select_information(information_list=[info_list.OS_LOGS, info_list.LOGS])
        self.sendlogs_job_id = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sendlogs_job_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sendlogs_job_id}] failed"
            )
        self.log.info(" job id " + job_id)
        self.jobid_list.clear()
        self.jobid_list.append(job_id)


    @test_step
    def verify_send_log(self, isBackup=True):
        """Verify SendLog job output """
        logs_path = self.send_log_utils.get_uncompressed_path(self.sendlogs_job_id, self.jobid_list)
        if self.tcinputs['AgentName'] == 'File System':
            if isBackup:
                file_name = 'clBackup.log'
            else:
                file_name = 'clRestore.log'
            logs_path = os.path.join(logs_path, self.tcinputs['ClientName'])
        elif self.tcinputs['AgentName'] == 'Virtual Server':
            if isBackup:
                file_name = 'vsbkp.log'
            else:
                file_name = 'vsrst.log'
            logs_path = os.path.join(logs_path, self.vsa_proxy_name)
        self.log.info(f'Opening client folder {logs_path} and checking logs: {file_name} ')
        file_list = self.local_machine.get_files_in_path(logs_path)
        found = False
        for file in file_list:
            if file_name in file:
                found = True
                break
        if not found:
            raise CVTestStepFailure(
                f" backup/restore log files are missing in the sendlogs bundle"
            )

    def run(self):
        try:
            self.init_tc()
            self.run_send_log_for_client()
            self.log.info('Waiting for 5 mins to check file present at location '
                          + _STORE_CONFIG.Reports.uncompressed_logs_path +
                          ' for send log job id ' + self.sendlogs_job_id)
            time.sleep(300)
            self.verify_send_log()
            self.run_backup()
            self.run_send_log_for_job(self.backup_jobid)
            self.log.info('Waiting for 5 mins to check file present at location '
                          + _STORE_CONFIG.Reports.uncompressed_logs_path +
                          ' for send log job id ' + self.sendlogs_job_id)
            time.sleep(300)
            self.verify_send_log()
            self.run_restore()
            self.run_send_log_for_job(self.restore_jobid)
            self.log.info('Waiting for 5 mins to check file present at location '
                          + _STORE_CONFIG.Reports.uncompressed_logs_path +
                          ' for send log job id ' + self.sendlogs_job_id)
            time.sleep(300)
            self.verify_send_log(False)

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
