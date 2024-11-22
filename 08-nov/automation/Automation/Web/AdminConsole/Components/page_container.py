from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides support for PageContainer entities in Admin Console pages

PageContainer:

    access_page_action()                --  Method to click on page action
    
    access_page_action_from_dropdown()    --  Method to click on the page action menu under a dropdown on a page

    check_if_page_action_item_exists()  --  Method to check if action item exists on top of page

    fetch_title()                       -- Method to fetch the title
    
    check_tab()                         --  Check if tab exists
    
    select_configuration_tab()          --  select the configuration tab
    
    select_overview_tab()               --  select the overview tab
    
    select_entities_tab()                    --  select the sub clients or backup sets tab

    click_button()                  -- Clicks on button by text value or id value

    click_button_using_id()         -- Method to click on a button using id

    click_button_using_text()       -- Method to click on a button using text
"""

from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.alert import Alert


class PageContainer:
    """ PageContainer component used in Admin console pages """

    def __init__(self, admin_console, id_value=None):
        """
        Initialize the PageContainer object

        Args:

            admin_console (obj)        :    Admin console class object
            id_value (str)             :    Page container ID attribute value
        """
        self._driver = admin_console.driver
        self._admin_console = admin_console
        self._alert = Alert(admin_console)
        if id_value:
            self._xp = f"//div[contains(@class, 'page-container') and @id='{id_value}']"
        else:
            self._xp = "//div[contains(@class, 'page-container')]"

    @WebAction()
    def __click_on_page_action_item(self, text_value, partial_selection=True):
        """
        method to click on page action
        Args:
            text_value: localized menu text
            partial_selection (bool): flag to determine if entity name should be selected in case of partial match or
                                      not
        """
        if partial_selection:
            xpath = f"{self._xp}//button/*[contains(text(), '{text_value}')]"
            dropdown_xpath = f"//ul[@role='menu']//li[contains(.,'{text_value}')]"
            if self._admin_console.check_if_entity_exists("xpath", xpath):
                self._driver.find_element(By.XPATH, xpath).click()
            else:
                self._driver.find_element(By.XPATH, dropdown_xpath).click()
        else:
            dropdown_xpath = f"//ul[@role='menu']//li//*[text()='{text_value}']"
            self._driver.find_element(By.XPATH, dropdown_xpath).click()

    @WebAction()
    def __click_on_page_action_dropdown(self):
        """
        method to click on page action from drop down menu

        """
        dropdown_xpath = f"//div[@aria-label='More' and @class='popup']"
        self._driver.find_element(By.XPATH, dropdown_xpath).click()

    @WebAction()
    def check_if_page_action_item_exists(self, text):
        """Method to check if page action item exists"""
        xpath = f"//div[contains(@class,'page-action') or contains(@class, 'action-list') or " \
                f"contains(@class,'MuiMenu-paper')]//*[contains(text(), '{text}')]"
        return self._admin_console.check_if_entity_exists("xpath", xpath)

    @PageService()
    def access_page_action(self, name, sub_action=None):
        """method click on page action

            Args:
            name: Name of the page action to be accessed
            sub_action: Name of the sub action to click (when page action opens a dropdown/menu)

        """
        self._alert.close_popup(5)  # sometimes, alert toast overlaps page actions, close it first
        if self.check_if_page_action_item_exists(name):
            self.__click_on_page_action_item(name)
            if sub_action:
                sub_action_btn = WebDriverWait(self._driver, 5).until(
                    ec.element_to_be_clickable(
                        (By.XPATH, f"//li[contains(.,'{sub_action}')]//button")
                    )
                )
                sub_action_btn.location_once_scrolled_into_view
                sub_action_btn.click()
            self._admin_console.wait_for_completion()
        else:
            self.access_page_action_from_dropdown(name)

    @PageService()
    def hover_over_save_as(self, text_value):
        """
        Hovers over Save as
        Args:
            text_value: localized text for save as
        """
        self.__click_on_page_action_dropdown()
        self._admin_console.wait_for_completion()
        save_as = self._driver.find_element(By.XPATH, f"//ul[@role='menu']//li[contains(.,'{text_value}')]")
        action_chain = ActionChains(self._driver)
        action = action_chain.move_to_element(save_as)
        action.perform()

    @PageService()
    def access_page_action_from_dropdown(self, name, partial_selection=True):
        """ Method to click on the page action menu under a dropdown on a page
        Args:
            name: localized menu text
            partial_selection (bool): flag to determine if entity name should be selected in case of partial match or
                                      not
        """
        self.__click_on_page_action_dropdown()
        self._admin_console.wait_for_completion()
        self.__click_on_page_action_item(name, partial_selection)
        self._admin_console.wait_for_completion()

    @WebAction()
    def __click_on_page_tab(self, tab_name):
        """Method to click on page tab"""
        tab_xpath = f"{self._xp}//*[contains(@class, 'bar-tabs page-tabs')]//*[contains(text(), '{tab_name}')]"
        self._driver.find_element(By.XPATH, tab_xpath).click()

    @WebAction()
    def __click_on_page_tab_by_id(self, tab_id):
        """Method to click on page tab using id

        Args:
            tab_id(str) :   Id of the tab to be clicked

        """
        tab_xpath = f"{self._xp}//*[contains(@class, 'bar-tabs page-tabs')]//*[@id='{tab_id}']"
        self._driver.find_element(By.XPATH, tab_xpath).click()

    @PageService()
    def select_tab(self, tab_name=None, tab_id=None):
        """Method to select the tab

        Args:
            tab_name (str)  : name of the tab to be clicked on
            tab_id  (str)       : id of the tab to be clicked on
        """
        if tab_name:
            self.__click_on_page_tab(tab_name)
        else:
            self.__click_on_page_tab_by_id(tab_id)
        self._admin_console.wait_for_completion()

    @WebAction()
    def check_tab(self, tab_name):
        """Method to check the tab

                Args:
                    tab_name (str)  : name of the tab to be checked
        """
        tab_xpath = f"{self._xp}//*[contains(@class, 'bar-tabs page-tabs')]//*[contains(text(), '{tab_name}')]"
        return self._admin_console.check_if_entity_exists("xpath", tab_xpath)

    @PageService()
    def select_configuration_tab(self):
        """
        Selects the configuration tab

        Raises:
            NoSuchElementException:
                if the configuration tab is not present
        """
        self.select_tab(self._admin_console.props['label.nav.configuration'])

    @PageService()
    def select_overview_tab(self):
        """
        Selects the configuration tab

        Raises:
            NoSuchElementException:
                if the configuration tab is not present
        """
        self.select_tab(self._admin_console.props['label.tab.overview'])

    @PageService()
    def select_entities_tab(self):
        """
            Method to select the backup sets or sub clients tab
        """
        if self._admin_console.check_if_entity_exists("id", "subclientList"):
            self.select_tab(tab_id="subclientList")
        elif self.check_tab(self._admin_console.props["heading.BackupSets"]):
            self.__click_on_page_tab(self._admin_console.props["heading.BackupSets"])
        elif self.check_tab(self._admin_console.props["label.tableGroups"]):
            self.__click_on_page_tab(self._admin_console.props["label.tableGroups"])
        elif self.check_tab(self._admin_console.props["label.DatabaseGroups"]):
            self.__click_on_page_tab(self._admin_console.props["label.DatabaseGroups"])
        elif self.check_tab(self._admin_console.props["label.subclients"]):
            self.__click_on_page_tab(self._admin_console.props["label.subclients"])
        elif self.check_tab(self._admin_console.props["label.instanceGroups"]):
            self.__click_on_page_tab(self._admin_console.props["label.instanceGroups"])
        elif self.check_tab(self._admin_console.props["label.projectGroups"]):
            self.__click_on_page_tab(self._admin_console.props["label.projectGroups"])

    @WebAction()
    def click_on_button_by_id(self, button_id):
        """Method to click on button using id

        Args:
            button_id(str) :   Id of the button to be clicked

        """
        button_xpath = f"{self._xp}//button[@id='{button_id}']"
        self._driver.find_element(By.XPATH, button_xpath).click()

    @WebAction()
    def click_on_button_by_text(self, button_value):
        """Method to click on button using text

        Args:
            button_value(str) :   text of the button to be clicked

        """
        button_xpath = f"{self._xp}//button[contains(.,'{button_value}')]"
        self._driver.find_element(By.XPATH, button_xpath).click()

    @PageService()
    def click_button(self, id=None, value=None, wait_for_completion=True):
        """Method to click on button using id

                Args:
                    id(str) :   Id of the button to be clicked
                    value(str): text of the button to be clicked
                    wait_for_completion(bool):Whether to wait for loading to finish
            """
        if id:
            self.click_on_button_by_id(id)
        elif value:
            self.click_on_button_by_text(value)
        else:
            raise Exception('click_button: Please provide at least one input')

        if wait_for_completion:
            self._admin_console.wait_for_completion()

    @WebAction()
    def fetch_title(self):
        """Fetches the name in title"""
        if self._admin_console.check_if_entity_exists("xpath", f"//input[contains(@class,'MuiInputBase-input') "
                                                               "and @id!='global-search-text-input']"):
            return self._driver.find_element(By.XPATH, f"//input[contains(@class,'MuiInputBase-input') "
                                                               "and @id!='global-search-text-input']')]") \
                .get_attribute('value')
        else:
            return self._driver.find_element(By.XPATH, "//span[contains(@class,'title-display')]").text

    @WebAction()
    def __click_on_name_change_button(self):
        """Clicks on name change edit button"""
        xpath1 = "//*[contains(@class, 'Title')]//button"
        if self._driver.find_elements(By.XPATH, xpath1):
            edit = self._driver.find_element(By.XPATH, xpath1)
        else:
            xpath2 = "//div[@id='cv-changename']"
            edit = self._driver.find_element(By.XPATH, xpath2)
        self._driver.execute_script("arguments[0].click();", edit)

    @WebAction()
    def __enter_new_title(self, new_title):
        """Method to type new title"""
        name_box = self._driver.find_element(By.XPATH, "//*[contains(@id,'editableTitle')] | "
                                             "//div[contains(@class,'entityTitleContainer')]//*[contains(@class,'MuiInputBase-input')]")
        name_box.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        name_box.send_keys(new_title + u'\ue007')  # new_title + enter

    @PageService()
    def edit_title(self, new_name):
        """Method to edit name for an entity from details page

        Args:
            new_name (str)  : new entity name
        """
        self.__click_on_name_change_button()
        self.__enter_new_title(new_name)
        self.__click_on_name_change_button()

    def _get_breadcrumb_xpath(self, breadcrumb_name: str) -> str:
        """Method to return breadcrumb xpath"""
        return f"{self._xp}//*[contains(@class, 'MuiBreadcrumbs')]//*[text()='{breadcrumb_name}']"

    @WebAction()
    def __is_breadcrumb_exists(self, breadcrumb_name: str) -> bool:
        """Method to check if breadcrumb available on the page"""
        return self._admin_console.check_if_entity_exists("xpath", self._get_breadcrumb_xpath(breadcrumb_name))

    @WebAction()
    def __click_on_breadcrumb(self, breadcrumb_name: str) -> None:
        """Method to click on breadcrumb available on the page"""
        self._driver.find_element(By.XPATH, self._get_breadcrumb_xpath(breadcrumb_name)).click()

    @PageService()
    def is_bread_crumb_exist(self, breadcrumb_name: str) -> bool:
        """
            Method to check if breadcrumb exists on the page

            Args:
                breadcrumb_name (str)  : breadcrumb name
        """
        return self.__is_breadcrumb_exists(breadcrumb_name)

    @PageService()
    def click_breadcrumb(self, breadcrumb_name: str) -> None:
        """
            Method to click on breadcrumb

            Args:
                breadcrumb_name (str)  : breadcrumb name
        """
        self.__click_on_breadcrumb(breadcrumb_name)

    @WebAction()
    def __get_action_list(self):
        """
                   Get the action list

                   Args:
                       action_list (str)  : action list
               """
        xpath = "//div[contains(@id, 'action-list') or contains(@id, 'actionList-menu')]//li"
        action_list = self._driver.find_elements(By.XPATH, xpath)
        return [each_action.text for each_action in action_list]

    @PageService()
    def get_action_list(self):
        """
                           Get the action list

                           Args:
                               action_list (str)  : action list
                       """
        return self.__get_action_list()

    @WebAction()
    def __click_action_item(self, action_item_name:str, case_insensitive_selection=False) -> None:
        """
        Method to click on list items

        Args:
            label (str): title for icon button
        """
        entity_text = "text()"
        if case_insensitive_selection:
            entity_text = "translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
            action_item_name = action_item_name.lower()
        
        xpath = f"//ul[contains(@role, 'menu')]//li[contains(@role, 'menuitem')]//*//div[{entity_text}='{action_item_name}']"
        self._driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def click_action_item_from_menu(self, action_menu_name: str, action_item_name: str, case_insensitive_selection: bool = False) -> None:
        """
        Clicks on the specified action item from the action menu.

        Args:
            action_menu_name (str): The name of the action menu.
            action_item_name (str): The name of the action item.
            case_insensitive_selection (bool, optional): Determines whether the selection is case-insensitive. Defaults to False.
        """
        self.access_page_action(action_menu_name)
        self.__click_action_item(action_item_name, case_insensitive_selection)
