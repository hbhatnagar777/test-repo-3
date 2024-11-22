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
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case
"""


import traceback

from AutomationUtils.config import get_config

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Components import callout
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure, CVWebAutomationException
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Global CC]: Validate Header Activities (Alerts/Events/Jobs) Functionality"
        self.browser = None
        self.admin_console = None
        self.config = None
        self.exp = None
        self.tcinputs = {}

    def setup(self):
        """Setup function of this test case"""
        self.config = get_config()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator

        # switch to global view
        self.log.info("Switching to Global view...")
        self.navigator.switch_service_commcell('Global')
        self.callout = callout.NotificationHeaderCallout(self.admin_console)
        self.table = Rtable(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:

            retry_count = 5
            while retry_count:
                try:
                    self.validate_alert_notifications()

                    self.validate_event_notifications()

                    self.validate_job_notifications()
                    break
                except Exception as exp:
                    if retry_count == 1:
                        raise exp

                    self.log.info(traceback.format_exc())
                    self.tear_down()
                    retry_count -= 1
                    self.log.info("TC Failed, trying again")
                    self.setup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def validate_alert_notifications(self):
        """Method to validate alert notifications from top header"""
        self.admin_console.access_alerts_notification()
        callout_data = self.callout.get_notifications()

        self.navigator.navigate_to_alerts()
        self.table.apply_sort_over_column("Detected time", False)
        table_data = self.table.get_rows_data()
        notifications_table_text = [table_data[1][idx]['Alert info'] for idx in table_data[1]]

        self.compare([list(i.keys())[0] for i in callout_data], notifications_table_text[:5], "Alert")

    @test_step
    def validate_job_notifications(self):
        """Method to validate job notifications from top header"""
        self.admin_console.access_jobs_notification()
        callout_data = self.callout.get_notifications()

        self.navigator.navigate_to_jobs()
        active_jobs_stats = Jobs(self.admin_console).get_active_jobs_stats()

        for label in callout_data:
            # Removing Completed jobs data as we don't have that in active jobs page
            if list(label.keys())[0] != 'Completed':
                self.compare(list(label.values())[0], active_jobs_stats[list(label.keys())[0]],
                             f'Jobs ({list(label.keys())[0]})')

    @test_step
    def validate_event_notifications(self):
        """Method to validate event notifications from top header"""
        self.admin_console.access_events_notification()
        callout_data = self.callout.get_notifications()

        self.navigator.navigate_to_events()
        self.table.apply_sort_over_column("Date", False)
        table_data = self.table.get_column_data('Description')

        self.compare([list(i.keys())[0] for i in callout_data], table_data, "Events")

    def compare(self, notification, listing, entity):
        """Method to process and compare data and raise exception if it doesn't match"""
        if notification != listing:
            self.log.info(f"Notification icon list: {notification}")
            self.log.info(f"{entity} Listing page list: {listing}")

            raise CVWebAutomationException(f"Data from notification icon {'list' if type(notification)==list else ''} "
                                           f"does not match the {entity} listing page list")