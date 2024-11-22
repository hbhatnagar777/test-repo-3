# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""

This module provides the function or operations that can be performed on the global exceptions page

Class:
      GlobalExceptions()

Functions :
   __init__()                       -> Method to initiate Global exceptions class

   __create_global_filter()         -> Protected method to create a global exception filter

   __modify_global_filter()         -> Protected method to edit the global exception filter

   open_global_filter()             -> Method to open global exceptions page

   add_global_filter()              -> Method to create windows or unix global filter

   edit__global_filter()            -> Method to modify the windows or unix global filter

   delete_global_filter()           -> Method to delete the windows or unix global filter

"""
from selenium.webdriver.common.by import By
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Table


class GlobalExceptions:
    """ class for the global exceptions page """

    def __init__(self, admin_page):
        """
        Method to initiate Global exceptions class

        Args:
            admin_page   (Object) :   Admin Page Class object
        """
        self.__admin_console = admin_page
        self.__admin_console.load_properties(self)
        self.__table = Table(admin_page)
        self.__driver = admin_page.driver

    @WebAction()
    def __create_global_filter(self, global_filter_path):
        """
        Method to create a global filter
        Args:
            global_filter_path(dict): dictionary with the global filter path to be added
              Eg.- global_filter_path = {'windows_global_filter_path' : "c\\test", 'unix_global_filter_path' :
                                                         "/root/test.txt" }
        Returns:
            None
        Raises:
            Exception:
                if failed to create a global filter
         """

        if global_filter_path['windows_global_filter_path']:
            if self.__admin_console.check_if_entity_exists("xpath",
                                                           "//div[@id='windowsGlobalExceptionsTable']/div/div/div/div/"
                                                           "ul/li[@id='toolbar-menu_Add']"):
                self.__driver.find_element(By.XPATH, 
                    "//div[@id='windowsGlobalExceptionsTable']/div/div/div/div/ul/li[@id='toolbar-menu_Add']").click()
                self.__admin_console.wait_for_completion()
            else:
                exp = "Add windows global filter operation is failed"
                self.__admin_console.log.exception(exp)
                raise Exception(exp)
            self.__admin_console.fill_form_by_id("filterAddData", global_filter_path['windows_global_filter_path'])
            self.__admin_console.submit_form()
            self.__admin_console.log.info("windows global filter was created successfully.")

        if global_filter_path['unix_global_filter_path']:
            if self.__admin_console.check_if_entity_exists("xpath", "//li[@id='toolbar-menu_Add']/span/a[@id='Add']"):
                self.__admin_console.driver.find_element(By.XPATH, 
                    "//li[@id='toolbar-menu_Add']/span/a[@id='Add']").click()
                self.__admin_console.wait_for_completion()
            else:
                exp = "Add unix global filter operation is failed"
                self.__admin_console.log.exception(exp)
                raise Exception(exp)
            self.__admin_console.fill_form_by_id("filterAddData", global_filter_path['unix_global_filter_path'])
            self.__admin_console.submit_form()
            self.__admin_console.log.info("Unix global filter was created successfully")

    @WebAction()
    def __modify_global_filter(self, global_filter_path, new_global_filter_path=None):
        """
        Method to modify an existing  global filter
        Args:
            global_filter_path(dict): dictionary for path of the existing  global filter
            new_global_filter_path(dict):dictionary for  new path of the  global filter
             Eg:- new_global_filter_path = {'new_windows_global_filter_path': "*.bat" ,
                'new_unix_global_filter_path': "**temp*"}
        Returns:
            None
        Raises :
            Exception:
                 if failed to modify the  global filter
        """

        if new_global_filter_path['windows_global_filter_path']:
            self.open_global_filter(global_filter_path['windows_global_filter_path'])
            self.__admin_console.fill_form_by_id("filterEditData",
                                                 new_global_filter_path['windows_global_filter_path'])
            self.__admin_console.submit_form()
            self.__admin_console.log.info("Editing completed for Windows global filter path")

        if new_global_filter_path['unix_global_filter_path']:
            self.open_global_filter(global_filter_path['unix_global_filter_path'])
            self.__admin_console.fill_form_by_id("filterEditData", new_global_filter_path['unix_global_filter_path'])
            self.__admin_console.submit_form()
            self.__admin_console.log.info("Editing completed for Unix global filter path")

    @PageService()
    def open_global_filter(self, global_filter_path):
        """Method to open global exceptions"""

        self.__admin_console.select_hyperlink(global_filter_path)

    @PageService()
    def add_global_filter(self, global_filter_path):
        """
        Method to create a global filter
        Args:
            global_filter_path(dict): dictionary with the global filter path to be added
              Eg.- global_filter_path = {'windows_global_filter_path' : "c\\test", 'unix_global_filter_path' :
                                                         "/root/test.txt" }
        Returns:
            None
        Raises:
            Exception:
                if failed to create a global filter
         """
        self.__create_global_filter(global_filter_path)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_global_filter(self, global_filter_path, new_global_filter_path=None):
        """
        Method to modify an existing  global filter
        Args:
            global_filter_path(dict): dictionary for path of the existing  global filter
            new_global_filter_path(dict):dictionary for  new path of the  global filter
             Eg:- new_global_filter_path = {'new_windows_global_filter_path': "*.bat" ,
                'new_unix_global_filter_path': "**temp*"}
        Returns:
            None
        Raises :
            Exception:
                 if failed to modify the  global filter
        """
        self.__modify_global_filter(global_filter_path, new_global_filter_path)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_global_filter(self, global_filter_path):
        """
        Method to delete a global filter

        Args:
            global_filter_path(dict) :dictionary for global filter path to be deleted
        Returns:
            None
        Raises:
            Exception :
                if failed delete the global filter path
        """
        if global_filter_path['windows_global_filter_path']:
            self.__table.access_context_action_item(global_filter_path['windows_global_filter_path'], 'DELETE')
            self.__admin_console.click_yes_button()
            self.__admin_console.check_error_message()
        if global_filter_path['unix_global_filter_path']:
            self.__table.access_context_action_item(global_filter_path['unix_global_filter_path'], 'DELETE')
            self.__admin_console.click_yes_button()
            self.__admin_console.check_error_message()
