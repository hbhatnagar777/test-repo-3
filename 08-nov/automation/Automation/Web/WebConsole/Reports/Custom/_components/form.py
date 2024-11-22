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
    CRComponentBuilder,
    CRComponentProperties,
    CRComponentViewer
)


class DateRangeBuilder(CRComponentBuilder):
    """Actions common to Date Range Builder goes here"""

    @property
    def category(self):
        """Returns: Category type as 'Form'."""
        return "Form"

    @property
    def name(self):
        """Returns: Name as 'Date Range'."""
        return "Date Range"

    @WebAction()
    def __drag_column_to_daterange(self, column_name):
        """Drag column to table"""
        self._drag_column_from_dataset(column_name, self._x + "//*[@class='dropMsg ng-scope']")

    @PageService()
    def add_column_from_dataset(self, column):
        """Add column from associated dataset to table

        Args:
            column (iterable): Any iterable of column name
        """
        self._validate_dataset_column(self.dataset_name, column)
        self.__drag_column_to_daterange(column)
        self._webconsole.wait_till_line_load()


class DateRangeViewer(CRComponentViewer):
    """Actions common to Date Range Viewer goes here"""

    @property
    def type(self):
        return ''

    @WebAction()
    def __click_date_range(self):
        """Clicks Date Range field/calender"""
        date_range = self._driver.find_element(By.XPATH, "//input[@type='daterange']")
        date_range.click()

    @WebAction()
    def __click_custom_drop_down_list(self, range_):
        """Clicks the given range"""
        range_ = self._driver.find_element(By.XPATH, f"//li[contains(.,'{range_}')]")
        range_.click()

    @WebAction()
    def __set_from_date(self, from_date):
        """Sets the from date"""
        from_ = self._driver.find_element(By.XPATH, "//input[@name='daterangepicker_start']")
        from_.clear()
        from_.send_keys(from_date)

    @WebAction()
    def __set_to_date(self, to_date):
        """Sets the to_ date"""
        to_ = self._driver.find_element(By.XPATH, "//input[@name='daterangepicker_end']")
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
        self._webconsole.wait_till_line_load()

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


class DateRangeProperties(CRComponentProperties):
    """Actions common to Date Range Properties go here"""

    def __init__(self, title):
        super().__init__(title)
        self.relative_row_count = 8

    @WebAction()
    def __click_add_button(self):
        """Clicks add button"""
        button = self._driver.find_element(By.XPATH, "//*[@title='Add Custom Range']")
        button.click()

    @WebAction()
    def __set_description(self, description):
        """Sets the given description"""
        text = self._driver.find_element(By.XPATH, 
            f"//*[@class='row ng-scope noLftRghtMargin'][{self.relative_row_count}]//div[@class='col-xs-7']//input")
        text.clear()
        text.send_keys(description)

    @WebAction()
    def __set_value(self, value):
        """Sets the given value"""
        text = self._driver.find_element(By.XPATH, 
            f"//*[@class='row ng-scope noLftRghtMargin'][{self.relative_row_count}]"
            f"//div[@class='col-xs-3 noLftRghtPadding']//input")
        text.clear()
        text.send_keys(value)

    @PageService()
    def add_custom_range(self, description, value):
        """Adds the custom Range

        Args:
            description (str): The description/ name of the new entry

            value (str):  Its corresponding value

        """
        self._select_current_component()
        self._click_general_tab()
        self.__click_add_button()
        self.__set_description(description)
        self.__set_value(value)
        self.relative_row_count += 1


class SearchBarBuilder(CRComponentBuilder):
    """Actions common to Search Bar Builder goes here"""
    @property
    def name(self):
        """Returns: Name as 'Search Bar'."""
        return "Search Bar"

    @property
    def category(self):
        """Returns: Category type as 'Form'."""
        return "Form"

    @WebAction()
    def __drag_column_to_search_bar(self, column):
        """Drag column to table"""
        self._drag_column_from_dataset(column, self._x + "//div[@data-ng-show='isFieldDragging']")

    @WebAction()
    def __drag_dataset_to_search_bar(self):
        """Drag dataset to table"""
        self._drag_dataset_to_component(self._x + "//div[@data-ng-show='isFieldDragging']")

    @PageService()
    def add_column_from_dataset(self, column=None):
        """Add column from associated dataset to table

        Args:
            column (iterable): Any iterable of column name
        """
        if column:
            self._validate_dataset_column(self.dataset_name, column)
            self.__drag_column_to_search_bar(column)
        else:
            self.__drag_dataset_to_search_bar()
        self._webconsole.wait_till_line_load()


class SearchBarViewer(CRComponentViewer):
    """Actions common to Search Bar Viewer goes here"""

    @property
    def type(self):
        return "SEARCH_BAR"

    @WebAction()
    def __set_keyword(self, keyword):
        """Sets search keyword"""
        search_field = self._driver.find_element(By.XPATH, self._x + "//*[contains(@class,'search-bar')]//input")
        search_field.clear()
        search_field.send_keys(keyword)
        search_field.send_keys(Keys.RETURN)
        self._webconsole.wait_till_line_load()

    @PageService()
    def search(self, keyword):
        """Searches for the given keyword in the components associated with the dataset same as it"""
        self.__set_keyword(keyword)
        self._webconsole.wait_till_load_complete()


class SearchBarProperties(CRComponentProperties):
    """Actions common to Search Bar Properties goes here"""
