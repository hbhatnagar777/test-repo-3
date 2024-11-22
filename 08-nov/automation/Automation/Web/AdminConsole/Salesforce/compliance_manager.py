# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions and operations that can be performed on a Salesforce Compliance Manager page

ComplianceManager:

    create_request()                  --  create a GDPR rule
    __create_del_request()            --  create a GDPR deletion request
    __create_modify_request()         --  create a GDPR modification request

"""
from dataclasses import dataclass

from Web.AdminConsole.Salesforce.base import SalesforceBase
from Web.AdminConsole.Salesforce.constants import GDPRRequestType
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable


class ComplianceManager(SalesforceBase):
    """Class for Compliance Manager page"""

    def __init__(self, admin_console, commcell):
        """
        Init method for this class

        Args:
            admin_console (Web.AdminConsole.Helper.AdminConsoleBase.AdminConsoleBase): Object of AdminConsoleBase class

        Returns:
            None:
        """
        super().__init__(admin_console, commcell)
        self.__admin_console = admin_console
        self.__page_container = PageContainer(self.__admin_console)
        self.__rdialog = RModalDialog(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)

    @PageService()
    def create_request(self, name, request_type: GDPRRequestType, rules, **kwargs):
        """
        create a GDPR rule

        Args:
            name (str): Request name
            request_type (GDPRRequestType): Type of request to be created
            rules (list[dict]):
                name (str): object name
                options (list[dict]):
                    id (str): record id
                    fieldValues (list[dict]):
                        name (str): field name
                        value (str): field value
        Returns:
            None:
        """
        if request_type == GDPRRequestType.DELETION:
            self.__create_del_request(name, rules, **kwargs)
        elif request_type == GDPRRequestType.MODIFICATION:
            self.__create_modify_request(name, rules, **kwargs)
        self.__admin_console.click_button(value=self.__admin_console.props["label.gdpr.submit"])

    @PageService()
    def __create_del_request(self, name, rules, **kwargs):
        """
        create a GDPR deletion request

        Args:
            name (str): Request name
            rules (list[dict]):
                name (str): object name
                options (list[dict]):
                    id (str): record id

            kwargs (dict): keyword arguments to hold any additional information

        Returns:
            None:
        """
        self.__rtable.access_menu_from_dropdown(self.__admin_console.props["label.gdpr.action.deleteRecords"],
                                                self.__admin_console.props["label.gdpr.newRequest"])
        self.__admin_console.fill_form_by_name("name", name)
        for rule in rules:
            self.__admin_console.click_button(value=self.__admin_console.props["title.gdpr.addRule"])
            self.__rdialog.select_dropdown_values(drop_down_id="objectNames", values=[rule["name"]],
                                                  case_insensitive=True)
            self.__admin_console.fill_form_by_name("recordIds", ",".join([record["id"] for record in rule["options"]]))
            self.__rdialog.click_submit()

    @PageService()
    def __create_modify_request(self, name, rules, **kwargs):
        """
        create a GDPR modification request

        Args:
            name (str): Request name
            rules (list[dict]):
                name (str): object name
                options (list[dict]):
                    id (str): record id
                    fieldValues (list[dict]):
                        name (str): field name
                        value (str): field value
            kwargs (dict): keyword arguments to hold any additional information

        Returns:
            None:
        """
        self.__rtable.access_menu_from_dropdown(self.__admin_console.props["label.gdpr.action.modifyRecords"],
                                                self.__admin_console.props["label.gdpr.newRequest"])
        self.__admin_console.fill_form_by_name("name", name)
        for rule in rules:
            self.__admin_console.click_button(value=self.__admin_console.props["title.gdpr.addRule"])
            for option in rule["options"]:
                self.__rdialog.select_dropdown_values(drop_down_id="objectNames", values=[rule["name"]],
                                                      case_insensitive=True)
                self.__rdialog.click_button_on_dialog(self.__admin_console.props["label.gdpr.addRecord"])
                self.__admin_console.fill_form_by_name("__modifyOp", option["id"])
                self.__rdialog.click_button_on_dialog(id="modifyOpConfirm")
                for idx, field in enumerate(option["fieldValues"]):
                    if idx != 0:
                        self.__rdialog.click_button_on_dialog(id="add_record")
                    self.__rdialog.select_dropdown_values(drop_down_id=f"{option['id']}_{idx+1}_name",
                                                          values=[field["name"]], case_insensitive=True)
                    self.__admin_console.fill_form_by_name(f"{option['id']}_{idx+1}_value", field["value"])
            self.__rdialog.click_submit()

    @PageService()
    def _click_on_backup(self, org_name):
        """
        Method to click on backup

        Args:
            org_name (str)  --  Name of org to click on backup for
        """
        self.__page_container.access_page_action(self.__admin_console.props['label.globalActions.backup'])

    @PageService()
    def access_overview_tab(self):
        """
        Clicks on Overview tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['label.dashboard.tab.overview'])
