from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Module has all the features which are present in any report page"""

from abc import ABC, abstractmethod
from time import sleep

from AutomationUtils import config
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.WebConsole.Reports.cte import ConfigureSchedules, ExportHandler, EmailNow
from Web.WebConsole.webconsole import WebConsole

_CONFIG = config.get_config()


class FileMenu:
    """
    FileMenu on access option on file menu present on Reports page
    """

    def __init__(self, webconsole: WebConsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole

    @WebAction()
    def click_file_menu(self):
        """
        opens the file menu
        """
        self._driver.find_element(By.XPATH, ".//*[@id='reportButton']").click()

    @WebAction()
    def click_email_now(self):
        """
        clicks the email now option in file menu
        """
        self._driver.find_element(By.ID, "exportEmail").click()

    @WebAction()
    def click_schedule(self):
        """
        clicks the schedule option in file menu
        """
        self._driver.find_element(By.ID, "exportSchedule").click()

    @WebAction()
    def click_security(self):
        """
        clicks the security option in file menu
        """
        self._driver.find_element(By.ID, 'securityButton').click()

    @WebAction()
    def _get_file_menu_objects(self):
        """
        Get file menu objects
        """
        menu_option_xp = "//ul[@id='reportMenu']//span[not(contains(@class, 'imageSpan'))]"
        return self._driver.find_elements(By.XPATH, menu_option_xp)

    @PageService()
    def get_file_options(self):
        """
        function to get list of options available under File button for the report
        :returns list of file menu options available
        """
        self.click_file_menu()
        return [menu_obj.text for menu_obj in self._get_file_menu_objects()]


class Report(ABC):
    """
    Report has interfaces to operate on various options in Metrics Report page
    """

    def __init__(self, webconsole: WebConsole):
        self._webconsole = webconsole
        self._driver = self._webconsole.browser.driver
        self._file = FileMenu(webconsole)

    @property
    @abstractmethod
    def report_type(self):
        """
        Returns: metrics/custom on the implementation
        """
        raise NotImplementedError

    @PageService()
    def export_handler(self):
        """
        Returns: export object
        """
        return ExportHandler(self._webconsole)

    @PageService()
    def get_file_menu_list(self):
        """
        Returns: list of file menu options available
        """
        self._file.get_file_options()

    @PageService()
    def open_email_now(self):
        """Opens email now panel

        Returns:email now object

        """
        self._file.click_file_menu()
        self._file.click_email_now()
        sleep(2)
        return EmailNow(self._webconsole)

    @PageService()
    def open_schedule(self):
        """Opens Schedule panel

        Returns:Schedule object

        """
        self._file.click_file_menu()
        self._file.click_schedule()
        sleep(2)
        return ConfigureSchedules(self._webconsole)

    @WebAction()
    def _click_update_report_settings(self):
        """ Click Update report settings"""
        self._driver.find_element(By.XPATH, "//*[@id='saveScheduleEdit']").click()

    @WebAction()
    def _click_cancel_update(self):
        """ Click cancel report settings"""
        self._driver.find_element(By.XPATH, "//*[@id='cancelScheduleEdit']").click()

    @PageService()
    def update_report_settings(self):
        """Update report settings for schedule"""
        self._click_update_report_settings()
        self._driver.switch_to.window(self._driver.current_window_handle)
        sleep(3)

    @PageService()
    def cancel_report_update(self):
        """Leaves the update report settings screen"""
        self._click_cancel_update()
        self._driver.switch_to.window(self._driver.current_window_handle)
        sleep(3)
