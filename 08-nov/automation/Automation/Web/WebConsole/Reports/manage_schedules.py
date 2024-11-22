from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Operations related to manage schedules page.


ScheduleSettings:

    __init__()                           --  initialize instance of the ScheduleSettings class,
                                             and the class attributes.

    delete_schedules()                   --  delete schedules

    cleanup_schedules()       --  deletes the schedules with specified string in
                                             schedule name
"""
from time import sleep

from AutomationUtils import logger
from selenium.common.exceptions import NoSuchElementException
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.cte import ConfigureSchedules
from Web.Common.page_object import WebAction, PageService


class ScheduleSettings:
    """ Trigger/delete/enable/disable schedules from these modules """
    def __init__(self, web_console: WebConsole):
        self._driver = web_console.browser.driver
        self._web_console = web_console
        self._log = logger.get_log()

    @WebAction()
    def _select_schedules(self, schedules: list):
        """
        Select schedules
        Args:
            schedules              (list)       --           list of schedule names
        """
        for each_schedule in schedules:
            try:
                self._driver.find_element(By.XPATH, 
                    "//*[contains(@title,'" + each_schedule + "')]/../td/div").click()
            except NoSuchElementException:
                raise NoSuchElementException("Schedule [%s] is not found in schedule settings page"
                                             "to select" % each_schedule)

    @WebAction()
    def _click_delete(self):
        """click delete"""
        self._driver.find_element(By.XPATH, "(//button[@id='deleteBtn'])[2]").click()

    @WebAction()
    def _click_edit_schedule(self, schedule_name):
        """Click on schedule"""
        try:
            xpath = "//span[text() ='%s']" % schedule_name
            self._driver.find_element(By.XPATH, xpath).click()
        except NoSuchElementException:
            raise NoSuchElementException("[%s] schedule is not found in schedule's setting page"
                                         % schedule_name)

    @WebAction()
    def _is_schedule_exists(self, schedule_name):
        """
        Check if specified schedule exists in schedule settings page
        Args:
            schedule_name                     (String)  --        Schedule name

        Returns:return True if schedule exists else returns false
        """
        schedules = self._driver.find_elements(By.XPATH, "//*[@title='%s']/../td/div"
                                                        % schedule_name)
        if schedules:
            return True
        return False

    @WebAction()
    def _is_filter_enabled(self):
        """Return true if filter is enabled or return false"""
        xpath = "//tr[@id='filterRow_schedulesList']"
        if not self._driver.find_elements(By.XPATH, xpath):
            # For the 1st time when page is loaded this element will not be there in document.
            # It will be added only atleast once it is enabled.
            return False
        if self._driver.find_element(By.XPATH, xpath).is_displayed():
            return True
        return False

    @WebAction()
    def _click_filter(self):
        """Click filter"""
        self._driver.switch_to.window(self._driver.current_window_handle)
        xpath = "//*[@id='schedulesList_Filter']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _select_schedule_containing(self, schedule_string):
        """
        Select all schedules containing string
        Args:
            schedule_string                   (String)       --    String present in schedule name
        """
        schedules = self._driver.find_elements(By.XPATH, "//*[contains(@title,'" + schedule_string
                                                        + "')]/../td/div")
        if not schedules:
            raise NoSuchElementException("No schedules are found with name containing [%s]" %
                                         schedule_string)
        for each_schedule in schedules:
            each_schedule.click()

    @WebAction()
    def _get_email_recipients(self, schedule_name):
        """
        Get email recipients id for specific schedule name
        Args:
            schedule_name                  (String)       --    Schedule name

        Returns: email id present in schedule
        """
        xpath = "//*[@title='%s']/..//*[@data-label='Email Recipient(s)']" % schedule_name
        return str(self._driver.find_element(By.XPATH, xpath).text)

    @WebAction()
    def _get_recipients_user(self, schedule_name):
        """
        Get recipients user and groups for specific schedule name
        Args:
            schedule_name                  (String)       --    Schedule name

        Returns: recipients user and groups present in schedule
        """
        xpath = "//*[@title='%s']/..//*[@data-label='Recipient Users and Groups']" % schedule_name
        element = self._driver.find_element(By.XPATH, xpath)
        return element.get_attribute("title")

    @WebAction()
    def _get_column_names(self):
        """Get column names from manage schedule page"""
        xpath = "//table[@id='schedulesList_table']//th[@class='sorting']"
        return [
            column.text for column in self._driver.find_elements(By.XPATH, xpath)
        ]

    @WebAction()
    def _get_filter_objects(self):
        """Get filter objects"""
        # 0th filter will be blank in manage schedules page. So that's ignored.
        return self._driver.find_elements(By.XPATH, "//input[contains(@id,"
                                                   "'schedulesList_filterText')]")[1:-1]

    @WebAction()
    def enable_filter(self):
        """Enable filter"""
        if not self._is_filter_enabled():
            self._click_filter()

    @PageService()
    def _set_filter_text(self, column_name, value):
        """Set filter"""
        column_idx = self._get_column_names().index(column_name)
        _filter = self._get_filter_objects()[column_idx]
        _filter.clear()
        _filter.send_keys(value)
        _filter.send_keys("\n")

    @PageService()
    def filter_by_schedule_name(self, schedule_name):
        """
        Filter by schedule name
        Args:
            schedule_name            (String)   --    Schedule name
        """
        self.enable_filter()
        self._set_filter_text('Name', schedule_name)

    @PageService()
    def edit_schedule(self, schedule_name):
        """
        Edit schedule
        Args:
            schedule_name                      (String)  --         schedule name

        Returns: ConfigureSchedule object
        """
        self.filter_by_schedule_name(schedule_name)
        self._click_edit_schedule(schedule_name)
        return ConfigureSchedules(self._web_console)

    @PageService()
    def delete_schedules(self, schedules):
        """
        Delete schedules
        Args:
            schedules                           (list)    --       list of schedule names
        """
        self._log.info("Deleting schedules:%s", str(schedules))
        self._select_schedules(schedules)
        self._click_delete()
        sleep(3)
        self._web_console.wait_till_load_complete()

    @PageService()
    def cleanup_schedules(self, schedule_string):
        """
        delete schedules containing specific string in schedule name

        Args:
            schedule_string                   (string)      --     schedule name to be selected

        """
        try:
            self._select_schedule_containing(schedule_string)
        except NoSuchElementException:
            return
        self._log.info("Deleting schedules containing [%s] string in schedule name",
                       schedule_string)
        self._click_delete()
        sleep(3)
        self._web_console.wait_till_load_complete()

    @PageService()
    def is_schedule_exists(self, schedule_name):
        """
        Verify schedule exists
        Args:
            schedule_name                  (String)       --    Schedule name

        Returns:True if schedule exists else return false

        """
        self.filter_by_schedule_name(schedule_name)
        return self._is_schedule_exists(schedule_name)

    @PageService()
    def get_email_recipients(self, schedule_name):
        """
        Get email recipients id for specified schedule name
        Args:
            schedule_name                  (String)       --    Schedule name

        Returns: email id present in schedule
        """
        self.filter_by_schedule_name(schedule_name)
        return self._get_email_recipients(schedule_name)

    @PageService()
    def get_recipients_user(self, schedule_name):
        """
        Get recipients users and groups for specified schedule name
        Args:
            schedule_name                  (String)       --    Schedule name

        Returns: receipient user and groups present in schedule
        """
        self.filter_by_schedule_name(schedule_name)
        return self._get_recipients_user(schedule_name)
