from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done on ComplianceSearch page.

ComplianceSearch  --  This class contains all the methods ComplianceSearch related actions

    Functions:

    click_confirm_delete_option()                   -- Click to confirm delete exportset
    click_search_button()                           -- Click on search button in compliance search ui
    get_preview_body()                              -- Gets text from compliance search preview
    clear_custodian_filter_all()                    -- Clears all selected filters in compliance search
    set_indexserver_and_searchview_preference()     -- Sets index and filetype preferences for search
    select_custodian_and_get_results()              -- Clicks on custodian link and returns count
    set_searchview_dropdown()                       -- Sets the given types on the serachview dropdown
    unset_searchview_dropdown()                     -- Unsets the given types on the serachview dropdown
    search_for_keyword_get_results()                -- Enters a keyword and retrieves search results
    do_export_to()                                  -- Performs export operations
    get_export_job_details()                        -- Gets export job completion details
    perfom_download()                               -- Downloads the export set with given jobid
    delete_exportset()                              -- Deletes export set of given jobid
    get_total_rows_count()                          -- Gets total number of items retrieved
    set_datatype()                                  -- Sets datatypes considered for search

CustomFilter  --  This class contains all the methods related to filters in compliance search

    Functions:

    clear_custodian_filter                          -- Clears Custodian filter
    select_filter_dropdown                          -- Select filter
    select_date_filter                              -- Filer with date
    select_size_filter                              -- Filter with size
    select_custom_filter                            -- Select value in filter using facets
    select_custom_filter_with_search                -- Search in the facet searchbar and select
    apply_date_filters                              -- Applies date filters
    apply_size_filters                              -- Applies size filters
    apply_filetype_filters                          -- Applies filetype filter
    apply_custom_filters                            -- Applies custom filters
    apply_custom_filters_with_search                -- Applies custom filters after searching
    enter_custom_filters                            -- Enter value in facet searchbar

"""

import re
import time
from dateutil.parser import parse
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.table import CVTable
from Web.AdminConsole.Components.panel import DropDown
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.panel import ModalPanel, PanelInfo
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.alert import Alert
from Web.Common.page_object import (
    WebAction, PageService
)
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
from Web.AdminConsole.Components.table import Rtable


class ComplianceSearch:
    """
     This class contains all the methods for action in ComplianceSearch page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        self.__admin_console = admin_console
        self.driver = admin_console.driver
        self.__table = Rtable(self.__admin_console)
        self.__panel = ModalPanel(self.__admin_console)
        self.__dropdown = RDropDown(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__export_to_dialog = _ExportToForm(self.__admin_console)
        self.__custom_filter = CustomFilter(self.__admin_console)
        self.__cvtable = CVTable(self.__admin_console)
        self.__job = Jobs(self.__admin_console)
        self.__browse = Browse(self.__admin_console)
        self.export_jobid = None

    @WebAction(delay=1)
    def __select_export_to(self):
        """
        select Export To operation

        Args:
            operation (str)  :  Type of operation- CAB/PST/PDF
        """
        element = self.driver.find_element(By.XPATH,
                                           "//button[@id='EXPORT_TO']")
        element.click()
        self.__admin_console.wait_for_completion()

    @WebAction(delay=1)
    def __select_table_checkbox(self, count):
        """
        Method to select values from a table

        Args:
            count (int)  :  Number of items to be chosen in the table, starting from zero
        """
        elements = self.driver.find_elements(By.XPATH, "//input[@class='k-checkbox k-checkbox-md k-rounded-md']")
        if len(elements) - 1 <= count:
            elements[0].click()
        else:
            idx = 2
            while idx <= count:
                elements[idx].click()
                idx += 1

    @WebAction()
    def __enter_search_term(self, value, is_grid=False):
        """
        enter search on grid
        Args:
                value (str)  - keyword to be searched for
                is_grid (bool) - to make searching in Export Set and Query Set grids.
        """
        xpath = "//input[@id='search-bar']"
        if is_grid:
            xpath = "//input[@aria-label='grid-search']"
        search = self.driver.find_element(By.XPATH, xpath)
        search.click()
        search.clear()
        search.send_keys(value)
        search.send_keys(Keys.ENTER)

    @WebAction()
    def __download_export_set(self, job_id):
        """
         Click to download exportset
         Args:
                 job_id (str)  - Id of export set job
         """
        self.driver.find_element(By.XPATH,
                                 f"//*[text() ='{job_id}']/ancestor::tr//div[contains(@class,"
                                 f"'action-cell-container')]/div"
                                 ).click()
        time.sleep(3)
        self.driver.find_element(By.XPATH,
                                 "//ul[contains(@class,'MuiList-root MuiList-padding')]//li[text()='Download']"
                                 ).click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def click_confirm_delete_option(self):
        """
        Click to confirm delete exportset
        """
        self.driver.find_element(By.XPATH,
                                 "//html/body/div[1]/div/div//button[@class='btn btn-primary ng-binding']").click()

    @WebAction()
    def click_search_button(self):
        """
        Clicks on search button
        """
        elem = self.driver.find_element(By.XPATH, "//button[@title='Search']")
        elem.click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def get_preview_body(self):
        """
        Gets text from compliance search preview
        """
        self.driver.switch_to.frame('iframeForPreview')
        preview_xpath = self.driver.find_element(By.XPATH, "//pre")
        return preview_xpath.text

    @PageService()
    def clear_custodian_filter_all(self):
        """
        Clears all filters applied
        """
        self.__admin_console.refresh_page()
        self.click_search_button()

    @PageService()
    def set_indexserver_and_searchview_preference(self, index_server, search_view):
        """Setting IndexServer and SearchView
         Args:
                index_server (str)  - index_server to be set
                search_view (str)   - search_view to be set
        """
        self.__admin_console.select_configuration_tab()
        self.__admin_console.wait_for_completion()
        panel_info = RPanelInfo(admin_console=self.__admin_console, title='Preference')
        panel_info.edit_tile()
        self.__admin_console.wait_for_completion()
        self.__dropdown.select_drop_down_values(
            drop_down_id='searchEngineDropdown', values=[index_server])
        self.__dropdown.select_drop_down_values(
            drop_down_id='searchViewDropdown', values=[search_view])
        panel_info.save()
        self.__admin_console.wait_for_completion()
        self.__admin_console.access_tab('Search')
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_custodian_and_get_results(self, user_smtp_list):
        """
        Clicks on Custodian link and returns count
         Args:
                user_smtp_list (list)  - list of custodian users

         Returns number of items
        """
        self.__custom_filter.select_filter_dropdown('Custodian')
        if len(user_smtp_list) > 1:
            # multiple users, clear the previous case of single user selection
            self.__custom_filter.clear_custodian_filter()
            self.__admin_console.wait_for_completion()
            self.__custom_filter.select_filter_dropdown('Custodian')
        self.__custom_filter.select_custom_filter(user_smtp_list)
        self.__admin_console.wait_for_completion()
        count = self.__table.get_total_rows_count()
        return int(count)

    @PageService()
    def set_searchview_dropdown(self, search_view_types):
        """
        Sets the given data types on the serachview dropdown on the Search Tab
        Args:
            search_view_types (list)  - list of str containing type names
        """
        self.__dropdown.select_drop_down_values(drop_down_id='applicationType', values=search_view_types)

    @PageService()
    def unset_searchview_dropdown(self, search_view_types):
        """
        Unsets the given data types on the serachview dropdown on the Search Tab
        Args:
            search_view_types (list)  - list of str containing type names
        """
        self.__dropdown.deselect_drop_down_values(index=0, values=search_view_types)

    @PageService()
    def search_for_keyword_get_results(self, index_server, keyword):
        """
        Searches for a given keyword

            Args:
                keyword (str)  - keyword name to be searched for
                index_server (str)  - index_server to be set

            Returns Number of items
        """
        self.set_indexserver_and_searchview_preference(index_server, "Email")
        count = self.get_total_rows_count(keyword)
        return int(count)

    @PageService()
    def do_export_to(self,
                     operation_type,
                     selected_item_count,
                     download_set_name,
                     export_set_name,
                     file_format=None):
        """
        perform export to operations
            Args:
                operation_type (str)  - CAB/PST
                selected_item_count (str)  - Number of items to be selected and exported
                                             All- for all items
                download_set_name (str) - Name of download set name
                export_set_name (str)   -   Name of the export set
                file_format (str) - Format of exported message (Applicable only for Export To CAB)
            Returns:
                1 - Export Job submitted successfully
                0- Error submitting Export Job
        """
        if 'All' not in str(selected_item_count):
            self.__select_table_checkbox(int(selected_item_count))
        self.__select_export_to()
        self.__export_to_dialog.choose_selection_range(str(selected_item_count))
        self.__export_to_dialog.create_new_export_set(export_set_name)
        self.__export_to_dialog.enter_export_name(download_set_name)
        self.__export_to_dialog.choose_file_format(operation_type, file_format)
        self.export_jobid = self.__admin_console.get_jobid_from_popup()
        if not self.export_jobid:
            return 0
        else:
            return 1

    @PageService()
    def get_export_job_details(self):
        """get export jobid and details upon job completion"""
        job_details = self.__job.job_completion(self.export_jobid)
        return self.export_jobid, job_details

    @PageService()
    def perfom_download(self, jobid, export_set_name):
        """
        perform download operation on given jobid
            Args:
                export_set_name: Name of the export set
                jobid (str): Export Job id
        """
        try:
            self.__admin_console.access_tab('Export sets')
            self.__admin_console.wait_for_completion()
            self.__enter_search_term(export_set_name, is_grid=True)
            time.sleep(5)
            self.driver.find_element(By.PARTIAL_LINK_TEXT, export_set_name).click()
            self.__admin_console.wait_for_completion()
            self.__download_export_set(jobid)
            self.__dialog.click_cancel()
            self.__admin_console.wait_for_completion()
        except Exception as excp:
            raise CVWebAutomationException(f'Export set download failed: {excp}')

    @PageService()
    def delete_exportset(self, export_set_name):
        """
        delete exportset of given jobid
            Args:
                export_set_name:  Name of the export set
        """
        self.__admin_console.access_tab('Export sets')
        self.__admin_console.wait_for_completion()
        self.__table.access_action_item(entity_name=export_set_name, action_item='Delete')
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_total_rows_count(self, search_keyword=None):
        """
        Get the total number of items
        Args:
                search_keyword (str)  - keyword to be searched for
                                        it will return rows already present

        Returns Number of items in table
        """
        if search_keyword:
            self.__enter_search_term(search_keyword)
            self.__admin_console.wait_for_completion()
        return self.__table.get_total_rows_count()

    @WebAction()
    def click_datatypes(self):
        """
        Method to click react datatypes section
        """
        self.driver.find_element(By.XPATH, f"//button[contains(@aria-label, 'View')]").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def set_datatype(self, datatypes):
        """ Method to select the datatypes to be retrieved
        Args:
                datatypes (List)  - List of datatypes to be selected
        """
        self.click_datatypes()
        self.__dropdown.select_drop_down_values(
            drop_down_id='searchAppDropdown', values=datatypes)
        self.__dialog.click_submit()


class CustomFilter:
    """
    This class contains all functions for selecting custom filters
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver

    @WebAction()
    def clear_custodian_filter(self):
        """
        Clears custodian filter
        Returns: bool - True/False
        """
        try:
            clear_button = self.__driver.find_element(By.CSS_SELECTOR,
                                                      ".ng-not-empty+ .ng-binding")
            if clear_button:
                clear_button.click()
            return True
        except Exception:
            return False

    @WebAction()
    def select_filter_dropdown(self, filtername):
        """
        select filter
        Args: filtername (str): Type of filter to be selected

        Returns: bool - True/False
        """
        try:
            element = self.__driver.find_element(By.XPATH,
                                                 "//*[@class=\"row\"]//span[contains(text(),'" + filtername + "')]")
            if element:
                # First check if already expanded
                # If not expanded, click; Otherwise don't do anything
                if not element.find_element(By.XPATH,
                                            './/ancestor::div[contains(@class, "cv-accordion-header expanded")]'):
                    element.click()
            return True
        except Exception:
            return False

    @WebAction()
    def select_date_filter(self, values_list):
        """
        Select Date filter and enter value
        Args: values_list (list) : list of date values to be selected
                                Ex: ["Beyond one year","past year",'12/12/2019"]
                                if value in the above list matches date format (ex: 12/12/2019), then it will be entered in the
                                from date textbox in the filter. Search will be fired for date from that date to till date
                                else, it is do string comparision and select the filter value (ex: past month, past year... )

        """
        # enter date
        is_date = False
        for value in values_list:
            try:
                if parse(value, fuzzy=False):
                    is_date = True
            except ValueError:
                is_date = False

            finally:
                if is_date:
                    endtime_text_box = self.__driver.find_element(By.XPATH,
                                                                  "//input[contains(@id,'cv-kendo-endtime')]")
                    endtime_text_box.clear()
                    endtime_text_box.send_keys(value)
                    add_element = self.__driver.find_element(By.XPATH,
                                                             "//*[@class=\"search-preview-panel search-preview-row\"]"
                                                             "//span[1]/a[contains(text(),'Add')]")
                    add_element.click()
                    return True
                else:
                    return self.select_custom_filter([value])

    @WebAction()
    def select_size_filter(self, values_list):
        """
        Select Size filter and enter value
        Args: values_list (list) : list of size values to be selected
        Ex: ["1 - 5 MB","6-20 SizeKB"]
                                if value in the above list contains "KB" string, it will be entered in the range text box.
                                ex: 6 to 20 KB
                                else, it is do string comparision and select the filter value (ex: 1-5 MB )
        """
        selected = False
        for value in values_list:
            if "SizeKB" in value:
                values = re.findall(r'\d+', value)
                from_text_box = self.__driver.find_element(By.XPATH,
                                                           "//input[@id=\"sizeValueInputFrom\"]")
                from_text_box.clear()
                from_text_box.send_keys(values[0])
                self.__admin_console.wait_for_completion()
                to_text_box = self.__driver.find_element(By.XPATH,
                                                         "//input[@id=\"sizeValueInputTo\"]")
                to_text_box.clear()
                to_text_box.send_keys(values[1])
                self.__admin_console.wait_for_completion()

                add_element = self.__driver.find_element(By.XPATH, f"//div[@id='Size']//div[@class='panel-content "
                                                                   f"']//button[contains(@aria-label, 'Add')]")
                add_element.click()
                self.__admin_console.wait_for_completion()
                selected = True
            else:
                selected = self.select_custom_filter([value])
        return selected

    @WebAction(delay=4)
    def select_custom_filter(self, value_list):
        """
        select values in filter
        Args:
                value_list (list)  - List of values(strings) to be selected for filtering
                                   ex:[abc@def.com, "test username",..]

        Returns: False : if value is not available in the list of facets
                else True
        """
        try:
            value_button_list = []
            for value in value_list:
                xpath = f"//label[contains(@class, 'Checkbox-label')]//span[contains(text(), '{value}')]"
                value_button_list.append(xpath)

            for path in value_button_list:
                if self.__driver.find_element(By.XPATH, path):
                    self.__driver.find_element(By.XPATH, path).click()
                    self.__admin_console.wait_for_completion()
            return True
        except NoSuchElementException:
            return False

    @WebAction(delay=4)
    def select_custom_filter_with_search(self, filtertype, value_list):
        """
        select values in filter
        Args:
                filtertype(string) - Type of the filter to which the value_list belongs to
                value_list (list)  - List of values(strings) to be selected for filtering
                                   ex:[abc@def.com, "test username",..]

        Returns: False : if value is not available in the list of facets
                else True
        """
        try:
            if filtertype == 'Attachment':
                for value in value_list:
                    attachment_value = 'Has' if value == 'true' else 'No'
                    self.__driver.find_element(By.XPATH, f"//span[contains(text(), '{attachment_value} attachment')]").click()
                    self.__admin_console.wait_for_completion()
                return True
            filtertype = "Enter " + filtertype
            facet = "//input[@placeholder='" + filtertype + "']"
            for value in value_list:
                elem = self.__driver.find_element(By.XPATH, facet)
                elem.send_keys(value)
                self.__admin_console.wait_for_completion()
                elem.send_keys(Keys.ARROW_DOWN)
                elem.send_keys(Keys.ENTER)
                self.__admin_console.wait_for_completion()

            return True
        except NoSuchElementException:
            return False

    @WebAction()
    def __enter_facet_value(self, value):
        """
        Enter values in textbox
        Args:
                value  - string to be selected for filtering
                                   ex:[abc@def.com, "test username",..]
        """
        text_box = self.__driver.find_element(By.XPATH, "(//input[@placeholder=\'Enter Email folder\'])")
        text_box.clear()
        text_box.send_keys(value[0:7])
        time.sleep(3)
        suggestion_element = self.__driver.find_element(By.XPATH, "//a[@ng-attr-title=\"{{match.label}}\"]")
        suggestion_element.click()

    @PageService()
    def apply_date_filters(self, daterange_list):
        """
        Applies date filter if it exists
         Args:
                daterange list(str)  - list of Date ranges whose value has to be applied
         :returns
                 True : if date filter is applied
                 False: if date filter is not applied
        """
        try:
            is_date_selected = self.select_date_filter(daterange_list)
            self.__admin_console.wait_for_completion()
            return is_date_selected
        except NoSuchElementException:
            return False

    @PageService()
    def apply_size_filters(self, sizerange_list):
        """
        Applies size filter if it exists
         Args:
                sizerange list(str)  - list of Size ranges whose value has to be applied
         :returns
                 True : if size filter is applied
                 False: if size filter is not applied
        """
        try:
            is_size_selected = self.select_size_filter(sizerange_list)
            self.__admin_console.wait_for_completion()
            return is_size_selected
        except NoSuchElementException:
            return False

    @PageService()
    def apply_filetype_filters(self, ftype):
        """
        Apply file type filter if it exists
        Args:
                ftype (str) - type of file to filter for
        """
        try:
            time.sleep(2)
            text_box = self.__driver.find_element(By.XPATH, "(//input[@placeholder=\'Enter File type\'])")
            text_box.clear()
            text_box.send_keys(ftype)
            time.sleep(3)
            suggestion_element = self.__driver.find_element(By.XPATH, "//a[@ng-attr-title=\"{{match.label}}\"]")
            suggestion_element.click()
            self.__admin_console.wait_for_completion()
            return True
        except NoSuchElementException:
            return False

    @PageService()
    def apply_custom_filters(self, filters_list):
        """
        Applies custom filters if they exist
         Args:
                 filterslist (dict)  - dictionary with filter name as Key
                and list of filter content as Value
         :returns
                dict: applied filters
        """
        parameters = {}
        for filtertype in filters_list:
            try:
                filter_values = filters_list[filtertype]
                parameters[filtertype] = self.select_custom_filter(filter_values)
            except NoSuchElementException:
                parameters[filtertype] = False
            self.__admin_console.wait_for_completion()
        return parameters

    @PageService()
    def apply_custom_filters_with_search(self, filters_list):
        """
        Applies custom filters if they exist by entering the item in the facet search bar
         Args:
                 filterslist (dict)  - dictionary with filter name as Key
                and list of filter content as Value
         :returns
                dict: applied filters
        """
        parameters = {}
        for filtertype in filters_list:
            try:
                filter_values = filters_list[filtertype]
                parameters[filtertype] = self.select_custom_filter_with_search(filtertype, filter_values)
            except NoSuchElementException:
                parameters[filtertype] = False
            self.__admin_console.wait_for_completion()
        return parameters

    @PageService()
    def enter_custom_filters(self, filtertype, value):
        """
        Enter the value in the facet dropdown textbox
        Args:
            filtertype: Type of filter
            value: value to be entered
        """
        self.select_filter_dropdown(filtertype)
        self.__enter_facet_value(value)
        self.__admin_console.wait_for_completion()


class _ExportToForm(RModalDialog):
    """
     This class contains all the actions for 'Export To' form
    """

    @WebAction()
    def choose_selection_range(self, selection_range):
        """
        Method to choose selection range
        Args:
            selection_range (str)  - value to be selected
        """
        xpath = 'selected'
        if 'All' in selection_range:
            xpath = 'all'
        radio_button = self._driver.find_element(By.XPATH,
                                                 f"//div[contains(@class, 'Radio-cardContent')]/p[contains(text(), '{xpath}')]")
        radio_button.click()
        self._adminconsole_base.wait_for_completion()

    @WebAction()
    def choose_file_format(self, operation_type, file_format):
        """
        Method to choose selection range
        Args:
            operation_type (str) - CAB/ PST
             file_format (str)  - file format to be selected
        """
        self._driver.find_element(By.XPATH, f"//input[@id='exportType{operation_type}']").click()
        if operation_type == "CAB":
            radio_button = self._driver.find_element(By.XPATH, f"//input[@id='fileExtensionType{file_format}']")
            radio_button.click()
        self.click_submit()
        self._adminconsole_base.wait_for_completion()

    @WebAction()
    def enter_search_filter(self, value):
        """
        enter search keyword for filter
        Args:
                value (str)  - keyword to be searched for
        """
        search = self._driver.find_element(By.XPATH,
                                           "//div[@class='modal-content']//input[@id='searchInput']")
        search.clear()
        search.send_keys(value)
        search.send_keys(Keys.ENTER)

    @WebAction()
    def __click_plus_icon(self):
        """
        Clicks on the plus icon to create new export set
        """
        self._driver.find_element(By.XPATH,
                                  "//div[contains(@class ,'Dropdown-fieldBtn')]/button").click()
        self._adminconsole_base.wait_for_completion()

    @WebAction()
    def __enter_export_set_name(self, name):
        """
            Enters Export Set Name
        """
        search = self._driver.find_element(By.XPATH,
                                           "//input[@id='exportSetNameField']")
        search.clear()
        search.send_keys(name)
        self._driver.find_element(By.XPATH, "//button[@aria-label='Create']").click()
        self._adminconsole_base.wait_for_completion()

    @PageService()
    def create_new_export_set(self, name):
        """
        Create a new export set
        Args:
            name: Name of the export set to be created
        """
        self.__click_plus_icon()
        self.__enter_export_set_name(name)

    @WebAction()
    def __enter_export_name(self, name):
        """
            Enters export name
            Args:
                    name (str) : Name of the export
        """
        elem = self._driver.find_element(By.XPATH,
                                         "//input[@id='exportNameField']")
        elem.clear()
        elem.send_keys(name)
        self._adminconsole_base.wait_for_completion()

    @PageService()
    def enter_export_name(self, name):
        """
            Enters Export Name
            Args:
                    name (str) : Name of the export
        """
        if name is None:
            raise CVWebAutomationException('Export name is empty!')
        self.__enter_export_name(name)
