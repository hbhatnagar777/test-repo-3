from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the navigating functions or operations that can be performed on the
"My Data" application on the WebConsole

Navigator is the only class defined in this file

Navigator:
    __init__()                 -- Initializes Navigator class object

    _click_computers()         -- Opens the computers Page from My data application

    _click_drive()             -- Opens the drive Page from My data application

    go_to_computers()          -- Navigates to the computers Page from My data application

    go_to_drive()              -- Navigates to the drive Page from My data application

"""
from Web.Common.page_object import WebAction, PageService


class Navigator:

    """
    This class holds the common navigation functionality for report app
    """

    def __init__(self, webconsole):
        """
        Args:
            webconsole (WebConsole): The webconsole object to use
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver

    @WebAction()
    def _click_computers(self):
        """
        Opens the computers [summary] Page from My data application
        """
        self._driver.find_element(By.XPATH, "//*[@id='fs']/a").click()

    @WebAction()
    def _click_drive(self):
        """
        Opens the drive Page from My data application
        """
        self._driver.find_element(By.XPATH, "//*[@id='drive']/a").click()

    @PageService()
    def go_to_computers(self):
        """
        Navigates to the computers [summary] Page from My data application
        """
        self._click_computers()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def go_to_drive(self):
        """
        Navigates to the drive Page from My data application
        """
        self._click_drive()
        self._webconsole.wait_till_load_complete()
