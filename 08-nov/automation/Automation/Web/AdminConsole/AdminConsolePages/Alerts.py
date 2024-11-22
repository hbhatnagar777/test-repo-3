# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Alerts page on the AdminConsole

Class:

    Alerts()

Functions:

select_triggered_alerts()      --  Method to select and open the triggered alerts tab

select_alert_definitions()     --  Method to select and open the alert definitions tab

delete_triggered_alert()       --  Method to delete single triggered alert

delete_all_triggered_alerts()  --  Method to delete all triggered alerts

dump_alerts_info()             --  prints the alert info for a scpecific machine and alert

all_triggered_alerts_info()    --  prints all the alerts triggered for all the clients

select_by_alert_type()         --  Displays only the alerts of the given type


Class:

    Ralerts()

Functions:

select_triggered_alerts()      --  Method to select and open the triggered alerts tab

select_alert_definitions()     --  Method to select and open the alert definitions tab

delete_alert_notification()    --  Method to delete a triggered alert notification

"""
from selenium.webdriver.common.by import By

import time

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.Common.exceptions import CVWebAutomationException

class Alerts:
    """
    This class provides the function or operations that can be performed on the Alerts page
    """

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.log = admin_console.log
        self.driver = admin_console.driver

    @WebAction()
    def __apply_filter(self, **kwargs):
        """
        Method to apply filter on the triggered alerts page

        Args:
            **kwargs: keyword arguments for search string, severity, commcell_name
                search_str (str): search string to filter the alerts
                severity (str): severity of the alert
                commcell_name (str): commcell name to filter the alerts (Global)
        """
        search_str = kwargs.get('search_str')
        severity = kwargs.get('severity')
        commcell_name = kwargs.get('commcell_name')

        if severity:
            self.__table.set_default_filter(filter_id='Severity', filter_value=severity)

        if commcell_name:
            self.__table.set_default_filter(filter_id='CommCell', filter_value=commcell_name)

        if search_str:
            self.__table.search_for(search_str)

    @PageService()
    def is_alert_triggered(self, alert_name, **kwargs):
        """
        Method to check if the triggered alert is present in the triggered alerts page

        Args:
            alert_name (str) : name of the alert to be checked

            **kwargs: keyword arguments for search string, severity, commcell_name
                severity (str): severity of the alert
                commcell_name (str): commcell name to filter the alerts (Global)

        Returns:
            bool: True if the alert is triggered for the client, False otherwise
        """
        self.select_triggered_alerts()
        self.__apply_filter(**kwargs)
        return self.__table.is_entity_present_in_column(column_name='Alert info', entity_name=alert_name)

    @PageService()
    def select_triggered_alerts(self):
        """
        Method to navigate to triggered alerts page
        """
        self.__page_container.select_tab("Triggered alerts")

    @PageService()
    def select_alert_definitions(self):
        """
        Method to navigate to alerts definition page
        """
        self.__page_container.select_tab("Alerts definitions")

    @PageService()
    def delete_current_triggered_alert(self, alert_name, **kwargs):
        """
        Method to delete a triggered alert

        Args:
           alert_name   (string) : Name of the alert to be deleted

              **kwargs: keyword arguments for search string, severity, commcell_name
                client_name (str): client name to filter the alerts
                severity (str): severity of the alert
                commcell_name (str): commcell name to filter the alerts (Global)

        Returns:
            None

        Raises:
            Exception:
                -- if fails to delete the triggered alert
        """
        self.__apply_filter(search_str=alert_name, **kwargs)
        
        if client_name := kwargs.get('client_name'):
            self.__table.apply_filter_over_column('Client name', client_name)
        
        self.delete_all_triggered_alerts() # after applying filter, delete all the available alerts

    @PageService()
    def delete_all_triggered_alerts(self):
        """Method to delete all triggered alerts"""
        self.__table.select_all_rows()
        self.__table.access_toolbar_menu('Delete')
        self.__dialog.click_yes_button()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def get_triggered_alerts(self, **kwargs):
        """
            Method to get the triggered alerts
        
            Args:
                **kwargs: keyword arguments for search string, severity, commcell_name, and fetch_all
                    search_str (str): search string to filter the alerts
                    severity (str): severity of the alert
                    commcell_name (str): commcell name to filter the alerts (Global)
                    fetch_all (bool): fetch all the alerts or not   
        """        
        self.__apply_filter(**kwargs)
        
        # by default fetch alerts for the first page
        fetch_all = kwargs.get('fetch_all', False)
        return self.__table.get_column_data(column_name='Alert info', fetch_all=fetch_all)
    
    @WebAction()
    def __manage_notes_for_alert(self, alert_name, notes: str='', action: str='add'):
        """
        Method to manage notes of an alert

        Args:
            alert_name (str) : name of the alert for which notes to be added

            notes (str) : notes to be added to the alert
            
            action (str) : action to be performed on the notes (add, edit, delete)
        """
        self.__apply_filter(search_str=alert_name)
        self.__table.select_rows([alert_name])
        self.__table.select_row_by_column_value(column_name='Alert info', column_value=alert_name)
        self.__table.access_toolbar_menu('Notes')
        self.__dialog.set_text(notes)
        self.__dialog.click_save_button()
        self.__admin_console.wait_for_completion()
        
class Ralerts:
    """
    This class provides the function or operations that can be performed on the Alerts page
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
        self.log = admin_console.log
        self.driver = admin_console.driver

    @PageService()
    def select_triggered_alerts(self):
        """
        Method to navigate to triggered alerts page
        """
        self.__admin_console.access_tab(self.__admin_console.props["Ralerts"]["label.triggeredAlerts"])

    @PageService()
    def select_alert_definitions(self):
        """
        Method to navigate to alerts definition page
        """
        self.__admin_console.access_tab(self.__admin_console.props["Ralerts"]["label.alertDefinitions"])
    
    @PageService()
    def delete_alert_notification(self, alert_name):
        """
        Method to delete a triggered alert notification

        Args:

            alert_name   (string) : Name of the alert to be deleted

        Returns:

            None

        """
        self.__table.access_action_item(entity_name=alert_name, action_item=self.__admin_console.props["Ralerts"]["label.delete"])
        self.__dialog.click_yes_button()
