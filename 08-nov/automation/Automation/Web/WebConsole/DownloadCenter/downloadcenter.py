from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Module has all the features which are present in downloadcenter page.

DownloadCenter:

    access_category              --  Access category link present on download center

    access_manage_information    --  Access manage insformation

    access_sub_Category          --  Access sub category

    download_package             --  Download specified packages

    get_package_list             --  Get packages list

    is_subcategory_exists        --  check if specified subcategory exists

    search_package_keyword       --  Search for package keyword in search bar

"""

from selenium.webdriver.common.keys import Keys

from AutomationUtils import config
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.WebConsole.DownloadCenter.settings import ManageInformation
from Web.WebConsole.webconsole import WebConsole

_CONFIG = config.get_config()


class DownloadCenter:
    """
    Class contains download center operations
    """

    def __init__(self, web_console: WebConsole):
        self._driver = web_console.browser.driver
        self._web_console = web_console

    @property
    def download_center_url(self):
        """download center url"""
        return self._web_console.base_url + "downloadcenter/dc.do?ps=10&q=&type=dc"

    @WebAction()
    def _click_manage_information(self):
        """
        click on manage information
        """
        self._driver.find_element(By.XPATH, "//a[@id='ManageCategory"
                                           "SubcategoryButton']").click()

    @WebAction()
    def _set_search_keyword_text(self, search_keyword):
        """
        Set search keyword
        Args:
            search_keyword               (String)        --        Keyword to be searched
        """
        self._driver.find_element(By.XPATH, "//input[@id='packageKeyword']").clear()
        self._driver.find_element(By.XPATH, "//input[@id='"
                                           "packageKeyword']").send_keys(search_keyword)
        self._driver.find_element(By.XPATH, "//input[@id="
                                           "'packageKeyword']").send_keys(Keys.RETURN)

    @WebAction()
    def _click_download_package(self, package_name):
        """
        Click on download of package
        Args:
            package_name               (String)        --        Package Name to be downloaded
        """
        self._driver.find_element(By.XPATH, "//div/a[text() = '%s']"
                                           "/../../..//button" % package_name).click()

    @WebAction()
    def _click_category(self, category_name):
        """
        click on specified category
        Args:
            category_name               (String)      --    Category name
        """
        self._driver.find_element(By.XPATH, "//a[@data-facettype='CATEGORY_NAME']"
                                           "/../../li[@title = '%s']"
                                           "/a" % category_name).click()

    @WebAction()
    def _click_sub_category(self, category_name):
        """
        click on specified category
        Args:
            category_name               (String)      --    Category name
        """
        self._driver.find_element(By.XPATH, "//a[@data-facettype='SUBCATEGORY_NAME']"
                                           "/../../li[@title = '%s']"
                                           "/a" % category_name).click()

    @WebAction()
    def _get_subcategories(self):
        """
        Get all subcategories list
        """
        categories = []
        sub_categories = self._driver.find_elements(By.XPATH, "//*[@id='facetList_"
                                                             "SUBCATEGORY_NAME']/li/a")
        for each_category in sub_categories:
            categories.append(each_category.get_attribute('data-value'))
        return categories

    @WebAction()
    def _get_package_list(self):
        """Get list of packages in present page"""
        package_list = []
        packages = self._driver.find_elements(By.XPATH, "//*[@id='packageResultGrid']"
                                                       "//a[@class='aCursor']")
        for each_package in packages:
            package_list.append(each_package.text)
        return package_list

    @PageService()
    def access_manage_information(self):
        """
        Access manage information
        """
        self._click_manage_information()
        self._web_console.wait_till_load_complete()
        return ManageInformation(self._web_console)

    @PageService()
    def search_package_keyword(self, search_keyword):
        """
        Search for package with specified keyword
        Args:
            search_keyword                  (String)      --       Keyword to be searched
        """
        self._set_search_keyword_text(search_keyword)
        self._web_console.wait_till_load_complete()

    @PageService()
    def download_package(self, package_name):
        """
        Download package
        Args:
            package_name                     (String)     --       Name of the package
        """
        self._click_download_package(package_name)

    @PageService()
    def access_category(self, category_name):
        """
        Access category
        Args:
            category_name               (String)      --    Category name
        """
        self._click_category(category_name)
        self._web_console.wait_till_load_complete()

    @PageService()
    def access_sub_category(self, sub_category_name):
        """
        Access sub category
        Args:
            sub_category_name           (String)    --      Sub category name
        """
        self._click_sub_category(sub_category_name)
        self._web_console.wait_till_load_complete()

    @PageService()
    def is_subcategory_exists(self, sub_category):
        """Check specified sub category exists"""
        return sub_category in self._get_subcategories()

    @PageService()
    def get_package_list(self):
        """Get packages list"""
        return self._get_package_list()
