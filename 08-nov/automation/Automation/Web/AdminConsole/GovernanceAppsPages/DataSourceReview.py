# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Sensitive Data Analysis
Project Data Source Review page.

Classes:

    DataSourceReview() ---> SensitiveDataAnalysisProjectDetails() --->
    SensitiveDataAnalysis() ---> GovernanceApps() ---> object()

DataSourceReview  --  This class contains all the methods for action in
    Sensitive Data Analysis Project Data Source Review page and is inherited by
    other classes to perform GDPR related actions

    Functions:
    get_data_source_name() -- Returns data source name from the admin page
    get_file_paths() -- Returns the list of file paths shown on the current page
    get_file_names() -- Returns the list of file names shown on the current page
    get_file_path_row_id() -- Returns the file path row id
    file_path_checked_status() -- Returns True/False based on the file path check box
    select_file() -- Selects the file for a file path
    clear_search_field() -- Clears the search field
    search_file() -- Search based on the file and folder and for a given data source
    expand_entity() -- Expands the given entity
    get_entities() -- Returns a Dictionary for all entities with its
                        corresponding list of values
    get_file_name() -- Returns the file name
    select_next_file() -- Selects the next file to review by
                            clicking on the right arrow if exists
    close_file_preview() -- Closes the file being previewed
    close_action_modal() --  Close the review action modal
    review_move_action() -- Review Move Files Action
    review_archive_action() -- Review Archive Files Action
    review_delete_action() --  Review Delete Action for Given Data Source
    review_ignore_files_action() --  Review Ignore Files Actions
    review_ignore_risks_actions() -- Review Ignore Risks Action
    review_set_retention_action() -- Review Set Retention Action
    get_advance_search_output()   -- Get Advance Search Output
    get_advance_search_query()    -- Get Advance Search query formed
    do_advanced_search()          -- Perform Advance Search
    expand_review_page_filter()   -- Expands search filter on review page
    apply_review_page_filter()    -- applies value to search filter on review page
    get_filter_values()           -- Gets search filter values shown in review page for given filter name
    _get_available_filters        -- Gets filter value available for given filter name in review page
    get_total_records()           -- Gets total records displayed in table
    review_tag_files_action()     -- Review Tag Files Action for List of Files
    click_sensitive_toggle()      -- Clicks on sensitive file toggle on review page
    get_tagged_file_names()       -- Returns the list of file names with the applied tag filter
"""
import re
import time

from dynamicindex.utils.constants import RETENTION_NOT_SET
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.core import Toggle, Checkbox
from Web.AdminConsole.Components.cventities import CVEntityMultiSelect
from Web.AdminConsole.Components.dialog import RModalDialog, Form
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.GovernanceAppsPages.SensitiveDataAnalysisProjectDetails import \
    SensitiveDataAnalysisProjectDetails
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.Common.page_object import PageService, WebAction


class DataSourceReview(SensitiveDataAnalysisProjectDetails):
    """
     This class contains all the methods for action in Sensitive Data Analysis
     Project Data Source Review page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.driver = self.__admin_console.driver
        self.log = self.__admin_console.log
        self.__table = Rtable(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__tag_grid_id = "tagActionModalForm"
        self.__cventities = CVEntityMultiSelect(
            self.__admin_console, self.__tag_grid_id)
        self.__dropdown = RDropDown(self.__admin_console)
        self.__fso = FSO(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console, 'dataSourceDetailsPage')
        self.__checkbox = Checkbox(self.__admin_console)
        self.__form = Form(self.__admin_console)
        self.actions_title_map = {
            self.__admin_console.props['label.datasource.onedrive']: {
                "DATA_FIELD": self.__admin_console.props['label.taskdetail.name'],
                "DELETE": "Delete files",
                "RETENTION": self.__admin_console.props['risks.action.retention'],
                "IGNORE_RISKS": self.__admin_console.props['risks.action.ignoreRisks'],
                "IGNORE_FILES_FOLDERS": "Ignore files"
            },
            self.__admin_console.props['label.datasource.file']: {
                "DATA_FIELD": self.__admin_console.props['entities.FileName'],
                "MOVE": "Move files",
                "DELETE": "Delete files",
                "ARCHIVE": "Archive files",
                "RETENTION": self.__admin_console.props['risks.action.retention'],
                "IGNORE_RISKS": self.__admin_console.props['risks.action.ignoreRisks'],
                "IGNORE_FILES_FOLDERS": "Ignore files",
                "TAG_FILES": "Tag documents"
            },
            self.__admin_console.props['label.datasource.googledrive']: {
                "DATA_FIELD": self.__admin_console.props['label.taskdetail.name'],
                "IGNORE_RISKS": self.__admin_console.props['risks.action.ignoreRisks'],
                "IGNORE_FILES_FOLDERS": "Ignore files"
            },
            self.__admin_console.props['label.datasource.exchange']: {
                "DATA_FIELD": self.__admin_console.props['label.subject'],
                "IGNORE_RISKS": self.__admin_console.props['risks.action.ignoreRisks'],
                "IGNORE_FILES_FOLDERS": "Ignore emails"
            },
            self.__admin_console.props['label.datasource.sharepoint']: {
                "DATA_FIELD": self.__admin_console.props['label.taskdetail.name'],
                "RETENTION": self.__admin_console.props['risks.action.retention'],
                "IGNORE_RISKS": self.__admin_console.props['risks.action.ignoreRisks'],
                "IGNORE_FILES_FOLDERS": "Ignore files"
            }
        }

    @WebAction()
    def get_data_source_name(self):
        """
        Returns data source name from the admin page
        """
        data_source_name = str(self.driver.find_element(By.XPATH, '//*[@id="dataSourceDetailsPage"]//h1').text)
        self.log.info("data source name obtained is: %s" % data_source_name)
        return data_source_name

    @WebAction()
    def _select_advanced_search(self):
        """
        Select Advanced search button in SDG data source
        review page
        """
        self.__admin_console.click_button(value=self.__admin_console.props['label.advancedsearch'])

    @WebAction()
    def _enter_advance_search_entity_value(self, selector_name, selector_value):
        """
        Enter advance search value
        Args:
            selector_name (str) : Entity name
            selector_value (str): Entity Value
        """
        xp = "//label[text()='{0}']/following::div[1]/input"
        elem = self.__admin_console.driver.find_element(By.XPATH,
                                                        xp.format(selector_name))
        elem.send_keys(selector_value)

    @PageService()
    def get_file_paths(self):
        """
        Returns the list of file paths shown on the current page

            Return:
                List of file paths
        """
        self.log.info("Obtaining all the file paths shown")
        return self.__table.get_column_data(self.__admin_console.props['entities.FolderName'])

    @PageService()
    def get_file_names(self, data_source='File system'):
        """
        Returns the list of file names shown on the current page

            Return:
                List of file names
        """
        return self.__table.get_column_data(
            self.actions_title_map[data_source]['DATA_FIELD'])

    @PageService()
    def get_advance_search_output(self, data_source='File system'):
        """
        Get output data after performing advanced search
        Args:
            data_source  (str): Data Source type of SDG
        Return :
            list Output data list
        """
        self.__table.set_pagination(500)
        self.__admin_console.wait_for_completion()
        return self.__table.get_column_data(
            self.actions_title_map[data_source]['DATA_FIELD'])

    @WebAction()
    def get_advance_search_query(self):
        """
        Get advanced search query formed
        Returns:
            (str) :- Advanced search query formed
        """
        return \
            self.__admin_console.driver.find_element(By.ID,
                                                     'queryInput').get_property('value')

    @PageService()
    def select_file(self, file_name):
        """
        Selects the file name link
        """
        self.__table.access_link_by_column(file_name, file_name)

    @WebAction()
    def clear_search_field(self):
        """
        Clears the search field
        """
        self.driver.find_element(By.ID, "searchInputFilterSearch").clear()

    @PageService()
    def do_advanced_search(self, selector_list=None, value_list=None,
                           input_query=None, data_source='File system'):
        """
        Perform Advanced search
        Args:
            selector_list (list): List of entities to be selected
            value_list    (list): List of values for respective entities given
            input_query   (str): Input Query for advanced search
            data_source   (str): Data Source Type
        """
        self._select_advanced_search()
        self.__admin_console.wait_for_completion()
        if input_query is not None:
            self.__admin_console.fill_form_by_id("queryInput", input_query)
            query = input_query
        else:
            self.__dropdown.select_drop_down_values(0, selector_list)
            if value_list is not None:
                for index, val in enumerate(selector_list):
                    self._enter_advance_search_entity_value(
                        val, value_list[index])
            query = self.get_advance_search_query()
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()

        output = []
        if data_source == 'File system':
            output = self.get_file_paths()
        else:
            output = self.get_advance_search_output(data_source=data_source)
        return output, query

    @PageService()
    def search_file(self, file_name, folder_name=None, is_fso=False,
                    data_source_type="File system"):
        """
        Search based on the file and folder name
        Args:
            file_name (str): Name of File
            folder_name (str): Name of Folder
            is_fso (bool): Is search operation done is FSO
            data_source_type (str): Data Source Type
        """
        # if data_source_type == self.__admin_console.props['label.datasource.onedrive']:
        #     search_string = file_name
        if data_source_type == self.__admin_console.props['label.datasource.googledrive']:
            search_string = '(FileName:{0})'.format(file_name)
        # elif data_source_type == self.__admin_console.props['label.datasource.exchange']:
        #     search_string = file_name
        elif data_source_type == self.__admin_console.props['label.datasource.database']:
            search_string = '(ColumnName:{0})'.format(file_name)
        # elif data_source_type == self.__admin_console.props['label.datasource.sharepoint']:
        #     search_string = '(FileName:{0})'.format(file_name)
        else:
            if folder_name is None:
                search_string = \
                    f'{file_name}'
            else:
                search_string = \
                    '(Url:{0}) AND (FileName:{1})'.format(
                        folder_name, file_name)
        if is_fso:
            search_string = file_name
        self.__enter_review_search(search_string)

    @WebAction()
    def __enter_review_search(self, search_string):
        """Enters the search text to the search bar for review files"""
        search_xpath = "//input[@aria-label='grid-search']"
        self.__admin_console.scroll_into_view(search_xpath)
        self.__table.search_for(search_string)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def expand_entity(self, entity_name, data_source_type="OneDrive"):
        """
        Expands the given entity

            Args:
                entity_name (str)  - Name of the entity
                data_source_type (str)  - Name of the data source
        """
        ds_db = self.__admin_console.props['label.datasource.database']
        ds_gd = self.__admin_console.props['label.datasource.googledrive']
        class_string = "treeview-tree-content"
        if data_source_type == ds_db or data_source_type == ds_gd:
            class_string = "treeview-tree-content"
        xpath = f"//div[contains(@class,'treeview-tree-content')]//span[contains(text(),'{entity_name}')]"
        self.log.info("Expanding Entity: %s" % entity_name)
        self.driver.find_element(
            By.XPATH,
            f"//div[contains(@class,'treeview-tree-content')]//span["
            f"contains(text(),'{entity_name}')]/../../../../span[1]").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def get_entities(self, data_source_type="OneDrive"):
        """
        Returns a Dictionary for all entities with its corresponding list of values

            Args:
                data_source_type (str)  - Name of the data source

            Return (Dict):
                Dictionary with list of entity values
        """
        ds_db = self.__admin_console.props['label.datasource.database']
        ds_gd = self.__admin_console.props['label.datasource.googledrive']
        sensitivity = self.__admin_console.props['label.filter.sensitivity']
        class_string = "treeview-tree-content"
        if data_source_type == ds_db or data_source_type == ds_gd:
            class_string = "panel-body"
        base_xp = f"//div[@class='{class_string}']//div[@role='tablist']"
        if data_source_type == ds_gd:
            base_xp = f"//h4[@class='panel-title']//span[text()='{sensitivity}']//ancestor::div[@role='tablist']"
        entities_list = []
        entities_dict = {}
        entity_name_xpath = "//div[contains(@class,'treeview-tree-content')]//span/span/span[2]"
        entity_value_xpath = "//div[contains(@class,'treeview-tree-content')]//span[" \
                             "contains(text(),'%s')]/../../../../../following-sibling::div//ul/li"
        entities = self.driver.find_elements(By.XPATH, entity_name_xpath)
        for entity in entities:
            entities_list.append(entity.text)
        self.log.info("Entity Names Obtained are: %s" % entities_list)
        for entity_name in entities_list:
            # RER entity will display entity count along with name. but classifiers will not so handle this
            if '(' in entity_name and ')' in entity_name:
                entity_name = " ".join(entity_name.split(" ")[:-1])
            self.expand_entity(entity_name, data_source_type)
            self.log.info(
                "Obtaining Entity Values for Entity: %s" %
                entity_name)
            entity_values = self.driver.find_elements(By.XPATH, entity_value_xpath % entity_name)
            entity_values_list = []
            for entity_value in entity_values:
                entity_values_list.append(entity_value.text)
            entity_values_list = sorted(entity_values_list, key=str.lower)
            entities_dict[entity_name.lower()] = entity_values_list
            self.expand_entity(entity_name, data_source_type)
        self.log.info(
            "Entities Dictionary obtained is: '{0}'".format(entities_dict))
        return entities_dict

    @WebAction()
    def get_file_name(self):
        """
        Returns the file name

            Return (str):
                Name of the file
        """
        file_name = self.driver.find_element(By.XPATH, "//h2[contains(@class,'mui-modal-title')]").text
        self.log.info("File Name Obtained is: %s" % file_name)
        return file_name

    @WebAction()
    def select_next_file(self):
        """
        Selects the next file to review by clicking on the right arrow if exists

            Return (Bool):
                True/False based on the status
        """
        xpath = "//div[@class='modal-content']//button[contains(@data-ng-click,'Next')]"
        if self.__admin_console.check_if_entity_exists('xpath', xpath):
            self.log.info("Clicking on the next button")
            self.driver.find_element(By.XPATH, xpath).click()
            self.__admin_console.wait_for_completion()
            return True

        self.log.info("Next button not found")
        return False

    @WebAction()
    def is_file_preview_present(self):
        """
        Is the file preview open
        Returns:
            bool - returns True if the file preview window is open
        """
        xpath = f"//div[@id='ContentPreview']"
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            return True
        else:
            return False

    @WebAction()
    def close_file_preview(self):
        """
        Closes the file being previewed
        """
        self.__dialog.click_close()

    @PageService()
    def close_action_modal(self):
        """
        Closes the Review Page Action Modal
        """
        self.__dialog.click_cancel()

    @WebAction()
    def _click_review_action(self, action_title):
        """
        Click on Review Action
        Args:
            action_title (str): Title of Review Action
        """
        page_action_xpath = "//div[@class='page-actions']"
        self.__admin_console.scroll_into_view(page_action_xpath)
        self.__page_container.access_page_action(action_title)

    @PageService()
    def click_sensitive_toggle(self):
        """Clicks on sensitive files toggle"""
        self.__admin_console.click_by_id("displaySensitiveFilesOnly")

    @PageService()
    def _enable_toggle(self, label):
        """
        Enable Toggle in Modal according to input label
        Args:
            label (str): Label for toggle element
        """
        self.__admin_console.toggle_enable(label)

    @WebAction()
    def _get_panel_element(self, name):
        """
        Get Panel Element in Review Page
        Args:
            name (str): Text within panel element

        Returns: Return Panel Element
        """
        elem = None
        xpath = f'//span[text()="{name}"]/ancestor::a'
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            elem = self.driver.find_element(By.XPATH, xpath)
        return elem

    @PageService()
    def review_move_action(self, file_name, destination_path, username=None, password=None, **kwargs):
        """
        Move action for a file
        Args:
            file_name         (str)    --  Name of the file
            destination_path  (str)    --  UNC path where the file would be moved
            username          (str)    --  Username needed to access the UNC path
            password          (str)    --  Password needed to access the UNC 

            Available **kwargs
            is_fso            (bool)   --  Is it a FSO Review Action
            data_source_type  (str)    --  Type of the datasource
            all_items_in_page (bool)   --  Take this action on all items present in the page
            all_items_in_datasource (bool)  -- Take this action on all items present in the datasource
            review_request    (bool)   --  To create Review Request
            reviewer          (str)    --  Reviewer to review the request
            request_name      (str)    --  Name of the review request
            approver          (str)    --  Approver of the review request
            credentials       (str)    --  Credential name
        Returns:
            bool - The status of this operation

        """
        data_source_type =  kwargs.get("data_source_type", "File system")
        is_fso = kwargs.get("is_fso", False)
        all_items_in_page = kwargs.get("all_items_in_page", False)
        all_items_in_datasource = kwargs.get("all_items_in_datasource", False)
        create_review_request = kwargs.get("review_request", False)
        credentials = kwargs.get("credentials", None)
        if create_review_request:
            reviewer = kwargs.get("reviewer", None)
            request_name = kwargs.get("request_name", None)
            approver = kwargs.get("approver")
            if not reviewer or not request_name:
              self.log.info("Insufficient review request args provided")
              return False
        if not all_items_in_datasource:
            if not all_items_in_page:
                self.search_file(file_name, is_fso=is_fso,
                                 data_source_type=data_source_type)
            self.__table.select_all_rows()
            review_page_file_list = self.get_file_names(data_source_type)
            self.log.info(review_page_file_list)

        self._click_review_action(
            self.actions_title_map[data_source_type]['MOVE'])
        self.__admin_console.wait_for_completion()
        self.__admin_console.fill_form_by_id(
            "path", destination_path)
        if credentials:
            self.log.info("Using saved credentials")
            self.__dropdown.select_drop_down_values(
                drop_down_id="credentials", values=[credentials])
        else:
            self.__checkbox.uncheck(id="toggleFetchCredentials")
            if username and password:
                self.__admin_console.fill_form_by_id("userName", username)
                self.__admin_console.fill_form_by_id("password", password)
            else:
                self.log.info("Username/password not supplied")
                return False
        if create_review_request:
            return self.create_review_request(reviewer=reviewer, request_name=request_name, approver=approver)
        self.__dialog.click_submit()

        if not all_items_in_page:
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()
            if is_fso:
                # Sleep for changes to reflect in UI
                time.sleep(60)
                self.__admin_console.refresh_page()
                self.__fso.fso_data_source_discover.select_fso_review_tab()
                self.search_file(file_name, is_fso=is_fso,
                                 data_source_type=data_source_type)
                review_page_file_list = self.__table.get_column_data(
                    self.actions_title_map[data_source_type]['DATA_FIELD'])
                return True if not review_page_file_list else False
        return True

    @PageService()
    def review_delete_action(self, file_name, delete_from_backup=False, is_fso=False,
                             data_source_type='File system', all_items_in_page=False, review_request=False,
                             reviewer=None, request_name=None, approver=None, all_items_in_datasource=False,):
        """
        Review delete action for list of files
        Args:
            file_name          (str)   -- Name of the file
            data_source_type   (str)   -- Data source type
            is_fso             (bool)  -- Is it FSO delete action
            delete_from_backup (bool)  -- To enable delete from backup
            all_items_in_page  (bool)  -- Take this action on all items present in the page
            all_items_in_datasource (bool)  -- Take this action on all items present in the datasource
            review_request     (bool)  -- To create Review Request
            reviewer           (str)   -- Reviewer to review the request
            request_name       (str)   -- Name of the review request
            approver           (str)   -- Approver of the review request
        Return (bool):
                True/False based on the status

        """
        if not all_items_in_datasource:
            if not all_items_in_page:
                self.search_file(file_name, is_fso=is_fso,
                                 data_source_type=data_source_type)
            self.__table.select_all_rows()
        self._click_review_action(
            self.actions_title_map[data_source_type]['DELETE']
        )
        self.__admin_console.wait_for_completion()
        if not all_items_in_datasource:
            self.__admin_console.select_radio("selectedFiles")
        if delete_from_backup:
            self.__admin_console.select_radio("deleteFilesFromBackup")
        if review_request:
            return self.create_review_request(reviewer=reviewer, request_name=request_name, approver=approver)
        self.__dialog.click_submit()
        if not all_items_in_page:
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()
            if is_fso:
                # Sleep for changes to reflect in UI
                time.sleep(60)
                self.__admin_console.refresh_page()
                self.__fso.fso_data_source_discover.select_fso_review_tab()
                self.search_file(file_name, is_fso=is_fso,
                                 data_source_type=data_source_type)
                review_page_file_list = self.__table.get_column_data(
                    self.actions_title_map[data_source_type]['DATA_FIELD'])
                return True if not review_page_file_list else False
        return True

    @PageService()
    def review_archive_action(self, file_name, archive_plan, is_fso=False, data_source_type='File system',
                              all_items_in_page=False, review_request=False, reviewer=None, request_name=None,
                              approver=None, all_items_in_datasource=False):
        """
        Review Archive action for list of files
        Args:
            file_name          (str)   -- Name of the file
            archive_plan       (str)   -- Name of the Archive plan
            data_source_type   (str)   -- Data source type
            is_fso             (bool)  -- Is it FSO Archive action
            all_items_in_page  (bool)  -- Take this action on all items present in the page
            all_items_in_datasource (bool)  -- Take this action on all items present in the datasource
            review_request     (bool)  -- To create Review Request
            reviewer           (str)   -- Reviewer to review the request
            request_name       (str)   -- Name of the review request
            approver           (str)   -- Approver of the review request
        Return (bool):
                True/False based on the status

        """
        if not all_items_in_datasource:
            if not all_items_in_page:
                self.search_file(file_name, is_fso=is_fso,
                                 data_source_type=data_source_type)
            self.__table.select_all_rows()
        self._click_review_action(
            self.actions_title_map[data_source_type]['ARCHIVE']
        )
        self.__admin_console.wait_for_completion()
        if not all_items_in_datasource:
            self.__admin_console.select_radio("selectedFiles")
        self.__dropdown.select_drop_down_values(0, [archive_plan])
        if review_request:
            return self.create_review_request(reviewer=reviewer, request_name=request_name, approver=approver)
        self.__dialog.click_submit()
        if not all_items_in_page:
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()
            if is_fso:
                # Sleep for changes to reflect in UI
                time.sleep(60)
                self.__admin_console.refresh_page()
                self.__fso.fso_data_source_discover.select_fso_review_tab()
            self.search_file(file_name, is_fso=is_fso,
                             data_source_type=data_source_type)
            review_page_file_list = self.__table.get_column_data(
                self.actions_title_map[data_source_type]['DATA_FIELD']
            )
        else:
            completed = True
            try:
                completed = self.__fso.track_job(
                    job_operation='FileOperations')
            except NoSuchElementException:
                self.log.info(
                    "Couldn't find the workflow job. Proceeding further")
            return completed

        return True if not review_page_file_list else False

    @PageService()
    def review_ignore_files_action(
            self,
            file_name,
            data_source_type='File system',
            all_items_in_page=False,
            review_request=False,
            reviewer=None,
            request_name=None,
            approver=None):
        """
        Review Ignore Files Action for List of Files
        Args:
            file_name          (str)  --  Name of the fiLe
            data_source_type   (str)  --  Datasource type
            all_items_in_page  (bool) --  Perform this review action on all the items present in the page
            review_request     (bool)  -- To create Review Request
            reviewer           (str)   -- Reviewer to review the request
            request_name       (str)   -- Name of the review request
            approver           (str)   -- Approver of the review request

        Return (bool):
                True/False based on the status

        """
        # Make Sure Display Sensitive Files Toggle Is On
        if not all_items_in_page:
            self.search_file(file_name, data_source_type=data_source_type)
        self.__table.select_all_rows()
        self._click_review_action(
            self.actions_title_map[data_source_type]["IGNORE_FILES_FOLDERS"]
        )
        self.__admin_console.wait_for_completion()
        self.__admin_console.select_radio("selectedFiles")
        if review_request:
            return self.create_review_request(reviewer=reviewer, request_name=request_name, approver=approver)
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
        return True

    @PageService()
    def review_ignore_risks_actions(self, file_name,
                                    risk_type_list, data_source_type='File system',
                                    all_items_in_page=False, review_request=False,
                                    request_name=None, reviewer=None, approver=None):
        """
        Review Ignore Risks action for file(s) in a review page
        Args:
            file_name         (str)  : Name of the file
            risk_type_list    (list) : List of risks to be ignored
            data_source_type  (str)  : Datasource type
            all_items_in_page (bool) : Take this action on all items present in the page
            review_request     (bool)  -- To create Review Request
            reviewer           (str)   -- Reviewer to review the request
            request_name       (str)   -- Name of the review request
            approver           (str)   -- Approver of the review request

        Return (bool):
            True/False based on the status

        """
        if not all_items_in_page:
            self.search_file(file_name, data_source_type=data_source_type)
        self.__table.select_all_rows()
        self._click_review_action(
            self.actions_title_map[data_source_type]["IGNORE_RISKS"]
        )
        self.__admin_console.wait_for_completion()
        self.__dropdown.select_drop_down_values(values=risk_type_list,
                                                drop_down_id="riskTypes")
        self.__admin_console.select_radio("selectedFiles")
        if review_request:
            return self.create_review_request(reviewer=reviewer, request_name=request_name, approver=approver)
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
        return True

    @PageService()
    def review_set_retention_action(self, file_name, retention_months, **kwargs):
        """
        Args:
            file_name         (str)  : Filename
            retention_months  (int)  : No. of months

            Available kwargs:

            data_source_type  (str)  : Datasource type
            all_items_in_page (bool) : Take this action on all items present in the page
            review_request     (bool)  -- To create Review Request
            reviewer           (str)   -- Reviewer to review the request
            request_name       (str)   -- Name of the review request
            approver           (str)   -- Approver of the review request

        Returns:
            True/False based on the status

        """
        data_source_type = kwargs.get("data_source_type", "File system")
        all_items_in_page = kwargs.get("all_items_in_page=", False)
        review_request = kwargs.get("review_request", False)
        reviewer = kwargs.get("reviewer", None)
        request_name = kwargs.get("request_name", None)
        approver = kwargs.get("approver", None)
        if not all_items_in_page:
            self.search_file(file_name, data_source_type=data_source_type)
        self.__table.select_all_rows()
        self._click_review_action(
            self.actions_title_map[data_source_type]["RETENTION"]
        )
        self.__admin_console.wait_for_completion()
        self.__admin_console.select_radio("selectedFiles")
        self.__form.fill_input_by_xpath(text=retention_months, element_xpath=".//div/input")
        if review_request:
            return self.create_review_request(reviewer=reviewer, request_name=request_name, approver=approver)
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
        return True

    @PageService()
    def risks_present(self, filename, risk_type_list, data_source_type="File system"):
        """
        Checks whether risks are present in a file
        Args:
             filename (str)          -- Name of the file
             data_source_type (str)  -- Data source type
             risk_type_list  (list)  -- Risks to be checked

         Return (bool):
                 True/False based on the availability of the retention risk
        """
        ignore_risks_flag = False
        self.search_file(filename, data_source_type=data_source_type)
        self.__table.select_rows([''])
        elem = self._get_panel_element(
            self.__admin_console.props['label.taskdetail.risks'])
        self.__admin_console.wait_for_completion()
        if elem is not None:
            if not elem.get_attribute("aria-expanded"):
                elem.click()
            for risks in risk_type_list:
                elem = self._get_panel_element(risks)
                self.__admin_console.wait_for_completion()
                if elem is not None:
                    ignore_risks_flag = True
                    break
            self.__table.select_rows([''])
        return ignore_risks_flag

    @WebAction()
    def expand_review_page_filter(self, filter_name):
        """
        Expands filter dropdown on review page
            Args:
                filter_name (str): Name of filter
        """
        self.__admin_console.driver.find_element(By.ID,
                                                 filter_name
                                                 ).click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def _get_available_filters(self, filter_name):
        """
                Gets search filter values shown in review page for given filter name

                    Args:
                        filter_name (str): Name of the filter

                    Returns:

                         (list)  -- returns filter value
        """
        return self.__dropdown.get_values_of_drop_down(drop_down_id=filter_name)

    @PageService()
    def get_filter_values(self, filter_name):
        """
        Gets search filter values shown in review page for given filter name

            Args:
                filter_name (str): Name of the filter

            Returns:

                 (dict)  -- returns filter value as key-value pair
        """
        temp_dict = {}
        temp_list = self._get_available_filters(filter_name=filter_name)
        for item in temp_list:
            match = re.match(r'(.+?)\s*\((\d+)\)', item)
            if match:
                key = match.group(1).strip()
                value = int(match.group(2))
                temp_dict[key] = value
        return temp_dict

    @WebAction()
    def get_total_records(self):
        """
                Gets total records displayed in table in review page

                    Args:
                        None

                    Returns:

                         (Int)  -- total records found in table
        """
        return self.__table.get_total_rows_count()

    @WebAction()
    def apply_review_page_filter(self, filter_name, filter_value):
        """
        Applies value on filter dropdown in review page

            Args:

                filter_name (str): Name of filter

                filter_value(str): Value of filter to be applied

            Returns:

                None
        """
        self.__dropdown.select_drop_down_values(
            drop_down_id=filter_name,
            values=[filter_value],
            preserve_selection=True,
            partial_selection=True,
            facet=True)
        self.__admin_console.wait_for_completion()

    @PageService()
    def review_tag_files_action(self, file_name, tag_name, is_fso=False, data_source_type='File system',
                                all_items_in_page=False, review_request=False, reviewer=None, request_name=None,
                                approver=None):
        """
        Review Tag Files Action for List of Files

            Args:

                file_name (str)          :     Name of The File
                tag_name                 :     Name of the tag to be applied
                data_source_type (str)   :     Data Source type
                is_fso (bool)            :     Is it FSO tagging action
                all_items_in_page (bool) :     Take this action on all items present in the page
                review_request     (bool):      To create Review Request
                reviewer           (str) :      Reviewer to review the request
                request_name       (str) :      Name of the review request
                approver           (str) :      Approver of the review request

            Return (Bool):

                True/False based on the status

        """
        tag_exists = False
        if not all_items_in_page:
            self.search_file(file_name, is_fso=is_fso,
                             data_source_type=data_source_type)
        self.__table.select_all_rows()
        self._click_review_action(
            self.actions_title_map[data_source_type]['TAG_FILES']
        )
        self.__admin_console.wait_for_completion()
        self.__admin_console.select_radio("selectedFiles")
        self.__admin_console.wait_for_completion()
        if self.__cventities.search_and_select(tag_name, click_submit=not review_request):
            tag_exists = True
        if review_request:
            return self.create_review_request(reviewer=reviewer, request_name=request_name, approver=approver)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

        return True if tag_exists else False

    @PageService()
    def get_tagged_file_names(self, tag_name):
        """
        Returns the list of file names with the applied tag filter

            Args:

                 tag_name (str)   :     Name of the tag to be applied

        """
        self.apply_review_page_filter(
            self.__admin_console.props['label.tags'], tag_name)
        self.__admin_console.wait_for_completion()

        return self.__table.get_column_data("Name")

    @WebAction()
    def fill_review_request_name(self, request_name):
        """
        Fills review request name in the textbox
        Args:
            request_name    (str):  Name of the request
        """
        self.__admin_console.fill_form_by_id("reviewRequestName", request_name)

    @WebAction()
    def _add_reviewer(self, reviewer):
        """
        Add a reviewer to review the request
        Args:
            reviewer    (str):  Username of the reviewer
        """
        self.__dropdown.select_drop_down_values(values=[reviewer], drop_down_label="Reviewers",
                                                partial_selection=True)
        self.__dialog.click_submit()

    @WebAction()
    def _add_approver(self, approver):
        """
        Add a approver to review the request
        Args:
            approver    (str):  Username of the approver
        """
        self.__dropdown.select_drop_down_values(values=[approver], drop_down_label="Approvers",
                                                partial_selection=True)
        self.__dialog.click_submit()

    @PageService()
    def create_review_request(self, reviewer, request_name=None, approver=None):
        """
        Creates a review Request
        Args:
            reviewer        (str):  Username of the reviewer
            request_name    (str):  Name of the request
            approver        (str):  Username of the approver
        """
        if not reviewer:
            raise Exception(f'Invalid Input for Reviewer: {reviewer}')
        toggle = Toggle(self.__admin_console)
        toggle.enable(id="createReviewRequest")
        if request_name:
            self.fill_review_request_name(request_name)
        self._add_reviewer(reviewer)
        if approver:
            self._add_approver(approver)
        self.__admin_console.wait_for_completion()
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()
        return True
