from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the Manage page on the
 log monitoring application in WebConsole

Manage is the only class defined in this file

Manage:
    __init__()              -- Initializes Manage class object
    _click_schedules()      -- Opens the Schedules list from the Manage dropdown
    _is_exists_schedule()   -- Checks if given schedule name exists on the LM Schedules list
    _click_alerts()         -- Opens the Alerts list from the Manage dropdown
    _is_exists_alert()      -- Checks if given alert name exists on the LM Alerts list
    click_schedules()       -- Opens the Schedules list from the Manage dropdown
    is_exists_schedule()    -- Checks if given schedule name exists on the LM Schedules list
    click_alerts()          -- Opens the Alerts list from the Manage dropdown
    is_exists_alert()       -- Checks if given alert name exists on the LM Alerts list
"""
from Web.Common.page_object import WebAction, PageService
from Web.WebConsole.LogMonitoring.navigator import Navigator
from selenium.common.exceptions import NoSuchElementException


class Manage(object):
    """
    Handles the operations in Manage dropdown of Log Monitoring application
    """
    def __init__(self, webconsole):
        """Initializes Manage class object"""
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self._nav = Navigator(self._webconsole)

    @WebAction()
    def _click_schedules(self):
        """
        Opens the Schedules list from the Manage dropdown in Log Monitoring Application
        """
        self._driver.find_element(By.XPATH, r"//span[text() = 'Schedules']").click()

    @WebAction()
    def _is_exists_schedule(self, schedule_name):
        """
        Checks if given schedule name exists on the LM Schedules list

        Args:
            schedule_name: schedule name for the search to be verified

        Example:
            ("schedule1")

        Raises:
            Exception:
                if failed to validate schedule name on LM Schedules list
        """
        try:
            if self._driver.find_element(By.XPATH, "//span[text()='"+schedule_name+"']"):
                return True
        except NoSuchElementException:
            return False

    @WebAction()
    def _click_alerts(self):
        """
        Opens the Alerts list from the Manage dropdown in Log Monitoring Application
        """
        self._driver.find_element(By.XPATH, r"//span[text() = 'Alerts']").click()

    @WebAction()
    def _is_exists_alert(self, alert_name):
        """
        Checks if given alert name exists on the LM Alerts list

        Args:
            alert_name: alert name for the search to be verified

        Example:
            ("alert1")

        Raises:
            Exception:
                if failed to validate alert name on LM Alerts list
        """
        try:
            if self._driver.find_element(By.XPATH, "//span[text()='" + alert_name + "']"):
                return True
        except NoSuchElementException:
            return False

    @PageService()
    def click_alerts(self):
        """
        Opens the Alerts list from the Manage dropdown in Log Monitoring Application
        """
        self._nav.go_to_manage()
        self._click_alerts()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def is_exists_alert(self, alert_name):
        """
        Checks if given alert name exists on the LM Alerts list

        Args:
            alert_name: alert name for the search to be verified

        Example:
            ("alert1")

        Raises:
            Exception:
                if failed to validate alert name on LM Alerts list
        """
        return self._is_exists_alert(alert_name)

    @PageService()
    def click_schedules(self):
        """
        Opens the Schedules list from the Manage dropdown in Log Monitoring Application
        """
        self._nav.go_to_manage()
        self._click_schedules()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def is_exists_schedule(self, schedule_name):
        """
        Checks if given schedule name exists on the LM Schedules list

        Args:
            schedule_name: schedule name for the search to be verified

        Example:
            ("schedule1")

        Raises:
            Exception:
                if failed to validate schedule name on LM Schedules list
        """
        return self._is_exists_schedule(schedule_name)
