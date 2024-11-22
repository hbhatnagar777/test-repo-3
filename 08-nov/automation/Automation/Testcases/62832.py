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
    run_backup()                                          --  run a backup for the client
    run_send_log()                                        --  perform sendlog by job id
    verify_client_log_folder()                            --  verifies if the client folder exists
    verify_job_log_present()                              --  verifies the backup job log present
    verify_ma_logs()                                      --  verifies media agent logs present
    verify_cs_logs()                                      --  verifies commserve logs present
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "62832":
                        {
                          "ClientName" : "Client1",
                          "AgentName" : "File System",
                          "BackupsetName":"defaultBackupSet",
                          "SubclientName" : "default"
                        }
            }
"""
import os
import time
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Reports.SendLog.utils import SendLogUtils
from cvpysdk.license import LicenseDetails
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Client Level Permission Check : Use Tenant Admin Credentials to run this TC"""
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
        self.sjob_id = None
        self.backupjobid = None
        self.machine = None
        self.job_details = None
        self.base_path = None
        self.curr_path = None
        self.job = None
        self.client = None
        self.subclient = None
        self.media_agent = None
        self.commcell_name = None
        self.navigator = None
        self.send_log_utils = None
        self.commcell_id = None
        self.local_machine = None
        self.jobid_list = []
        self.name = "Sendlogs with Client Level Permission Check"
        self.tcinputs = {
            "ClientName": None,
        }

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
            if self.admin_console.driver.title == 'Hub - Metallic':
                self.log.info("Navigating to adminconsole from Metallic hub")
                hub_dashboard = Dashboard(self.admin_console, HubServices.endpoint)
                try:
                    hub_dashboard.choose_service_from_dashboard()
                    hub_dashboard.go_to_admin_console()
                except:  # in case service is already opened
                    hub_dashboard.go_to_admin_console()
            self.navigator = self.admin_console.navigator
            self.commcell_name = self.commcell.commserv_name
            self.machine = Machine()
            self.job_details = JobDetails(self.admin_console)
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.send_log = SendLogs(self.admin_console)
            licence = LicenseDetails(self.commcell)
            self.local_machine = Machine()
            self.media_agent = self.subclient.storage_ma
            self.commcell_id = licence.commcell_id_hex
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_backup(self):
        """Run a backup from a subclient for which the user has permission"""
        job = self.subclient.backup(backup_level="Full")
        self.backupjobid = job.job_id
        self.jobid_list.append(self.backupjobid)

    @test_step
    def run_send_log(self):
        """ Running sendlog job on the backup job id"""
        self.job = Jobs(self.admin_console)
        self.job.access_job_by_id(self.backupjobid)
        self.job_details.send_logs()
        info_list = self.send_log.Informationlist
        self.send_log.deselect_information(information_list=[info_list.OS_LOGS, info_list.MACHINE_CONFIG,
                                                             info_list.ALL_USERS_PROFILE])
        self.sjob_id = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sjob_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f" Send log Job ID {self.sjob_id} failed"
            )

    @test_step
    def verify_client_log_folder(self):
        """Verify if the entire client folder is collected"""
        folders = self.machine.get_folders_in_path(self.base_path, recurse=False)
        for folder in folders:
            folder_name = folder.split('\\')[-1]
            if folder_name == self.tcinputs['ClientName']:
                self.log.info(f'Client log folder {folder_name} found on {self.base_path}')
                return
        self.log.error(f'Client log folder missing on {self.base_path}')
        raise CVTestStepFailure(
            f"Client log folder {self.tcinputs['ClientName']} missing on {self.base_path}"
        )

    @test_step
    def verify_job_log_present(self):
        """Verifies if the Job_{self.backupjobid}.log is present at {self.base_path} or not"""

        file_list = self.machine.get_files_in_path(self.base_path, recurse=False)
        if any([True for file in file_list if f'Job_{self.backupjobid}.log' in file]):
            self.log.info(f'Job_{self.backupjobid}.log is present at {self.base_path}')
        else:
            raise CVTestStepFailure(
                f'Job_{self.backupjobid}.log is missing on the {self.base_path}. Please check the logs'
            )

    @test_step
    def verify_ma_logs(self):
        """Verifies if archiveIndex.log is present or not"""
        if self.media_agent == self.client.client_name:
            self.curr_path = os.path.join(self.base_path, self.media_agent)
            file_list = self.machine.get_files_in_path(self.curr_path, recurse=False)
            for file in file_list:
                if 'archiveIndex.log' in file:
                    self.log.info(f'archiveIndex.log is found at the {self.curr_path}')
                    return

            raise CVTestStepFailure(
                f'archiveIndex.log is not found at {self.curr_path}. Please check the logs to debug further'
            )

        else:
            self.curr_path = os.path.join(self.base_path, f'Job_{self.backupjobid}.log')
            contents = self.local_machine.find_lines_in_file(self.curr_path, ['File    : archiveIndex.log'])
            if len(contents):
                self.log.info(f'archiveIndex.log is present at Job_{self.backupjobid}.log on {self.curr_path}')
            else:
                self.log.error(f'archiveIndex.log is not present at Job_{self.backupjobid}.log on {self.curr_path}')
                raise CVTestStepFailure(
                    f'archiveIndex.log is not logged at Job_{self.backupjobid}.log on {self.curr_path}'
                )

    @test_step
    def verify_cs_logs(self):
        """Verifies if JobManager.log is present at Job_{self.backupjobid}.log or not"""
        self.curr_path = os.path.join(self.base_path, f'Job_{self.backupjobid}.log')
        contents = self.local_machine.find_lines_in_file(self.curr_path, ['File    : JobManager.log'])
        if len(contents):
            self.log.info(f'JobManager.log is present at Job_{self.backupjobid}.log on {self.curr_path}')
        else:
            self.log.error(f'JobManager.log is not present at Job_{self.backupjobid}.log on {self.curr_path}')
            raise CVTestStepFailure(
                f'JobManager.log is not logged at Job_{self.backupjobid}.log on {self.curr_path}'
            )

    def run(self):
        try:
            self.run_backup()
            self.log.info(f'Waiting for 5 minutes to complete the backup job with job id: {self.backupjobid}')
            time.sleep(300)
            self.init_tc()
            self.run_send_log()
            self.log.info(f'Waiting for 25 minutes to check file present at network location '
                          + ' for send log job id ' + self.sjob_id)
            time.sleep(1500)
            self.base_path = self.send_log_utils.get_uncompressed_path(self.sjob_id, self.jobid_list)
            self.verify_client_log_folder()
            self.verify_job_log_present()
            self.verify_ma_logs()
            self.verify_cs_logs()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
