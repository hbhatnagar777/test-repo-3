# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
jobs page on the AdminConsole

Class:

    Jobs()

Functions:

    reload_jobs()                               -- Reloads jobs table data
    if_job_exists()                             -- Check if a job with given job id is displayed on page 
                                                   as link
    if_table_job_exists()                       -- check if a job with given job id is displayed 
                                                   as row on table
    job_completion()                            -- Waits for job completion
    access_active_jobs()                        -- Shows all the active jobs in the jobs page
    access_job_history()                        -- Moves to job history tab
    access_admin_jobs()                         -- Moves to admin jobs tab
    view_jobs_of_last_24_hours()                -- Shows all the jobs that were run in the last 24 hrs
    view_jobs_of_last_3_months()                -- Shows all the jobs that were run in the last 3 months

    get_job_ids()                               -- Gets the jobs ids in the jobs page table
    access_job()                                -- Clicks job id link to go to job details
    access_job_by_id()                          -- Access job details directly by entering browser URL
    get_job_status()                            -- Read job status from Table for given job id

    job_details()                               -- Get all the details of the job after expanding panel
    kill_job()                                  -- Kills the job
    view_job_details()                          -- access job details from actions menu
    view_failed_items()                         -- View failed items page for the job.
    action_list_snaps()                         -- List snapshots for specific jobid.
    view_logs()                                 -- View logs for the job
    send_logs()                                 -- Send logs for the job
    suspend_job()                               -- Suspends the job
    resume_job()                                -- Resumes the job
    resubmit_job()                              -- Resubmits the job from job history page

    job_restore()                               -- Initiate subclient restore
    get_job_id_by_subclient()                   -- Get job id for subclient
    get_job_id_by_operation()                   -- Get job id for server
    get_latest_job_by_operation()               -- Gets the last run job with the given operation type
    show_admin_jobs()                           -- Same as access_admin_jobs, clicks admin jobs tab
    check_if_item_present_in_column()           -- Checks if a search item is present in the given column or not

    kill_selection()                            -- Kills selected jobs
    suspend_selection()                         -- Suspends selected job for given duration
    resume_selection()                          -- Resumes selected jobs
    multi_job_control()                         -- Performs multi-job operations from multi-job panel

    add_filter()                                -- Adds filter to job table
    clear_filter()                              -- Deletes filter from job table

    create_view()                               -- Creates a new view in jobs table
    select_view()                               -- Selects a view
    delete_view()                               -- Deletes a view

    wait_jobs_status()                          -- Waits for jobs status to match given strings
    get_jobs_data()                             -- Gets all job columns data from table
    wait_for_jobs()                             -- Waits for given jobs to show up in table
    sort_by_column()                            -- Sorts by given column and returns data
    export_jobs_csv()                           -- Downloads CSV for jobs table
    get_active_jobs_stats()                     -- Gets active jobs counts for active, suspended, Failed etc
"""

import time
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, \
    NoSuchElementException
from selenium.webdriver.common.by import By
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.Components.alert import Alert
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.Components.table import Rtable, Rfilter
from Web.AdminConsole.Components.panel import PanelInfo, ModalPanel, RPanelInfo, MultiJobPanel, RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.exceptions import CVWebAutomationException

JOB_ID_LABEL = "Job ID"
CLIENT_LABEL = "Server"


class Jobs:
    """ Class for the jobs page """

    text_input_columns = ["Instance", "Backup set", "Subclient", "Company", "Error description", "Error code",
                          "Backup copy status"]
    integer_input_columns = [JOB_ID_LABEL, "Total number of files", "Backup copy job ID"]
    choice_input_columns = ["Operation", "Elapsed", "Size", "Status", CLIENT_LABEL, "Agent type", "Backup type",
                            "Plan", "Server group"]
    time_input_columns = ["Start", "End", "Last update"]
    misc_columns = ["Progress"]
    all_columns = text_input_columns + integer_input_columns + choice_input_columns + time_input_columns + misc_columns

    def __init__(self, admin_console):
        """
        Method to initiate Maintenance class

        Args:
            admin_console   (Object) :   admin_console object
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__admin_console.load_properties(self)
        self.__navigator = self.__admin_console.navigator
        self.log = self.__admin_console.log
        self.__rtable = Rtable(self.__admin_console)
        self.__panel = PanelInfo(self.__admin_console)
        self.__modal_panel = ModalPanel(self.__admin_console)
        self.__confirm_dialog = RModalDialog(self.__admin_console, xpath="//div[@class='confirm']")
        self.__multijob_panel = MultiJobPanel(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__rdrop_down = RDropDown(self.__admin_console)
        self.__alert = Alert(self.__admin_console)
        self.__job_details = JobDetails(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console)
        self.__warning_dialog = RModalDialog(self.__admin_console, title='Warning')

    @WebAction()
    def __is_table_empty(self):
        """Checks if no jobs are available (table is empty)"""
        empty_msg = self.__admin_console.props['label.noResultsFound']
        return self.__admin_console.check_if_entity_exists("xpath", f"//td[text()='{empty_msg}']")

    @WebAction()
    def reload_jobs(self):
        """Reloads the jobs data table in active jobs page"""
        self.__rtable.reload_data()

    @WebAction()
    def if_job_exists(self, job_id, search=True, clear=False):
        """
        Method to check if a job with given job id is displayed on page as link

        Args:
            job_id (str/int) : Id of the job
            search (bool)    : performs job id search first if true
            clear (bool)     : clears the search bar after searching if true
        """
        job_id = str(job_id)
        if search:
            self.__rtable.search_for(job_id)
        job_existence = False
        if not self.__is_table_empty():
            attempts = 0
            while attempts < 3:
                try:
                    if self.__admin_console.check_if_entity_exists(
                            "xpath", f"//a[text()='{job_id}']"):
                        job_existence = True
                        break
                except StaleElementReferenceException:
                    pass
                finally:
                    attempts += 1
        if search and clear:
            self.__rtable.clear_search()
        return job_existence

    @WebAction()
    def if_table_job_exists(self, job_id, search=True, clear=False):
        """
                Method to check if a job with given job id is displayed as row on table

                Args:
                    job_id (str/int) : Id of the job
                    search (bool)    : performs job id search first if true
                    clear (bool)     : clears the search bar after searching if true
                """
        job_id = str(job_id)
        if search:
            self.__rtable.search_for(job_id)
        job_existence = job_id in self.__rtable.get_column_data(JOB_ID_LABEL)
        if search and clear:
            self.__rtable.clear_search()
        return job_existence

    @WebAction()
    def __select_jobs(self, job_ids="All"):
        """
        Selects jobs for further operation
        Args:
            job_ids     (list/str): list of job ids to select or selects all
        """
        if job_ids == "All":
            self.__rtable.select_all_rows()
        else:
            self.__rtable.select_rows(job_ids, False)

    @WebAction()
    def __clear_selection(self):
        """
        Clears job selection
        """
        try:
            self.__page_container.click_on_button_by_text(self.__admin_console.props['teer.grid.label.clearAll'])
        except NoSuchElementException:
            self.log.error("Couldn't find clear all button, ignoring")

    @PageService()
    def job_completion(self, job_id, retry=2, skip_job_details=False, timeout=3*60*60):
        """
        Waits for job completion
        :param job_id         (str/int)   --  ID of the job to wait for
        :param retry              (int)   --  the number of times the job has to be resumed if it goes into pending
        :param skip_job_details   (bool)  --  if true, skips getting job details
        :param timeout             (int)  --  How long to wait if job never completes (3 hrs default)
        """
        job_id = str(job_id)
        self.access_job_by_id(job_id)
        start = time.time()
        while True:
            if time.time() - start >= timeout:
                raise CVWebAutomationException("Timeout: Job took too long to complete")
            self.__admin_console.refresh_page()
            status = self.__job_details.get_status()
            if status == "Running":
                progress = self.__job_details.get_progress()
                if progress == '100%':
                    retry_progress = 0
                    while retry_progress < 18:
                        time.sleep(10)
                        status = self.__job_details.get_status()
                        if status == "Running":
                            retry_progress += 1
                            continue
                        else:
                            break
                    else:
                        raise CVWebAutomationException("Job Status is not getting updated correctly. "
                                                       "job progress says 100 % but status still shows as "
                                                       "running even 3 minutes of wait")
                else:
                    self.log.info("Waiting for Job %s to complete.", str(job_id))
                    self.__admin_console.refresh_page()
                    time.sleep(10)
                    continue
            if status in ["Completed", "Failed", "Completed w/ one or more errors",
                          "Pending", "Killed", "Failed to Start", "Committed"]:
                if status != "Pending":
                    break
                else:
                    if retry > 0:
                        self.__job_details.resume()
                        retry -= 1
                    else:
                        self.__job_details.kill()
                        time.sleep(30)
                    continue
        details = None
        if not skip_job_details:
            details = self.__job_details.get_all_details()
        self.__admin_console.wait_for_completion()
        return details

    @PageService()
    def access_active_jobs(self):
        """
        Shows all the active jobs in the jobs page
        """
        self.__page_container.select_tab(tab_id='activeJobsTab')

    @PageService()
    def access_job_history(self):
        """
        Clicks job history tab
        """
        self.__page_container.select_tab(tab_id='jobHistoryTab')

    @PageService()
    def access_admin_jobs(self):
        """
        Click admin jobs tab
        """
        self.__page_container.select_tab(tab_id='adminJobHistoryTab')

    @PageService()
    def view_jobs_of_last_24_hours(self):
        """
        Shows all the jobs that were run in the last 24 hrs
        """
        self.access_job_history()
        self.__rtable.select_view(self.__admin_console.props['viewname.jobs.finishedJobs1'])

    @PageService()
    def view_jobs_of_last_3_months(self):
        """
        Shows all the jobs that were run in the last 3 months
        """
        self.access_job_history()
        self.__rtable.select_view(self.__admin_console.props['viewname.jobs.finishedJobs90'])

    @PageService()
    def get_job_ids(self):
        """
        Gets the jobs ids in the jobs page table
        """
        return self.__rtable.get_column_data(JOB_ID_LABEL)

    @PageService()
    def access_job(self, job_id, search=True):
        """
        Access the job id link from table

        Args:
            job_id  (int/str)   -   id of job to click
            search  (bool)      -   apply job id search first if True
        """
        if search:
            self.__rtable.search_for(job_id)
        self.__rtable.access_link(str(job_id))

    @PageService()
    def access_job_by_id(self, job_id):
        """
        Access the job with given ID
        Args:
            job_id - id of the job to be selected

        Return:
            True    --  if the job opened successfully
        """
        # self.__table.access_link(job_id)
        base_url = self.__driver.current_url.split("commandcenter")[0]
        self.__driver.get(f'{base_url}commandcenter/#/jobs/{job_id}')
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_job_status(self, job_id):
        """Read job status from Jobs Page Table
        Args:
            job_id (str/int) - id of the job
        Returns:
            status (str) - job status if row is visible in page
            False       - if job id did not appear within wait time
        """
        job_id = str(job_id)
        job_ids = self.__rtable.get_column_data(JOB_ID_LABEL)
        stati = self.__rtable.get_column_data('Status')
        if job_id not in job_ids or len(job_ids) != len(stati):
            return False
        return stati[job_ids.index(job_id)]

    @PageService()
    def job_details(self):
        """Get all the details of the job after expanding panel"""
        """
        Ex: {
                'Status': 'Completed',
                'Data Written': '4.44 MB',
                'Job started by': 'Admin',
                'Backup type': 'Incremental',
                'Elapsed time': '2 min 8 sec',
                'iDataAgent': 'Virtual Server',
                'Software compression': 'Storage Policy',
                'Start time': 'Nov 18, 2015 00:23:57 AM',
                'Collection': 'NewCol',
                'Server': 'ADMINCONSOLECB',
                'Data transfered on network': '28.07 KB',
                'Instance': 'Hyper-V',
                'End time': 'Nov 18, 2015 00:26:14 AM',
                'Throughput': '3.67 MB/hr',
                'Last update time': 'Nov 18, 2015 00:26:14 AM',
                'Progress': '100%',
                'Type': 'Backup',
                'Source client computer': 'ADMINCONSOLECB',
                'Job started from': 'Interactive',
                'Size': '110.55 KB'
            }
        """
        return self.__job_details.get_all_details()

    def __handle_warning_dialog(self):
        """
        Function to handle the warning dialog that opens in SP37+

        # todo: add validation support, validate the warning message content
        # todo: add textbox input job description
        """
        time.sleep(2)
        if self.__warning_dialog.is_dialog_present():
            self.__warning_dialog.click_submit(True)

    @PageService()
    def kill_job(self, job_id, search=True, wait=0):
        """
        Kills the job
        Args:
            job_id (str): job id to kill
            search (bool): searches for job id if true
            wait (int): seconds to wait for status to change (will not wait if 0)
        """
        self.__rtable.access_action_item(job_id, self.__admin_console.props['Kill'], search=search)
        self.__handle_warning_dialog()
        if wait:
            self.wait_jobs_status([job_id], ["Killed", "Committed", "Completed"], wait)

    @PageService()
    def view_job_details(self, job_id, details=True, search=True):
        """
        access job details from actions menu
        Args:
            job_id (str): job id to access
            details (bool): returns dict of job details if true
            search (bool): searches for job id if true
        """
        self.__rtable.access_action_item(job_id, self.__admin_console.props['notification.jobDetails'], search=search)
        if not details:
            return
        self.__admin_console.wait_for_completion()
        return self.__rpanel.get_details()

    @PageService()
    def view_failed_items(self, job_id, search=True):
        """
        View failed items page for the job.
        Args:
            job_id(string): job id to access
            search(bool): searches for job id if true
        """
        self.__rtable.access_action_item(job_id, self.__admin_console.props['label.viewFailedItems'], search=search)

    @PageService()
    def action_list_snaps(self, job_id, search=True):
        """
        List snapshots for specific jobid.
        Args:
            job_id(string): job id to access
            search(bool): searches for job id if true
        """
        self.__rtable.access_action_item(job_id, self.__admin_console.props['label.listSnapshots'], search=search)

    @PageService()
    def view_logs(self, job_id, search=True):
        """
        View logs for the job
        Args:
            job_id(string): job id to access logs of
            search(bool): searches for job id if true
        """
        self.__rtable.access_action_item(job_id, self.__admin_console.props['label.viewLogs'], search=search)

    @PageService()
    def send_logs(self, job_id, search=True):
        """
        Send logs for the job
        Args:
            job_id(string): job id to access logs of
            search(bool): searches for job id if true
        """
        self.__rtable.access_action_item(job_id, self.__admin_console.props['action.sendLogs'], search=search)

    @PageService()
    def suspend_job(self, job_id, duration, wait=0):
        """
        Suspends the job
        Args:
            job_id (str): job id to suspend
            duration (str):    duration to suspend for (1 hour/2 hours/Forever)
            wait (int): seconds to wait for status to change (will not wait if 0)
        """
        self.__rtable.search_for(job_id)
        self.__rtable.hover_click_actions_sub_menu(job_id, self.__admin_console.props['Suspend'], duration)
        self.__handle_warning_dialog()
        if wait:
            self.wait_jobs_status([job_id], ["Suspended", "Committed", "Completed"], wait)

    @PageService()
    def resume_job(self, job_id, search=True, wait=0):
        """
        Resumes the job
        Args:
            job_id (str): job id to resume
            search (bool): search for job id first if true
            wait (int): seconds to wait for status to change (will not wait if 0)
        """
        self.__rtable.access_action_item(job_id, self.__admin_console.props['Resume'], search=search)
        if wait:
            self.wait_jobs_status([job_id], ["Running", "Completed"], wait)

    @PageService()
    def resubmit_job(self, job_id, search=True):
        """
        Resubmits the job from job history page
        Args:
            job_id (str): job id to resubmit
            search (bool): searches for job id if true
        Returns:
            job_id (int): job id of new resubmitted job
        """
        self.__rtable.access_action_item(job_id, self.__admin_console.props['Resubmit'], search=search)
        self.__confirm_dialog.click_submit(wait=False)
        _jobid = self.__alert.get_jobid_from_popup()
        self.__admin_console.wait_for_completion()
        return _jobid

    @PageService()
    def job_restore(self, job_id, search=True):
        """
        Initiate subclient restore

        Args:
            job_id   (string)   : job id which restore is to be initiated
            search (bool): searches for job id if true
        """
        self.__rtable.access_action_item(job_id, self.__admin_console.props['label.restore'], search=search)

    @PageService()
    def get_job_id_by_subclient(self, subclient):
        """
        Get job id for subclient
        Args:
            subclient               (str):     subclient name
        Returns:                    (int):     job id of sublcient
        """
        self.__rtable.apply_filter_over_column('Subclient', subclient)
        job_id = self.__rtable.get_column_data(JOB_ID_LABEL)[0]
        if not job_id:
            raise CVWebAutomationException("Job id not found for [%s] subclient" % subclient)
        return int(job_id)

    @PageService()
    def get_job_id_by_operation(self, operation, server=None):
        """
        Get job id for server
        Args:
            operation               (str):     operation name
            server                  (str):     server name
        Returns:                    (int):     job id of server
        """
        if server:
            try:
                self.__rtable.apply_filter_over_column(column_name=CLIENT_LABEL, filter_term=server,
                                                       criteria=Rfilter.equals)
                jobid_data = self.__rtable.get_column_data(column_name=JOB_ID_LABEL)
                operation_data = self.__rtable.get_column_data(column_name='Operation')
                index = operation_data.index(operation)
                jobid = int(jobid_data[index]) or None
            except ElementClickInterceptedException:
                self.log.info("Job not found in the table")
                jobid = None
            return jobid
        self.__rtable.clear_column_filter('Operation', '')
        self.__admin_console.wait_for_completion()
        self.__rtable.apply_filter_over_column_selection('Operation', operation)
        job_id = self.__rtable.get_column_data(JOB_ID_LABEL)[0]
        if not job_id:
            raise CVWebAutomationException("Job id not found for [%s] operation" % operation)
        return int(job_id)

    @PageService()
    def get_latest_job_by_operation(self, operation_type):
        """
        Gets the last run job with the given operation type

          Args:
              operation_type (str) -- The job operation name
          Returns:
              details (dict) -- Details of the job panel in key value pair
              None           -- If no relevant job ran in the last 24 hours

        """
        running_job_id = 0
        details_dict = {}
        try:
            running_job_id = self.get_job_id_by_operation(operation_type)
            details_dict = self.job_completion(job_id=running_job_id)
        except Exception:
            self.log.info(
                "Exception occurred or no active job of this type found.")

        if running_job_id == 0:
            try:
                self.log.info("Refreshing the page")
                self.__admin_console.refresh_page()
                self.view_jobs_of_last_24_hours()
                self.show_admin_jobs()
                running_job_id = self.get_job_id_by_operation(operation_type)
                details_dict = self.view_job_details(running_job_id)
            except:
                return None
        details_dict.update({"Id": running_job_id})
        return details_dict

    @PageService()
    def show_admin_jobs(self, show=True):
        """
        Show or hide admin jobs

        Args:
            show    (bool)  -    if False will hide admin jobs
        """
        if show:
            self.access_admin_jobs()
        else:
            self.access_job_history()

    @PageService()
    def check_if_item_present_in_column(self, column, value):
        """
        Checks if a search item is present in the given column or not
        Args:
            column    (str)  -    name of the column to searched in
            value     (ste)  -    string item to be searched in the column
        """
        rows = self.__rtable.get_column_data(column_name=column)
        if value in rows:
            return True
        else:
            return False

    @PageService()
    def kill_selection(self, job_ids=None, deselect=True, wait=0):
        """
        Kills selected jobs
        Args:
            job_ids (list): job ids to kill after selecting
                            will not perform selection if not given
                            will select all if "All"
            deselect(bool): will deselect after operation if True
            wait (int) : seconds to wait for all status to change (will not wait if 0)
        """
        if job_ids:
            self.__select_jobs(job_ids)
        self.__page_container.click_on_button_by_id("JOB_KILL")
        if wait:
            self.wait_jobs_status(job_ids, ["Killed", "Committed", "Completed"], wait)
        if deselect:
            self.__clear_selection()

    @PageService()
    def suspend_selection(self, duration, job_ids=None, deselect=True, wait=0):
        """
        Suspends selected job for given duration
        Args:
            duration (str): duration to suspend job for (1 hour/2 hours/Indefinitely)
            job_ids (list): job ids to suspend after selecting
                            will not perform selection if not given
                            will select all if "All"
            deselect(bool): will deselect after operation if True
            wait (int) : seconds to wait for all status to change (will not wait if 0)
        """
        duration_id_map = {
            self.__admin_console.props['SuspendHour'].format(1).lower(): 'JOB_SUSPEND_1_HOUR',
            self.__admin_console.props['SuspendHours'].format(2).lower(): 'JOB_SUSPEND_2_HOURS',
            self.__admin_console.props['SuspendForever'].lower(): 'JOB_SUSPEND_FOREVER'
        }
        if job_ids:
            self.__select_jobs(job_ids)
        self.__page_container.click_button("JOB_SUSPEND")
        self.__admin_console.click_by_id(duration_id_map[duration.lower()])  # this opens outside page container
        if wait:
            self.wait_jobs_status(job_ids, ["Suspended", "Committed", "Completed"], wait)
        if deselect:
            self.__clear_selection()

    @PageService()
    def resume_selection(self, job_ids=None, deselect=True, wait=0):
        """
        Resumes selected jobs
        Args:
            job_ids (list): job ids to kill after selecting
                            will not perform selection if not given
                            will select all if "All"
            deselect(bool): will deselect after operation if True
            wait (int) : seconds to wait for all status to change (will not wait if 0)
        """
        if job_ids:
            self.__select_jobs(job_ids)
        self.__page_container.click_on_button_by_id("JOB_RESUME")
        if wait:
            self.wait_jobs_status(job_ids, ["Running", "Completed"], wait)
        if deselect:
            self.__clear_selection()

    @PageService()
    def multi_job_control(self, operation, selection, entity_name=None, agent_name=None, selected_jobs=None):
        """
        Performs multi-job operations from multi-job control popup menu
        Args:
            operation       (str): operation to perform on job
                                    ("suspend","resume","kill")
            selection       (enum): selection criteria of jobs to perform operation on
                                    see MultiJobPanel.SelectionType Enum
            entity_name     (str):  name of entity if entity based job selection i.e.
                                    name of client/clientgroup/jobtype as seen in the menu
            agent_name      (str):  name of agent if 'jobs of agent' criteria is selected

            selected_jobs   (list): job ids to select if 'selected jobs' criteria is used

        """
        if self.__is_table_empty():
            raise CVWebAutomationException("Jobs table is empty, cannot perform multi job controls")
        if selection.value == MultiJobPanel.SelectionType.SELECTED.value:
            self.__clear_selection()
            if selected_jobs:
                self.__select_jobs(selected_jobs)
        self.__page_container.click_button("MULTI_JOB_CONTROL")
        self.__multijob_panel.config_operation(operation, selection, entity_name, agent_name)
        self.__multijob_panel.submit()
        try:
            self.__confirm_dialog.click_submit()
        except NoSuchElementException:
            pass

    @PageService()
    def add_filter(self, column, value=None, condition=None):
        """
        Adds filter to job table (active jobs or job history)
        Args:
            column      (str)   : column name to filter by as it appears in webpage
            value  (str/list)   : value or values (as list) to filter the column by
            condition   (enum)  : condition to filter by - if filtering from active jobs
                                ex: Rfilter.contains, Rfilter.not_equals
        """
        self.__rtable.apply_filter_over_column(column, value, condition)

    @PageService()
    def clear_filter(self, column, value=""):
        """
        Deletes filter from job table (active jobs or job history)
        Args:
            column      (str)   : column name in the filter as it appears in webpage
            value       (str)   : value of that column in the filter to delete
        """
        self.__rtable.clear_column_filter(column, value)

    @PageService()
    def create_view(self, view_name, rules, set_default=False):
        """
        Creates a new view in the Jobs page
        Args:
            view_name: Name of the view to be created
            rules: A dictionary of rules in the form of {<column-name>: <value>}
                    eg: {'Operation': 'Backup'}
                    rule conditions are left as default i.e. contains, equals..
            set_default: Sets the view as default
        """
        self.__rtable.create_view(view_name, rules, set_default)

    @PageService()
    def select_view(self, view_name="All"):
        """
        Selects a view
        Args:
            view_name: Name of the view to select
        """
        self.__rtable.select_view(view_name)

    @PageService()
    def delete_view(self, view_name):
        """
        Deletes a view
        Args:
            view_name: Name of the view to delete
        """
        self.select_view(view_name)
        self.__rtable.delete_view(view_name)

    @PageService()
    def wait_jobs_status(self, job_ids, status, wait_time=300):
        """
        Waits for given job ids status to match given statuses
        Args:
            job_ids (list): list of job ids to wait for
            status (list):  list of statuses to match to
            wait_time (int): maximum seconds to wait
        """
        self.__rtable.wait_column_values(job_ids, "Status", status, wait_time)

    @PageService()
    def wait_for_jobs(self, job_ids, timeout=60):
        """
        Waits for given job ids to show up in active jobs table

        Args:
            job_ids (list)  -   list of job ids to wait for
            timeout (int)   -   maximum time to wait before raising exception
        """
        self.__rtable.wait_for_rows(job_ids, timeout)

    @PageService()
    def get_jobs_data(self, columns=None, search=None, pages=1):
        """
        Gets all job column data from table

        Args:
            columns (list)     -    hidden columns to include for job data
                                    'all' for all columns
                                    [col1, col2...] for multiple columns
                                    default: columns will not be modified
            search  (str)      -    keyword to search in table before fetching table data
                                    default: search will be cleared
            pages   (int/str)  -    number of pages to read jobs data from
                                    'all' for all pages (max limit of 20)
                                    default: first page only

        Returns:
            count       (int)          -    the total number of jobs in table, 
                                            total rows across all pages
            jobs_data   (OrderedDict)  -    ordereddict with key job id 
                                            and column data as value 
                                            in the top to bottom order
                                            example: {
                                                'xyz': {
                                                    'client': 'abc', 
                                                    'subclient': 'def', ...
                                                    },
                                                '123': {...},
                                                ...
                                            }
        """
        return self.__rtable.get_rows_data(columns, search, pages=pages, id_column=JOB_ID_LABEL)

    @PageService()
    def get_active_jobs_stats(self) -> dict:
        """Method to get Active jobs stats such as count of Active, Suspended, Pending etc jobs

        Returns: (dict) active jobs stats
        Example :
        """
        kpi_elements = self.__driver.find_elements(By.XPATH, "//div[contains(@class, 'kpi-category')]")

        stats_dict = {}
        for kpi in kpi_elements:
            count = kpi.find_element(By.XPATH, ".//span[@class='kpi-category-count']").text
            label = kpi.find_element(By.XPATH, ".//span[@class='kpi-category-label']").text
            stats_dict[label] = count

        return stats_dict

    @PageService()
    def sort_by_column(self, column, data=False, search=None, ascending=True):
        """
        Sorts by given column and returns job ids list

        Args:
            column  (str)   -   name of column to sort
            data    (bool)  -   returns ordered job id and column's data also if True
            search  (str)   -   any search to apply
            ascending(bool) -   sort by ascending if True else descending

        Returns:
            job_ids (list)      -   list of job ids (top to bottom sequence) as visible in table
            data    (list)      -   list of column values (top to bottom sequence) that were sorted
        """
        self.__rtable.setup_table([column, JOB_ID_LABEL], search)
        self.__rtable.apply_sort_over_column(column, ascending)
        time.sleep(5)
        job_ids = []
        return_data = []
        if data:
            job_ids = self.__rtable.get_column_data(JOB_ID_LABEL)
            return_data = self.__rtable.get_column_data(column)
        return job_ids, return_data

    @PageService()
    def export_jobs_csv(self, columns=None, search=None, pages=1):
        """
        Clicks Export as CSV from the jobs table

        Args:
            columns (list/str)  -   list of columns to make visible
                                    'all' for all columns
                                    default: columns will not be modified
            search  (str)       -   any search to apply if required
                                    default: search will be cleared
            pages   (int/str)   -   number of pages to download csv of
                                    'all' for all pages
                                    default: all pages
        Returns:
            files   (list)   -   list of filepaths of csv
        """
        return self.__rtable.export_csv(columns, search, pages)

    @PageService()
    def get_successful_tables(self):
        """Get the number of Dynamics 365 tables completed which were successfully backed up from the job details
        page"""
        button_xpath = "//button/span[text()='Table status']"
        element = self.__driver.find_element(By.XPATH, button_xpath)
        element.click()
        self.__admin_console.wait_for_completion()
        successful_number_xpath = "//span[@class='kpi-category-label' and text()='Successful']/parent::span/span[" \
                                  "@class='kpi-category-count']"
        successful_number = None
        if self.__admin_console.check_if_entity_exists("xpath", successful_number_xpath):
            element = self.__driver.find_element(By.XPATH, successful_number_xpath)
            successful_number = int(element.text)
        return successful_number

    @PageService()
    def get_job_start_time(self, backup_job_details):
        """Returns the jobs start time, date , month and year"""
        date_time = backup_job_details["Start time"]
        day, year, start_time = date_time.split(", ")
        month, date = day.split()
        month_abbr = {
            "Jan": "january",
            "Feb": "february",
            "Mar": "march",
            "Apr": "april",
            "May": "may",
            "Jun": "june",
            "Jul": "july",
            "Aug": "august",
            "Sep": "september",
            "Oct": "october" ,
            "Nov": "november" ,
            "Dec": "december"
        }
        month = month_abbr[month]
        hour_min, period = start_time.split()
        hour_min = hour_min[:-3]
        start_time = hour_min + " " + period
        return year, month, date, start_time
