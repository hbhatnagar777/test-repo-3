# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
 Module to manage Metrics activity report.
"""

from Web.Common.page_object import (WebAction, PageService)


class MetricsActivity:

    """
    Activity report operation on metrics
    """
    def __init__(self, webconsole):
        """
                Args:
                     webconsole: WebConsole object
                """
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver

    @WebAction()
    def _click_last16_day_chart(self):
        """
        Click on last 16 days backup statistics bar chart
        """
        xpath = "//div[@id='summaryLast7DaysChartData']//*[name() ='text' and @fill='#006699']"
        days = self._driver.find_elements(By.XPATH, xpath)
        days[0].click()

    @WebAction()
    def _click_last12_month(self):
        """
        click on last 12 months backup stattistics
        """
        xpath = "//div[@id='summaryLast6MonthsChartData51']//*[name() ='text' and @fill='#006699']"
        month = self._driver.find_elements(By.XPATH, xpath)
        month[0].click()

    @WebAction()
    def _click_day_daily_backup(self, date):
        """
        Click on daily backup jobs report
        Args:
            date(INT): current day

        Returns:
            None
        """
        xpath = "//div[@id='barchartcontainer']//*[name() ='text' and @fill='#006699']"
        day = self._driver.find_elements(By.XPATH, xpath)
        for each_day in day:
            if each_day.text == date:
                each_day.click()
                break

    @WebAction()
    def _click_time_hourly(self, hour):
        """
        Click latest time from hourly backup jobs
        Args:
            hour(INT): current hour

        Returns:
            None
        """
        hpath = "//div[@id='barchartcontainer']//*[name() ='text' and @fill='#006699']"
        time = self._driver.find_elements(By.XPATH, hpath)
        for each_time in time:
            if each_time.text == hour:
                each_time.click()
                break

    @PageService()
    def access_last_12_months_chart(self):
        """
        Click on last 12 months chart
        """
        self._click_last12_month()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_daily_details(self, date):
        """
        Click on daily backup jobs report
        Args:
            date(INT): current day

        Returns:
            None
        """
        self._click_day_daily_backup(date)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_last16_day_chart(self):
        """
        Click on last 16 days backup statistics bar chart.
        Args:
            date(INT): current day

        Returns:
            None
        """
        self._click_last16_day_chart()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_hourly_details(self, hour):
        """
            Click latest time from hourly backup jobs
        Args:
            hour (INT): current hour

        Returns:
            None
        """
        self._click_time_hourly(hour)
        self._webconsole.wait_till_load_complete()
