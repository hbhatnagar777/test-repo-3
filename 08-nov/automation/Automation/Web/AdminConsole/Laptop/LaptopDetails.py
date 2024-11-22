from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
LaptopDetails Page on the AdminConsole

Class:

    LaptopDetails ()

Functions:

extract_laptop_info()                -- Extracts and returns contained information from the laptop

laptop_info()                        -- Returns all information about the laptop

change_laptop_region()               -- Method to change the workload and backup destination region in the details page
"""

from Web.Common.page_object import (WebAction, PageService)
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils import logger
from AutomationUtils.idautils import CommonUtils
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.table import CVTable
from Web.AdminConsole.Components.panel import PanelInfo, RPanelInfo
from Web.AdminConsole.Components.panel import DropDown, RDropDown
from Web.AdminConsole.Components.panel import ModalPanel
from Web.AdminConsole.Components.page_container import PageContainer


class LaptopDetails:
    """
    This class provides the operations that can be performed on LaptopDetails Page of
    admin console
    """
    def __init__(self, admin_page, commcell):
        """
        Method to initiate Laptop class

        Args:
            admin_page   (Object) :   Admin Page Class object
        """
        self.__admin_console = admin_page
        self.__commcell = commcell
        self.__table = Table(self.__admin_console)
        self.__cv_table = CVTable(self.__admin_console)
        self.__driver = admin_page.driver
        self.__drop_down = DropDown(self.__admin_console)
        self.__model_panel = ModalPanel(self.__admin_console)
        self.__job_manager = JobManager(commcell=self.__commcell)
        self.__ida_utils = CommonUtils(self.__commcell)
        self.__navigator = admin_page.navigator
        self.last_online_time = None
        self.last_backupsize = None
        self.__page_container = PageContainer(self.__admin_console)
        self.log = logger.get_log()


    @WebAction()
    def __extract_laptop_info(self):
        """
        Extracts all the information about the laptop

        Args:
            None

        Returns:
            laptop_info (dict) : all info about laptop

        Raises:
            Exception:
                -- if fails to return laptop info
        """
        laptop_info = {}
        elements = self.__admin_console.driver.find_elements(By.XPATH, 
            "//div[@class='page-details group']")

        for elem in elements:
            key = elem.find_element(By.XPATH, "./span").text
            if key == 'Summary':
                summary_values = PanelInfo(self.__admin_console, key).get_details()

                laptop_info.update({key: summary_values})

            elif key == 'Security':
                values_list = []
                div_elements = elem.find_elements(By.XPATH, "./div[@class='tile-accordion ng-scope']")
                for div_elem in div_elements:
                    owners_rows = div_elem.find_elements(By.XPATH, 
                        "//div[@id='tileContent_Security']/div/cv-tabset-component/div/div/ul/li")
                    for each_owner in owners_rows:
                        val = each_owner.find_element(By.XPATH, "./span").text
                        values_list.append(val)
                laptop_info.update({key: values_list})

            elif key == 'Schedules':
                schedule_values = PanelInfo(self.__admin_console, key).get_details()
                laptop_info.update({key: schedule_values})

            elif key == 'Content':
                values_list = elem.find_element(By.XPATH, 
                    "./div[@class='tile-accordion ng-scope']").text.split(',')
                laptop_info.update({key: values_list})

            elif key == 'Plan':
                values_list = []
                values_list = elem.find_element(By.XPATH, 
                    "./div[@class='tile-accordion ng-scope']").text
                laptop_info.update({key: values_list})

        return laptop_info

    @PageService()
    def laptop_info(self, client_name):
        """
        collates and returns all the information about the Laptop

        Returns:
            displayed_val(dict) : displayed values of the laptop

        Raises:
            Exception:
                -- if fails to return displayed_val
        """
        self.__navigator.navigate_to_devices()
        self.__table.access_link(client_name)
        self.__admin_console.wait_for_completion()
        displayed_val = self.__extract_laptop_info()
        self.__admin_console.log.info(displayed_val)
        return displayed_val

    @WebAction()
    def __extract_laptop_region_plan(self):
        """
        Extracts region and plan for the laptop

        Args:
            None

        Returns:
            laptop_info (dict) : info about laptop

        """
        laptop_summary = RPanelInfo(self.__admin_console, 'Summary').get_details()
        laptop_region = laptop_summary.get('Workload region')
        laptop_plan = laptop_summary.get('Plan')
        backup_dest_region = laptop_summary.get('Backup destination region')
        laptop_info = {'Laptop Region': laptop_region, 'Laptop Plan': laptop_plan, 'Backup Destination Region': backup_dest_region}
        return laptop_info

    @WebAction()
    def __change_laptop_workload_region(self, region):
        """
        Changes the workload region for the laptop

        Args:
            region (str) : Name of the region to change into
        """
        rpanel = RPanelInfo(self.__admin_console, "Summary")
        rpanel.edit_tile_entity('Workload region')
        RDropDown(self.__admin_console).select_drop_down_values(values=[region], index=0, partial_selection=True)
        rpanel.click_button('Save')

    @WebAction()
    def __change_laptop_backupdest_region(self, region):
        """
        Changes the backup destination region for the laptop

        Args:
            region (str) : Name of the region to change into
        """
        rpanel = RPanelInfo(self.__admin_console, "Summary")
        rpanel.edit_tile_entity('Backup destination region')
        RDropDown(self.__admin_console).select_drop_down_values(values=[region], index=0, partial_selection=True)
        rpanel.click_button('Save')
        self.__admin_console.click_button('Yes')

    @PageService()
    def laptop_region_plan(self, client_name):
        """
        Extracts region and plan for the laptop

        Returns:
            displayed_info (dict) : info about laptop

        """
        self.__table.access_link(client_name)
        self.__admin_console.wait_for_completion()
        displayed_info = self.__extract_laptop_region_plan()
        self.__admin_console.log.info(displayed_info)
        return displayed_info

    @PageService()
    def change_laptop_region(self, client_name, region_name):
        """
        Method to change the workload and backup destination region in the details page

        Args:
            client_name (str) : Name of the laptop client
            region_name (str) : Name of the region to change into

        Returns:
            None
        """
        self.log.info(f"Changing workload region to {region_name}")
        self.__navigator.navigate_to_devices()
        self.__table.access_link(client_name)
        self.__admin_console.wait_for_completion()
        self.__change_laptop_workload_region(region_name)
        self.log.info(f"Changing backup destination region to {region_name}")
        self.__change_laptop_backupdest_region(region_name)

    @PageService()
    def change_laptop_name(self, name):
        """
        Method to edit laptop's name
        Args:
            name(str): new name of the laptop
        """
        self.__page_container.edit_title(name)
        self.__admin_console.wait_for_completion()
