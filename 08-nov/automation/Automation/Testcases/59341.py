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
    verify_tenant_admin_actions()  -- verify tenant admin can perform send logs and
                                        view logs
    verify_tenant_user_actions()   -- verify tenant user can't see send logs and
                                        view logs actions.
    run()                    --  run function of this test case

Input Example:

    "testCases":
            {
                "59341":
                        {
                            "TenantAdminUser": "Tenant admin user",
                            "TenantAdminPassword": "Tenant admin password",
                            "TenantUser" : "Tenant user"
                            "TenantUserPassword" : "Tenant user password",
                            "ClientName": "Client Name",
                            "AgentName": "File System",
                            "BackupsetName": " Backup set",
                        }
            }


"""
import time
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
from selenium.common.exceptions import NoSuchElementException

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Sendlogs: verify view logs and sendlogs for tenant admin and tenant users"""
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
        self.jobid = None
        self.utils = None
        self.commcell_id = None
        self.commcell_name = None
        self.download_directory = None
        self.machine = None
        self.path = None
        self.directory = None
        self.utils = TestCaseUtils(self)
        self.utils.reset_temp_dir()
        self.download_directory = self.utils.get_temp_dir()
        self.send_log_utils = None
        self.commserv_client = None
        self.fs_client = None
        self.file_server = None
        self.job = None
        self.job_details = None
        self.sendlogs_job_id = None
        self.jobid_list = []
        self.backup_jobid = None
        self.local_machine = None
        self.name = "Sendlogs: verify view logs and sendlogs for tenant admin and tenant users"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.fs_client = self.tcinputs['ClientName']
            self.commserv_client = self.commcell.commserv_client
            self.machine = Machine()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.tcinputs['TenantAdminUser'],
                                     self.tcinputs['TenantAdminPassword'])
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.download_directory = self.send_log_utils.create_directory_for_given_path(
                "TC59341")
            self.commcell_name = self.commcell.commserv_name
            self.file_server = FileServers(self.admin_console)
            self.send_log = SendLogs(self.admin_console)
            self.job = Jobs(self.admin_console)
            self.job_details = JobDetails(self.admin_console)
            self.local_machine = Machine()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log_for_client(self, userName):
        """Running SendLog job for the client"""
        self.admin_console.navigator.navigate_to_file_servers()
        self.admin_console.wait_for_completion()
        self.file_server.action_sendlogs(self.fs_client)
        if self.send_log.is_csdb_option_present():
            raise CVTestStepFailure(
                f"Commserv Database option is present for the tenant admin [{userName}] "
            )
        else:
            self.log.info(
                f"Commserv Database option is not present for the tenant admin [{userName}] ")
        self.jobid = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.jobid)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.jobid}] failed"
            )

    @test_step
    def run_backup(self):
        """Run backup job """
        self.subclient = self.backupset.subclients.get("TC59341")
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
    def verify_send_log_for_job(self):
        """Verify SendLog job output for a job"""
        logs_path = self.send_log_utils.get_uncompressed_path(self.sendlogs_job_id,
                                                              self.jobid_list)
        self.log.info("logs path " + logs_path)
        folders_list = self.local_machine.get_folders_in_path(logs_path, recurse=False)
        for folder in folders_list:
            if self.commcell_name in folder:
                raise CVTestStepFailure(
                    f" Commcell folder is collected as part of tenant admin job "
                )
        self.log.info("Commcell folder is not collected as part of tenant admin job")

    @test_step
    def view_logs_for_client(self):
        """View logs for the client"""
        self.admin_console.refresh_page()
        self.admin_console.navigator.navigate_to_file_servers()
        self.file_server.view_live_logs(self.fs_client)

    @test_step
    def verify_tenant_admin_actions(self):
        """Verify tenant admin actions ( send logs and view logs )"""
        self.run_send_log_for_client(self.tcinputs['TenantAdminUser'])
        try:
            self.view_logs_for_client()
        except NoSuchElementException:
            self.log.info("view logs action is not available for the tenant admin")
            raise CVTestStepFailure(
                f"Tenant admin doesn't have view logs action in the servers page"
            )
        self.run_backup()
        self.run_send_log_for_job()
        self.log.info('Waiting for 15 mins to check file present at location ' +
                      _STORE_CONFIG.Reports.uncompressed_logs_path
                      + ' for send log job id ' + self.sendlogs_job_id)
        time.sleep(900)
        self.verify_send_log_for_job()

    @test_step
    def verify_tenant_user_actions(self):
        """Verify tenant user actions ( send logs and view logs )"""
        self.admin_console.login(self.tcinputs['TenantUser'],
                                 self.tcinputs['TenantUserPassword'])
        try:
            self.run_send_log_for_client(self.tcinputs['TenantUser'])
        except NoSuchElementException:
            self.log.info("send logs action is not available for the tenant user")
        else:
            raise CVTestStepFailure(
                f"Tenant user has send logs action in the servers page"
            )

        try:
            self.view_logs_for_client()
        except NoSuchElementException:
            self.log.info("view logs action is not available for the tenant user")
        else:
            raise CVTestStepFailure(
                f"Tenant user has view logs action in the servers page"
            )

    def run(self):
        try:
            self.init_tc()
            self.verify_tenant_admin_actions()
            AdminConsole.logout_silently(self.admin_console)
            self.verify_tenant_user_actions()
            self.machine.remove_directory(self.download_directory)
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
