# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
AlertRuleDetails page inside Developer Tools, on the AdminConsole

Class:

    AlertRuleDetails()

Functions:

    __init__()                          --  initialize the Alerts class

    export_table()                      --  Method to export and verify the file type

    toggle_alert_rule()                 --  Method to toggle the alert rule

    export_alert_rule()                 --  Method to export the alert rule

    click_add_alert_definition()        --  Method to click on the add alert definition button

"""
from selenium.webdriver.common.by import By


from Web.Common.page_object import (
    PageService
)
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.Components.panel import RDropDown


class AlertRuleDetails:
    """
    This class provides the function or operations that can be performed on the AlertRuleDetails page
    """

    def __init__(self, admin_console):
        """
        Initializes the Alerts class
        
        Args:
            admin_console   (object)    --  instance of the AdminConsole class
            
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self, unique=True)
        self.__table = Rtable(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.__navigator = self.__admin_console.navigator
        self.__wizard = Wizard(admin_console)
        self.__toggle = Toggle(admin_console)
        self.__alert = Alert(admin_console)
        self.__dropdown = RDropDown(admin_console)
        self.log = admin_console.log
        self.driver = admin_console.driver

    @PageService()
    def export_table(self, file_type_capitalized):
        """
        Method to export and verify the file type

        Args:
            file_type_capitalized:          (str)   --  file type to export
                                                        (Ex: XLSX, CSV, PDF)

        Returns:
            None

        Raises:
            Exception:
                if export fails
        """

        # Click on the export button with relevant file type
        self.__table.click_reset_column_widths(f'Export {file_type_capitalized}')

    @PageService()
    def toggle_alert_rule(self, rule_name):
        """
        Method to toggle the alert rule
        
        Args:
            rule_name:          (str)   --  name of the alert rule
            
            Returns:
                None
                
            Raises:
                Exception:
                    if fails to toggle the alert rule
                    
        """

        # search for the rule
        self.__table.search_for(rule_name)
        if self.__toggle.is_enabled(id='isDisabledValue'):
            self.__toggle.disable(id='isDisabledValue')
            self.log.info(f"Disabled the alert rule '{rule_name}'")
        else:
            self.__toggle.enable(id='isDisabledValue')
            self.log.info(f"Enabled the alert rule '{rule_name}'")
        self.__table.clear_search()


    @PageService()
    def export_alert_rule(self):
        """
        Method to export the alert rule
        """
        
        self.__page_container.access_page_action('Export')
        latest_downloaded_file = self.__admin_console.browser.get_latest_downloaded_file()
        if not latest_downloaded_file.endswith('xml'):
            raise Exception(f"Export failed")
    
    @PageService()
    def click_add_alert_definition(self):
        """
        Method to click on the add alert definition button
        """
        
        self.__page_container.access_page_action('Add alert definition')
    
    @PageService()
    def edit_security(self, user_to_role_mapping):
        """
        Method to edit the security of the alert rule

        Args:
            user_to_role_mapping:          (dict)   --  user to role mapping
                                                        (Ex: {
                                                        'user1': ['role1','role2'], 
                                                        'user2': ['role2']
                                                        })

        Returns:
            None

        Raises:
            Exception:
                if fails to edit the security of the alert rule

        """

        self.__page_container.click_button(id="tile-action-btn")

        for user in user_to_role_mapping.keys():
            for role in user_to_role_mapping[user]:
                self.__dropdown.search_and_select(user, id="security_usersAndGroupsList")
                self.__dropdown.select_drop_down_values(drop_down_label="Roles", values=[role])
                self.__dialog.click_button_on_dialog(text="Add")
        self.__dialog.click_save_button()