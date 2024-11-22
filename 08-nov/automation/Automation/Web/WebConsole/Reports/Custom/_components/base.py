from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module holds the classes that are common for
one or more classes

Only classes present inside the __all__ variable should be
imported by TestCases and Utils, rest of the classes are for
internal use
"""

from abc import ABC
from abc import abstractmethod
from time import sleep
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)


class CRComponent(ABC):
    """All components on custom reports must directly or indirectly
    inherit this class"""

    DS_COLUMN = "//*[@data-datasetname='%s']//*[.='%s']"

    def __init__(self, title):
        """
        Args:
            title (str): Title of the CustomReport component
        """
        self.__browser: Browser = None
        self.__webconsole = None
        self.__driver: Browser.driver = None
        self.__x = None

        self.title = title
        self.dataset_name = None
        self.page_name = None
        self.id = None

    @property
    def _driver(self):
        if self.__driver is None:
            raise ValueError("driver not initialized, was add_component called ?")
        return self.__driver

    @property
    def _webconsole(self):
        if self.__webconsole is None:
            raise ValueError("webconsole not initialized, was add_component called ?")
        return self.__webconsole

    @property
    def _browser(self):
        if self.__browser is None:
            raise ValueError("browser not initialized, was add_component called ?")
        return self.__browser

    @_driver.setter
    def _driver(self, value):
        self.__driver = value

    @_browser.setter
    def _browser(self, value):
        self.__browser = value

    @_webconsole.setter
    def _webconsole(self, value):
        self.__webconsole = value

    @property
    def _x(self):
        """Return the base component XPath.

        Simply kept it 'x' to avoid long names in xpath string"""
        if self.__x is None:
            self.__x = "//*[@comp='%s']" % self.id
        return self.__x

    def _set_x(self, id_, xp=None):
        """
        Set base component XPath
        Args:
             id_ : Set the component ID, Base XPath will be derived
                as `"//*[@comp='%s']" % id_`
             xp : Directly use the supplied value as base XP, set id_ to None
                while using xp
        """
        if xp is None:
            self.__x = "//*[@comp='%s']" % id_
        else:
            self.__x = xp

    @WebAction()
    def _select_current_component(self):
        """Clicks the current component"""
        WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.XPATH, self._x)))
        component = self._driver.find_element(By.XPATH, self._x)
        component.click()

    def __str__(self):
        return f"<{self.__class__.__name__} Title=[{self.title}] ID=[{id(self)}]>"


class CRComponentBuilder(CRComponent):

    """This class holds this common functionalities for all the Builder operations
    done on the Component"""

    @property
    @abstractmethod
    def name(self):
        """
        Override this as variable inside subclass and return the
        components name

        The name has to be the exact name displayed on the
        Visualization panel
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def category(self):
        """
        Override this as variable inside subclass and return the
        components category

        The category name has to exactly match what has been displayed
        on the Visualization panel
        """
        raise NotImplementedError

    @WebAction()
    def _validate_dataset_column(self, dataset_name, column_name):
        """Checking if column exists"""
        col_obj = self._driver.find_element(By.XPATH, 
            "//*[@data-datasetname='%s']//*[.='%s']" % (
                dataset_name, column_name))  # To check if column and dataset exists
        if col_obj.is_displayed():
            return
        raise CVWebAutomationException(
            "Column [%s] not found inside dataset [%s]" % (
                column_name, self.dataset_name))

    def _drag_column_from_dataset(self, column_name, target_xpath):
        """Add columns from the dataset to the target"""
        source_xpath = CRComponent.DS_COLUMN % (self.dataset_name, column_name)
        self._browser.drag_and_drop_by_xpath(source_xpath, target_xpath)

    def _drag_dataset_to_component(self, target_xpath):
        """Drag dataset to component"""
        self._browser.drag_and_drop_by_xpath(
            f"//*[@data-id]//*[@title='{self.dataset_name}']",
            target_xpath
        )

    def configure_builder_component(self, webconsole, dataset, page, id_, xpath=None):
        """
        Do not call this method explicitly, it would automatically be called
        when you add this component to Builder
        """
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self.dataset_name = dataset
        self.page_name = page
        self.id = id_
        self._set_x(id_, xpath)


class CRComponentViewer(CRComponent):

    """All the actions common to all components on viewer go to this class"""

    @WebAction()
    def _get_id_from_component_title(self, title):
        """Get component ID from component Title"""
        try:
            web_obj = self._driver.find_element(By.XPATH, 
                f"//*[text()='%s' and contains(@class, 'component-title-text')]/ancestor::li[@data-component-type='{self.type}']"
                % title)
        except NoSuchElementException:  # for column level id checks above xpath wont work
            web_obj = self._driver.find_element(By.XPATH, 
                "//*[text()='%s']/ancestor::li" % title)
        return web_obj.get_attribute("comp")

    @WebAction()
    def _get_id_from_component_type(self):
        """Get component ID from component Type"""
        web_obj = self._driver.find_element(By.XPATH, 
            "//li[@data-component-type='%s']" % self.type)
        return web_obj.get_attribute("comp")

    @property
    @abstractmethod
    def type(self):
        """
        Override this as variable inside subclass and return the
        components type

        The type name has to exactly match what has been set on data-component-type on li tag
        of Component
        this will be used to access the component if title is not set
        """
        raise NotImplementedError

    def configure_viewer_component(self, webconsole, page, comp_id=None):
        """
        Do not call this method explicitly, it would automatically be called
        when you add this component to Viewer
        """
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self.page_name = page
        if comp_id:
            self.id = comp_id
        elif self.title:
            self.id = self._get_id_from_component_title(self.title)
        else:
            self.id = self._get_id_from_component_type()
        self._set_x(self.id)


class CRComponentProperties(CRComponent):

    """All the actions common to all components on Properties panel go to this class. """

    @WebAction()
    def _click_general_tab(self):
        """ Clicks on General Tab """
        tab = self._driver.find_element(By.XPATH, "//li[@title='General']")
        return tab.click()

    @WebAction()
    def _click_fields_tab(self):
        """ Clicks on Fields Tab """
        tab = self._driver.find_element(By.XPATH, "//li[@title='Fields']")
        tab.click()

    @WebAction()
    def _click_scripts_tab(self):
        """ Clicks on Custom Code Tab """
        tab = self._driver.find_element(By.XPATH, "//li[@title='Custom Code']")
        tab.click()

    @WebAction()
    def _click_add_expression(self):
        """Click add expression"""
        button = self._driver.find_element(By.XPATH, "//button[contains(., 'Add Expression')]")
        button.click()

    @WebAction()
    def _click_add_style(self):
        """Sets the style"""
        button = self._driver.find_element(By.XPATH, "//button[contains(., 'Add Style')]")
        button.click()

    @WebAction(delay=1)
    def _click_add_script(self):
        """Click add script"""
        button = self._driver.find_element(By.XPATH, "//button[contains(., 'Add Script')]")
        button.click()

    @WebAction()
    def _click_save_on_code_editor(self):
        """Click save on code windows"""
        save = self._driver.find_element(By.XPATH, "//button[.='Save']")
        save.click()

    @WebAction(delay=1)
    def _set_code_editor(self, code, clear=False):
        """Enter style in code area"""
        text_area = self._driver.find_element(By.XPATH, "//textarea[@class='ace_text-input']")
        # text_area.clear()
        if clear:
            text_area.send_keys(Keys.DELETE)
            text_area.send_keys(Keys.DELETE)
        text_area.send_keys(code)

    @WebAction()
    def __set_active_component_title(self, title):
        """Enter component title """
        title_field = self._driver.find_element(By.XPATH, 
            "//input[@*='propData.title.text']")
        title_field.clear()
        title_field.send_keys(title)

    @WebAction()
    def _set_component_security(self, role):
        """Sets Component Security"""

        roles = self._driver.find_element(By.XPATH, 
            "//label[text()='Component Security']/..//*[contains(@data-ng-model,'item.visible.type')]")
        select = Select(roles)
        select.select_by_visible_text(role)

    @PageService()
    def set_component_title(self, title):
        """ Sets the component title

        Args:
            title(str) : The title which is to be set

        """
        self._select_current_component()
        self._click_general_tab()
        self.__set_active_component_title(title)

    @PageService()
    def set_component_security(self, role):
        """ Set Component Security with specified role

        Args:
            role(str) : The role which is to be set (Case Sensitive)
            Available roles : All, Tenant Admin,Commcell Admin, Custom

        """
        self._select_current_component()
        self._click_general_tab()
        sleep(5)
        self._set_component_security(role)
