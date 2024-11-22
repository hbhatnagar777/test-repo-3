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
    __init__()                                            --  initialize TestCase class
    init_tc()                                             --  Initialize pre-requisites
    run_backup()                                          --  Run backup job
    run_send_log()                                        -- run send log for job id return by backup job
    verify_cs_client_media_agent_in_send_log_bundle()     -- verify inside send log bundle log from client, comm server,
                                                             media agent is present or not
    verify_send_log_for_client()                          -- verify different log in side log collected from client
    verify_send_log_for_media_agent()                     -- verify different log in side log collected from media agent
    verify_send_log_for_cs()                              -- verify different log in side log collected from comm server
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "55121":
                        {
                           "AgentName":"File System",
                           "BackupLevel":"FULL",
                           "BackupsetName":"defaultBackupSet",
                           "ClientName":"c1",
                           "client_display_name":"c1",
                           "SubclientName":"sc1"
                        }
            }


"""
import time
import os
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
from FileSystem.FSUtils.fshelper import FSHelper
from cvpysdk.license import LicenseDetails

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """send logs by JobID"""
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
        self.media_agent = None
        self.commcell_name = None
        self.navigator = None
        self.send_log_utils = None
        self.commserv_client = None
        self.commcell_id = None
        self.local_machine = None
        self.jobid_list = []
        self.name = "send logs by JobID"
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
            self.navigator = self.admin_console.navigator
            self.media_agent = self.subclient.storage_ma
            self.commcell_name = self.commcell.commserv_name
            self.commserv_client = self.commcell.commserv_client
            self.machine = Machine(self.commcell.commserv_client)
            self.job_details = JobDetails(self.admin_console)
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.send_log = SendLogs(self.admin_console)
            licence = LicenseDetails(self.commcell)
            self.local_machine = Machine()
            self.commcell_id = licence.commcell_id_hex
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_backup(self):
        """
        Run Backup
          """
        fs_helper = FSHelper(self)
        job = fs_helper.run_backup(backup_level=self.tcinputs['BackupLevel'])
        self.backupjobid = str(job[0].job_id)
        self.jobid_list.append(self.backupjobid)
        job_obj = self.commcell.job_controller.get(self.backupjobid)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Backup job [{self.backupjobid}] failed"
            )

    @test_step
    def run_send_log(self):
        """Running SendLog job"""
        self.job = Jobs(self.admin_console)
        self.job.access_job_by_id(self.backupjobid)
        self.job_details.send_logs()
        advanced_list = self.send_log.Advancedlist
        self.send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        info_list = self.send_log.Informationlist
        self.send_log.select_information(information_list=[info_list.OS_LOGS, info_list.LOGS])
        self.sjob_id = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sjob_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sjob_id}] failed"
            )

    @test_step
    def verify_cs_client_media_agent_in_send_log_bundle(self):
        """ To verify cs, client, media agent folder present in the path """
        entities_dict = {self.tcinputs['ClientName']: False, self.commcell_name: False,
                         self.media_agent: False}
        self.curr_path = self.base_path
        folder_list = self.local_machine.get_folders_in_path(self.curr_path, recurse=False)
        self.send_log_utils.verify_entities(folder_list, entities_dict, self.curr_path)

    @test_step
    def verify_send_log_for_client(self):
        """Verifying send logs collected from client"""
        self.log.info(f'Opening client folder and checking logs: clBackup.log ')
        entities_dict = {'clBackup.log': False}
        self.curr_path = os.path.join(self.base_path, self.tcinputs['ClientName'])
        file_list = self.local_machine.get_files_in_path(self.curr_path, recurse=False)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.curr_path)

    @test_step
    def verify_send_log_for_media_agent(self):
        """Verifying send logs collected from media agent """
        self.log.info(f'Opening {self.media_agent} folder and checking logs: archiveIndex.log')
        entities_dict = {'archiveIndex.log': False}
        self.curr_path = os.path.join(self.base_path, self.media_agent)
        file_list = self.local_machine.get_files_in_path(self.curr_path, recurse=False)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.curr_path)

    @test_step
    def verify_send_log_for_cs(self):
        """Verifying send logs collected from comm server"""
        self.log.info("Unzipping comm server bundle and checking logs: JobManager.log ")
        entities_dict = {'JobManager.log': False}
        if "windows" in self.commserv_client.os_info.lower():
            entities_dict[f'PerfAnalysis_{self.backupjobid}.log'] = False
        else:
            perf_path = os.path.join(self.base_path, 'PerfAnalysisLogs')
            if f'PerfAnalysis_{self.backupjobid}.log' in os.listdir(perf_path):
                self.log.info(f'PerfAnalysis_{self.backupjobid}.log collection validated on Unix at {perf_path} ')
            else:
                raise CVTestStepFailure(
                    f'PerfAnalysis_{self.backupjobid}.log was not found on {perf_path}.'
                )
        self.curr_path = os.path.join(self.base_path, self.commcell_name)
        file_list = self.local_machine.get_files_in_path(self.curr_path, recurse=False)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.curr_path)

    def run(self):
        try:
            self.run_backup()
            self.init_tc()
            self.run_send_log()
            self.log.info('Waiting for 25 mins to check file present at location ' +
                          _STORE_CONFIG.Reports.uncompressed_logs_path
                          + ' for send log job id ' + self.sjob_id)
            time.sleep(1500)
            self.base_path = self.send_log_utils.get_uncompressed_path(self.sjob_id, self.jobid_list)
            self.verify_cs_client_media_agent_in_send_log_bundle()
            self.verify_send_log_for_client()
            self.verify_send_log_for_media_agent()
            self.verify_send_log_for_cs()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
