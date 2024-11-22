# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this testcase

    run()                           --  run function of this testcase

    tear_down()                     --  tear down function of this testcase

    verify_event_table_displayed()  --  Events are displayed in table properly

    verify_filters()                --  Verifies each tab in events page

    verify_events_list()            --  Verifies given tab in events page

    verify_date_for_critical()      --  Verifies date for 24 hour tabs
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Events import Events
from Web.AdminConsole.Components.table import Rtable
from Reports.utils import TestCaseUtils
from datetime import datetime
from dateutil.parser import parse

from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test for Events test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Test Case to verify proper working of Events page filters"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.table = None
        self.event_obj = None
        self.tcinputs = {}

    @test_step
    def verify_event_table_displayed(self):
        """ To verify that the events table is displayed """
        event_table_data = self.table.get_table_data()
        if event_table_data:
            self.log.info('Event table displayed correctly')
        else:
            exp = "'Event table not displayed correctly'"
            raise Exception(exp)

    @test_step
    def verify_filters(self):
        """ To apply the filters and verify the data displayed one by one"""
        self.event_obj.show_critical_events()
        self.verify_events_list('Critical')
        self.event_obj.show_major_events()
        self.verify_events_list('Major')
        self.event_obj.show_minor_events()
        self.verify_events_list('Minor')
        self.event_obj.show_info_events()
        self.verify_events_list('Info')
        self.event_obj.show_critical_events(day=True)
        self.verify_events_list('Critical', day=True)

    @test_step
    def verify_events_list(self, expected_severity, day=False):
        """
        Method to verify lists all the events for a job
        Args:
                expected_severity (str) : the severity to be checked for table events
                day (bool) : indicates checking of date column for less than 24 hrs
        """
        self.log.info('Validating displayed columns on {} filter applied'.format(expected_severity))
        if day:
            self.verify_date_for_critical()

        event_severity_list = self.table.get_column_data('Severity')
        if all(severity == expected_severity for severity in event_severity_list):
            self.log.info('All the values match, filter "{}" working correctly'.format(expected_severity))
        else:
            exp = "'Values do not match, filter - {} not working correctly'".format(expected_severity)
            raise Exception(exp)

    @test_step
    def verify_date_for_critical(self):
        """ Method to check if all the values for filter Critical (last 24 hours) are correct """
        event_date_list = self.table.get_column_data('Date')
        if all(datetime.now().timestamp() - parse(date).timestamp() <= 2 * 24 * 60 * 60 for date in event_date_list):
            self.log.info('All events are of last 24 hrs')
        else:
            exp = "'All events are not from the last 24 hrs'"
            raise Exception(exp)

    def setup(self):
        """Setup function of this test case"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.table = Rtable(self.admin_console)
        self.event_obj = Events(self.admin_console)

    def run(self):
        """Main function for test case execution"""
        try:
            self.admin_console.navigator.navigate_to_events()
            self.verify_event_table_displayed()
            self.verify_filters()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean up the test case environment created """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
