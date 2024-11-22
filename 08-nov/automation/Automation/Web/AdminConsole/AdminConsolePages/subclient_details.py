# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods for all the common actions that can be done of the Subclient Details
page.


Classes:

    SubclientDetails()


SubclientDetails  --  This class contains all the methods for action in a particular
                        subclient's page common to all iDA's

    Functions:

    edit_storage_target() -- Edit the storage of a collection. Changes the library and retention

    add_sc_schedule()     -- Adds a backup schedule for the collection with the specified frequency

    edit_plan()           -- Edits The plan

    backup_now()          -- Starts a backup job for the collection

    restore()           --  Opens the select restore page

    backup_jobs()       -- Lists all the backup jobs of the collection

    content_info()      -- Returns the list of all the VMs and rules in the collection content

    schedule_info()       -- Displays all the schedules associated with the subclient

    delete_schedule()   -- Deletes a schedule with the given name

"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.panel import Backup
from Web.Common.page_object import (PageService, WebAction)


class SubclientDetails:
    """
    This class contains all the methods for action in any iDA's subclient's page
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console

    @WebAction()
    def _add_one_time_schedule(
            self,
            schedule_options=None
    ):
        """
        To add or edit one time schedule using the given options

        Args:
            schedule_options (dict)     -- one time schedule options to be selected

        Returns:
            None

        Raises:
            Exception

                if input argument is missing

        Usage:
            * sample dict for schedule options

                schedule_options:
                {
                    'year': '2017',
                    'month': 'december',
                    'date': '31',
                    'hours': '09',
                    'mins': '19',
                    'session': 'AM'
                }

            * If schedule options are None, default values if any, are chosen

        """
        # To select the radio button
        self._admin_console.select_radio('One time')
        if schedule_options:
            # To edit the date and time
            self._admin_console.date_picker(schedule_options)

    @WebAction()
    def _add_automatic_schedule(
            self,
            schedule_options=None
    ):
        """
        To add or edit automatic schedule using the given options

        Args:
            schedule_options (dict)     -- automatic schedule options to be selected

        Returns:
            None

        Raises:
            Exception

                if input argument is missing

        Usage:
            * sample dict for schedule options

                schedule_options:
                {
                    'frequency': 'Automatic'
                    'min_job_interval_hrs': '24',
                    'min_job_interval_mins': '30',
                    'max_job_interval_hrs': '72',
                    'max_job_interval_mins': '45',
                    'min_sync_interval_hrs': '1',
                    'min_sync_interval_mins': '30',
                    'ignore_operation_window': True,
                    'only_wired': True,
                    'min_bandwidth': True,
                    'bandwidth': '128',
                    'use_specific_network': True,
                    'specific_network_ip_address': '0.0.0.0',
                    'specific_network': '24',
                    'start_on_ac': True,
                    'stop_task': True,
                    'prevent_sleep': True,
                    'cpu_utilization_below': True,
                    'cpu_below_threshold': '10',
                    'start_only_files_bkp': True
                }

        **Note** For Automatic there is NO default value

        """
        # To select the radio button
        self._admin_console.select_radio('Automatic')
        # To fill the Min job interval
        if schedule_options.get('min_job_interval_hrs') and schedule_options.get(
                'min_job_interval_mins'):

            self._admin_console.fill_form_by_id("minBackupIntervalHours",
                                 schedule_options['min_job_interval_hrs'])

            self._admin_console.fill_form_by_id("minBackupIntervalMinutes",
                                 schedule_options['min_job_interval_mins'])

        # To fill the Max job interval
        if schedule_options.get('max_job_interval_hrs') and schedule_options.get(
                'max_job_interval_mins'):

            self._admin_console.fill_form_by_id("maxBackupIntervalHours",
                                 schedule_options['max_job_interval_hrs'])

            self._admin_console.fill_form_by_id("maxBackupIntervalMinutes",
                                 schedule_options['max_job_interval_mins'])

        # To fill the Job Interval
        # To fill the min sync interval
        if schedule_options.get('min_sync_interval_hrs') and \
                schedule_options.get('min_sync_interval_mins'):
            self._admin_console.fill_form_by_id("minSyncIntervalHours",
                                 schedule_options['min_sync_interval_hrs'])
            self._admin_console.fill_form_by_id("minSyncIntervalMinutes",
                                 schedule_options['min_sync_interval_mins'])

            # To select the ignore operation checkbox
            if schedule_options.get('ignore_operation_window'):
                self._admin_console.checkbox_select("ignoreAtMaxInterval")

        # To fill the Network Management
        # To select the wired network checkbox
        if schedule_options.get('only_wired'):
            self._admin_console.checkbox_select("onlyWiredWork")

        # To select the min network bandwidth checkbox
        if schedule_options.get('min_bandwidth'):
            self._admin_console.checkbox_select("minBandwidth")
            if schedule_options.get('bandwidth'):
                self._admin_console.fill_form_by_id("bandwidth", schedule_options['bandwidth'])
            else:
                raise Exception('Bandwidth argument missing for Automatic schedule')

        # To select the specific network checkbox
        if schedule_options.get('use_specific_network'):
            self._admin_console.checkbox_select("specificNetwork")
            if schedule_options.get('specific_network_ip_address') and \
                    schedule_options.get('specific_network'):
                # To fill the IP address
                self._admin_console.fill_form_by_id("specificNetworkIpAddress",
                                     schedule_options['specific_network_ip_address'])

                # To fill the port
                self._admin_console.driver.find_element(By.XPATH, 
                    "//input[@id='specificNetwork'and @type='number']").send_keys(
                        schedule_options['specific_network'])
            else:
                raise Exception("Specific network arguments missing in automatic schedule")

        # Power Management
        # To select A/C power checkbox
        if schedule_options.get('start_on_ac'):
            self._admin_console.checkbox_select("startOnAC")

        # To select the stop task checkbox
        if schedule_options.get('stop_task'):
            self._admin_console.checkbox_select("StopTask")

        # To select the prevent sleep checkbox
        if schedule_options.get('prevent_sleep'):
            self._admin_console.checkbox_select("preventSleep")

        # Resource Utilization
        if schedule_options.get('cpu_utilization_below'):
            self._admin_console.checkbox_select("cpuBelowThresholdEnabled")
            if schedule_options.get('cpu_below_threshold'):
                self._admin_console.fill_form_by_id("cpuBelowThreshold", schedule_options['cpu_below_threshold'])
            else:
                raise Exception('CPU threshold missing in automatic schedule')

        # File Management
        if schedule_options.get('start_only_files_bkp'):
            self._admin_console.checkbox_select("startOnlyFileBackUp")

    @WebAction()
    def _add_daily_schedule(
            self,
            schedule_options=None
    ):
        """
        To add or edit daily schedule using the given options

        Args:
            schedule_options (dict)     -- daily schedule options to be selected

        Returns:
            None

        Raises:
            Exception

                if input argument is missing

        Usage:
            * sample dict for schedule options

                schedule_options:
                {
                    'repeatDay': '1',
                }

            * If schedule options are None, default values if any, are chosen

        """
        # To select the radio button
        self._admin_console.select_radio('Daily')

        # To fill the repeat every day field
        if schedule_options.get('repeatDay'):
            self._admin_console.fill_form_by_id("dayFrequency", schedule_options.get('repeatDay'))

    @PageService()
    def edit_storage_target(self, storage_policy):
        """
        Edit the storage target of a subclient

        Args:
            storage_policy  (str):   the storage policy to be selected

        Raises:
            Exception:
                if there is no option to change the storage target

        """
        if self._admin_console.check_if_entity_exists(
                "xpath", "//cv-tile-component[@data-title='Storage targets']"
                         "//a[contains(text(),'Edit')]"):
            self._admin_console.tile_select_hyperlink("Storage targets", "Edit")
            self._admin_console.select_value_from_dropdown("dataStoragePolicy", storage_policy)
            self._admin_console.submit_form()
            self._admin_console.check_error_message()
        else:
            raise Exception("There is no option to edit the storage target of the collection")

    @WebAction()
    def edit_plan(self, plan):
        """
        Edits the plan

        Args:
            plan    (str):   the name of the plan to select

        Raises:
              Exception:
                if there is an error with selecting a plan

        """
        if self._admin_console.check_if_entity_exists("xpath", "//cv-tile-component[@data-ac-id="
                                                "'label_profile-profiles']//a["
                                                "contains(text(),'Edit')]"):
            self._admin_console.tile_select_hyperlink("Plan", "Edit")
            self._admin_console.cv_single_select("Plan", plan)
            self._admin_console.submit_form()
        else:
            raise Exception("There is no option to edit the plan")

    @PageService()
    def backup_now(self, bkp_type):
        """
        Starts a backup job for the collection

        Args:

            bkp_type (BackupType): the backup level, among the type in Backup.BackupType enum

        Returns:
            Job ID of backup job

        """
        self._admin_console.driver.execute_script("window.scrollTo(0,0)")
        self._admin_console.select_hyperlink("Back up now")
        backup = Backup(self)
        return backup.submit_backup(bkp_type)

    @WebAction()
    def restore(self):
        """
        Opens the select restore page

        Returns:
            None
        """
        self._admin_console.driver.execute_script("window.scrollTo(0,0)")
        self._admin_console.select_hyperlink("Restore")

    @WebAction()
    def backup_jobs(self):
        """
        Lists all the backup jobs of the collection

        Returns:
            None
        """
        self._admin_console.select_hyperlink("Jobs")

    @WebAction()
    def content_info(self):
        """
        Returns the list of all the subclient content info

        Returns:
            content     (list):     list of all VMs in the subclient content
        """

        content = []
        self._admin_console.log.info("Printing the collection content")
        elements = self._admin_console.driver.find_elements(By.XPATH, 
            "//cv-tile-component[@data-title='Content']"
            "/div/div[3]/div/div[@data-ng-show='closeLoader']/ul")
        for elem in elements:
            content.append(elem.find_element(By.XPATH, "./li").text)
        self._admin_console.log.info(content)
        return content

    @WebAction()
    def schedule_info(self):
        """
        Displays all the schedules associated with the subclient

        Returns:
            List of all schedules associated to the subclient
        """
        elements = self._admin_console.driver.find_elements(By.XPATH, "//cv-tile-component[@data-title="
                                                      "'Schedules']/div/div[3]/div/div[2]/ul")
        schedules = []
        for element in elements:
            schedules.append(element.find_element(By.XPATH, "./li").text)
        self._admin_console.log.info("The schedules associated with the subclient are %s", str(schedules))
        return schedules

    @WebAction()
    def delete_schedule(self, schedule_name):
        """
        Deletes a schedule with the given name

        Args:
            schedule_name    (str):  the name of the schedule to be deleted

        Raises:
            Exception:
                if there is no schedule with the given name

        """
        self._admin_console.select_hyperlink(schedule_name)
        self._admin_console.click_button('Delete')
        self._admin_console.click_button('Yes')
        self._admin_console.check_error_message()
