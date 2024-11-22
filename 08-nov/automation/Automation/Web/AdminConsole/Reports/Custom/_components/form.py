from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All the operations common to Form component goes to this file."""
from selenium.webdriver.common.keys import Keys

from Web.Common.page_object import (
    WebAction,
    PageService
)

from .base import (
    CRComponentViewer
)


class DateRangeViewer(CRComponentViewer):
    """Actions common to Date Range Viewer goes here"""

    @property
    def type(self):
        return ''

    @WebAction()
    def __click_date_range(self):
        """Clicks Date Range field/calender"""
        date_range = self._driver.find_element(By.XPATH, "//div[@id='timeRangeDropdown']")
        date_range.click()

    @WebAction()
    def __click_custom_drop_down_list(self, range_):
        """Clicks the given range"""
        range_ = self._driver.find_element(By.XPATH, f"//li[contains(.,'{range_}')]")
        range_.click()

    @WebAction()
    def __set_from_date(self, from_date):
        """Sets the from date"""
        from_ = self._driver.find_element(By.XPATH,
                                          "//*[contains(@class, 'puoynj')]//button[@aria-label='Open calendar']")
        from_.click()
        from_.send_keys(from_date)

    @WebAction()
    def __set_to_date(self, to_date):
        """Sets the to_ date"""
        to_ = self._driver.find_element(By.XPATH,
                                        "//*[contains(@class, '6qkidq')]//button[@aria-label='Open calendar']")
        to_.clear()
        to_.send_keys(to_date)

    @PageService()
    def set_predefined_range(self, range_):
        """Sets the predefined Date Range

        Args:
            range_ (str) : The existing predefined date range in the drop down list

        """
        self.__click_date_range()
        self.__click_custom_drop_down_list(range_)
        self._adminconsole.wait_for_completion()

    @PageService()
    def set_custom_range(self, from_date, to_date):
        """Sets the custom Date Range

        Args:
            from_date (str): From date

            to_date: To date

        Examples:
                date_range.set_custom_range("Aug 23 2018", "Sep 03 2018")

        """
        self.set_predefined_range("Custom Range")
        self.__set_from_date(from_date)
        self.__set_to_date(to_date)


class SearchBarViewer(CRComponentViewer):
    """Actions common to Search Bar Viewer goes here"""

    @property
    def type(self):
        return "SEARCH_BAR"

    @WebAction()
    def __set_keyword(self, keyword):
        """Sets search keyword"""
        search_field = self._driver.find_element(By.XPATH, self._x + "//input")
        search_field.clear()
        search_field.send_keys(keyword)
        search_field.send_keys(Keys.RETURN)
        self._adminconsole.wait_for_completion()

    @PageService()
    def search(self, keyword):
        """Searches for the given keyword in the components associated with the dataset same as it"""
        self.__set_keyword(keyword)
        self._adminconsole.wait_for_completion()
