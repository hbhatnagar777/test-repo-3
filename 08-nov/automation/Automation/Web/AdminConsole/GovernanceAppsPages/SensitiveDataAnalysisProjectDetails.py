from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Sensitive Data Analysis
Project details page.


Classes:

    SensitiveDataAnalysisProjectDetails() ---> SensitiveDataAnalysis() --->
    GovernanceApps() ---> object()


SensitiveDataAnalysisProjectDetails  --  This class contains all the methods for
    action in Sensitive Data Analysis Project details page and is inherited by other
    classes to perform GDPR related actions

    Functions:

    select_add_data_source()          --  Selects the data source type to be added
    get_data_sources()     -       -- Returns all the data sources
    wait_for_data_source_status_completion() -- Waits for the data source scan status
                                                                            completion
    select_data_source() -- Selects a given data source
    select_overview()                    -- Clicks on the Overview link
    select_details()                    -- Clicks on the Details link
    data_source_exists()    --  Checks if a given datasource with provided name exists
    delete_data_source()    --  deletes a datasource with given name
    select_review()         --  Go to the datasource review page
    select_data_source_panel()  --  Clicks on the Data source link
    start_data_collection()     --  Starts the data collection job
"""

import re
import time

from Web.AdminConsole.GovernanceAppsPages.SensitiveDataAnalysis import SensitiveDataAnalysis
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog


class SensitiveDataAnalysisProjectDetails(SensitiveDataAnalysis):
    """
     This class contains all the methods for action in Sensitive Data Analysis
     Project details page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__table = Rtable(self.__admin_console)
        self.__panelinfo = RPanelInfo(self.__admin_console)
        self.modal_dialog = RModalDialog(self.__admin_console)

    @WebAction()
    def select_add_data_source(self, data_source_type='File system'):
        """
            Selects the File system data source to be addedpylint

            Args:
                data_source_type (str) - Type of the data source to be selected
                Values:
                    Default - "File system"

            Raise:
                Exception if invalid data source type provided
        """
        self.select_data_source_panel()
        data_source_list = [
            self.__admin_console.props['label.datasource.file'],
            self.__admin_console.props['label.datasource.onedrive'],
            self.__admin_console.props['label.datasource.exchange'],
            self.__admin_console.props['label.datasource.sharepoint'],
            self.__admin_console.props['label.datasource.database'],
            self.__admin_console.props['label.datasource.gmail'],
            self.__admin_console.props['label.datasource.googledrive']
        ]
        self.log.info('Clicking on Add button')
        self.__admin_console.click_button_using_text(self.__admin_console.props['label.add'])
        self.log.info('Selecting %s data source option' % data_source_type)
        if data_source_type in data_source_list:
            self.driver.find_element(
                By.XPATH, f"//li[@role='menuitem']/span[contains(text(),'{data_source_type}')]").click()
        else:
            raise Exception("Invalid data source type: %s" % data_source_type)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def get_number_files(self, data_source_name):
        """
                Returns number of files in data sources

                    Return:
                        Number of files

                """
        number_files = str(
            self.driver.find_element(By.XPATH,
                                     "//a[text()='%s']/../../div[4]/span" %
                                     data_source_name).text)
        return number_files

    @WebAction()
    def get_data_sources(self):
        """
        Returns all the list of data sources

            Return:
                List of data sources

        """
        self.select_data_source_panel()
        data_sources_list = []
        rows = self.driver.find_elements(By.XPATH,
                                         "//div[@class='ui-grid-canvas']/div")
        for row_id in range(1, len(rows) + 1):
            data_sources_list.append(str(self.driver.find_element(By.XPATH, "//div[@class='ui-grid-canvas']\
                                         /div[%d]/div/div[1]/a" % row_id).text))
        self.log.info('List of data source names obtained are: %s'
                      % data_sources_list)
        return data_sources_list

    @WebAction()
    def wait_for_data_source_status_completion(
            self, data_source_name, timeout=30):
        """
        Waits for the data source scan status completion

            Args:
                data_source_name (str)  - Name of the data source
                timeout     (int)   --  minutes
                    default: 30

            Returns:
                bool  - boolean specifying if the data source scan had finished or not
                    True    -   if the data source scan had finished successfully

                    False   -   if the data source scan was not completed within the
                                                                            timeout

        """
        status = False
        start_time = int(time.time())
        current_time = start_time
        completion_time = start_time + timeout * 60
        url = self.__admin_console.current_url()
        job_id = 0
        if 'analytics' in url:
            self.__admin_console.access_tab("Active jobs")
            data = self.__table.get_column_data('Job ID')
            job_id = data[0] if len(data) > 0 else 0
        else:
            self.select_data_source_panel()
        while completion_time > current_time:
            self.log.info("Refreshing the page")
            self.driver.refresh()
            self.__admin_console.wait_for_completion()
            self.log.info(
                'Obtaining the data source status of: %s' % data_source_name)
            num_try = 0
            while num_try < 10:
                try:
                    data = self.__table.get_column_data('Status')
                    current_status = data[0] if len(data) > 0 else ""
                    self.log.info('Data source status obtained is: %s' %current_status)
                    if len(current_status) == 0:
                        self.__admin_console.access_tab("Job history")
                        if job_id == 0:
                            current_status = self.__table.get_column_data('Status')[0]
                        else:
                            table_data = self.__table.get_table_data()
                            index = table_data['Job ID'].index(job_id)
                            current_status = table_data('Status')[index]

                    if re.search("FINISHED", current_status, re.IGNORECASE):
                        status = True
                        break
                    elif re.search(
                            self.__admin_console.props['label.taskDetail.status.Completed'],
                            current_status, re.IGNORECASE):
                        status = True
                        break
                    elif re.search("COMPLETED WITH ERRORS", current_status, re.IGNORECASE):
                        status = True
                        break
                    self.log.info("Refreshing the page")
                    self.driver.refresh()
                    self.__admin_console.wait_for_completion()
                    time.sleep(30)
                except Exception:
                    num_try += 1
            if status:
                break
            current_time = int(time.time())
        return status

    @WebAction()
    def select_data_source(self, data_source_name, refresh=True, refresh_count=0):
        """
        Selects the given data source

            Args:
                data_source_name  - Data Source name

            Raise:
                Exception if data source not found
        """
        self.select_data_source_panel()
        self.log.info("Selecting Data Source: %s" % data_source_name)
        self.driver.find_element(By.XPATH, "//a[text()='%s']" % data_source_name).click()
        self.__admin_console.wait_for_completion()
        if refresh:
            for count in range(refresh_count):
                self.log.info("Refreshing the page %s/%s" % (count, refresh_count))
                self.driver.refresh()
                self.__admin_console.wait_for_completion()
                time.sleep(30)

    @WebAction()
    def select_overview(self):
        """
        Clicks on the Overview link
        """
        self.driver.find_element(By.XPATH,
                                 "//a[contains(@class,'bc-item') and text()='%s']"
                                 % self.__admin_console.props['label.overview']).click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_data_source_panel(self):
        """
                Clicks on the Data source link
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.datasource.title'])
        self.__admin_console.wait_for_completion()

    @WebAction()
    def select_details(self):
        """
        Clicks on the Details link
        """
        self.driver.find_element(By.XPATH,
                                 "//a[contains(@class,'bc-item') and text()='%s']"
                                 % self.__admin_console.props['label.details']).click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def data_source_exists(self, data_source_name):
        """
        Checks if a given datasource exists

            Args:
                data_source_name (str)  - Datasource name to be checked for

            Returns True/False based on the presence of the datasource
        """
        self.select_data_source_panel()
        return self.__table.is_entity_present_in_column(
            self.__admin_console.props['label.name'], data_source_name)

    @PageService()
    def delete_data_source(self, data_source_name):
        """
        Deletes a Datasource

            Args:
                data_source_name (str)  - Datasource name to be deleted

            Returns
                True if datasource deletion is successful
                False if datasource deletion fails
        """
        wait_time = 10
        self.select_data_source_panel()
        self.__table.access_action_item(
            data_source_name, self.__admin_console.props['label.delete'])
        self.modal_dialog.click_submit()
        time.sleep(wait_time)
        return not self.data_source_exists(data_source_name)

    @PageService()
    def select_review(self, data_source_name):
        """Go to the datasource review page"""
        self.__table.access_action_item(
            data_source_name, self.__admin_console.props['label.review'])

    @PageService()
    def start_data_collection(self, data_source_name, type='incremental'):
        """Start the data collection job"""
        self.__table.access_action_item(
            data_source_name, self.__admin_console.props['label.datasource.startJob'])
        if type == 'full':
            self.__admin_console.select_radio(id='full')
        self.__admin_console.click_button(
            self.__admin_console.props['label.datasource.startJob'])
        self.__admin_console.wait_for_completion()
