# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
admin console schedules page
"""

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Reports.cte import CommonFeatures
from Web.Common.page_object import PageService, WebAction


class ScheduleDetailsPage(CommonFeatures):
    """Class to manage report schedule details page"""

    def __init__(self, admin_console):
        super().__init__(admin_console)

        self.notification_panel = RPanelInfo(admin_console, title='Notification')

    @PageService()
    def return_to_schedules(self):
        """
            Returns back to schedules page from schedule details
        """
        self._admin_console.select_breadcrumb_link_using_text('Schedules')

    @PageService()
    def get_email_recipients(self):
        """
            returns the list of email recipients
        """
        return self.notification_panel.get_details()['Email recipients']

    @PageService()
    def get_users_to_notify(self):
        """
            returns the list of users to notify (includes user/user groups)
        """
        return self.notification_panel.get_list()


class ManageSchedules(CommonFeatures):
    """Class for managing report's schedules"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.job_alert = Alert(admin_console)

    @WebAction()
    def __get_schedule_names(self):
        """Returns the list of all schedules"""
        return [schedule.text for schedule in self._driver.find_elements(By.XPATH, "//td//a")]

    @WebAction()
    def _select_schedule_containing(self, schedule_string):
        """
        Return all schedules containing string
        Args:
            schedule_string                   (String)       --    String present in schedule name
        """
        self.table.search_for(schedule_string)
        schedules = self._driver.find_elements(By.XPATH, "//td//a[contains(text(), '" + schedule_string + "')]")
        if not schedules:
            raise NoSuchElementException("No schedules are found with name containing [%s]" %
                                         schedule_string)
        return [schedule.text for schedule in schedules]

    @WebAction()
    def _click_schedule(self, schedule_name):
        """
            Goes to the schedule of a particular schedule_name
        """
        self._driver.find_element(By.XPATH, "//a[contains(text(), '" + schedule_name + "')]").click()

    @PageService()
    def get_email_recipients(self, schedule_name, user_or_user_groups=False):
        """
            returns email recipients for schedule
        """
        self.table.search_for(schedule_name)
        self._click_schedule(schedule_name)
        self._admin_console.wait_for_completion()

        details_page = ScheduleDetailsPage(self._admin_console)
        if user_or_user_groups:
            recipients = details_page.get_users_to_notify()
        else:
            recipients = details_page.get_email_recipients()
        details_page.return_to_schedules()

        return recipients

    @PageService()
    def enable_schedules(self, schedules):
        """
        Enable Schedules
        Args:
            schedules              (list)     -- List of schedules
        """
        self.enable_entity(schedules)
        self._admin_console.wait_for_completion()

    @PageService()
    def disable_schedules(self, schedules):
        """
        Disable Schedules
        Args:
            schedules              (list)     -- List of schedules
        """
        self.disable_entity(schedules)
        self._admin_console.wait_for_completion()

    @PageService()
    def run_schedules(self, schedules):
        """
        run schedules
        Args:
            schedules              (list)     -- List of schedules
        """
        self.run_entity(schedules, wait_for_completion=False)
        job_id = self.job_alert.get_jobid_from_popup()
        self._admin_console.wait_for_completion()
        return job_id

    @PageService()
    def delete_schedules(self, schedules):
        """
        Delete Schedules
        Args:
            schedules              (list)     -- List of schedules
        """
        self.delete_entity(schedules)
        self._admin_console.wait_for_completion()

    @PageService()
    def get_all_schedules(self, column_name ):
        """
        Fetches the list of all schedules
        Args:
            column_name: Schedule first column name

        Returns:
            All the schedule names

        """
        return self.table.get_column_data(column_name, fetch_all=True)

    @PageService()
    def cleanup_schedules(self, schedule_string):
        """
        delete schedules containing specific string in schedule name

        Args:
            schedule_string                   (string)      --     schedule name to be selected

        """
        try:
            schedules = self._select_schedule_containing(schedule_string)
        except NoSuchElementException:
            return
        self.delete_entity(schedules)
        self._admin_console.wait_for_completion()

    @PageService()
    def open_schedule(self, schedule_string):
        """
        Opens the schedule window of a particular schedule_name

        Args:
            schedule_string                   (string)      --     schedule name to be selected

        """
        self.table.search_for(schedule_string)
        self._click_schedule(schedule_string)

    @PageService()
    def edit_schedule(self, page_level=True):
        """
        Clicks the edit option on the schedule details page of a particular schedule
        """
        self.edit_entity(page_level=page_level)



