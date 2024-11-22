from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides method to check status of vm on multiple parameters.

Classes:

    VMStatus() ---> _Navigator() ---> AdminConsoleBase() ---> Object()

VMStatus() -- This class provides methods to check status of vm on multiple parameters.
Functions:

    get_listed_vm()      -- This return dict {vmname:[status,size,backupsize,collection,
                            lastbackuptime]}.

    time_range()         -- Selecting the time range

    select_subclient()   -- Displays the VMs backed up by the Subclient chosen

    select_status()      -- Displays only the VMs with the chosen status from the list of VMs in
                            the server

    select_vm()          -- Opens the VM details page

    back_to_hypervisor() -- Brings the control back to hypervisor page

"""
from selenium.webdriver.support.ui import Select
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService


class VMStatus:
    """
    This class provides methods to check status of vm on multiple parameters.
    """

    def __init__(self, admin_console):
        """ """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__table_obj = Table(admin_console)

    @PageService()
    def get_listed_vm(self):
        """
        This return dict {vmname:[status,size,backupsize,collection,lastbackuptime]}
        """
        self.__admin_console.log.info("The details of the backed up VM like status, size, backupsize, \
            collection and lastbackuptime")
        vm_list = {}
        while True:
            element_list = self.__driver.find_elements(By.XPATH, 
                "//div[@class='ui-grid-canvas']/div")
            element_count = len(element_list)
            for index in range(1, element_count + 1):
                if element_count == 1:
                    elem_text = self.__driver.find_element(By.XPATH, 
                        "//div[@class='ui-grid-canvas']/div/div/div[1]/div/a").text
                else:
                    elem_text = self.__driver.find_element(By.XPATH, 
                        "//div[@class='ui-grid-canvas']/div[" +
                        str(index) + "]/div/div[1]/div").text
                temp = []
                for num in range(2, 7):
                    temp.append(
                        self.__driver.find_element(By.XPATH, 
                            "//div[@class='ui-grid-canvas']/div[" +
                            str(index) + "]/div/div[" + str(num) + "]/div").text)
                    num += 1
                vm_list[elem_text] = temp
                index += 1
            if self.__admin_console.cv_table_next_button_exists():
                if self.__driver.find_element(By.XPATH, 
                        "//button[@ng-disabled='cantPageForward()']").is_enabled():
                    self.__admin_console.cv_table_click_next_button()
                    self.__admin_console.wait_for_completion()
                else:
                    break
            else:
                break
        self.__admin_console.log.info(vm_list)
        return vm_list

    @PageService()
    def time_range(self, t_range, from_date=None, to_date=None):
        """
        Seleting the time range
        """
        self.__admin_console.log.info("Seleting the time range")
        Select(self.__driver.find_element(By.ID, 
            "time-range-select")).select_by_visible_text(t_range)
        if t_range == "Custom":
            self.__driver.find_element(By.XPATH, 
                "//span[@id='time-range-wrapper]/input[1]").clear()
            self.__driver.find_element(By.XPATH, 
                "//span[@id='time-range-wrapper]/input[1]").send_keys(from_date)
            self.__driver.find_element(By.XPATH, 
                "//span[@id='time-range-wrapper]/input[2]").clear()
            self.__driver.find_element(By.XPATH, 
                "//span[@id='time-range-wrapper]/input[2]").send_keys(to_date)
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_subclient(self, subclient_name):
        """
        Displays the VMs backed up by the Subclient chosen

        Args:
            subclient_name  (str):   Name of the subclient to open

        """
        self.__admin_console.log.info("Opening subclient %s", subclient_name)
        Select(self.__driver.find_element(By.XPATH, 
            "//div[@id='wrapper']/div/div/span/div/div/label[2]/select") \
            ).select_by_visible_text(subclient_name)
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_status(self, status):
        """
        Displays only the VMs with the chosen status from the list of VMs in the server

        Args:
            status  (str):   the VM of the specific status to open

        """
        self.__admin_console.log.info("Selecting VMs of status %s", status)
        Select(self.__driver.find_element(By.XPATH, 
            "//div[@class='group filter-options']/label[1]/select" \
            )).select_by_visible_text(status)
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_vm(self, vm_name):
        """
        Opens the VM details page

        Args:
            vm_name (str):   the name of the VM to open

        """
        self.__admin_console.log.info("Opening VM %s", vm_name)
        self.__driver.find_element(By.XPATH, "//input[@id='search-field']").clear()
        self.__driver.find_element(By.XPATH, "//input[@id='search-field']").send_keys(vm_name)
        self.__admin_console.wait_for_completion()
        if self.__admin_console.check_if_entity_exists("xpath", "//a[contains(text(),'" + vm_name + "')]"):
            self.__driver.find_element(By.XPATH, 
                "//a[text()='" + vm_name + "']").click()
            self.__admin_console.wait_for_completion()
        else:
            raise Exception("The specified VM is not available in the chosen collection "
                            "and status")

    @PageService()
    def back_to_hypervisor(self):
        """
        Brings the control back to hypervisor page
        """
        self.__admin_console.log.info("Going back to the server")
        if self.__admin_console.check_if_entity_exists(
                "xpath", "//div[@class='nav-breadcrumbs group ng-scope' \
                ]/div/span/ul[1]/li[2]/a"):
            self.__driver.find_element(By.XPATH, 
                "//div[@class='nav-breadcrumbs group ng-scope']/div/span/ul[1]/li[2]/a").click()
            self.__admin_console.wait_for_completion()
        else:
            raise Exception("There is no option to go back to the servers")
