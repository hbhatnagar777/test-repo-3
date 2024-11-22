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
    run_backup()                                          --  Run backup job
    run_send_log()                                        -- run send log for job id return by backup job
    verify_cs_client_media_agent_in_send_log_bundle()     -- verify inside send log folder log from client, comm server,
                                                             media agent is present or not
    verify_send_log_for_client()                          -- verify different log in side log collected from client
    verify_send_log_for_media_agent()                     -- verify different log in side log collected from media agent
    verify_send_log_for_cs()                              -- verify different log in side log collected from comm server
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "62793":
                        {
                           "ClientName": "c1",
                           "AgentName": "File System",
                           "BackupsetName": "defaultBackupSet",
                           "SubclientName" : "sc1",
                           "SubclientName1" : "sc2"
                        }
            }


"""
import time
import os
from AutomationUtils.config import get_config
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Reports.SendLog.utils import SendLogUtils
from cvpysdk.license import LicenseDetails
from AutomationUtils.machine import Machine

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
        self.jobid_list = []
        self.sjob_id = None
        self.backupjob_id1 = None
        self.backupjob_id2 = None
        self.machine = None
        self.path = None
        self.job = None
        self.media_agent = None
        self.media_agent1 = None
        self.subclient = None
        self.subclient1 = None
        self.commcell_name = None
        self.commcell_id = None
        self.local_machine = None
        self.navigator = None
        self.send_log_utils = None
        self.commserv_client = None
        self.job_details = None
        self.base_path = None
        self.curr_path = None
        self.name = "send logs by Multiple JobIDs"
        self.tcinputs = {
            "ClientName": None
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
            self.media_agent1 = self.subclient1.storage_ma
            self.commcell_name = self.commcell.commserv_name
            self.commserv_client = self.commcell.commserv_client
            self.job_details = JobDetails(self.admin_console)
            self.machine = Machine(self.commcell.commserv_client)
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
        Run Two Backups from different subclients
        """
        self.subclient1 = self.backupset.subclients.get(self.tcinputs["SubclientName1"])
        job1 = self.subclient.backup(backup_level="Full")
        job2 = self.subclient1.backup(backup_level="Full")
        self.backupjob_id1 = job1.job_id
        self.backupjob_id2 = job2.job_id
        self.jobid_list.extend([self.backupjob_id1, self.backupjob_id2])

    @test_step
    def run_send_log(self):
        """Running SendLog job"""
        self.job = Jobs(self.admin_console)
        self.job.access_job_by_id(self.jobid_list[0])
        self.job_details.send_logs()
        self.send_log.enter_additional_jobs(self.jobid_list[1])
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
        """ To verify cs, client , and media folders present in the path """
        entities_dict = {self.tcinputs['ClientName']: False, self.commcell_name: False,
                         self.media_agent: False, self.media_agent1: False}

        self.curr_path = self.base_path
        folder_list = self.local_machine.get_folders_in_path(self.curr_path, recurse=False)
        self.send_log_utils.verify_entities(folder_list, entities_dict, self.curr_path)

    @test_step
    def verify_send_log_for_client(self):
        """Verifying send logs collected from client"""
        self.log.info("Opening client folder and checking logs: clbackup.log ")
        entities_dict = {'clBackup.log': False}
        self.curr_path = os.path.join(self.base_path, self.tcinputs['ClientName'])
        file_list = self.local_machine.get_files_in_path(self.curr_path, recurse=False)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.curr_path)

    @test_step
    def verify_send_log_for_media_agent(self, mediaagent):
        """Verifying send logs collected from media agent """
        self.log.info(f'Opening {mediaagent} folder and checking logs: archiveIndex.log')
        entities_dict = {'archiveIndex.log': False}
        self.curr_path = os.path.join(self.base_path, mediaagent)
        file_list = self.local_machine.get_files_in_path(self.curr_path, recurse=False)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.curr_path)

    @test_step
    def verify_send_log_for_cs(self):
        """Verifying send logs collected from comm server"""
        self.log.info("Opening Commserver folder and checking logs: JobManager.log, PerfAnalysis logs ")
        entities_dict = {'JobManager.log': False}
        if "windows" in self.commserv_client.os_info.lower():
            entities_dict[f'PerfAnalysis_{self.backupjob_id1}.log'] = False
            entities_dict[f'PerfAnalysis_{self.backupjob_id2}.log'] = False
        else:
            perf_path = os.path.join(self.base_path, 'PerfAnalysisLogs')
            perf_files = [f'PerfAnalysis_{self.backupjob_id1}.log', f'PerfAnalysis_{self.backupjob_id2}.log']
            if all(perf_file in os.listdir(perf_path) for perf_file in perf_files):
                self.log.info(f'PerfAnalysis_{self.backupjob_id1}.log found in {perf_path}')
                self.log.info(f'PerfAnalysis_{self.backupjob_id2}.log found in {perf_path}')
            else:
                raise CVTestStepFailure(
                    f'PerfAnalysis_{self.backupjob_id1} and/or PerfAnalysis_{self.backupjob_id2} not found'
                    f'on {perf_path}'
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
            self.verify_send_log_for_media_agent(self.media_agent)
            self.verify_send_log_for_media_agent(self.media_agent1)
            self.verify_send_log_for_cs()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
