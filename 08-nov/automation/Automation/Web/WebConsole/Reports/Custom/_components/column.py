from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All the operations common to column component goes to this file."""

from selenium.webdriver.support.ui import Select

from Web.Common.page_object import WebAction, PageService
from .base import (
    CRComponentBuilder,
    CRComponentViewer,
    CRComponentProperties
)


class ColumnBuilder(CRComponentBuilder):
    """Actions common to Column Properties  go here"""
    @property
    def category(self):
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError


class ColumnViewer(CRComponentViewer):
    """Actions common to Column Properties  go here"""

    @property
    def type(self):
        return ''

    @WebAction()
    def __click_hyperlink(self, hyperlink):
        """Clicks hyperlink on a particular cell"""
        link = self._driver.find_element(By.XPATH, 
            f"{self._x.rsplit('//', 1)[0]}//td[@data-label='{self.id}']/.."
            f"//*[text()='{hyperlink}']")
        link.click()

    @PageService()
    def open_hyperlink_on_cell(self, hyperlink, open_in_new_tab=False):
        """Opens Hyperlink on a cell"""
        self.__click_hyperlink(hyperlink)
        if open_in_new_tab:
            self._driver.switch_to.window(self._driver.window_handles[-1])
        self._webconsole.wait_till_load_complete()


class ColumnProperties(CRComponentProperties):
    """Actions common to Column Properties  go here"""

    @WebAction()
    def __click_formatter(self):
        """Click formatter"""
        formatter = self._driver.find_element(By.XPATH, "//*[@title='Formatter']/..//span[@class='pull-right']")
        formatter.click()

    @WebAction()
    def __select_formatter_type(self, type_):
        """Selects the formatter type from the drop down"""
        drop_down = self._driver.find_element(By.XPATH, "//select[@id ='inputFormatType']")
        Select(drop_down).select_by_value(type_)

    @WebAction()
    def __click_apply(self):
        """Clicks Apply button on the formatter options window."""
        apply = self._driver.find_element(By.XPATH, 
            "//*[@data-ng-if='formatterOptions']//button[contains(text(),'Apply')]"
        )
        apply.click()

    @WebAction()
    def __click_column(self):
        """Clicks the column title."""
        column = self._driver.find_element(By.XPATH, self._x)
        column.click()

    @WebAction()
    def __enter_style(self, script):
        """Enters the code snippet for style into the text area. """
        column = self._driver.find_element(By.XPATH, "//*[label[contains(.,'Custom Styles')]]/..//textarea")
        column.clear()
        column.send_keys(script)

    @WebAction()
    def __select_link_type(self, link):
        """Selects the link type from the drop down"""
        drop_down = self._driver.find_element(By.XPATH, 
            "//*[@data-ng-if='formatterOptions']//*[@title='onClick']/following-sibling::*//select")
        Select(drop_down).select_by_visible_text(link)

    @WebAction()
    def __select_wf(self, wf_name):
        """Selects the link type from the drop down"""
        drop_down = self._driver.find_element(By.XPATH, 
            "//*[@data-ng-if='formatterOptions']//*[@title='eventModel.action']/following-sibling::*//select")
        Select(drop_down).select_by_visible_text(wf_name)

    @WebAction()
    def __set_url(self, url):
        """Sets URL in link formatter"""
        textbox = self._driver.find_element(By.XPATH, 
            "//*[@*='formatterOptions']//*[contains(text(),'URL')]/..//input")
        textbox.clear()
        textbox.send_keys(url)

    @WebAction()
    def __set_source(self, size):
        """Selects the source size from the drop down"""
        drop_down = self._driver.find_element(By.XPATH, 
            "//*[contains(@data-ng-show,'size')]//*[contains(text(),'Source')]/following-sibling::*//select")
        Select(drop_down).select_by_value(size)

    @WebAction()
    def __set_target(self, size):
        """Selects the target size from the drop down"""
        drop_down = self._driver.find_element(By.XPATH, 
            "//*[contains(@data-ng-show,'size')]//*[contains(text(),'Target')]/following-sibling::*//select")
        Select(drop_down).select_by_value(size)

    @WebAction()
    def __set_precision(self, precision):
        """Sets precision for the size formatter"""
        textbox = self._driver.find_element(By.XPATH, 
            "//*[contains(@data-ng-show,'size')]//*[contains(text(),'Precision')]/following-sibling::*//input")
        textbox.clear()
        textbox.send_keys(precision)

    @WebAction()
    def __set_number_format(self, format_):
        """Selects the number format"""
        drop_down = self._driver.find_element(By.XPATH, 
            "//*[contains(@data-ng-show,'number')]//*[contains(text(),'Format')]/following-sibling::*//select")
        select = Select(drop_down)
        select.select_by_value(format_)

    @WebAction()
    def __set_timezone(self, zone):
        """Selects the time zone"""
        drop_down = self._driver.find_element(By.XPATH, 
            "//*[contains(@data-ng-show,'date')]//*[contains(text(),'Zone')]/following-sibling::*//select")
        select = Select(drop_down)
        select.select_by_visible_text(zone)

    @WebAction()
    def __set_time_input_format(self, format_):
        """Selects the time input format"""
        drop_down = self._driver.find_element(By.XPATH, 
            "//*[contains(@data-ng-show,'date')]//*[contains(text(),'Input Format')]/following-sibling::*//select")
        select = Select(drop_down)
        select.select_by_value(format_)

    @WebAction()
    def __set_time_output_format(self, format_):
        """Selects the time output format"""
        drop_down = self._driver.find_element(By.XPATH, 
            "//*[contains(@data-ng-show,'date')]//*[contains(text(),'Output Format')]/following-sibling::*//select")
        select = Select(drop_down)
        select.select_by_value(format_)

    @WebAction()
    def __set_column_name(self, name):
        """Types the given input to the display name"""
        display_name = self._driver.find_element(By.XPATH, "//*[@title='DisplayName']/..//input")
        display_name.clear()
        display_name.send_keys(name)

    @WebAction()
    def __select_aggregation_drop_down(self, aggregation):
        """Selects the aggregation dropdown"""
        drop_down = self._driver.find_element(By.XPATH, "//*[@title='Aggregate']/..//select")
        select = Select(drop_down)
        select.select_by_value(aggregation)

    @WebAction()
    def _get_toggle_state(self):
        """Gets the Wrap Text toggle button state """
        state = self._driver.find_element(By.XPATH, "//*[contains(@id,'wraptext')]")
        return True if "ng-not-empty" in state.get_attribute('class') else False

    @WebAction()
    def __toggle_wrap_text(self):
        """Toggles the wrap text slider"""
        toggle = self._driver.find_element(By.XPATH, 
            "//*[contains(@for,'wraptext')]//*[contains(@class,'on-off-switch-switch')]")
        toggle.click()

    @WebAction()
    def __select_hidden_drop_down(self, value):
        """Selects the Hidden Dropdown"""
        drop_down = self._driver.find_element(By.XPATH, "//*[@title='Hidden']/..//select")
        select = Select(drop_down)
        select.select_by_visible_text(value)

    @WebAction()
    def __set_column_width(self, width):
        """Types the given width"""
        input_field = self._driver.find_element(By.XPATH, "//*[@title='Width']/..//input")
        input_field.send_keys(width)

    @WebAction()
    def __exclude_column(self):
        """Toggles the exclude from CSV slider"""
        toggle = self._driver.find_element(By.XPATH, 
            "//*[contains(@for,'exclude')]//*[contains(@class,'on-off-switch-switch')]")
        toggle.click()

    @WebAction()
    def __open_url_in_new_tab(self):
        """Toggles new tab under URL link formatter"""
        toggle = self._driver.find_element(By.XPATH, 
            "//*[@*='formatterOptions']//*[@title='Open in new tab']/..//span[2]")
        toggle.click()

    @WebAction()
    def __set_duration_unit(self, source_duration):
        """Sets the source input for duration"""
        drop_down = self._driver.find_element(By.XPATH, 
            "//*[contains(@data-ng-show,'duration')]//*[contains(text(),'Source')]/following-sibling::*//select")
        select = Select(drop_down)
        select.select_by_value(source_duration)

    @PageService()
    def format_as_custom(self, script):
        """Sets custom scripts for the invoked column object

        Args:
            script (str):  script which is to be applied.

        """
        self._select_current_component()
        self._click_general_tab()
        self.__click_formatter()
        self.__select_formatter_type("custom")
        self._click_add_expression()
        self._set_code_editor(script)
        self._click_save_on_code_editor()
        self.__click_apply()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def format_as_url_link(self, url, new_tab=True):
        """Sets custom scripts for the invoked column object

        Args:
            url (str):  link which which is to be applied.

            new_tab (bool): opens URL in new tab

        """
        self._select_current_component()
        self._click_general_tab()
        self.__click_formatter()
        self.__select_formatter_type("link")
        self.__select_link_type("Url")
        self.__set_url(url)
        if new_tab:
            self.__open_url_in_new_tab()
        self.__click_apply()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def format_as_link_wf(self, wf_name):
        """Sets workflow for the invoked column object

        Args:
            wf_name (str):  name of the workflow

        """
        self._select_current_component()
        self._click_general_tab()
        self.__click_formatter()
        self.__select_formatter_type("link")
        self.__select_link_type("Run a workflow")
        self.__select_wf(wf_name)
        self.__click_apply()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def format_as_size(self, source, target, precision):
        """Sets format by size for the invoked column object

        Args:
            source      (str): Source format size

            target      (str): Target format size

            precision   (int): Precision
        """
        self._select_current_component()
        self._click_general_tab()
        self.__click_formatter()
        self.__select_formatter_type("size")
        self.__set_source(source)
        self.__set_target(target)
        self.__set_precision(precision)
        self.__click_apply()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def format_as_number(self, type_):
        """Sets the number format of the given type"""
        self._select_current_component()
        self._click_general_tab()
        self.__click_formatter()
        self.__select_formatter_type("number")
        self.__set_number_format(type_)
        self.__click_apply()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def format_as_date(self, timezone, input_format, output_format):
        """Sets the number format of the given type"""
        self._select_current_component()
        self._click_general_tab()
        self.__click_formatter()
        self.__select_formatter_type("date")
        self.__set_timezone(timezone)
        self.__set_time_input_format(input_format)
        self.__set_time_output_format(output_format)
        self.__click_apply()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def format_as_boolean(self):
        """Sets the format as boolean"""
        self._select_current_component()
        self._click_general_tab()
        self.__click_formatter()
        self.__select_formatter_type("boolean")
        self.__click_apply()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def format_as_duration(self, source_duration):
        """Sets custom scripts for the invoked column object

        Args:
            source_duration (str):  source duration which is to be given.

        """
        self._select_current_component()
        self._click_general_tab()
        self.__click_formatter()
        self.__select_formatter_type("duration")
        self.__set_duration_unit(source_duration)
        self.__click_apply()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def set_custom_styles(self, script):
        """Sets custom styles for the invoked column object

        Args:
            script (str):  script which is to be applied.

        """
        self._select_current_component()
        self._click_general_tab()
        self.__enter_style(script)

    @PageService()
    def set_display_name(self, name):
        """Sets the given display name"""
        self._select_current_component()
        self._click_general_tab()
        self.__set_column_name(name)

    @PageService()
    def set_aggregation(self, aggregation):
        """Set the given Aggregation"""
        self._select_current_component()
        self._click_general_tab()
        self.__select_aggregation_drop_down(aggregation.capitalize())

    @PageService()
    def wrap_text(self, toggle=True):
        """Wraps the text"""
        if toggle != self._get_toggle_state():
            self._select_current_component()
            self._click_general_tab()
            self.__toggle_wrap_text()

    @PageService()
    def set_column_width(self, width):
        """Sets the column width"""
        self._select_current_component()
        self._click_general_tab()
        self.__set_column_width(width)

    @PageService()
    def split_column_by(self, delimiter):
        """Splits the column"""
        self._select_current_component()
        self._click_general_tab()
        self.__split_column(delimiter)

    @WebAction()
    def __split_column(self, delimiter):
        """Sets the split delimiter"""
        input_field = self._driver.find_element(By.XPATH, "//*[@title='Split By']/..//input")
        input_field.clear()
        input_field.send_keys(delimiter)

    @PageService()
    def hide_column(self):
        """Hide Column"""
        self._select_current_component()
        self._click_general_tab()
        self.__select_hidden_drop_down("True")

    @PageService()
    def exclude_column_from_csv(self):
        """Excludes column form CSV"""
        self._select_current_component()
        self._click_general_tab()
        self.__exclude_column()
