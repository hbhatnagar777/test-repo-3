# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions that can be performed on the
instant clone job details page, the page that opens after selecting
a clone job from instant clones page.

InstantCloneDetails:

    get_expiry_time     -- Method to get the expiration time of clone
    get_creation_time   -- Method to get the creation time of clone
    extend_retention    -- Method to extend the clone retention period
                            in job details page
    verify_retention    -- Verifies that expiry time is set correctly
                            from job details page

"""
from datetime import datetime
from Web.Common.page_object import PageService
from Web.AdminConsole.Databases.Instances.instant_clone import InstantClone
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.core import CalendarView
from Web.Common.exceptions import CVWebAutomationException


class InstantCloneDetails(InstantClone):
    """This class provides methods to perform in instant clone details page"""

    def __init__(self, admin_console):
        """Class constructor
            Args:
                admin_console (obj) --  The admin console class object
        """
        super(InstantCloneDetails, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.dialog = RModalDialog(self.__admin_console)
        self.page_container = PageContainer(self.__admin_console, id_value='instantCloneDetails')

    @property
    def get_expiry_time(self):
        """Method to get expiry time of running clone
        Returns:
           details["Expiration date"] - Expiry time as string
                Syntax: %m %d, %Y %H:%M:%S %p
        """
        destination_details = RPanelInfo(self.__admin_console, title=self.props['label.destDetails'])
        details = destination_details.get_details()
        return details["Expiration date"]

    @property
    def get_creation_time(self):
        """Method to get creation time of running clone
        Returns:
           details["Created date"] - Clone creation time as string
                Syntax: %m %d, %Y %H:%M:%S %p
        """
        source_details = RPanelInfo(self.__admin_console, title=self.props['label.sourDetails'])
        details = source_details.get_details()
        return details["Created date"]

    @PageService()
    def extend_retention(self, new_retention):
        """Method to calculate new expiry time and call extend method
        Args:
            new_retention (dict): Syntax = {"days": 7, "hours": 0}
            """
        expiry_time = int(datetime.timestamp(
            datetime.strptime(self.get_expiry_time, '%b %d, %Y %I:%M:%S %p')))
        if "days" in new_retention:
            expiry_time += (new_retention["days"] * 24 * 60 * 60)
        if "hours" in new_retention:
            expiry_time += (new_retention["hours"] * 60 * 60)
        expiry_time_map = {
            'year': int(datetime.fromtimestamp(expiry_time).strftime("%Y")),
            'month':  datetime.fromtimestamp(expiry_time).strftime("%B"),
            'day': int(datetime.fromtimestamp(expiry_time).strftime("%d")),
            'hour': int(datetime.fromtimestamp(expiry_time).strftime("%I")),
            'minute': int(datetime.fromtimestamp(expiry_time).strftime("%M")),
            'session': datetime.fromtimestamp(expiry_time).strftime("%p")
        }
        self.page_container.access_page_action('Extend')
        self.dialog.click_button_on_dialog(aria_label="Open calendar")
        calendar = CalendarView(self._admin_console)
        calendar.set_date_and_time(expiry_time_map)
        self.dialog.click_button_on_dialog(text='Save')
        self.__admin_console.wait_for_completion()
        return datetime.fromtimestamp(expiry_time).strftime('%m/%d/%Y %H:%M:%S')

    @PageService()
    def verify_retention(self, expiry_time):
        """Method to verify retention set is same as argument value
                Args:
                    expiry_time (str): expected expiry time of clone
                                       in syntax '03/01/2022 19:54:00'
                Raises:
                    CVWebAutomationException:
                        If expiry time set in command center is not expiry_time value
                """
        current_expiry_time = int(datetime.timestamp(
            datetime.strptime(self.get_expiry_time, '%b %d, %Y %I:%M:%S %p')))
        current_expiry_time = datetime.fromtimestamp(
            current_expiry_time).strftime('%m/%d/%Y %H:%M:%S')
        if not expiry_time == current_expiry_time:
            raise CVWebAutomationException("Expiry time is not set correctly")
