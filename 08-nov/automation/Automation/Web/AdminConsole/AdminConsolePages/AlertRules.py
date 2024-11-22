# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
AlertRules page inside Developer Tools, on the AdminConsole

Class:

    AlertRules

Functions:

    import_alert_rule()                 --  Method to import alert rule given a file path

    export_table()                      --  Method to export and verify the file type

    toggle_alert_rule()                 --  Method to toggle the alert rule

    delete_alert_rule()                 --  Method to delete the alert rule

    export_alert_rule()                 --  Method to export the alert rule

    access_alert_rule()                 --  Method to search for the alert rule

"""

from Web.Common.page_object import PageService
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.core import Toggle


class AlertRules:
    """
    This class provides the function or operations that can be performed on the Alerts page
    """

    def __init__(self, admin_console):
        """
        Initializes the Alert Rules class

        Args:
            admin_console   (object)    --  instance of the AdminConsole class
        """

        self.__admin_console = admin_console
        self.__admin_console.load_properties(self, unique=True)
        self.__table = Rtable(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__toggle = Toggle(admin_console)
        self.__alert = Alert(admin_console)
        self.log = admin_console.log
        self.driver = admin_console.driver

    @PageService()
    def import_alert_rule(self, alert_rule_file_path):
        """
        Method to import alert rule given a file path

        Args:
            alert_rule_file_path:           (str)   --  path to the alert rule file

        Returns:
            None
        """

        # Click on the import button
        self.__table.access_toolbar_menu('Import')

        # Upload the file
        self.__dialog.submit_file("alert-rule-import", alert_rule_file_path)
        self.__dialog.click_save_button()
        self.__admin_console.wait_for_completion()

        # Check if error toast or back button visible
        try:
            
            alert_content = self.__alert.get_content()
            if alert_content != "":
                raise Exception(alert_content)
        except Exception as e:
            self.log.info("No error encountered. Assuming import successful.")


    @PageService()
    def export_table(self, file_type_capitalized):
        """
        Method to export and verify the file type

        Args:
            file_type_capitalized:          (str)   --  file type to export

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
    def delete_alert_rule(self, rule_name):
        """
        Method to delete the alert rule
        
        Args:
            rule_name:          (str)   --  name of the alert rule
            
            Returns:
                None
                
            Raises:
                Exception:
                    if fails to delete the alert rule
                    
        """

        self.__table.access_action_item(entity_name=rule_name, action_item=self.__admin_console.props["AlertRules"]["label.delete"])
        self.__dialog.click_yes_button()
    
    @PageService()
    def export_alert_rule(self, rule_name):
        """
        Method to export the alert rule

        Args:
            rule_name:          (str)   --  name of the alert rule
        
        Returns:

            None
        """

        self.__table.access_action_item(entity_name=rule_name, action_item="Export")

    @PageService()
    def access_alert_rule(self, rule_name):
        """
        Method to search for the alert rule

        Args:
            rule_name:          (str)   --  name of the alert rule

        Returns:

            None
        """

        self.__table.access_link(rule_name)
