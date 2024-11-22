from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Inventory Manager
details page.


Classes:

    InventoryManagerDetails() ---> InventoryManager() ---> GovernanceApps() ---> object()


InventoryManagerDetails  --  This class contains all the methods for action in
    Inventory Manager details page and is inherited by other classes to perform
    GDPR related actions

    Functions:

    _select_add_asset_type()          --  Selects the asset type to be added
    get_assets()     -       -- Returns all the assets from the inventory details page
    add_asset_name_server()      -- Adds name server asset from Inventory details page
    wait_for_asset_status_completion()   -- Waits for the asset scan status completion
    select_overview()                    -- Clicks on the Overview link
    select_details()                    -- Clicks on the Details link
    __convert_list_to_string()         -- Convert list to a comma separated string
    __check_schedule()                 -- Checks for schedule
    check_if_schedule_is_assigned()    -- Checks if there is any existing schedule associated
    remove_schedule()                  -- Removes any schedule associated
    select_add_or_edit_schedule()      -- Selects either add or edit schedule
    add_edit_schedule()                -- Add or Edit the schedule
    __one_time_schedule()              -- Adds a one time schedule
    __daily_schedule()                 -- Adds daily schedule
    __weekly_schedule()                -- Adds a weekly schedule
    __monthly_schedule()               -- Adds a monthly schedule
    get_last_collection_time()         -- Returns the last collection time for a given asset
    __get_exceptions_toggle_check_element() -- Gets Exceptions Toggle Check WebElement
    __get_exceptions_toggle_element()  -- Gets Exceptions Toggle WebElement
    is_exceptions_toggle_enabled()     -- Checks if exceptions toggle is enabled
    enable_exceptions_toggle()         -- Enables the exceptions toggle bar if disabled
    disable_exceptions_toggle()        -- Disables the exceptions toggle bar if enabled
    get_schedule_frequency()           -- Returns the current selected schedule frequency
    add_exception()                    -- Adds an exception to the current schedule
    share_inventory()                  -- Shares inventory with the users for roles specified
"""

import re
import time

from Web.AdminConsole.Components.core import CalendarView

from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo, Security
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.GovernanceAppsPages.InventoryManager import \
    InventoryManager
from Web.Common.page_object import PageService, WebAction


class InventoryManagerDetails(InventoryManager):
    """
     This class contains all the methods for action in Inventory Manager details page
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
        self.__rpanelinfo = RPanelInfo(self.__admin_console, title="Configuration")
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__modal_dialog = ModalDialog(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__security = Security(self.__admin_console)
        self.__calendar = CalendarView(self.__admin_console)
        self.panel_details = None
        self.schedule_options = None

    @WebAction()
    def _select_add_asset_type(self, asset_type):
        """
            Selects the asset type to be added

            Args:
                asset_type(str)  - Type of the asset to be selected
                Values:
                    "Name server",
                    "File server"

            Raise:
                Exception if invalid asset type provided
        """

        self.log.info('Clicking on Add button')
        self.__rtable.access_toolbar_menu(
            self.__admin_console.props['label.assets.add'])
        self.__admin_console.wait_for_completion()
        self.log.info(f'Selecting {asset_type} asset option')
        if re.search(self.__admin_console.props['label.assets.nameserver'], str(asset_type), re.IGNORECASE):
            self.__rtable.access_menu_from_dropdown(
                self.__admin_console.props['label.assets.nameserver'])
        elif re.search("File server", str(asset_type), re.IGNORECASE):
            self.__rtable.access_menu_from_dropdown(
                self.__admin_console.props['label.assets.fileserver'])
        else:
            raise Exception(f"Invalid asset type: {asset_type}")
        self.__admin_console.wait_for_completion()

    @WebAction()
    def get_assets(self):
        """
        Returns all the list of assets

            Return:
                List of assets

        """
        self.__admin_console.access_tab(self.__admin_console.props['label.assets'])
        assets_list = self.__rtable.get_column_data(self.__admin_console.props['label.name'])
        return assets_list

    @WebAction()
    def add_asset_name_server(self, name_server):
        """
        Adds name server asset

            Args:
                name_server (str)  - Name of the domain server

            Raise:
                Exception if inventory creation failed
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.assets'])
        self._select_add_asset_type(self.__admin_console.props['label.assets.nameserver'])
        self.log.info("Selecting name servers")
        name_servers = self.__rdropdown.get_values_of_drop_down(
            "IdentityServersDropdown")
        name_server_obtained = False
        if name_server.lower() in (name.lower() for name in name_servers):
            name_server_obtained = True
        if name_server_obtained:
            self.log.info(f"Selecting the asset: {name_server}")
            self.__rdropdown.select_drop_down_values(
                values=[name_server], drop_down_id="IdentityServersDropdown")
            self.log.info("Submitting the form")
            self.__rmodal_dialog.click_submit()
            self.__admin_console.check_error_message()

        else:
            raise Exception(f"Nameserver: {name_server} not found")

    @WebAction()
    def wait_for_asset_status_completion(self, asset_name, timeout=20):
        """
        Waits for the asset scan status completion

            Args:
                asset_name (str)  - Name of the asset
                timeout     (int)   --  minutes
                    default: 20

            Returns:
                bool    -   boolean specifying if the asset scan had finished or not
                    True    -   if the asset scan had finished successfully

                    False   -   if the asset scan was not completed within the timeout

        """
        self.__admin_console.access_tab(self.__admin_console.props['label.assets'])
        status = False
        start_time = int(time.time())
        current_time = start_time
        completion_time = start_time + timeout * 60

        while completion_time > current_time:
            self.log.info("Refreshing the page")
            self.__rtable.reload_data()
            self.__admin_console.wait_for_completion()
            self.log.info(f'Obtaining the asset status of: {asset_name}')
            assets = self.__rtable.get_column_data(
                self.__admin_console.props['label.name'])
            assets_status = self.__rtable.get_column_data(
                self.__admin_console.props['label.status'])
            current_status = dict(zip(assets, assets_status))[asset_name]
            self.log.info(f'Asset status obtained is: {current_status}')
            if re.search(self.__admin_console.props['label.taskDetail.status.Completed'],
                         current_status, re.IGNORECASE):
                status = True
                break
            time.sleep(30)
            current_time = int(time.time())
        return status

    @WebAction()
    def select_overview(self, name):
        """
        Clicks on the Overview link
        """
        self.__rtable.access_link(name)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def select_details(self, name):
        """
        Clicks on the Details link
        """
        self.__rtable.access_action_item(
            name, self.__admin_console.props['label.details'])
        self.__admin_console.wait_for_completion()

    @staticmethod
    def __convert_list_to_string(values_list):
        '''
        Convert list to a comma separated string
            Args:
                values_list (List)  - List of string values to be converted
            Example:
                values_list = ['Second','Third']
                returns:
                    'Second,Third'
        '''
        return_text = ''
        for value in values_list:
            return_text += f",{value}"
        return return_text[1:]

    @PageService()
    def __check_schedule(self):
        '''
        Checks for schedule
        Returns True if present, False if not
        '''
        config_details = self.__rpanelinfo.get_details()
        string_pattern = f" {int(self.schedule_options['hours'])}:{self.schedule_options['mins']} " +\
            f"{self.schedule_options['session']}"
        if self.schedule_options['frequency'] == 'One time':
            temp = (f" {self.schedule_options['hours']}:{self.schedule_options['mins']} "
                    f"{self.schedule_options['session']}")
            string_pattern = f"One time on {self.schedule_options['month'][:3]} " +\
                f"{int(self.schedule_options['date'])}"+temp
        elif self.schedule_options['frequency'] == 'Daily':
            if int(self.schedule_options['repeat']) == 1:
                string_pattern = "Every day at"+string_pattern
            else:
                string_pattern = f"Every {self.schedule_options['repeat']} days at"+string_pattern
        elif self.schedule_options['frequency'] == 'Weekly':
            days_text = self.__convert_list_to_string(
                self.schedule_options['days'])
            if int(self.schedule_options['repeat']) == 1:
                string_pattern = f"Every week on {days_text} at"+string_pattern
            else:
                string_pattern = f"Every {self.schedule_options['repeat']} weeks on {days_text} at" + string_pattern
        elif self.schedule_options['frequency'] == 'Monthly':
            if int(self.schedule_options['repeat']) == 1:
                temp_str = "Every month"
            else:
                temp_str = f"Every {self.schedule_options['repeat']} months"
            string_pattern = temp_str + \
                f" on day {self.schedule_options['onday']} at"+string_pattern
        if 'exceptionweeks' in self.schedule_options:
            string_pattern += '\n.*\nexcept\nOn '
            string_pattern += self.__convert_list_to_string(
                self.schedule_options['exceptionweeks'])
            string_pattern += ' '
            string_pattern += self.__convert_list_to_string(
                self.schedule_options['exceptiondays'])
        elif 'exceptiondays' in self.schedule_options:
            string_pattern += '\nExcept On days: '
            string_pattern += self.__convert_list_to_string(
                self.schedule_options['exceptiondays'])
            string_pattern += " of each month"
        self.log.info(f"Matching with string pattern: '{string_pattern}'")
        if re.search(string_pattern,
                     config_details[self.__admin_console.props['label.schedule']],
                     re.IGNORECASE):
            return True
        return False

    @PageService()
    def check_if_schedule_is_assigned(self, default_schedule=False, schedule_options=None):
        """
        Checks if there is any existing schedule associated
            Returns: True if schedule is assigned
            Args:
                default (Bool)  - To check for default schedule
                schedule_options (dict)  -- schedule options to check for
                Usage:
                    * Sample dict for one time schedule
                        {
                            'frequency': 'One time',
                            'year': '2020',
                            'month': 'January',
                            'date': '17',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                    * Sample dict for daily schedule
                        {
                            'frequency': 'Daily',
                            'repeat': '1',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                    * Sample dict for weekly schedule
                        {
                            'frequency': 'Weekly',
                            'repeat': '1',
                            'days': ['Monday','Wednesday'],
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                    * Sample dict for monthly schedule
                        {
                            'frequency': 'Monthly',
                            'repeat': '1',
                            'onday': '31',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                        or
                        {
                            'frequency': 'Monthly',
                            'repeat': '1',
                            'customweeks': 'First',
                            'customdays': 'Saturday',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
        """
        try:
            self.__admin_console.access_tab(self.__admin_console.props['label.details'])
        except Exception as e:
            self.log.error("Details tab not found trying Configurations")
            self.__admin_console.access_tab(self.__admin_console.props['label.configuration'])
        config_details = self.__rpanelinfo.get_details()
        if schedule_options:
            return self.__check_schedule()
        if default_schedule:
            if not re.search('Every day at 12:00 AM',
                             config_details[self.__admin_console.props['label.schedule']],
                             re.IGNORECASE):
                return False
        else:
            if re.search(self.__admin_console.props['info.notAssigned'],
                         config_details[self.__admin_console.props['label.schedule']]):
                return False
            elif re.search(self.__admin_console.props['label.planBasedSchedule'],
                           config_details[self.__admin_console.props['label.schedule']]):
                return False
        return True

    @PageService()
    def remove_schedule(self):
        """
        Removes any schedule associated
        """
        try:
            self.__admin_console.access_tab(self.__admin_console.props['label.details'])
        except Exception as e:
            self.log.error("Details tab not found trying Configurations")
            self.__admin_console.access_tab(self.__admin_console.props['label.configuration'])
        self.select_add_or_edit_schedule()
        self.__admin_console.click_button(
            self.__admin_console.props['label.delete'])
        self.__rmodal_dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def select_add_or_edit_schedule(self):
        """
        Selects either add or edit schedule based on whatever is displayed
        """
        try:
            self.__admin_console.access_tab(self.__admin_console.props['label.details'])
        except Exception as e:
            self.log.error("Details tab not found trying Configurations")
            self.__admin_console.access_tab(self.__admin_console.props['label.configuration'])
        try:
            self.driver.find_element(By.XPATH, "//div[@id='InventorySchedule']//button").click()
        except Exception as e:
            self.log.error("Inventory schedule not found trying Project schedule")
            self.driver.find_element(By.XPATH, "//div[@id='schedule']//button").click()

    @PageService()
    def add_edit_schedule(self, schedule_options):
        """
        Add or Edit the schedule
            Args:
                schedule_options (dict)  -- schedule options to create or edit a schedule
                Usage:
                    * Sample dict for one time schedule
                        {
                            'frequency': 'One time',
                            'year': '2020',
                            'month': 'January',
                            'date': '17',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                    * Sample dict for daily schedule
                        {
                            'frequency': 'Daily',
                            'repeat': '1',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                    * Sample dict for weekly schedule
                        {
                            'frequency': 'Weekly',
                            'repeat': '1',
                            'days': ['Monday','Wednesday'],
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                    * Sample dict for monthly schedule
                        {
                            'frequency': 'Monthly',
                            'repeat': '1',
                            'onday': '31',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                        or
                        {
                            'frequency': 'Monthly',
                            'repeat': '1',
                            'customweeks': 'First',
                            'customdays': 'Saturday',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                    * Sample dict for schedule exception options
                        {
                            'exceptiondays': ['1','22']
                        }
                        or
                        {
                            'exceptionweeks': ['First','Last'],
                            'exceptiondays': ['Monday','Saturday']
                        }
        """
        try:
            self.__admin_console.access_tab(self.__admin_console.props['label.details'])
        except Exception as e:
            self.log.error("Details tab not found trying Configurations")
            self.__admin_console.access_tab(self.__admin_console.props['label.configuration'])
        self.schedule_options = schedule_options
        self.select_add_or_edit_schedule()
        if self.schedule_options['frequency'] == 'One time':
            self.__one_time_schedule()
        if self.schedule_options['frequency'] == 'Daily':
            self.__daily_schedule()
        elif self.schedule_options['frequency'] == 'Weekly':
            self.__weekly_schedule()
        elif self.schedule_options['frequency'] == 'Monthly':
            self.__monthly_schedule()
        if 'exceptiondays' in self.schedule_options:
            self.add_exception(self.schedule_options)
        else:
            self.__rmodal_dialog.click_button_on_dialog(self.__admin_console.props['action.save'])
            self.__admin_console.check_error_message()

    @PageService()
    def __one_time_schedule(self):
        '''
        Adds a one time schedule
            Args:
                schedule_options (dict)  -- schedule options to create or edit a one time schedule
                Usage:
                    * Sample dict for schedule options
                        {
                            'year': '2020',
                            'month': 'January',
                            'date': '17',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
        '''
        self.__rdropdown.select_drop_down_values(
            drop_down_id="scheduleFrequency", values=[self.__admin_console.props['option.oneTime']])
        self.driver.find_element(By.XPATH, f"//div[@id='day-{int(self.schedule_options['date'])}-btn']").click()
        time_element = self.driver.find_element(By.XPATH, "//div[@id='scheduleTime']//input")
        time_element.click()
        time_element.send_keys(self.schedule_options['hours'])
        time_element.send_keys(self.schedule_options['mins'])
        time_element.send_keys(self.schedule_options['session'])

    @PageService()
    def __daily_schedule(self):
        '''
        Adds daily schedule
            Args:
                schedule_options (dict)  -- schedule options to create or edit a one time schedule
                Usage:
                    * Sample dict for schedule options
                        {
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM',
                            'repeat': '1',
                        }
        '''
        self.__rdropdown.select_drop_down_values(
            drop_down_id="scheduleFrequency", values=[self.__admin_console.props['option.daily']])
        time_element = self.driver.find_element(By.XPATH, "//div[@id='scheduleTime']//input")
        time_element.click()
        time_element.send_keys(self.schedule_options['hours'])
        time_element.send_keys(self.schedule_options['mins'])
        time_element.send_keys(self.schedule_options['session'])
        self.__admin_console.fill_form_by_id(
            'duration', self.schedule_options['repeat'])

    @PageService()
    def __weekly_schedule(self):
        '''
        Adds a weekly schedule
            Args:
                schedule_options (dict)  -- schedule options to create or edit a weekly schedule
                Usage:
                    * Sample dict for schedule options
                        {
                            'repeat': '1',
                            'days': ['Monday','Wednesday'],
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
        '''
        self.__rdropdown.select_drop_down_values(
            drop_down_id="scheduleFrequency", values=[self.__admin_console.props['option.weekly']])
        time_element = self.driver.find_element(By.XPATH, "//div[@id='scheduleTime']//input")
        time_element.click()
        time_element.send_keys(self.schedule_options['hours'])
        time_element.send_keys(self.schedule_options['mins'])
        time_element.send_keys(self.schedule_options['session'])
        self.__rdropdown.select_drop_down_values(
            drop_down_id="daysOfWeek", values=self.schedule_options['days'])
        self.__admin_console.fill_form_by_id(
            'duration', self.schedule_options['repeat'])

    @PageService()
    def __monthly_schedule(self):
        '''
        Adds a monthly schedule
            Args:
                schedule_options (dict)  -- schedule options to create or edit a monthly schedule
                Usage:
                    * Sample dict for schedule options
                        {
                            'repeat': '1',
                            'onday': '31',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
                        or
                        {
                            'repeat': '1',
                            'customweeks': 'First',
                            'customdays': 'Saturday',
                            'hours': '03',
                            'mins': '45',
                            'session': 'PM'
                        }
        '''
        self.__rdropdown.select_drop_down_values(
            drop_down_id="scheduleFrequency", values=[self.__admin_console.props['option.monthly']])
        time_element = self.driver.find_element(By.XPATH, "//div[@id='scheduleTime']//input")
        time_element.click()
        time_element.send_keys(self.schedule_options['hours'])
        time_element.send_keys(self.schedule_options['mins'])
        time_element.send_keys(self.schedule_options['session'])
        if 'onday' in self.schedule_options:
            self.__admin_console.fill_form_by_name(
                'dayOfMonth', self.schedule_options['onday'])
        else:
            self.__admin_console.select_radio(id="relativeInputs")
            self.__rdropdown.select_drop_down_values(
                drop_down_id="weekOfMonth", values=[self.schedule_options['customweeks']])
            self.__rdropdown.select_drop_down_values(
                drop_down_id="dayOfWeek", values=[self.schedule_options['customdays']])
        self.__admin_console.fill_form_by_id(
            'duration', self.schedule_options['repeat'])

    @PageService()
    def get_last_collection_time(self, asset_name):
        """
        Returns the last collection time(str) for a given asset
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.assets'])
        assets = self.__rtable.get_column_data(
            self.__admin_console.props['label.name'])
        last_completion_times = self.__rtable.get_column_data(
            self.__admin_console.props['label.lastActive'])
        return dict(zip(assets, last_completion_times))[asset_name]

    @PageService()
    def share_inventory(self, associations):
        """
        Shares Inventory with a given username
        Args:
             associations (dict) : dictionary containing user and role pairs
                Eg. -> associations = {
                                        'User1' : ['View'],
                                        'User2': ['View', 'Edit']
                                      }
        """
        self.__security.edit_security_association(associations, add=True)

    @WebAction()
    def __get_exceptions_toggle_check_element(self):
        """ Gets Exceptions Toggle Check WebElement

        Returns : toggle check WebElement

        """
        return self.driver.find_element(By.XPATH, 
            "//*[@id='addScheduleForm']//div[contains(@class,'cv-accordion-header')]")

    @WebAction()
    def __get_exceptions_toggle_element(self):
        """ Gets Exceptions Toggle WebElement

        Returns : toggle WebElement

        """
        return self.driver.find_element(By.XPATH, 
            "//*[@id='addScheduleForm']//div[contains(@class,'cv-material-toggle cv-toggle')]")

    @WebAction()
    def is_exceptions_toggle_enabled(self):
        """ Checks if exceptions toggle is enabled

        Returns (bool) : True if toggle is enabled

        """
        element = self.__get_exceptions_toggle_check_element()
        if 'expanded' in element.get_attribute('class'):
            return False
        return True

    @PageService()
    def enable_exceptions_toggle(self):
        """ Enables the exceptions toggle bar if disabled """
        self.__admin_console.driver.find_element(By.XPATH, "//span[contains(text(),'Exceptions')]").click()

    @PageService()
    def disable_exceptions_toggle(self):
        """ Disables the exceptions toggle bar if enabled """
        if self.is_exceptions_toggle_enabled():
            self.__get_exceptions_toggle_element().click()
            self.__admin_console.wait_for_completion()

    @WebAction()
    def get_schedule_frequency(self):
        """Returns the current selected schedule frequency"""
        return self.driver.find_element(By.XPATH, 
            '//*[@id="scheduleFrequency"]//div[contains(@class,"buttonLabel")]').text

    @PageService()
    def add_exception(self, schedule_options):
        '''
        Adds an exception to the current schedule
            Args:
                schedule_options (dict)  -- schedule options to create or edit a weekly schedule
                Usage:
                    * Sample dict for schedule exception options
                        {
                            'exceptiondays': ['1','22']
                        }
                        or
                        {
                            'exceptionweeks': ['First','Last'],
                            'exceptiondays': ['Monday','Saturday']
                        }
        '''
        try:
            self.__admin_console.access_tab(self.__admin_console.props['label.details'])
        except Exception:
            self.log.error("Details tab not found trying Configurations")
            self.__admin_console.access_tab(self.__admin_console.props['label.configuration'])
        exception_dialog = RModalDialog(self.__admin_console, title="Exceptions")
        self.schedule_options = schedule_options
        self.enable_exceptions_toggle()
        if 'exceptionweeks' in self.schedule_options:
            self.__admin_console.select_radio('weekInMonthRadio')
            self.__rdropdown.select_drop_down_values(
                drop_down_id="weekInMonth", values=self.schedule_options['exceptionweeks'])
            self.__rdropdown.select_drop_down_values(
                drop_down_id="dayInWeek", values=self.schedule_options['exceptiondays'])
        else:
            self.__admin_console.select_radio('dayInMonthRadio')
            self.__rdropdown.select_drop_down_values(
                drop_down_id="dayInMonth", values=self.schedule_options['exceptiondays'])
        self.__admin_console.click_button('Add exception')
        exception_dialog.click_save_button()
        self.__admin_console.check_error_message()
        self.__rmodal_dialog.click_button_on_dialog(self.__admin_console.props['action.save'])
