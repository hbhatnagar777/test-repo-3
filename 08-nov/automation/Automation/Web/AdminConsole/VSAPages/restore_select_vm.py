from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods for opening the vm, selecting files for restore and selecting the
destinations. It is inherited by different types of restore.


Classes:

    RestoreSelectVM() ---> _Navigator() --->  AdminConsoleBase() ---> Object()


RestoreSelectVM --  This class contains all the methods for opening the vm, selecting files
                    for restore and selecting the destinations.
    Functions:

    select_vm()                 -- Opens the given VM
    backup_for_specific_date()  -- Shows backup content as of a specific date
    backup_for_date_range()     -- Shows backup content in a time range
"""
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import WebAction, PageService


class RestoreSelectVM:
    """
    This class contains all the methods for opening the vm, selecting files for restore and
    selecting the destinations.
    """
    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__table = Table(admin_console)

    @PageService()
    def select_vm(self, vm_name):
        """
        Opens the given VM

        Args:
            vm_name (str): vm to be selected
        """
        self.__table.access_link(vm_name)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def backup_for_specific_date(
            self,
            time_value):
        """
        Shows backup content as of a specific date

        Args:
            time_value (dict): dictionary containing the value to set as date range
                    Sample dict:    {   'year':     '2017',
                                    'month':    December,
                                    'date':     '31',
                                    'hours':    '09',
                                    'mins':     '19',
                                    'session':  'AM'
                                }
        """
        self.__admin_console.log.info("Displaying backup data as of a specific date")
        self.__driver.find_element(By.XPATH, 
            "//div[@data-ng-controller='browseOptionsController']/span/a").click()
        self.__driver.find_element(By.XPATH, 
            "//div[@data-ng-controller='browseOptionsController']/span/ul/li[1]/a").click()

        self.__admin_console.date_picker(time_value, "to-picker")

        self.__driver.find_element(By.XPATH, 
            "//div[3]/button[contains(text(),'OK')]").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def backup_for_date_range(
            self,
            from_time,
            to_time):
        """
        Shows backup content in a time range

        Args:
            from_time (dict):  dictionary containing the value to be set as from time
            to_time (dict)  :  dictionary containing the value to be set as to time
                     Sample dict:    {   'year':     2017,
                                    'month':    12,
                                    'date':     31,
                                    'hours':    09,
                                    'mins':     19,
                                    'session':  'AM'
                                }
        """
        self.__driver.find_element(By.XPATH, 
            "//div[@data-ng-controller='browseOptionsController']/span/a").click()
        self.__driver.find_element(By.XPATH, 
            "//div[@data-ng-controller='browseOptionsController']/span/ul/li[1]/a").click()

        self.__admin_console.date_picker(from_time, "from-picker")

        # To Time
        self.__admin_console.date_picker(to_time, "to-picker")

        self.__driver.find_element(By.XPATH, 
            "//div[3]/button[contains(text(),'OK')]").click()
        self.__admin_console.wait_for_completion()
