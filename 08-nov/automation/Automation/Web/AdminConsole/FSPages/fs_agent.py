from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on
all the iDA on the AdminConsole

Class:

    FsAgent -> Agents() -> _Navigator() -> AdminConsoleBase() -> object()

Functions:

    add_backupset()                     -- Adds a new backupset to the Fs iDA.

    _browse_and_select_data()           -- Selects backup data through FS Browse

    action_add_fs_subclient()           -- Adds a new subclient to the Fs iDA.

Class:
    FSSubClient

Functions:

    __add_custom_path()             -- enter the custom path in the custom path field
    __click_add_custom_path()       -- click add button to add the entered custom path(s)

"""
from Web.AdminConsole.AdminConsolePages.agents import Agents
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.panel import ModalPanel


class FsAgent(Agents):
    """
    This class provides the function or operations that can be performed on
    FS Agent on the AdminConsole
    """

    def __init__(self, admin_console):

        super(FsAgent, self).__init__(admin_console)
        self.__table = Table(admin_console)
        self.__modal_dialog = ModalDialog(admin_console)
        self.admin_console = admin_console

    @PageService()
    def add_backupset(self, backup_set):
        """
        Adds the backup set

        Args:
            backup_set        (str)    :    name of the backupset we want to associate
                                            with a Fs server

        Raises:
            Exception:
                The error message displayed
        """

        self.admin_console.select_hyperlink("Add backup set")
        self.admin_console.fill_form_by_id("backupSetName", backup_set)
        self.admin_console.submit_form()
        self.admin_console.check_error_message()

    @PageService()
    def action_add_fs_subclient(self,
                                backup_set,
                                subclient_name,
                                plan,
                                browse_and_select_data,
                                backup_data,
                                impersonate_user=None,
                                exclusions=None,
                                exceptions=None,
                                backup_system_state=False,
                                storage_policy=None,
                                schedule_policies=None,
                                file_system='Windows'):
        """
        Method to Add New Subclient

        Args:
            subclient_name (string)       : Name of the new sub client to be added

            backup_set      (string)       :name of the backupset we want to associate
                                            with a Fs server

            plan           (string)       : plan name to be used as policy for new sub client
                                            backup

            browse_and_select_data(bool)  : Pass True to browse and select data,
                                            False for custom path

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            impersonate_user (dict)        :  Username and passowrd for impersonate user

            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            backup_system_state (boolean)  :  boolean values to determine if syatem state to
                                            be backed up or not

            storage_policy   (string)      :  storage policy to be used by subclient

            schedule_policies   (list)       :  list containing schedule policies to be used
                                                by subclient

            file_system       (string)     :  file system of the client
                Eg. - 'Windows' or 'Unix'

        Raises:
            Exception:
                -- if fails to initiate backup
        """

        self.__table.access_action_item(backup_set, "Add subclient")
        fs_subclient = FSSubClient(self.admin_console)
        fs_subclient.add(subclient_name, plan, browse_and_select_data, backup_data,
                         impersonate_user, exclusions, exceptions, backup_system_state,
                         storage_policy, schedule_policies, file_system)

    @PageService()
    def delete_backup_set(self, backup_set_name):
        """
        Method to delete backup set

        Args:
            backup_set_name : Name of the back up set
        """
        self.__table.access_action_item(backup_set_name, 'Delete')
        self.__modal_dialog.type_text_and_delete('DELETE')


class FSSubClient:
    def __init__(self, admin_console):
        """ Initialize the base panel """

        self.admin_console_base = admin_console
        self.driver = admin_console.driver
        self.__modal_panel = ModalPanel(self.admin_console_base)

    @WebAction()
    def __browse_and_select_data(self, backup_data, file_system):
        """
        selects backup data through FS Browse

        Args:

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            file_system      (string)     :  file system of the client
                Eg. - 'Windows' or 'Unix'

        Returns:
            None

        Raises:
            Exception:
                if not able to select data
        """

        for data in backup_data:
            count = 0
            dest = 0
            flag = True
            if file_system.lower() == 'windows':
                pattern = "\\"
            else:
                pattern = "/"
            directories = []
            start = 0
            while flag:
                tag = data.find(pattern, start)
                if tag == -1:
                    flag = False
                else:
                    count += 1
                    start = tag+1

            for i in range(0, count+1):
                directory, sep, folder = data.partition(pattern)
                data = folder
                if directory != '':
                    directories.append(directory)
            path = len(directories)

            for i in range(0, path-1):
                if self.driver.find_element(By.XPATH, 
                        "//span[contains(text(),'"+str(directories[i])+"')]/../../button").\
                        get_attribute("class") == 'ng-scope collapsed':
                    self.driver.find_element(By.XPATH, 
                        "//span[contains(text(),'"+str(directories[i])+"')]/../../button").click()
                dest = i+1

            self.driver.find_element(By.XPATH, 
                "//span[contains(text(),'" + str(directories[dest]) + "')]").click()
        self.__modal_panel.submit()

    @PageService()
    def browse_and_select_data(self, backup_data, file_system):
        """browse and select data"""
        self.__browse_and_select_data(backup_data, file_system)

    @WebAction()
    def __add_custom_path(self, path):
        """Add custom paths in the path input box"""
        custom_path_input_xpath = "//input[@placeholder='Enter custom path']"
        custom_path_input = self.driver.find_element(By.XPATH, custom_path_input_xpath)
        custom_path_input.clear()
        custom_path_input.send_keys(path)

    @WebAction()
    def __click_add_custom_path(self):
        """Clicks the add custom path icon"""
        add_path_icon_xpath = "//i[@title='Add']"
        self.driver.find_element(By.XPATH, add_path_icon_xpath).click()

    @PageService()
    def add(self,
            subclient_name,
            plan,
            browse_and_select_data,
            backup_data,
            impersonate_user=None,
            exclusions=None,
            exceptions=None,
            backup_system_state=False,
            storage_policy=None,
            schedule_policies=None,
            file_system='Windows'):
        """
            Method to Add New Subclient

            Returns:
                None

            Raises:
                Exception:
                    -- if fails to initiate backup
        """
        self.admin_console_base.fill_form_by_id("subclientName", subclient_name)

        if plan:
            self.admin_console_base.enable_toggle(0)
            self.admin_console_base.cv_single_select("Plan", plan)
        else:
            self.admin_console_base.disable_toggle(0)
            self.admin_console_base.cv_single_select("Storage policy", storage_policy)
            if schedule_policies:
                self.admin_console_base.cvselect_from_dropdown("Schedule policy", schedule_policies)

        if browse_and_select_data:
            self.admin_console_base.select_hyperlink('Content')
            self.admin_console_base.select_hyperlink('Browse')
            self.__browse_and_select_data(backup_data, file_system)

        else:
            for path in backup_data:
                self.__add_custom_path(path)
                self.__click_add_custom_path()

        if impersonate_user:

            self.admin_console_base.select_hyperlink("Impersonate user")
            self.admin_console_base.wait_for_completion()

            if isinstance(impersonate_user, str):
                self.admin_console_base.cv_single_select("Credential", impersonate_user)
                self.admin_console_base.click_button("OK")

            elif isinstance(impersonate_user, dict):
                self.admin_console_base.fill_form_by_id('loginName', impersonate_user['username'])
                self.admin_console_base.fill_form_by_id('password', impersonate_user['password'])
                self.admin_console_base.submit_form()

        if exclusions:
            self.admin_console_base.select_hyperlink('Exclusions')
            self.admin_console_base.select_hyperlink('Browse')
            self.__browse_and_select_data(backup_data, file_system)

        if exceptions:
            self.admin_console_base.select_hyperlink('Exceptions')
            self.admin_console_base.select_hyperlink('Browse')
            self.__browse_and_select_data(backup_data, file_system)

        if backup_system_state:
            self.admin_console_base.enable_toggle(1)
        else:
            self.admin_console_base.disable_toggle(1)

        self.admin_console_base.click_button('Save')
        self.admin_console_base.check_error_message()
