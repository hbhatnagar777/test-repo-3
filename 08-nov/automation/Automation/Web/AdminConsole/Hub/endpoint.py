from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# -------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on Metallic ring for Laptop
"""
import time
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from Install import installer_constants

class EndPoint():
    """Class to perform operation in metallic Hub for Endpoint"""
    
    def __init__(self, admin_page):
        """Constructor for EndPoint class"""
        self.__admin_console = admin_page
        self.__driver = admin_page.driver
        self.__services = HubServices.endpoint
        self.__hub_dashborad = Dashboard(self.__admin_console,self.__services)
        self._xp = "//table[contains(@class,'packages-table')]"

    @WebAction()
    def __click_on_downloadpackages_option(self):
        """ Method to click on download packages options on hub in Endpoint workload"""
        download_xpath="//span[contains(.,'Download packages')]"
        self.__driver.find_element(By.XPATH, download_xpath).click()
        
    @WebAction()
    def __get_column_names(self):
        """Read all Column names"""
        col_xp = "//th"
        columns = self.__driver.find_elements(By.XPATH, self._xp + col_xp)
        return [column.text for column in columns if column.is_displayed()]
    
    @WebAction(delay=0)
    def __get_data_from_column_by_idx(self, col_idx):
        """Read data from column by index"""
        row_xp = f"//td[{col_idx}]"
        return [
            column.text.strip() for column in
            self.__driver.find_elements(By.XPATH, self._xp + row_xp)
            if column.is_displayed()
        ]
    
    @WebAction()
    def select_hyperlink(self, link_text, index=0):
        """
        Selects hyperlink of the Download for the give package 
        Args:

            link_text       (str)   --  Link name as displayed in the webpage.

            index           (int)   --  Index in case multiple links exist, default is 0.

        Returns:
        """
        link_xp = f'//a[contains(text(),"{link_text}")]'
        self.__driver.find_elements(By.XPATH, link_xp)[index-1].click()
        self.__admin_console.wait_for_completion()
        
    @WebAction()
    def __click_protected_sources(self):
        """Click the device count hyperlink on the Protected Data Sources"""
        xpath="//a[@href='/adminconsole/#/devices']"
        self.__driver.find_element(By.XPATH, xpath).click()
        
    @WebAction()
    def __click_on_advanced_view(self):
        """click on advanced view hyper link"""
        xpath="//a[contains(text(),'Advanced View')]"
        self.__driver.find_element(By.XPATH, xpath).click()
        
    @PageService()
    def download_required_package(self, package_name, column_name='File name'):
        """
        download the package from hub based on selection 
        Args:
            Package_name: Required package to be downloaded
            column_name: Column Name
        Returns:
            list of column data
        """

        column_list = self.__get_column_names()
        if column_list:
            col_idx = column_list.index(column_name) + 1
            column_data = self.__get_data_from_column_by_idx(col_idx)
            row_index=0
            for each_item in column_data:
                row_index = row_index+1
                if each_item ==package_name:
                    self.select_hyperlink('Download',index=row_index)
                    break
                    
        else:
            raise Exception("Unable to get table cloumns list")
        
    @PageService()
    def download_laptop_package(self, package_name):
        """
        Download laptop package 
        """
        self.__click_on_downloadpackages_option()
        self.__admin_console.wait_for_completion()
        executable_package = installer_constants.METALLIC_PACKAGE_EXE_MAP[package_name]
        self.download_required_package(executable_package)
        self.__admin_console.click_button('Back')
        
    @PageService()        
    def login_to_adminconsole(self):
        """
        click on protected resources view from hub to login to adminconsole page
        """
        self.__driver.refresh()
        self.__admin_console.wait_for_completion()
        self.__click_protected_sources()
        self.__admin_console.wait_for_completion()
        
    @PageService()        
    def login_to_dashboard(self):
        """
        Login to dashborad as new tenant admin
        """
        self.__hub_dashborad.click_get_started()
        self.__hub_dashborad.choose_service_from_dashboard()
    @PageService() 
    def get_storage_plan_provisioning(self):
        """
        get the storage and plan provisioning as new tenant
        """
        self.__admin_console.click_button("Continue")
        time.sleep(60)
        self.__admin_console.click_button("OK")
