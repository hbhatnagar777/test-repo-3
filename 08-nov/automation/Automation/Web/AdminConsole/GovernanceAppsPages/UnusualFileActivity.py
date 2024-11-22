# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the operations that can be done on the unusual file activity page
and file data page

UnusualFileActivity: Class for performing unusual file activity operations

UnusualFileActivity
==============

    Functions:

    refresh_grid()                 --  Refreshes the grid
    search_for_client()            --  Searches for a client
    open_client_details()          --  Open the file activity page of the client
    get_file_count()               --  Gets the file count displayed for a client
    click_client_action()          --  Click on client's action
    delete_anomaly()               --  Deletes the anomalies
    clear_anomaly()                --  Clears the anomaly for a client
    start_threat_scan()            --  Starts the threat scan job
    start_data_restore()           --  Triggers a data restore job

FileData: Class for carrying out actions on the file data page

FileData
===============
    
    Functions:

    navigate_to_threat_scan()      --  Navigates to the threat scan page
    get_row_count()                --  Gets the total row count
    search_for_keyword()           --  Searches for a keyword
    download_file()                --  Searches for and downloads a file
    open_file_preview()            --  Searches for and opens the file's preview
    get_preview_details()          --  Gets all the file details available in the preview panel
    close_file_preview()           --  Closes the file preview panel
    mark_safe()                    --  Marks a file safe
    mark_corrupt()                 --  Marks a file corrupt
    get_total_files_count()        --  Gets the total no. of files
    get_suspicious_files_count()   --  Gets the total no. of suspicious files
    get_corrupt_files_count()      --  Gets the total no. of corrupt files
    toggle_file_details()          --  Expand or Collapse files in the suspicious files listing
    get_suspicious_file_info()     --  Get the file information displayed in the suspicious file listing

"""
import re
import dynamicindex.utils.constants as cs
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.Components.core import CalendarView, Checkbox
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import PanelInfo, RDropDown, RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction
from Web.WebConsole.Reports.Custom import viewer
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException

class UnusualFileActivity:
    """
     This class contains all the actions in unusual file activity page
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__dropdown = RDropDown(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__checkbox = Checkbox(self.__admin_console)

    @PageService()
    def refresh_grid(self):
        """
        Refreshes the grid
        """
        self.__table.reload_data()
    
    @PageService()
    def search_for_client(self, client_name):
        """
        Searches for a client

            Args:
                client_name (str)  - client name to be searched for

            Returns True/False based on the presence of the client
        """
        __flag = False
        self.__table.apply_filter_over_column("Name", client_name)
        if self.__admin_console.check_if_entity_exists("link", client_name):
            __flag = True
        return __flag

    @PageService()
    def open_client_details(self, client_name):
        """
        Open the file activity page of the client
            Args:
                client_name (str)  - client name
        """
        is_present = self.search_for_client(client_name)
        if not is_present:
            raise CVWebAutomationException("Client entry is not present")
        self._click_client_action(client_name, cs.DETAILS)

    @PageService()
    def get_file_count(self, client_name): 
        """
         Gets the file count displayed for a client
            Args:
                client_name (str)  - client name
        """
        is_present = self.search_for_client(client_name)
        if not is_present:
            raise CVWebAutomationException("Client entry is not present")
        file_count = self.__table.get_column_data("File count")
        return int(file_count[0])    
    
    @PageService()
    def click_client_action(self, client_name, action_name):
        """
        Clicks on a client's action item
            Args:
                client_name (str)  - client action item to be clicked
        """
        self._click_client_action(client_name, action_name)

    @WebAction()
    def _click_client_action(self, client_name, action_name):
        """
        Clicks on a client's action item
            Args:
                client_name (str)  - client action item to be clicked
        """
        self.__table.access_action_item(client_name, action_name)

    @WebAction()
    def _select_client_by_name(self, client_name):
        """
        Select client by client name
        Args:
               client_name (str)  - client name to be selected
        """
        self.__table.access_link(client_name)

    @PageService()
    def delete_anomaly(self, client_name, anomaly_list=None):
        """
        Deletes the anomalies

            Args:
                client_name         - client name
                anomaly_list (list)  - list of anomalies to delete

        """
        is_present = self.search_for_client(client_name)
        if not is_present:
            raise CVWebAutomationException("Client entry is not present")
        self.log.info("Deleting the anomaly(s)")
        self._click_client_action(client_name, cs.DELETE_ANOMALY)
        self.__dialog.click_submit()

    @PageService()
    def clear_anomaly(self, client_name, anomaly_list=None):
        """
        Clears the anomaly for a client

            Args:
                client_name         - client name
                anomaly_list (list)  - list of anomalies to delete

        """
        is_present = self.search_for_client(client_name)
        if is_present:
            self.log.info("Client exists, Deleting the anomaly(s)")
            self._click_client_action(client_name, cs.DELETE_ANOMALY)
            self.__dialog.click_submit() 
            self.__table.clear_column_filter("Name",client_name)
            self.__table.clear_search()
        else:    
            self.log.info("Client entry does not exist, no deletion required")
   

    @PageService()
    def start_threat_scan(self, client_name, index_server, anomaly_types=None, **kwargs):
        """
        Analyzes file data
        Args:
                client_name  (str)      - client name
                index_server (str)      - index server name
                anomaly_types (list)     - Types of anomalies to detect
                                          ["File data analysis", "Threat analysis"]

                Available kwargs
                state_date   (dict)     - start date, e.g.
                                         {'year': 2012, 'month': "March",'day': 20}
                start_time   (dict)     - start time 
                                         {'hour': 0, 'minute': 45, 'session': 'AM'}
                end_date     (dict)     - end date
                                         {'year': 2012, 'month': "March",'day': 20}
                end_time     (dict)     - end time
                                          {'hour': 1, 'minute': 45, 'session': 'AM'}
        """
        anomaly_list = [cs.FDA_ANOMALY, cs.TA_ANOMALY]
        checkbox = Checkbox(self.__admin_console)
        calendar = CalendarView(self.__admin_console)
        is_present = self.search_for_client(client_name)
        if is_present:
            self._click_client_action(client_name, cs.START_THREAT_SCAN)
        else:
            self.log.info("Client entry is not present. Adding a server")
            self.__admin_console.click_button_using_text("Add server")
            self.__admin_console.wait_for_completion()
            self.__dropdown.select_drop_down_values(
            values=[client_name], drop_down_id="serverDropdown")
        if "start_date" in kwargs:
            calendar.open_calendar("Start date")
            # Select start date
            self.log.info("Selecting the start date.")
            calendar.select_date(kwargs.get("start_date"))
            self.__admin_console.wait_for_completion()
            if "start_time" in kwargs:
                # Select start time
                self.log.info("Selecting the start time.")
                calendar.select_time(kwargs.get("start_time"))
            calendar.set_date()
        if "end_date" in kwargs:
            calendar.open_calendar("End date")
            # Select end date
            self.log.info("Selecting the end date.")
            calendar.select_date(kwargs.get("end_date"))
            self.__admin_console.wait_for_completion()
            if "end_time" in kwargs:
                # Select end time
                self.log.info("Selecting the end time.")
                calendar.select_time(kwargs.get("end_time"))
            calendar.set_date()
        self.__admin_console.wait_for_completion()
        self.__dropdown.select_drop_down_values(
            values=[index_server], drop_down_id="IndexServersDropdown")
        if anomaly_types:
           for element in anomaly_list:
               if element not in anomaly_types:
                   checkbox.uncheck(label=element)
        self.__admin_console.click_button_using_text("Analyze")
        self.__admin_console.wait_for_completion()
        if self.__dialog.check_if_button_exists("Analyze"):
            self.log.info("The job isnt triggered, retrying the analyze option")
            self.__dialog.click_button_on_dialog("Analyze")
            self.__admin_console.wait_for_completion()

    @PageService()
    def start_data_restore(self, client_name, destination_path, restore_original=False, overwrite=False):
        """
        Triggers a data restore job
        Args:
                client_name  (str)          - Client Name
                destination_path (str)      - Desination path to restore data
                restore_original (bool)     - Restore data to original folder
                overwrite (bool)            - Overwrite existing data in folder
        """
        self.__dropdown.select_drop_down_values(
            values=[client_name],drop_down_id="destinationServerList",drop_down_label="Destination")
        if not restore_original:
            self.__checkbox.uncheck(label="Restore to original folder")
        self.__dialog.fill_text_in_field("pathInputdestinationPathInput",destination_path)
        if overwrite:
             self.__checkbox.check(label="Unconditionally overwrite if it already exists")
        self.__dialog.click_submit()            

class ThreatScan:
    """
     This class contains all the actions in Threat scan page
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__table = Rtable(admin_console, id='FileDataAnomalyFilesGrid')
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__dialog = ModalDialog(self.__admin_console)
        self.__Rdialog = RModalDialog(self.__admin_console)
        self.__panelInfo = PanelInfo(self.__admin_console)
        self.__RpanelInfo = RPanelInfo(self.__admin_console)
        self.__web_adapter = WebConsoleAdapter(
            self.__admin_console, self.__admin_console.browser)
        self.__viewer_obj = viewer.CustomReportViewer(self.__web_adapter)
        self.__tsGrid_ID = "FileDataAnomalyFilesGrid"
        self.__tsInnerGrid_ID = 'FileDataAnomalyFileDetailsGrid'
        self.__rtable = Rtable(self.__admin_console, id=self.__tsGrid_ID)
        self._rInnerTable = Rtable(self.__admin_console, id=self.__tsInnerGrid_ID)

    @PageService()
    def navigate_to_threat_scan(self):
        """
        Navigates to the file data page
        """
        self.__admin_console.select_main_bar_tab_item("Threat scan")

    @PageService()
    def get_row_count(self, search_keyword=None):
        """
        Gets the total row count
            Args:
                Optional
                search_keyword (str)  - keyword to be searched for
        Returns:
               (int) - No. of rows in the table
        """
        return self.__table.get_total_rows_count(search_keyword)

    @WebAction()
    def scroll_into_view_search(self):
        """
        Scrolls into view the search element
        """
        search_input_xp = "//div[contains(@id,'FileDataAnomalyFilesGrid')]//input[contains(@data-testid,'grid-search-input')]"
        self.__admin_console.scroll_into_view(search_input_xp)

    @PageService()
    def search_for_keyword(self, keyword):
        """
        Searches for a keyword
            Args:
                keyword (str)  - search keyword

            Returns True/False based on the presence of the result
        """
        self.scroll_into_view_search()
        self.__table.search_for(keyword)
    
    @PageService()
    def download_file(self, search_keyword, file_name):
        """
        Searches for and downloads a file
            Args:
                search_keyword    (str)  - the search string
                file_name         (str)  - file name
        """
        self.open_file_preview(search_keyword, file_name)
        self.__panelInfo.click_button_on_tile(cs.DOWNLOAD)
        self.__admin_console.wait_for_completion()
    
    @PageService()
    def open_file_preview(self, search_keyword, file_name):
        """
        Searches for and opens the file's preview
            Args:
                search_keyword    (str)  - the search string
                file_name         (str)  - file name
        """
        self.search_for_keyword(search_keyword)
        self.__admin_console.select_hyperlink(file_name)

    @PageService()
    def get_preview_details(self):
        """
        Gets all the file details available in the preview panel

        Returns Dict of file details displayed in the preview panel
        """
        return(self.__RpanelInfo.get_details())
    
    @PageService()
    def close_file_preview(self):
        """
        Closes the file preview panel
        """
        self.__Rdialog.click_close()       

    @PageService()
    def toggle_file_details(self, file_name, expand=True):
        """
        Expand or Collapse files in the suspicious files listing
        Args:
            file_name (str) : suspicious file name on the row to be expanded
            expand (bool) : Whether to expand or collapse
        """
        self.__rtable.expand_row(file_name, expand)    

    @PageService()
    def get_suspicious_file_info(self, file_name,file_info_field):
        """
        Get the file information displayed in the suspicious file listing
        """
        self.toggle_file_details(file_name)
        return self._rInnerTable.get_column_data(file_info_field)   
    
    @PageService()
    def mark_safe(self, search_keyword, file_name):
        """
        Marks a file safe
            Args:
                search_keyword    (str)  - the search string
                file_name         (str)  - file name
        """
        self.open_file_preview(search_keyword, file_name)
        self.__admin_console.wait_for_completion()
        self.__panelInfo.click_button_on_tile(cs.MARK_SAFE)
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def mark_corrupt(self, search_keyword, file_name):
        """
        Marks a file corrupt
            Args:
                search_keyword    (str)  - the search string
                file_name         (str)  - file name
        """
        self.open_file_preview(search_keyword, file_name)
        self.__panelInfo.click_button_on_tile(cs.MARK_CORRUPT)
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_total_files_count(self):
        """
        Gets the total no. of files
            Returns:
               (int) - No. of total files
        """
        xpath = "//div[@id='component_Hits1677280298570']"
        total_docs = self.__admin_console.driver.find_element(By.XPATH, xpath).text
        total_docs = re.search(r'\d+',total_docs).group()
        return int(total_docs)

    @PageService()
    def get_suspicious_files_count(self):
        """
        Gets the total no. of suspicious files
            Returns:
               (int) - No. of suspicious files
        """
        suspicious_docs = viewer.HitsComponent("Hits1677280512143")
        self.__viewer_obj.associate_component(suspicious_docs, comp_id="Hits1677280512143")
        return int(suspicious_docs.get_value())

    @PageService()
    def get_corrupt_files_count(self):
        """
        Gets the total no. of corrupt files
            Returns:
               (int) - No. of corrupt files
        """
        corrupt_docs = viewer.HitsComponent("Hits1677281567546")
        self.__viewer_obj.associate_component(corrupt_docs, comp_id="Hits1677281567546")
        text = corrupt_docs.get_value()
        if text == "N/A":
            count = 0
        else:
            count = int(text)
        return count

    @WebAction()
    def _click_file_action(self, file_name_keyword, action_name):
        """
        Clicks on a file's action item
            Args:
                file_name_keyword (str)  - file item to be clicked
                action_name       (str)  - action name to be selected  
        """
        try:
            self.__table.access_action_item(file_name_keyword, action_name)
            self.log.info(f"{action_name} action completed successfully")
        except Exception as exception:
            if isinstance(exception, ElementClickInterceptedException):
                return("The Selected Action is Disabled")
            else:
                raise CVWebAutomationException("The selected action failed")
    
    @PageService()
    def select_recover_files(self):
        """
        Select recover files option

        """  
        self.__admin_console.click_button_using_text(cs.RECOVER_FILES)
        self.__admin_console.wait_for_completion()
