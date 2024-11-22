# -*- coding: utf-8 -*-
#
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
All the operations on html component go to this file
"""

from selenium.webdriver.common.by import By

from Web.Common.page_object import (
    WebAction,
    PageService
)
from .base import (
    CRComponentViewer
)


class HtmlComponentViewer(CRComponentViewer):
    """functions for retrieving html component data"""

    @property
    def type(self):
        return "CUSTOM"

    @WebAction()
    def __get_html_component_text(self):
        """Get html component text"""
        html_component = self._driver.find_element(By.XPATH, f"{self._x}//*[contains(@class, 'panel-content')]")
        return html_component.text

    @WebAction()
    def __click_button(self, label):
        """Click on button with specific label"""
        html_component_button = self._driver.find_element(By.XPATH, f"{self._x}//button[.='{label}']")
        html_component_button.click()

    @PageService()
    def get_html_component_contents(self):
        """
        Get html component contents
        Returns                  (String)      --      html component string
        """
        return self.__get_html_component_text()

    @PageService()
    def click_button(self, label):
        """Click on button present in html component"""
        self.__click_button(label)


class HitsViewer(CRComponentViewer):

    @WebAction()
    def __get_hit_title(self):
        """Returns HIT component's title"""
        return self._driver.find_element_by_xpath(f'{self._x}//h4').text

    @WebAction()
    def __get_hit_value(self):
        """Returns HIT component's value"""
        return self._driver.find_element_by_xpath(f'{self._x}//h5').text

    @WebAction()
    def __click_by_text(self, text):
        """click HIT component's value"""
        return self._driver.find_element_by_xpath(
            f"{self._x}//h5//a[contains(text(),'{text}')]").text

    @PageService()
    def get_title(self):
        """Returns HIT title"""
        return self.__get_hit_title()

    @PageService()
    def get_value(self):
        """Returns HIT value"""
        return self.__get_hit_value()

    @PageService()
    def click_by_content(self):
        """Returns HIT value"""
        self.__click_by_text()
        self._adminconsole.wait_for_completion()

    @property
    def type(self):
        return "HITS"


class RComponentViewer(CRComponentViewer):
    """functions for retrieving html component data"""

    @property
    def type(self):
        return "R-GGPlot"

    @WebAction()
    def __get_img_src(self):
        """Get html component text"""
        r_component = self._driver.find_element(By.XPATH, f"{self._x}//div[@id='rImage']//img")
        return r_component.get_attribute('src')

    @PageService()
    def get_img_src(self):
        """Get img src"""
        return self.__get_img_src()

