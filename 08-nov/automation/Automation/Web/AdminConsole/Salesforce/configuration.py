# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions and operations that can be performed on a Salesforce organization configuration page

SalesforceConfiguration:

    check_alert_status()        --  Checks whether Anomaly Alerts are enabled for the organization

    access_overview_tab()       --  Clicks on Overview tab

    access_monitoring_tab()       --  Clicks on Monitoring tab


SalesforceConfiguration instance attributes:
    **api_limit**               --  API limit for file download
"""
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog


class SalesforceConfiguration:
    """Class for Salesforce Configuration page"""

    def __init__(self, admin_console):
        """
        Init method for this class

        Args:
            admin_console (AdminConsole): Object of AdminConsole class

        Returns:
            None:
        """
        self.__admin_console = admin_console
        self.__page_container = PageContainer(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__account_details_panel = RPanelInfo(
            self.__admin_console,
            title=self.__admin_console.props['label.cAppClientAccountDet']
        )
        self.__dialog = RModalDialog(self.__admin_console)

    @property
    def api_limit(self):
        """
        Gets API limit for file download

        Returns:
            int: value between 1 and 90
        """
        return self.__account_details_panel.get_details()[self.__admin_console.props['label.filesPerBackup']]

    @api_limit.setter
    def api_limit(self, api_limit):
        """
        Sets API limit for file download

        Args:
            api_limit (int): value between 1 and 90

        Returns:
            None:
        """

        self.__account_details_panel.edit_tile_entity(self.__admin_console.props["label.filesPerBackup"])
        self.__admin_console.fill_form_by_id("tile-row-field", api_limit)
        self.__account_details_panel.click_button("Submit")

    @WebAction()
    def check_alert_status(self):
        """
            Checks whether alerts are enabled for the org and enables it
        """
        self.__rpanel.enable_toggle(self.__admin_console.props["label.smartAlerts"])

    @PageService()
    def access_overview_tab(self):
        """
        Clicks on overview tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['label.tab.overview'])

    @PageService()
    def access_monitoring_tab(self):
        """
        Clicks on Monitoring tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['label.sf.tabs.anomalyAlerts'])
