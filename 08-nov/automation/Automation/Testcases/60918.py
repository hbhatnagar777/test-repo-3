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
    run_send_log_for_client()                             --  run send log for a client
    verify_action_logs()                                  --  verify action logs present in the path
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "60918":
                        {
                            "ClientName":"c1"
                        }
            }

"""

import os
import time
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Reports.SendLog.utils import SendLogUtils
from cvpysdk.license import LicenseDetails
from cvpysdk.job import Job, JobController

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Test Case: Sendlogs: Index Transaction Logs on a Client"""
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
        self.client = None
        self.admin_console = None
        self.sjob_id = None
        self.machine = None
        self.send_log_utils = None
        self.send_log = None
        self.navigator = None
        self.start_jid = None
        self.end_jid = None
        self.latest_jobs = None
        self.final_jobs = []
        self.commcell_name = None
        self.commcell_id = None
        self.job_controller = None
        self.job_details = None
        self.jobid_list = []
        self.client_name = None
        self.path = None
        self.file_server = None
        self.name = "Sendlogs: Index Transaction Logs on a Client"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
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
            self.job_controller = JobController(self.commcell)
            self.local_machine = Machine()
            self.job_details = JobDetails(self.admin_console)
            self.commcell_id = licence.commcell_id_hex
            self.client_name = self.client.client_name
            self.file_server = FileServers(self.admin_console)
            self.latest_jobs = self.job_controller.finished_jobs(self.client_name, lookup_time=72, job_filter='Backup')
            self.latest_jobs = [str(job_id) for job_id, information in self.latest_jobs.items()
                                if information['status']=='Completed']

            for each_job in self.latest_jobs:
                job_object = Job(self.commcell, each_job)
                filesTransferredCount = job_object.num_of_files_transferred
                applicationSize = job_object.size_of_application
                if filesTransferredCount > 0 and applicationSize > 0:
                    self.final_jobs.append(each_job)
            self.latest_jobs = self.final_jobs
            self.start_jid = min(self.latest_jobs)
            self.end_jid = max(self.latest_jobs)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log_for_client(self):
        """ Running sendlog job for a client"""
        self.admin_console.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.admin_console.wait_for_completion()
        self.file_server.action_sendlogs(self.client_name)
        info_list = self.send_log.Informationlist
        advanced_list = self.send_log.Advancedlist
        self.send_log.deselect_information(information_list=[info_list.OS_LOGS, info_list.MACHINE_CONFIG,
                                                             info_list.ALL_USERS_PROFILE])
        self.send_log.select_advanced(advanced_list=[advanced_list.INDEX_TRANS])
        self.send_log.select_index_trn_logs(self.start_jid, self.end_jid)
        self.sjob_id = self.send_log.submit()

    @test_step
    def verify_action_logs(self):
        """Verifies the action logs present at the actionLogs folder in the path"""
        self.path = os.path.join(self.path, self.client_name, "ActionLogs")
        file_list = self.local_machine.get_folders_in_path(self.path, recurse=False)
        jobid_list = [path.split('\\')[-1][1:] for path in file_list]  # \\client_name\\ActionLogs\\J123456 -> 123456
        if len(jobid_list) == 0:
            self.log.error(f"No action logs collected for {self.client_name} at {self.path}")
            raise CVTestStepFailure(
                f'No action logs collected for {self.client_name} at {self.path}'
            )

        if len(jobid_list) > len(self.latest_jobs):  # If more jobs are present on the bundle,
            leftover_jobids = list(set(jobid_list).difference(set(self.latest_jobs)))
            for each_job in leftover_jobids:
                job_obj = self.commcell.job_controller.get(each_job)
                job_details = job_obj._get_job_details()
                curr_job_client = job_details['jobDetail']['generalInfo']['subclient']['clientName']
                if curr_job_client != self.client_name:
                    self.log.error(f'Action logs of {each_job} collected from {curr_job_client} at {self.path}'
                                   f'Please debug further')

                    raise CVTestStepFailure(
                        f'Action logs of {each_job} collected from {curr_job_client} at {self.path}'
                        f'Please debug further'
                    )
            self.log.info(f"All action logs are collected successfully from {self.client_name} at {self.path}")

        elif len(jobid_list) == len(self.latest_jobs): # If the jobid_list and the latest_jobs count are equal
            jobid_list.sort()
            if jobid_list[0] >= self.start_jid and jobid_list[-1] <= self.end_jid:
                self.log.info(f"Action logs collected in range from jobids: {self.start_jid}  to {self.end_jid}")
            else:
                self.log.error(f"Action logs collected from outside the range of jobids"
                               f"Please check the contents on {self.path} to debug further")
                raise CVTestStepFailure(
                    f'Action logs contains the jobids from outside the range.'
                    f'The range should be {self.start_jid} to {self.end_jid}'
                    f'Kindly check the contents on {self.path} to debug further'
                )
        else: # If the latest_jobs count more than the jobid_list
            missing_job_ids = list(set(self.latest_jobs).difference(set(jobid_list)))
            self.log.error(f'Some of the action logs missing for jobids: {missing_job_ids} at {self.path}')
            raise CVTestStepFailure(
                f'Action logs missing for jobids : {missing_job_ids} at {self.path}'
            )

    def run(self):
        try:
            self.init_tc()
            self.run_send_log_for_client()
            self.log.info('Waiting for 20 mins to check file present at location ' +
                          _STORE_CONFIG.Reports.uncompressed_logs_path
                          + ' for send log job id ' + self.sjob_id)
            time.sleep(1200)
            self.path = self.send_log_utils.get_uncompressed_path(self.sjob_id, self.jobid_list)
            self.verify_action_logs()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
