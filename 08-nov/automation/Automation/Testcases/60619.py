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
    __init__()                                            --  initialize TestCase class
    init_tc()                                             --  Initialize pre-requisites
    run_backup()                                          --   run backup on two subclients
    run_sendlogs()                                        --  run send log
    verify_job_results()                                  --  check job folder in job results
                                                              directory
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "60619":
                        {
                            "ClientName": "c1",
                            "ClientName1": "c2",
                            "AgentName": "File System",
                            "BackupsetName": "defaultBackupSet",
                            "BackupsetName1": "default",
                            "SubclientName" : "sc",
                            "SubclientName1" : "sc1"
                        }
            }

"""
import os
import time
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Reports.SendLog.utils import SendLogUtils
from cvpysdk.license import LicenseDetails

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Test Case: Send logs: validate job results collection"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case


        """
        super(TestCase, self).__init__()
        self.job = None
        self.local_machine = None
        self.browser = None
        self.commcell = None
        self.admin_console = None
        self.sjob_id = None
        self.machine = None
        self.directory = None
        self.send_log_utils = None
        self.send_log = None
        self.client1 = None
        self.backupset1 = None
        self.agent1 = None
        self.subclient1 = None
        self.navigator = None
        self.commcell_name = None
        self.backupjob_id1 = None
        self.backupjob_id2 = None
        self.subclient = None
        self.commcell_id = None
        self.job_details = None
        self.jobid_list = []
        self.base_path = None
        self.name = "Sendlogs: Verify Job Results"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()

            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.commcell_name = self.commcell.commserv_name
            self.client1 = self.commcell.clients.get(self.tcinputs['ClientName1'])
            self.agent1 = self.client1.agents.get(self.tcinputs['AgentName'])
            self.backupset1 = self.agent1.backupsets.get(self.tcinputs['BackupsetName1'])
            self.job_details = JobDetails(self.admin_console)
            self.machine = Machine(self.commcell.commserv_client)
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.directory = self.send_log_utils.create_directory_for_given_path("TC60619")
            self.send_log = SendLogs(self.admin_console)
            licence = LicenseDetails(self.commcell)
            self.local_machine = Machine()
            self.commcell_id = licence.commcell_id_hex

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_backup(self):
        """Running Backup job from two different subclients having different clients"""
        self.subclient1 = self.backupset1.subclients.get(self.tcinputs['SubclientName1'])
        job1 = self.subclient.backup(backup_level="Full")
        job2 = self.subclient1.backup(backup_level="Full")
        self.backupjob_id1 = job1.job_id
        self.backupjob_id2 = job2.job_id
        self.jobid_list.extend([self.backupjob_id1, self.backupjob_id2])

    @test_step
    def run_sendlogs(self):
        """Running SendLog job"""
        self.job = Jobs(self.admin_console)
        self.job.access_job_by_id(self.backupjob_id1)
        self.job_details.send_logs()
        self.send_log.enter_additional_jobs(self.backupjob_id2)
        advanced_list = self.send_log.Advancedlist
        self.send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        self.send_log.select_advanced(advanced_list=[advanced_list.JOBS_RESULTS])
        self.sjob_id = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sjob_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sjob_id}] failed"
            )

    def _verify_job_results(self, client_name, backupjob_id):
        folder_list = self.local_machine.get_folders_in_path(self.base_path, recurse=False)
        for folder in folder_list:
            if f"{client_name}~jobresult~" in folder:
                job_result_path = folder
                job_result_path = os.path.join(job_result_path, "CV_JobResults", "2", "0", backupjob_id)
                if self.local_machine.check_directory_exists(job_result_path):
                    self.log.info(f"Job Results for the Backup Job {backupjob_id} found at {job_result_path}")
                    return
                else:
                    raise CVTestStepFailure(
                        f"Job Results for the Backup Job {backupjob_id} not found at {job_result_path}"
                    )
        raise CVTestStepFailure(
            f"Job Result folder couldn't be found on {self.base_path}"
        )

    @test_step
    def verify_job_results(self):
        """ To unzip Job Results bundle and verify  job exists in job results folder """
        self._verify_job_results(self.tcinputs['ClientName'], self.backupjob_id1)
        self._verify_job_results(self.tcinputs['ClientName1'], self.backupjob_id2)

    def run(self):
        try:
            self.init_tc()
            self.run_backup()
            self.log.info("Waiting for 10 mins to complete both backup job")
            time.sleep(600)
            self.run_sendlogs()
            self.log.info('Waiting for 25 mins to check file present at location ' +
                          _STORE_CONFIG.Reports.uncompressed_logs_path
                          + ' for send log job ids ' + self.sjob_id)
            time.sleep(1500)
            self.base_path = self.send_log_utils.get_uncompressed_path(self.sjob_id, self.jobid_list)
            self.verify_job_results()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
