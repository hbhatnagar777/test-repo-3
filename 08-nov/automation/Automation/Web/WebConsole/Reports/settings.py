from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Operation on settings page such as access/disable/enable the report
ReportSettings:

     access_report           --  Access specified report

     get_retention_value     --  Get the retention value of report

     set_report_status       --  set report status

     set_retention           --  Set retention for the report
"""

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)


class ReportSettings:
    """ Operation on settings page such as access/disable/enable the report """
    class ReportStatus:
        """
        Report status constants
        """
        REPORT_ENABLED = 'Enabled'
        REPORT_DISABLED = 'Disabled'

    def __init__(self, webconsole: WebConsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole
        self.report = MetricsReport(self._webconsole)

    @WebAction()
    def _click_edit(self):
        """
        click on edit
        """
        self._driver.find_element(By.XPATH, "//span[@class='actionLinks edit sprite "
                                           "icon-edit']").click()

    @WebAction()
    def _click_filter(self):
        """Click on filter"""
        self._driver.find_element(By.XPATH, "//input[@id='reportdiv_FilterButton']").click()

    @WebAction()
    def _set_retention(self, retention):
        """
        set retention
        """
        xpath = "//*[@id = 'reportdiv_table_wrapper']//input[@id='retention']"
        self._driver.find_element(By.XPATH, xpath).clear()
        self._driver.find_element(By.XPATH, xpath).send_keys(retention)

    @WebAction()
    def _click_report(self, report):
        """
        Click on report
        Args:
            report                (String)     --      Report name
        """
        self._driver.find_element(By.XPATH, "//*[@data-label='Report Name']"
                                           "/a[text()='%s']" % report).click()

    @WebAction()
    def _click_save(self, report_name):
        """Click save"""
        xpath = "//*[@title='%s']/..//span[@class='save sprite icon-save']" % report_name
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _mouse_hover_report(self, report_name):
        """
        Mouse hovers over the specified report
        """
        xpath = "//tbody[@role='alert']//*[@title='%s' and @data-label='Report Name']" % report_name
        report = self._driver.find_element(By.XPATH, xpath)
        hover = ActionChains(self._driver).move_to_element(report)
        hover.perform()

    @PageService()
    def access_report(self, report):
        """
        Access report
        Args:
            report              (String)           --     Report name
        """
        table = self.report.get_tables()[0]
        table.enable_filter()
        table.set_filter('Report Name', report)
        self._click_report(report)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_retention_value(self, report_name):
        """
                Get retention value for specified report
        Args:
            report_name                  (String)           --    Report name
        Returns                          (String)           --    Retention value
        """
        table = self.report.get_tables()[0]
        table.enable_filter()
        table.set_filter('Report Name', report_name)
        retentiontion_value = table.get_data_from_column("Retention")[0]
        if not retentiontion_value:
            raise CVWebAutomationException("[%s] report is not found in report settings "
                                           "page" % report_name)
        return retentiontion_value

    @PageService()
    def set_retention(self, report_name, retention_value):
        """
            Set retention value
        Args:
            report_name                    (String)     --   Report name
            retention_value                (String)     --   Set retention value
        """
        table = self.report.get_tables()[0]
        table.enable_filter()
        table.set_filter('Report Name', report_name)
        self._mouse_hover_report(report_name)
        self._click_edit()
        self._set_retention(retention_value)
        self._click_save(report_name)

    @PageService()
    def set_report_status(self, report_name, status=ReportStatus.REPORT_ENABLED):
        """
        Set report status enabled/disabled
        Args:
            status                     (String)    --     Set report status
            report_name                (String)    --     report name
        """
        table = self.report.get_tables()[0]
        table.enable_filter()
        table.set_filter('Report Name', report_name)
        self._mouse_hover_report(report_name)
        self._click_edit()
        select = Select(self._driver.find_element(By.ID, 'status'))
        select.select_by_visible_text(status)
        self._click_save(report_name)

    @PageService()
    def get_report_status(self, report_name):
        """
        Set report status enabled/disabled
        Args:
            report_name                (String)    --     report name
        """
        table = self.report.get_tables()[0]
        table.enable_filter()
        table.set_filter('Report Name', report_name)
        return table.get_data_from_column("Status")[0]
