# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
job details page on the AdminConsole

Class:

    Jobs()

Functions:

    wait_label_text()                   -- waits for label text in overview to match given strings  
    get_status()                        -- returns status displayed
    get_progress()                      -- returns progress displayed

    get_general_details()               -- returns all details under general heading as dict
    get_progress_details()              -- returns all details under progress heading as dict
    get_association_details()           -- returns all details under associations heading as dict
    get_item_status()                   -- returns all details under item status heading as dict
    get_error_summary()                 -- returns error summary text

    get_all_details()                   -- returns all details under all headings as dict

    access_overview()                   -- access overview tab
    access_attempts()                   -- access attempts tab
    access_events()                     -- access events tab
    access_retention()                  -- access retention tab

    kill()                              -- kills job
    resume()                            -- resumes job
    suspend()                           -- suspends job
    resubmit()                          -- resubmits job
    restore()                           -- access restore
    view_logs()                         -- clicks view logs from more options
    send_logs()                         -- clicks send logs from more options
    view_failed_items()                 -- access view failed items
    job_completion()                    -- waits for job completion
    access_job_status_tab()             --  Access the status tab for a particular tab
    get_status_tab_stats()              -- Returns the stats of status tab under grid info component in job details page

    export_csv()                        -- downloads csv of attempts/events/retention table
    get_tabs_data()                     -- gets table data of attempts/events/retention table

"""
import time

from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService


class JobDetails:
    """ Class for the job details page """

    def __init__(self, admin_console):
        """
        Method to initiate Maintenance class

        Args:
            admin_console   (Object) :   admin_console object
        """
        self.__admin_console = admin_console
        self.log = self.__admin_console.log
        self.__driver = admin_console.driver
        self.__admin_console.load_properties(self)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console, id_value="jobDetailsPageId")
        self.__rtable = Rtable(self.__admin_console)
        self.__confirm_dialog = RModalDialog(self.__admin_console, xpath="//div[@class='confirm-dialog']")
        self.__warning_dialog = RModalDialog(self.__admin_console, title='Warning')

    def __handle_warning_dialog(self):
        """
        Function to handle the warning dialog that opens in SP37+

        # todo: add validation support, validate the warning message content
        # todo: add textbox input job description support
        """
        time.sleep(2)
        if self.__warning_dialog.is_dialog_present():
            self.__warning_dialog.click_submit(True)

    @WebAction()
    def __get_label_text(self, label):
        """Returns the text next to label in job details panel"""
        attempts = 5
        label_text = ''
        while attempts > 0:
            try:
                label_text = self.__driver.find_element(By.XPATH, 
                    f"//div[contains(text(),'{label}')]/following-sibling::div"
                ).text
                break
            except (StaleElementReferenceException, NoSuchElementException):
                time.sleep(1)
            attempts -= 1
        return label_text

    @WebAction()
    def wait_label_text(self, label, expected_texts, wait_time):
        """
        Waits till label text changes to any of the expected texts within wait time
        
        Args:
            label   (str)           -   the label who's corresponding value needs to be monitored for change
            expected_texts  (list)  -   list of values to match the label's text to
            wait_time   (int)       -   maximum time to wait before throwing timeout
        """
        WebDriverWait(self.__driver, wait_time).until(
            ec.any_of(
                *[
                    ec.text_to_be_present_in_element(
                          (By.XPATH, f"//div[contains(text(),'{label}')]/following-sibling::div"), expected_text
                    ) for expected_text in expected_texts
                ]
            ),
            message=f"Data point [{label}] failed to match among [{expected_texts}] within {wait_time} seconds"
        )

    @PageService()
    def get_status(self):
        """Returns status displayed"""
        return self.__get_label_text("Status")

    @PageService()
    def get_progress(self):
        """Returns progress displayed"""
        return self.__get_label_text("Progress")

    @PageService()
    def get_general_details(self):
        """Returns dict of all details under general panel"""
        return RPanelInfo(self.__admin_console, "General").get_details()

    @PageService()
    def get_progress_details(self):
        """Returns dict of all details under progress panel"""
        return RPanelInfo(self.__admin_console, "Progress").get_details()

    @PageService()
    def get_association_details(self, include_callout=False):
        """
        Returns dict of all details under associations panel
        
        Args:
            include_callout (bool)  -   whether to also return any callout's data
        
        Returns:
            association_dict    (dict)  -   all details from associations panel
        """
        details = RPanelInfo(self.__admin_console, "Associations").get_details()
        if 'Source client computer' in details:
            # ignore the callout's data returned by panel
            if not include_callout:
                details['Source client computer'] = details['Source client computer'].split(',')[0]
        return details

    @PageService()
    def get_item_status(self):
        """Returns dict of all details under item status panel"""
        return RPanelInfo(self.__admin_console, "Item status").get_details()

    @PageService()
    def get_error_summary(self):
        """Returns error summary text"""
        """Returns the text next to label in job details panel"""
        attempts = 5
        while attempts > 0:
            try:
                return self.__driver.find_element(By.XPATH, 
                    f"//span[contains(@class, 'MuiCardHeader-title') and text()='Error summary']"
                    f"/ancestor::div[contains(@class, 'MuiCard-root')]"
                    f"//div[contains(@class,'MuiCardContent-root')]"
                ).text
            except StaleElementReferenceException:
                pass
            attempts -= 1

    @PageService()
    def get_all_details(self):
        """Returns all visible details in one dict"""
        return self.__rpanel.get_details()

    @PageService()
    def access_overview(self):
        """
        Moves to overview tab
        """
        self.__admin_console.click_button_using_text("Overview")

    @PageService()
    def access_attempts(self):
        """
        Moves to attempts tab
        """
        self.__admin_console.click_button_using_text("Attempts")

    @PageService()
    def access_events(self):
        """
        Moves to events tab
        """
        self.__admin_console.click_button_using_text("Events")

    @PageService()
    def access_retention(self):
        """
        Moves to retention tab
        """
        self.__admin_console.click_button_using_text("Retention")

    @PageService()
    def kill(self, wait_time=0):
        """
        Kills job
        Args:
            wait_time (int) : waits for given seconds until status shows killed
        """
        self.__page_container.access_page_action("Kill")
        self.__handle_warning_dialog()
        if wait_time:
            self.wait_label_text("Status", ["Killed", "Committed", "Completed"], wait_time)

    @PageService()
    def resume(self, wait_time=0):
        """
        Resumes job
        Args:
            wait_time (int) : waits for given seconds until status shows running
        """
        self.__page_container.access_page_action("Resume")
        if wait_time:
            self.wait_label_text("Status", ["Running", "Completed"], wait_time)

    @PageService()
    def suspend(self, duration, wait_time=0):
        """
        Suspends the job
        Args:
            duration (str): duration to suspend job for (1 hour/2 hours/Forever)
            wait_time (int): waits for given seconds until status shows suspended
        """
        self.__page_container.access_page_action("Suspend", duration)
        self.__handle_warning_dialog()
        if wait_time:
            self.wait_label_text("Status", ["Suspended", "Committed", "Completed"], wait_time)

    @PageService()
    def resubmit(self):
        """
        Resubmits job and returns new job id
        """
        try:
            self.__page_container.access_page_action("Resubmit")
        except NoSuchElementException:
            # self.__admin_console.collapse_menus()
            raise Exception("Resubmit is missing!")
        self.__confirm_dialog.click_submit()
        _jobid = self.__admin_console.get_jobid_from_popup()
        self.__admin_console.wait_for_completion()
        return _jobid

    @PageService()
    def restore(self):
        """Clicks restore from job details page"""
        self.__page_container.access_page_action('Restore')

    @PageService()
    def view_logs(self):
        """Clicks view logs from job details page"""
        self.__page_container.access_page_action("View logs")

    @PageService()
    def send_logs(self):
        """Clicks send logs from job details page"""
        self.__page_container.access_page_action("Send logs")

    @PageService()
    def view_failed_items(self):
        """Clicks view failed items from job details page"""
        self.__page_container.access_page_action("View failed items")

    @PageService()
    def job_completion(self, timeout=30):
        """
        waits for job completion and returns a dict of the job details

        Args: 
                timeout(int)  -- Minutes after which Exception is raised
        returns:
                details(dict) -- job details

        """
        status = self.get_status()
        retry = 0
        while retry < timeout:
            self.log.info("Waiting for Job to complete")
            self.__admin_console.refresh_page()
            time.sleep(60)
            if self.get_status() == "Running":
                retry += 1
                continue
            else:
                break
        else:
            raise CVWebAutomationException("Retry exceeded. Job is still running")
        details = self.get_all_details()
        return details

    @PageService()
    def get_tabs_data(self, tab=None, columns=None, search=None, pages=1):
        """
        Gets all data from table in attempts/events/retention tabs

        Args:
            tab     (str)       -   the job details tab to get data from
                                    (Attempts/Events/Retention)
                                    default: Current Tab
            columns (str/list)  -   hidden columns to include
                                    'all' for all columns
                                    [col1, col2...] for multiple columns
                                    default: columns will not be modified
            search  (str)       -   keyword to search in table before fetching table data
                                    default: search will be cleared
            pages   (int/str)   -   number of pages to read jobs data from
                                    'all' for all pages (max limit of 20)
                                    default: first page only
        Returns:
            count       (int)          -   the total number of rows available
            tabs_data   (OrderedDict)  -   ordereddict with row_index key and value 
                                           row's data in top to bottom order
        """
        if tab:
            self.__admin_console.click_button_using_text(tab.title())
        return self.__rtable.get_rows_data(columns, search, pages=pages)

    @PageService()
    def export_csv(self, columns=None, search=None, pages='all'):
        """
        Clicks Export as CSV from the attempts/events/retention table

        Args:
            columns (list/str)  -   list of columns to make visible
                                    'all' for all columns
                                    default: columns will not be modified
            search  (str)       -   any search to apply if required
                                    default: search will be cleared
            pages   (int/str)   -   number of pages to download csv for
                                    'all' for all pages
                                    default: all pages

        Returns:
            files   (list)      -   list of filepaths of csv
        """
        return self.__rtable.export_csv(columns, search, pages)

    def access_job_status_tab(self):
        """
                    Access the status tab in job details page
        """
        self.__page_container.select_tab("Table status")

    @PageService()
    def get_status_tab_stats(self):
        """Returns the stats of status tab under grid info component in job details page"""

        return self.__rtable.get_grid_stats()
