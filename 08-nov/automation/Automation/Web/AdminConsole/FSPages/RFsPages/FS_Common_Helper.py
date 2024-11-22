# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

# When editing this file kindly either of the following people for review : Aravind Putcha , Rohan Prasad

"""
This module provides the function or operations that are common to FS 
"""


import os
import time
import re
from typing import Optional
from Web.AdminConsole.Components.core import Checkbox, Toggle
from Web.AdminConsole.FileServerPages.file_servers import AddWizard
from Web.AdminConsole.AdminConsolePages.agents import Agents
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RModalPanel, RPanelInfo, RDropDown
from Web.AdminConsole.Components.browse import RBrowse, RContentBrowse
from Web.AdminConsole.Storage.CloudStorage import CloudStorage
from AutomationUtils import logger
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys


class RRestorePanel(RModalPanel):

    # Class containing commons fuctions to perform on react restore panel
    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.admin_console = admin_console
        self.__checkbox = Checkbox(admin_console)
        self.__driver = admin_console.driver
        self.__toggle = Toggle(admin_console)
        self.__rmodal_dialog = RModalDialog(self.admin_console)

    @PageService()
    def select_restore_destination_client(self, destination_client_name: str) -> None:
        """
        Selects the destination client to restore

        Args:
            destination_client_name (str): Destination client name to restore to
        """
        self.__rdropdown.select_drop_down_values(
            drop_down_id="destinationServerList", values=[destination_client_name]
        )

    @PageService()
    def toggle_acl_restore_checkbox(self, check_option_to: bool = True) -> None:
        """
        Toggles the ACL restore option based on the parameter

        Args:
            check_option_to (bool, optional): Whether to toggle option or not. Defaults to True.
        """
        if check_option_to == True:
            self.__checkbox.check(id="acl")
        else:
            self.__checkbox.uncheck(id="acl")

    @PageService()
    def toggle_ibmi_spool_file_data(self, check_option_to: bool = False) -> None:
        """
        Select the toggle for restore spooled file data restore option based on the parameter

        Args:
            check_option_to (bool, optional): Whether to toggle option or not. Defaults to False.
        """
        if self.__toggle.is_exists(label="Restore Spooled File Data"):
            if check_option_to:
                self.__toggle.enable(label="Restore Spooled File Data")
            else:
                self.__toggle.disable(label="Restore Spooled File Data")

    @PageService()
    def toggle_data_restore_checkbox(self, check_option_to: bool = True) -> None:
        """
         Toggles the data restore option based on the parameter

        Args:
            check_option_to (bool, optional): Whether to toggle option or not. Defaults to True.
        """
        if check_option_to:
            self.__checkbox.check(id="data")
        else:
            self.__checkbox.uncheck(id="data")

    @PageService()
    def toggle_restore_to_original_folder_checkbox(self, check_option_to: bool = True) -> None:
        """
        Toggles the option to restore to original folder or not

        Args:
            check_option_to (bool, optional): Whether to toggle option or not. Defaults to True.
        """
        if check_option_to:
            self.__checkbox.check(id="restoreToFolder")
        else:
            self.__checkbox.uncheck(id="restoreToFolder")

    @PageService()
    def impersonate_user(self, username: str, password: str) -> None:
        """
        Function to add impersonate user creds

        Args:
            username (str): username to impersonate
            password (str): password for impersonating the user

        """
        if self.__checkbox.is_exists(id="useImpersonation"):
            self.__checkbox.check(id="useImpersonation")
        self.fill_input(text=username, id="impersonateUsername")
        self.fill_input(text=password, id="impersonatePassword")

    @PageService()
    def add_destination_path_for_restore(self, destination_path: str) -> None:
        """
        Function to add destination path to perfrom OOP restore

        Args:
            destination_path (str): Path to restore the data to.
        """
        self.toggle_restore_to_original_folder_checkbox(check_option_to=False)
        self.fill_input(text=destination_path, id="destinationPathdestinationPathInput")

    @PageService()
    def toggle_unconditional_overwrite_checkbox(self, check_option_to: bool = False) -> None:
        """
        Toggles the option to perform unconditional overwrite or not

        Args:
            check_option_to (bool, optional): Whether to toggle option or not. Defaults to False.
        """
        if self.__checkbox.is_exists(id="unconditionalOverwrite"):
            if check_option_to == True:
                self.__checkbox.check(id="unconditionalOverwrite")
            else:
                self.__checkbox.uncheck(id="unconditionalOverwrite")

    @PageService()
    def submit_restore(self, impersonate_dialog=False) -> str:
        """
        Clicks the restore button and returns the job id
        Args:
               impersonate_dialog (bool): Click "Yes" button when impersonate dialog shows up for NAS clients.
                    Defaults to False
        Returns:
           Job Id (str) : Job id for the restore job
        """
        self.click_restore_button()
        if impersonate_dialog:
            self.__rmodal_dialog.click_yes_button()
        return self.admin_console.get_jobid_from_popup()

    @PageService()
    def fill_restore_panel_details_and_submit(self,
                                              destination_client=None,
                                              destination_path=None,
                                              acl=True,
                                              data=True,
                                              unconditional_overwrite=False,
                                              impersonate_user=None,
                                              impersonate_dialog=False,
                                              **kwargs):
        """
        Method to fill all the restore panel details
        destination_client (str) : Destination client
        destination_path (str)   : Destination path for restore
        acl (bool)               : To restore ACL. Defaults to True
        data (bool)              : To restore Data. Defaults to True
        unconditional_overwrite (bool) : To restore unconditionally. Defaults to True
        impersonate_user (dict)  : Dict containing username and password
        impersonate_dialog (bool): Click "Yes" button when impersonate dialog shows up for NAS clients. Defaults to False
        kwargs(dict) : Optional
        Available kwargs Options:
            ndmp(bool, optional): for ndmp restore set it to True else False.
            cifs(bool, optional): for cifs restore set it to True else False
            nfs(bool, optional): for nfs restore set it to True else False
            cloud_client (bool, optional): for cloud restore set it to True else False
        """

        if destination_client:
            self.select_restore_destination_client(destination_client)

        if destination_path:
            self.add_destination_path_for_restore(destination_path)
        
        if not (kwargs.get('ndmp', None)) and not (kwargs.get('cloud_client', None)):
            if unconditional_overwrite:
                self.toggle_unconditional_overwrite_checkbox(True)

            if impersonate_user:
                self.impersonate_user(impersonate_user["username"],
                                      impersonate_user["password"])

            # Let Restore ACL's & Data be at the last because ACL's might be deselected
            # when different destination client is selected.

            self.toggle_acl_restore_checkbox(acl)

            self.toggle_data_restore_checkbox(data)

        return self.submit_restore(impersonate_dialog=impersonate_dialog)

class FileServersUtils:

    # Class for common functions
    # Add function for each actiob button
    def __init__(self, admin_console):
        self.__Rtable = Rtable(admin_console)
        self.__rmodal_dialog = RModalDialog(admin_console)
        self.__rbrowse = RBrowse(admin_console)
        self.__rcontent_browse = RContentBrowse(admin_console)
        self.__driver = admin_console.driver
        self.__rdropdown = RDropDown(admin_console)
        self.__toggle = Toggle(admin_console)
        self.__checkbox = Checkbox(admin_console)
        self.admin_console = admin_console
        self.__rrestore_panel = RRestorePanel(admin_console)
        self.__add_wizard = AddWizard(admin_console)
        self.log = logger.get_log()

    @WebAction()
    def __hover_and_remove_content(self, path: str, label: str) -> None:
        """
        This is a web action to remove content from the edit content panel.

        Args:
            path (str): Path to be removed
            label (str): Label from where the content has to be removed.
                         Label values: "Backup content", "Exclusions", "Define exceptions"
        """

        label_elem = "h4"

        if "exceptions" in label.lower():
            label_elem = "span"

        base_xpath = f"//{label_elem}[contains(., '{label}')]//ancestor::div[contains(@class, 'header-container')]"\
                    "/following-sibling::div[contains(@class, 'path-list-container')]"
        
        # Adding base_xpath to parent_xpath to support content removal if exclusions and exceptions are the same.

        parent_xpath = base_xpath + f"//*[@aria-label='{path}']"
        btn_xpath = parent_xpath + "//following-sibling::div//button"
        parent_element = self.__driver.find_element(By.XPATH, parent_xpath)
        ActionChains(self.__driver).move_to_element(parent_element).perform()
        btn_element = self.__driver.find_element(By.XPATH, btn_xpath)
        btn_element.click()

    @PageService()
    def remove_plan_content(self) -> None:
        """
        Function to remove the content inherited from plan
        """
        base_xpath = "//h4[contains(., 'Backup content')]//ancestor::div[contains(@class, 'header-container')]/following-sibling::div[contains(@class, 'path-list-container')]"
        get_data = self.__driver.find_element(By.XPATH, base_xpath).text
        content_list = get_data.split("\n")
        for content in content_list:
            # If customer path is added we need to skip the value
            # Sample Output of contnet list :
            # ['Enter custom path', 'C:\\dummy', 'Audio', 'Disk images', 'Email files', 'Executable', 'Image', 'Office', 'Scripts',
            # 'Source code files', 'System', 'Temporary files (linux)', 'Temporary files (mac)', 'Temporary files (windows)', 'Text', 'Thumbnail supported',
            #  'Video', 'Virtual machine']
            if content != "Enter custom path" and content != "No contents are added":
                self.__hover_and_remove_content(content, "Backup content")

    @PageService()
    def remove_plan_exclusions(self) -> None:
        """
        Function to remove exclusions inherited from plan
        """
        base_xpath = "//h4[contains(., 'Exclusions')]//ancestor::div[contains(@class, 'header-container')]/following-sibling::div[contains(@class, 'path-list-container')]"
        get_data = self.__driver.find_element(By.XPATH, base_xpath).text
        exclusion_list = get_data.split("\n")
        for exclusion in exclusion_list:
            # Sample Output of contnet list :
            # ['Enter custom path', 'C:\\dummy', 'Audio', 'Disk images', 'Email files', 'Executable', 'Image', 'Office', 'Scripts',
            # 'Source code files', 'System', 'Temporary files (linux)', 'Temporary files (mac)', 'Temporary files (windows)', 'Text', 'Thumbnail supported',
            #  'Video', 'Virtual machine']
            if (
                exclusion != "Enter custom path"
                and exclusion != "No exclusions are added"
            ):
                self.__hover_and_remove_content(exclusion, "Exclusions")

    @PageService()
    def remove_plan_exceptions(self):
        """
        Function to remove exceptions inherited from plan
        """

        if self.__toggle.is_exists(label="Define exceptions"):

            if self.__toggle.is_enabled(label="Define exceptions"):

                base_xpath = "//span[contains(., 'Define exceptions')]//ancestor::div[contains(@class, 'header-container')]"\
                    "/following-sibling::div[contains(@class, 'path-list-container')]"
                
                get_data = self.__driver.find_element(By.XPATH, base_xpath).text
                exclusion_list = get_data.split("\n")
                for exclusion in exclusion_list:
                    # Sample Output of contnet list :
                    # ['Enter custom path', 'C:\\dummy', 'Audio', 'Disk images', 'Email files', 'Executable', 'Image', 'Office', 'Scripts',
                    # 'Source code files', 'System', 'Temporary files (linux)', 'Temporary files (mac)', 'Temporary files (windows)', 'Text', 'Thumbnail supported',
                    #  'Video', 'Virtual machine']
                    if (
                        exclusion != "Enter custom path"
                        and exclusion != "No exceptions are added"
                    ):
                        self.__hover_and_remove_content(exclusion, "Define exceptions")
        

    @PageService()
    def remove_content(self, content_list: list[str], header="Content"):
        """
        _summary_

        Args:
            content_list (list[str]): _description_
            header (str): Header from which the content has to be removed.
                        Header values: Content / Exclusions / Exceptions
        """

        label = "Content"

        if header.lower() == "exclusions":
            label = "Exclusions"
        elif header.lower() == "exceptions":
            label = "Define exceptions"

        for content in content_list:
            self.__hover_and_remove_content(content, label)

    @PageService()
    def change_file_server_name(self):
        """
        _summary_
        """
        pass

    @WebAction()
    def restore_from_calender(self, calendar, backuspet_name=None, measure_time=True):
        """
        Selects the backupset and calendar options then clicks on restore

        Args:
            calendar (dict): Dict containing year, month, date, hours, minutes
            backupset_name Optional(str): Name of the backupset. Defaults to None
            measure_time Optional(bool): True to raise Exception if page load is taking time
        """

        recovery_panel = RPanelInfo(self.admin_console, title="Recovery points")

        if backuspet_name:
            self.__rdropdown.select_drop_down_values(drop_down_id="backupSetsDropdown", values=[backuspet_name])

        recovery_panel.date_picker(calendar)

        if measure_time:
            start_time = time.time()
            recovery_panel.click_button("Restore")
            elapsed_time = time.time() - start_time
            elapsed_time_minutes = elapsed_time / 60
            if elapsed_time_minutes > 3:
                raise Exception("Time limit for browse exceeded")
        else:
            recovery_panel.click_button("Restore")

    @PageService()
    def search_files_for_restore(self, 
                                 filename: str = None, 
                                 contains: str = None, 
                                 file_type: str = None, 
                                 modified: str = None, 
                                 include_folders = True,
                                 backupset_name = None,
                                 show_deleted_items = True) -> None:
        
        """
        Method to set the values in the search bar in RBrowse
        """

        self.admin_console.click_by_id("searchInput")
        time.sleep(10)

        if filename:
            self.admin_console.fill_form_by_id("Filename", filename)
        if contains:
            self.admin_console.fill_form_by_id("Contains")
        if file_type:
            self.__rdropdown.select_drop_down_values(index=0, values=[file_type])
        if modified:
            self.__rdropdown.select_drop_down_values(index=1, values=[modified])

        # To select backupset from search bar in fsAgentDetails page
        if backupset_name:
            self.__rdropdown.select_drop_down_values(drop_down_id="BackupSet",
                                                     values=[backupset_name])
        
        # Include folders / Show deleted items are checked by default
        if not include_folders:
            self.__checkbox.uncheck(id="IncludeFolders")
        if not show_deleted_items:
            self.__checkbox.uncheck(id="ShowDeletedFiles")

        # self.admin_console.click_button_using_text("Search")
        self.admin_console.driver.find_element(By.ID, "Filename").send_keys(Keys.RETURN)

        # There is no loading icon visible from clicked on search
        # So adding sleep(30)

        time.sleep(30)

        self.admin_console.wait_for_completion()

    @PageService()
    # Ideally the assumption with this function is that its called on Browse screen
    def restore(
            self,
            dest_client: Optional[str] = None,
            restore_acl: bool = True,
            restore_data: bool = True,
            destination_path: Optional[str] = None,
            restore_aux_copy: bool = False,
            storage_copy_name: Optional[str] = None,
            unconditional_overwrite: bool = False,
            selected_files: Optional[list[str]] = None,
            modified_file: Optional[str] = None,
            version_nums: Optional[list[str]] = None,
            impersonate_user: Optional[dict] = None,
            show_deleted_items: bool = False,
            deleted_items_path: Optional[list[str]] = None,
            show_hidden_items: bool = False,
            hidden_items_path: Optional[list[str]] = None,
            search_pattern: Optional[str] = None,
            **kwargs,
    ) -> str:
        """
        _summary_

        Args:
            dest_client (Optional[str], optional): _description_. Defaults to None.
            restore_acl (bool, optional): _description_. Defaults to True.
            restore_data (bool, optional): _description_. Defaults to True.
            destination_path (bool, optional): _description_. Defaults to None.
            restore_aux_copy (bool, optional): _description_. Defaults to False.
            storage_copy_name (Optional[str], optional): Name of storage to use
                                                        E.g - Restore from snap copy
                                                        E.g - Restore from secondary copy
                                                        E.g - Restore from secondary snap copy
                                                        Defaults to None.
            unconditional_overwrite (bool, optional): _description_. Defaults to False.
            selected_files (Optional[list[str]], optional): _description_. Defaults to None.
            impersonate_user (Optional[dict], optional): _description_. Defaults to None.
            show_deleted_items (bool, optional): Defaults to False
            modified_file (Optional[str]) : Defaults to None
            version_nums (Optional[list[str]]) : Defaults to None
            deleted_items_path ([list[str]], optional): List of deleted paths. Defaults to None
            show_hidden_items (bool, optional): Defaults to False
            hidden_items_path ([list[str]], optional): List of hidden paths. Defaults to None
            search_pattern (Optional[str], optional): _decsription_. Defaults to None
            kwargs (dict)--Optional arguments.
            Available kwargs Options:
                 ndmp (bool, optional): for ndmp restore set it to True else False.
                 cifs (bool, optional): for cifs restore set it to True else False
                 nfs (bool, optional): for nfs restore set it to True else False
                 cloud_client (bool, optional): for cloud restore set it to True else False
        Returns:
            str: _description_
        """
        # TODO
        if kwargs.get("blocklevel"):
            if kwargs.get("filelevel"):
                self.admin_console.click_by_id("fileLevelRestore")
            if kwargs.get("volumelevel"):
                self.admin_console.click_by_id("fileLevelRestore")

        if restore_aux_copy:
            self.admin_console.click_button_using_text("Change source")
            self.__rmodal_dialog.select_dropdown_values(drop_down_id="sourcesList", values=[storage_copy_name])
            # yet to add code for media agent selection dropdown in Change source dialog box
            self.admin_console.click_button_using_text("OK")
            self.admin_console.wait_for_completion()
            # yet to add code for Show latest backup dropdown

        if show_deleted_items:
            parent_dir = os.path.dirname(deleted_items_path[0])
            self.__rbrowse.select_deleted_items_for_restore(content_path=parent_dir,
                                                            files_folders=deleted_items_path)

        elif modified_file:
            self.__rbrowse.select_multiple_version_of_files(modified_file, version_nums)

        if show_hidden_items:
            parent_dir = os.path.dirname(hidden_items_path[0])
            self.__rbrowse.select_hidden_items(content_path=parent_dir,
                                               hidden_items=hidden_items_path)

        if search_pattern:
            self.search_files_for_restore(filename=search_pattern)

        if selected_files:
            if kwargs.get('cifs', None):
                if not len(selected_files[0].strip("\\").split("\\")) > 2:
                    selected_files[0] = selected_files[0].strip("\\")
            paths = os.path.dirname(selected_files[0])
            if kwargs.get('cifs', None):
                paths = "\\\\" + paths
            if kwargs.get('nfs', None):
                paths = paths.strip(":")
            self.__rbrowse.navigate_path(paths)
            select_files = [os.path.basename(file) for file in selected_files]
            self.__rbrowse.select_files(file_folders=select_files)
        else:
            self.__rbrowse.select_files(select_all=True)

        self.__rbrowse.submit_for_restore()
        self.admin_console.wait_for_completion()

        impersonate_dialog = False
        return self.__rrestore_panel.fill_restore_panel_details_and_submit(destination_client=dest_client,
                                                                           destination_path=destination_path,
                                                                           acl=restore_acl,
                                                                           data=restore_data,
                                                                           unconditional_overwrite=unconditional_overwrite,
                                                                           impersonate_user=impersonate_user,
                                                                           impersonate_dialog=impersonate_dialog,
                                                                           **kwargs)

    @PageService()
    def download_selected_items(self,
                                parent_dir: str = None,
                                download_files: list[str] = None,
                                select_all = False
    ):
        """
        Downloads the files from the Browse page

        Args:
            parent_dir (str) : Path from which the files have to be downloaded 
                Ex: "/opt", "C:\\data"
            download_files list(str) : List of items to download under parent_dir
                Ex: ["file1.txt", "dir2"]
            select_all (bool) : True to select all content. False by default
        """
        if parent_dir:
            self.__rbrowse.navigate_path(parent_dir)

        if select_all:
            self.__rbrowse.select_files(select_all=True)
        else:
            self.__rbrowse.select_files(download_files)
        
        return self.__rbrowse.submit_for_download()


    @PageService()
    def edit_content(
        self,
        add_content: list[str] = None, 
        del_content: list[str] = None,
        add_exclusions: list[str] = None, 
        del_exclusions: list[str] = None,
        add_exceptions: list[str] = None, 
        del_exceptions: list[str] = None,
        impersonate_user: Optional[dict] = None,
        browse: bool = False
    ):
        """
        Method to edit subclient content inside the RModalDialog
        Args:
            adding_custom_content: Adding content using custom path,
            adding_custom_exclusions: Adding exclusions using custom path,
            adding_custom_exceptions: Adding exceptions using custom path,
            add_content: List of strings to add backup content
            del_content: List of strings to remove from backup content
            add_exclusions: List of strings to add exclusions
            del_exclusions: List of strings to remove from exclusions
            add_exceptions: List of strings to add exceptions
            del_exceptions: List of strings to remove from exceptions
            impersonate_user: Dict containing username and password for cifs content
            browse: If content has to be browsed and added
        """

        if del_exceptions:
            self.remove_content(del_exceptions, "Exceptions")
        if del_exclusions:
            self.remove_content(del_exclusions, "Exclusions")
        if del_content:
            self.remove_content(del_content, "Content")

        if add_content:
            self.__rmodal_dialog.click_button_on_dialog("Add", button_index=0)
            # If browse is set to true, we click on browse
            if browse:
                self.admin_console.click_button(value='Browse')

                for path in add_content:
                    self.__rcontent_browse.select_path(path)

                self.__rcontent_browse.save_path()
            else:
                # Click on Add custom path
                self.admin_console.click_button(value='Custom path')

                for index in range(len(add_content)):
                    self.__add_wizard.add_path(add_content[index])

                    # For cifs path, we provide impersonation only once when the first path is added
                    if index == 0 and add_content[index].startswith("\\\\") and impersonate_user:
                        self.admin_console.wait_for_completion()
                        content_edit = RModalDialog(self.admin_console, "Impersonate user")
                        content_edit.deselect_checkbox(checkbox_id="toggleFetchCredentials")
                        content_edit.fill_text_in_field("userName", impersonate_user["username"])
                        content_edit.fill_text_in_field("password", impersonate_user["password"])
                        content_edit.click_submit()

        if add_exclusions:
            self.__rmodal_dialog.click_button_on_dialog("Add", button_index=1)
            # Click on Add custom path
            self.admin_console.click_button(value='Custom path')
            for exclusion in add_exclusions:
                self.__add_wizard.add_path(exclusion)
        
        if add_exceptions:
            self.__rmodal_dialog.enable_toggle(label="Define exceptions")
            self.__rmodal_dialog.click_button_on_dialog("Add", button_index=2)
            # Click on Add custom path
            self.admin_console.click_button(value='Custom path')
            for exception in add_exceptions:
                self.__add_wizard.add_path(exception)

    @PageService()
    def edit_ibmi_content(self,
                          add_content: list[str] = None,
                          del_content: list[str] = None,
                          add_exclusions: list[str] = None,
                          del_exclusions: list[str] = None,
                          add_exceptions: list[str] = None,
                          del_exceptions: list[str] = None,
                          is_predefined_content: bool = True
                          ):
        """
        Method to edit IBMi subclient content inside the RModalDialog
        Args:
            add_content: List of strings to add backup content
            del_content: List of strings to remove from backup content
            add_exclusions: List of strings to add exclusions
            del_exclusions: List of strings to remove from exclusions
            add_exceptions: List of strings to add exceptions
            del_exceptions: List of strings to remove from exceptions
            is_predefined_content: is subclient content has pre-defined content
        """

        if del_exceptions:
            self.remove_content(del_exceptions, "Exceptions")
        if del_exclusions:
            self.remove_content(del_exclusions, "Exclusions")
        if del_content:
            self.remove_content(del_content, "Content")

        if add_content:
            # if Pre-Defined content is selected, then Content will not be modified
            self.__rmodal_dialog.click_button_on_dialog("Add", button_index=0)
            # Click on Add custom path
            self.admin_console.click_button(value='Custom path')

            for index in range(len(add_content)):
                self.__add_wizard.add_path(add_content[index])

        add_index = 0 if is_predefined_content else 1

        if add_exclusions:
            self.__rmodal_dialog.click_button_on_dialog("Add", button_index=add_index)
            # Click on Add custom path
            self.admin_console.click_button(value='Custom path')
            for exclusion in add_exclusions:
                self.__add_wizard.add_path(exclusion)

        add_index = 1 if is_predefined_content else 2

        if add_exceptions:
            self.__rmodal_dialog.enable_toggle(label="Define exceptions")
            self.__rmodal_dialog.click_button_on_dialog("Add", button_index=add_index)
            # Click on Add custom path
            self.admin_console.click_button(value='Custom path')
            for exception in add_exceptions:
                self.__add_wizard.add_path(exception)

    @PageService()
    def access_protocol(self, protocol: str):
        """
        Method to navigate to the protocol

        Args:
            protocol (str): Name of the protocol (CIFS / NFS / NDMP)
        """

        self.__Rtable.access_link(protocol)

    @PageService()
    def disable_complaince_lock(self, commcell, plan_name):
        """
        Method to disable complaince lock

        Args:
            commcell: Commcell object
            plan_name (str): name of the plan where primary is cloud storage
        """

        self.log.info("Disabling compliance lock")
        is_agp_storage = False
        
        storage_policy = commcell.storage_policies.get(plan_name)

        storage_policy_properties = storage_policy._get_storage_policy_properties()

        if "DrivePool(mas0" in storage_policy_properties["copy"][0]["drivePool"]["drivePoolName"]:
            is_agp_storage = True

        storage = storage_policy.library_name

        if is_agp_storage:
            self.admin_console.navigator.navigate_to_air_gap_protect_storage()
        else:
            self.admin_console.navigator.navigate_to_cloud_storage()

        cloud_storage = CloudStorage(self.admin_console)
        cloud_storage.select_cloud_storage(storage)

        self.admin_console.access_tab("Configuration")
        self.log.info("Sleeping for 2mins for all the tiles to load")
        time.sleep(120)
        rpanel = RPanelInfo(self.admin_console, "WORM")
        if rpanel.is_toggle_enabled(label="Compliance lock"):
            rpanel.disable_toggle("Compliance lock")
            confirm_dialog = RModalDialog(self.admin_console, "Confirm")
            confirm_dialog.click_yes_button()
            self.log.info("Done disabling compliance lock")
        else:
            self.log.info("Compliance lock is disabled already")

    def validate_sparse_tag(self, path=None):
        """
        Method to verify sparse tag in browse page

        Args:
              path  (Optional) str : Absolute path
        """
        if path:
            self.__rbrowse.navigate_path(path)
        values = self.__Rtable.get_column_data(column_name="Name")
        self.log.info(values)
        for value in values:
            filename = value.split('\n')[0]
            if re.search(r'Sparse file', value):
                self.log.info(f"{filename} contains 'Sparse file' tag")
            else:
                raise Exception(f"{filename} is missing the 'Sparse file' tag")
