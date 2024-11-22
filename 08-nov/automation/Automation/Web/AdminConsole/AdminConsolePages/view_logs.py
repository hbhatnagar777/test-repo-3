# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
View logs page on the AdminConsole
Class:
    ViewLogs
Functions:
    __get_log_data()        -- web action which gets the data logged for the log lines visible in the page
    get_log_data()          -- gets the raw data logged for the log lines visible in the page
    get_log_lines()         -- gets the list of lines matching common log format
    get_log_lines_by_search() -- Processes the log data and returns lines that contains string
    get_logfile_names()     -- logfile names in the given log page
    pause_logs()            -- pauses the log from updating live
    resume_logs()           -- resumes the log to updating live
    word_wrap()             -- word wraps the log file
    change_to_log_window()  -- changes the window handle to the log window
    enable_toggle()         -- enables the toggle when toggle id is provided
    __enter_filter          -- enter the filter provided and return current value
    set_filters()           -- set provided filters
    set_markers()           -- set markers for given keywords
    browse_logs()           -- browse and access different log file
    get_log_props()         -- get log level, file size, versions
    set_log_level()         -- set log level, file size, versions

Class:
    ViewLogsPanel

Functions:
    search_logs()                -- Method to search specified log on view logs window
    view_logs_selectrow()        -- Select rows which contains given names in React Table
    add_filter()                 -- Method to add filter on view logs window
    table_columndata()           -- Method to add filter on specified column name
    access_log()                 -- Method to open log file by navigating through folders
"""
import re

from selenium.webdriver.common.by import By

from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.Components.page_container import PageContainer


class ViewLogs:
    """ Class for ViewLogs page """

    def __init__(self, admin_console):
        """ Initialize the base panel
        Args:
            admin_console: instance of AdminConsoleBase
        """
        self._driver = admin_console.driver
        self._admin_console = admin_console
        self.__filter_list = ['processId', 'jobId', 'threadId', 'includeString', 'excludeString']
        self.__toggle = Toggle(self._admin_console)
        self.__page_container = PageContainer(self._admin_console)
        self.__rpanelinfo = RPanelInfo(self._admin_console)

    @WebAction()
    def __get_log_data(self, job_view_logs, line_number=False):
        """web action which gets the data logged for the log present in the page (only visible lines)"""
        if job_view_logs:
            log_raw_text = self._driver.find_element(By.ID,
                                                     'jobLogsPage').text.strip().splitlines()
            if line_number:
                return {line_num: log for line_num, log in enumerate(log_raw_text)}
            return log_raw_text

        log_raw_text = self._driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'codemirror')]").text.splitlines()
        if not line_number:
            return log_raw_text[1::2]
        else:
            return {line_num: log for line_num, log in zip(log_raw_text[0::2], log_raw_text[1::2])}
        # TODO: find a way to get all the lines

    @PageService()
    def get_log_line_numbers(self):
        """
        gets the log lines along with their corresponding line number in dict format

        Returns:
            log_lines   (dict)  -   dict with line number as key and log line string as value
        """
        return self.__get_log_data(False, True)

    @PageService()
    def get_log_data(self, job_view_logs=False):
        """gets the raw data logged for the log present and only lines visible in the page
            job_view_logs (bool): True if job level view logs page is present
        """
        return self.__get_log_data(job_view_logs)

    @PageService()
    def get_log_lines(self, job_view_logs=False, log_line_pattern=None):
        """ Processes the log data visible and returns lines matching common log format
             job_view_logs (bool): True if job level view logs page is present
             log_line_pattern (str) : pattern used to fetch the log line
        """
        log_data = self.__get_log_data(job_view_logs)
        if not log_line_pattern:
            log_line_pattern = "^([+-]?[0-9]+)(( )|(    ))+([+-]?[0]?[xX]?[0-9A-Fa-f]+)(( )|(    ))+((1[0-2]|0?[" \
                               "1-9])/([12][0-9]|[3][01]|0?[1-9]))(( )|(    ))+(([0-2]?[0-9]):([0-5]?[0-9]):([" \
                               "0-5]?[0-9]))(( )|(    ))+([^     ]+)(( )|(    ))+(.*) "
        log_lines = [line for line in log_data if re.match(log_line_pattern, line)]
        return log_lines

    @PageService()
    def get_log_lines_by_search(self, job_view_logs=False, search_string=None, line_number=False):
        """
        Processes the log data and returns lines that contains string
        job_view_logs (bool): True if job level view logs page is present
        search_string (str) : used to fetch the log lines that contains the string
        line_number(bool)   : True if line numbers should be returned as well
        """
        if line_number:
            log_data = self.__get_log_data(job_view_logs=job_view_logs, line_number=line_number)
            log_lines = {num: line for num, line in log_data.items() if
                         re.search(search_string, line)}
            return log_lines

        log_data = self.__get_log_data(job_view_logs)
        log_lines = [line for line in log_data if re.search(search_string, line)]
        return log_lines

    @PageService()
    def get_logfile_names(self, job_view_logs=False):
        """Processes the list of log file names from the view logs page
            job_view_logs (bool): True if job level view logs page is present
        """
        log_data = self.__get_log_data(job_view_logs)
        logfile_names = [line.split(':')[1].strip() for line in log_data if re.match("File", line)]
        return logfile_names

    @PageService()
    def pause_logs(self):
        """Pauses the log file from updating live"""
        self.__page_container.access_page_action('Pause')

    @PageService()
    def resume_logs(self):
        """Resumes the log file to updating live"""
        self.__page_container.access_page_action('Resume')

    @PageService()
    def word_wrap(self):
        """word wraps the log file"""
        self.__page_container.access_page_action('Word wrap')

    @PageService()
    def clear_buffer(self):
        """
        Clears current log buffer
        """
        self.__page_container.access_page_action_from_dropdown('Clear buffer')

    @PageService()
    def load_complete_file(self):
        """
        Loads complete log file
        """
        self.__page_container.access_page_action_from_dropdown('Load complete file')

    @PageService()
    def change_to_log_window(self):
        """changes the window handle to the log window"""
        log_window = self._driver.window_handles
        self._driver.switch_to.window(log_window[1])
        self._admin_console.wait_for_completion()

    @PageService()
    def enable_toggle(self, toggle_name):
        """Page service to enable toggle
            toggle_name (str): attribute name of the toggle
        """
        if not self.__toggle.is_enabled(id=toggle_name):
            self.__toggle.enable(id=toggle_name)
            self._admin_console.wait_for_completion()

        if not self.__toggle.is_enabled(id=toggle_name):
            raise Exception('%s Toggle did not get enabled' % toggle_name)

    @WebAction()
    def __enter_filter(self, filter_name, filter_value=None, clear=False):
        """web action to enter the filter in the filter window
        filter_name (str) : name of the filter to be set
        filter_value(str) : value of the filter to be set
        """
        filter_input = self._driver.find_element(By.ID, filter_name)
        if clear:
            filter_input.send_keys(u'\ue009' + 'a' + u'\ue003')
        if filter_value is not None:
            filter_input.send_keys(str(filter_value))
        return filter_input.get_attribute('value').strip()

    @PageService()
    def set_filters(self, filter_dict, clear_existing=False):
        """
        Page Service to set filters in view_logs page
        Args:
            filter_dict: (dict) with the key as the filter name(ng-model) and the value as the filter value
                                Eg: {'processId': 100}
                                Accepted values: 'processId', 'jobId', 'threadId', 'includeString', 'excludeString'
            clear_existing: (bool) this is to clear existing filters
        """
        self.__page_container.access_page_action('Filter')
        self.enable_toggle('toggleEnableFilter')
        for name, value in filter_dict.items():
            self.__enter_filter(name, value, clear_existing)
        self.__rpanelinfo.click_button('Apply')

    @PageService()
    def set_markers(self, marker_words, clear_existing=False):
        """
        Page Service to set filters in view_logs page
        Args:
            marker_words: (list) list with marker keywords to mark uniquely with color
                            Eg: maximum 5 words can be marked at once ['keyword1','keyword2',...]
                                pass None as keyword if no changes intended for that marker position
                            if more than 5 given, only first 5 will be used
                            if less than 5 given, remaining last keywords will be left empty
            clear_existing: (bool) this is to clear all existing markers

        Returns:
            marker_colors: (dict) with marker keyword as key and its color as value
        """
        marker_colors = {}
        self.__page_container.access_page_action_from_dropdown('Markers')
        if clear_existing:
            self.__rpanelinfo.click_button('Clear all')
        for marker_number, marker_keyword in enumerate(marker_words, 1):
            if marker_keyword is not None:
                self.__enter_filter(f"markerKeyword{marker_number}", marker_keyword, True)
                marker_colors[marker_keyword] = self._admin_console.get_element_color(
                    f"//*[@id='markerKeyword{marker_number}']"
                )
        self.__rpanelinfo.click_button('Submit')
        return marker_colors

    @PageService()
    def browse_logs(self, log_path):
        """
        Browse log files from logs page to go to different log file

        Args:
            log_path (str)   -   full path name of log file to access
        """
        self.__page_container.access_page_action_from_dropdown('Browse logs')
        ViewLogsPanel(self._admin_console).access_log(log_path)
        self._admin_console.wait_for_completion()

    @WebAction()
    def __access_log_level(self, log_level=None, file_size=None, file_versions=None):
        """
        Sets new log level, file size and versions for current log file and returns the same
        """
        return (
            self.__enter_filter('debugLevel', log_level, log_level is not None),
            int(self.__enter_filter('fileSizeInMB', file_size, file_size is not None)),
            int(self.__enter_filter('fileVersions', file_versions, file_versions is not None)),
        )

    @PageService()
    def get_log_props(self):
        """
        Gets current log file's log level, file size, file versions set

        Returns:
            log_level   (str)   -   level of log (Ex: '1','2','5','default')
            file_size   (int)   -   size in MB
            file_versions (int) -   versions
        """
        self.__page_container.access_page_action('Log level')
        log_data = self.__access_log_level()
        self.__rpanelinfo.click_button('Cancel')
        return log_data

    @PageService()
    def set_log_level(self, log_level, file_size=None, file_versions=None):
        """
        Sets new log level, file size and file versions

        Args:
            log_level   (int/str)   -   log level to set (Ex: '1','2','default')
            file_size   (int/str)       -   size in MB
            file_versions (int/str)     -   number of versions
        """
        self.__page_container.access_page_action('Log level')
        self.__access_log_level(log_level, file_size, file_versions)
        self.__rpanelinfo.click_button('Submit')


class ViewLogsPanel(RModalDialog):
    """ Class for ViewLogs for all pages"""

    def __init__(self, admin_console):
        """ Initialize the base panel
        Args:
            admin_console: instance of AdminConsoleBase
        """
        super().__init__(admin_console)
        self._viewlog_table = Rtable(self._adminconsole_base, id="viewClientLogsGrid")

    @PageService()
    def searchlogs(self, logname):
        """ Method to search specified log on view logs window

              Args:
                  logname (str) --- Name of log to be searched on the window

              Returns:
                    None

              Raises:
                Exception:

                    -- if fails to search log file
        """
        self._viewlog_table.search_for(logname)

    @PageService()
    def view_logs_selectrow(self, names):
        """ Select rows which contains given names in React Table
        Args:
            names  (List)    --    entity name whose row has to be selected
        Returns:
            None

        Raises:
            Exception:
            -- if fails to select log file
        """
        self._viewlog_table.select_rows(names)

    @PageService()
    def add_filter(self, columnname, filter_item, criteria):
        """
        method to add filter on view logs window
        Arguments:
                filter_item   (str):      To filter values of a particular value
                columnname    (str):      To filter values on perticular column
                criteria      (enum):     enum value of Rfilter value
        Returns:
            None
        Raises:
            Exception:
                -- if fails to validate view logs operation
        """
        self._viewlog_table.apply_filter_over_column(columnname, filter_item, criteria)

    @PageService()
    def table_columndata(self, columnname):
        """
        method to add filter on specified column name
        Arguments:
                columnname    (str):  apply filter on specified columnname           
        Returns:
            tabledata (list):  List of values for the column.   
        Raises:
            Exception:
                -- if fails to apply filter on specified column
        """
        return self._viewlog_table.get_column_data(columnname, fetch_all=True)

    @PageService()
    def access_log(self, log_path):
        """
        View the specified log by navigating through folders
        Args:
            log_path (str) : Full path of the log to access (from LogFiles dir)
                            Ex: 'Web/Global/AuditTrail.log'
        """
        folders = log_path.split('/')[:-1]
        file_name = log_path.split('/')[-1]
        for folder_name in folders:
            self._viewlog_table.access_link(folder_name)
        self._viewlog_table.search_for(file_name)
        self._viewlog_table.select_rows([file_name], False)
        self.click_button_on_dialog(text='View')
