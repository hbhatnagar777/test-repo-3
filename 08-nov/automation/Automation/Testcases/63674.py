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
    self.get_associated_server                            -- get the server names associated from cvpysdk
    self.validate_schedule_mails()                        -- Verify the schedule data
    subscribe_for_me()                                    -- Enable Subscription for user
    subscribe_for_usergroup()                             -- Enable Subscription for usergroup
    unsubscribe()                                         -- Disbale Subscription
    run()                                                 --  run function of this test case
Input Example:

    "testCases":
            {
                "63674":
                        {
                            "Username": "test",
                            "Password": "test"
                        }
            }
"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mail_box import MailBox
from AutomationUtils import config

from Reports.utils import TestCaseUtils
from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.webconsole import WebConsole

from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from cvpysdk.schedules import Schedules

_CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
        TestCase class used to execute the test case from here.
        """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Acceptance Test case for Tenant Report Subscription Schedules."
        self.browser = None
        self.webconsole = None
        self.admin_console = None
        self.format = "HTML"
        self.manage_report = None
        self.manage_schedules_api = None
        self.navigator = None
        self.mail = None
        self.tcinputs = {
            "Username": None,
            "Password": None
        }
        self.viewer = None
        self.schedule_name = f"63674 Backup job summary"
        self.utils = CustomReportUtils(self)
        self.utils = TestCaseUtils(self)
        self.html_browser = None
        self.input_values = None

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.mail = MailBox()
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
                except Exception as exp:  # in case service is already opened
                    hub_dashboard.go_to_admin_console()
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.navigator.navigate_to_reports()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.viewer = viewer.CustomReportViewer(self.admin_console)
            self.ununsubscribe_report(self.schedule_name, user_type=1)
            self.ununsubscribe_report(self.schedule_name, user_type=2)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def get_client_display_name(self, clients):
        """Gets Client's display name"""
        client_name = clients.keys()
        display_name = []
        for name in client_name:
            display_name.append(clients.get(name).get('displayName'))
        return display_name

    @test_step
    def get_associated_servers(self):
        """ get_associated_servers"""
        all_clients = self.commcell.clients.all_clients
        all_clients.update(self.commcell.clients.hidden_clients)
        self.input_values = sorted(self.get_client_display_name(all_clients))
        # Adding Hypervisors / VC to client list
        virtualization_clients = self.commcell.clients._get_virtualization_clients()
        if virtualization_clients:
            virtualization_client = virtualization_clients.keys()
            self.input_values.extend(virtualization_client)
        salesforce_clients = self.commcell.clients.salesforce_clients
        if salesforce_clients:
            salesforce_client = salesforce_clients.keys()
            self.input_values.extend(salesforce_client)

    @test_step
    def subscribe_for_me(self):
        """Subscribe user to schedule"""
        self.subscribe_report(self.schedule_name, user_type=1)
        self.log.info(f"Subscription for [user] is successfully done.")

    @test_step
    def subscribe_for_usergroup(self):
        """Subscribe usergroup to schedule"""
        self.subscribe_report(self.schedule_name, user_type=2)
        self.log.info(f"Subscription for [user group] is successfully done.")

    @test_step
    def unsubscribe_for_me(self):
        """unsubscribe from schedule subscription"""
        self.ununsubscribe_report(self.schedule_name, user_type=1)
        self.log.info(f"Unsubscribe for [user] is successfully done.")

    @test_step
    def unsubscribe_for_usergroup(self):
        """unsubscribe from schedule subscription"""
        self.ununsubscribe_report(self.schedule_name, user_type=2)
        self.log.info(f"Unsubscribe for [user group] is successfully done.")

    def subscribe_report(self, schedule_name, user_type):
        """
        Subscribe User to report schedule
        Args:
            schedule_name (str): report schedule name
            user_type: 1 for user, 2 for user group
        """
        self.manage_report.check_subscription_checkbox(schedule_name, user_type)
        notification = self.admin_console.get_notification(10)
        self.log.info(f"Notification received - {notification}")
        if 'successfully subscribed' not in notification:
            self.log.error("Subscription Failed!")
            self.log.error(f"Notification received {notification}")
            raise CVTestStepFailure("Subscription Failed!")
        self.log.info("Subscribed to Schedule successfully!")

    def ununsubscribe_report(self, schedule_name, user_type):
        """
        UnSubscribe User to report schedule
        Args:
            schedule_name (str): report schedule name
            user_type: 1 for user, 2 for user group
        """
        self.manage_report.uncheck_subscription_checkbox(schedule_name, user_type)
        notification = self.admin_console.get_notification(10)
        self.log.info(f"Notification received - {notification}")
        if 'successfully unsubscribed' not in notification:
            self.log.error("Unsubscription Failed!")
            self.log.error(f"Notification received {notification}")
            raise CVTestStepFailure("Unsubscription Failed!")
        self.log.info("UnSubscribed to Schedule successfully")

    def get_html_content(self):
        """
        Read HTML table and returns specified column data
        """
        file_path = self.utils.get_attachment_files(ends_with="HTML")
        self.html_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.html_browser.open()
        self.html_browser.goto_file(file_path=file_path[0])
        html_adminconsole = AdminConsole(self.html_browser, self.commcell.webconsole_hostname)
        html_viewer = viewer.CustomReportViewer(html_adminconsole)
        html_table = viewer.DataTable("Job Details")
        html_viewer.associate_component(html_table)
        html_column_data = html_table.get_column_data('Server')
        html_column_data = [x.lower() for x in html_column_data]
        return html_column_data

    @test_step
    def validate_schedule_mails(self):
        """Validate schedule mails"""
        self.utils.reset_temp_dir()
        self.mail.connect()
        self.log.info("verifying [%s] schedule email for subscribe schedules", self.schedule_name)
        self.utils.download_mail(self.mail, self.schedule_name)
        html_data = self.get_html_content()
        mismatch = list(set(html_data) - set(self.input_values))
        if mismatch:
            self.log.error("HTML column has values :%s", str(html_data))
            self.log.error("Web report column has values :%s", set(self.input_values))
            self.log.error(f"Mismatched column values are [{mismatch}]")
            raise CVTestStepFailure("HTML column values are not matching with report column values")
        self.log.info("HTML contents are verified successfully!")
        Browser.close_silently(self.html_browser)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.get_associated_servers()
            self.subscribe_for_me()
            self.log.info("Waiting for 30 mins, for subscription schedule email to be received.")
            sleep(1800)
            self.validate_schedule_mails()
            self.unsubscribe_for_me()
            self.subscribe_for_usergroup()
            self.log.info("Waiting for 30 mins, for subscription schedule email to be received.")
            sleep(1800)
            self.validate_schedule_mails()
            self.unsubscribe_for_usergroup()

        except Exception as e:
            self.utils.handle_testcase_exception(e)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
