from selenium.webdriver.common.by import By
"""
All the logic to handle the page operations reside inside this module

Only classes present inside the __all__ variable should be
imported by TestCases and Utils, rest of the classes are for
internal use
"""
from Web.Common.page_object import WebAction, PageService
from time import sleep
from .base import (
    CRComponentBuilder,
    CRComponentViewer,
    CRComponentProperties
)


class PageBuilder(CRComponentBuilder):

    """Although page is not standard Visualization component, internally for
    design sake we consider it as a component just like other CR components"""

    @property
    def name(self):
        return ""

    @property
    def category(self):
        return ""

    def __click_page_title(self, page):
        """Click Page title text"""
        title = self._driver.find_element(By.XPATH, 
            "//*[@id='centerCol']//*[@title='%s']" % page)
        title.click()

    def __drag_component_to_page(self, category, name):
        """Drag the component to page"""
        comp_xpath = "//*[@id='rightCol']//*[@title='%s']//*[.='%s']" % (
            category, name)
        self._browser.drag_and_drop_by_xpath(
            comp_xpath, "//*[@id='lowerPaddingDiv']")


class PageViewer(CRComponentViewer):
    """
    All methods for page viewer goes here
    """
    @property
    def type(self):
        return ''


class PageProperties(CRComponentProperties):
    """
    All methods for page properties goes here
    """

    @WebAction()
    def __click_page_properties(self):
        """Clicks page properties"""
        page_properties = self._driver.find_element(By.XPATH, f"//*[@title='{self.page_name}']/"
                                                             "following-sibling::span[@title='Page Properties']")
        page_properties.click()

    @PageService()
    def custom_javascript(self, script):
        """Apply Custom Javascript to the page

        Args:
            script (str):     --      script to be applied

        """
        self.__click_page_properties()
        self._click_scripts_tab()
        self._click_add_script()
        self._set_code_editor(script)
        self._click_save_on_code_editor()

    @PageService()
    def custom_styles(self, style):
        """Apply Custom CSS to the page

        Args:
            style (str):     --      CSS to be applied

        """
        self.__click_page_properties()
        self._click_scripts_tab()
        self._click_add_style()
        self._set_code_editor(style)
        self._click_save_on_code_editor()

    @PageService()
    def set_component_security(self, role):
        """ Set Component Security with specified role

        Args:
            role(str) : The role which is to be set (Case Sensitive)
            Available roles : All, Tenant Admin,Commcell Admin, Custom

        """
        # Overriding CRComponent Properties method here specific to page
        self.__click_page_properties()
        sleep(5)
        self._set_component_security(role)
