# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Object storage Account details page

ObjectDetails
    get_details                 --      returns details of client

    get_content_groups          --      gets all visbile client names

    create_content_group        --      Creates content group

    access_content_group        --      Selects the content group

    submit_backup               --      submits backup job

    access_restore              --      Acesses restore for browse

    submit_restore              --      Submits restore job

    delete_account              --      Delete account
    
    get_content_group_contents  --      retrieves the contents of the subclient

_AddContentGroup
    add                         --      Adds Content group

"""
from Web.Common.page_object import (
    PageService,
    WebAction
)
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.dialog import RModalDialog, RBackup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.ObjectStorage.clients.restore_panels import RestoreOptions
from Web.AdminConsole.Components.page_container import PageContainer
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.wizard import Wizard


class ObjectDetails:
    """Class for Object storage Accounts details page"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        self._admin_console = admin_console
        self.driver = self._admin_console.driver
        self.__table = Rtable(self._admin_console)
        self.__panel = RPanelInfo(admin_console)
        self.__browse = RBrowse(self._admin_console)
        self.__page_container = PageContainer(self._admin_console)
        self._dialog = RModalDialog(self._admin_console)

    def __click_add_content_group(self):
        """Add content group"""
        self.__page_container.click_on_button_by_text(self._admin_console.props['pageHeader.addContentGroup'])

    @WebAction()
    def __get_elements_of_content_group(self):
        """returns elements of content group tile"""
        self.__table.expand_row("default")
        return self._admin_console.driver.find_elements(By.XPATH, "//div[@id='Contents']/ul/li/div/div/span")

    @PageService
    def get_details(self):
        """returns details of client"""
        return self.__panel.get_details()

    @PageService()
    def get_content_groups(self):
        """
        gets all visbile client names
        """
        return self.__table.get_column_data(self._admin_console.props['label.name'])

    @PageService()
    def create_content_group(self, name, plan, content_path):
        """
        Create content group
        Args:
            name (str): content group name
            plan (str): plan
            content_path (list): content

        """
        self.__click_add_content_group()
        _AddContentGroup(self._admin_console).add(name, plan, content_path)
        self._admin_console.check_error_message()

    @PageService()
    def access_content_group(self, content_group_name):
        """
        Selects the content group
        Args:
            content_group_name (str): Content group Name
        """
        if content_group_name in self.get_content_groups():
            self._admin_console.select_hyperlink(content_group_name)

    @PageService()
    def submit_backup(self, group_name, backup_type=RBackup.BackupType.INCR):
        """
        submits backup job
        Args:
            group_name    (str)             : content group name
            backup_type (Backup.BackupType) : backup type

        Returns
            (str) -- Backup job id

        """
        self.__table.access_action_item(
            group_name,
            self._admin_console.props['action.backup']
        )
        return RBackup(self._admin_console).submit_backup(backup_type)

    @PageService()
    def access_restore(self, group_name):
        """
        Acesses restore for browse
        Args:
            group_name    (str): content group name
        """
        self.__table.access_action_item(
            group_name,
            self._admin_console.props['action.restore']
        )
        self._admin_console.wait_for_completion()

    @PageService()
    def submit_restore(self, file_folders, copy=None, database=True):
        """
        Submits restore job
        Args:
            file_folders (list): list of files and folders to be restored

            copy(str) : copy selection for restoring of data

            database(bool) : To confirm the database restore screen
        Returns
          (str):  Restore options object

        """
        if copy:
            self.__browse.select_storage_copy(label=copy, database=database)

        self.__browse.clear_all_selection()
        self.__browse.select_path_for_restore(path=None, file_folders=file_folders)
        self.__browse.submit_for_restore()
        return RestoreOptions(self._admin_console)

    @PageService()
    def delete_account(self):
        """Deletes the account"""
        self.__page_container.access_page_action_from_dropdown('Delete')
        self._dialog.type_text_and_delete('DELETE')
        self._admin_console.wait_for_completion()

    @PageService()
    def get_content_group_contents(self):
        """gets the content group content"""
        contents = []
        content_elements = self.__get_elements_of_content_group()
        for element in content_elements:
            contents.append(element.text)
        return contents


class _AddContentGroup(Wizard):

    def __init__(self, admin_console):
        """
              Args:
                  admin_console (AdminConsole): adminconsole base object
              """
        super().__init__(admin_console)
        self.__dropdown = RDropDown(admin_console)
        self._driver = admin_console.driver

    @WebAction()
    def __click_plus(self):
        """clicks plus near custom content """
        self._driver.find_element(By.XPATH, "//div[contains(@class,'add-path-btn')]").click()

    @PageService()
    def __set_custom_path(self, path):
        """
        sets custom path
        Args:
            path (str): content path
        """
        self.fill_text_in_field(id="custom-path", text=path)

    @PageService()
    def add(self, name, plan, contents):
        """ Adds content group """

        # Enter the name
        self.fill_text_in_field(id="contentGroupName", text=name)

        # Choose plan from dropdown
        self.__dropdown.select_drop_down_values(
            values=[plan], drop_down_id='contentGroupPlan')

        # Click on next
        self.click_next()

        # Open the input field
        self.click_add_icon()
        self._driver.find_element(By.XPATH, "//div[normalize-space()='Custom path']").click()

        # Type in the path
        for content_path in contents:
            self.__set_custom_path(content_path)
            self.__click_plus()

        # Click on submit
        self.click_submit()
