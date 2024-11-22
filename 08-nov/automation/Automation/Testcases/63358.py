# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Mainfile for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                            --  initialize TestCase class
    init_tc()                                             --  Initialize pre-requisites
    run_backup_job()                                      --  runs backup job on a FS subclient
    gather_details_for_rfc()                              --  collects the necessary information for rfc
    run_send_log()                                        --  send logs operation for the job
    verify_rfc_logs()                                     --  verifies the rfc logs by comparison
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "63358":
                        {
                            AgentName: "",
                            BackupLevel: "",
                            BackupsetName: "",
                            ClientName: "",
                            SubclientName: ""

                        }
            }

"""

import os
import re
import time
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Indexing.database import index_db
from Indexing.helpers import IndexingHelpers
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
from Reports.utils import TestCaseUtils
from cvpysdk.job import JobController

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Test Case: Sendlogs: Validate RFC collection"""
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
        self.client = None
        self.subclient = None
        self.idx_client = None
        self.admin_console = None
        self.sjob_id = None
        self.backup_jobid = None
        self.machine = None
        self.idx_db = None
        self.utils: TestCaseUtils = None
        self.send_log_utils = None
        self.send_log = None
        self.local_machine = None
        self.navigator = None
        self.commcell_name = None
        self.commcell_id = None
        self.job_controller = None
        self.job_details = None
        self.jobid_list = []
        self.path = None
        self.idx_help = None
        self.name = "Sendlogs: Validate RFC collection"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.utils = TestCaseUtils(self,
                                       username=self.inputJSONnode["commcell"]["commcellUsername"],
                                       password=self.inputJSONnode["commcell"]["commcellPassword"])
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
            license = LicenseDetails(self.commcell)
            self.job_controller = JobController(self.commcell)
            self.idx_help = IndexingHelpers(self.commcell)
            self.local_machine = Machine()
            self.job_details = JobDetails(self.admin_console)
            self.commcell_id = license.commcell_id_hex

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_backup_job(self):
        """Run a backup job"""
        self.subclient = self.backupset.subclients.get(self.tcinputs["SubClientName"])
        job = self.subclient.backup(backup_level="FULL")
        self.backup_jobid = job.job_id
        self.log.info(f'Backup Job ID: {self.backup_jobid}')
        job.wait_for_completion()

    @test_step
    def gather_details_for_rfc(self):
        """Gather details for RFC collection"""
        job_obj = self.commcell.job_controller.get(self.backup_jobid)
        job_details = job_obj._get_job_details()
        self.idx_db = index_db.get(self.subclient)
        self.idx_client = job_details['jobDetail']['generalInfo']['subclient']['clientName']
        self.jobid_list.append(self.backup_jobid)

    @test_step
    def run_send_log(self):
        """Running SendLog job"""
        self.job = Jobs(self.admin_console)
        self.job.access_job_by_id(self.backup_jobid)
        self.job_details.send_logs()
        info_list = self.send_log.Informationlist
        self.send_log.deselect_information(information_list=[info_list.OS_LOGS, info_list.MACHINE_CONFIG,
                                                             info_list.ALL_USERS_PROFILE])
        advanced_list = self.send_log.Advancedlist
        self.send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        self.send_log.select_advanced(advanced_list=[advanced_list.RFC])
        self.sjob_id = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sjob_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sjob_id}] failed"
            )

    @test_step
    def verify_rfc_logs(self):
        """Verifies the rfc logs present at the RFC path or not"""
        rfc_server = self.idx_help.get_rfc_server(job_id=self.backup_jobid)
        rfc_server_name = rfc_server.name
        self.log.info('RFC server for the job: %s is %s', self.backup_jobid, rfc_server_name)
        rfc_server_machine = Machine(rfc_server_name, self.commcell)
        rfc_folder_path = self.idx_db.get_rfc_folder_path(
            rfc_server_machine= rfc_server_machine,
            job_id = self.backup_jobid
        )
        flag = True
        self.log.info(f"Index Client where RFC is present is {self.idx_client}")
        sl_rfc_path = os.path.join(self.path, self.idx_client, "Index Cache")
        folder_list = self.local_machine.get_folders_in_path(sl_rfc_path, recurse=False)
        for each_folder_path in folder_list:
            if f'J{self.backup_jobid}' in each_folder_path:
                sl_rfc_path = each_folder_path
                flag = False
                break
        if flag:
            self.log.error(f"RFC is not collected for {self.backup_jobid} at {sl_rfc_path}")
            raise CVTestStepFailure(
                f"RFC is not collected for {self.backup_jobid} at {sl_rfc_path}"
            )
        sl_rfc_files = self.local_machine.get_files_in_path(sl_rfc_path)
        rfc_server_files = rfc_server_machine.get_files_in_path(rfc_folder_path)
        self.log.info(f"RFC files from Sendlogs: {sl_rfc_files}")
        self.log.info(f"RFC files from RFC: {rfc_server_files}")
        sl_rfc_files = sorted([file.split('\\')[-1] for file in sl_rfc_files])  # Gives the filename from path
        rfc_server_files = [file.split('\\')[-1] for file in rfc_server_files]
        rfc_server_files = [file.replace('.rfczip', '') for file in rfc_server_files]  # Removes .rfczip from filename
        pattern = re.compile('|'.join(map(str, ['COLLECT', 'STATEFILE'])))  # Removes collectfile and statefile
        rfc_avoid_files = sorted(list(filter(pattern.search, rfc_server_files)))
        rfc_check_files = sorted(list(set(rfc_server_files).difference(set(rfc_avoid_files))))
        if rfc_check_files == sl_rfc_files:
            self.log.info(f'RFC files are collected successfully'
                          f'{sl_rfc_files}')
        else:
            if len(rfc_check_files) > len(sl_rfc_files):
                self.log.error(f'Not all RFC files are collected successfully')
            else:
                self.log.error(f'Unnecessary RFC files are collected')

            raise CVTestStepFailure(
                f'RFC_Check_Files: {rfc_check_files}'
                f'Collected RFC Files: {sl_rfc_files}'
            )

    def run(self):
        try:
            self.init_tc()
            self.run_backup_job()
            self.gather_details_for_rfc()
            self.run_send_log()
            self.log.info('Waiting for 20 mins to check file present at location ' +
                          _STORE_CONFIG.Reports.uncompressed_logs_path
                          + ' for send log job id ' + self.sjob_id)
            time.sleep(1200)
            self.path = self.send_log_utils.get_uncompressed_path(self.sjob_id, self.jobid_list)
            self.verify_rfc_logs()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
