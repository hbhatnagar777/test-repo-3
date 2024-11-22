from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
testcases of OneDrive for Business module.

This file consists of two classes: OneDrive, OneDriveContentIndexing.

OneDrive  --  This class contains all the methods related to OneDrive

To begin, create an instance of OneDrive for test case.

To initialize the instance, pass the testcase object to the OneDrive class.

Call the required definition using the instance object.

    Functions:

    open_discover_cache_info_modal()                -- Opens discover cache modal
    get_onedrive_discovery_count()                  -- Gets discover count
    refresh_cache()                                 -- Refresh discover cache
    add_group()                                     -- Add a user group into app
    run_restore()                                   -- Runs a restore job
    point_in_time_restore()                         -- Run a point in time restore
    verify_cache_is_fetched()                       -- Verify that existing cache is fetched
    remove_from_content()                           -- Remove given user from content
    get_jobs_count()                                -- Get client job count
    run_ci_job()                                    -- Run a manual CI job on the client

OneDriveContentIndexing  --  This class contains all the methods for Onedrive CI testcases

    Functions:

    get_document_count_in_index()                   -- Query index server wrt jobid to get count
    get_content_indexing_job_id()                   -- Gets jobid of the content indexing job for the client
    get_ci_details_from_index()                     -- Gets Content indexing details

"""


import time

from cvpysdk.job import JobController
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoSuchElementException,
                                        ElementClickInterceptedException)

from Application.Office365.solr_helper import SolrHelper
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.core import SearchFilter,FacetPanel,RfacetPanel
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction
from . import constants
from Web.AdminConsole.Components.wizard import Wizard



class OneDrive(Office365Apps):
    """ Class for OneDrive object """

    def __init__(self, tcinputs, admin_console):
        super(OneDrive, self).__init__(tcinputs, admin_console)
        self._navigator = self._admin_console.navigator
        self.__table = Table(self._admin_console)
        self.__searchfilter = SearchFilter(self._admin_console)
        self.__rtable = Rtable(self._admin_console)
        self._wizard = Wizard(self._admin_console)

    @WebAction(delay=2)
    def _view_user_details(self, user_name):
        """
        Go to user details page for given user

        Args:
            user_name (str):    Email address of user to be accessed

        """
        self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
        xp = (f"//*[@id='cv-k-grid-td-URL']/span[normalize-space()='{user_name}']"
              f"/ancestor::tr/td[contains(@id,'cv-k-grid-td-DISPLAY_NAME')]/a")
        self._driver.find_element(By.XPATH, xp).click()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _click_selectall_browse(self):
        """Select all items during browse"""
        self._driver.find_element(By.XPATH, 
            "//th[@id='cv-k-grid-th-:checkbox']"
        ).click()

    @WebAction(delay=2)
    def _click_refresh_cache(self):
        """Clicks on the Refresh Cache option"""
        self._driver.find_element(By.XPATH,
                                  f"//button[@aria-label='{self._admin_console.props['label.forceCacheRefresh']}']"
                                  ).click()
        self._admin_console.click_button("Close")

    @WebAction(delay=2)
    def _click_add_group(self, all_users=False):
        """Clicks on Add User Group button of Office365 OneDrive Client"""
        self._admin_console.access_tab(self._admin_console.props['label.content'])
        self._driver.find_element(By.XPATH, "//a[@id='ID_ADD_AD_GROUPS']").click()
        time.sleep(3)
        try:
            if all_users:
                self._driver.find_element(By.XPATH, "//a[@id='ALL_USERS']").click()
            else:
                self._driver.find_element(By.XPATH, "//a[@id='ADD_GROUP']").click()
        except ElementClickInterceptedException:
            if all_users:
                self._driver.find_element(By.XPATH, 
                    f"//span[text()='{self._admin_console.props['subtext.add.allOneDriveUsers']}']"
                ).click()
            else:
                self._driver.find_element(By.XPATH, 
                    f"//span[text()='{self._admin_console.props['desc.text.addOneDriveADGroup']}']"
                ).click()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _select_restore_time(self, restore_time):
        """
        Clicks on the given restore time

        Args:
            restore_time (str): Start time of backup job for
                                which items have to be restored
                                Format: Nov 5, 2020 5:35:58 PM

        """
        split_time = restore_time.split(' ')
        split_time[3] = split_time[3].split(':')
        split_time[3] = split_time[3][0] + ':' + split_time[3][1] + ' '
        restore_time = split_time[3] + split_time[4]
        retry = 5
        while retry > 0:
            retry -= 1
            try:
                self._driver.find_element(By.XPATH, 
                    f"//div[contains(@class,'cv-ProductNav_Link ng-scope')]"
                    f"//span[text()='{restore_time}']"
                ).click()
                break
            except ElementNotInteractableException:
                self._admin_console.refresh_page()

    @WebAction(delay=2)
    def open_discover_cache_info_modal(self, overview=False):
        """Opens the Discover cache info modal from Add User panel or overview"""
        if overview:
            self._driver.find_element(By.XPATH,
                                      f"//div[@id='tile-discovery-status']//descendant::button"
                                      ).click()

        else:
            try:
                self._driver.find_element(By.XPATH,
                                          f"//a[normalize-space()='{self._admin_console.props['info.usersFromCache']}']"
                                          ).click()
            except ElementClickInterceptedException:
                element = self._driver.find_element(By.XPATH,
                                                    f"//a[normalize-space()='{self._admin_console.props['info.usersFromCache']}']"
                                                    )
                self._admin_console.driver.execute_script(
                    "arguments[0].scrollIntoView();", element)
                self._admin_console.driver.execute_script(
                    "arguments[0].click();", element)

    @WebAction(delay=2)
    def _enter_browse_destination_path(self, path):
        """Clicks the browse button on the app page

                path (str)   --  The destination path to which files/users are to be restored
        """
        if self.is_react:
            self._wizard.fill_text_in_field(id='fileServerPathInput', text=path)
        else:
            input_xp = (f"//div[@class='modal-content']//label[text()='"
                        f"{self._admin_console.props['label.restoreoptions.machinePath']}"
                        f"']/following-sibling::div//input")
            self._driver.find_element(By.XPATH, input_xp).send_keys(path)

    @WebAction(delay=2)
    def _expand_restore_options_accordion(self):
        """Clicks on the Restore options accordion to expand it"""
        self._driver.find_element(By.XPATH, 
            "//span[contains(text(),'File options')]"
        ).click()

    @WebAction(delay=2)
    def _click_restore_option_radio_button(self, option):
        """
        Clicks on the radio button option under File options in restore panel

        Args:
            option:    Object of type RestoreOptions

        """
        self._driver.find_element(By.XPATH, 
            f'//input[@type="radio" and @value="{option.value}"]'
        ).click()

    @WebAction(delay=2)
    def _select_searchbar(self):
        """Clicks searchbar in onedrive browse"""
        return self._driver.find_element(By.XPATH, "//div[@class='cvSearchFilter']/input")

    @PageService()
    def get_onedrive_discovery_count(self):
        """Get the count of users in tenant that was added by discovery"""

        if self.is_react:
            try:
                self._admin_console.access_tab(self.app_type.OVERVIEW_TAB.value)
                self.open_discover_cache_info_modal(overview=True)
                cache_info_details = self.get_details_from_discover_cache_info()
            except (ElementNotInteractableException, NoSuchElementException):
                self.wait_while_discovery_in_progress()
                self.open_discover_cache_info_modal(overview=True)
                self._admin_console.wait_for_completion()
                cache_info_details = self.get_details_from_discover_cache_info()
            user_count = int(cache_info_details[self._admin_console.props['count.lastCacheUsersCount']])
            group_count = int(cache_info_details[
                                  self._admin_console.props['count.lastCacheGroupsCount']])
            cache_update_time = cache_info_details[self._admin_console.props['label.cacheUpdateTime']]
            return user_count, group_count, cache_update_time

        else:

            self._open_add_user_panel()
            self._admin_console.wait_for_completion()
            try:
                self.open_discover_cache_info_modal()
                self._admin_console.wait_for_completion()
                cache_info_details = self.get_details_from_discover_cache_info()
            except (ElementNotInteractableException, NoSuchElementException):
                self.wait_while_discovery_in_progress()
                self.open_discover_cache_info_modal()
                self._admin_console.wait_for_completion()
                cache_info_details = self.get_details_from_discover_cache_info()
            user_count = int(cache_info_details[self._admin_console.props['count.lastCacheUsersCount']])
            group_count = int(cache_info_details[
                                  self._admin_console.props['count.lastCacheGroupsCount']])
            cache_update_time = cache_info_details[self._admin_console.props['label.cacheUpdateTime']]
            self._modal_dialog.click_cancel()
            self._admin_console.wait_for_completion()
            return user_count, group_count, cache_update_time

    @PageService()
    def refresh_cache(self):
        """Refreshes the OneDrive discovery cache"""
        self._admin_console.access_tab(self.app_type.OVERVIEW_TAB.value)
        self._driver.find_element(By.XPATH, "//div[@id='tile-discovery-status']//button").click()
        self._click_refresh_cache()

    @PageService()
    def add_group(self, groups=None, plan=None):
        """
        Adds user groups to the Office 365 App
        Args:
            groups (list):  Groups to be added to the app
            plan (str):     Plan to be associated to each group

        """
        if plan:
            o365_plan = plan
        else:
            o365_plan = self.tcinputs['Office365Plan']
        if groups:
            o365_groups = groups
        else:
            o365_groups = self.groups
        self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
        self.__rtable.access_toolbar_menu('Add')
        self._wizard.select_card("Add content to backup")
        self._wizard.click_next()
        self._wizard.click_element("//div[text()='Advanced']")
        self._wizard.select_card(self.app_type.ADD_GROUP_CARD_TEXT.value)
        self._wizard.click_next()
        self._admin_console.wait_for_completion()
        for group in o365_groups:
            self.__rtable.search_for(group)
            self.__rtable.select_rows([group])
        self.log.info(f'Groups added: {o365_groups}')
        self._wizard.click_next()
        self._admin_console.wait_for_completion()
        self._wizard.select_drop_down_values(id="cloudAppsPlansDropdown", values=[o365_plan])
        self.log.info(f'Selected Office365 Plan: {o365_plan}')
        self._wizard.click_next()
        self._admin_console.wait_for_completion()
        self._wizard.click_button("Submit")
        self._admin_console.refresh_page()

    @WebAction()
    def __choose_oop_restore_option(self):
        """
        Choose the OOP Restore option by clicking the radio button
        """
        self._driver.find_element(By.XPATH, "//input[@value='OUTOFPLACE']").click()

    @WebAction()
    def __enter_dest_user_for_oop_restore(self, user_name):
        """
        Enter the destination user for OOP restore

        Args:
            user_name   --  SMTP of destination user

        """
        self._driver.find_element(By.ID, 'userAccountInput').send_keys(user_name)

    @WebAction()
    def __click_folder_browse_button_for_oop_restore(self):
        """
        For OOP restore, click on the button to browse folders of destination user
        """
        self._driver.find_element(By.XPATH, "//button[@id='browse_folder']").click()

    @WebAction()
    def __click_new_folder_button_for_oop_restore(self):
        """
        For OOP restore, click on the button to create new folder on destination user
        """
        self._driver.find_element(By.XPATH, "//button[@id='new_folder']").click()

    @WebAction()
    def __enter_folder_name_for_oop_restore(self, folder_name):
        """
        For OOP restore, enter folder name for the new folder to be created
        on destination user

        Args:
            folder_name (str)   :   Name of the new folder to be created

        """
        self._driver.find_element(By.XPATH, 
            "//input[@id='newFolderName']").send_keys(folder_name)

    @WebAction()
    def __choose_newly_created_folder_for_oop_restore(self, folder_name):
        """
        For OOP restore, choose the newly created folder on the destination user
        on destination user

        Args:
            folder_name (str)   :   Name of the newly created folder

        """
        self._driver.find_element(By.XPATH, 
            f"//input[contains(@aria-label, '{folder_name}')]"
            f"//ancestor::span[@class='k-checkbox-wrapper']"
        ).click()

    @WebAction()
    def click_folder(self, foldername):
        """
        In OneDrive browse page, click on a foldername
        Args:
            foldername(str) - The folder to click on
        """
        self._driver.find_element(By.XPATH, 
                                  "//span[contains(text(), '" + foldername + "')]").click()
        self._admin_console.wait_for_completion()

    @PageService()
    def _enter_details_in_restore_panel(self,
                                        destination,
                                        file_server=None,
                                        dest_path=None,
                                        user_name=None,
                                        restore_option=None):
        """
        Enters the details in the Restore Options panel

        Args:
            destination --  Specifies the destination
            file_server --  Name of server where files have to be restored
            dest_path   --  Path to which the files have to be restored
            user_name   --  User to which files have to be restored
            restore_option  --  Specifies what to fo if file already exists

        """
        if self.is_react:
            if destination == constants.RestoreType.TO_DISK:
                self._wizard.select_card("File location")
                self._wizard.select_drop_down_values(id="fileServersDropdown", values=[file_server])
                self._enter_browse_destination_path(dest_path)
            elif destination == constants.RestoreType.IN_PLACE:
                self._wizard.select_drop_down_values(id="agentDestinationDropdown", values=["Restore the data to its "
                                                                                            "original location"])
            elif destination == constants.RestoreType.OOP:
                self._wizard.select_drop_down_values(id="agentDestinationDropdown",
                                                     values=["Restore the data to another"
                                                             "location"])
            self._wizard.click_next()
            if restore_option:
                if restore_option == constants.RestoreOptions.OVERWRITE:
                    self._wizard.select_radio_button(id="OVERWRITE")
                elif restore_option == constants.RestoreOptions.COPY:
                    self._wizard.select_radio_button(id="RESTORE_AS_COPY")
                else:
                    self._wizard.select_radio_button(id="SKIP")
        else:
            if destination == constants.RestoreType.TO_DISK:
                self._dropdown.select_drop_down_values(
                    values=['File location'],
                    drop_down_id='restoreDestinationSummaryDropdown',
                    partial_selection=True
                )
                self._dropdown.select_drop_down_values(
                    values=[file_server],
                    drop_down_id='office365AccessNodesDropdown'
                )
                self._admin_console.wait_for_completion()
                self._enter_browse_destination_path(dest_path)
            elif destination == constants.RestoreType.IN_PLACE:
                self._dropdown.select_drop_down_values(
                    values=['OneDrive for Business'],
                    drop_down_id='restoreDestinationSummaryDropdown',
                    partial_selection=True
                )
            elif destination == constants.RestoreType.OOP:
                self._dropdown.select_drop_down_values(
                    values=['OneDrive for Business'],
                    drop_down_id='restoreDestinationSummaryDropdown',
                    partial_selection=True
                )
                self.__choose_oop_restore_option()
                self.__enter_dest_user_for_oop_restore(user_name)

                # Steps for selecting the destination folder
                self.__click_folder_browse_button_for_oop_restore()
                self._admin_console.wait_for_completion()
                self.__click_new_folder_button_for_oop_restore()
                self._admin_console.wait_for_completion()
                self.__enter_folder_name_for_oop_restore(dest_path)
                self._admin_console.submit_form()

                self.__choose_newly_created_folder_for_oop_restore(dest_path)
                time.sleep(2)  # Adding a sleep since there are two consecutive clicks
                self._admin_console.submit_form()
            if restore_option:
                self._expand_restore_options_accordion()
                self._click_restore_option_radio_button(restore_option)

    @PageService()
    def run_restore(self,
                    destination,
                    users=None,
                    file_server=None,
                    dest_path=None,
                    user_name=None,
                    restore_option=None):
        """
        Runs the restore by selecting all users associated to the app

        Args:
            destination (str):  Specifies the destination
                                Acceptable values: to_disk, in_place, out_of_place
            users (list):       List of users to be selected for Restore
            file_server (str):  Name of file server in case of restore to disk
            dest_path (str):    Path to which the files have to be restored
            user_name (str):    User to which files have to be restored in case of OOP
            restore_option:     Whether to Skip, Restore as copy or Overwrite for In-place restore

        Returns:
            job_details (dict): Details of the restore job

        """
        self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
        if users:
            for user in users:
                self._select_user(user)
        else:
            self._select_all_users()
        self._click_restore(account=True)
        self._admin_console.wait_for_completion()
        self._enter_details_in_restore_panel(
            destination=destination,
            file_server=file_server,
            dest_path=dest_path,
            user_name=user_name,
            restore_option=restore_option)
        if self.is_react:
            self._wizard.click_next()
            self._wizard.click_submit()
            self._admin_console.wait_for_completion()
            job_id = self._wizard.get_job_id()
            job_details = self._job_details(job_id)
        else:
            self._modal_dialog.click_submit()
            job_details = self._job_details()
        self.log.info('job details: %s', job_details)
        return job_details

    @PageService()
    def point_in_time_restore(self, user_name, restore_time, file_server, dest_path):
        """
        Perform Point-in-time Restore for given user

        Args:
            user_name (str):    User to be restored
            restore_time (str): Time for which restore has to be performed
                                Format: Nov 5, 2020 5:35:58 PM
            file_server (str):  Server to which data has to be restored
            dest_path (str):    Path in the file server

        Returns:
            job_details (dict): Details of the restore job

        """
        self._view_user_details(user_name)
        self._select_restore_time(restore_time)
        self._admin_console.select_hyperlink('Restore')
        self._admin_console.wait_for_completion()
        self._click_selectall_browse()
        self._click_restore()
        self._admin_console.wait_for_completion()
        self._enter_details_in_restore_panel(
            destination=constants.RestoreType.TO_DISK,
            file_server=file_server,
            dest_path=dest_path)
        self._modal_dialog.click_submit()
        return self._job_details()
    
    @PageService()
    def run_browse_restore(self,
                           destination,
                           file_server=None,
                           dest_path=None,
                           user_name=None,
                           restore_option=None):
        """
                Perform Restore from browse page

                Args:
                    destination (str):  Specifies the destination
                                Acceptable values: to_disk, in_place, out_of_place
                    file_server (str):  Name of file server in case of restore to disk
                    dest_path (str):    Path to which the files have to be restored
                    user_name (str):    User to which files have to be restored in case of OOP
                    restore_option:     Whether to Skip, Restore as copy or Overwrite for In-place restore

                Returns:
                    job_details (dict): Details of the restore job

        """
        self._click_selectall_browse()
        self._click_restore()
        self._admin_console.wait_for_completion()
        self._enter_details_in_restore_panel(
            destination=destination,
            file_server=file_server,
            dest_path=dest_path,
            user_name=user_name,
            restore_option=restore_option)
        self._modal_dialog.click_submit()
        return self._job_details()

    @PageService()
    def browse_keyword_search(self, searchterm):
        """Search using a keyword in onedrive browse"""
        elem = self._select_searchbar()
        elem.send_keys(searchterm)
        self._admin_console.wait_for_completion()

    @PageService()
    def verify_cache_is_fetched(self):
        """Verify that existing cache is fetched"""
        self._click_add_group()
        if self._admin_console.check_if_entity_exists(
                'id', 'office365OneDriveAddAssociation_isteven-multi-select_#5444'):
            self.log.info('VERIFIED: Existing cache is fetched')
            self._modal_dialog.click_cancel()
        else:
            raise CVWebAutomationException(
                'Existing cache is not fetched when Auto-discovery is running')

    @PageService()
    def remove_from_content(self, user=None, is_group=False):
        """
        Excludes the given user from backup
        Args:
            user (str):         User which has to be deleted
            is_group (bool):    Whether user/group is to be deleted
        """
        if user:
            self._select_user(user, is_group=is_group)
        else:
            self._select_user(self.users[0], is_group=is_group)
        self._click_remove_content(user=user)
        self._admin_console.wait_for_completion()
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        self.log.info(f'User removed from content: {user}')

    @PageService()
    def get_jobs_count(self):
        """Get the count of jobs in the job history of client"""
        return int(self.__rtable.get_total_rows_count())

    @PageService()
    def run_ci_job(self, client_name, return_status=False):
        """
        Runs the content indexing job for OneDrive app and verifies
        job completes successfully

            client_name:- name of the client
            return_status: Returns the job status if value set to True
        """

        self.access_office365_app(client_name)
        self._admin_console.access_tab("Users")
        self._select_all_users()
        self._click_more_actions()
        self._click_ci_path()
        self._Rmodal_dialog.click_submit()

        self._navigator.navigate_to_jobs()
        try:
            self._jobs.access_active_jobs()
            self._jobs.add_filter(column='Server', value=client_name)
            self._jobs.add_filter(column='Operation', value='Content Indexing')
        except:
            self._admin_console.refresh_page()
            self._jobs.access_admin_jobs()
            self._jobs.add_filter(column='Server', value=client_name)
            self._jobs.add_filter(column='Operation', value='Content Indexing')

        jobid = self._jobs.get_job_ids()[0]

        job_details = self._jobs.job_completion(job_id=jobid)
        self.log.info(f"Job details are: {job_details}")
        if return_status:
            return job_details[self._admin_console.props['Status']]
        else:
            if job_details[self._admin_console.props['Status']] != "Completed":
                raise CVWebAutomationException(
                    "CI job did not completed successfully. Please check logs for more details")

    @PageService()
    def get_facet_details_of_single_file(self, facet_list):
        """
        get facet details of file
        Args:
            facet_list (list): list of facets
        Returns:
             result (dict): dict containing facet and its value
        """
        facet_dict = {}
        for each_facet in facet_list:
            facet_obj=FacetPanel(self._admin_console,each_facet)
            values = facet_obj.get_values_from_facet()
            facet_dict[each_facet] = (values[0].split("(")[0]).rstrip()
        self.__searchfilter.clear_search()
        return facet_dict

    @PageService()
    def click_facet(self, facet_name,facet_value):
        """
        clicks the required facet in browse
        Args:
            facet_name (str): name of facet applied
            facet_value (str): value of facet
        Returns:
             result (list): list containing browse response
        """
        facet_obj=FacetPanel(self._admin_console,facet_name)
        facet_obj.click_value_of_facet(facet_value)
        browse_response = self.get_browse_table_content()
        self.__searchfilter.clear_search()
        return browse_response

    @PageService()
    def apply_dropdown_type_search_filter(self, filter_config):
        """
        to apply dropdown search filter in browse section
         Args:
            filter_config (list):         filter configuration

        Returns:
             browse_response (list of dicts): returns the response after applying filter
        """
        self.__searchfilter.click_filter()
        self.__searchfilter.apply_dropdown_type_filter(filter_config[0], [filter_config[1]])
        self.__searchfilter.submit()
        browse_response = self.get_browse_table_content()
        self.__searchfilter.clear_search()
        return browse_response

    @PageService()
    def apply_advance_search_filter(self, filter_config):
        """
        to apply advance search filter with dropdown and input in browse section
         Args:
            filter_config (list):         filter configuration

        Returns:
             browse_response (list of dicts): returns the response after applying filter
        """
        self.__searchfilter.click_filter()
        self.__searchfilter.apply_dropdown_type_filter(filter_config[0],[filter_config[1]])
        self.__searchfilter.apply_input_type_filter(filter_config[2],filter_config[3])
        self.__searchfilter.submit()
        browse_response = self.get_browse_table_content()
        self.__searchfilter.clear_search()
        return browse_response

    def compare_file(self, file_name, browse_response):
        """
        to compare the response of searched file with actual file details

        Args:
            file_name (str):                       Name of the file
            browse_response (list of dicts):       response recieved after searching the file

        Returns:
             result (str): returns whether file is matched or not

        """
        result = "File Matched"
        for each_response in browse_response:
            if (each_response['Name'] != file_name):
                result = "File Not Matched"
        return result

    def compare_facets_of_file(self, actual_dict, facet_dict):
        """
        to compare the dictionary with actual file details and dictionary with values taken from facets

        Args:
            actual_dict (dict): dictionary with actual file details
            facet_dict (dict):  dictionary with values taken from facets

        Returns:
             result (str): returns whether dictionaries are matched or not

        """
        result = "Facets of File Matched"
        if actual_dict != facet_dict:
            return "Facets of File Not Matched"
        return result

    def compare_facet_response(self, facet_name,facet_value, facet_response):
        """
                to compare facet value and response after applying facet

                Args:
                    facet_name (str)              : name of facet applied
                    facet_value(str)              : value of facet
                    facet_response (list of dicts):  response after applying facet

                Returns:
                     result (str): returns whether results after applying facet are matched or not

                """
        if facet_name == "File extension":
            result = "File extension Facet Matched"
            file_extension = facet_value
            for each_response in facet_response:
                file_name = each_response["Name"].split(".")
                if file_name[-1] != file_extension:
                    result = "File extension Facet Not Matched"
            return result

        if facet_name == "User":
            result = "User Facet Matched"
            user = facet_value
            for each_response in facet_response:
                if each_response["User"] != user:
                    result = "User Facet Not Matched"
            return result

    def compare_filter_response(self, filter_config, browse_response):
        """
        to compare search filter

        Args:
            filter_config (list): filter configuration
            browse_response(list of dicts): response after applying filter

        Returns:
             result (str): returns whether applied filters are matched or not

        """
        result = ""
        if "searchType" in filter_config:
            if filter_config[1] == "PDFs":
                for each_response in browse_response:
                    str = each_response["Name"].split(".")
                    if str[-1] != "pdf":
                        result = "type filter is not matched"
                        break

            if filter_config[1] == "Documents":
                for each_response in browse_response:
                    str = each_response["Name"].split(".")
                    if str[-1] != "docx":
                        result = "type filter is not matched"
                        break

        if "customUserName" in filter_config:
            for each_response in browse_response:
                if each_response["User"] != filter_config[3]:
                    result = "user filter not matched"
                    break

        if "customLocation" in filter_config:
            for each_response in browse_response:
                if each_response["Location"] != (filter_config[3] + "\\" + each_response["Name"]):
                    result = "location filter not matched"
                    break

        return result


class OneDriveContentIndexing:
    """Class for Content indexing operations for OneDrive"""

    def __init__(self, cvcloud_object):
        self._solr_helper_obj = None
        self.cvcloud_object = cvcloud_object

    def get_document_count_in_index(self, csdb_helper, mssql, job_id):
        """
        Query Index Server wrt Job Id to get Document count

        Args:
            csdb_helper: csdb helper object
            job_id: Job Id of backup job
            mssql: mssql object

        """
        query_url = csdb_helper.get_index_server_url(mssql, job_id)
        query_url += '/select?'
        self._solr_helper_obj = SolrHelper(self.cvcloud_object, query_url)
        solr_results = self._solr_helper_obj.create_url_and_get_response(
            {'JobId': job_id, 'DocumentType': '1'})

        backup_count = int(self._solr_helper_obj.get_count_from_json(solr_results.content))

        return backup_count

    def get_content_indexing_job_id(self, commcell, subclient_id):
        """Gets ContentIndexing JobID from active jobs"""

        _job_controller = JobController(commcell)
        jobs_list = _job_controller.active_jobs()

        content_indexing_job = None

        for jobID in jobs_list:
            if jobs_list[jobID]['job_type'] == 'Content Indexing' and jobs_list[jobID]['subclient_id'] == subclient_id:
                content_indexing_job = jobID

        return content_indexing_job

    def get_ci_details_from_index(self, csdb_helper, mssql, job_id):
        details = {}
        query_url = csdb_helper.get_index_server_url(mssql, job_id)
        query_url += '/select?'
        self._solr_helper_obj = SolrHelper(self.cvcloud_object, query_url)
        solr_results = self._solr_helper_obj.create_url_and_get_response(
            {'JobId': job_id, 'DocumentType': '1', 'ContentIndexingStatus': '1'})

        solr_count = int(self._solr_helper_obj.get_count_from_json(solr_results.content))

        details["Success"] = solr_count

        solr_results = self._solr_helper_obj.create_url_and_get_response(
            {'JobId': job_id, 'DocumentType': '1', 'ContentIndexingStatus': '2'})

        solr_count = int(self._solr_helper_obj.get_count_from_json(solr_results.content))

        details["Failed"] = solr_count

        solr_results = self._solr_helper_obj.create_url_and_get_response(
            {'JobId': job_id, 'DocumentType': '1', 'ContentIndexingStatus': '3'})

        solr_count = int(self._solr_helper_obj.get_count_from_json(solr_results.content))

        details["Skipped"] = solr_count

        solr_results = self._solr_helper_obj.create_url_and_get_response(
            {'JobId': job_id, 'DocumentType': '1', 'ContentIndexingStatus': '0'})

        solr_count = int(self._solr_helper_obj.get_count_from_json(solr_results.content))

        details["NotProcessed"] = solr_count

        return details

