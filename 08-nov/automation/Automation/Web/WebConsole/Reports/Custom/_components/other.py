from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
All the operations on html component go to this file
"""

from Web.Common.page_object import (
    WebAction,
    PageService
)
from .base import (
    CRComponentBuilder,
    CRComponentProperties,
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
        html_component = self._driver.find_element(By.XPATH, f"{self._x}//*[@class='customHtml']")
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


class HtmlComponentProperties(CRComponentProperties):
    """This class contains html component properties"""

    def _click_add_html(self):
        """Click add html"""
        button = self._driver.find_element(By.XPATH, "//button[contains(.,'Add HTML')]")
        button.click()

    def add_html_script(self, script):
        """
        Add html script
        Args:
            script                      (String)  --     html string
        """
        self._select_current_component()
        self._click_scripts_tab()
        self._click_add_html()
        self._set_code_editor(script)
        self._click_save_on_code_editor()


class HtmlComponentBuilder(CRComponentBuilder):
    """This class contains all the builder actions specific to html component"""

    @property
    def category(self):
        """'Other' property"""
        return "Other"

    @property
    def name(self):
        """Name of the component"""
        return "Html"

    @WebAction()
    def __drag_data_column(self, column):
        """drag data column"""
        self._select_current_component()
        self._drag_column_from_dataset(column, self._x + "//*[@class='axisColumnDrop "
                                                         "ng-isolate-scope']")

    @PageService()
    def drop_data_column(self, column):
        """
        Set data column into html component
        Args:
            column               (String)            --    name of the column
        """
        self.__drag_data_column(column)


class RPlotBuilder(CRComponentBuilder):
    @property
    def category(self):
        return "Other"

    @property
    def name(self):
        return "R-Plot"

    @WebAction()
    def __drag_data_column(self, column):
        """drag data column"""
        self._select_current_component()
        self._drag_column_from_dataset(column, self._x + "//div[@class='dropMsg']")

    @PageService()
    def drop_data_column(self, column):
        """
        Set data column into html component
        Args:
            column               (String)            --    name of the column
        """
        self.__drag_data_column(column)


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


class RComponentProperties(CRComponentProperties):
    """This class contains R component properties"""


class HitsViewer(CRComponentViewer):

    @WebAction()
    def __get_hit_title(self):
        """Returns HIT component's title"""
        return self._driver.find_element_by_xpath(f'//*/div[@id="{self.title}"]//../h4').text

    @WebAction()
    def __get_hit_value(self):
        """Returns HIT component's value"""
        return self._driver.find_element_by_xpath(f'//*/div[@id="{self.title}"]//../h5').text

    @PageService()
    def get_title(self):
        """Returns HIT title"""
        return self.__get_hit_title()

    @PageService()
    def get_value(self):
        """Returns HIT value"""
        return self.__get_hit_value()

    @property
    def type(self):
        return "HITS"


class FacetViewer(CRComponentViewer):

    @property
    def type(self):
        return "FacetFilters"

    @WebAction()
    def __select_filter_value(self, filter_value):
        """Clicks on the facet filter dropdown value"""
        xpath = f'{self._x}//../table//../span[text()="{filter_value}"]'
        self._driver.find_element_by_xpath(xpath).click()

    @PageService()
    def select_filter(self, filter_value):
        """Selects the given filter value from the component dropdown"""
        self._select_current_component()
        self.__select_filter_value(filter_value)
        self._webconsole.wait_till_load_complete()
        self._select_current_component()
