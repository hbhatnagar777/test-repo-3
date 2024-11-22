# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module to manage Commcell operations.
"""
from selenium.webdriver.common.by import By
from AutomationUtils import config, logger
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import RSecurity, RModalDialog
from Web.AdminConsole.Components.table import RptTable

_CONSTANTS = config.get_config()




class Commcell:
    """
    Commcell has the interfaces to do commcell operations

    is_commcell_exist  -- checks if given commcell  exists

    delete_commcell    - deletes the commcell

    edit_commcell_name     - edit commcell name

    access_command_center  - access command center of the commcell


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
        self._page_container = PageContainer(self._admin_console)
        self._log = logger.get_log()

    @WebAction()
    def _is_commcell_exist(self, commcell_name):
        """
        checks if given commcell exists
        Args:
                commcell_name (str): commcell name
        """
        commcell_exists = self._rtable.is_entity_present_in_column('CommCell Name',
                                                                 commcell_name)
        if not commcell_exists:
            raise Exception('CommCell not found')
        return commcell_exists

    @PageService()
    def access_commcell(self, commcell_name):
        """
        Access commcell
        Args:
            commcell_name: commcell name
        """
        self._rtable.access_link(commcell_name)

    @PageService()
    def goto_commcell_tab(self):
        """
        click commcell tab
        """
        self._page_container.select_tab(tab_name='CommCells')

    @WebAction()
    def get_commcell_names(self):
        """
        Get the list of commcell  names
        """
        return self._rtable.get_column_data('CommCell Name', fetch_all=True)

    @WebAction()
    def _is_it_single_commcell(self):
        """
        check the user have only one Commcell
        Returns: True or False
        """
        commcell_count= len(self.get_commcell_names())
        if commcell_count ==1:
            return True
        return False

    @WebAction()
    def associate_user(self, commcell_name, user_name):
        """associate user
        Args:
            commcell_name (str): commcell name
            user_name (str): user or user group name
        """
        self._rtable.access_action_item(commcell_name, 'Security')
        self._security.associate_permissions(user_name)

    @PageService()
    def is_it_single_commcell(self):
        """
        check the user have only one Commcell

        Returns: True or False
        """
        self._is_it_single_commcell()

    @PageService()
    def get_nodata_notification(self):
        """get the display text"""
        return self._admin_console.get_notification()

    @PageService()
    def save(self):
        """save commcell group"""
        return self._rdialog.click_submit()


    @PageService()
    def delete(self, commcell_name):
        """
        Deletes the given commcell name
        Args:
                commcell_group_name (str): commcell name
        """
        if not self.is_commcell_exist(commcell_name):
            return
        self._rtable.access_action_item(commcell_name, 'Delete')
        self._rdialog.fill_text_in_field('confirmText', 'CONFIRM')
        self._rdialog.click_submit()

    @PageService()
    def edit(self, commcell_name):
        """
        Selects given commcell  and clicks on the edit button.
        Args:
                commcell_name (str): commcell  name
        """
        self._rtable.access_action_item(commcell_name, 'Edit CommCell name')

    @PageService()
    def access_command_center(self, commcell_name):
        """
        Selects given commcell  and clicks on the command center button.
        Args:
                commcell_name (str): commcell  name
        """
        self._rtable.access_action_item(commcell_name, 'Command Center')

    @PageService()
    def update_name(self, newname):
        """
        Updates the name of the commcell .
        Args:
                newname (str): commcell  name
        """
        self._admin_console.fill_form_by_id('ccname', newname)
        self._admin_console.click_button_using_text('Save')

    @PageService()
    def is_commcell_exist(self, commcell_name):
        """
        checks if given commcell exists
        Args:
                commcell__name (str): commcell name
        """
        return self._is_commcell_exist(commcell_name)

