# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Chargeback report metrics table validation

Input: no input is required

"""

from enum import Enum
from datetime import date, timedelta, datetime


from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports import reportsutils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.chargeback import Chargeback

from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.API.customreports import CustomReportsAPI


class IntervalType(Enum):
    """Interval type used in chargeback report"""
    Daily = 4
    Weekly = 2
    Monthly = 1


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.utils = None
        self.name = "Chargeback report metrics table validation"
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.chargeback = None
        self.private_metrics = None
        self.db_connection = None

    def init_webconsole(self):
        """Initialize the webconsole and redirect to chargeback report"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
        self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                              self.inputJSONnode['commcell']["commcellPassword"])
        self.webconsole.goto_commcell_dashboard()
        self.navigator = Navigator(self.webconsole)
        commcell_name = reportsutils.get_commcell_name(self.commcell)
        self.navigator.goto_commcell_dashboard(commcell_name)
        self.navigator.goto_commcell_reports("Chargeback")
        self.chargeback = Chargeback(self.webconsole)


    def setup(self):
        """Intializes Private metrics object required for this testcase"""
        self.db_connection = CustomReportsAPI(self.commcell.webconsole_hostname,
                                              username=self.inputJSONnode['commcell']["commcellUsername"],
                                              password=self.inputJSONnode['commcell']["commcellPassword"])
        self.utils = TestCaseUtils(self, self.inputJSONnode['commcell']["commcellUsername"],
                                   self.inputJSONnode['commcell']["commcellPassword"])

    def get_start_date_data(self, interval_type):
        """
        Get StartDate column data from database
        Args:
            interval_type (int): select TYPE from declaration Enum Daily, Weekly, Monthly

        Returns (list) : query result in list
        """
        query = """SELECT TOP 1 StartDate FROM UsageHistoryDB..ChargebackUsageDetails SurveyChargeback INNER
         JOIN cf_CommcellIdNameMap NameMap WITH (NOLOCK) ON 
         NameMap.id = SurveyChargeback.CommservUniqueId and SurveyChargeback.Type = %s WHERE 
         NameMap.CommServHostName = '%s' order by surveyChargeback.startDate desc""" % \
                (interval_type, self.commcell.webconsole_hostname)
        self.log.info("Executing the query: [%s] ", query)
        _date = self.db_connection.execute_sql(query, database_name="CVCloud")
        self.log.info("Query result:%s", _date[0][0])
        date_time_obj = datetime.strptime(_date[0][0], "%b %d, %Y, %H:%M:%S %p")
        date_db = date_time_obj.strftime("%Y-%m-%d") + " 00:00:00.0"
        # If today is '03/13/2020' this will return 2020-03-12 00:00:00.0' for Daily(4) type
        # If today is '03/13/2020' this will return 2020-03-02 00:00:00.0' for Weekly(2) type
        # If today is '03/13/2020' this will return 2020-02-01 00:00:00.0' for Monthly(1) type
        return date_db

    def get_startdate_string(self, interval_type):
        """
        Get expected date based on 'type',

        Args:
            interval_type (int): type should be selected from DAILY_TYPE, WEEKLY_TYPE
        MONTHLY_TYPE from declaration

        Returns (String): returns expected string  depending on type
        """
        #  if today is '2020-03-06 00:00:00.0', this should return '2020-03-05 00:00:00.0'
        if interval_type == int(4):  # return previous day date
            return str(date.today() - timedelta(1)) + " 00:00:00.0"

        #  if today is '2020-03-06 00:00:00.0', this should return '2020-02-01 00:00:00.0'
        if interval_type == int(1):  # return previous month date
            last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
            start_day_of_prev_month = date.today().replace(day=1) - timedelta(
                days=last_day_of_prev_month.day)
            return str(start_day_of_prev_month) + " 00:00:00.0"

        #  if today is '2020-03-06 00:00:00.0', this should return '2020-02-24 00:00:00.0'
        if interval_type == int(2):  # return previous week date
            today = date.today()
            return str(today - timedelta(days=today.weekday(), weeks=1)) + " 00:00:00.0"
        raise CVTestStepFailure("Invalid interval type is sent, Please select type from "
                                "DAILY_TYPE, WEEKLY_TYPE, MONTHLY_TYPE")

    @test_step
    def verify_table_content(self):
        """verify ChargebackUsageDetails contents updated to daily/monthly/weekly"""
        for each_type in [IntervalType.Daily, IntervalType.Weekly,
                          IntervalType.Monthly]:
            self.log.info("Verifying data for table ChargebackUsageDetails with [%s] type ",
                          each_type.name)

            # Read StartdDate column from table
            start_date_found = self.get_start_date_data(each_type.value)

            # form the string according to type
            start_date_expected = self.get_startdate_string(each_type.value)
            self.log.info("Expected startdt string %s", start_date_expected)

            # Verify expected startdt is equal to table's startdt
            if start_date_expected != start_date_found:
                raise CVTestStepFailure("expected [%s] startdate in table with [%s] type in table "
                                        "ChargebackUsageDetails ,but "
                                        "[%s] exists" % (start_date_expected, each_type.value,
                                                         start_date_found))
            self.log.info("Verified data for table with [%s] type", each_type.value)

    def verify_time_frame_value(self, time_frame, interval_type):
        """
        Verify exepted time frame value is present in webconsole chargeback report
        Args:
            interval_type(int): select 'Monthly/Weekly/Daily'
        """
        time_frame_expected = None
        start_date_string = self.get_startdate_string(interval_type)
        start_date_string = start_date_string.split()[0]
        datetime_obj = datetime.strptime(start_date_string, '%Y-%m-%d')
        if interval_type == IntervalType.Monthly.value:
            # 2020-03-13 should time_frame_expected 'Feb 2020'                  -- Previous month
            time_frame_expected = datetime_obj.strftime("%b %Y")
        elif interval_type == IntervalType.Weekly.value:
            # if today is 2020-03-13 should time_frame_expected 'Mar 02, 2020'  -- Previous Week
            time_frame_expected = datetime_obj.strftime("%b %d, %Y")
            time_frame = str(time_frame.split('-')[0]).strip()
        elif interval_type == IntervalType.Daily.value:
            # if today is 2020-03-13 should time_frame_expected 'Mar 12, 2020'  -- Previous day
            time_frame_expected = datetime_obj.strftime("%b %d, %Y")
        if time_frame != time_frame_expected:
            raise CVTestStepFailure("Expecting [%s] timeframe in chargeback report, found [%s]" %
                                    (time_frame_expected, time_frame))

    @test_step
    def verify_report_in_webconsole(self):
        """Verify latest monthly/weekly/daily data exists in webconsole report"""
        for each_type in [IntervalType.Daily, IntervalType.Weekly, IntervalType.Monthly]:
            self.chargeback.generate_report(group_by="Client Groups", time_interval=each_type.name)
            time_frame_value = self.chargeback.read_time_frame_value()
            self.verify_time_frame_value(time_frame_value, each_type.value)

    def run(self):
        try:
            self.utils.private_metrics_upload(enable_all_services=True)
            self.verify_table_content()
            self.init_webconsole()
            self.verify_report_in_webconsole()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
