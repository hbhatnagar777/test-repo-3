from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Module to work on Reports page of Metrics
"""
from time import sleep
from Web.WebConsole.Reports.report import Report
from Web.WebConsole.Reports.Metrics.components import MetricsTable
from Web.Common.exceptions import (
    CVWebAutomationException,
    CVWebNoData
)
from Web.Common.page_object import (
    WebAction,
    PageService
)


class MetricsReport(Report):
    """
    Report has interfaces to operate on various options in Metrics Report page
    """

    @property
    def report_type(self):
        """
        Returns:Report type as MetricsReport
        """
        return "MetricsReport"

    @WebAction()
    def _get_all_table_names(self):
        """
        Returns: table names
        """
        title_xp = "//span[@class='reportstabletitle']"
        return [table_name.text for table_name in self._driver.find_elements(By.XPATH, title_xp)]

    @WebAction()
    def _get_page_title(self):
        """ Get page title """
        return str(self._driver.find_element(By.XPATH, "//span[@id='surveyName']").text)

    @WebAction()
    def _select_company(self, company_name):
        """
        Select the company from the dropdown
        Args:
            company_name: Name of the company

        Returns:
            None
        """
        cmp_xpath = "//input[@id='tenantChooser']"
        select_cmp = self._driver.find_element(By.XPATH, cmp_xpath)
        select_cmp.clear()
        select_cmp.send_keys(company_name)
        sleep(2)
        xpath = f"//li[@class='ui-menu-item']/a[text()='{company_name}']"
        self._driver.find_element(By.XPATH, xpath).click()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def select_company(self, company_name):
        """
        Select the company from the dropdown
        Args:
            company_name(str): Name of the company

        Returns:
            None
        """
        self._select_company(company_name)

    @PageService()
    def get_tables(self):
        """Returns list of table objects visible in report"""
        return [MetricsTable(self._webconsole, each_table) for each_table in self._get_all_table_names()]

    @PageService()
    def get_table_names(self):
        """Returns all table names  in the report"""
        return self._get_all_table_names()

    @PageService()
    def get_table(self, table_name):
        """
        get access to table in metrics reports
        Args:
            table_name: table name
        Returns: table object
        """
        return MetricsTable(self._webconsole, table_name)

    @WebAction()
    def _get_no_data_error(self):
        """ Get chart error if exists"""
        chart_error_classes = ['chart-no-data', 'chartErrorMessage', 'no-data_Cloud',
                               'noDataErrorMsg', 'ngLabel', 'noChartDiv']
        for each_class in chart_error_classes:
            chart_error_message = self._webconsole.browser.driver.find_elements(By.CLASS_NAME, each_class)
            if chart_error_message:
                for each_obj in chart_error_message:
                    if each_obj.text:
                        return each_obj.text

    @PageService()
    def is_no_data_error_exists(self):
        """ Check if any chart error exists """
        if self._get_no_data_error() is not None:
            return True
        return False

    @PageService()
    def is_page_blank(self):
        """Check if Metrics report page is blank"""
        if not self._get_report_title():
            return True
        return False

    def verify_page_load(self):
        """Verify page is loading without any errors"""
        if self.is_no_data_error_exists():
            raise CVWebAutomationException("Page is not having data in link %s" %
                                           self._driver.current_url)
        if self.is_page_blank():
            raise CVWebAutomationException("Page is blank in link %s" %
                                           self._driver.current_url)
        notifications = self._webconsole.get_all_error_notifications()
        if notifications:
            raise CVWebAutomationException("[%s]Notification error found in link %s" %
                                           (notifications, self._driver.current_url))

    @WebAction()
    def _get_report_title(self):
        """ Check if merics page title exist"""
        ids = ['surveyName', 'sectionTitle', 'welcomeMsg']
        for each_id in ids:
            xpath = "//span[@id='%s']" % each_id
            page_title = self._driver.find_elements(By.XPATH, xpath)
            if page_title and page_title[0].text:
                return page_title[0].text
        return ''

    @PageService()
    def get_page_title(self):
        """ Get page title """
        return self._get_page_title()

    @PageService()
    def raise_for_no_data_error(self):
        """ raise error if any chart error exists """
        if self._get_no_data_error() is not None:
            raise CVWebNoData(
                self._driver.current_url
            )


class ExportedReport:
    """Modules related to exported file"""

    def __init__(self, browser):
        self._browser = browser
        self._driver = self._browser.driver

    @WebAction()
    def _get_page_title(self):
        """Get page title"""
        return str(self._driver.find_element(By.XPATH, "//span[@id='surveyName']").text)

    @PageService()
    def get_page_title(self):
        """Get page title"""
        return self._get_page_title()
