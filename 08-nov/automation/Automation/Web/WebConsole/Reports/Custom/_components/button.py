from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All the operations common to Button component goes to this file."""
from enum import Enum

from selenium.webdriver.support.ui import Select

from Web.Common.page_object import WebAction, PageService
from .base import (
    CRComponentBuilder,
    CRComponentViewer,
    CRComponentProperties
)


class ButtonBuilder(CRComponentBuilder):
    """Actions common to Button Builder goes here"""
    @property
    def category(self):
        raise NotImplementedError

    @property
    def name(self):
        return NotImplementedError


class ButtonViewer(CRComponentViewer):
    """Actions common to Button Viewer goes here"""

    @property
    def type(self):
        return ''

    @WebAction()
    def _get_id_from_component_title(self, title):
        """Get component ID from component Title"""
        web_obj = self._driver.find_element(By.XPATH, 
            f"//*[.='{title}']/parent::button")
        return web_obj.get_attribute("id")

    @WebAction()
    def _button_state(self):
        """Returns the button state for the attribute disabled"""
        button = self._driver.find_element(By.XPATH, self._x)
        return button.get_attribute("disabled")

    @WebAction()
    def __fetch_button_image_source(self):
        """Fetches the image source"""
        button = self._driver.find_element(By.XPATH, self._x + "//img")
        return button.get_attribute("src")

    @WebAction()
    def __fetch_button_color(self):
        """Returns the value of the color attribute"""
        button = self._driver.find_element(By.XPATH, self._x)
        return button.value_of_css_property("color")

    @WebAction()
    def __press_button(self):
        """Presses the button"""
        button = self._driver.find_element(By.XPATH, self._x)
        button.click()

    @PageService()
    def is_button_enabled(self):
        """
        Returns (bool): True if button is enabled

        """
        state = self._button_state()
        return False if state == "true" else True

    @PageService()
    def get_button_image_source(self):
        """Get button image URL"""
        return self.__fetch_button_image_source()

    @PageService()
    def get_button_color(self):
        """Returns the button color"""
        return self.__fetch_button_color()

    @PageService()
    def click_button(self):
        """Clicks the button"""
        self.__press_button()


class ButtonProperties(CRComponentProperties):
    """Actions common to Button Properties go here"""

    @WebAction()
    def __select_image_type(self, type_):
        """Selects the image type from the drop down"""
        drop_down = self._driver.find_element(By.XPATH, "//*[@title='Image Type']/..//select")
        Select(drop_down).select_by_value(type_)

    @WebAction()
    def __set_image_source(self, source):
        """Sets the given source"""
        img_source = self._driver.find_element(By.XPATH, "//*[@title='Image Source']/..//input")
        img_source.clear()
        img_source.send_keys(source)

    @WebAction()
    def __select_enable_type_from_drop_down(self, type_):
        """Selects the given drop down"""
        drop_down = self._driver.find_element(By.XPATH, "//*[@title='Enable']/..//select")
        Select(drop_down).select_by_value(type_)

    @WebAction()
    def __set_button_expression(self, script):
        """Sets the button expression"""
        text_area = self._driver.find_element(By.XPATH, "//*[@title='Expression']/..//textarea")
        text_area.clear()
        text_area.send_keys(script)

    @WebAction()
    def __set_enable_expression(self, script):
        """Sets the button expression"""
        text_area = self._driver.find_element(By.XPATH, "//*[@title='Enable Expression']/..//textarea")
        text_area.clear()
        text_area.send_keys(script)

    @WebAction()
    def __add_custom_class(self, class_):
        """Sets the class for the button"""
        img_source = self._driver.find_element(By.XPATH, "//*[@title='Add custom class']/..//input")
        img_source.clear()
        img_source.send_keys(class_)

    @WebAction()
    def __set_onclick_drop_down(self, value):
        """Sets the onclick dropdown of the button"""
        onclick = self._driver.find_element(By.XPATH, "//*[@title='onClick']/..//select")
        Select(onclick).select_by_visible_text(value)

    @WebAction()
    def __set_workflow_drop_down(self, value):
        """Sets the workflow dropdown of the button"""
        workflow = self._driver.find_element(By.XPATH, "//label[contains(text(),'Workflow')]"
                                                      "/following-sibling::div/select")
        Select(workflow).select_by_visible_text(value)

    @PageService()
    def set_image(self, type_, source):
        """Set image on button

        Args:
            type_ (str): Type of the image. Either 'custom' or 'url'

            source (str): Source of the image

        """
        self._select_current_component()
        self._click_general_tab()
        self.__select_image_type(type_)
        self.__set_image_source(source)

    @PageService()
    def set_custom_class(self, class_):
        """Sets the custom class

        Args:
            class_ (str): Custom class string for the button

        """
        self._select_current_component()
        self._click_general_tab()
        self.__add_custom_class(class_)

    @PageService()
    def enable_option(self, option, expression=None):
        """Selects the given enable from the drop down list

        Args:
            option (ButtonProperties.EnableOption)     : The type of option. One among 'always', 'singleSelect',
             'multiSelect', 'custom' is usually selected.

            expression (str) : Script to be inserted

        """
        if option not in ButtonProperties.EnableOption:
            raise KeyError(f"Unsupported enable option type [{option.value}] received")
        self._select_current_component()
        self._click_general_tab()
        self.__select_enable_type_from_drop_down(option.value)
        if option == "custom":
            self.__set_enable_expression(expression)

    @PageService()
    def set_button_style(self, style):
        """Sets the button style

        Args:
            style (str): style to be inserted.

        """
        self._select_current_component()
        self._click_scripts_tab()
        self._click_add_style()
        self._set_code_editor(style)
        self._click_save_on_code_editor()

    @PageService()
    def set_expression(self, script):
        """Sets expression

        Args:
            script (str): script to be inserted

        """
        self._select_current_component()
        self._click_scripts_tab()
        self.__set_onclick_drop_down("Custom")
        self._click_add_expression()
        self._set_code_editor(script, clear=True)
        self._click_save_on_code_editor()

    @PageService()
    def set_workflow(self, name):
        """sets workflow

        Args:
            name (str): Name of the workflow to be set

        """
        self._select_current_component()
        self._click_scripts_tab()
        self.__set_onclick_drop_down("Run a workflow")
        self.__set_workflow_drop_down(name)

    class EnableOption(Enum):
        ALWAYS = 'always'
        SINGLE_SELECT = 'singleSelect'
        MULTI_SELECT = 'multiSelect'
        CUSTOM = 'custom'