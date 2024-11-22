from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Module has all the features which are present in Manage categories page

CategoryInfo:

    set_description              --         Set description

    set_name                     --         Set name

    switch_anonymous_access      --         Switch anonymous access True/False

    switch_anonymous_download    --         Switch anonymous download True/False

ManageInformation:

    edit_category                --         Edit specified category

    edit_sub_category            --         Edit specified sub category

    search_text                  --         Search for category/Subcategory

    select_category              --         select category

    delete_category              --         Delete a category

    is_category_exist            --         Returns True is category exist else False


"""

from Web.Common.page_object import (
    PageService
)
from selenium.webdriver.common.action_chains import ActionChains
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.Components.dialog import RModalDialog


class ManageInformation:
    """
    Manage information categories and subcategories present in download
    center
    """

    def __init__(self, admin_console: AdminConsole):
        self._driver = admin_console.browser.driver
        self.action = ActionChains(self._driver)
        self._admin_console = admin_console
        self.__tree = TreeView(self._admin_console)

    @PageService()
    def edit_category(self, category_name):
        """
        Edit category
        Args:
            category_name               (String)     --      Category name
        """
        self.__tree.set_search_text(category_name, wait_time= 10)
        self.__tree.perform_action_on_node("Edit category", category_name)
        return CategoryInfo(self._admin_console)

    @PageService()
    def edit_sub_category(self, sub_category_name):
        """
        Edit sub category
        Args:
            sub_category_name           (String)    --       sub category name
        """
        self.__tree.perform_action_on_node("Edit subcategory", sub_category_name)
        return CategoryInfo(self._admin_console)

    @PageService()
    def select_category(self, category_name):
        """
        Expand category to view its subcategories
        Args:
            category_name              (String)     --      name of the category
        """
        self.__tree.expand_node(category_name)

    @PageService()
    def search_text(self, keyword):
        """
        Search for category/subcategory
        Args:
            keyword                (String)      --       name of the category/subcategory
        """
        self.__tree.set_search_text(keyword, wait_time= 10)

    @PageService()
    def delete_category(self, category_name):
        """
        Delete a category
        Args:
            category_name               (String)     --      Category name
        """
        self.__tree.set_search_text(category_name, wait_time=10)
        self.__tree.perform_action_on_node("Delete category", category_name)
        self._admin_console.click_button_using_text('Delete')

    @PageService()
    def is_category_exist(self, category_name):
        """
        Returns True is category exist else False
        Args:
            category_name               (String)     --      Category name
        """
        try:
            element = self._driver.find_element(By.XPATH, f"//*[text()='{category_name}']")
            return True
        except Exception as exp:
            return False


class CategoryInfo:
    """
       Edit Specific category/subcategory details
    """

    def __init__(self, adminconsole: AdminConsole):
        """
        Edit category/subcategory using this class
        Args:
            adminconsole              (Obj)       --           Adminconsole object
        """
        self._driver = adminconsole.browser.driver
        self._adminconsole = adminconsole
        self._modal = RModalDialog(self._adminconsole)

    @PageService()
    def set_name(self, name):
        """
        Set name for category/subcategory
        Args:
            name                     (String)     --      name of category/subcategory
        """
        self._modal.fill_text_in_field("name", name)

    @PageService()
    def set_description(self, description):
        """
        Set description for category/subcategory
        Args:
            description               (String)     --    description of category/subcategory
        """
        self._modal.fill_text_in_field("description", description)

    @PageService()
    def switch_anonymous_access(self, status=True):
        """
        Enable or disable anonymous access
        Args:
            status                     (Bool)      --      True/False
        """
        if status:
            self._modal.enable_toggle('publicView')
        else:
            self._modal.disable_toggle('publicView')

    @PageService()
    def switch_free_downloads(self, status=True):
        """
        Enable or disable free download
        Args:
            status                     (Bool)      --      True/False
        """
        if status:
            self._modal.enable_toggle('publicDownload')
        else:
            self._modal.disable_toggle('publicDownload')

    @PageService()
    def save(self):
        """Save edited category/subcategory"""
        self._modal.click_submit()
