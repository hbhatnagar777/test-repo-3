# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module to manage Commcell group operations.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from AutomationUtils import config, logger
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import RSecurity, RModalDialog
from Web.AdminConsole.Components.table import RptTable

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
    def __init__(self, adminconsole):
        """
        Args:
             adminconsole: AdminConsole object
        """
        self._admin_console = adminconsole
        self._rdropdown = RDropDown(self._admin_console)
        self._rdialog = RModalDialog(self._admin_console)
        self._rtable = RptTable(self._admin_console)
        self._security = RSecurity(self._admin_console)

    @WebAction()
    def _mouse_hover_group(self, group_name):
        """
        Mouse hovers over the group name
        Args:
                group_name (str): commcell group name
        """
        group_item = self._admin_console.driver.find_element(By.XPATH,
                                                             "//a[text()='" + group_name + "']")
        hover = ActionChains(self._admin_console.driver).move_to_element(group_item)
        hover.perform()

    @PageService()
    def access_commcell_group(self, commcell_group_name):
        """
        Access commcell group
        Args:
            commcell_group_name: commcell group name
        """
        self._rtable.access_link(commcell_group_name)

    @WebAction()
    def get_commcell_group_names(self):
        """
        Get the list of commcell group names
        """
        return self._rtable.get_column_data(ColumnNames.GROUP_NAME, fetch_all=True)

    @WebAction()
    def _get_commcell_count(self, commcell_group_name):
        """
        Reads the number of commcells column value for a CommCell group.
        Args:
            commcell_group_name (str): commcell group name
        """
        self._rtable.search_for(commcell_group_name)
        column_data = self._rtable.get_column_data(ColumnNames.NUMBER_OF_COMMCELLS)
        return column_data[0]

    @WebAction()
    def associate_user(self, group_name, user_name):
        """associate user
        Args:
            group_name (str): commcell group name
            user_name (str): user or user group name
        """
        self._rtable.access_action_item(group_name, 'Security')
        self._security.associate_permissions(user_name)

    @PageService()
    def get_details_of_commcells_in_commcell_group(self):
        """
            gets the details of all the commcells listing page
        """
        return self._rtable.get_table_data(all_pages=True)

    @PageService()
    def get_nodata_notification(self):
        """get the display text"""
        return self._admin_console.get_notification()

    @PageService()
    def save(self):
        """save commcell group"""
        self._rdialog.click_submit()

    @PageService()
    def create(self, name, listofcommcells=None, description='Automation Commcell Group'):
        """
        Creates commcell group with given name, description and with list of commcells
        Args:
            name (str): commcell group name
            listofcommcells (list): list of commcells
            description (str): description for the commcell group
        """
        self._rtable.access_toolbar_menu('New CommCell Group')
        self.update_name(name)
        self.update_description(description)
        if listofcommcells:
            self.add_commcells(listofcommcells)
        self.save()
        self._admin_console.check_error_message()

    @PageService()
    def delete(self, commcell_group_name):
        """
        Deletes the given commcell group name
        Args:
                commcell_group_name (str): commcell group name
        """
        if not self.is_group_exist(commcell_group_name):
            return
        self._rtable.access_action_item(commcell_group_name, 'Delete')
        self._rdialog.fill_text_in_field('confirmText', 'CONFIRM')
        self._rdialog.click_submit()

    @PageService()
    def edit(self, commcell_group_name):
        """
        Selects given commcell group and clicks on the edit button.
        Args:
                commcell_group_name (str): commcell group name
        """
        self._rtable.access_action_item(commcell_group_name, 'Edit')


    @PageService()
    def add_commcells(self, list_of_commcells=None):
        """
        Adds given list of commcells to the commcell group.
        Args:
            listofcommcells (list): list of commcells
        """
        if list_of_commcells is not None:
            self._rdropdown.select_drop_down_values(drop_down_id='commcellsDropdown', values=list_of_commcells,
                                                    preserve_selection=True)

    @PageService()
    def update_name(self, newname):
        """
        Updates the name of the commcell group.
        Args:
                newname (str): commcell group name
        """
        self._admin_console.fill_form_by_id("ccName", newname)

    @PageService()
    def update_description(self, description):
        """
        Updates the description of the commcell group.
        Args:
            description (str): description for the commcell group
        """
        self._admin_console.fill_form_by_id("description", description)

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
        return self._rtable.is_entity_present_in_column(ColumnNames.GROUP_NAME,
                                                        commcell_group_name)

    @PageService()
    def get_commcell_group_details(self, group_name):
        """
        Gets the Commcell group details of all column values from group listing page

        Returns:
            dict: details of given group with all column values
        """
        self._rtable.search_for(group_name)
        return self._rtable.get_table_data()
