from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All opereations on localization goes in this file."""
from Web.Common.page_object import (
    WebAction,
    PageService
)


class Localization:
    """Base class for operations on localization"""

    def __init__(self):
        self.__webconsole = None
        self.__browser = None
        self.__driver = None

    @property
    def _driver(self):
        if self.__driver is None:
            raise ValueError(
                "Dataset not initialized, was Builder.add_dataset called ?"
            )
        return self.__driver

    @WebAction()
    def __click_add_button(self):
        """Clicks add button under localization popup"""
        add = self._driver.find_element(By.XPATH, "//a[contains(., 'Add')]")
        add.click()

    @WebAction()
    def __click_done_button(self):
        """Clicks done button under localization popup"""
        done = self._driver.find_element(By.XPATH, "//a[contains(.,'Done')]")
        done.click()

    @WebAction()
    def __get_new_row_position(self):
        """returns the new row position"""
        rows = self._driver.find_elements(By.XPATH, "//div[@class='row movableRow ng-scope']")
        return len(rows)

    @WebAction()
    def __set_locale(self, position, text):
        """Sets the given text under 'Locale' column"""
        input_ = self._driver.find_element(By.XPATH, 
            "//div[@class='row movableRow ng-scope'][%s]//input[@data-ng-model='row.locale']" % position)
        input_.clear()
        input_.send_keys(text)

    @WebAction()
    def __set_key(self, position, text):
        """Sets the given text under 'Key' column"""
        input_ = self._driver.find_element(By.XPATH, 
            "//div[@class='row movableRow ng-scope'][%s]//input[@data-ng-model='row.localeKey']" % position)
        input_.clear()
        input_.send_keys(text)

    @WebAction()
    def __set_value(self, position, text):
        """Sets the given text under 'Value' column"""
        input_ = self._driver.find_element(By.XPATH, 
            "//div[@class='row movableRow ng-scope'][%s]//input[@data-ng-model='row.localeValue']" % position)
        input_.clear()
        input_.send_keys(text)

    @PageService()
    def configure_localization(self, webconsole):
        """Configures localization

        DO NOT call this method directly.
        It is invoked by the report builder when required.
        """
        self.__webconsole = webconsole
        self.__browser = webconsole.browser
        self.__driver = webconsole.browser.driver

    @PageService()
    def add_localization(self, locale, key, value):
        """Adds new entry in to the localization"""
        self.__click_add_button()
        position = self.__get_new_row_position()
        self.__set_locale(position, locale)
        self.__set_key(position, key)
        self.__set_value(position, value)

    @PageService()
    def save_localization(self):
        """Saves the localization changes"""
        self.__click_done_button()
