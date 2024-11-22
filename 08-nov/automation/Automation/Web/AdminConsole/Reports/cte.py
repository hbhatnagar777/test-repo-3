# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
File for all CTE operations like export, schedule, alert and Security operations
any common functionality across Reports APP can be added here.

Email:

    _select_format     --     Select email attachment export_type

    _set_recipient     --     Set recipient email id

    _choose_format     --     Choose export_type

    email_now          --     emails the report

ConfigureSchedules:

    _select_format     --     Select schedule email attachment export_type

    _select_daily      --     select daily schedule option

    _select_weekly     --     select weekly schedule option

    _select_monthly    --     select monthly schedule option

    set_schedule_name  --     Set schedule name

    select_frequency   --     select schedule frequency

    create_schedule    --     Create schedule on report

"""
from selenium.webdriver.common.by import By
from time import sleep, time

from AutomationUtils import config
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo, RModalPanel
from Web.Common.exceptions import CVTimeOutException
from Web.Common.page_object import (
    WebAction,
    PageService
)

_CONFIG = config.get_config()


class Email:
    """
    EmailNow has the interfaces to work on Email now panel and do email operations on admin console
    Reports

    email_now(file_format, recipient_mail_id) -- emails the report with given export_type
                                                 to recipient mail given in input
    """

    class Format:
        """
        export_type is a constant on different type of file formats in Email now panel on reports
        """
        PDF = "PDF"
        HTML = "HTML"
        CSV = "CSV"

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._dialog = RModalDialog(admin_console)

    @PageService()
    def _select_format(self, attachment_type):
        """
        Select pdf/html/csv export_type in email frame
        Args:
            attachment_type: select attachment type from export_type class
        """
        self._dialog.select_dropdown_values('fileFormat', [attachment_type])

    @PageService()
    def _set_recipient(self, recipient_mail_id):
        """
        Set recipient name
        Args:
            recipient_mail_id       (String)   --    recipient email id

        Returns:

        """
        self._dialog.fill_text_in_field('emailRecipients', recipient_mail_id)

    @PageService()
    def _set_compress_attachment(self, enable):
        """
        clicks on the compress attachment toggle
        """
        if enable:
            self._dialog.enable_toggle('compressEmailFile')
        else:
            self._dialog.disable_toggle('compressEmailFile')

    @PageService()
    def _choose_format(self, file_format):
        """
        Choose file export_type
        Args:
            file_format           (String)   --   Select formats available from export_type class
        """
        if file_format == self.Format.PDF:
            self._select_format(self.Format.PDF)
        elif file_format == self.Format.HTML:
            self._select_format(self.Format.HTML)
        elif file_format == self.Format.CSV:
            self._select_format(self.Format.CSV)
        else:
            raise ValueError("Invalid attachment type is passed!")

    @PageService()
    def email_now(self, file_format, recipient_mail_id, compress=False):
        """
        Emails the report
        Args:
            file_format           (String)   --   Select formats available from export_type class
            recipient_mail_id:    (String)   --   recipient email id
            compress:             (Bool)     --   whether to compress attachment
        """
        self._set_compress_attachment(compress)
        self._choose_format(file_format)
        self._set_recipient(recipient_mail_id)
        self._dialog.click_submit(wait=False)

    @PageService()
    def get_job_id(self):
        """
            Get job id of email job from notification
            Returns:(string) job id
        """
        job_id = self._admin_console.get_jobid_from_popup(hyperlink=True)
        return job_id


class ConfigureSchedules:
    """
    ConfigureSchedules has the interfaces to schedule reports and
    to operate on Reports schedule panels

    create_schedule(schedule_name, email_recipient, file_format) -- creates a schedule
                    with email notification with given frequency type of default time.
    """

    class Frequency:
        """
        Frequency is a constant on different frequency types available on Reports schedule panel
        """
        DAILY = 'Daily'
        WEEKLY = "Weekly"
        Monthly = "Monthly"

    class Format:
        """
        export_type is a constant on different type of export_type available on schedule panel of reports
        """
        PDF = "PDF"
        HTML = "HTML"
        CSV = "CSV"
        EXECUTIVE_SUMMARY = "Executive Summary"  # executive summary for WW activity report.
        INLINE = "INLINE"

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver

    @WebAction()
    def _access_schedule_frame(self):
        """
        Switch to schedule frame
        """
        frame = self._driver.find_element(By.CLASS_NAME, "modal-iframe")
        self._driver.switch_to.frame(frame)

    @WebAction()
    def _select_format(self, attachment_type):
        """
        Select pdf/html/csv export_type in schedule frame
        Args:
            attachment_type: select attachment type from export_type class
        """
        self._driver.find_element(By.XPATH, "//*[contains(@class, 'checkboxLayer')]"
                                            f"//div[@title='{attachment_type}']").click()

    @WebAction()
    def _user_to_notify(self, user_or_user_group_name):
        """
        select user to notify for the user or user group
        Args:
            user_or_user_group_name: Enter string user or group name
        """
        self._admin_console.fill_form_by_id('field', user_or_user_group_name)
        self._admin_console.wait_for_completion()
        self._admin_console.driver.find_element(By.XPATH,
                                                f"//*[@class='suggestedText vw-text']/..//*[@title='{user_or_user_group_name}']").click()

    @WebAction()
    def _select_inline(self):
        """
        Select inline as email body
        """
        self._admin_console.select_radio("Inline (as email body)")

    @WebAction()
    def _select_daily(self):
        """
        Select daily schedule
        """
        self._admin_console.select_radio("Daily")

    @WebAction()
    def _select_weekly(self):
        """
        Select weekly
        """
        self._admin_console.select_radio("Weekly")

    def _select_monthly(self):
        """
        Select monthly
        """
        self._admin_console.select_radio("Monthly")

    @WebAction()
    def _click_on_save(self):
        """
        Click on save button
        """
        self.save()

    @WebAction()
    def set_schedule_name(self, schedule_name):
        """
        sets name for the schedule
           Args:
           schedule_name               (String)   --    name for schedule
        """
        self._driver.find_element(By.ID, "name").clear()
        self._driver.find_element(By.ID, "name").send_keys(schedule_name)

    @WebAction()
    def _click_format(self):
        """
        Click on export_type before selecting file type in schedule frame
        """
        self._driver.find_element(By.XPATH, "//*[@id='outputFormatSelect']").click()

    @PageService()
    def select_frequency(self, frequency):
        """
        selects the frequency pattern for schedules
        :param frequency: frequency to select, use self.frequency for available types
        """
        if frequency == self.Frequency.DAILY:
            self._select_daily()
        elif frequency == self.Frequency.WEEKLY:
            self._select_weekly()
        elif frequency == self.Frequency.Monthly:
            self._select_monthly()
        else:
            raise Exception("Undefined Frequency type [%s] " % frequency)

    @PageService()
    def save(self):
        """
        saves the schedule
        """
        self._admin_console.click_button("Save")

    @PageService()
    def cancel(self):
        """
        closes the schedule panel
        """
        self._admin_console.click_button("Cancel")

    @WebAction()
    def set_recipient(self, recipient):
        """
        sets recipient mail id in schedule
        Args:
            recipient: mail id of recipient, use comma seperation for multiple id
        """
        self.clear_recipient()
        self._driver.find_element(By.NAME, "emailRecipients").send_keys(recipient)

    @WebAction()
    def clear_recipient(self):
        """
        Clears recipient name in schedule
        """
        self._driver.find_element(By.NAME, "emailRecipients").clear()

    @PageService()
    def select_format(self, file_type='PDF'):
        """
        selects the export_type given in input
        :param file_type: file export_type to select in schedule
        """
        self._click_format()
        if file_type == self.Format.PDF:
            self._select_format(self.Format.PDF)
        elif file_type == self.Format.HTML:
            self._select_format(self.Format.HTML)
        elif file_type == self.Format.CSV:
            self._select_format(self.Format.CSV)
        elif file_type == self.Format.INLINE:
            self._select_inline()
        else:
            raise Exception('Given export_type %s not available in schedule panel' % file_type)

    @PageService()
    def create_schedule(self, schedule_name, email_recipient, file_format=Format.PDF):
        """
        Method to create schedule with basic options with email
        notification and with given export_type and frequency
        Args:
            schedule_name: name of schedule to be created
            email_recipient: email id for notfication, comma seperated to multiple id
            file_format: export_type of file type, use self.export_type for available formats
        """
        self._admin_console.log.info(
            "Creating schedule:%s ; email recipient:%s; export_type:%s;",
            schedule_name, email_recipient, file_format
        )
        self.set_schedule_name(schedule_name)
        self.set_recipient(email_recipient)
        self.select_format(file_format)
        self.save()

    @PageService()
    def enable_end_user_security(self):
        """ select the end user security"""
        xpath = '//*[@toggle-name="endUserSecurity"]'
        self._driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def select_user_to_notify(self, user_or_group):
        """
        select the user to notify and send user or user group
        Args:
            user_or_group: string user or group name
        """
        self._user_to_notify(user_or_group)


class RConfigureSchedules:
    """
    RConfigureSchedules has the interfaces to schedule reports and
    to operate on Reports schedule panels

    create_schedule(schedule_name, email_recipient, file_format) -- creates a schedule
                    with email notification with given frequency type of default time.
    """

    class Format:
        """
        export_type is a constant on different type of export_type
        available on schedule panel of reports
        """
        PDF = "PDF"
        HTML = "HTML"
        CSV = "CSV"
        EXECUTIVE_SUMMARY = "Executive Summary"  # executive summary for WW activity report.
        INLINE = "Email body"

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._wizard = Wizard(self._admin_console)
        self._dropdown = RDropDown(self._admin_console)
        self._dialog = RModalDialog(self._admin_console)

    @WebAction()
    def _select_format(self, attachment_type):
        """
        Select pdf/html/csv export_type in schedule frame
        Args:
            attachment_type: select attachment type from
            export_type class
        """
        self._wizard.select_drop_down_values(id="exportTypeDropdown", values=[attachment_type],
                                             wait_for_content_load=False)

    @PageService()
    def set_schedule_name(self, schedule_name):
        """
        sets name for the schedule
           Args:
           schedule_name               (String)   --    name for schedule
        """
        self._wizard.fill_text_in_field(id='scheduleName', text=schedule_name)

    @PageService()
    def select_frequency(self, frequency):
        """
        selects the frequency pattern for schedules
        :param frequency: frequency to select
        """

        self._wizard.select_drop_down_values(id="freqDropdown", values=[frequency])

    @PageService()
    def save(self):
        """
        saves the schedule
        """
        self._wizard.click_button('Submit')

    @PageService()
    def cancel(self):
        """
        closes the schedule panel
        """
        self._wizard.click_cancel()
        self._dialog.click_submit()

    @WebAction()
    def set_recipient(self, recipient):
        """
        sets recipient mail id in schedule
        Args:
            recipient: mail id of recipient, use comma seperation for multiple id
        """
        self._wizard.fill_text_in_field(id='emails', text=recipient)

    @PageService()
    def select_format(self, file_type='PDF'):
        """
        selects the export_type given in input
        :param file_type: file export_type to select in schedule
        """
        if file_type == self.Format.PDF:
            self._select_format(self.Format.PDF)
        elif file_type == self.Format.HTML:
            self._select_format(self.Format.HTML)
        elif file_type == self.Format.CSV:
            self._select_format(self.Format.CSV)
        elif file_type == self.Format.INLINE:
            self._select_format(self.Format.INLINE)
        elif file_type == self.Format.EXECUTIVE_SUMMARY:
            self._select_format(self.Format.EXECUTIVE_SUMMARY)
        else:
            raise Exception('Given export_type %s not available in schedule panel' % file_type)

    @PageService()
    def create_schedule(self, schedule_name, email_recipient=None,
                        file_format=Format.PDF, user_or_group=None, end_user_security_enabled=None
                        ):
        """
        Method to create/modify schedule with basic options with email
        notification and with given export_type and frequency
        Args:
            end_user_security_enabled: string
            schedule_name: name of schedule to be created
            email_recipient: email id for notfication, comma seperated to multiple id
            file_format: export_type of file type, use self.export_type for available formats
            user_or_group: users or usergroups to be notified
        """
        self._admin_console.log.info(
            "Creating schedule:%s ; email recipient:%s; export_type:%s; user/user_groups:%s to be notified",
            schedule_name, email_recipient, file_format, user_or_group
        )

        self.set_schedule_name(schedule_name)
        self.select_format(file_format)
        if end_user_security_enabled:
            self.enable_end_user_security()
        self._wizard.click_next()
        if user_or_group and end_user_security_enabled:
            self.select_user_to_notify(user_or_group)
        elif user_or_group:
            self.select_user_to_notify(user_or_group)
            self.set_recipient(email_recipient)
        else:
            self.set_recipient(email_recipient)
        self._wizard.click_next()
        self._wizard.click_next()
        self.save()
        sleep(4)

    @PageService()
    def enable_end_user_security(self):
        """ select the end user security"""
        self._wizard.select_radio_button(id='individualEmail')

    @PageService()
    def select_user_to_notify(self, user_or_group):
        """
        select the user to notify and send user or user group
        Args:
            user_or_group: string user or group name
        """
        self._dropdown.search_and_select(select_value=user_or_group, id='notifyList_usersAndGroupsList')

    @PageService()
    def click_equivalent_api(self):
        """
        Clicks the equivalent api button on schedule window page
        """
        self._wizard.click_button('Equivalent API')

    @PageService()
    def click_manage_schedules(self):
        """
        Clicks the manage schedules button on the schedule window page
        """
        self._wizard.click_button('Manage schedules')

    @PageService()
    def click_edit_report_settings(self):
        """
        Clicks the Edit Report Settings on the schedule window page
        """
        self._wizard.click_button('Edit report settings')


class ConfigureAlert:
    """
    ConfigureAlert has interfaces to setup alert on reports, for basic alert use create_alert,
    to create alert with for non default options create your own customized method

    create_alert(alert_name=None, column_name=None, column_value=None,
                     recipient_mail='reportautomation@commvault.com')
                -- creates a alert with email notification and with default time.

    set_name(name): -- sets name for the alert

    select_notifications_type(notification_option)
                -- selects notification type, use self.notifications_type for available formats

    set_recipient(recipient) -- sets recipient mail id

    set_time(hour, minute, ampm='AM')  -- sets time for Alert

    select_frequency(self, interval): selects frequency of alert

    add_condition() -- clicks on add alert condition

    check_test_criteria() -- clicks test criteria in alert panel

    select_alert_severity(notification_with) -- select severity in alert notification

    select_alert_condition(condition='all') --selection condition for alerts (all or any)

    select_column(name) -- selects the column for alert

    set_value(value) -- sets the value for column selected

    select_operator(operator) -- selects the operator for column to be checked

    save() -- saves Alert

    cancel() -- closes Alert panel

    get_column_names() - gets the columns name available in drop down

    get_available_conditions() - gets available conditions for a column.

    select_health_param(status) -- select health param status in alert(good/warning/critical)
    """

    class Operator:
        """
        Operator is constant on different types of operators supported in alerts
        """
        EQUAL_TO = "equal to"
        NOT_EQUAL_TO = "not equal to"
        CONTAINS = "contains"
        NOT_CONTAINS = "not contains"
        IS_EMPTY = "is empty"
        NOT_EMPTY = "not empty"
        LESS_THAN = "less than"
        MORE_THAN = "more than"

    class Notification:
        """
        Notification is a constant on different notification types
        available on Reports Alerts panel
        """
        EMAIL = "Email"
        CONSOLE_ALERTS = "Console Alerts"
        EVENT_VIEWER = "Windows Event Viewer"
        SNMP_Traps = "SNMP Traps"
        SCOM = "SCOM"

    class Frequency:
        """
        Frequency is a constant on different frequency types available on Reports Alerts panel
        """
        DAILY = 'Day'
        WEEKLY = "Week"
        Monthly = "Month"

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.operator = ConfigureAlert.Operator
        self.notifications_type = ConfigureAlert.Notification
        self.frequency = ConfigureAlert.Frequency
        self._wizard = Wizard(self._admin_console)
        self._dropdown = RDropDown(self._admin_console)
        self._dialog = RModalDialog(self._admin_console)
        self._panel = RPanelInfo(self._admin_console)
        self._rmodule = RModalPanel(self._admin_console)

    @staticmethod
    def _isvalid_time(hour, minute, ampm):
        if int(hour) < 1 or int(hour) > 12:
            raise Exception('invalid Hour input')
        if int(minute) < 0 or int(minute) > 60:
            raise Exception('invalid Minute input')
        if ampm not in ('AM', 'PM'):
            raise Exception('invalid time period input')

    @WebAction()
    def _select_email(self):
        """
        Select email
        """
        self._wizard.select_radio_button(label=self.notifications_type.EMAIL)

    @WebAction()
    def _select_console_alert(self):
        """
        Select console alert
        """
        self._wizard.select_radio_button(label=self.notifications_type.CONSOLE_ALERTS)

    @WebAction()
    def _select_event_viewer(self):
        """
        Select event viewer
        """
        self._wizard.select_radio_button(label=self.notifications_type.EVENT_VIEWER)

    @WebAction()
    def _select_snmp(self):
        """
        Select snmp
        """
        self._wizard.select_radio_button(label=self.notifications_type.SNMP_Traps)

    @WebAction()
    def _select_scom(self):
        """
        Select snmp
        """
        self._wizard.select_radio_button(label=self.notifications_type.SCOM)

    @PageService()
    def access_edit_criteria(self):
        """access edit criteria"""
        self._panel.click_button(button_name='Edit')

    @PageService()
    def set_alert_name(self, alert_name):
        """
        set name for alert
        Args:
            alert_name (string): name of the alert
        """
        self._wizard.fill_text_in_field(id='alertName', text=alert_name)

    @PageService()
    def select_notifications_type(self, notification_option):
        """
        select notification types for alert
        :param notification_option: use self.notifications_type for available notification types
        """
        if notification_option == self.notifications_type.EMAIL:
            self._select_email()
        elif notification_option == self.notifications_type.CONSOLE_ALERTS:
            self._select_console_alert()
        elif notification_option == self.notifications_type.EVENT_VIEWER:
            self._select_event_viewer()
        elif notification_option == self.notifications_type.SNMP_Traps:
            self._select_snmp()

    @PageService()
    def set_recipient(self, recipient):
        """
        sets recipient mail id in schedule

        Args:
            recipient: enter the email id for recipient

        """
        self._rmodule.search_and_select(id='emailToDropdown', select_value=recipient)

    @PageService()
    def set_time(self, hour, minute, ampm='AM'):
        """
        sets the time for schedule
        :param hour:  hour input 1-12
        :param minute: minute input 1-60
        :param ampm: period input 'AM' or 'PM'
        """
        self._isvalid_time(hour, minute, ampm)
        self._admin_console.log.info("Setting alert time:" + str(hour) + ":" + str(minute) + ":" + str(ampm))
        self._wizard.fill_text_in_field(id=':r4c:', text=hour + ':' + minute + ampm)

    @PageService()
    def select_frequency(self, frequency):
        """
        selects the frequency pattern for schedules
        Args:
            frequency (String):  Daily/ Weekly/ Monthly
        """
        self._wizard.select_drop_down_values(id='freqDropdown', values=[frequency])

    @WebAction()
    def _click_column_value(self):
        """select column value field"""
        xpath = "//input[@class='alert-criteria-input ' and @value='']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _click_criteria(self, col_count):
        """
        select criteria from the dropdown
        Args:
            col_count:      (Int)  index of the column

        """
        xpath = "//div[@class='custom-report-criteria-row']//div[@id='optionsDropdown']"
        columns = self._driver.find_elements(By.XPATH, xpath)
        columns[col_count].click()

    @WebAction()
    def _click_column_dropdown(self, column_count):
        """
         select column count
        Args:
            column_count:      (INT) column index
        """

        xpath = "//div[@class='custom-report-criteria-row']//div[@id='columnsDropdown']"
        columns = self._driver.find_elements(By.XPATH, xpath)
        columns[column_count].click()

    @WebAction()
    def _select_column(self, column_name):
        """
        select the column name
        Args:
            column_name:   (Sting) name of the column

        """

        col_xpath = f"//li[contains(@class, 'Dropdown-ddListItem')]//div[@title= '{column_name}']"
        self._driver.find_element(By.XPATH, col_xpath).click()

    @PageService()
    def select_column_dropdown(self, column_name, column_index):
        """
        select the column from the dropdown
        Args:
            column_name:             (String)   name of the column
            column_index:                 (Int)    index of the column name
        """
        self._click_column_dropdown(column_index)
        self._select_column(column_name)
        self._admin_console.wait_for_completion()

    @PageService()
    def select_criteria(self, criteria_name, criteria_index):
        """

        Args:
            criteria_name:        (String)   name of the criteria
            criteria_index:     (Int)    index of the criteria
        """
        self._click_criteria(criteria_index)
        self._select_column(criteria_name)

    @PageService()
    def fill_column_value(self, column_value):
        """
        fill the value in the value field
        Args:
            column_value:    (Sting) value of the column
        """

        self._click_column_value()
        self.set_value(column_value)

    @PageService()
    def add_condition(self, column_name=None, column_value=None, column_condition=None, alert_criteria_idx=None):
        """
        add alert condition
        Args:
            alert_criteria_idx:                       (Int)       --     column index
            column_name                      (String)    --     name of the column
            column_value                    (String)     --     criteria value
            column_condition                 (String)    --     Operator to be selected
        """
        self._wizard.click_button(name='Add condition')
        self.select_column_dropdown(column_name, alert_criteria_idx)
        self.select_criteria(column_condition, alert_criteria_idx)
        self.fill_column_value(column_value)

    @PageService()
    def check_test_criteria(self):
        """
        clicks test criteria in alert panel
        """
        self._wizard.click_button(name='Test criteria')
        self._driver.switch_to.window(self._driver.window_handles[-1])
        self._admin_console.wait_for_completion()

    @PageService()
    def select_alert_severity(self, notification_with):
        """
        send notification with option can be changed as: Info/Warning/Critical
        """
        self._wizard.select_dropdown_list_item(label=notification_with)

    def click_alert_condition(self, condition_id):
        """
        click any or all condition
        Returns:
        """
        xpath = "//div[contains(@aria-labelledby,'severityDropdown')]"
        conditions = self._driver.find_elements(By.XPATH, xpath)
        conditions[condition_id].click()

    @PageService()
    def select_alert_condition(self, condition='all'):
        """
        select condition: all or any
        """
        self.click_alert_condition(condition_id=1)
        xpath = f"//ul[contains(@aria-labelledby,'severityDropdown')]//div[@title='{condition}']"
        self._driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def select_column(self, column_name):
        """
        select a column form the dropdown
        Args:
            column_name: name of the column
        """
        self._wizard.select_drop_down_values(id='columnsDropdown', values=[column_name])

    @PageService()
    def set_criteria(self, criteria_value):
        """
        set the value for columns selected
        Args:
            criteria_value: column value

        """
        self._wizard.select_drop_down_values(id='optionsDropdown', values=[criteria_value])

    @PageService()
    def set_value(self, value):
        """
        set the value for columns selected
        Args:
            value: column value

        """
        value_field = self._driver.find_element(By.XPATH, "//input[@class='alert-criteria-input ' and @value='']")
        value_field.send_keys(value)

    @PageService()
    def select_operator(self, operator):
        """
        select the operator to be applied to column,
        :param operator: use self.operator to find the available types
        """
        self._wizard.select_drop_down_values(id='optionsDropdown', values=operator)

    @PageService()
    def create_alert(self, alert_name=None, column_name=None, column_value=None, criteria=None,
                     recipient_mail=_CONFIG.email.email_id, is_health=None, is_edit_alert=False):
        """
        create alert
        Args:
            is_edit_alert: Edit alert
            is_health: type of alert in string
            alert_name: name of the alert
            column_name: column name to be selected
            column_value: column value to set
            criteria: criteria to be selected
            recipient_mail: email id for recipient

        """
        if not is_health:
            self._admin_console.log.info("Creating alert:%s", alert_name)
            self.set_alert_name(alert_name)
            if not is_edit_alert:
                self.select_column(column_name)
                self.set_criteria(criteria)
                self.set_value(column_value)
            self._wizard.click_next()
            self._admin_console.wait_for_completion()
            self.set_recipient(recipient_mail)
            self._wizard.click_next()
            self._admin_console.wait_for_completion()
            self._wizard.click_submit()
            self._admin_console.wait_for_completion()
        else:
            self._admin_console.log.info("Creating alert:%s", alert_name)
            self.set_alert_name(alert_name)
            self.select_health_param(criteria)
            self._wizard.click_next()
            self._admin_console.wait_for_completion()
            self.set_recipient(recipient_mail)
            self._wizard.click_next()
            self._admin_console.wait_for_completion()
            self._wizard.click_submit()
            self._admin_console.wait_for_completion()

    @PageService()
    def is_alert_created(self, time_out=30):
        """
        Verify alert is created through notification
        Returns:True/False
        """
        end_time = time() + time_out
        while time() < end_time:
            notifications = self._admin_console.get_notification()
            if not notifications:
                continue
            if notifications[0] == "Alert created successfully":
                return True
            self._admin_console.log.info("Notification:[%s]", notifications[0])
            return False
        raise CVTimeOutException(time_out, "Alert notification is not recieved within time "
                                           "period")

    @PageService()
    def get_column_names(self):
        """
        :return: columns list available for alert
        """
        return self._panel.get_list()

    @PageService()
    def cancel(self):
        """
        closes the alert panel
        """
        self._admin_console.click_button("Cancel")
        self._panel.click_button('Yes')

    @PageService()
    def get_available_conditions(self):
        """
        :return: list of available conditions for column
        """
        return self._panel.get_list()

    @PageService()
    def select_health_param(self, status):
        """
        selects the status of parameter to be set.
        :param status: Warning/Critical/Good
        """
        self._wizard.select_drop_down_values(id='criteriaSeverityDropdown', values=[status])


class CommonFeatures:
    """CommonFeatures has Commonly used options such as alerts and schedules options"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console = admin_console
        self._driver = self._admin_console.driver
        self.table = Rtable(self._admin_console)
        self.page_container = PageContainer(self._admin_console)
        self.dialog = RModalDialog(self._admin_console)
        self._driver = admin_console.driver

    @PageService()
    def delete_entity(self, names, page_level=False):
        """
        Delete particular row entity
        Args:
            names              (String)     --        names of the entity to delete
            page_level         (Boolean)    --        if the action is on page level
        """
        if page_level:
            self.page_container.access_page_action('Delete')
        else:
            self.table.select_rows(names, search_for=True)
            self.table.access_toolbar_menu('Delete')
            self.dialog.click_submit()

    @PageService()
    def enable_entity(self, names, page_level=False):
        """
        Enable entity
        Args:
            names             (list)     --        name of the entity to delete
            page_level        (Boolean)  --        if the action is on page level
        """
        if page_level:
            self.page_container.access_page_action('Enable')
        else:
            self.table.select_rows(names)
            self.table.access_toolbar_menu('Enable')

    @PageService()
    def disable_entity(self, names, page_level=False):
        """
        Disable entity
        Args:
            names             (String)    --        name of the entity to delete
            page_level        (Boolean)   --        if the action is on page level
        """
        if page_level:
            self.page_container.access_page_action('Disable')
        else:
            self.table.select_rows(names)
            self.table.access_toolbar_menu('Disable')

    @PageService()
    def run_entity(self, names, wait_for_completion=True, page_level=False):
        """
        Run Entity
        Args:
            names            (String)     --        name of the entity to run
            wait_for_completion (Boolean) --        waits for completion
            page_level (Boolean)          --        if the action is on page level
        """
        if page_level:
            self.page_container.access_page_action('Run now')
        else:
            self.table.select_rows(names, search_for=True)
            self.table.access_toolbar_menu('Run now', wait_for_completion)

    @PageService()
    def edit_entity(self, page_level=False):
        """
        Edits the entity
        Args:
            page_level (Boolean)          --         if the action is on page level
        """
        if page_level:
            self.page_container.access_page_action('Edit')
        else:
            self.table.access_toolbar_menu('Edit')
