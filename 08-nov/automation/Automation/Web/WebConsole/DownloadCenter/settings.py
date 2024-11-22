from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Module has all the features which are present in Manage information page

CategoryInfo:

    set_description              --         Set description

    set_name                     --         Set name

    switch_anonymous_access      --         Switch anonymous access True/False

    switch_anonymous_download    --         Switch anonymous download True/False

ManageInformation:

    edit_category                --         Edit specified category

    edit_sub_category            --         Edit specified sub category

    seach_category               --         Search for category

    select_category              --         select category


"""

from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.WebConsole.webconsole import WebConsole


class ManageInformation:
    """
    Manage information categories and subcategories present in download center
    """

    def __init__(self, web_console: WebConsole):
        self._driver = web_console.browser.driver
        self._web_console = web_console

    @WebAction()
    def _click_category(self, category_name):
        """
        Click on specified category
        Args:
            category_name                   (String)    --       category name
        """
        self._driver.find_element(By.XPATH, "//td[@class=' categoryName' and text() = '%s']" %
                                           category_name).click()

    @WebAction()
    def _click_edit(self, section, category_name):
        """
        Click on edit
        Args:
            section                     (String)     --       category/sub category
            category_name               (String)     --       name of the category/subcategory
        """
        self._driver.find_element(By.XPATH, "//*[@class='%s' and text() = '%s']/"
                                           "..//button[text() = "
                                           "'Edit' ]" % (section, category_name)).click()

    @WebAction()
    def _click_delete(self, section, category_name):
        """
        Click on edit
        Args:
            section                     (String)     --       category/sub category
            category_name               (String)     --       name of the category/subcategory
        """
        self._driver.find_element(By.XPATH, "//*[@class='%s' and text() = '%s']/"
                                           "..//button[text() = "
                                           "'Delete' ]" % (section, category_name)).click()

    @WebAction()
    def _click_properties(self, section, category_name):
        """
        Click on edit
        Args:
            section                     (String)     --       category/sub category
            category_name               (String)     --       name of the category/subcategory
        """
        self._driver.find_element(By.XPATH, "//*[@class='%s' and text() = '%s']/"
                                           "..//button[text() = "
                                           "'Properties' ]" % (section, category_name)).click()

    @WebAction()
    def _set_search_text_manage_category(self, keyword):
        """
        Set search text in manage category
        Args:
            keyword                     (String)     --       Keyword to be searched
        """
        self._driver.find_element(By.XPATH, "//*[@id="
                                           "'categoryTable_filter']//input").clear()
        self._driver.find_element(By.XPATH, "//*[@id="
                                           "'categoryTable_filter']//input").send_keys(keyword)

    @WebAction()
    def _set_search_text_manage_sub_category(self, keyword):
        """
        Set search text in manage category
        Args:
            keyword                     (String)     --       Keyword to be searched
        """
        self._driver.find_element(By.XPATH, "//*[@id="
                                           "'subCategoryTable_filter']//input").clear()
        self._driver.find_element(By.XPATH, "//*[@id="
                                           "'subCategoryTable_filter']"
                                           "//input").send_keys(keyword)

    @PageService()
    def search_category(self, category):
        """
        Search for category
        Args:
            category                  (String)      --       name of the category
        """
        self._set_search_text_manage_category(category)

    @PageService()
    def edit_category(self, category_name):
        """
        Edit category
        Args:
            category_name               (String)     --      Category name
        """
        self._set_search_text_manage_category(category_name)
        self._click_edit("categoryName", category_name)
        return CategoryInfo(self._web_console, category=CategoryInfo.CATEGORY)

    @PageService()
    def edit_sub_category(self, sub_category_name):
        """
        Edit sub category
        Args:
            sub_category_name           (String)    --       sub category name
        """
        self._set_search_text_manage_sub_category(sub_category_name)
        self._click_edit(" subCategoryName", sub_category_name)
        return CategoryInfo(self._web_console, category=CategoryInfo.SUB_CATEGORY)

    @PageService()
    def select_category(self, category_name):
        """
        Click on category
        Args:
            category_name              (String)     --      name of the category
        """
        self._click_category(category_name)


class CategoryInfo:
    """
    Edit Specific category details
    """
    CATEGORY = "category"
    SUB_CATEGORY = "sub_category"

    CATEGORY_XP = "add"
    SUBCATEGORY_XP = "addSub"

    def __init__(self, webconsole: WebConsole, category):
        """
        Edit category/subcategory using this class
        Args:
            webconsole              (Obj)       --           Webconsole object
            category                (String)    --           select category from call Category
                                                             (CATEGORY/SUB_CATEGORY)
        """
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole
        if category == self.CATEGORY:
            self._xp = self.CATEGORY_XP
        else:
            self._xp = self.SUBCATEGORY_XP

    @WebAction()
    def _set_name(self, name):
        """
        Set name
        Args:
            name                (String)      --        Set name
        """
        self._driver.find_element(By.XPATH, "//*[@id='%sCategoryName']" % self._xp).clear()
        self._driver.find_element(By.XPATH, "//*[@id="
                                           "'%sCategoryName']" % self._xp).send_keys(name)

    @WebAction()
    def _set_description(self, description):
        """
        Set name
        Args:
            description                (String)      --        Set description
        """
        self._driver.find_element(By.XPATH, "//*[@id="
                                           "'%sCategoryDescription']" % self._xp).clear()
        self._driver.find_element(By.XPATH, "//*[@id='%sCategoryDescription']" %
                                           self._xp).send_keys(description)

    @WebAction()
    def _click_anonymous_access(self):
        """
        Click on anonymous access
        """
        self._driver.find_element(By.XPATH, "//*[@id='anonymous-sc-access-switch']").click()

    @WebAction()
    def _click_free_downloads(self):
        """
        Click on anonymous access
        """
        self._driver.find_element(By.XPATH, "//*[@id='free-sc-downloads-switch']").click()

    @WebAction()
    def _get_anonymous_access_status(self):
        """
        Get anonymous access is enabled or disabled
        """
        status = self._driver.find_elements(By.XPATH, "//*[contains(@id, 'anonymous-sc-access"
                                                     "-switch') and contains(@class, "
                                                     "'icon-switch-yes')]")
        if status:
            return True
        return False

    @WebAction()
    def _get_free_download_status(self):
        """
        Get anonymous download is enabled or disabled
        """
        status = self._driver.find_elements(By.XPATH, "//*[@id='free-downloads-switch' and "
                                                     "contains(@class, 'icon-switch-yes')]")
        if status:
            return True
        return False

    @WebAction()
    def _click_save(self):
        """Click save"""
        self._driver.find_element(By.XPATH, "//button[text() = 'Save']").click()

    @PageService()
    def set_name(self, name):
        """
        Set name for category/subcategory
        Args:
            name                     (String)     --      name of category/subcategory
        """
        self._set_name(name)

    @PageService()
    def set_description(self, description):
        """
        Set name for category/subcategory
        Args:
            description               (String)     --    description of category/subcategory
        """
        self._set_description(description)

    @PageService()
    def switch_anonymous_access(self, status=True):
        """
        Enable or disable anonymous access
        Args:
            status                     (Bool)      --      True/False
        """
        existing_status = self._get_anonymous_access_status()
        if (existing_status is True and status is True) or (existing_status is False and
                                                            status is False):
            return
        self._click_anonymous_access()

    @PageService()
    def switch_free_downloads(self, status=True):
        """
        Enable or disable free download
        Args:
            status                     (Bool)      --      True/False
        """
        existing_status = self._get_free_download_status()
        if (existing_status is True and status is True) or (existing_status is False and
                                                            status is False):
            return
        self._click_free_downloads()

    @PageService()
    def save(self):
        """Save edited subcategory"""
        self._click_save()
