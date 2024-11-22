# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Hosts functions for validating the search operations.

Validation is the only class defined in this module.

Validation: Hosts the various validation methods.

Validation:

    close_search_tabs()         --  Closes all the search tabs.

    wait_to_load()              --  Checks if the required operation is completed.

    loading()                   --  Checks if the page is still loading.

    display_result()            --  Counts the number of items present.

    if_displayed()              --  Checks if an element with the given xpath is displayed.

    if_text_present_in_events() --  Checks if an element with this xpath is present under 'Events'

    wait_for_element()          --  Waits for the element to be visible.

"""
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils import logger
from dynamicindex.utils.constants import TWO_MINUTES, ONE_MINUTE
from ..common.locators import Locators
from ..common.locators import SearchPageLocators
from ..common.locators import MainPageLocators


class Validation(object):
    """Hosts validation methods."""

    def __init__(self, driver):
        """Initializes the instance attributes.

        Args:
           driver    (object)  --  An instance of WebDriver class.
        """
        self.logger = logger.get_log()
        self.driver = driver

    def close_search_tabs(self):
        """Closes all the search tabs."""
        try:
            self.logger.info("Trying to close all the open tabs.")
            if self.if_displayed(*MainPageLocators.ADVANCEDSEARCH_CLOSE_BUTTON):
                self.logger.info("Closing the advance search tab.")
                self.driver.find_element(*MainPageLocators.ADVANCEDSEARCH_CLOSE_BUTTON).click()
                
            while True:
                if self.if_displayed(*SearchPageLocators.SEARCHTAB2_CLOSE_BUTTON):
                    self.logger.info("Closing a tab.")
                    self.driver.find_element(*SearchPageLocators.SEARCHTAB2_CLOSE_BUTTON).click()
                else:
                    self.logger.info("Didn't find any tab to close.")
                    break

            while True:
                if self.if_displayed(*SearchPageLocators.SEARCHTAB_CLOSE_BUTTON):
                    self.logger.info("Closing a tab.")
                    self.driver.find_element(*SearchPageLocators.SEARCHTAB_CLOSE_BUTTON).click()
                else:
                    self.logger.info("Didn't find any tab to close.")
                    break
        except NoSuchElementException:
            self.logger.info("Couldn't locate xpath of search tab(s).")

    def wait_to_load(self):
        """Checks if the required operation is completed."""
        seconds = 0
        flag = 0
        waiting_list = [
            'Searching...',
            'Loading...',
            'Please wait...',
            'loading',
            "Retrieving...",
            'Adding',
            'Loading Jobs Data',
            'Closing...',
            'Deleting...']
        body_element = self.driver.find_element(*Locators.BODY_ELEMENT)
        while True:
            if seconds >= ONE_MINUTE:
                self.logger.info("Couldn't complete the requested operation.")
                break
            else:
                flag = 0
                for ele in waiting_list:
                    if ele in body_element.text:
                        flag = 1
                        self.logger.info("Waiting...")
                time.sleep(1)        
                seconds = seconds + 1    
                if flag == 0:
                    break

            if flag == 0:
                return

    def loading(self):
        """Checks if the page is still loading."""
        txt = "Loading..."
        seconds = 0
        if txt in self.driver.find_element(*Locators.BODY_ELEMENT).text:
            while True:
                if seconds >= TWO_MINUTES:
                    self.logger.info(
                        "Text %s is still present. Failing the test, the page is loading.", txt)
                    break
                time.sleep(1)
                seconds += 1

                if txt not in self.driver.find_element(*Locators.BODY_ELEMENT).text:
                    break
                if seconds % 10 == 0:
                    self.logger.info("Waiting for the page to finish loading.")

    def display_result(self, *xpath):
        """Counts the number of items displayed in the page.

        Args:
            xpath    (tuple)  --  XPath of the element.

        Example:
            display_result(*SearchPageLocators.DISPLAY_RESULT_ALL_TEXT)

        Returns:
            int  -  Returns the number of items displayed.
        """
        count_string = self.driver.find_element(*xpath).text
        self.logger.info("Text obtained from xpath- %s is %s", xpath[1], count_string)
        count_string = count_string.split()
        if count_string[0] == "Displaying":
            count = count_string[5]
            return int(count)
        return 0

    def if_displayed(self, *xpath):
        """Checks if an element with the given xpath is displayed.

        Args:
            xpath    (tuple)  --  XPath of the element.

        Returns:
            boolean  -  True if the element is displayed, False if it is not.
        """
        try:
            element = self.driver.find_element(*xpath)

            if element.is_displayed():
                return True
            return False

        except NoSuchElementException:
            return False

    def if_text_present_in_events(self, text):
        """Checks if an element with the given xpath is present under 'Events'.

        Args:
            text    (str)      --  Text to be located.

        Returns:
            boolean  -  Whether or not the text is present in the body.
        """
        self.driver.find_element(*MainPageLocators.EVENTS_BUTTON).click()
        body_element = self.driver.find_element(*Locators.BODY_ELEMENT)
        return bool(text in body_element.text)

    def wait_for_element(self, timeout, *xpath):
        """Waits for the element to be visible.

        Args:
            timeout    (int)    --  Number of seconds to wait.

            xpath      (tuple)  --  XPath of the element.

        """
        wait = WebDriverWait(self.driver, timeout)

        self.logger.info("Waiting for the element with xpath- %s to be displayed.", xpath[1])
        try:
            wait.until(EC.presence_of_element_located(xpath))
            self.logger.info("Done waiting.")
        except TimeoutException:
            self.logger.info(
                "Couldn't find element with xpath %s even after %d seconds.", xpath[1], timeout)
