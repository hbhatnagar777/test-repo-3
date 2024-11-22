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
    init_backupjobid()                                    --  Initialize the backup job
    run_send_log_for_backupjob()                          --  run send log
    verify_job_results()                                  --  check job folder in job results
                                                              directory
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "63661":
                        {
                            "ClientName":"c1",
                            "AgentName":"File System",
                            "BackupsetName":"default",
                            "SubclientName":"sc1"
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
        self.cre_api = None
        self.job = None
        self.local_machine = None
        self.browser = None
        self.commcell = None
        self.admin_console = None
        self.backupjob_id = None
        self.sjob_id = None
        self.machine = None
        self.send_log_utils = None
        self.send_log = None
        self.navigator = None
        self.commcell_name = None
        self.subclient = None
        self.commcell_id = None
        self.job_details = None
        self.jobid_list = []
        self.client_name = None
        self.path = None
        self.name = "Sendlogs with Job Results Option : UNC Path"

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
            self.machine = Machine(self.commcell.commserv_client)
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.send_log = SendLogs(self.admin_console)
            licence = LicenseDetails(self.commcell)
            self.local_machine = Machine()
            self.job_details = JobDetails(self.admin_console)
            self.commcell_id = licence.commcell_id_hex
            self.client_name = self.client.display_name
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def init_backupjobid(self):
        """
        Initialize backup job for the client
        """
        job = self.subclient.backup(backup_level="Full")
        self.backupjob_id = job.job_id
        self.jobid_list.append(self.backupjob_id)

    @test_step
    def run_send_log_for_backupjob(self):
        """ Running sendlog job"""
        self.job = Jobs(self.admin_console)
        self.job.access_job_by_id(self.backupjob_id)
        self.job_details.send_logs()
        advanced_list = self.send_log.Advancedlist
        info_list = self.send_log.Informationlist
        self.send_log.deselect_information(information_list=[info_list.OS_LOGS, info_list.MACHINE_CONFIG,
                                                             info_list.ALL_USERS_PROFILE])
        self.send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        self.send_log.select_advanced(advanced_list=[advanced_list.JOBS_RESULTS])
        self.sjob_id = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sjob_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sjob_id}] failed"
            )

    @test_step
    def verify_job_results(self):
        """Verifying the contents of Job Results folder"""
        job_dir = self.client.job_results_directory
        self.log.info(f"The job results directory is {job_dir} ")
        if not job_dir.startswith("\\"):
            raise CVTestStepFailure(
                f'The job result directory of the client is not UNC path'
            )

        folder_list = self.local_machine.get_folders_in_path(self.path, recurse=False)
        for folder in folder_list:
            if f"{self.client_name}~jobresult~" in folder:
                job_result_path = folder
                job_result_path = os.path.join(job_result_path, "CV_JobResults","2","0", self.backupjob_id)
                if self.local_machine.check_directory_exists(job_result_path):
                    self.log.info(f"Job Results for the Backup Job {self.backupjob_id} found at {job_result_path}")
                    return
                else:
                    raise CVTestStepFailure(
                        f"Job Results for the Backup Job {self.backupjob_id} not found at {job_result_path}"
                    )
        raise CVTestStepFailure(
            f"Job Results folder coudn't be found on {self.path} "
        )

    def run(self):
        try:
            self.init_tc()
            self.init_backupjobid()
            self.log.info('Waiting for 10 minutes to complete the backup job')
            time.sleep(600)
            self.run_send_log_for_backupjob()
            self.log.info('Waiting for 25 minutes to check the file present at the location '
                          + _STORE_CONFIG.Reports.uncompressed_logs_path
                          + ' for send log job id ' + self.sjob_id)
            time.sleep(1500)
            self.path = self.send_log_utils.get_uncompressed_path(self.sjob_id, self.jobid_list)
            self.verify_job_results()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
