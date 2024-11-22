# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Module for browse page

Browse:

    access_folder()               :       Navigates to the file path

    select_tableview()            :       Selects table view from dropdown to browse tables.

    access_table_action_item      :       Selects option from action-dropdown for given entity.

    select_multiple_version_of_files():   Selects Multiple versions of file to restore

    select_hidden_items()         :       Selects hidden items to restore

    select_deleted_items_for_restore():   Selects deleted files or folders to restore

    select_for_preview()          :       Select to view the file

    close_preview_file()          :       Closes the preview file

    select_for_restore()          :       Selects files and folders to restore

    show_latest_backups()         :       Selects the latest backup

    select_adv_options_submit_restore(): Restores from the selected option

    show_backups_by_date_range()  :       Selects backups by daterange and picks
                                          from and to time

    submit_for_restore()          :       Restores the selected files

    submit_for_download()         :       Downloads the selected files

    select_path_for_restore()     :      Expand the source path and
                                         selects files and folders to be restore

    select_from_multiple_pages    :     Selects files/items from multiple pages in browse window

    select_from_actions_menu      :     Selects files/items whose related items must be selected from actions menu.

    switch_to_collections_view    :     Switches to collection view

    get_restore_nodelist          :     returns restore node list

    get_restore_copies_for_plan   :     Returns the copies available for restore from a region-based storage plan

    get_folders_from_tree_view    :     Fetch the folders names from the tree view

ContentBrowse:

    select_path()                 :       selects folder/files

    get_path()                    :       list all folders shown in browse panel

    save_path()                   :       Saves the selected path

RContentBrowse:

    Functions:

    select_content()                :       selects the content in tree structure

    select_path()                 :       selects folder/files

    get_path()                    :       list all folders shown in browse panel

    save_path()                   :       Saves the selected path

CVAdvancedTree:

    select_elements()               :       Selects CV Advanced Tree Type Elements

RBrowse:

    access_folder()                 :       Access a folder from Browse table

    clear_all_selection()           :       Clear all selections from table

    close_preview_file()            :       Close the preview panel of file

    get_column_data()               :       Get the data of a particular column from Browse table

    navigate_path()                 :       Navigate to a folder location using tree or row links

    reset_folder_navigation()       :       Reset the browse table to root folder

    select_action_dropdown()        :       Select value from a dropdown in action panel

    select_deleted_items_for_restore:       Select deleted files from restore table

    select_files()                  :       Select files from table

    select_for_preview()            :       Navigate to folder location and preview a file

    select_hidden_items()           :       Select hidden files from restore table

    select_multiple_version_of_files:       Display multiple versions of a file and select the rows

    select_path_for_restore()       :       Navigate to folder location and select files from table

    select_storage_copy()           :       Select the storage copy for the subclient

    show_backups_by_date_range()    :       Specify the time range to select backup date from

    show_latest_backups()           :       Display the latest backup data

    submit_for_download()           :       Click on the 'Download' button

    submit_for_restore()            :       Click on the 'Restore' button

    select_tableview()              :       Selects table view from dropdown to browse tables

    select_from_multiple_pages()    :       Selects files/items from multiple pages in restore browse window

    select_from_actions_menu()      :       Selects files/items whose related items must be selected from actions menu

Integration for Browse component is added in TC 58048, for any new methods added here,
add the corresponding integration method

"""
import os

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver import Keys

from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.core import TreeView, CalendarView, Checkbox
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction
from AutomationUtils import logger


class Browse:
    """ Class for restoring selected files and folders """

    def __init__(self, admin_console, is_new_o365_browse: bool = False):
        self.__driver = admin_console.driver
        self.__admin_console = admin_console
        self.__selected_files = []
        self.__admin_console.load_properties(self)
        self.__xp = "//div[@class='ui-grid-canvas']"
        self._is_o365_browse: bool = is_new_o365_browse
        self._table = Table(admin_console)

    @WebAction()
    def __select_dropdown(self, restore_options=False, show_backup=False, cluster_view=False):
        """ selects dropdown
        Args:
            restore_options     (bool)      selects 'restore from copy' dropdown
            show_backup         (bool)      selects 'show backup by latest/daterange' dropdown
            cluster_view        (bool)      selects 'collections/replica set view' dropdown
        """
        if restore_options:
            self.__driver.find_element(By.XPATH,
                                       "//a[@class='uib-dropdown-toggle ng-binding dropdown-toggle'"
                                       " and contains(text(), 'Restore from')]").click()
        elif show_backup:
            self.__driver.find_element(By.XPATH,
                                       "//a[@class='uib-dropdown-toggle ng-binding dropdown-toggle'"
                                       " and contains(text(), 'Show')]").click()
        elif cluster_view:
            self.__driver.find_element(By.XPATH,
                                       "//a[@class='uib-dropdown-toggle ng-binding dropdown-toggle'"
                                       " and contains(text(), 'Restore c')]").click()
        else:
            self.__driver.find_element(By.XPATH,
                                       "//a[@class='uib-dropdown-toggle ng-binding dropdown-toggle'  "
                                       "and not(contains(text(), 'Restore from'))]").click()

    @WebAction()
    def __select_keyspaceview_dropdown(self):
        """ selects keyspace/cluster view dropdown for cassandra
        """
        self.__driver.find_element(By.XPATH,
                                   "//a[@class='uib-dropdown-toggle ng-binding dropdown-toggle'"
                                   " and contains(text(), ' view')]").click()

    @WebAction()
    def __click_keyspace_view(self):
        """  selects Keyspace view from cassandra keyspace/cluster view dropdown"""
        self.__driver.find_element(By.XPATH,
                                   "//li/a[contains(text(),'Keyspace view')]").click()

    @WebAction()
    def __click_cluster_view(self):
        """  selects Cluster view from cassandra keyspace/cluster view dropdown"""
        self.__driver.find_element(By.XPATH,
                                   "//li/a[contains(text(),'Cluster view')]").click()

    @WebAction()
    def __click_table_view(self):
        """ selects Table view from Oracle Tablespace_view dropdown"""
        self.__driver.find_element(By.XPATH,
                                   "//li/a[contains(text(),'Table view')]").click()

    @WebAction()
    def __click_latest_backup(self):
        """ selects latest backup """
        self.__driver.find_element(By.XPATH,
                                   "//a[contains(text(),'Show latest backup')]").click()

    @WebAction()
    def __click_daterange_backup(self):
        """  selects show backups by date range  """
        elem = "//a[contains(text(),'" + self.__admin_console.props['Show_backups_date_range'] + "')]"
        self.__driver.find_element(By.XPATH, elem).click()

    @WebAction()
    def __click_backups_by_specific_date(self):
        """  selects show backup by specific date"""
        elem = "//a[contains(text(),'" + \
               self.__admin_console.props['Show_backups_specific_date'] + "')]"
        self.__driver.find_element(By.XPATH, elem).click()

    @WebAction()
    def __click_primary_copy_restore(self):
        """  selects restore from primary copy"""
        self.__driver.find_element(By.XPATH,
                                   "//a[contains(text(),'Primary') and"
                                   " not(contains(text(),'snap')) and"
                                   " not(contains(text(),'Snap'))]").click()

    @WebAction()
    def __click_restore(self):
        """ clicks restore """

        _xp = "//*[contains(text(),'Restore') and contains(@data-ng-class,'btn btn-primary')]"
        ad_xp = "//*[@id='browseActions']//a[contains(text(),'Restore')]"

        if self.__admin_console.check_if_entity_exists("xpath", _xp):
            self.__driver.find_element(By.XPATH, _xp).click()

        elif self.__admin_console.check_if_entity_exists("xpath", ad_xp):
            self.__driver.find_element(By.XPATH, ad_xp).click()

        else:
            raise CVWebAutomationException("Xpath for clicking restore button isn't valid")

    @WebAction()
    def __click_download(self):
        """ clicks download """
        xp = "//a[contains(text(),'Download') and contains(@data-ng-class,'btn btn-primary')]"
        self.__driver.find_element(By.XPATH, xp).click()

    @WebAction(delay=1)
    def __select_all(self):
        """ selects All files and folders to restore"""
        if self._is_o365_browse:
            elem = self.__driver.find_element(By.XPATH,
                "//input[@data-role='checkbox' and @aria-label='Select all rows']")
            if 'false' in elem.get_attribute('aria-checked'):
                xp = "//input[@data-role='checkbox' and @aria-label='Select all rows']/.."
                self.__driver.find_element(By.XPATH, xp).click()
        else:
            elem = self.__driver.find_element(By.XPATH,
                "//div[@class='ui-grid-cell-contents']/div[@ng-model='grid.selection.selectAll']")
            if 'selected' not in elem.get_attribute('class'):
                elem.click()

    @WebAction()
    def select_all(self):
        """Selects All files and folders to restore"""

        self.__select_all()

    @WebAction()
    def __browse_elements(self, second_column=False):
        """ Browses all elements in the page
        Args:
            second_column   (Boolean):True to select files/items from second column of browse page
                                      False to select files/items from first column of browse page

                            Default: False
        """
        if not second_column:
            elements = self.__driver.find_elements(By.XPATH,
                                                   "(//div[@class='ui-grid-row ng-scope']//div[@role='gridcell'][1]) | //td[@role='gridcell'][2]")
        else:
            elements = self.__driver.find_elements(By.XPATH,
                                                   "//div[@class='ui-grid-row ng-scope']//div[@role='gridcell'][2]")
        return [elem.text for elem in elements if elem.is_displayed()]

    @WebAction()
    def __read_column_data(self, column_idx):
        """ reads column data """
        elements = self.__driver.find_elements(By.XPATH,
                                               f"//div[@class='ui-grid-row ng-scope']//div[@role='gridcell'][{column_idx}]"
                                               )
        return [elem.text for elem in elements if elem.is_displayed()]

    @WebAction()
    def __read_column_names(self):
        """ read column names """
        elements = self.__driver.find_elements(By.XPATH,
                                               "//div[@class='ui-grid-header-canvas']"
                                               "//span[@class='ui-grid-header-cell-label ng-binding']"
                                               )
        return [elem.text for elem in elements if elem.is_displayed()]

    @WebAction()
    def __click_elem_checkbox(self, index):
        """ Clicks element checkbox

        Args:
            index (int) : Index of the file in page

        """
        self.__driver.find_element(By.XPATH,
                                   f"//div[@class='ui-grid-canvas']/div[{index}]//"
                                   f"div[@ng-click='selectButtonClick(row, $event)']").click()

    @WebAction()
    def __available_folders(self):
        """ Lists all available paths

        Returns (list) : available paths

        """
        self.__admin_console.unswitch_to_react_frame()
        elements = self.__driver.find_elements(By.XPATH,
                                               "//div[@class='ui-grid-canvas']//a")
        return [elem.text for elem in elements]

    @WebAction()
    def __click_access_path(self, title):
        """ Lists and clicks the element if path exists

        Args:
            title (str) : file path (eg- ['folder1','Hackathon'] )

        """
        self.__driver.find_element(By.XPATH,
                                   f"//div[@class='ui-grid-canvas']//a[@title='{title}' or @name='{title}' or text()='{title}']").click()

    @WebAction()
    def __set_pagination(self):
        """Sets number of files in browse to the maximum possible"""
        try:
            elem = self.__driver.find_element(By.XPATH,
                                              "//div[contains(@class, 'ui-grid-pager-row-count-picker')]/select"
                                              )
        except NoSuchElementException:
            return
        if not (elem.is_enabled() and elem.is_displayed()):
            return
        select = Select(elem)
        select.select_by_index(len(select.options) - 1)
        self.__admin_console.wait_for_completion()

    @PageService()
    def __select_files(self, file_folders, second_column=False):
        """ Finds similar files in the panel and those which are input

        Args:
            file_folders (list):    the list of files and folders to select for restore

            second_column   (Boolean): True to select files/items from second column of browse page
                                       False to select files/items from first column of browse page

                            Default: False
        """
        self.__set_pagination()
        if not second_column:
            files = self.__browse_elements()
        else:
            files = self.__browse_elements(second_column=True)
        index = 0
        for each_file in files:
            index += 1
            if each_file not in file_folders:
                continue
            self.__click_elem_checkbox(index)
            self.__selected_files.append(each_file)

    @WebAction()
    def __select_node_from_tree(self, root_node):
        """Clicks on the root or top most node in the browse tree

        Args:
            root_node (str):  The name of the root/top most node to click in the browse screen

        """
        self.__driver.find_element(By.XPATH,
                                   f"//div[@class='browse-tree']//span[contains(text(), '{root_node}')]").click()

    @WebAction()
    def __unselect_all(self):
        """ selects All files and folders to restore"""
        elem = self.__driver.find_element(By.XPATH,
                                          "//div[@class='ui-grid-cell-contents']/div[@ng-model='grid.selection.selectAll']")
        if 'selected' in elem.get_attribute('class'):
            elem.click()
        else:
            elem.click()
            elem.click()

    @WebAction()
    def __expand_source_folder(self, folder):
        """
        expands the folder
        Args:
            folder (str): expands folder
        """
        self.__set_pagination()
        if self._is_o365_browse:
            _xpath = f"//span[contains(text(),'{folder}')]/parent::div"
            self.__driver.find_element(By.XPATH, _xpath).click()
        else:
            self.__driver.find_element(By.XPATH,
                self.__xp + f"//a[text()='{folder}']").click()

    @PageService()
    def clear_all_selection(self):
        """Clear selection"""
        self.__unselect_all()

    @PageService()
    def get_column_data(self, column_name):
        """returns column data"""
        columns = self.__read_column_names()
        if column_name not in columns:
            raise CVWebAutomationException(f"Column [{column_name}] doesn't exist in browse page")
        col_idx = columns.index(column_name) + 1
        return self.__read_column_data(col_idx)

    @PageService()
    def access_folder(self, folder):
        """ Navigates to the file path

        Args:
            folder (str) : file path (eg- folder1)

        """
        folders = self.__available_folders()
        folders_list = [entity for entity in folders if folder.lower() == entity.lower()]
        if folders_list:
            self.__click_access_path(folders_list[0])
            self.__admin_console.wait_for_completion()
        else:
            raise CVWebAutomationException(
                f"Invalid Path, {folder} doesnt exist, available are [{folders}]"
            )

    @WebAction()
    def __is_deleted_file(self, entity):
        """ select the deleted file in the panel
        Args:
            entity (string):  file name or folder name to check whether it is
                              marked as deleted or not.
                              (eg- 'filename.txt' or 'C' )
        """
        flag = False
        result = self.__driver.find_elements(By.XPATH,
                                             f"//span[@data-ng-show='true']/parent::div/following-sibling::div/a[@name='{entity}']")
        if result:
            flag = True
        return flag

    @WebAction()
    def __select_delected_file(self, entity):
        """ select the deleted file in the panel
               Args:
                   entity (string):    file or folder to be selected.(eg- 'filename.txt' or 'C' )
        """
        elem = f"//div[contains(@class,'deleted-item')]//a[@name='{entity}']//ancestor::div[@role='gridcell']"
        result = self.__driver.find_element(By.XPATH, elem)
        get_id = ''
        if result.is_displayed():
            get_id = result.get_attribute("id").split('-')
            get_id = get_id[0] + '-' + get_id[1]

        if get_id:
            elem = f"//*[contains(@id,'{get_id}')]//div[@role='checkbox']"
            self.__driver.find_element(By.XPATH, elem).click()

    @WebAction()
    def __click_dropdown(self, column_idx):
        """ Selects dropdown in restore page
        Args:
            column_idx (int): dropdown to be selected for the restore
                              Example:
                              For File system browse page:
                              column_idx:0 -- restore from default copy
                              column_idx:1 -- Showing backup as of <PIT>

                              For database browse page:
                              column_idx:0 -- Showing backup as of <PIT>
                              column_idx:1 -- restore from default copy

        """
        elements = self.__driver.find_elements(By.XPATH,
                                               "//a[@class='uib-dropdown-toggle ng-binding dropdown-toggle']")
        elements[column_idx].click()

    @WebAction()
    def __select_dropdown_value(self, storage_copy_name, plan_name=None):
        """ Selects items from dropdown in restore page
        Args:
            storage_copy_name(str): The name of the storage copy to be selected
                                    (eg: 'Primary' or 'Secondary')
            plan_name   (str): The name of the plan (eg: 'Server plan')
        """
        if plan_name:
            self.__driver.find_element(By.XPATH,
                                       f"//li/a[contains(@class, 'ng-binding') and "
                                       f"contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
                                       f"'restore from {storage_copy_name.lower()} ({plan_name.lower()})')]").click()

        else:
            self.__driver.find_element(By.XPATH,
                                       f"//li/a[contains(@class, 'ng-binding') and "
                                       f"translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')="
                                       f"'restore from {storage_copy_name.lower()}']").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_action_dropdown(self):
        """ Selects action dropdown in restore page """
        elem = f"//a[contains(@class,'uib-dropdown-toggle')]/span[contains(@class,'right ng-binding')]"
        self.__driver.find_element(By.XPATH, elem).click()

    @WebAction()
    def __click_action_dropdown_against_entity(self, entity_name):
        """
            Selects action dropdown against an entity in restore page
               Args:
                   entity_name(str): The entity whose action dropdown needs to be accessed
        """
        if self._is_o365_browse:
            elem = (f"//span[text()='{entity_name}']/ancestor::a/ancestor::td/following-sibling::td/"
                    f"span[contains(@class,'action-btn')]")
        else:
            elem = f"//div[contains(@class,'ui-grid-cell')]//a[text()='{entity_name}']" \
                   f"//ancestor::div[contains(@class,'ui-grid-row')]//a[contains(@class,'dropdown-toggle')]"

        self.__driver.find_element(By.XPATH, elem).click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_sub_link(self, text):
        """ Selects items from action dropdown in restore page
        Args:
            text(str): The select the specific entity from dropdown
        """
        self.__driver.find_element(By.XPATH,
                                   f"//span[@data-ng-bind-html='subLinks.label' and text()='{text}']").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_entity_sub_link(self, text):
        """
            Selects items from action dropdown of a specific entity in restore page
              Args:
                text(str): To select the option from dropdown associated to a specific entity
        """
        if self._is_o365_browse:
            elem = f"//ul[@id='office365SharepointWebSearchTable_actionContextMenu']//a[text()='{text}']"
        else:
            elem = f"//ul[contains(@class, 'dropdown-menu') and contains(@style,'block')]//a[text()='{text}']"

        self.__driver.find_element(By.XPATH, elem).click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __get_deleted_files(self):
        """ Gets the deleted files on that page """
        files = self.__driver.find_elements(By.XPATH,
                                            f"//div[contains(@class, 'deleted-item')]//a"
                                            )
        file_names = [file.text for file in files]
        return file_names

    @WebAction()
    def __click_file_preview(self, file_name):
        """ Selects the file to preview
        Args:
            file_name (str): Name of the file to be selected
                             (eg: 'file.txt')
        """
        self.__driver.find_element(By.XPATH, f"//a[@name='{file_name}']").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_close_preview(self):
        """ Clicks close option of previews file"""
        self.__driver.find_element(By.XPATH, "//a[@class='modal__close-btn']").click()

    def __select_modified_file(self, modified_file):
        """ Selects multiple versions of a file
        Args:
            modified_file (str):  modified file versions to be selected
                                        (eg- 'C:\\Files\\Text.html'  or
                                             '/opt/files/text.txt')
        """

        if "/" in modified_file:
            delimiter = "/"
        else:
            delimiter = "\\"
        paths = modified_file.split(delimiter)

        if modified_file.startswith("\\\\"):
            paths = paths[2:]
            paths[0] = "\\\\" + paths[0]

        for folder in range(0, len(paths) - 1):
            self.access_folder(paths[folder])
        self.__select_files([os.path.basename(modified_file)])

    @WebAction()
    def __click_collections_view(self):
        """ selects collections view """
        self.__driver.find_element(By.XPATH,
                                   "//a[contains(text(),'Restore collections')]").click()

    @WebAction()
    def __get_restore_copies(self):
        """ Returns the copies available to restore from for a client """
        self.__select_dropdown(restore_options=True)
        # path = "(//span[contains(@class,'uib-dropdown')])[1]//a[@class='crop ng-binding']"
        path = '//*[@id="action-list"]//li'
        list_of_copies = [
            copy for copy in self.__driver.find_elements(By.XPATH, path) if copy.is_displayed()
        ]
        return list_of_copies

    @WebAction()
    def __get_folders_from_tree_view(self):
        """Returns the folders from the tree view"""
        folder_names = list()
        folders = self.__driver.find_elements(By.XPATH,
                                              "//ul[@class='k-group']/li[contains(@class,'k-item') and contains(@role,'treeitem')]")
        for folder in folders:
            folder_names.append(folder.text)
        return folder_names

    @PageService()
    def select_tableview(self):
        """Select Table_view from Oracle Tablespaceview Dropdown"""
        self.__select_keyspaceview_dropdown()
        self.__click_table_view()
        self.__admin_console.wait_for_completion(1000)

    @PageService()
    def access_table_action_item(self, entity_name, action_item):
        """
        Selects the action items from the actions menu in table-level browse.

        Args:
            entity_name (str): Entity against which action item has to be selected

            action_item (str): Action item which has to be selected
                    Accepted Values:
                    "Select/Deselect all dependent tables "
                    "Select/Deselect all referenced tables "
                    "Select all dependent/referenced tables recursively"

        """
        self.__click_action_dropdown_against_entity(entity_name)
        self.__admin_console.wait_for_completion()
        self.__click_entity_sub_link(action_item)
        self.__admin_console.wait_for_completion()

    @PageService()
    def confirm_delete_data_popup(self, delete_all=False):
        """Fill the text field and press the confirm button to delete backed up data in SharePoint
        Args:
            delete_all (bool): set to "true" to delete all data present in view in the browse table
                               set to "false" to only delete the selected data in the browse table
        """
        if delete_all:
            self.__admin_console.select_radio(value='All')
        self.__admin_console.fill_form_by_id(element_id='reconfirmActionId', value='DELETE')
        self.__admin_console.click_button(value='Delete')

    @PageService()
    def select_multiple_version_of_files(self, modified_file_path, version_nums):
        """ Selects multiple versions of a file
        Args:
            modified_file_path (str):  modified file versions to be selected
                                       (eg- 'C:\\Files\\Text.html'  or
                                            '/opt/files/text.txt')

            version_nums (list): To select the specified version
                                 (eg: ['1', '2'])
        """
        self.__select_modified_file(modified_file_path)
        self.__click_action_dropdown()
        self.__click_sub_link(self.__admin_console.props['label.viewVersions'])
        files = []
        for version_no in version_nums:
            file = os.path.basename(modified_file_path) + " (" + version_no + ")"
            files.append(file)
        self.select_for_restore(file_folders=files)

    @PageService()
    def select_hidden_items(self, hidden_items, delimiter):
        """Selects hidden items for restore
        Args:
            hidden_items (list(file_paths)):  hidden files to be selected
                                              (eg- 'C:\\Files\\Text.html'  or
                                                    '/opt/files/text.txt')
            delimiter   (str):  To know windows or unix path
        """
        self.__click_action_dropdown()
        self.__click_sub_link(self.__admin_console.props['label.showHiddenItems'])
        paths = os.path.dirname(hidden_items[0])
        if delimiter == '/':
            paths = paths.strip('/')
        paths = paths.split(delimiter)
        hidden_files = [os.path.basename(file) for file in hidden_items]
        for folder in paths:
            self.access_folder(folder)
        self.select_for_restore(file_folders=hidden_files)

    @PageService()
    def select_deleted_items_for_restore(self, content_path, delimiter):
        """ Selects deleted files and folders to restore
        Args:
            content_path (str):  deleted files path location
                                 (eg- 'C:\\Files\\Text.html'  or '/opt/files/text.txt')
            delimiter   (str):  To know windows or unix path
        """

        self.__click_action_dropdown()
        self.__click_sub_link('Show deleted items')
        paths = content_path.split(delimiter)

        if content_path.startswith("\\\\"):
            paths = paths[2:]
            paths[0] = "\\\\" + paths[0]

        flag = True
        for folder in paths:
            if self.__is_deleted_file(folder):
                self.__select_delected_file(folder)
                flag = False
                break
            self.access_folder(folder)

        if flag:
            files = self.__get_deleted_files()
            for file in files:
                self.__select_delected_file(file)

    @PageService()
    def select_for_preview(self, file_path):
        """ Selects to view the file
        Args:
            file_path (str):    the file path to select for preview
        """
        file_path = file_path.replace("\\", "/").strip("/")
        paths = os.path.dirname(file_path).split("/")
        for folder in paths:
            self.access_folder(folder)
            self.__admin_console.wait_for_completion()
        self.__click_file_preview(os.path.basename(file_path))

    @PageService()
    def close_preview_file(self):
        """ Closes the preview file"""
        self.__click_close_preview()

    @PageService()
    def select_for_restore(self, file_folders=None, all_files=False):
        """ Selects files and folders to restore

        Args:
            file_folders (list):    the list of files and folders to select for restore

            all_files   (bool):     select all the files shown for restore / download

        """
        self.__selected_files = []
        if all_files:
            self.__select_all()
            self.__admin_console.wait_for_completion()
            return

        while True:
            self.__select_files(file_folders)
            file_folders = list(set(file_folders) - set(self.__selected_files))
            if file_folders:
                #  access next page as all files are not visible in current page
                if self.__driver.find_element(By.XPATH,
                                              "//button[@ng-disabled='cantPageForward()']").is_enabled():
                    self.__admin_console.cv_table_click_next_button()
                else:
                    break
            else:
                break
        if file_folders:
            raise CVWebAutomationException(f"Could not find the items {file_folders}")

    @PageService()
    def select_path_for_restore(self, path, file_folders=None, select_items=True):
        """ Expand the source path and selects files and folders to be restore
        Args:
            path (str):source path to be expanded

            file_folders (list):    the list of files and folders to select for restore

            select_items (bool):    When set to false , it will only access the folder and not select any items
        Examples:
            c:\data\f1  --> select f1
            c:  --> select c:
            data/f1  --> select f1
        """
        temp_path = path.replace('\\', '/')
        paths = temp_path.split('/')
        while '' in paths:
            paths.remove('')
        for path in paths:
            self.__expand_source_folder(path)
            self.__admin_console.wait_for_completion()
        if not select_items:
            pass
        elif file_folders:
            self.__select_files(file_folders)
        else:
            self.__select_all()
        self.__admin_console.wait_for_completion()
        return

    @PageService()
    def select_from_multiple_pages(self, mapping_dict, subclient_name, rds_agent=False):
        """Selects files/items from multiple pages in browse window
        Args:
            mapping_dict (dict) : The dictionary containing the folder names as keys
                                and list of files to be selected under them as value
                                Example --
                                mapping_dict={
                                'FOLDER1':['file1','file2','file3']
                                'FOLDER2':['fileA','fileB','fileC']
                                }
            subclient_name  (str):  The name of the subclient on which browse operation
                                    was performed or the name of the root folder that
                                    appears on the browse page

            rds_agent  (Boolean):  Flag to indicate if browse is performed for RDS agent

                                   True if browsing from amazon RDS instance or subclient
                                   False for any other agent

        """
        if not isinstance(mapping_dict, dict):
            raise CVWebAutomationException("Mapping dict is empty or invalid")
        else:
            for key, value in mapping_dict.items():
                self.access_folder(key)
                if not rds_agent:
                    self.__select_files(value)
                else:
                    self.__select_files(value, second_column=True)
                self.__select_node_from_tree(subclient_name)

    @PageService()
    def select_from_actions_menu(self, mapping_dict, subclient_name):
        """
            Selects files/items from multiple pages in browse window
              Args:
                mapping_dict (dict) : The dictionary containing the folder names as keys
                                      and 2D list of tables and the operation on the actions
                                      menu to be performed as value.
                                      Example --
                                      mapping_dict={
                                      'FOLDER1':[['file1',Option],['file2',Option]]
                                      'FOLDER2':[['fileA',Option]]
                                      }
                subclient_name (str):  The name of the subclient on which browse operation
                                       was performed or the name of the root folder that
                                       appears on the browse page
              Raises:
                  CVWebAutomationException:
                    -- If mapping_dict is empty or invalid
        """

        if not isinstance(mapping_dict, dict):
            raise CVWebAutomationException("Mapping dict is empty or invalid")
        else:
            for key, value in mapping_dict.items():
                self.access_folder(key)
                for entity in value:
                    self.access_table_action_item(entity[0], entity[1])
                self.__select_node_from_tree(subclient_name)

    @PageService()
    def show_latest_backups(self):
        """Shows the latest backup"""
        self.__select_dropdown()
        self.__click_latest_backup()
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_adv_options_submit_restore(self, storage_copy_name, plan_name=None, database=False):
        """ Restores from the selected option
            Args:
                storage_copy_name(str): The name of the storage copy
                                        (eg: 'Primary' or 'Secondary')
                plan_name(str): The name of the plan (eg: 'Server plan')

                database (Boolean): Flag to indicate if browse was performed for
                                    database agents
                                default: False
        """
        if not database:
            self.__click_dropdown(0)
        else:
            self.__click_dropdown(1)
        self.__select_dropdown_value(storage_copy_name, plan_name)
        self.__admin_console.wait_for_completion()

    @PageService()
    def show_backups_by_date_range(self, to_time, from_time=None):
        """Shows backup data by date range
            Args:
                from_time   :   Time from when to backup
                    format: %d-%B-%Y-%I-%M-%p
                            (dd-Month-yyyy-hour(12 hour)-minutes-session(AM/PM))
                            (01-January-2000-11-59-PM)

                to_time   :   Time till when to backup
                    format: %d-%B-%Y-%I-%M-%p
                            (dd-Month-yyyy-hour(12 hour)-minutes-session(AM/PM))
                            (01-January-2000-11-59-PM)
        """
        self.__select_dropdown(show_backup=True)
        if from_time:
            self.__click_daterange_backup()
        else:
            self.__click_backups_by_specific_date()
        self.__admin_console.wait_for_completion()
        if from_time:
            calender = {}
            calender['date'], calender['month'], calender['year'], \
            calender['hours'], calender['mins'], \
            calender['session'] = from_time.split("-")
            self.__admin_console.date_picker(calender, time_id="from-picker")
        calender = {}
        calender['date'], calender['month'], calender['year'], \
        calender['hours'], calender['mins'], \
        calender['session'] = to_time.split("-")
        self.__admin_console.date_picker(calender, time_id="to-picker")
        self.__admin_console.driver.find_element(By.XPATH,
                                                 "//button[@data-ng-click='ok()']").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_restore_copies_for_plan(self, plan_name):
        """ Returns the copies available for restore from a region-based storage plan
             Args:
                 plan_name (str)  :   Name of the region-based plan for which the copies are to be fetched
        """
        list_of_copies = self.__get_restore_copies()
        list_of_plan_copies = [copy.text for copy in list_of_copies if plan_name.lower() in copy.text]
        return list_of_plan_copies

    @PageService()
    def restore_from_primary_copy(self):
        """ Selects restore from primary copy from drop down"""
        self.__select_dropdown(restore_options=True)
        self.__click_primary_copy_restore()
        self.__admin_console.wait_for_completion()

    @PageService()
    def submit_for_restore(self):
        """ Restores the selected files """
        self.__click_restore()
        self.__admin_console.wait_for_completion()

    @PageService()
    def submit_for_download(self):
        """ Downloads the selected files """
        self.__click_download()
        notification = self.__admin_console.get_notification()
        self.__admin_console.wait_for_completion()
        return notification

    @PageService()
    def get_restore_nodelist(self):
        """ returns restore node list"""
        hostport_list = self.get_column_data("Backup host:port")
        shard_list = self.get_column_data("Replica set")
        restorenodelist = {}
        for host_port, shard in zip(hostport_list, shard_list):
            restorenodelist[shard] = host_port.replace("::", "_")
        return restorenodelist

    @PageService()
    def switch_to_collections_view(self):
        """Switches to collection view"""
        self.__select_dropdown(cluster_view=True)
        self.__click_collections_view()
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_keyspace_view(self, keyspace_view=True):
        """Select Keyspace View for Cassandra"""
        self.__select_keyspaceview_dropdown()
        self.__admin_console.wait_for_completion()
        if keyspace_view:
            self.__click_keyspace_view()
        else:
            self.__click_cluster_view(self)
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_folders_from_tree_view(self, folder):
        """Fetch the folders names from the tree view
            Args:-
                folder(str) -- Name of the root folder
        """
        self.__expand_source_folder(folder)
        self.__admin_console.wait_for_completion()
        folder_names = self.__get_folders_from_tree_view()
        return folder_names

    @PageService()
    def select_browse_action_item(self, entity_name: str, action_item: str, partial_selection=False,
                                  second_entity=None):
        """Select an action item for an item from the browse page"""
        self._table.access_action_item(entity_name=entity_name, action_item=action_item,
                                       partial_selection=partial_selection, second_entity=second_entity)

    @PageService()
    def search_for_content(self, search_term: str):
        """Search for content on browse page"""
        _search_xpath = "//input[@type='text' and contains(@class,'searchTerm')]"
        self.__driver.find_element(By.XPATH, _search_xpath).clear()
        self.__driver.find_element(By.XPATH, _search_xpath).send_keys(search_term+'\ue007') #press enter key
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_path_from_browse_tree(self, paths: list):
        """
            Expand the path in the browse tree
        Args:
            paths (list):    source path to be expanded

        Examples:
            ['user1@example.com' , 'Inbox', ' CustomFolder1']
        """

        for path in paths:
            self._expand_browse_tree(path)
            self.__admin_console.wait_for_completion()
        self.__admin_console.wait_for_completion()
        return

    @WebAction()
    def _expand_browse_tree(self, item: str):
        """Expand the browse tree for item"""
        _xpath = f"//span[contains(@class,'childNode') and text()='{item}']/" \
                 f"ancestor::li[@role='treeitem' and @class='k-item']"
        _elem = self.__driver.find_element(By.XPATH, _xpath)
        if _elem.get_attribute("aria-selected") == "false":
            _elem.click()


class RBrowse:
    """Class for restoring selected files and folders
    """

    def __init__(self, admin_console, browse_table_id=None):
        """Initialize RBrowse class

            Args:

                admin_console       (AdminConsole)      :   Instance of AdminConsole
                browse_table_id     (str)               :   id of Browse Table
        """
        self.__driver = admin_console.driver
        self.__admin_console = admin_console
        self.__tree = TreeView(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__calendar = CalendarView(self.__admin_console)
        self.__table = Rtable(self.__admin_console, id=browse_table_id)
        self.__checkbox = Checkbox(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.log = logger.get_log()

        if browse_table_id:
            self.__xp = f"//div[@id='{browse_table_id}']"
        else:
            self.__xp = ""

        self.__table_xpath = self.__xp + "//table[contains(@class, 'k-grid-table')]"
        self.__action_panel_xpath = self.__xp + "//div[contains(@class, 'top-panel-container')]"

    @WebAction()
    def __click_toolbar_button(self, button_text: str, wait=True) -> None:
        """Clicks on button on the toolbar

            Args:

                button_text     (str)       :   Text on the button to click
                wait           (bool)      :   Flag to indicate if wait is required after clicking the button

        """
        button_xpath = self.__action_panel_xpath + f"//button//*[contains(text(), '{button_text}')]"
        self.__admin_console.scroll_into_view(button_xpath)
        self.__driver.find_element(By.XPATH, button_xpath).click()
        if wait:
            self.__admin_console.wait_for_completion()

    @WebAction()
    def __select_dropdown_value(self, dropdown_index: int, value: str) -> None:
        """Selects items from dropdown in restore page

            Args:

                dropdown_index      (int)       :   The index of the dropdown on action panel

                value               (str)       :   Value to select from dropdown
        """
        dropdown_xpath = self.__action_panel_xpath + "//div[contains(@class, 'action-list-dropdown-wrapper')]//button"
        dropdown_list = self.__driver.find_elements(By.XPATH, dropdown_xpath)
        dropdown_list[dropdown_index].click()
        self.__admin_console.wait_for_completion()

        menu_item_xpath = f"//li[contains(@class, 'MuiMenuItem-root')]//*[contains(text(), '{value}')]"
        menu_item = self.__driver.find_element(By.XPATH, menu_item_xpath)
        menu_item.click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __get_deleted_files(self) -> list:
        """Gets the deleted files on that page
        """
        return [file for file in self.get_column_data() if 'Deleted' in file]

    @WebAction()
    def __click_file_preview(self, file_name: str) -> None:
        """ Selects the file to preview

            Args:

                file_name       (str)       :   Name of the file to be selected
                                                (eg: 'file.txt')
        """

        file_xpath = self.__table_xpath + f"//td//*[contains(text(), '{file_name}')]"
        self.__driver.find_element(By.XPATH, file_xpath).click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_close_preview(self) -> None:
        """Clicks close button of previewed file
        """

        button_xpath = "//div[contains(@class, 'close-btn')]/button"
        button_element = self.__driver.find_element(By.XPATH, button_xpath)
        button_element.click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_calendar_button(self, label: str) -> None:
        """Click on the calendar button in backup time range dialog based on label

            Args:

                label       (str)       :   Label corresponding to calendar button
        """
        self.__dialog.click_button_on_dialog(label, preceding_label=True)

    @WebAction()
    def __click_root_folder(self) -> None:
        """Click on the link over the root folder in navigation breadcrumb
        """
        root_folder_xpath = "//div[@id='browseContentGrid']//div[contains(@class, 'grid-lead-header')]//li[1]"
        breadcrumb_element = self.__driver.find_element(By.XPATH, root_folder_xpath)
        if 'c-link' in breadcrumb_element.get_attribute("class"):
            breadcrumb_element.click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __get_restore_copies(self):
        """ Returns the copies available to restore from for a client """
        dropdown_xpath = self.__action_panel_xpath + "//div[contains(@class, 'action-list-dropdown-wrapper')]//button"
        dropdown_list = self.__driver.find_elements(By.XPATH, dropdown_xpath)
        dropdown_list[2].click()
        self.__admin_console.wait_for_completion()
        path = '//*[@id="action-list"]//li'
        list_of_copies = [
            copy for copy in self.__driver.find_elements(By.XPATH, path) if copy.is_displayed()
        ]
        return list_of_copies

    @WebAction()
    def __clear_search_box(self):
        """clears text from search box"""
        search_box = self.__driver.find_element(By.XPATH, "//input[contains(@id,'searchInput')]")
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.BACKSPACE)

    @WebAction(delay=0)
    def __set_search_string(self, keyword):
        """Clears the search box and sets with the given string on React Table
            Args:
                keyword         (str)       :   Keyword to be searched on table
        """
        self.__clear_search_box()

        search_box = self.__driver.find_element(By.XPATH, "//input[contains(@id,'searchInput')]")
        search_box.send_keys(keyword)
        RPanelInfo(self.__admin_console).click_button('Search')
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __set_search_settings(self, search_settings):
        """Sets the search settings on the browse page
            Args:
                search_settings (dict) :   The search settings to be applied on the browse page
                E.g.:
                {
                    "contains": "",
                    "size": "",
                    "file_type": "",
                    "deleted": "",
                    "modified": "",
                    "include_folders": {'enable': True},
                    "show_deleted_items": {'enable': True}
                }
        """
        if search_settings:
            self.__driver.find_element(By.XPATH, "//input[contains(@id,'searchInput')]").click()
            if search_settings.get('contains', None):
                return NotImplementedError
            if search_settings.get('size', None):
                return NotImplementedError
            if search_settings.get('file_type', None):
                return NotImplementedError
            if search_settings.get('deleted', None):
                return NotImplementedError
            if search_settings.get('modified', None):
                return NotImplementedError
            if search_settings.get('include_folders', None):
                if search_settings['include_folders']['enable']:
                    self.__checkbox.check(id="IncludeFolders")
                else:
                    self.__checkbox.uncheck(id="IncludeFolders")
            if search_settings.get('show_deleted_items', None):
                if search_settings['show_deleted_items']['enable']:
                    self.__checkbox.check(id="ShowDeletedFiles")
                else:
                    self.__checkbox.uncheck(id="ShowDeletedFiles")

            self.__admin_console.wait_for_completion()

    @PageService()
    def select_files(self, file_folders: list = None, select_all: bool = False, partial_selection=False) -> None:
        """Finds similar files in the panel and select them

            Args:

                file_folders        (list)      :   The list of files and folders to select for restore.
                                                For eg, ['file1', 'folder1']
                select_all          (bool)      :   To select all files
                partial_selection   (bool)      :   To select the using partial file name

        """
        if self.__table.has_next_page():
            self.__table.set_pagination('max')

        if select_all:
            self.__table.select_all_rows()
        elif file_folders:
            self.__table.select_rows(file_folders, partial_selection)
        else:
            raise CVWebAutomationException("No files or folders given to select")

    @PageService()
    def clear_all_selection(self) -> None:
        """Clear selection from browse table
        """
        self.__table.unselect_all_rows()

    @PageService()
    def get_column_data(self, column_name: str = None) -> list:
        """Returns data of column

            Args:

                column_name         (str)       :   Name of the column to get data
                                                    Default: Returns data of first column

        """
        column_name = column_name or self.__admin_console.props['label.name']
        return self.__table.get_column_data(column_name=column_name, fetch_all=True)

    @PageService()
    def get_restore_copies_for_plan(self, plan_name):
        """ Returns the copies available for restore from a region-based storage plan
             Args:
                 plan_name (str)  :   Name of the region-based plan for which the copies are to be fetched
        """
        list_of_copies = self.__get_restore_copies()
        list_of_plan_copies = [copy.text for copy in list_of_copies if plan_name.lower() in copy.text]
        return list_of_plan_copies

    @PageService()
    def access_folder(self, folder: str) -> None:
        """Access the link to open folder

            Args:

                folder      (str)       :   Folder to access (eg- folder1)
        """
        column_name = self.__admin_console.props['label.name']
        if self.__table.is_entity_present_in_column(column_name=column_name, entity_name=folder):
            self.__table.access_link_by_column(entity_name=column_name, link_text=folder)
        else:
            raise CVWebAutomationException(
                f"Invalid Path, {folder} doesnt exist"
            )

    @PageService()
    def select_from_actions_menu(self, mapping_dict):
        """
            Selects files/items from multiple pages in browse window
              Args:
                mapping_dict (dict) : The dictionary containing the folder names as keys
                                      and 2D list of tables and the operation on the actions
                                      menu to be performed as value.
                                      Example --
                                      mapping_dict={
                                      'FOLDER1':[['file1',Option],['file2',Option]]
                                      'FOLDER2':[['fileA',Option]]
                                      }
              Raises:
                  CVWebAutomationException:
                    -- If mapping_dict is empty or invalid
        """

        if not isinstance(mapping_dict, dict):
            raise CVWebAutomationException("Mapping dict is empty or invalid")
        else:
            for key, value in mapping_dict.items():
                self.access_folder(key)
                for entity in value:
                    self.__table.access_action_item(entity[0], entity[1])
                self.reset_folder_navigation()

    @PageService()
    def select_action_dropdown_value(self, value: str, index: int = 0) -> None:
        """Select value from dropdown in action panel

            Args:

                value       (str)       :   Dropdown item to select

                index       (int)       :   Dropdown index if there are multiple dropdowns

        """
        self.__select_dropdown_value(dropdown_index=index, value=value)

    @PageService()
    def select_multiple_version_of_files(self, modified_file_path: str,
                                         version_nums: list = None, use_tree: bool = True) -> None:
        """Selects multiple versions of a file

            Args:

                modified_file_path      (str)       :   Modified file versions to be selected
                                                       (eg- 'C:\\Files\\Text.html'  or
                                                            '/opt/files/text.txt')

                version_nums            (list)      :   To select the specified version
                                                        Select all if not specified.
                                                        (eg: ['1', '2'])

                use_tree                (bool)      :   To use folder tree to navigate instead of row links
        """

        folder_path = os.path.dirname(modified_file_path)
        file_name = os.path.basename(modified_file_path)
        self.select_path_for_restore(path=folder_path, file_folders=[file_name], use_tree=use_tree)

        self.select_action_dropdown_value(index=0, value=self.__admin_console.props['label.viewVersions'])
        files = []
        if version_nums:
            for version_no in version_nums:
                file = file_name + " (" + str(version_no) + ")"
                files.append(file)
        self.select_files(file_folders=files, select_all=(not files))

    @PageService()
    def select_hidden_items(self, content_path: str = None, hidden_items: list = None, use_tree: bool = True) -> None:
        """Selects hidden items for restore

            Args:

                content_path            (str)       :   Path to navigate which contains the content

                hidden_items            (list)      :   Hidden files to be selected from table
                                                        (eg- 'C:\\Files\\Text.html'  or
                                                            '/opt/files/text.txt')

                use_tree                (bool)      :   To use folder tree to navigate instead of row links
        """
        self.select_action_dropdown_value(index=0, value=self.__admin_console.props['label.showHiddenItems'])
        if content_path:
            self.navigate_path(content_path, use_tree=use_tree)
        self.select_files(file_folders=hidden_items, select_all=(not hidden_items))

    @PageService()
    def select_deleted_items_for_restore(self, content_path: str,
                                         files_folders: list = None, use_tree: bool = True) -> None:
        """Selects deleted files and folders to restore

            Args:

                content_path            (str)       :   Path to navigate which contains the content

                files_folders           (list)      :   Deleted files to be selected from table
                                                        (eg- 'C:\\Files\\Text.html'  or
                                                            '/opt/files/text.txt')

                use_tree                (bool)      :   To use folder tree to navigate instead of row links
        """
        self.select_action_dropdown_value(self.__admin_console.props['label.showDeletedItems'])
        self.navigate_path(content_path, use_tree=use_tree)

        deleted_files = [deleted_file.removesuffix('\nDeleted') for deleted_file in self.__get_deleted_files()]

        if files_folders:
            for deleted_file in files_folders:
                if deleted_file in deleted_files:
                    self.select_files([deleted_file])
        else:
            self.select_files(deleted_files)

    @PageService()
    def navigate_path(self, path: str, use_tree: bool = True) -> None:
        """Navigate to the folder path

            Args:

                path        (str)       :   Folder path to navigate to

                use_tree    (bool)      :   Use tree component to navigate instead of links on rows

        """
        node_list = path.replace("\\", "/").split('/')
        while '' in node_list:
            node_list.remove('')
        self.reset_folder_navigation()

        # CIFS path startswith \\\\
        if path.startswith("\\\\"):
            node_list[0] = "\\\\" + node_list[0]

        # NFS path is in the format server:/share-path, we dont show ':' in the browse
        elif ":/" in path and (not path.startswith("/")):
            node_list[0] = node_list[0].replace(":", "")

        for node in node_list:
            if use_tree:
                self.__tree.collapse_node(node)
                self.__tree.expand_node(node)
            else:
                self.access_folder(node)

    @PageService()
    def select_for_preview(self, file_path: str, use_tree: bool = True) -> None:
        """Selects to view the file

            Args:

                file_path       (str)       :   The file path to select for preview

                use_tree        (bool)      :   To pass to navigate_path
        """
        dir_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)

        if dir_path:
            # Navigate to the folder subdirectory
            self.navigate_path(dir_path, use_tree=use_tree)
        self.__click_file_preview(file_name)

    @PageService()
    def close_preview_file(self) -> None:
        """ Closes the preview file"""
        self.__click_close_preview()

    @PageService()
    def select_path_for_restore(self, path: str = None, file_folders: list = None, use_tree: bool = True):
        """Expand the source path and selects files and folders to be restored

            Args:

                path                (str)       :   Source path to be expanded

                file_folders        (list)      :   The list of files and folders to select for restore

                use_tree            (bool)      :   Use tree component to navigate instead of links on rows

        """
        if path:
            self.navigate_path(path, use_tree=use_tree)
        self.select_files(file_folders, select_all=(not file_folders))
        self.__admin_console.wait_for_completion()

    @PageService()
    def show_latest_backups(self, database=False):
        """Shows the latest backup
        """

        # Dropdown for backup time-range is the second dropdown, hence index is 1
        index = 1
        if database:
            index = 0

        self.select_action_dropdown_value(
            index=index, value=self.__admin_console.props['Show_latest_backups']
        )

    @PageService()
    def show_backups_by_date_range(self, to_time, from_time=None, prop=None, index=1):
        """Shows backup data by date range

            Args:

                from_time       (str)       :   Time from when to backup

                to_time         (str)       :   Time till when to backup

                                                format: %d-%B-%Y-%H-%M
                                                        (dd-Month-yyyy-hour(24 hour)-minutes)
                                                        (Eg, 01-January-2000-23-59)

                                                        or
                                                        %d-%B-%Y-%H-%M-%p
                                                        (dd-Month-yyyy-hour(12 hour)-minutes-session(AM/PM))
                                                        (Eg, 01-January-2000-23-59-AM)

                prop            (str)       :   Property to select from dropdown

                index           (int)       :   Index of the dropdown to select the property
        """

        if not prop:
            if from_time:
                prop = self.__admin_console.props['Show_backups_date_range']
            else:
                prop = self.__admin_console.props['Show_backups_specific_date']
        self.select_action_dropdown_value(value=prop, index=index)
        self.__admin_console.wait_for_completion()

        # Converting the 'to date' from string format to dict format
        date_format = "day-month-year-hour-minute"
        to_date_time_dict = {}

        to_time_list = to_time.split('-')
        for idx, key in enumerate(date_format.split('-')):
            if key == 'month':
                to_date_time_dict[key] = to_time_list[idx]
            else:
                to_date_time_dict[key] = int(to_time_list[idx])

        # implies 12 hour format hence need to add the session
        if len(to_time_list) > 5:
            to_date_time_dict['session'] = to_time_list[-1]

        self.__click_calendar_button(label="To time")
        self.__calendar.set_date_and_time(to_date_time_dict)

        if from_time:
            # Converting the 'to date' from string format to dict format
            from_date_time_dict = {}

            from_time_list = from_time.split('-')
            for idx, key in enumerate(date_format.split('-')):
                if key == 'month':
                    from_date_time_dict[key] = from_time_list[idx]
                else:
                    from_date_time_dict[key] = int(from_time_list[idx])

            if len(from_time_list) > 5:
                from_date_time_dict['session'] = from_time_list[-1]

            self.__click_calendar_button(label="From time")
            self.__calendar.select_date(from_date_time_dict)
            self.__calendar.select_time(from_date_time_dict)
            self.__calendar.set_date()

        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def submit_for_restore(self) -> None:
        """Restores the selected files
        """
        self.__click_toolbar_button(button_text=self.__admin_console.props['action.restore'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def view_selections(self) -> None:
        """Displays the selected files
        """
        self.__click_toolbar_button(button_text=self.__admin_console.props['label.viewSelections'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def submit_for_download(self) -> str:
        """Downloads the selected files and returns the notification"""
        self.__click_toolbar_button(button_text='Download', wait=False)
        notification = self.__admin_console.get_notification()
        self.__admin_console.wait_for_completion()
        return notification

    @PageService()
    def click_download(self):
        """Downloads the selected files and returns the job id"""

        button_text = self.__admin_console.props['backupBrowse.action.download']
        button_xpath = self.__action_panel_xpath + f"//button//*[contains(text(), '{button_text}')]"
        try:
            self.__driver.find_element(By.XPATH, button_xpath).click()
        except NoSuchElementException:
            raise NoSuchElementException("Download Button Not Found")
        job_id = 0
        try:
            job_id = self.__admin_console.get_jobid_from_popup()
        except:
            self.log.info("Could not get job id as file got downloaded directly without triggering job")

        self.__admin_console.wait_for_completion()
        return job_id

    @PageService()
    def select_storage_copy(self, label, database=False, mediaagent=None) -> None:
        """Select the storage copy from the dropdown

            Args:

                label       (str)       :   Value of the dropdown item to select
                database    (Boolean)   : Flag to indicate if browse is performed for database agents default: False
                mediaagent  (str)       :   Value of the mediaagent to select
        """
        self.__click_toolbar_button("Change source")
        self.__dialog.select_dropdown_values(drop_down_id='sourcesList', values=[label], case_insensitive=True)
        if mediaagent:
            self.__dialog.select_dropdown_values(drop_down_id='mediaAgentsList', values=[mediaagent])
        self.__admin_console.wait_for_completion()
        self.__dialog.click_submit()

    @PageService()
    def reset_folder_navigation(self) -> None:
        """Reset folder navigation to root
            Eg, if navigation is at /folder1/folder2/folder3, reset it to /
        """
        self.__click_root_folder()

    @PageService()
    def set_search_string(self, keyword, search_settings=None) -> None:
        """Select search string in search bar

                Args:

                    keyword             (str)       :   Keyword to search or wildcard
                    search_settings     (dict)      :   To edit the search settings
                    search_settings = {
                        "contains": "",
                        "size": "",
                        "file_type": "",
                        "deleted": "",
                        "modified": "",
                        "include_folders": {'enable': True},
                        "show_deleted_items": {'enable': True}
                    }
        """
        self.__set_search_settings(search_settings)
        self.__set_search_string(keyword)

    @PageService()
    def switch_to_collections_view(self):
        """Switches to collection view"""
        return NotImplementedError

    @PageService()
    def select_keyspace_view(self):
        """Select Keyspace View for Cassandra"""
        return NotImplementedError

    @PageService()
    def select_tableview(self) -> None:
        """Select Table_view from Oracle Tablespaceview Dropdown"""
        self.__select_dropdown_value(dropdown_index=0, value='Table view')
        self.__admin_console.wait_for_completion(1000)

    @PageService()
    def select_from_multiple_pages(self, mapping_dict):
        """Selects files/items from multiple pages in browse window
        Args:
            mapping_dict (dict) : The dictionary containing the folder names as keys
                                and list of files to be selected under them as value
                                Example --
                                mapping_dict={
                                'FOLDER1':['file1','file2','file3']
                                'FOLDER2':['fileA','fileB','fileC']
                                }

        """
        if not isinstance(mapping_dict, dict):
            raise CVWebAutomationException("Mapping dict is empty or invalid")
        else:
            for key, value in mapping_dict.items():
                self.access_folder(key)
                self.clear_all_selection()
                self.__table.select_rows(value)
                self.reset_folder_navigation()


class ContentBrowse:
    """ Class to handle content browse in subclient create/edit panels"""

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__xp = "//div[contains(@class, 'browse-tree')]"

    @WebAction()
    def __expand_folder(self, folder):
        """
        expands the folder
        Args:
            folder (str): expands folder
        """
        xpath = self.__xp + f"//span[contains(@class,'ng-binding') and %s/../..//button"
        if self.__admin_console.check_if_entity_exists(entity_name='xpath',
                                                       entity_value=xpath % f"text()='{folder}']"):
            self.__driver.find_element(By.XPATH, xpath % f"text()='{folder}']").click()
        elif self.__admin_console.check_if_entity_exists(entity_name='xpath',
                                                         entity_value=xpath % f"contains(text(), '({folder})')]"):
            self.__driver.find_element(By.XPATH, xpath % f"contains(text(), '({folder})')]").click()
        elif self.__admin_console.check_if_entity_exists(entity_name='xpath',
                                                         entity_value=xpath % f"contains(text(), '{folder}')]"):
            self.__driver.find_element(By.XPATH, xpath % f"contains(text(), '{folder}')]").click()
        else:
            raise CVWebAutomationException(f"Given file/folder path [{folder}] does not exist")

    @WebAction()
    def __select_folder(self, folder):
        """
        Select the folder or file
        Args:
            folder (str): selects folder
        """
        xpath = self.__xp + f"//span[contains(@class,'ng-binding') and %s"
        if self.__admin_console.check_if_entity_exists(entity_name='xpath',
                                                       entity_value=xpath % f"text()='{folder}']"):
            self.__driver.find_element(By.XPATH, xpath % f"text()='{folder}']").click()
        elif self.__admin_console.check_if_entity_exists(entity_name='xpath',
                                                         entity_value=xpath % f"contains(text(), '({folder})')]"):
            self.__driver.find_element(By.XPATH, xpath % f"contains(text(), '({folder})')]").click()
        elif self.__admin_console.check_if_entity_exists(entity_name='xpath',
                                                         entity_value=xpath % f"contains(text(), '{folder}')]"):
            self.__driver.find_element(By.XPATH, xpath % f"contains(text(), '{folder}')]").click()
        else:
            raise CVWebAutomationException(f"Given file/folder path [{folder}] does not exist")

    @WebAction()
    def __read_folder(self):
        """
        Select the folder or file
        """
        elems = self.__driver.find_elements(By.XPATH,
                                            self.__xp + f"//span[contains(@title, '') and contains(@class, 'ng-binding')]"
                                            )
        return [each_elem.text for each_elem in elems if each_elem]

    @WebAction()
    def _click_save(self):
        """ Method to click on save after selecting destination paths"""
        self.__driver.find_element(By.XPATH,
                                   '//button[@id="machineBrowse_button_#2266"]'
                                   ).click()

    @PageService()
    def select_path(self, path):
        """
        Selects Path
        Args:
            path (str): selects paths
        Examples:
            c:/data/f1  --> select f1
            c:  --> select c:
            data/f1  --> select f1
        """
        temp_path = path.replace('\\', '/')
        paths = temp_path.split('/')
        if '' in paths:
            paths.remove('')
        if len(paths) > 1:
            for idx in range(0, len(paths) - 1):
                self.__expand_folder(paths[idx])
                self.__admin_console.wait_for_completion()
        self.__select_folder(paths[-1])

    @PageService()
    def get_paths(self):
        """
        returns the visible paths as list
        """
        return self.__read_folder()

    @PageService()
    def save_path(self):
        """Method to click on save in restore panel after setting destination path"""
        self._click_save()
        self.__admin_console.wait_for_completion()


class RContentBrowse:
    """ Class to handle content browse in React subclient create/edit panels"""

    def __init__(self, admin_console):
        """Initalize the React content browse object
            Args:
                admin_console       (obj)       --  Admin console class object
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__tree = TreeView(admin_console)
        self.__xp = "//div[contains(@class, 'treeview-tree-content')]"

    @WebAction()
    def __read_folder(self):
        """
        Read the name of files in the folder
        """
        elems = self.__driver.find_elements(By.XPATH,
                                            self.__xp + "//ul//li//span[contains(@class, 'text-content')]"
                                            )
        return [each_elem.text for each_elem in elems if each_elem]

    @WebAction()
    def _click_save(self) -> None:
        """Method to click on save after selecting destination paths"""
        xpath = self.__xp + ("//ancestor::div[contains(@class, 'mui-modal-dialog')]"
                             "//div[contains(@class, 'modal-footer')]"
                             "/span[contains(@class, 'modal-footer-btn positive-modal-btn')]//button")
        self.__driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def select_path(self, path: str, wait_for_spinner: int = 60, **kwargs) -> None:
        """
        Selects Path
        Args:
            path (str): path of file or folder to select

            wait_for_spinner (int): Timeout in seconds to wait for spinner element

        Examples:
            c:/data/f1  --> select f1
            c:  --> select c:
            data/f1  --> select f1
        """
        if kwargs.get('expand_folder', True):
            self.expand_folder_path(folder=path, wait_for_spinner=wait_for_spinner, **kwargs)
        self.__tree.select_items([os.path.basename(path)])

    @PageService()
    def select_content(self, content):
        """
        this selects the required content
        args:
            content (list of strings)  :   list of content
        """
        self.__tree.select_items(content)

    @PageService()
    def unselect_content(self, content):
        """
        this unselects the required content
        args:
            content (list of strings)  :   list of content
        """
        self.__tree.unselect_items(content)

    @PageService()
    def get_paths(self) -> list:
        """
        returns the visible paths as list
        """
        return self.__read_folder()

    @PageService()
    def save_path(self) -> None:
        """Method to click on save button"""
        self._click_save()
        self.__admin_console.wait_for_completion()

    @PageService()
    def expand_folder_path(self, folder: str = None, wait_for_spinner: int = 60, **kwargs) -> None:
        """Expands the folder node with the folder name

            Args:

                folder      (str)   --  Expands folder if folder path is passed
                                        If None, then expands the first node.
                                        Eg. 1. C:/data/f1  --> expand f1
                                            2. C:  --> expand c:
                                            3. data/f1  --> expand f1

                wait_for_spinner    (int)   --  Timeout in seconds to wait for spinner element

        """

        if not folder:
            folder = self.get_paths()[0]

        paths = folder.replace('\\', '/').split('/')
        if '' in paths:
            paths.remove('')

        for node in paths:
            self.__tree.expand_node(node, wait_time=wait_for_spinner, **kwargs)


class CVAdvancedTree:
    """Class to handle content browse in CV Advanced Tree"""

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver

    @WebAction()
    def _expand_parent_elem(self, parent_elem):
        """
            Expand Client List
            Args:
                parent_elem (str) : Name of Parent Client to Expand
            """
        xp = f"//cv-advanced-tree//label[@title='{parent_elem}']/../preceding::span[1]"
        cv_arrow_elem = self.__driver.find_element(By.XPATH, xp)
        cv_arrow_status = cv_arrow_elem.get_attribute('class').split()[1]
        if cv_arrow_status == 'collapsed':
            cv_arrow_elem.click()
        return

    @WebAction()
    def _get_parent_element(self, parent_elem):
        """
            Get Parent Tree Node
            Args:
                parent_elem (str): Name of Parent Client

            Returns: Node Element for given parent

            """
        parent_elem = self.__driver.find_element(By.XPATH,
                                                 f"//cv-advanced-tree//label[@title='{parent_elem}']/../parent::cv-advanced-node"
                                                 )
        return parent_elem

    @WebAction()
    def _select_checkbox(self, parent_elem, checkbox_label):
        """
            Select Given Checkbox Element for mentioned parent elem
            Args:
                parent_elem : Parent Element which checkbox Belongs to
                checkbox_label (str): label for checkbox to be selected
            """
        label_elem = parent_elem.find_element(By.XPATH,
                                              f"//label[@title='{checkbox_label}']"
                                              )
        checkbox_input = parent_elem.find_element(By.XPATH,
                                                  f"//label[@title='{checkbox_label}']/preceding::input[1]"
                                                  )
        status = checkbox_input.get_attribute('class').split()[1]
        if status == 'unchecked':
            label_elem.click()

    @PageService()
    def select_elements(self, parent_elem, child_elems):
        """
            Select Mentioned Subclients
            Args:
                parent_elem (str) : parent element name
                child_elems (list) : list of children to be selected in the parent element
            """
        self._expand_parent_elem(parent_elem)
        self.__admin_console.wait_for_completion()
        parent_elem = self._get_parent_element(parent_elem)
        for child in child_elems:
            self._select_checkbox(parent_elem, child)

    @PageService()
    def select_elements_by_full_path(self, element_path, agent_type=None):

        """
        Selects the element by traversing through its entire ancestors
        Args:
            element_path    (list): list of strings to passed, with ancestors separated by '\' or '/'
            agent_type      (str) : type of Agent to be passed. Ex: (sharepoint, filesystem, onedrive)
        """
        for element in element_path:
            element = element.replace('\\', '/')
            if agent_type == "sharepoint":
                *parents, child = element.split(',')
            else:
                *parents, child = element.split('/')
            for parent in parents:
                self._expand_parent_elem(parent)
                self.__admin_console.wait_for_completion()
            self.select_elements(parents[-1], [child])
