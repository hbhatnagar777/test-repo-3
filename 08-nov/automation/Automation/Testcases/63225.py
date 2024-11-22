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
    view_log_setting()                                    --  set registry setting for viewlogbyjobidfilenumberlimit
    run_backup()                                          --  run a backup job
    navigate_to_view_logs                                 --  navigate to view log
    validate_archive_limit                                --  step to validate the archive limit based on key
    revert_settings                                       --  removing the applied settings
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
            "63225":{
               "ClientName":"Client1",
               "AgentName":"File System",
               "BackupsetName":"defaultBackupSet",
               "SubclientName":"sc1",  // the subclient should have lots of contents so log file
                                              grows beyond 3 archive files
               "log_modules":[
                  "clBackup",
                  "FileScan"
               ]
               }
            }


"""
import time
from AutomationUtils.config import get_config
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.AdminConsolePages.view_logs import ViewLogs
from Web.AdminConsole.adminconsole import AdminConsole
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
        self.backupjob_id = None
        self.machine = None
        self.path = None
        self.job = None
        self.subclient = None
        self.commcell_name = None
        self.commcell_id = None
        self.navigator = None
        self.send_log_utils = None
        self.commserv_client = None
        self.job_details = None
        self.log_module_list = None
        self.file_size_limit = None
        self.view_logs = None
        self.debug_level = None
        self.registry_path = None
        self.archive_log_limit = None
        self.name = "Validate Archived Log Limit on View Logs by Job ID"

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
            self.commserv_client = self.commcell.commserv_client
            self.job_details = JobDetails(self.admin_console)
            self.machine = Machine(self.client)
            self.send_log_utils = SendLogUtils(self, self.machine)
            licence = LicenseDetails(self.commcell)
            self.view_logs = ViewLogs(self.admin_console)
            self.commcell_id = licence.commcell_id_hex
            self.log_module_list = self.tcinputs["log_modules"]
            self.file_size_limit = "1"
            self.registry_path = "sendLogFiles"
            self.archive_log_limit = "3"
            self.debug_level = "10"

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def view_log_setting(self):
        """
        Controls the archive files read by view logs
        """
        for each_module in self.log_module_list:
            self.log.info(f'Increasing the debug level to {self.debug_level} for {each_module}')
            self.machine.set_logging_debug_level(each_module.upper(), self.debug_level)
            self.log.info(f'Setting {each_module} file size to {self.file_size_limit} MB on Path EventManager')
            self.machine.set_logging_filesize_limit(each_module.upper(), self.file_size_limit)

    @test_step
    def run_backup(self):
        """
        Run backup from a subclient
        """
        job = self.subclient.backup(backup_level="Full")
        self.backupjob_id = job.job_id
        self.log.info(f'Running Backup Job ID: {self.backupjob_id}')

    @test_step
    def navigate_to_view_logs(self):
        """Running view logs job"""
        self.job = Jobs(self.admin_console)
        self.job.access_job_by_id(self.backupjob_id)
        self.job_details.view_logs()

    def get_archive_file_counts(self):
        log_dict = {}
        logfile_names = self.view_logs.get_logfile_names(job_view_logs=True)
        for each_log in logfile_names:
            for log_name in self.log_module_list:
                if each_log.startswith(log_name) and any(char.isdigit() for char in each_log):
                    if log_name in log_dict:
                        log_dict[log_name] += 1
                    else:
                        log_dict[log_name] = 1

        for log_name, archive_count in log_dict.items():
            self.log.info(f'Number of archive files count for {log_name} is {archive_count}')

        return log_dict

    @test_step
    def validate_archive_limit(self):
        """Validate the archive limit"""
        log_dict = self.get_archive_file_counts()
        self.log.info(f'Validating...')
        for log_name, archive_count in log_dict.items():
            if archive_count <= int(self.archive_log_limit):
                self.log.info(f'{log_name} : {archive_count}')
            else:
                self.log.info("Validation Error")
                raise CVTestStepFailure(
                    f"Validation Failure for {log_name} : {archive_count}"
                )

    @test_step
    def revert_settings(self):
        """Removing the registry settings"""
        for each_module in self.log_module_list:
            self.machine.remove_registry("EventManager", each_module.upper() + "_DEBUGLEVEL")
            self.machine.remove_registry("EventManager", each_module.upper() + "_MAXLOGFILESIZE")

    def run(self):
        try:
            self.init_tc()
            self.view_log_setting()
            self.run_backup()
            self.log.info("Waiting for 15 minutes to complete the backup job")
            time.sleep(900)
            self.navigate_to_view_logs()
            self.validate_archive_limit()
            self.revert_settings()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
