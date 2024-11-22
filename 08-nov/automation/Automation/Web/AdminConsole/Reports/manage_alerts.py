# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
admin console alerts page
"""

from Web.AdminConsole.Reports.cte import CommonFeatures
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from Web.Common.page_object import (
    PageService,
    WebAction
)


class ManageAlerts(CommonFeatures):
    """Class for managing report's alerts"""

    @WebAction()
    def _select_alert_containing(self, alert_string):
        """
        Return all alerts containing string
        Args:
            alert_string                   (String)       --      String present in alert name
        """
        alerts = self._driver.find_elements(By.XPATH, 
            "//td//a[contains(text(), '" + alert_string + "')]")
        if not alerts:
            raise NoSuchElementException("No alerts are found with name containing [%s]" %
                                         alert_string)
        return [alert.text for alert in alerts]

    @PageService()
    def enable_alerts(self, alerts):
        """
        Enable alerts
        Args:
            alerts              (list)     -- List of alerts
        """
        self.enable_entity(alerts)
        self._admin_console.wait_for_completion()

    @PageService()
    def disable_alerts(self, alerts):
        """
        Disable alerts
        Args:
            alerts              (list)     -- List of alerts
        """
        self.disable_entity(alerts)
        self._admin_console.wait_for_completion()

    @PageService()
    def edit_alert(self, alert_name):
        """
        edit the alert from manager page
        Args:
            alert_name (String): Name of the alert
        """
        self.table.access_link(alert_name)
        self.edit_entity(page_level=True)
        self._admin_console.wait_for_completion()

    @PageService()
    def run_alerts(self, alerts):
        """
        run alerts
        Args:
            alerts              (list)     -- List of alerts
        """
        self.run_entity(alerts)
        self._admin_console.wait_for_completion()

    @PageService()
    def delete_alerts(self, alerts):
        """
        Delete alerts
        Args:
            alerts              (list)     -- List of alerts
        """
        self.delete_entity(alerts)
        self._admin_console.wait_for_completion()
        
    @PageService()
    def get_all_alerts(self, column_name):
        """Fetches the list of all alerts"""
        return self.table.get_column_data(column_name, fetch_all=True)

    @PageService()
    def cleanup_alerts(self, alert_string):
        """
        delete alerts containing a specific string in alert name

        Args:
            alert_string                   (string)      --     alert name to be selected

        """
        try:
            alerts = self._select_alert_containing(alert_string)
        except NoSuchElementException:
            return
        self.delete_entity(alerts)
        self._admin_console.wait_for_completion()


class TestCriteriaHealthTable:
    """ This class can be used to get details of table content
    present in test criteria table for health tiles alert. """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.driver

    @WebAction()
    def _get_column_names(self):
        """Returns column names in table"""
        return [column.text for column in self._driver.find_elements(By.XPATH, "//div[@class='item-title']")]

    @WebAction()
    def _get_rows_count(self):
        """Returns rows count"""
        return len(self._driver.find_elements(By.XPATH, "//div[@class='item-title']")) - 1

    @WebAction()
    def _get_row_data(self):
        """Reads the row data"""
        row_xp = "//div[contains(@class, 'item-content')]/label"
        return [cellvalue.text for cellvalue in self._driver.find_elements(By.XPATH, row_xp)]

    @PageService()
    def get_alert_table_data(self):
        """
        Reads whole table for all the columns
        :return: list fo rows(list of list)
        """
        rowcount = self._get_rows_count()
        table_data = []
        for row_idx in range(1, int(rowcount) + 1):
            table_data.append(self._get_row_data()[row_idx])
        return table_data

