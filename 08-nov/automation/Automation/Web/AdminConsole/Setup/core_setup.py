# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Commvault getting started page
Setup : This class provides methods for setup related operations

Setup
=====

    __click_more                -- Click on more accordion

    __get_solutions             -- Gets supported solutions from the page

    __get_banner_text           -- Gets the banner text on page

    select_get_started()        -- To select the lets get started button

    configure_email()           -- To configure email

    add_storage_pool()          -- To add storage pool

    create_server_backup_plan() -- To create a sever backup plan

    core_setup_status()         -- To check if the core setup is completed or not

    supported_solutions()       -- Lists supported solutions on guided setup

    has_owned_storage()         -- Returns if infrastructure types is owned or not

    **Note** using Admin console default values for filled web elements

"""

from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from selenium.webdriver.common.by import By


class Setup:
    """
    Class for commvault's Setup page

    """
    def __init__(self, admin_console: AdminConsole):
        """Initializer to move the setup class to use AdminConsole class"""
        self.admin_console = admin_console

    @PageService()
    def select_get_started(self):
        """
        To select the lets get started button

        """
        self.admin_console.select_hyperlink('get started')

    @PageService(hide_args=True)
    def configure_email(
            self,
            smtp_server='smtp.commvault.com',
            smtp_port='25',
            sender_email=None,
            sender_name=None,
            authentication=False,
            username=None,
            password=None,
            encryption=None):
        """
        To configure email

        Args:
            smtp_server     (str)   -- SMTP server to send mails

            smtp_port       (str)   -- Port for the smtp server
                                        default: 25

            sender_email    (str)   -- Email address of the sender

            sender_name     (str)   -- name of the sender

            authentication  (bool)  -- set to True if authentication is enabled

            username        (str)   -- Username for authentication

            password        (str)   -- Password for the authentication

            encryption      (str)   -- Encrytion algorithm to be used

        """
        self.admin_console.fill_form_by_id('smtpServer', smtp_server)
        self.admin_console.fill_form_by_id('smtpPort', smtp_port)

        # Its automatically populated
        if sender_email:
            self.admin_console.fill_form_by_id('senderEmail', sender_email)

        self.admin_console.fill_form_by_id('senderName', sender_name)

        # To select authentication checkbox and to fill the username and password
        if authentication and username and password:
            self.admin_console.checkbox_select('authentication')
            self.admin_console.fill_form_by_id('username', username)
            self.admin_console.fill_form_by_id('password', password)
            self.admin_console.fill_form_by_id('confirmPassword', password)

        # To set encryption
        if encryption:
            self.admin_console.select_value_from_dropdown('encryption', encryption)

        self.admin_console.submit_form()

        # To check for errors
        self.admin_console.check_error_message()

    @PageService(hide_args=True)
    def add_storage_pool(
            self,
            pool_name=None,
            media_agent=None,
            username=None,
            password=None,
            path=None,
            partition_path=None):
        """
        To add storage pool

        Args:
            pool_name       (str)   -- Name of the storage pool to be created

            media_agent     (str)   -- media agent to be selected, by default it is selected

            username        (str)   -- Username for the network path

            password        (str)   -- Password for the network path

            path            (str)   -- Path to be selected as storage

            partition_path  (str)   -- DDB partition path

        """
        self.admin_console.fill_form_by_id('storagePoolName', pool_name)

        # By default media agent for the commcell machine is created and selected here
        if media_agent:
            self.admin_console.select_value_from_dropdown('mediaAgent', media_agent)

        if username and password:
            self.admin_console.select_radio('Network Path')
            self.admin_console.fill_form_by_id('userName', username)
            self.admin_console.fill_form_by_id('password', password)

        self.admin_console.fill_form_by_id('mountPath', path)
        self.admin_console.fill_form_by_id('partitionPath', partition_path)

        self.admin_console.click_button('Save')

        # To check for error messages
        self.admin_console.check_error_message()

    @PageService()
    def create_server_backup_plan(self):
        """
        To create a sever backup plan

        """
        self.admin_console.submit_form()

        # To check for error messages
        self.admin_console.check_error_message()

    @PageService()
    def core_setup_status(self):
        """
        Checks the status of the core setup completion.

        Returns:
            True / False based on the setup completion

        """
        if self.admin_console.check_if_entity_exists('xpath', '//div[@data-ng-if="coreSetupCompleted"]'):
            return True
        else:
            return False

    @WebAction()
    def __click_more(self):
        """Click on more accordion"""
        more_accordion = self.admin_console.driver.find_elements(By.XPATH, "//a[@data-ng-if='showMoreSolutionsButton']")
        if more_accordion:
            more_accordion[0].click()

    @WebAction()
    def __get_solutions(self):
        """Gets supported solutions from the page"""
        solns = self.admin_console.driver.find_elements(By.XPATH, "//div[@class='tab-content']"
                                                                 "//div[contains(@class, 'active')]"
                                                                 "//div[contains(@class, 'panel-body')]//h3")
        return [elem.text for elem in solns if elem.is_displayed()]

    @WebAction()
    def get_banner_text(self):
        """Gets the banner text on page"""
        text = self.admin_console.driver.find_elements(
            By.XPATH, "//div[contains(@id, 'SETUP_BANNER_HEADER')]//span")
        if text:
            return text[0].text.split("\n")

        return ""

    @PageService()
    def supported_solutions(self):
        """ Lists supported solutions on guided setup """
        self.__click_more()
        solns_list = self.__get_solutions()
        return solns_list

    @PageService()
    def has_owned_storage(self):
        """ Returns if infrastructure types is owned or not """
        text = self.get_banner_text()

        if text:
            return "Let's get started with configuring your storage" in text

        return False


class SetupContainer:
    """
    Class for commvault's Guided Setup page Quick tasks

    """
    def __init__(self, admin_console: AdminConsole):
        """Initializer to move the setup class to use AdminConsole class"""
        self.__admin_console = admin_console
        self.__navigator = self.__admin_console.navigator
        self.__plans = Plans(self.__admin_console)
        self.plan_name = None
        self.sec_copy_name = None
        self.storage = None
        self.backup_data = None
        self.backup_day = None
        self.backup_duration = None
        self.rpo_hours = None
        self.allow_override = None
        self.snapshot_options = None
        self.database_options = None

    @WebAction()
    def __click_quick_task(self, label):
        """Click a quick task container"""
        xpath = f"//div[@class='app-setup-container']//*[contains(text(),'{label}')]"
        self.__admin_console.click_by_xpath(xpath)
        self.__admin_console.wait_for_completion()

    @PageService()
    def create_server_plan_from_guided_setup(self):
        """
        Creates Plan from getting started page (guided setup)

        Args:
            plan_name (string): Name of the plan to be created

            storage (dict) : Dict containing storage attributes for admin console
                Eg. - self._storage = {'pri_storage': None,
                         'pri_ret_period':'30',
                         'sec_storage': None,
                         'sec_ret_period':'45',
                         'ret_unit':'Day(s)'}

            rpo (list): List of schedule properties
                Eg. - rpo_dict = [{
                            'BackupType' : 'Full',
                            'Agents'     : 'Databases',
                            'Frequency'  : '1',
                            'FrequencyType' : 'Day(s)',
                            'StartTime'  : '10:30 pm'
                        }, {
                            'BackupType' : 'Incremental',
                            'Agents'     : 'All agents',
                            'Frequency'  : '10',
                            'FrequencyType' : 'Month(s)',
                            'StartTime'  : '05:30 pm'
                        }]

            allow_override (dictionary): dictionary containing values for Override parameters
                Eg. - allow_override = {"Storage_pool": "Override required",
                                        "RPO": "Override optional"}

            backup_day (dictionary): dictionary containing values of backup days for backup
                window
                Eg. - backup_day = dict.fromkeys(['1', '2', '3'], 1)

            backup_duration (dictionary): dictionary containing values of excluded backup
                time for backup window
                Eg. - backup_duration = dict.fromkeys(['2', '3', '4', '5'], 1)

            backup_data (Dictionary): Dictionary with data to be selected
                for backup or excluded from backup
                Eg. - backup_data = {'file_system':["Mac", "Unix", "Windows"],
                                    'content_backup':["Content Library"],
                                    'content_library':['Content Library', 'GoogleDrive'],
                                    'custom_content':None,
                                    'exclude_folder':['Content Library', 'Documents'],
                                    'exclude_folder_library':['DropBox', 'EdgeDrive', 'Executable']
                                    'exclude_folder_custom_content':None}

            snapshot_options (dictionary) : dictionary containing values for snapshot parameters
                Eg. - snapshot_options = {'snap_recovery_points':'5',
                                          'Enable_backup_copy':True,
                                          'sla_hours':'5',
                                          'sla_minutes':'20'}

            database_options (dictionary) : dictionary containing values for databse parameters
                Eg. - database_options = {'sla_hours':'5',
                                          'sla_minutes':'20'}

            sec_copy_name (string): Name of the secondary copy

        Returns:
            None
        """
        self.__navigator.navigate_to_getting_started()
        self.__click_quick_task('Create a server backup plan')
        self.__plans.create_server_plan(
            self.plan_name,
            self.storage,
            self.rpo_hours,
            self.allow_override,
            self.backup_day,
            self.backup_duration,
            self.backup_data,
            self.snapshot_options,
            self.database_options,
            sec_copy_name=self.sec_copy_name,
            guided=True)

