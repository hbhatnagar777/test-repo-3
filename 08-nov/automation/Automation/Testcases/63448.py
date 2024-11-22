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
    run_send_log_for_job()    --  run send logs job for the backup job with index collection option
    verify_index_collection() --  verify index collection in the sendlogs output
    run()                     --  run function of this test case

Input Example:

    "testCases":
            {
                "63448":
                        {
                            "ClientName": "Client Name",
                            "AgentName": "File System",
                            "BackupsetName": "Backup set",
                            "SubclientName": "subclient"
                        }
            }


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
from Web.API.customreports import CustomReportsAPI



_STORE_CONFIG = get_config()
class TestCase(CVTestCase):
    """Sendlogs - test case to validate index collection from job level"""
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
        self.job = None
        self.job_details = None  
        self.sendlogs_job_id = None
        self.jobid_list = []
        self.backup_jobid = None
        self.local_machine = None
        self.backupset_guid = None
        self.name = "Sendlogs: Validate index collection from job level"

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
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def init_backupset_guid(self):
        """
        read backup set guid from the database
        """
        self.cre_api = CustomReportsAPI(self.commcell_name)
        query = r"select distinct BS.GUID from APP_Client C with (nolock) " \
                "inner join app_application A with (nolock) " \
                "on C.id = A.clientid and A.apptypeid = 33 " \
                "and A.subclientStatus & 8 = 0 " \
                "inner join APP_BackupSetName BS with (nolock) " \
                "on A.backupSet = BS.id and BS.status & 8 = 8 " \
                " where C.name = '" + self.tcinputs['ClientName'] + "' and " \
                " BS.name = '" + self.tcinputs['BackupsetName'] + "'"

        response = self.cre_api.execute_sql(query)
        if not response:
            raise CVTestStepFailure(
                "Retreiving Backupset set guid from Database failed"
            )
        self.backupset_guid = response[0][0]


    @test_step
    def run_backup(self):
        """Run backup job """
        self.subclient = self.backupset.subclients.get(self.tcinputs['SubclientName'])
        backup_job = self.subclient.backup(backup_level="Full")
        backup_job.wait_for_completion()
        self.backup_jobid = backup_job.job_id

    @test_step
    def run_send_log_for_job(self):
        """Running SendLog job for a job"""
        self.job.access_job_by_id(self.backup_jobid)
        self.job_details.send_logs()
        advanced_list = self.send_log.Advancedlist
        self.send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        self.send_log.select_advanced(advanced_list=[advanced_list.INDEX])
        info_list = self.send_log.Informationlist
        self.send_log.select_information(information_list=[info_list.OS_LOGS, info_list.LOGS])
        self.sendlogs_job_id = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sendlogs_job_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sendlogs_job_id}] failed"
            )
        self.log.info("Backup job id " + self.backup_jobid)
        self.jobid_list.append(self.backup_jobid)

    @test_step
    def verify_index_collection(self):
        """Verify SendLog job index files """
        logs_path = self.send_log_utils.get_uncompressed_path(self.sendlogs_job_id, self.jobid_list)
        self.send_log_utils.is_index_file_exists(logs_path, self.tcinputs['ClientName'], self.backupset_guid)
    
    def run(self):
        try:
            self.init_tc()
            self.init_backupset_guid()
            self.run_backup()
            self.run_send_log_for_job()
            self.log.info('Waiting for 5 mins to check file present at location '
                          + _STORE_CONFIG.Reports.uncompressed_logs_path +
                          ' for send log job id ' + self.sendlogs_job_id)
            time.sleep(300)
            self.verify_index_collection()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
