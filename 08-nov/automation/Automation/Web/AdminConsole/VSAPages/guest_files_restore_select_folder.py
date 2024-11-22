# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides method for guest files restore.

Classes:

    GuestFilesRestoreSelectFolder() ---> _Navigator() ---> AdminConsoleBase() ---> Object()

    GuestFilesRestoreSelectFolder() -- This class provides methods to do various types of guest
                                        agent files restore.
Functions:

    __select_restore_or_download()           -- Selects either restore or download

    submit_this_vm_restore()     -- Submits a VMware guest files restore with the backed up VM as
                                    the destination server

    submit_other_vm_restore()    -- Submits a VMware guest files restore to a different VM.

    submit_guest_agent_restore() -- Restores the content to the guest agents.

    download_content()           -- Downloads the files and folders

"""

import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.panel import PanelInfo, DropDown
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Rtable
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException
)


class GuestFilesRestoreSelectFolder:
    """
    This class provides methods to do various types of guest agent files restore
    """
    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__browse_obj = RBrowse(admin_console, "virtualizationBrowse")
        self.__panel_obj = PanelInfo(admin_console)
        self.__panel_dropdown_obj = DropDown(admin_console)
        self.__tree_obj = TreeView(admin_console)
        self.__restore_modal_dialog = RModalDialog(self.__admin_console, "Restore options")
        self.__table = Rtable(admin_console)

    @WebAction()
    def __select_restore_or_download(self, action="Restore"):
        """
        Selects restore / download button

        Args:
            action  (str):   To Select restore or download button

        """
        self.__driver.execute_script("window.scrollTo(0,0)")
        if action == "Download":
            self.__browse_obj.submit_for_download()
        else:
            self.__browse_obj.submit_for_restore()

    @WebAction()
    def __fill_form_by_name(self, element_name, value):
        """
        Fill the value in a text field with element name.

        Args:
            element_name (str) -- the name attribute of the element to be filled
            value (str)      -- the value to be filled in the element

        Raises:
            Exception:
                If there is no element with given name/id

        """
        element = self.__driver.find_element(By.NAME, element_name)
        element.clear()
        element.send_keys(value)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __verify_vm(self, vm_name):
        """
        Verify backup vm is selected by default under myVM

        Args:
        vm_name (base string) -- name of the backup vm

        Raises:
            Exception:
                If the VM name is different from the VM selected under myVM

        """

        if vm_name not in self.__driver.find_element(By.XPATH, "//button[@id='vm']/div").text:
            raise Exception("The source backup VM was not selected by default.")

    @WebAction()
    def __show_deleted_items(self):
        """Selects show deleted items"""
        xpath = "//div[@aria-label='Show deleted items']"
        self.__driver.find_element(By.XPATH, xpath).click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def enable_deleted_items(self):
        """
        Enable deleted items
        """
        self.__show_deleted_items()

    @WebAction()
    def __show_file_versions(self):
        """Selects view versions"""
        xpath = "//div[@aria-label='Show hidden items']"
        self.__driver.find_element(By.XPATH, xpath).click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def enable_file_versions(self):
        """
        Enable file versions
        """
        self.__show_file_versions()

    @PageService()
    def submit_this_vm_restore(
            self,
            files,
            vm_name,
            proxy,
            vm_username,
            vm_password,
            path,
            over_write=True,
            all_files=False):
        """
        Submits a VMware guest files restore with the backed up VM as the destination server

        Args:
            files            (list)         :  the files to be restored

            vm_name          (str)   :  the VM to which the files are to be restored

            proxy            (str)   :  the proxy to be used for restore

            vm_username      (str)   :  the username of the destination VM

            vm_password      (str)   :  the password of the destination VM

            path             (str)   :  the path in the destination VM where files are
                                                to be restored

            over_write       (bool)         :  if files are to be overwritten during restore

            all_files        (bool)         :  if all the files are to be selected for restore

        Returns:
            job_id           (str)   :  the ID of the restore job submitted

        """
        self.__admin_console.log.info("Guest Files Restore to the same VM")
        self.__browse_obj.select_files(files, all_files)
        self.__admin_console.wait_for_completion()
        self.__admin_console.log.info("Files selected. Submitting restore")
        self.__select_restore_or_download()
        if self.__admin_console.check_if_entity_exists("xpath", '//*[text()="Select instance"]'):
            self.__restore_modal_dialog.access_tab(self.__admin_console.props['label.myVMAMAZON'])
        else:
            self.__restore_modal_dialog.access_tab(self.__admin_console.props['label.select.client'])

        self.__admin_console.log.info("Selecting destination client")
        self.__restore_modal_dialog.select_dropdown_values(drop_down_id="proxy", values=[proxy])

        # if self.__driver.find_element(By.ID, "vm"):
        #     self.__verify_vm(vm_name)
        if self.__admin_console.check_if_entity_exists("id", "userName"):
            self.__admin_console.log.info("Filling the vm creds")
            self.__restore_modal_dialog.fill_text_in_field("userName", vm_username)
            self.__restore_modal_dialog.fill_text_in_field("password", vm_password)

        self.__add_destination_path(path)

        if over_write:
            self.__restore_modal_dialog.enable_toggle(toggle_element_id="overwrite")

        self.__restore_modal_dialog.disable_notify_via_email()

        self.__admin_console.log.info("Submitting guest files restore to same VM")
        self.__restore_modal_dialog.click_submit()

        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def submit_other_vm_restore(
            self,
            files,
            proxy,
            destination_server,
            vm_name,
            username,
            password,
            path,
            vm_path=None,
            zone=None,
            region=None,
            over_write=True):
        """
        Submits a VMware/AWS guest files restore to a different VM. Agentless restore
        Args:
            files                (list)         :  list of files to be restored

            proxy                (str)   :  the proxy to be used for restore

            destination_server   (str)   :  the hypervisor where the restore to VM is

            vm_name              (str)   :  the VM to which the files are to be restored

            username             (str)   :  the username of the destination VM

            password             (str)   :  the password of the destination VM

            path                 (str)   :  the path in the destination VM where files are
                                                    to be restored
            vm_path          (list)  :  path to the destination VM in tree

            zone                 (str)   :   availability zone of AWS instance

            region               (str)   :   region of AWS instance

            over_write           (bool)         :  if the files are to be overwritten

        Returns:
            job_id              (str)   :  the ID of the restore job submitted

        """
        self.__admin_console.log.debug("Going to perform other VM restore to %s", vm_name)
        self.__browse_obj.select_files(files)
        self.__admin_console.wait_for_completion()
        self.__admin_console.log.info("Files selected. Submitting restore")
        self.__select_restore_or_download()
        if self.__admin_console.check_if_entity_exists("xpath", '//*[text()="Other instance"]'):
            self.__restore_modal_dialog.access_tab(self.__admin_console.props['label.otherVmAMAZON'])
        elif self.__admin_console.check_if_entity_exists("xpath", '//*[text()="Select Instance"]'):
            self.__restore_modal_dialog.access_tab('Select Instance')
        else:
            self.__restore_modal_dialog.access_tab(self.__admin_console.props['label.otherVm'])

        self.__admin_console.log.info("Selected the destination hypervisor")
        self.__restore_modal_dialog.select_dropdown_values(drop_down_id="destinationHypervisor",
                                                           values=[destination_server])
        self.__admin_console.log.info("Selecting destination proxy")
        self.__restore_modal_dialog.select_dropdown_values(drop_down_id="proxy", values=[proxy])
        self.__admin_console.wait_for_completion()

        restore_destination_modal_dialog = RModalDialog(self.__admin_console, "Select restore destination")
        self.__restore_modal_dialog.click_button_on_dialog(self.__admin_console.props["label.browse"], button_index=0)
        tree_view = TreeView(self.__admin_console, restore_destination_modal_dialog.base_xpath)

        if vm_path:
            time.sleep(30)
            tree_view.expand_path(vm_path)
        else:
            self.__tree_obj.select_items([vm_name])
        restore_destination_modal_dialog.click_submit()

        if self.__admin_console.check_if_entity_exists("id", "userName"):
            self.__admin_console.log.info("Filling the vm creds")
            self.__restore_modal_dialog.fill_text_in_field("userName", username)
            self.__restore_modal_dialog.fill_text_in_field("password", password)

        self.__add_destination_path(path)

        if over_write:
            self.__restore_modal_dialog.enable_toggle(toggle_element_id="overwrite")

        self.__restore_modal_dialog.disable_notify_via_email()

        self.__admin_console.log.info("Submitting guest files restore to a different VM")
        self.__restore_modal_dialog.click_submit()

        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def submit_file_restore_from_vm(self, drive, files, path, proxy, over_write=True, download=False,
                                    deleted_items=False, versions = False, show_versions=False):
        """
        Restores/downloads the content form a VM using file indexing.

        Args:
            drive                (str)    : drive in which file is selected

            files                (list)   :  The files to be restored.

            path                 (str)   :  The path where files are to be restored.

            proxy                (str)   :  The client where the files are to be restored.

            over_write           (bool)         :  If the files are to be overwritten.

            download             (bool)         :  Whether to perform a download or a restore.

            through_search        (bool)         :  Whether to browse file via search or browse

            show_versions        (bool)         :  Whether to show versions or not.

        Returns:
            job_id               (basestring)   :  The ID of the restore job submitted.
        """
        self.__admin_console.log.info("Starting file restore from VM.")
        # if through_search:
        #     files = [drive + ':\\' + file for file in files]
        self.select_files_on_search_using_path(files, show_versions=show_versions)
        search_page = PageContainer(self.__admin_console, id_value='virtualizationBrowse')
        self.__admin_console.log.info("Files selected. Submitting " + "Download" if download else "Restore")
        search_page.click_button(value='Restore' if not download else 'Download')
        restore_modal = RModalDialog(self.__admin_console, title='Restore options')
        self.__admin_console.log.info("Selecting destination client")
        restore_modal.select_dropdown_values(drop_down_id='destinationClient', values=[proxy])
        restore_modal.click_button_on_dialog(text='Browse')
        self.__admin_console.wait_for_completion()
        path_modal = RModalDialog(self.__admin_console, title='Select a path')
        browse_tree = TreeView(self.__admin_console, xpath=path_modal.base_xpath)
        browse_tree.expand_path(path=path.split('\\'), partial_selection=True)
        path_modal.click_submit()
        if over_write:
            restore_modal.enable_toggle(toggle_element_id='overwrite')
        self.__admin_console.log.info("Submitting the file restore job")
        self.__admin_console.wait_for_completion()
        restore_modal.click_submit()
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def select_files_on_search_using_path(self, path, show_versions=False):
        """
        select file on the search results page using path column
        """
        search_results_table = Rtable(admin_console=self.__admin_console, id='browseContentGrid')
        if show_versions:
            search_results_table.access_action_item(path[0], 'View versions')
            self.__admin_console.wait_for_completion()
            search_results_table.apply_sort_over_column('Modified time', ascending=False)
            search_results_table.select_row_by_index(index=2)
        else:
            search_results_table.select_rows(path)


    @PageService()
    def submit_guest_agent_restore(self, files, path, proxy, over_write=True):
        """
        Restores the content to the guest agent (clients)

        Args:
            files                (list)         :  the files to be restored

            path                 (str)   :  the path where files are to be restored

            proxy                (str)   :  the client where the files are to be restored

            over_write           (bool)         :  if the files are to be overwritten

        Returns:
            job_id              (str)   :  the ID of the restore job submitted

        """
        self.__admin_console.log.info("Guest File Restore to the guest agent")
        self.__browse_obj.select_files(files)
        self.__admin_console.log.info("Files selected. Submitting restore")
        self.__select_restore_or_download()

        if self.__admin_console.check_if_entity_exists("xpath", '//*[text()="Select instance"]'):
            self.__restore_modal_dialog.access_tab(self.__admin_console.props['label.myVMAMAZON'])
        else:
            try:
                self.__restore_modal_dialog.access_tab(self.__admin_console.props['label.select.client'])
            except Exception:
                self.__admin_console.log.info("this hypervisor does not have tab to select during guest file restore")

        self.__admin_console.log.info("Selecting destination client")
        self.__restore_modal_dialog.select_dropdown_values(drop_down_id="destinationClient", values=[proxy])
        self.__admin_console.log.info("Destination client is selected. Filling in the restore path")

        try:
            self.__tree_obj.select_items([proxy])
        except:
            self.__admin_console.log.info("Search vm option not present")

        self.__add_destination_path(path, is_destination_agent=True)

        if over_write:
            self.__restore_modal_dialog.enable_toggle(toggle_element_id="overwrite")

        self.__restore_modal_dialog.disable_notify_via_email()

        self.__admin_console.log.info("Submitting guest files restore to Guest Agent")
        self.__restore_modal_dialog.click_submit(wait=False)

        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def download_content(self, files, select_one=False):
        """
        Downloads the files and folders

        Args:
            files   (list):     list of all files and folders to download

            select_one (Boolean) : download only single file.

        Raises:
            Exception:
                if the download option is not present or
                if the download job did not trigger

        """
        if select_one:
            self.__browse_obj.select_files(files)
        else:
            self.__browse_obj.select_files(files)
        self.__admin_console.log.info("Selected content for download. Clicking on download")

        self.__select_restore_or_download(action="Download")

        try:
            WebDriverWait(self.__driver, 120).until(EC.presence_of_element_located((
                By.ID, "download-tracker")))
            self.__admin_console.wait_for_completion()
        except Exception as exp:
            raise Exception("Download job did not start in 5 minutes." + str(exp))

        self.__admin_console.log.info("Download job started successfully. Please wait for the job to complete.")

    @PageService()
    def select_download(self):
        """
        Selects download button and return the job id from the triggered job
        """
        self.__driver.execute_script("window.scrollTo(0,0)")
        return self.__browse_obj.click_download()

    def download_guest_file_content(self, files, browse_folder, select_one=False):
        """
        Downloads the files and folders

        Args:
            files   (list):     list of all files and folders to download

            select_one (Boolean) : download only single file.

        Raises:
            Exception:
                if the download option is not present or
                if the download job did not trigger

        """
        if browse_folder:
            if "/" in browse_folder:
                folder_to_browse = browse_folder.split("/")
            else:
                folder_to_browse = [browse_folder]

            for folder in folder_to_browse:
                self.__table.access_link_by_column(entity_name="Name", link_text=folder)

        if select_one:
            # self.__admin_console.select_for_restore(files, select_one=True)
            self.__browse_obj.select_files(files)
        else:
            self.__browse_obj.select_files(files)
        self.__admin_console.log.info("Selected content for download. Clicking on download")

        job_id = self.select_download()
        return job_id

    @PageService()
    def submit_google_cloud_vm_restore(
            self,
            files,
            vm_name,
            proxy,
            vm_username,
            vm_password,
            path,
            over_write=True,
            all_files=False):
        """
        Submits a Google Cloud guest files restore with the backed up VM as the destination server

        Args:
            files            (list)         :  the files to be restored

            vm_name          (str)   :  the VM to which the files are to be restored

            proxy            (str)   :  the proxy to be used for restore

            vm_username      (str)   :  the username of the destination VM

            vm_password      (str)   :  the password of the destination VM

            path             (str)   :  the path in the destination VM where files are
                                                to be restored

            over_write       (bool)         :  if files are to be overwritten during restore

            all_files        (bool)         :  if all the files are to be selected for restore

        Returns:
            job_id           (str)   :  the ID of the restore job submitted

        """
        self.__admin_console.log.info("Guest Files Restore to the same VM")
        self.__browse_obj.select_files(files, all_files)
        self.__admin_console.log.info("Files selected. Submitting restore")
        self.__select_restore_or_download()

        self.__admin_console.log.info("Selecting destination proxy")
        self.__admin_console.cv_single_select("Destination", proxy)
        self.__admin_console.log.info("Selected destination proxy. Filling in the VM credentials")

        if self.__admin_console.check_if_entity_exists("name", "fsLoginName"):
            self.__admin_console.log.info("Filling the vm creds")
            self.__fill_form_by_name("fsLoginName", vm_username)
            self.__fill_form_by_name("fsPassword", vm_password)

        self.__admin_console.log.info("Filling in the restore path")
        self.__restore_modal_dialog.fill_text_in_field("selectedPath", path)

        if over_write:
            self.__restore_modal_dialog.enable_toggle(toggle_element_id="overwrite")

        self.__restore_modal_dialog.disable_notify_via_email()

        self.__admin_console.log.info("Submitting the Guest files restore to the same VM")
        self.__restore_modal_dialog.click_submit(wait=False)

        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def __browse_and_select_destination_path(self, path, is_destination_agent=False):
        """
        Browse and selects the path from tree

        Args:
            path    (str):  Restore path
            is_destination_agent    (bool): True if the restore destination is an agent
        """
        if self.__admin_console.check_if_entity_exists(By.XPATH, "//div[@role='tablist']/button[contains(@class, 'Mui-selected')]/span[1]") \
            and self.__restore_modal_dialog.current_tab().lower() == "other vm":
            self.__restore_modal_dialog.click_button_on_dialog(self.__admin_console.props["label.browse"],
                                                               button_index=1)
        else:
            self.__restore_modal_dialog.click_button_on_dialog(self.__admin_console.props["label.browse"])

        self.__admin_console.wait_for_completion()
        if "/" in path:
            sep = "/"
            folder_list = path.split(sep)[1:]
            if not is_destination_agent:
                folder_list[0] = sep + folder_list[0]
        else:
            sep = "\\"
            folder_list = path.split(sep)
        try:
            #For AWS, with root 'C:'
            browse_path_dialog = RModalDialog(self.__admin_console, "Select a path")
            select_path_tree = TreeView(self.__admin_console, '(' + browse_path_dialog._dialog_xp + ')')
            for e, folder in enumerate(folder_list):
                select_path_tree.expand_node(folder)
                self.__admin_console.wait_for_completion()
            select_path_tree.select_items(folder_list[-1:])
            browse_path_dialog.click_submit()
        except:
            #For VMW, with root 'C://'
            if not is_destination_agent:
                folder_list[0] = folder_list[0] + sep
            browse_path_dialog = RModalDialog(self.__admin_console, "Select a path")
            select_path_tree = TreeView(self.__admin_console, '(' + browse_path_dialog._dialog_xp + ')')
            select_path_tree.expand_path(folder_list)
            browse_path_dialog.click_submit()

    @PageService()
    def __add_destination_path(self, path, is_destination_agent=False):
        """
        Fills the destination path input field with the given path

        Args:
            path    (str):  Restore path
            is_destination_agent    (bool): True if the restore destination is an agent
        """
        self.__admin_console.log.info("Filling in the restore path")
        try:
            self.__restore_modal_dialog.fill_text_in_field("selectedPath", path)
        except ElementNotInteractableException:
            self.__admin_console.log.info("Path field disabled for typing, browsing and selecting restore path")
            self.__browse_and_select_destination_path(path, is_destination_agent)
            inputFieldValue = self.__restore_modal_dialog.get_text_in_field("selectedPath") 
            if not inputFieldValue:
                self.__admin_console.log.info("Input Field Value is empty. Attempting to browse destination path agian")
                self.__browse_and_select_destination_path(path, is_destination_agent)