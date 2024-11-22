# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Regions page on the AdminConsole

Class:

    Regions()

Functions:

_init_()                                :       initialize the class object

__fill_location(self, location)         :       Adds location to location field in the form

__select_location(self, location)       :       Clicks the specified location from location drop-down

__add_location(self, locations)         :       Searches for location from a given list of locations selects it

 __remove_location(self, locations)     :       Removes locations from selected locations

 add_region(self, region_name, region_locations)    :       Method to add a new region

 delete_region(self, region_name)                   :       Method to delete a region

 access_region_details(self, region_name)           :       Method to get the region details

 get_region_locations(self, region_name)            :       Method to get the list of locations under a given region

 edit_region_locations(self, region_name, region_locations)     :       Method to edit locations in given region

 get_associated_servers_plans(self, region_name, server, plan)  :       Method to get the name of the laptops and plans
                                                                        that are associated to the region

 search_for(self, search_string: str)   :       searches a string in the search bar and return all the plans listed

 edit_region_name(self, region_name: str, new_name: str)        :       edits region name
"""
from time import sleep
from selenium.webdriver.common.by import By

from Web.Common.page_object import (WebAction, PageService)
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.page_container import PageContainer


class Regions:
    """ Class for Regions page in Admin Console """

    def __init__(self, admin_console):
        """
        Method to initiate Regions class

        Args:
            admin_console   (Object) :   Admin Console Class object
        """
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__log = admin_console.log
        self.__driver = admin_console.driver
        self.__drop_down = RDropDown(self.__admin_console)
        self.__page_container = PageContainer(admin_console)

    @WebAction()
    def __fill_location(self, location):
        """
        Adds location to location field in the form
        Args:
            location (string):      location name to be added
        """
        location_box = self.__driver.find_element(By.XPATH, '//input[@id="locations"]')
        location_box.click()
        for letter in location:
            location_box.send_keys(letter)

    @WebAction()
    def __select_location(self, location):
        """
        Clicks the specified location from location drop-down
        Args:
            location (string):      location name to be clicked
        """
        location_xpath = f'//li[contains(text(), "{location}")]'
        if self.__admin_console.check_if_entity_exists('xpath', location_xpath):
            self.__driver.find_element(By.XPATH, location_xpath).click()
            return True
        else:
            return False

    @PageService()
    def __add_location(self, locations, search_wait=20):
        """
        Searches for location from a given list of locations selects it

        Args:
            locations (list):   list of locations
            search_wait (int):  seconds to wait for location suggestions
        """
        for location in locations:
            self.__fill_location(location)
            sleep(search_wait)
            if self.__admin_console.check_if_entity_exists('xpath', '//ul[@id="locations-listbox"]'):
                if self.__select_location(location):
                    self.__admin_console.wait_for_completion()
                    self.__log.info('Location {} added'.format(location))
                else:
                    exp = "No such location found"
                    raise CVWebAutomationException(exp)
            else:
                exp = 'Cannot find given location in drop down location suggestions'
                raise CVWebAutomationException(exp)
        try:
            self.__driver.find_element(By.ID, 'name').click()
        except:
            self.__driver.find_element(By.XPATH, "//div[@class='mui-modal-header']/*").click()

    @WebAction()
    def __click_remove_location(self, location):
        """Click the remove button for locations"""
        xpath = f"//span[contains(text(), '{location}')]/following-sibling::*"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __click_tab_region(self, tab_idx):
        """Clicks the appropriate tab in the table to get the details"""
        self.__driver.find_elements(By.XPATH, "//*[contains(@class,'MuiTab-root')]")[tab_idx].click()

    @WebAction()
    def __get_callout_locations(self):
        """Gets the locations from callout"""
        locations = self.__driver.find_elements(
            By.XPATH,
            "//div[contains(@class, 'overflow-list-dropdown')]//span[contains(@class, 'content')]"
        )
        return [elem.text for elem in locations]

    @PageService()
    def __remove_location(self, locations):
        """
        Removes locations from selected locations
        Args:
            locations (list):   list of locations
        """
        for location in locations:
            self.__click_remove_location(location)

    @PageService()
    def add_region(self, region_name, region_type, region_locations):
        """
        Method to add a new region
        Args:
            region_name(string) :   test region name
            region_type(str)    :   type of region to add
            region_locations (list):   list of locations
        """
        self.__admin_console.click_button('Add region')
        self.__admin_console.wait_for_completion()
        self.__admin_console.fill_form_by_name('name', region_name)
        self.__drop_down.select_drop_down_values(values=[region_type], drop_down_id="type")

        self.__add_location(region_locations)
        self.__admin_console.click_button_using_text('Save')
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_region(self, region_name):
        """
        Method to delete a region
        Args:
            region_name(string) :   test region name
        """
        self.__table.access_context_action_item(region_name, 'Delete')
        self.__admin_console.click_button('Yes')

    @PageService()
    def access_region_details(self, region_name):
        """
        Method to get the region details
        Args:
            region_name(string) :   test region name
        """
        self.__table.access_link(region_name)

    @PageService()
    def get_region_locations(self, region_name):
        """
        Method to get the list of locations under a given region
        Args:
            region_name(string) :   test region name
        """
        self.__table.search_for(region_name)
        cell_location_value = self.__table.get_column_data('Location')[0]
        self.__table.access_link_without_text(region_name, 'Location', cell_xp="//button")
        region_locations = self.__get_callout_locations()
        self.__admin_console.click_on_base_body()
        return region_locations + [cell_location_value]

    @PageService()
    def edit_region_locations(self, region_name, region_locations):
        """
        Method to edit locations in given region
        Args:
            region_name(string) :   test region name
            region_locations (dict):   dictionary of locations
        """
        self.__table.access_link(region_name)
        self.__admin_console.click_button('Add locations')
        add_locations = region_locations['Add']
        remove_locations = region_locations['Remove']
        self.__remove_location(remove_locations)
        self.__add_location(add_locations)
        self.__admin_console.click_button('Save')
        self.__admin_console.check_error_message()

    @PageService()
    def get_associated_servers_plans(self, region_name, server=False, plan=False):
        """
        Method to get the name of the laptops and plans that are associated to the region
        Args:
            region_name (str) : Name of the region used for fetching the details
            server (bool)     : Used to select the Server tab
            plan (bool)       : Used to select the Plans tab
        """
        server_idx = 1
        plan_idx = 2
        self.access_region_details(region_name)
        if server:
            self.__click_tab_region(server_idx)
            list_of_laptops = Rtable(self.__admin_console, title='Associated servers').get_column_data('Server name')
            return list_of_laptops
        if plan:
            self.__click_tab_region(plan_idx)
            list_of_plans = Rtable(self.__admin_console, title='Associated region based plans').get_column_data('Plan name')
            return list_of_plans

    @PageService()
    def search_for(self, search_string: str) -> list:
        """
        Method to search a string in the search bar and return all the plans listed
        Args:
            search_string(str): string to search for

        returns:
            list : list of plans matching the string
        """
        self.__table.search_for(search_string)
        res = self.__table.get_column_data(column_name='Name')
        return res

    @PageService()
    def edit_region_name(self, region_name: str, new_name: str):
        """Method to edit region name"""
        self.access_region_details(region_name)
        self.__page_container.edit_title(new_name)
