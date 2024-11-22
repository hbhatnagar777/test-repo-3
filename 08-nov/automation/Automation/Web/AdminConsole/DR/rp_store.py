# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
specific RP or on RP store page of the AdminConsole
"""
from selenium.webdriver.common.by import By
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import (RDropDown, RPanelInfo)
from Web.AdminConsole.Components.browse import RContentBrowse
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.exceptions import CVWebAutomationException


class RPStores:
    """Class for overview tab of the group details page"""

    def __init__(self, admin_console):
        self.__admin_console = admin_console

        self.__modal_panel = RPanelInfo(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__browse = RContentBrowse(admin_console)
        self.__table = Rtable(self.__admin_console)
        self.__dropdown = RDropDown(self.__admin_console)

        self.__admin_console.load_properties(self, unique=True)
        self.__label = self.__admin_console.props[self.__class__.__name__]

    @PageService()
    def goto_rpstore(self, name):
        """ Get Rp store details
        Args:
            name    (str): Specify the name of teh rp store
        """
        self.__table.access_link(name)

    @PageService()
    def configure_rpstore(self, is_local):
        """
        Navigate to RP store configuration page
        Args:
            is_local (bool): Whether to open the local RP store configuration page(True)
                             or the network RP store configuration page(False)
        """
        rpstore_creation = RConfigureRPStore(self.__admin_console)
        menu_id = (self.__label['label.local']
                   if is_local
                   else self.__label['label.network'])
        self.__table.access_menu_from_dropdown(menu_id=menu_id,
                                               label=self.__label['label.addRPStore'])
        return rpstore_creation

    @PageService()
    def create_recovery_store(self, name, media_agent, max_size, path, path_type='',
                              path_username=None, path_password=None, peak_interval=None):
        """
        Creates an rp store with specified arguments
        Args:
            name            (str): name of the recovery point store
            media_agent     (str): name of the media agent on which the store will reside on
            max_size        (int): the maximum size of the recovery point store in GB
            path            (str): the path at which the store will be present
            path_type       (str): the path type as 'Local path' or 'Network path'
            path_username   (str): the path access username, only for network path
            path_password   (str): the path access password, only for network path
            peak_interval  (dict): the intervals at which recovery point store is marked at peak
                Must be a dict of keys as days, and values as list of date time ids(0-23)
        """
        rpstore_creation = self.configure_rpstore(is_local=path_type == self.__label['Network_Path'])
        rpstore_creation.set_rp_store_name(name)
        rpstore_creation.select_media_agent(media_agent)
        rpstore_creation.set_maximum_size(max_size)
        if path_type == self.__label['Local_Path']:
            rpstore_creation.browse_path()

        self.__admin_console.fill_form_by_name('rpStoreName', name)
        self.__dropdown.select_drop_down_values(values=[media_agent], drop_down_id='mediaAgent')
        self.__admin_console.fill_form_by_name("maxThreshold", max_size)

        rpstore_creation.browse_path(path)
        if path_type == self.__label['Network_Path']:
            rpstore_creation.set_username_and_password(path_username, path_password)

        if peak_interval:
            rpstore_creation.edit_peak_interval(peak_interval)

        rpstore_creation.save()

    @PageService()
    def delete_rpstore(self, rpstore_name):
        """
        Delete the specified RP store
        Args:
            rpstore_name        (str): Specify the name of the rp store that is to be deleted
        """
        self.__table.access_action_item(rpstore_name, self.__label["action.delete"])
        self.__dialog.click_submit()

    @PageService()
    def get_all_rpstores(self):
        """
        Get all the names of RP store
        return     (lst):  Returns a list of all the rp store names
        """
        rpstore_list = self.__table.get_column_data(self.__label['label.name'])
        return rpstore_list


class RpstoreOperations:

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self.__admin_console = admin_console

        self.__modal_panel = RPanelInfo(admin_console)
        self.__admin_console.load_properties(self, unique=True)
        self.__label = self.__admin_console.props[self.__class__.__name__]
        self.__table = Rtable(self.__admin_console)

    @WebAction()
    def __verify_is_field_disabled(self, value):
        """
        Verifies the disabled field on edit storage
        Args:
            value            (str): Value of the input type
        return              (Bool): True if disabled else False
        """
        if self.__admin_console.check_if_entity_exists("xpath", f"//input[@value=' {value}']"):
            return bool(self.__admin_console.driver.find_element(By.XPATH, f"//input[@value=' {value}']")
                        .get_attribute('disabled'))

    @WebAction()
    def __click_action_menu(self):
        """Clicks the action menu button for the first row in the table"""
        self.__admin_console.driver.find_element(By.XPATH, "//*[contains(@class, 'cv-permitted-actions')]").click()

    @WebAction()
    def __click_action(self, action_name):
        """Clicks on the action name provided"""
        self.__admin_console.driver.find_element(By.XPATH, "//*[contains(@class, 'cv-permitted-actions')]"
                                                          "//li/a[contains(text(), '{}')]".format(action_name)).click()

    @WebAction()
    def __get_rp_list(self):
        """Get the rp list present currently"""
        self.__admin_console.select_value_from_dropdown('recoveryType', "Recovery point time")
        dropdown_values_xpath = '//select[@id="crashConsistentRPTDetailDate"]//option'
        dropdown_rp_values = self.__admin_console.driver.find_elements(By.XPATH, dropdown_values_xpath)
        rp_list = [rp_stat.text for rp_stat in dropdown_rp_values]
        self.__modal_panel.cancel()
        return rp_list

    @PageService()
    def clear_intervals(self):
        """
        Clears the RP intervals
        """
        rpstore_configure = RConfigureRPStore(self.__admin_console)
        rpstore_configure.edit_peak_interval()
        rpstore_configure.clear_peak_intervals()
        rpstore_configure.save()

    @PageService()
    def add_mediagent(self, media_agent_name):
        """
        Add a mediagent to an rpstore
        Args:
            media_agent_name        (lst): Specify a list of media agents to be added to a rpstore
        """
        self.__table.access_action_item(self.__label['label.networkStore.readyStatus'],
                                        self.__label['title.addMediaAgent'])
        self.__table.select_rows([media_agent_name])
        self.__modal_panel.submit()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_storage(self, name, max_size, peak_interval):
        """
        Creates an rp store with specified arguments
        Args:
            name            (str): name of the recovery point store
            max_size        (int): the maximum size of the recovery point store in GB
            peak_interval  (dict): the intervals at which recovery point store is marked at peak
                Must be a dict of keys as days, and values as list of date time ids(0-23)
        """
        page_container = PageContainer(self.__admin_console)
        page_container.edit_title(name)
        self.__modal_panel.edit_and_save_tile_entity(self.__label['label.maximumThreshold'], str(max_size))
        if peak_interval:
            rpstore_configure = RConfigureRPStore(self.__admin_console)
            rpstore_configure.edit_peak_interval(peak_interval)
            rpstore_configure.save()

    @PageService()
    def verify_disabled_fields(self, value):
        """
        Verifies the disabled field on edit storage
        Args:
            value            (str): Value of the input type
        return              (Bool): True if disabled else False
        """
        result = self.__verify_is_field_disabled(value)
        return result

    @PageService()
    def get_rpstorepanel_info(self):
        """ Method to validate panel information fetched """

        panel_details = RPanelInfo(self.__admin_console, self.__label['header.label.general']).get_details()

        for key, value in panel_details.items():
            if not key or not value:
                raise CVWebAutomationException(f'Details are not fetched correctly for panel')
        return panel_details

    @PageService()
    def get_column_data(self, column_name):
        """
        Get the column data
        Args:
            column_name      (str): Value of the input type
        return               (str): Value retrieved from the column
        """
        data = self.__table.get_column_data(column_name)[0]
        return data

    @PageService()
    def access_action(self, action_name):
        """
        Access the actions options present in the action button for the first row
        Args:
            action_name: Actio name to be performed Eg. Start, Stop, Suspend etc
        """
        self.__click_action_menu()
        self.__admin_console.wait_for_completion()
        self.__click_action(action_name)
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_all_rp_stats(self):
        """
        Get all the current RP stats date
        return          (list): List of RP stats
        """

        self.access_action(self.__label['action.createNewTestBootFailoverEnabled'])
        self.__admin_console.wait_for_completion()
        rp_list = self.__get_rp_list()
        return rp_list


class RConfigureRPStore:
    """ Page class for RP stores creation wizard """

    def __init__(self, admin_console) -> None:
        """
        Initializer to create component objects
        Args:
            admin_console (AdminConsole): The admin console object used for initializing component objects
        """
        self._admin_console = admin_console

        self._panel: RPanelInfo = RPanelInfo(self._admin_console)
        self._drop_down: RDropDown = RDropDown(self._admin_console)
        self._content_browse: RContentBrowse = RContentBrowse(self._admin_console)

        self._admin_console.load_properties(self, unique=True)
        self._props = self._admin_console.props[self.__class__.__name__]

    @WebAction()
    def __click_edit_peak_interval_button(self) -> None:
        """Clicks the edit button for peak interval"""
        self._admin_console.driver.find_element(By.XPATH, f"//button[@title='{self._props['action.edit']}'").click()

    @PageService()
    def clear_peak_intervals(self) -> None:
        """Clicks on the clear interval button"""
        self._admin_console.click_button("Clear")

    @WebAction()
    def __is_interval_selected(self, day_index: int, interval_idx: int) -> bool:
        """
        Checks whether the interval is selected or not
        Args:
            day_index    (int): Day index of 'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
                                'Thursday': 3, 'Friday': 4, 'Saturday': 5 or 'Sunday': 6
            interval_idx (int): The index of hourly interval starting from 0 upto 23
        """
        xpath = f"//tr[@id='{day_index}']/td[@date-time-id='{interval_idx}']"
        return "selected" in self._admin_console.driver.find_element(By.XPATH, xpath).get_attribute('class')

    @WebAction()
    def __click_interval_selection_cell(self, day_index: int, interval_idx: int) -> None:
        """
        Clicks the peak interval selection cells according to index for particular day
        Args:
            day_index    (int): Day index of 'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
                                'Thursday': 3, 'Friday': 4, 'Saturday': 5 or 'Sunday': 6
            interval_idx (int): The index of hourly interval starting from 0 upto 23
        """
        xpath = f"//tr[@id='{day_index}']/td[@date-time-id='{interval_idx}']"
        self._admin_console.driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def peak_interval_selection(self, peak_interval: dict) -> None:
        """
        Selects the intervals which are marked as peak for the recovery point store
        Args:
            peak_interval (dict): the intervals at which recovery point store is marked at peak
                Must be a dict of keys as days, and values as list of date time ids(0-23)
                eg: {'Monday': [0,1,2,3], 'Tuesday': [0,1,2,3], 'Wednesday': [0,1,2,3]}
        """
        self.clear_peak_intervals()
        days = [self._props['label.day.mon'], self._props['label.day.tue'], self._props['label.day.web'],
                self._props['label.day.thu'], self._props['label.day.fri'], self._props['label.day.sat'],
                self._props['label.day.sun']]
        for day_index, day in enumerate(days):
            if day in peak_interval.keys():
                for slot in peak_interval[day]:
                    if not self.__is_interval_selected(day_index, slot):
                        self.__click_interval_selection_cell()
        self._panel.submit()

    @PageService()
    def set_rp_store_name(self, rpstore_name: str) -> None:
        """
        Set the RP store name in the input field
        Args:
            rpstore_name (str): The name of the RP store to be created
        """
        name_field_id = "rpStoreName"
        self._admin_console.fill_form_by_id(name_field_id, rpstore_name)

    @WebAction()
    def __click_add_media_agent(self) -> None:
        """Click on the add button for media agent dropdown action"""
        # TODO: Remove this method by implementing in a component class
        label = "Create new"
        self._admin_console.driver.find_element(By.XPATH, f"//button[@aria-label='{label}']").click()

    @PageService()
    def create_media_agent(self) -> Servers:
        """Allows creation of new MA server"""
        servers_page = Servers(self._admin_console)
        self.__click_add_media_agent()
        return servers_page

    @PageService()
    def select_media_agent(self, media_agent_name: str) -> None:
        """
        Selects the media agent from the dropdown to create RP store on
        Args:
            media_agent_name (str): The name of the MA
        """
        ma_selection_dropdown_id = "mediaAgent"
        self._drop_down.select_drop_down_values(values=[media_agent_name],
                                                drop_down_id=ma_selection_dropdown_id)

    @PageService()
    def set_maximum_size(self, size_in_gb: int) -> None:
        """
        Sets the maximum size of the RP store in GBs
        Args:
            size_in_gb (int): The maximum size of the RP store in GBs
        """
        size_field_id = "maxThreshold"
        self._admin_console.fill_form_by_id(size_field_id, size_in_gb)

    @PageService()
    def set_path(self, rpstore_path: str) -> None:
        """
        Set the RP store path on media agent
        Args:
            rpstore_path (str): To set the path of the RP store on MA
        """
        path_field_id = "rpStorePath"
        self._admin_console.fill_form_by_id(path_field_id, rpstore_path)

    @PageService()
    def browse_path(self, rpstore_path: str) -> None:
        """
        Browse the RP store path on the MA. If it doesn't exist, create folders
        Args:
            rpstore_path (str): The path of the RP store
        """
        self._admin_console.click_button(self._props['Browse'])
        self._content_browse.select_path(rpstore_path)
        self._content_browse.save_path()

    @PageService()
    def select_credential(self, credential_name: str) -> None:
        """
        Select the saved credential for drop down
        Note: Only applicable for network RP stores
        Args:
            credential_name (str): Name of the credential to be selected
        """
        self._admin_console.checkbox_select(checkbox_id="toggleFetchCredentials")
        self._drop_down.select_drop_down_values(values=[credential_name],
                                                drop_down_id="credentials")

    @PageService(hide_args=True)
    def set_username_and_password(self, username: str, password: str) -> None:
        """
        Set the username and password for the RP store network credentials
        Note: Only applicable for network RP stores
        Args:
            username (str): The username of the network path
            password (str): The password of the network path
        """
        self._admin_console.fill_form_by_id("userName", username)
        self._admin_console.fill_form_by_id("password", password)

    @PageService()
    def edit_peak_interval(self, peak_interval: dict) -> None:
        """
        Args:
            peak_interval (dict): the intervals at which recovery point store is marked at peak
                                  Must be a dict of keys as days, and values as list of date time ids(0-23)
                                  eg: {'Monday': [0,1,2,3], 'Tuesday': [0,1,2,3], 'Wednesday': [0,1,2,3]}
        """
        self.__click_edit_peak_interval_button()
        self.peak_interval_selection(peak_interval)

    @PageService()
    def cancel(self) -> None:
        """Cancel the RP store creation"""
        self._panel.cancel()
        self._admin_console.check_error_message()

    @PageService()
    def save(self) -> None:
        """Save the RP store configuration"""
        self._panel.submit()
        self._admin_console.check_error_message()
