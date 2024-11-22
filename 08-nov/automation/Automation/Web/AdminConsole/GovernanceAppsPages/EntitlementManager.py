from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Entitlement Manager page

Classes:

    EntitlementManager() ---> GovernanceApps() ---> object()
    _BrokenPermissionBrowser()


EntitlementManager --  This class contains all the methods for action in
    Entitlement Manager page

    Functions:
    expand_tree() : Traverse all the nodes
    read_nodes_permissions() : Select all files/folders and read permission
    load_project() : Load a project name in Entitlement Manager
    perform_permission_change() : Perform permission change for a filer/folder
    revert_permission_to_point() : Revert permission to a point for an user for a filer/folder


_BrokenPermissionBrowser -- This class contains all the methods to Browse/load broken permissions

    Functions:
    _initialize_report_components() : Initializes custom report components
    _select_report_tab() : Selects report tab
    _select_folder_by_index() : Selects folder from table by index
    run_fix_permission_job() : Runs a fix permissions job
    search_for_folder() : Searches for a folder in table
    select_ignore_folder() : Selects ignore folder tab
    select_review_permission() : Selects review permissions tab
    select_mismatched_permission() : Select mismatched permissions filter
    select_disabled_inheritance() : Select inheritance disabled filter
    get_folder_to_review_count() : Returns folders count to review
    get_total_folder_count() : Returns total number of folders present in Datasource
    refresh_report() : Refreshes the report

"""

import time
from selenium.common import exceptions
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.exceptions import CVWebAPIException, CVWebAutomationException
from Web.Common.page_object import WebAction, PageService


class EntitlementManager:
    """
     This class contains all the methods for action in Entitlement Manager page
    """

    browse = None
    load = None
    active = None
    audit = None
    action = None
    constants = None
    broken = None

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__admin_console.load_properties(self)
        self.__driver = self.__admin_console.driver
        self.browse = _EntityBrowser(self.__admin_console)
        self.load = _ProjectBrowser(self.__admin_console)
        self.audit = _Audit(self.__admin_console)
        self.action = _Actions(self.__admin_console)
        self.broken = _BrokenPermissionBrowser(self.__admin_console)
        self.constants = _Constants()

    @PageService()
    def select_review(self):
        """Selects review tab"""
        self.__admin_console.access_tab("Review")


class _BrokenPermissionBrowser:
    """
            Browse/load broken permissions
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._browser = self._admin_console.browser
        self.__driver = self._admin_console.driver
        self.__constant = _Constants()
        self.__rdrop_down = RDropDown(self._admin_console)
        self.__rtable = Rtable(self._admin_console, id="ReviewPermissionGrid")
        self.__rdialog = RModalDialog(self._admin_console)

    @WebAction()
    def _select_folder(self, row_data, select_all=False):
        """Selects the checkbox on first folder from the folder list table"""
        if select_all:
            self.__rtable.select_all_rows()
        else:
            self.__rtable.select_rows([row_data])

    @PageService()
    def run_fix_permission_job(self, folder_path):
        """Run fix permissions on folder and returns the job id"""
        self.search_for_folder(folder_path)
        self._select_folder(row_data=folder_path)
        self._admin_console.click_button_using_text(value="Fix permissions")
        self.__rdialog.click_yes_button()
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def search_for_folder(self, search_entity):
        """Inserts given entity text to the search box on broken permissions report"""
        self.__rtable.search_for(keyword=search_entity)

    @PageService()
    def select_ignore_folder(self):
        """Selects ignored folders report tab"""
        self._admin_console.click_button(id="ignored")

    @PageService()
    def select_review_permission(self):
        """Selects review folder permissions report tab"""
        self._admin_console.click_button(id="to-be-reviewed")

    @PageService()
    def select_mismatched_permission(self):
        """Selects facet filter for mismatched permission folder"""
        self.__rdrop_down.select_drop_down_values(
            drop_down_id="Filter by",
            values=["Mismatched permissions"],
            facet=True, partial_selection=True)

    @PageService()
    def select_disabled_inheritance(self):
        """Selects facet filter for disabled inheritance folder"""
        self.__rdrop_down.select_drop_down_values(
            drop_down_id="Filter by",
            values=["Disabled inheritance"],
            facet=True, partial_selection=True)

    @PageService()
    def get_folder_to_review_count(self):
        """Gets folder to review count from report"""
        return self.__rtable.get_grid_stats().get("Folders to review", 0)

    @PageService()
    def get_total_folder_count(self):
        """Gets the total folders count from report"""
        return self.__rtable.get_grid_stats().get("Total folders", 0)

    @PageService()
    def refresh_report(self):
        """Reloads the data on broken permissions report"""
        self.__rtable.reload_data()


class _EntityBrowser:
    """
            Browse files/folders
    """
    all_permissions = []

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.constants = _Constants()

    @WebAction()
    def _fetch_load_more(self):
        """
            Fetch load more elements
        """
        elements = self._admin_console.driver.find_elements(By.XPATH, 
            "//span[@class='loadMoreLink']")
        return elements

    @WebAction()
    def _scroll_into_view(self, element):
        """
        Scroll element into view
        Args:
            element (WebElement): element to be brought in view
        """
        self._admin_console.driver.execute_script("arguments[0].scrollIntoView();",
                                                  element)

    @PageService()
    def _expand_all_offset(self):
        """
                Load all trees beyond offsets
        """
        more_elements = True
        while more_elements:
            elements = self._fetch_load_more()
            if len(elements) == 0:
                more_elements = False
            for element in elements:
                try:
                    self._scroll_into_view(element)
                    element.click()
                    self._admin_console.wait_for_completion(30)
                except exceptions.StaleElementReferenceException as e:
                    self._admin_console.log.info(e)

    @WebAction()
    def _read_file_path(self):
        """
            Read file name
            Returns:
                str : file_name

        """
        file_name_path = "//div[@class='permissions-panel']//*/h5"
        file_name = self._admin_console.driver.find_element(By.XPATH, file_name_path).text
        file_name = file_name.replace(self.constants.FILE_DELIMITER, "\\")
        return file_name

    @WebAction()
    def _fetch_user_elements(self):
        """
            Fetch user elements
            Returns:
                user elements
        """
        user_path = "//cv-permissions-grid//*/td[@id='cv-k-grid-td-displayName']"
        users_elements = self._admin_console.driver.find_elements(By.XPATH, user_path)
        return users_elements

    @WebAction()
    def _fetch_permission_elements(self):
        """
            Fetch permission elements
            Returns:
                permission elements
        """
        permission_path = "//cv-permissions-grid//*/td[@id='cv-k-grid-td-aggregatedSummary']"
        permissions_elements = self._admin_console.driver.find_elements(By.XPATH, permission_path)
        return permissions_elements

    @PageService()
    def _read_permission(self):
        """
                   Read current node permission
        """
        permissions = {}
        users_elements = self._fetch_user_elements()
        permissions_elements = self._fetch_permission_elements()
        file_name = self._read_file_path()
        if len(users_elements) == 0 and len(permissions_elements) == 0:
            print("Nothing to be processed.")
        else:
            index = 0
            permissions[self.constants.FILE_NAME] = file_name
            for users_element in users_elements:
                user = users_element.text
                permission = permissions_elements[index].text
                permissions[user] = permission
                index = index + 1
            self.all_permissions.append(permissions)

    @WebAction()
    def _fetch_nodes(self, path):
        """
            Fetch nodes
        """

        nodes = self._admin_console.driver.find_elements(By.XPATH, path)
        return nodes

    @PageService()
    def read_nodes_permissions(self, specific_file=None):
        """
            Select all files/folders and read permission
            :param specific_file - if passed, then browse to specific file
            :return all permissions
        """
        try:
            path = "//cv-directory-tree//*/tr[@role='row']/child::td[@role='gridcell']"
            self._expand_all_offset()
            nodes = self._fetch_nodes(path)
            for node in nodes:
                try:
                    self._scroll_into_view(node)
                    current_file = node.text
                    self._admin_console.log.info("Current file {}".format(current_file))
                    node.click()
                    self._read_permission()
                    if current_file.strip() == specific_file.strip():
                        self._admin_console.log.info("Found the file [{}]".format(specific_file))
                        break
                except Exception as e:
                    nodes = self._fetch_nodes(path)

        except Exception as e:
            raise CVWebAPIException(
                f"Node is either stale or invalid"
            ) from e

    @PageService()
    def expand_tree(self):
        """
             Traverse all the nodes
        """

        try:
            path = "//cv-directory-tree//*/tr[@role='row']/child::td[@role='gridcell']" \
                   "/child::span[contains(@class,'k-i-expand')]"
            more_sub_tree = True

            while more_sub_tree:
                nodes = self._fetch_nodes(path)
                if len(nodes) == 0:
                    self._admin_console.log.info("Nothing to traverse.")
                    more_sub_tree = False
                for node in nodes:
                    try:
                        self._scroll_into_view(node)
                        node.click()
                        self._admin_console.wait_for_completion(5)
                    except exceptions.StaleElementReferenceException as exception:
                        self._admin_console.log.info(exception)

        except exceptions.StaleElementReferenceException as exception:
            self._admin_console.log.info(exception)


class _ProjectBrowser:
    """
            Browse/Load activate projects
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__dropdown = RDropDown(admin_console)

    @WebAction()
    def _search_select_project(self, project_name):
        """
         Search and select an project_name
         :param entity_type_list (list): list of entities to select
        """
        self.__dropdown.select_drop_down_values(drop_down_id="ServerDropdown", values=project_name)

    @PageService()
    def load_project(self, project_name, datasource_name=None):
        """
        Browse to project name

            Args:
                project_name (str)  - project name details to be navigated
                :raise If project is not found

                datasource_name (str)   -   datasource name details to be navigated

        """
        if isinstance(project_name, str):
            project_name = [project_name]
        if isinstance(datasource_name, str):
            datasource_name = [datasource_name]
        self._search_select_project(project_name)
        if datasource_name:
            self.__dropdown.select_drop_down_values(
                drop_down_id="dataSourceDropDown", values=datasource_name)
        self._admin_console.check_error_message()


class _Audit:
    """
            Audit activities after any action
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console


class _Actions:
    """
            Supported file/folders actions
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._panel = RPanelInfo(self._admin_console)
        self._table = Rtable(self._admin_console)

    @WebAction()
    def _review_permission_change(self):
        """
        Review permission change
        """
        self._admin_console.access_tile('ReviewChanges')

    @WebAction()
    def _apply_permission_change(self):
        """
        Apply permission change
        """
        self._admin_console.click_button("Apply permission")

    @WebAction()
    def _click_add_new_user(self):
        """
            Click add new user
        """
        self._admin_console.access_tile("AddNewUserButton")

    @WebAction()
    def _click_add(self):
        """
            Click add
        """
        self._admin_console.click_button("Add")

    @WebAction()
    def _select_file_activity(self):
        """
            Select file activity
        """
        self._panel.open_hyperlink_on_tile('Permission activity')

    @WebAction()
    def _click_revert_to_point(self, user_name):
        """
        Click revert permission to point for an user
        : user: user to revert permission for
        """
        self._table.access_action_item(user_name, "Revert to this point")
        self._admin_console.wait_for_completion()

    @WebAction()
    def _click_revert(self):
        """
        Click revert button
        """
        self._admin_console.click_button("Revert")
        self._admin_console.wait_for_completion()

    @WebAction()
    def _select_all_permissions(self):
        """
            Select all available permission changes to revert
        """
        xpath = "//table[contains(@id,'permissionsMain')]//tbody//tr"
        permissions = self._admin_console.driver.find_elements(By.XPATH, xpath)
        for permission in permissions:
            if not permission.find_element(By.XPATH, 
                    ".//following-sibling::input").is_selected():
                element = permission.find_element(By.XPATH, 
                    ".//following-sibling::label")
                self._admin_console.driver.execute_script(
                    "arguments[0].click();", element)
                self._admin_console.wait_for_completion()

    @WebAction()
    def _search_user(self, user):
        """
            Search for an user
            Args:
                user (str): user
            Returns:
                bool : True/False
        """
        xpath = "//input[contains(@name, 'searchComponent')]"
        if self._admin_console.check_if_entity_exists("xpath", xpath):
            search = self._admin_console.driver.find_element(By.XPATH, xpath)
            search.send_keys(user)
            self._admin_console.wait_for_completion()
            return True
        return False

    @WebAction()
    def _select_user(self):
        """
            Select user
            Returns:
                bool : True/False
        """
        xpath = "//div[contains(@class,'result-item')]/h5"
        if self._admin_console.check_if_entity_exists(
                "xpath", xpath):
            self._admin_console.driver.find_element(By.XPATH, xpath).click()
            return True
        return False

    @PageService()
    def _search_select_user(self, user):
        """
        Search and select an active directory user
        Args:
            user (str) : user to search and select
        Raises:
            CVWebAutomationException : if user can not be found and selected
        """
        if self._search_user(user):
            if self._select_user():
                self._admin_console.log.info("User {} is selected.".format(user))
            else:
                raise CVWebAutomationException(
                    "User [{}] is not selected".format(user))
        else:
            raise CVWebAutomationException(
                "User [{}] is not found".format(user))

    @PageService()
    def _add_new_user(self, new_user):
        """
        Add new user
        Args:
            new_user (str) : new active directory user
        """
        self._click_add_new_user()
        self._search_select_user(new_user)
        self._click_add()

    @WebAction()
    def read_change_permission_status(self):
        """
            Read change permission status
        """
        status = self._admin_console.driver.find_element(By.CLASS_NAME, 
            "permissionsPreviewModalBody").text
        return status

    @PageService()
    def _track_change_permission(self):
        """
        Track change permission job status
        """
        import time
        n_success = True
        i = 0
        poll_retries = 10
        while i < poll_retries:
            status = self.read_change_permission_status()
            if status.find("applied successfully") == -1:
                if i > poll_retries:
                    n_success = False
                else:
                    time.sleep(30)
                    i = i + 1
                    continue
            else:
                self._admin_console.log.info(
                    "Change permission applied.")
                break
        self._admin_console.click_button("Ok")
        return n_success

    @WebAction()
    def read_revert_permission_status(self):
        """
            Read revert permission status
        """
        status = self._admin_console.driver.find_element(By.CLASS_NAME, 
            "activitiesRevertModalBody").text
        return status

    @PageService()
    def _track_revert_permission(self):
        """
        Track revert permission status
        """
        import time
        n_success = True
        i = 0
        poll_retries = 10
        while i < poll_retries:
            status = self.read_revert_permission_status()
            if status.find("applied successfully") == -1:
                if i > poll_retries:
                    n_success = False
                else:
                    time.sleep(30)
                    i = i + 1
                    continue
            else:
                self._admin_console.log.info(
                    "Revert permission completed.")
                break
        self._admin_console.click_button("Ok")
        return n_success

    @PageService()
    def perform_permission_change(self, new_user):
        """
        Perform permission change on a file/folder
        Args:
            new_user (str) - user to be added in permission list
        Returns:
            bool : True/False
        """
        self._add_new_user(new_user)
        self._review_permission_change()
        self._apply_permission_change()
        if self._track_change_permission():
            return True
        return False

    @PageService()
    def revert_permission_to_point(self, user_name):
        """
        Revert permission to a point for an user for a filer/folder
        Args:
            user_name (str) : User account who is affecting the change
        Returns:
            bool : True/False
        """
        self._select_file_activity()
        self._click_revert_to_point(user_name)
        self._select_all_permissions()
        self._click_revert()
        if self._track_revert_permission():
            return True
        return False


class _Constants:
    """
    Constants required for entitlement management
    """
    FILE_NAME = "file_name"
    USER = "user"
    FILE_DELIMITER = "  >  "
    FIX_PERMISSION_BUTTON_TEXT = "Fix permissions"
