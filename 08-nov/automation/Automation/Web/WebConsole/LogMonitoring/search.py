from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the search page on the
log monitoring application in WebConsole

Search is the only class defined in this file

Search:
    __init__()                -- Initializes the search class object
    _enter_search_string()    -- Sends input to the search bar for the data indexed
    _read_search_results()    -- Reads the log lines returned on the search page
    _click_save_search()      -- clicks on the option to favorite a search
    _click_save_button()      -- Clicks on the save button to save the search
    _set_search_name()        -- Sets the search name
    make_search()             -- Makes a Search on the data in Log Monitoring Application
    get_log_lines_count()     -- Gets the count of log lines in the search page
    save_search()             -- Saves a search explicitly

"""
from AutomationUtils import logger
from selenium.webdriver.common.keys import Keys
from Web.Common.page_object import WebAction, PageService
from Web.WebConsole.LogMonitoring.navigator import Navigator


class Search(object):
    """
    Handles the operations on Log Monitoring
    """

    def __init__(self, webconsole):
        """Initializes Search class object"""
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()
        self._nav = Navigator(self._webconsole)

    @WebAction()
    def _enter_search_string(self, input_string):
        """
        Sends input to the search bar for the data indexed

        Args:
             input_string : the string to be searched for the given policy in webconsole

        Example:
            ("monitoring")
        """
        search = self._driver.find_element(By.ID, "keyword")
        search.clear()
        search.send_keys(input_string)
        search.send_keys(Keys.ENTER)

    @WebAction()
    def _read_search_results(self):
        """
        Reads the log lines returned on the search page after making a search
        """
        log_lines = self._driver.find_elements(By.XPATH, 
            r"//table[@id = 'globalSearchResultsTable']/tbody/tr")
        return log_lines

    @WebAction(delay=5)
    def _click_save_search(self):
        """
        clicks on the option to favorite a search
        """
        self._driver.find_element(By.XPATH, 
            r"//span[@class = 'halflings halflings-star-empty']").click()

    @WebAction()
    def _click_save_button(self):
        """Clicks on the save button to save the search"""
        self._driver.find_element(By.ID, "okButton").click()

    @WebAction()
    def _set_search_name(self, search_name):
        """
        Sets the search name
        Args:
            search_name: search name to be set
        """
        search_input = self._driver.find_element(By.XPATH, r"//input[@id = 'title']")
        search_input.clear()
        search_input.send_keys(search_name)

    @PageService()
    def make_search(self, input_string):
        """
        Makes a Search on the data in Log Monitoring Application

        Args:
            input_string : the string to be searched for the given policy in webconsole

        Example:
            ("monitoring")
        """
        self._enter_search_string(input_string)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_log_lines_count(self):
        """
        Gets the count of log lines in the search page

        raises:
            Exception:
                    if failed to get the number of log lines on the search page
        """
        log_lines = self._read_search_results()
        count_log_lines = len(log_lines)
        if count_log_lines == 1:
            for log_line in log_lines:
                self._log.info(log_line.text)
                if log_line.text == 'No data found':
                    count_log_lines = 0
        self._log.info("The count of log lines is: %d", count_log_lines)

        return count_log_lines

    @PageService()
    def save_search(self, search_name):
        """
        Saves a search explicitly

        Args:
            search_name: search name for the search to be saved

        Example:
            ("search1")
        """
        self._click_save_search()
        self._webconsole.wait_till_load_complete()
        self._nav.switch_frame()
        self._set_search_name(search_name)
        self._webconsole.wait_till_load_complete()
        self._click_save_button()
        self._driver.switch_to.default_content()
        self._webconsole.wait_till_load_complete()
