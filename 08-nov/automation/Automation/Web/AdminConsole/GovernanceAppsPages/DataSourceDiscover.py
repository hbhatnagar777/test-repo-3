from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Sensitive Data Analysis
Project Data Source discover page.


Classes:

    DataSourceDiscover() ---> SensitiveDataAnalysisProjectDetails() --->
    SensitiveDataAnalysis() ---> GovernanceApps() ---> object()


DataSourceDiscover  --  This class contains all the methods for action in
    Sensitive Data Analysis Project Data Source discover page and is inherited by
    other classes to perform GDPR related actions

    Functions:
    get_data_source_name() -- Returns data source name from the admin page
    get_total_files() -- Returns total number of files count
    get_sensitive_files() -- Returns total number of sensitive files count
    get_size() -- Returns total files size
    get_owners() -- Returns total number of owners for the files
    select_review() -- Selects the review link
    select_details() -- Clicks on the Details link
    start_data_collection_job() -- Starts the data collection job
    get_running_job_id()    --  Return running data collection job id
    select_active_jobs()    --  Selects active jobs tab
"""

from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.GovernanceAppsPages.\
    SensitiveDataAnalysisProjectDetails import SensitiveDataAnalysisProjectDetails

class DataSourceDiscover(SensitiveDataAnalysisProjectDetails):
    """
     This class contains all the methods for action in Sensitive Data Analysis
     Project Data Source discover page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        super().__init__(admin_console)
        self.__table = Rtable(admin_console)
        self.__admin_console = admin_console
        self.driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log

    @WebAction()
    def get_data_source_name(self):
        """
        Returns data source name from the admin page
        """
        data_source_name = str(self.driver.find_element(By.XPATH, '//*[@id="dataSourceDetailsPage"]//h1').text)
        self.log.info("data source name obtained is: %s" % data_source_name)
        return data_source_name

    @WebAction()
    def get_total_number_after_crawl(self):
        """
        Get total number of files after crawl
        :return: total_files
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.datasource.title'])
        total_files = self.__table.get_column_data('Documents')
        return total_files.pop(0)

    @PageService()
    def get_total_files(self):
        """
        Returns total number of files count
        """
        count = self.get_component_value("component_TotalFiles", "Total Files")
        self.log.info("total files count obtained is: %s" % count)
        return int(count)

    @PageService()
    def get_sensitive_files(self):
        """
        Returns total number of sensitive files count
        """
        count = self.get_component_value("component_SensitiveFiles", "Sensitive Files")
        self.log.info("sensitive files count obtained is: %s" % count)
        return int(count)

    @PageService()
    def get_size(self):
        """
        Returns total files size
        """
        size = self.get_component_value("component_Size", self.__admin_console.props['label.size'])
        self.log.info("size obtained is: %s" % size)
        return size

    @WebAction()
    def get_owners(self):
        """
        Returns total number of owners for the files
        """
        count = self.driver.find_element(By.XPATH, 
            '//*[@id="otherInfo"]//div[text()="Owners"]/following-sibling::p').text
        self.log.info("Owners obtained are: %s" % count)
        return int(count)

    @PageService()
    def select_review(self):
        """
        Selects the review link
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.review'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_details(self):
        """
        Clicks on the Details link
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.configuration'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_active_jobs(self):
        """Selects active jobs tab"""
        self.__admin_console.access_tab(self.__admin_console.props['label.activeJobs'])
        self.__admin_console.wait_for_completion()

    @WebAction()
    def start_data_collection_job(self, job_type='incremental'):
        """
        Clicks on the Start Data collection and run full
            or incremental crawl based on job type provided
        :param job_type    (str)   --  takes input of job type
                                        'full' or 'incremental'
        """
        self.driver.find_element(By.XPATH,
                                 "//div[text()='%s']" % self.__admin_console.props['label.datasource.startJob']).click()
        self.__admin_console.wait_for_completion()
        if job_type == 'full':
            self.driver.find_element(By.ID, "full").click()
            self.__admin_console.wait_for_completion()
        self.__admin_console.submit_form()
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_running_job_id(self):
        """
        Returns running Data collection Job id
        """
        self.select_active_jobs()
        table_data = self.__table.get_table_data()
        job_id = table_data['Job Id'][0]
        self.log.info('Data source Job ID obtained is: %s' % job_id)
        return job_id
