from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module to manage Commcell group operations.
"""
from time import sleep

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from AutomationUtils import config, logger
from Web.Common.page_object import (WebAction, PageService)
from Web.WebConsole.Reports.cte import Security
from Web.WebConsole.Reports.Metrics.components import MetricsTable


_CONSTANTS = config.get_config()


class ColumnNames:
    """
    Column names present in commcell groups page
    """
    GROUP_NAME = "Group Name"
    NUMBER_OF_COMMCELLS = "Number of CommCells"
    ACTIVE_CLIENTS = "Active Clients"
    ACTIVE_SERVERS = "Active Servers"
    ACTIVE_LAPTOPS = "Active Laptops"
    ACTIVE_VMS = "Active VMs"
    SLA = "SLA (%)"


class CommcellGroup:
    """
    CommcellGroup has the interfaces to do commcell group operations

    is_group_exist  -- checks if given commcell group exists

    create_commcell_group   - creates the commcell group with given inputs i.e. group name,
                              description , list of commcells.

    delete_commcell_group   - deletes the commcell group

    edit_commcell_group     - clicks edit button of the given commcell group

    add_commcells           - adds given list of commcells to the given commcell group

    remove_commcells        - removes given list of commcells from the given commcell group

    """
    def __init__(self, webconsole):
        """
        Args:
             webconsole: WebConsole object
        """
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()
        self._security = Security(self._webconsole)
        self._table = MetricsTable(self._webconsole, None)

    @WebAction()
    def _mouse_hover_group(self, group_name):
        """
        Mouse hovers over the group name
        Args:
                group_name (str): commcell group name
        """
        group_item = self._driver.find_element(By.XPATH, "//a[text()='" + group_name + "']")
        hover = ActionChains(self._driver).move_to_element(group_item)
        hover.perform()

    @WebAction()
    def _click_menu(self):
        """Clicks on the Menu"""
        self._driver.find_element(By.XPATH, ".//*[@id='reportButton']").click()

    @WebAction()
    def _click_create(self):
        """Clicks create new Group in file menu"""
        self._driver.find_element(By.ID, 'createGroup').click()

    @WebAction()
    def _fill_name(self, name):
        """fills the name in new group page"""
        name_elem = self._driver.find_element(By.ID, 'name')
        name_elem.clear()
        name_elem.send_keys(name)

    @WebAction()
    def _fill_description(self, description):
        """fills the description in new group page"""
        desc_elem = self._driver.find_element(By.ID, 'description')
        desc_elem.clear()
        desc_elem.send_keys(description)

    @WebAction()
    def _select_commcells(self, list_of_commcells=None):
        """
        selects the commcells in new group page
        Args:
            list_of_commcells (list): list of commcells
        """

        for commcell_name in list_of_commcells:
            commcell_xp = "//a[text() = '" + commcell_name + "']/../..//input"
            checkbox = self._driver.find_element(By.XPATH, commcell_xp)
            if not checkbox.is_selected():
                checkbox.click()

    @WebAction()
    def _click_save(self):
        """Saves the CommCell group"""
        self._driver.find_element(By.ID, 'submit_new_group_Details').click()

    @WebAction()
    def _click_group_drop_down(self, commcellgroupname):
        """click on group drop down menu to open the actions"""
        self._mouse_hover_group(commcellgroupname)
        open_element = self._driver.find_element(By.XPATH, "//div[@class='openButton']")
        self._browser.click_web_element(open_element)

    @WebAction()
    def _click_delete(self):
        """clicks delete group in Group drop down menu"""
        delete_element = self._driver.find_element(By.CLASS_NAME, 'commcell-action-delete')
        self._browser.click_web_element(delete_element)

    @WebAction()
    def _click_delete_button(self):
        """clicks delete in confirmation pop up"""
        self._driver.find_element(By.XPATH, "//a[@class='deleteButton "
                                           "deleteCommCellGroupBtn']").click()

    @WebAction()
    def _click_edit(self):
        """clicks edit group in Group drop down menu"""
        edit_element = self._driver.find_element(By.CLASS_NAME, 'commcell-action-edit')
        self._browser.click_web_element(edit_element)

    @WebAction()
    def _enable_profile(self):
        """clicks enable profile checkbox in edit group page"""
        checkbox = self._driver.find_element(By.ID, "enableProfile")
        if not checkbox.is_selected():
            checkbox.click()

    @WebAction()
    def _disable_profile(self):
        """clicks disable profile checkbox in edit group page"""
        checkbox = self._driver.find_element(By.ID, "enableProfile")
        if checkbox.is_selected():
            checkbox.click()

    @WebAction()
    def _is_group_exist(self, commcell_group_name):
        """
        checks if given commcell group exists
        Args:
                commcell_group_name (str): commcell group name
        """
        try:
            self._driver.find_element(By.XPATH, "//a[text() = '" + commcell_group_name + "']")
            return True
        except NoSuchElementException:
            return False

    @WebAction()
    def _get_column_names(self):
        """gets column names in commcell groups listing page"""
        enabled_columns_xp = "//table[@id='ccTableWrapper_table']//th"
        return [column.text for column in self._driver.find_elements(By.XPATH, enabled_columns_xp)]

    @WebAction()
    def _get_column_index(self, column_name):
        """
        Get column index for specified column name
        """
        col_idx = self._get_column_names().index(column_name)
        if col_idx < 0:
            raise Exception("Column %s not found", column_name)
        else:
            return col_idx

    @WebAction()
    def _get_filter_objects(self):
        """
        Get all filter objects
        """
        return self._driver.find_elements(By.XPATH, "//input[contains(@id,'ccTableWrapper"
                                                   "_filterText')]")

    @WebAction()
    def apply_filter(self, column_name, filter_string):
        """
        Apply filter in specified column name with filter string
        Args:
            column_name:(string) column name
            filter_string:(String) Filter string
        """
        column_index = self._get_column_index(column_name)
        filter_objects = self._get_filter_objects()
        filter_objects[column_index].send_keys(str(filter_string))
        filter_objects[column_index].send_keys(Keys.ENTER)

    @WebAction()
    def _click_commcell_group(self, commcell_group_name):
        """
        Click on specified commcell group
        Args:
            commcell_group_name: commcell group name to access
        """
        try:
            self._driver.find_element(By.LINK_TEXT, commcell_group_name).click()
        except NoSuchElementException as e:
            raise NoSuchElementException("Commcell group [%s] is not found" % commcell_group_name)\
                from e

    @PageService()
    def access_commcell_group(self, commcell_group_name):
        """
        Access commcell group
        Args:
            commcell_group_name: commcell group name
        """
        self._click_commcell_group(commcell_group_name)
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _get_name_objects(self):
        """
        Get all commcell group name objects present in commcell listing page.
        """
        return self._driver.find_elements(By.XPATH, "//a[@class='ccGroupDrillDown']")

    @WebAction()
    def get_commcell_group_names(self):
        """
        Get the list of commcell group names
        """
        commcell_groups = []
        for each_group in self._get_name_objects():
            commcell_groups.append(each_group.text)
        return commcell_groups

    @WebAction()
    def _read_nodata_notification(self):
        """ read the message"""
        display_label = self._driver.find_elements(By.XPATH, 
            "//div[@id='noDataNotificationPanel']"
        )
        return display_label[0].text

    @WebAction()
    def _get_commcell_count(self, commcell_group_name):
        """
        Reads the number of commcells column value for a CommCell group.
        Args:
            commcell_group_name (str): commcell group name
        """
        col_name = ColumnNames.NUMBER_OF_COMMCELLS
        commcell_count_col_xp = "//a[text()='%s']/..//following-sibling::td[%d]"\
                                % (commcell_group_name, self._get_column_index(col_name))
        return self._driver.find_element(By.XPATH, commcell_count_col_xp).text

    @WebAction()
    def _click_security(self):
        """clicks security in Group drop down menu"""
        security_element = self._driver.find_element(By.CLASS_NAME, 'commcell-action-security')
        self._browser.click_web_element(security_element)

    @WebAction()
    def associate_user(self, group_name, user_name):
        """associate user
        Args:
            group_name (str): commcell group name
            user_name (str): user or user group name
        """
        self._click_group_drop_down(group_name)
        self._click_security()
        self._webconsole.wait_till_load_complete()
        self._security.associate_user(user_name)
        self._security.close()

    @PageService()
    def get_details_of_commcells_in_commcell_group(self):
        """
        gets the number of commcells from commcell listing page of group
        :return:
            dict: Commcell Count and Active Clients Count
        """
        total_active_servers_count = 0
        total_active_laptops_count = 0
        total_active_vms_count = 0
        active_servers = self._table.get_data_from_column(ColumnNames.ACTIVE_SERVERS)
        commcell_listing_values = dict({})
        commcell_listing_values["Commcell Count"] = len(active_servers)
        for active_servers_count in active_servers:
            total_active_servers_count += int(active_servers_count)
        active_laptops = self._table.get_data_from_column(ColumnNames.ACTIVE_LAPTOPS)
        for active_laptops_count in active_laptops:
            total_active_laptops_count += int(active_laptops_count)
        active_vms = self._table.get_data_from_column(ColumnNames.ACTIVE_VMS)
        for active_vms_count in active_vms:
            total_active_vms_count += int(active_vms_count)
        total_active_clients_count = total_active_servers_count + \
                                     total_active_laptops_count + \
                                     total_active_vms_count
        commcell_listing_values["Active Clients Count"] = total_active_clients_count
        return commcell_listing_values

    @PageService()
    def get_nodata_notification(self):
        """get the display text"""
        return self._read_nodata_notification()

    @PageService()
    def save(self):
        """ Save the settings for the commcell group """
        self._click_save()
        self._webconsole.wait_till_load_complete()
        sleep(10)

    @PageService()
    def create(self, name, listofcommcells=None, description='Automation Commcell Group'):
        """
        Creates commcell group with given name, description and with list of commcells
        Args:
            name (str): commcell group name
            listofcommcells (list): list of commcells
            description (str): description for the commcell group
        """
        self._click_menu()
        self._click_create()
        self._webconsole.wait_till_load_complete()
        self._fill_name(name)
        self._fill_description(description)
        if listofcommcells:
            self._select_commcells(listofcommcells)
        self.save()

    @PageService()
    def delete(self, commcell_group_name):
        """
        Deletes the given commcell group name
        Args:
                commcell_group_name (str): commcell group name
        """
        if not self._is_group_exist(commcell_group_name):
            return
        self._click_group_drop_down(commcell_group_name)
        self._click_delete()
        self._click_delete_button()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def edit(self, commcell_group_name):
        """
        Selects given commcell group and clicks on the edit button.
        Args:
                commcell_group_name (str): commcell group name
        """
        self._click_group_drop_down(commcell_group_name)
        self._click_edit()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def add_commcells(self, listofcommcells=None):
        """
        Adds given list of commcells to the commcell group.
        Args:
            listofcommcells (list): list of commcells
        """
        if listofcommcells is not None:
            self._select_commcells(listofcommcells)

    @PageService()
    def update_name(self, newname):
        """
        Updates the name of the commcell group.
        Args:
                newname (str): commcell group name
        """
        self._fill_name(newname)

    @PageService()
    def update_description(self, description):
        """
        Updates the description of the commcell group.
        Args:
            description (str): description for the commcell group
        """
        self._fill_description(description)

    @PageService()
    def enable_profile(self):
        """enable profile check box for commcell group."""
        self._enable_profile()

    @PageService()
    def disable_profile(self):
        """disable profile  for commcell group"""
        self._disable_profile()

    @PageService()
    def commcell_count_of_group(self, commcell_group_name):
        """
        get the number of commcells column value for a commcell group.
        Args:
                commcell_group_name (str): commcell group name
        """
        return self._get_commcell_count(commcell_group_name)

    @PageService()
    def is_group_exist(self, commcell_group_name):
        """
        checks if given commcell group exists
        Args:
                commcell_group_name (str): commcell group name
        """
        return self._is_group_exist(commcell_group_name)

    @PageService()
    def get_commcell_group_details(self, group_name):
        """
        Gets the Commcell group details of all column values from group listing page

        Returns:
            dict: details of given group with all column values
        """
        commcell_listing_values = {}
        visible_columns = self._table.get_visible_column_names()
        self._table.set_filter(ColumnNames.GROUP_NAME, group_name)
        for each_column in visible_columns:
            commcell_listing_values[each_column] = self._table.get_data_from_column(each_column)[0]
        return commcell_listing_values
