# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Send logs page on the AdminConsole

Class:

    SendLogs

Functions:

    disable_auto_upload()           -- disables auto upload option
    add_process_id()                -- adds the process id for new process dumps
    add_process_name()              -- adds the process name for new process dumps
    add_dump_interval()             -- adds the dump interval time for multiple dumps
    select_local_output()           -- selects local output
    select_network_output()         -- selects network output
    select_information()            -- select the information to be collected
    is_csdb_option_present()        -- checks if csdb option is present or not
    select_advanced()               -- selects the options in the advanced list
    select_index_trn_logs()         -- selects the index transaction logs with start and end job ids
    deselect_information()          -- deselects the options present in the information list
    deselect_advanced()             -- deselects the option present in the advanced list
    email()                         -- email notification configurations
    disable_email_notification()    -- disables email notification
    disable_self_email_notification -- disables emailing oneself for the notification
    enter_additional_jobs()         -- option to include additional job id
    submit()                        -- submits the sendlogs job

"""
from enum import Enum
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.Components.core import Checkbox
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.panel import RDropDown


class SendLogs:
    """ Class for Sendlogs page """

    class Informationlist(Enum):
        """ list of options available to select under information"""
        ESCALATION_NUMBER = "escalationNumberCheck"
        LOGS = "galaxyLogs"
        OS_LOGS = "osLogs"
        MACHINE_CONFIG = "machineInformation"
        ALL_USERS_PROFILE = "allUsersProfile"
        CSDB = "csDatabase"
        OTHER_DB = "otherDatabases"
        TSDB = "tsDatabase"
        LATEST_DB = "getLatestUpdates"

    class Advancedlist(Enum):
        """ list of options available to select under Advanced"""
        INDEX = "includeIndex"
        JOBS_RESULTS = "includeJobResults"
        PROC_DUMP = "crashDump"
        INDEX_TRANS = "actionLogs"
        HYPER_SCALE = "collectHyperScale"
        SCRUB_LOGFILES = "scrubLogFiles"
        USER_APP_LOGS = "collectUserAppLogs"
        RFC = "collectRFC"
        NEW_PROCESS_DUMP = "newProcessDump"
        MULTIPLE_DUMP = "multipleDump"
        DCDB = "includeDCDB"
        VCLOGS = "vCenterLogs"

    def __init__(self, admin_console):
        """ Initialize the base panel

        Args:
            admin_console: instance of AdminConsoleBase

        """
        self._driver = admin_console.driver
        self._admin_console = admin_console
        self._dropdown = RDropDown(self._admin_console)
        self._checkbox = Checkbox(self._admin_console)

    @WebAction(delay=0)
    def _enter_addtnl_recipients(self, addtnl_recepient):
        """Enter additional recipients"""
        rcpt = self._driver.find_element(By.XPATH, "//input[@class='additionalMailRecipients']")
        for each_recipient in addtnl_recepient:
            rcpt.send_keys(each_recipient + '\t')

    @WebAction(delay=0)
    def _enter_description(self, description):
        """Enter description"""
        desc = self._driver.find_element(By.XPATH, "//textarea")
        desc.send_keys(description)

    @WebAction(delay=2)
    def _click_submit(self):
        """click_submit"""
        xp = "//button[contains(@type, 'submit')]"
        self._admin_console.scroll_into_view(xp)
        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def _enter_user(self, user_name):
        """Enter user"""
        self._dropdown.search_and_select(user_name, id='to_usersAndGroupsList')
        self._admin_console.driver.find_element(By.XPATH, "//body").click()

    @WebAction()
    def _enter_user_cc(self, user_name):
        """Enter user"""
        self._dropdown.search_and_select(user_name, id='cc_usersAndGroupsList')
        self._admin_console.driver.find_element(By.XPATH, "//body").click()

    @WebAction()
    def _add_process_id(self, process_id):
        """
        Adds the process id on send logs menu for new process dump collection
        Args:
            process_id (str): process id of a process
        """
        self._checkbox.check(id='additionalLogsOrInfo')
        self._checkbox.check(id='newProcessDump')
        self._admin_console.fill_form_by_id('processIdForNewDump', process_id)

    @WebAction()
    def _add_escalation_number(self, escalation_number):
        """
        Adds the escalation number on the sendlogs page
        Args:
            escalation_number (str): escalation number
        """
        self._checkbox.check(id='escalationNumberCheck')
        self._admin_console.fill_form_by_id('escalationNumber', escalation_number)

    @WebAction()
    def _add_process_name(self, process_name):
        """
        Adds the process name on sendlogs menu for new process dump collection
        Args:
            process_name (str): process name of a process
        """
        self._checkbox.check(id='additionalLogsOrInfo')
        self._checkbox.check(id='newProcessDump')
        self._admin_console.fill_form_by_id('processIdForNewDump', process_name)

    @WebAction()
    def _add_dump_interval(self, interval_time):
        """
        Adds the dump interval time on the sendlogs menu
        Args:
            interval_time (int): interval duration between two dumps collection
        """
        self._checkbox.check(id='additionalLogsOrInfo')
        self._checkbox.check(id='newProcessDump')
        self._checkbox.check(id='multipleDump')
        self._admin_console.fill_form_by_id('dumpInterval', interval_time)

    @WebAction()
    def _enter_additional_jobs(self, job_id):
        """
                Sendlogs for multiple jobs
                Args:
                    job_id  (str) : backup job id
        """
        self._admin_console.fill_form_by_id('multiJobIds', job_id)

    @WebAction()
    def _switch_to_description_iframe(self):
        """ Switch the driver object to description iframe """
        iframe = self._admin_console.driver.find_element(By.CLASS_NAME, "k-iframe")
        self._admin_console.driver.switch_to.frame(iframe)

    @WebAction()
    def _switch_to_parent_frame(self):
        """Switch the driver object to window frame"""
        self._admin_console.driver.switch_to.parent_frame()

    @WebAction()
    def _enable_bold_text(self):
        """ enable bold text """

        bold_text_xpath = "//span[contains(@class, 'bold')]"
        self._admin_console.driver.find_element(By.XPATH, bold_text_xpath).click()

    @WebAction()
    def _populate_description_text(self, description_text):
        """
        Fill the description body with rich text content

        Args:
                description_text    (str): text content

        """
        self._enable_bold_text()
        self._switch_to_description_iframe()
        tag_element = self._driver.find_element(By.TAG_NAME, "p")
        tag_element.send_keys(description_text)
        self._switch_to_parent_frame()

    @WebAction()
    def _populate_description_link(self, description_link):
        """
        Fill the description body with rich text content

        Args:
                description_link    (str): hyperlink

        """
        self._switch_to_description_iframe()
        tag_element = self._admin_console.driver.find_element(By.TAG_NAME, "p")
        tag_element.send_keys(Keys.CONTROL + "A")
        self._switch_to_parent_frame()
        hyperlink_xpath = "//button[@title='Insert hyperlink']/span"
        self._admin_console.driver.find_element(By.XPATH, hyperlink_xpath).click()
        input_link = "//*[contains(@id, 'k-editor-link-url')]"
        self._admin_console.driver.find_element(By.XPATH, input_link).send_keys(description_link)
        text_link = "//*[contains(@id, 'k-editor-link-text')]"
        self._admin_console.driver.find_element(By.XPATH, text_link).send_keys("hyper link")
        insert_button = "//span[contains(text(), 'Insert')]"
        self._admin_console.driver.find_element(By.XPATH, insert_button).click()

    @WebAction()
    def _is_csdb_option_hidden(self):
        """checks if cs database option is hidden"""

        xp = f"//*[contains(@id, 'csDatabase')]"
        try:
            self._admin_console.driver.find_element(By.XPATH, xp)
        except NoSuchElementException:
            return True
        return False

    @PageService()
    def disable_auto_upload(self):
        """
        Disables auto upload
        """
        self._checkbox.uncheck(id='uploadLogsSelected')

    @PageService()
    def disable_email_notification(self):
        """
        Disables email notification
        """
        self._checkbox.uncheck(id='emailSelected')

    @PageService()
    def enter_additional_jobs(self, job_id=None):
        """
        Sendlogs for additional jobs

        Args:
                job_id    (str): job id of the additional job

        """
        self._enter_additional_jobs(job_id)

    @PageService()
    def add_process_id(self, process_id=None):
        """
        Adds the process id to get the new dumps from

        Args:
                process_id    (str): process id of the dump to be collected

        """
        self._add_process_id(process_id)

    @PageService
    def add_escalation_number(self, escalation_number):
        """
        Adds the escalation number on the sendlogs page

        Args:
                escalation_number (str): escalation number to be added
        """
        self._add_escalation_number(escalation_number)

    @PageService()
    def add_process_name(self, process_name=None):
        """
        Adds the process name to get the new dumps from

        Args:
              process_name   (str) : process name of the dump to be collected
        """
        self._add_process_name(process_name)

    @PageService()
    def add_dump_interval(self, interval_time=2):
        """
        Adds the interval time (in minutes) for the two dumps

        Args:
            interval_time (int) : dump interval in minutes (Default : 2)
        """
        self._add_dump_interval(interval_time)

    @PageService()
    def select_local_output(self, local_path=None):
        """
        Selects the local output
        Args:
            local_path  (str) : local path
        """
        self._checkbox.check(id='saveToFolderSelected')
        self._admin_console.select_radio(id='localPathRadio')
        self._admin_console.fill_form_by_id('pathInput', local_path)

    @PageService()
    def select_network_output(self, nw_path, nw_user, nw_pwd):
        """
        Selects the network output
        Args:
            nw_path     (str) :  N/w path
            nw_user     (str) :  N/w user name
            nw_pwd      (str) :  N/w password

        """
        self._checkbox.check(id='saveToFolderSelected')
        self._admin_console.select_radio(id='networkPathRadio')
        self._admin_console.fill_form_by_id('saveToNetworkDir', nw_path)
        self._admin_console.fill_form_by_id('username', nw_user)
        self._admin_console.fill_form_by_id('password', nw_pwd)

    @PageService()
    def select_information(self, information_list):
        """
        Args:
            information_list (list):  list from Informationlist enum
        """

        for each_info in information_list:
            self._checkbox.check(id=each_info.value)

    @PageService()
    def is_csdb_option_present(self):
        """
        checks if cs database option is present or not
        """
        return not self._is_csdb_option_hidden()

    @PageService()
    def select_advanced(self, advanced_list):
        """
         Args:
                advanced_list (list):  list from AdvancedList enum
        """
        self._checkbox.check(id='additionalLogsOrInfo')
        for each_info in advanced_list:
            self._checkbox.check(id=each_info.value)

    @PageService()
    def select_index_trn_logs(self, start_jobid, end_jobid):
        """
        Selecting the index transaction logs
        Args:
            start_jobid (str) : starting job id
            end_jobid   (str) : ending job id
        """
        if not self._checkbox.is_checked(id='additionalLogsOrInfo'):
            self._checkbox.check(id='additionalLogsOrInfo')
        if not self._checkbox.is_checked(id='actionLogs'):
            self._checkbox.check(id='actionLogs')
        self._admin_console.fill_form_by_id('actionLogsStartJobId', start_jobid)
        self._admin_console.fill_form_by_id('actionLogsEndJobId', end_jobid)

    @PageService()
    def deselect_information(self, information_list=[]):
        """
        Args:
            information_list (list):  list from Informationlist enum
        """
        for each_info in information_list:
            self._checkbox.uncheck(id=each_info.value)

    @PageService()
    def deselect_advanced(self, advanced_list=[]):
        """
        Args:
            advanced_list (list):  list from AdvancedList enum
        """
        self._checkbox.check(id='additionalLogsOrInfo')
        for each_info in advanced_list:
            self._checkbox.uncheck(id=each_info.value)

    @PageService()
    def disable_self_email_notification(self):
        """
        Disables email notification
        """
        self._checkbox.check(id='emailSelected')
        self._checkbox.uncheck(id='notifyMe')

    @PageService()
    def email(self, users, cc_users=None, subject=None, description_text=None,
              description_link=None):
        """
        email notification
        Args:
            users               (list) : user or user groups for notification
            cc_users            (list) : user or user groups for cc notification
            subject             (str)  : mail subject, default subject is populated in page
            description_text    (str)  : problem description
            description_link    (str)  : hyperlink in the description

        """
        self._checkbox.check(id='emailSelected')
        for each_user in users:
            self._enter_user(each_user)

        if cc_users is None:
            cc_users = []

        for each_user in cc_users:
            self._enter_user_cc(each_user)

        if subject:
            self._admin_console.fill_form_by_id('emailSubject', subject)
        if description_text:
            self._populate_description_text(description_text)
        if description_link:
            self._populate_description_link(description_link)

    @PageService()
    def submit(self):
        """
        Submits send logs jobs
        Returns:
            send logs Job id
        """
        self._click_submit()
        jobid = self._admin_console.get_jobid_from_popup()
        self._admin_console.wait_for_completion()
        return jobid
