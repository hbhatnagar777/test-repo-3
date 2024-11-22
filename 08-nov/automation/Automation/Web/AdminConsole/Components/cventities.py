# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" 
This module provides support for cv designed entities in Admin Console pages

CVEntityMultiSelect, CVActionsToolbar and CVMainBarAction are the 3 classes defined in this file

CVEntityMultiSelect:

    search_and_select()        --    Searches for the given text value and applies it

CVActionsToolbar:

    select_action_sublink()     --   To select action sublink from the dropdown

CVMainBarAction:

    access_action_item()        --   Selects the action item depending on the button text provided

"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.dialog import ModalDialog
from Web.Common.page_object import WebAction, PageService


class CVEntityMultiSelect:
    """ CVEntityMultiSelect component used in Admin console pages """

    def __init__(self, admin_console, id=None):
        """ 
        Initialize the CVEntityMultiSelect object
        
        Args:

            admin_console (obj)        :    Admin console class object
            id (str)                   :    Multi select panel ID attribute value
        """
        self._driver = admin_console.driver
        self._adminconsole_base = admin_console
        self.log = self._adminconsole_base.log
        self._dialog = ModalDialog(self._adminconsole_base)
        if id:
            self._xp = f"//form[@id='{id}']"
        else:
            self._xp = "//cv-entity-multi-select"


    @WebAction()
    def search_and_select(self, text_value, click_submit=True):
        """ 
        Searches for the given text value and applies it
            Args:
                text_value          (str):      Text to be searched and applied
                click_submit        (bool):     To Click Submit button or not
            
            Return (Bool):
                True/False based on the success of the text selection   
            
        """
        search_xpath = f"{self._xp}//input[@type='text']"
        select_xpath = f"{self._xp}//label[contains(text(),'{text_value}')]"
        self._adminconsole_base.driver.find_element(By.XPATH, search_xpath).send_keys(text_value)
        if self._adminconsole_base.check_if_entity_exists('xpath', select_xpath):
            self._adminconsole_base.click_by_xpath(select_xpath)
            if click_submit:
                self._dialog.click_submit()
            return True

        self.log.info("Applying the given text value failed")
        return False

class CVActionsToolbar:
    """CVActionsToolbar component used in Admin console pages"""

    def __init__(self,admin_console):
        """
        Initialize the CVActionsToolbar object

        Args:

            admin_console (obj)        :    Admin console class object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = "//div[@class='cvActionsToolbar']"

    @WebAction()
    def __click_action_dropdown(self):
        """Selects action dropdown"""
        xp = self._xpath+"//span[contains(@data-ng-if,'action.isKebabMenu') and contains(@class,'uib-dropdown dropdown header-menu ng-scope')]"
        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def __click_sub_link(self,text):
        """
        Selects item from action dropdown
        Args:
            text(str):  select the specific entity from dropdown
        """
        xp = self._xpath + f"//span[text()='{text}']"
        self._driver.find_element(By.XPATH, xp).click()

    @PageService()
    def select_action_sublink(self, text, expand_dropdown=True):
        """
        to select action sublink
        Args:
            text(str): select the specific entity from dropdown
            expand_dropdown (bool): expand dropdown
        """
        if expand_dropdown:
            self.__click_action_dropdown()
        self.__click_sub_link(text)


class CVMainBarAction:
    """CVMainBarAction component used in Admin console pages"""

    def __init__(self, admin_console):
        """
        Initialize the CVActionsToolbar object

        Args:

            admin_console (obj)        :    Admin console class object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = "//div[contains(@class, 'cv-main-bar-action')]"

    @WebAction()
    def access_action_item(self, button_text):
        """
        Selects the action item depending on the button text provided
        Args:
            button_text(str):  select the specific entity from dropdown
        """
        xp = self._xpath + f"/child::span[contains(text(), {button_text})]"
        self._driver.find_element(By.XPATH, xp).click()
