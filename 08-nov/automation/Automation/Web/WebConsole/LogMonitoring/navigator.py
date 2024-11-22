from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the navigating functions or operations that can be performed on the
log monitoring application on the WebConsole

Navigator is the only class defined in this file

Navigator:
    __init__()                 -- Initializes Navigator class object
    _click_homepage()          -- Opens the Log Monitoring Home Page
    _click_search()            -- Opens the Search tab from Log Monitoring Application
    _click_upload()            -- Opens the Upload tab from Log Monitoring Application
    _click_manage()            -- Opens the Manage tab from Log Monitoring Application
    _switch_frame()            -- Switches between multiple frames on the browser
    switch_frame()             -- Switches between multiple frames on the browser
    go_to_lm_homepage()        -- Navigates to the Log Monitoring Home Page
    go_to_manage()             -- Opens the Manage tab from Log Monitoring Application
    go_to_upload()             -- Opens the Upload tab from Log Monitoring Application
    go_to_search()             -- Opens the Search tab from Log Monitoring Application
"""
from Web.Common.page_object import WebAction, PageService


class Navigator(object):
    """
    Handles the navigation between the common tabs in log monitoring application
    """
    def __init__(self, webconsole):
        """Initializes Navigator class object"""
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver

    @WebAction()
    def _click_homepage(self):
        """
        Navigates to the Log Monitoring Home Page
        """
        self._driver.find_element(By.XPATH, r"//a[text() = 'Log Monitoring']").click()
        self._driver.refresh()

    @WebAction()
    def _click_search(self):
        """
        Opens the Search tab from Log Monitoring Application
        """
        self._driver.find_element(By.XPATH, 
            r"//li[@data-viewid = '1']//a[text() = 'Search']").click()

    @WebAction()
    def _click_upload(self):
        """
        Opens the Upload tab from Log Monitoring Application
        """
        self._driver.find_element(By.XPATH, 
            r"//li[@data-viewid = '2']//a[text() = 'Upload']").click()

    @WebAction()
    def _click_manage(self):
        """
        Opens the Manage tab from Log Monitoring Application

        """
        self._driver.find_element(By.XPATH, 
            r"/html/body/div[4]/div[2]/div/div[1]/div[2]/div/nav[1]/ul/li[5]/a").click()

    @WebAction(delay=5)
    def _switch_frame(self):
        """
        Switches between multiple frames on the browser
        """
        frame_id = self._driver.find_element(By.TAG_NAME, "iframe")
        self._driver.switch_to.frame(frame_id)

    @PageService()
    def switch_frame(self):
        """
        Switches between multiple frames on the browser
        """
        self._switch_frame()

    @PageService()
    def go_to_manage(self):
        """
        Opens the Manage tab from Log Monitoring Application
        """
        self._click_manage()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def go_to_lm_homepage(self):
        """
        Navigates to the Log Monitoring Home Page
        """
        self._click_homepage()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def go_to_search(self):
        """
        Opens the Search tab from Log Monitoring Application
        """
        self._click_search()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def go_to_upload(self):
        """
        Opens the Upload tab from Log Monitoring Application
        """
        self._click_upload()
        self._webconsole.wait_till_load_complete()
