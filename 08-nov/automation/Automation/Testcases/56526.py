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
    self.init_tc()                                        --  Initialize pre-requisites
    self.get_report_server_data()                         -- get the server names from command center
    self.verify_schedule_data()                           -- create schedule on command center
    self.validate_schedule_mails()                        -- Verify the schedule date
    run()                                                 --  run function of this test case
Input Example:

    "testCases":
            {
                "56526":
                        {
                            "Tenant_admin_group" : "Tenant_admin_group_Name",
                            "Tenant_admin_username" : "Tenant_user_Name",
                            "Tenant_admin_password" : "Tenant_Credential",
                            "ClientName" : "Display_Name"
                        }
            }
"""
from time import sleep, time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mail_box import MailBox
from AutomationUtils import config

from Reports.utils import TestCaseUtils
from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.WebConsole.Reports import cte
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.Custom import viewer

from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules

from cvpysdk.commcell import Commcell
from cvpysdk.schedules import Schedules

_CONSTANTS = config.get_config()
export_type = cte.ConfigureSchedules.Format


class TestCase(CVTestCase):
    """
        TestCase class used to execute the test case from here.
        """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.report_servers = None
        self.name = "Verify End User Security check"
        self.browser = None
        self.admin_console = None
        self.reports = "Backup job summary"
        self.format = export_type.HTML
        self.manage_report = None
        self.manage_schedules_api = None
        self.navigator = None
        self.mail = None
        self.tcinputs = {
            "tenant_admin_group": None,
            "ClientName": None
        }
        self.table = None
        self.viewer = None
        self.schedule_name = f"Automation_tc_56526_{self.format}_{str(int(time()))}"
        self.utils = CustomReportUtils(self)
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.mail = MailBox()
            self.mail.connect()
            self.manage_schedules_api = Schedules(self.commcell)

            # open browser
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()

            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.tcinputs["Username"],
                self.tcinputs["Password"],
            )
            sleep(5)
            if self.admin_console.driver.title == 'Hub - Metallic':
                self.log.info("Navigating to adminconsole from Metallic hub")
                hub_dashboard = Dashboard(self.admin_console, HubServices.endpoint)
                try:
                    hub_dashboard.choose_service_from_dashboard()
                    hub_dashboard.go_to_admin_console()
                except:  # in case service is already opened
                    hub_dashboard.go_to_admin_console()
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.navigator.navigate_to_reports()
            self.manage_report.access_report(self.reports)
            self.viewer = viewer.CustomReportViewer(self.admin_console)
            self.table = viewer.DataTable("Job Details")
            self.viewer.associate_component(self.table)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def get_report_server_data(self):
        """Get the list of servers from the report"""
        self.report_servers = self.table.get_column_data('Server')
        return self.report_servers

    @test_step
    def create_schedules(self):
        """create schedule with end-user security enabled"""
        tenant_group = self.tcinputs["tenant_admin_group"]

        self.log.info("Creating [%s]  schedule with the [%s] export_type for the [%s] tenant admin group ",
                      self.schedule_name, self.format, tenant_group)
        report = Report(self.admin_console)
        schedule = report.schedule()
        schedule.create_schedule(
            schedule_name=self.schedule_name,
            user_or_group=tenant_group,
            end_user_security_enabled = True,
            file_format=self.format
        )

    def verify_schedule_exists(self):
        """Verify schedules are present in commcell"""
        self.manage_schedules_api.refresh()
        self.log.info("Checking [%s] schedule is created", self.schedule_name)
        if not self.manage_schedules_api.has_schedule(self.schedule_name):
            err_str = f"{self.schedule_name} schedule does not exists in commcell"
            raise CVTestStepFailure(err_str)

    def run_schedules(self):
        """Run schedule"""
        _schedule = self.manage_schedules_api.get(self.schedule_name)
        self.log.info(f"Running {self.schedule_name} schedule")
        job_id = _schedule.run_now()
        job = self.commcell.job_controller.get(job_id)
        self.log.info("Wait for [%s] job to complete", str(job))
        if job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info(f"Schedule job completed with job id:{job_id} for {self.schedule_name} schedule")
        else:
            err_str = f"{self.schedule_name} Schedule job failed with job id {job}"
            raise CVTestStepFailure(err_str)
        self.log.info("All schedules are completed successfully")

    def get_servers_count(self):
        """ get the list of server from the tenant group account"""
        tenant_commcell = Commcell(webconsole_hostname=self.inputJSONnode['commcell']["webconsoleHostname"],
                                   commcell_username=self.tcinputs['tenant_admin_username'],
                                   commcell_password=self.tcinputs['tenant_admin_password'])
        client_names = tenant_commcell.clients.all_clients
        client_list = list(client_names.keys())
        return client_list

    @test_step
    def validate_schedule_mails(self):
        """Validate schedule mails"""
        tenant_servers = self.get_servers_count()
        self.utils.reset_temp_dir()
        self.log.info("verifying [%s] schedule email for [%s] report with [%s] file extension",
                      self.schedule_name, self.reports, self.format)
        self.utils.download_mail(self.mail, self.schedule_name)

        # To navigate to the downloaded mail
        file_path = self.utils.get_attachment_files(ends_with="HTML")
        self.browser.open_new_tab()
        self.browser.switch_to_latest_tab()
        self.browser.driver.get(file_path[0])
        sleep(3)
        adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        mail_viewer = viewer.CustomReportViewer(adminconsole)
        mail_table = viewer.DataTable("Job Details")
        mail_viewer.associate_component(mail_table)
        servers = mail_table.get_exported_table_data()['Server']
        for each_server in servers:
            if each_server.lower() not in self.client.client_name and each_server.lower() not in tenant_servers and \
                    each_server.lower() not in self.report_servers:
                self.log.error(f"Expected server name is {self.report_servers} but received {each_server}")
        self.log.info(" The email content has only visible client")
        self.browser.close_current_tab()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.delete_schedules()

    def delete_schedules(self):
        """Delete the schedules"""
        self.navigator.navigate_to_reports()
        self.manage_report.view_schedules()
        manage_schedules_web = ManageSchedules(self.admin_console)
        if self.schedule_name not in manage_schedules_web.get_all_schedules(column_name='Name'):
            raise CVTestStepFailure(f"The schedule {self.schedule_name} is not available")
        manage_schedules_web.cleanup_schedules(self.schedule_name)
        self.log.info("Schedules are deleted")

    @test_step
    def verify_schedule_data(self):
        """ create schedule and validate it"""
        self.create_schedules()
        self.verify_schedule_exists()
        self.run_schedules()
        self.log.info("Wait for 2 minutes for mail to be received")
        sleep(120)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.get_report_server_data()
            self.verify_schedule_data()
            self.validate_schedule_mails()

        except Exception as Exp:
            self.utils.handle_testcase_exception(Exp)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
