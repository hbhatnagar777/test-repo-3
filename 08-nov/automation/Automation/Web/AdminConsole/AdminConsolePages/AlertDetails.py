# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
AlertDetails page

Class:

    Alerts()

Functions:

    __init__()                          --  initialize the Alerts class

    edit_alert_name()                   --  Method to edit the alert name

    delete_alert()                      --  Method to delete the alert



"""
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.page_container import PageContainer


class AlertDetails:
    """
    This class provides the function or operations that can be performed on the Alert details page
    """

    def __init__(self, admin_console):
        """
        Initializes the AlertDetails class

        Args:
            admin_console   (object)    --  instance of the AdminConsole class
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self, unique=True)
        self.__table = Rtable(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.__navigator = self.__admin_console.navigator
        self.__dialog = RModalDialog(admin_console)
        self.log = admin_console.log
        self.driver = admin_console.driver

    @PageService()
    def edit_alert_name(self, new_alert_name):
        """Edit the alert name
        
        Args:
            new_alert_name (str) -- New name for the alert    
        """

        self.__page_container.edit_title(new_alert_name)
        self.log.info(f"Alert name modified to '{new_alert_name}'")
    
    @PageService()
    def delete_alert(self):
        """Delete the alert"""

        self.__page_container.access_page_action('Delete')
        self.__dialog.click_yes_button()