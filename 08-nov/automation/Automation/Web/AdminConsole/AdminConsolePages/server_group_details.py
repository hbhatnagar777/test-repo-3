# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
plan detail page on the AdminConsole

Class:

    ServerGroupConfigurations()

Functions:

enabled_activities()    -- Returns the enabled activities at server group level
enable_activity()       -- Enable activities at in server group page
edit_file_exceptions()  -- Edits file exceptions for a server group
delete_group()          -- Deletes a server group
access_configuration()  -- accesses configuration tab for a server group
set_workload_region()   -- assigns workload region to the server group
get_workload_region()   -- returns the workload region assigned to the server group
"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown, RModalPanel
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.core import Checkbox
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.table import Rtable
from selenium.webdriver.common.keys import Keys

class ServerGroupConfiguration:
    """Class for server group configuration page of adminconsole"""

    def __init__(self, admin_console):
        self.__adminconsole = admin_console
        self.__panel = RPanelInfo(self.__adminconsole)
        self.__drop_down = RDropDown(self.__adminconsole)
        self.__table = Rtable(self.__adminconsole)
        self.__network_panel = RPanelInfo(self.__adminconsole, 'Network settings')
        self.__dialog = RModalDialog(self.__adminconsole,xpath="//div[@aria-labelledby ='customized-dialog-title']")
        self.__rmodalpanel = RModalPanel(self.__adminconsole)
        self.__portdialog = RModalDialog(self.__adminconsole, xpath="//div[contains(@class,'mui-modal-centered')]//div[@aria-labelledby ='customized-dialog-title']")
        self.__checkbox = Checkbox(self.__adminconsole)
        self.__adminconsole.load_properties(self)

    @WebAction()
    def __next_line(self, element_id):
        """
        Method to enter file exceptions

        Args:
            element_id (str) : id of the textbox to enter values in
        """
        self.__adminconsole.driver.find_element(By.ID, element_id).send_keys(Keys.RETURN)

    @WebAction()
    def __append_file_exception(self, element_id, exception):
        """
        Method to enter file exceptions

        Args:
            element_id (str) : id of the textbox to enter values in

            exception (str) : exception to be added to the company
        """
        self.__adminconsole.driver.find_element(By.ID, element_id).send_keys(exception)

    @PageService()
    def enabled_activities(self):
        """Returns the enabled activities at server group level"""
        panel = RPanelInfo(self.__adminconsole, 'Activity control')
        activities = panel.get_details()
        enabled_activities = []
        for i in activities:
            if activities[i] == 'ON':
                enabled_activities.append(i)
        return enabled_activities

    @PageService()
    def enable_activity(self, activities):
        """Enable activities at in server group page
        Args:
            activity (dict): activity name with ON/OFF
                example:
                    activity = {
                                "backup": 'True',
                                "restore": 'True',
                                "aging": 'True'
                            }
            """
        for activity in activities:
            if activities[activity]:
                self.__panel.enable_toggle('Data ' + activity)
            else:
                self.__panel.disable_toggle('Data ' + activity)

    @PageService()
    def edit_file_exceptions(self,
                             file_exceptions):
        """
        Edits file exceptions for a server group

        Args:
            file_exceptions (dict of lists) : List of paths to be excluded for the server group
               Eg. -  file_exceptions = {"windows_path":["C:\\Test"],
                                         "unix_path": ["/root/file1"]}

        Returns:
            None

        Raises:
            Exception:
                -- if fails to set edit file exceptions for the server group
        """

        RPanelInfo(self.__adminconsole, 'File exceptions').edit_tile()
        self.__adminconsole.admin_console.wait_for_completion()

        if file_exceptions.get('windows_path', None):
            self.__adminconsole.driver.find_element(By.ID, 'windowsFiles').clear()
            for win_path in file_exceptions['windows_path']:
                self.__append_file_exception("windowsFiles", win_path)
                self.__next_line("windowsFiles")

        if file_exceptions.get('unix_path', None):
            self.__adminconsole.driver.find_element(By.ID, 'unixFiles').clear()
            for unix_path in file_exceptions['unix_path']:
                self.__append_file_exception("unixFiles", unix_path)
                self.__next_line("unixFiles")

        self.__adminconsole.submit_form()
        self.__adminconsole.check_error_message()

    @PageService()
    def delete_group(self):
        """Deletes a server group"""
        self.__adminconsole.access_menu(self.__adminconsole.props['label.delete'])

        self.__adminconsole.admin_console.wait_for_completion()

    @PageService()
    def access_configuration_tab(self, group_name):
        """
        method to access configuration tab for a server group

        Args:
            group_name (str): server group name
        """
        self.__table.access_link(group_name)
        self.__adminconsole.select_configuration_tab()

    @PageService()
    def set_workload_region(self, region):
        """
        assigns workload region to server groups

        Args:
            region (str): the region name
        """
        self.__panel.edit_tile_entity('Workload region')
        self.__drop_down.select_drop_down_values(drop_down_id="regionDropdown_",
                                                values=[region])
        self.__panel.click_button(self.__adminconsole.props["label.save"])

    def get_workload_region(self, group_name):
        """
        Method used to get the assigned region for the entity

        Args:
            group_name(str) = name of the server group

        returns:
            Workload region
        """
        self.access_configuration_tab(group_name)
        return self.__panel.get_details()['Workload region']

    @PageService()
    def get_network_settings(self):
        """
        Method used to fetch the group level network settings

        returns:
            A dictionary containing group level settings like keepalive interval, tunnelport, open port etc
            Example :  {'Tunnel port': '8403', 
                        'Additional open port range': '', 
                        'Bind all services to open ports only': 'No', 
                        'Keep-alive interval in seconds': '180', 
                        'Force SSL encryption in incoming tunnels': 'Yes', 
                        'Enable network gateway': 'Yes'}
        """
        details = self.__network_panel.get_details()
        return details

    @WebAction()
    def __open_network_settings(self):
        """
        Method to open network settings tile
        """
        self.__network_panel.edit_tile()

    @WebAction()
    def __override_default_tunnelport(self, tunnel_port, override=True):
        """
        Method to override the default tunnel port

        Args:
            tunnel_port (str) : Tunnel port to be set
            override (bool) : Flag to override the default tunnel port
        """
        if not override:
            self.__checkbox.uncheck(label=self.__adminconsole.props['label.overridePort'])
            return
        self.__checkbox.check(label=self.__adminconsole.props['label.overridePort'])
        self.__rmodalpanel.fill_input(id='tunnelconnectionPort', text=tunnel_port)

    @WebAction()
    def __bind_services_to_openports(self, bind_services=True):
        """
        Method to bind services to open ports

        Args:
            bind_services (bool) : Flag to bind services to open ports
        """
        if not bind_services:
            self.__checkbox.uncheck(label=self.__adminconsole.props['label.bindAllServicesToOpenPorts'])
            return
        self.__checkbox.check(label=self.__adminconsole.props['label.bindAllServicesToOpenPorts'])
    
    @WebAction()
    def __set_keepalive_interval(self, interval):
        """
        Method to set the keepalive interval

        Args:
            interval (str) : Keepalive interval to be set
        """
        self.__rmodalpanel.fill_input(text=interval, id='keepAliveSeconds')

    @WebAction()
    def __force_ssl(self, force_ssl=True):
        """
        Method to force ssl for incoming connections

        Args:
            force_ssl (bool) : Flag to force ssl
        """
        if not force_ssl:
            self.__checkbox.uncheck(label=self.__adminconsole.props['label.forceSSL'])
            return
        self.__checkbox.check(label=self.__adminconsole.props['label.forceSSL'])
    
    @WebAction()
    def __set_open_port_range(self, startport, endport):
        """
        Method to set the open port range on the server group

        Args:
            port (str) : Open port range to be set
        """
        self.__dialog.click_add()
        self.__fill_port_range(startport, endport)
        self.__portdialog.click_button_on_dialog(text=self.__adminconsole.props['label.addPort'])

    @WebAction()
    def __update_open_port_range(self, startport, endport):
        """
        Method to update the open port range on the server group

        Args:
            startport (str) : Open port range start to be set

            endport (str) : Open port range end to be set
        """
        self.__adminconsole.click_by_id('icon-btn-0')
        self.__fill_port_range(startport, endport)
        self.__portdialog.click_button_on_dialog(text=self.__adminconsole.props['label.updatePort'])
    
    @WebAction()
    def __delete_open_port_range(self):
        """
        Method to delete the open port range on the server group
        """
        self.__adminconsole.click_by_xpath("//div[@aria-label='Delete']")

    @WebAction()
    def __fill_port_range(self, startport, endport):
        """
        Method to fill the port range

        Args:
            startport (str) : Open port range start to be set

            endport (str) : Open port range start to be set
        """
        self.__portdialog.fill_input_by_xpath(startport, element_id="startPort")
        self.__portdialog.fill_input_by_xpath(endport, element_id="endPort")
    
    @WebAction()
    def __enable_network_gateway(self, enable=True):
        """
        Method to enable network gateway flag on the server group

        Args:
            enable (bool) : Flag to enable network gateway
        """
        if not enable:
            self.__checkbox.uncheck(label=self.__adminconsole.props['label.enableGateway'])
            return
        self.__checkbox.check(label=self.__adminconsole.props['label.enableGateway'])
    
    @WebAction()
    def __save_network_settings(self):
        """
        Method to save the network settings
        """
        self.__adminconsole.submit_form()
    
    @PageService()
    def apply_network_settings(self, settings):
        """
        Method to apply network settings based on the provided dictionary.

        Args:
            settings (dict): Dictionary containing network settings and their values.
            Use 'delete' key with a boolean flag to indicate if a setting should be deleted.
            Example:
            {
                'keepalive_interval': {'value': '30', 'delete': False},
                'tunnel_port': {'value': '8080', 'delete': False},
                'bind_services': {'value': True, 'delete': False},
                'open_port_range': {'start': '8000', 'end': '9000', 'delete': False},
                'enable_gateway': {'value': True, 'delete': False},
                'force_ssl': {'value': True, 'delete': False}
            }
        """
        # Open the network settings before applying any changes
        self.__open_network_settings()

        for setting, details in settings.items():
            delete_flag = details.get('delete', False)

            if setting == 'keepalive_interval':
                if delete_flag:
                    self.__set_keepalive_interval('180')
                else:
                    self.__set_keepalive_interval(details['value'])

            elif setting == 'tunnel_port':
                if delete_flag:
                    self.__override_default_tunnelport('', override=False)
                else:
                    self.__override_default_tunnelport(details['value'], override=True)

            elif setting == 'bind_services':
                if delete_flag:
                    self.__bind_services_to_openports(bind_services=False)
                else:
                    self.__bind_services_to_openports()

            elif setting == 'open_port_range':
                if delete_flag:
                    self.__delete_open_port_range()
                else:
                    self.__set_open_port_range(details['start'], details['end'])

            elif setting == 'enable_gateway':
                if delete_flag:
                    self.__enable_network_gateway(enable=False)
                else:
                    self.__enable_network_gateway()

            elif setting == 'force_ssl':
                if delete_flag:
                    self.__force_ssl(force_ssl=False)
                else:
                    self.__force_ssl()

        # Save all the settings after applying changes
        self.__save_network_settings()