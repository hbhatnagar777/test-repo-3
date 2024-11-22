# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
server groups page of the File System iDA on the AdminConsole

Class:

    ServerGroups()

Functions:

open_server_group()          -- open the server group
add_manual_server_group()    -- Creates a manual server group
add_automatic_server_group() -- Creates a manual server group
change_server_group_name()   -- Renames the server group name
search_for()                 -- searches a string in the search bar and return all the server groups listed
reset_filters()              -- reset the filters applied on the page
action_push_network_configuration() -- Pushes the network configuration to the selected servers
"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.panel import RDropDown, RModalPanel
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Table, CVTable, Rtable
from Web.AdminConsole.Components.core import TreeView
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.exceptions import CVWebAutomationException


class ServerGroups:
    """Class for server groups page of adminconsole """

    def __init__(self, admin_console):
        self.__table = Table(admin_console)
        self.__rtable = Rtable(admin_console)
        self.__cvtable = CVTable(admin_console)
        self.__drop_down = RDropDown(admin_console)
        self.__rmodalpanel = RModalPanel(admin_console)
        self.__treeview = TreeView(admin_console)
        self.__Rmodal_dialog = RModalDialog(admin_console)
        self.driver = admin_console.driver
        self.admin_console = admin_console
        self.__page_container = PageContainer(self.admin_console)

    @PageService()
    def open_server_group(self, group_name):
        """
        Opens a server group with the given name.

        Args:
            group_name (str): the name of the server group to be opened

        Returns:
            None

        Raises:
            Exception:
                The given server is not present
        """
        self.__rtable.access_link(group_name)

    @PageService()
    def add_manual_server_group(self, name, servers=None, service_commcells=None):
        """Creates a manual server group
        Args:
            name(str)                   :  name of the server group
            servers(list)               :  list of servers to associate to the server group
            service_commcells (list)    :  list of service commcell this server group has to be created on (GCM Feature)
        """
        self.admin_console.click_button_using_text(self.admin_console.props["label.addServerGroup"])
        self.admin_console.fill_form_by_id('name', name)
        if servers:
            for server in servers:
                self.__drop_down.search_and_select(select_value=server,id = "selectedServers")

        if service_commcells:
            self.__drop_down.select_drop_down_values(id='GlobConfigInfoCommCellId', values=service_commcells)

        self.__rmodalpanel.save()

    def __select_scope(self, client_scope):
        """Method to select client scope and corresponding value"""
        scope = client_scope.get("scope", None)
        value = client_scope.get("value", None)
        self.__drop_down.select_drop_down_values(values = [scope], drop_down_label = "Client scope")
        if value:
            self.__drop_down.search_and_select(select_value=value,id = "scgScopeEntity")

    @WebAction()
    def __add_rule(self,rules):
        """Method to add rules"""
        for rule in rules:
            rule_for = rule.get("rule_for",None)
            comp = rule.get("matches_with",None)
            value = rule.get("value",None)
            self.admin_console.select_hyperlink(self.admin_console.props["label.addRule"])
            if rule_for and comp is not None:
                self.__drop_down.select_drop_down_values(values=[rule_for], drop_down_id="scgProp")
                self.__drop_down.select_drop_down_values(values=[comp], drop_down_id="scgFilter")
                if value:
                    if self.admin_console.check_if_entity_exists('xpath','//div[contains(@class,"treeview-tree-content")]'):
                        self.__treeview.expand_path(value)
                    if self.admin_console.check_if_entity_exists('xpath','//div[contains(@id,"enumSelection")]'):
                        self.__drop_down.select_drop_down_values(values=value, drop_down_id="enumSelection")
                    if self.admin_console.check_if_entity_exists('xpath','//label[contains(@id,"stringValue")]'):
                        self.admin_console.fill_form_by_id("stringValue", value[0])
            self.__Rmodal_dialog.click_submit()

    @PageService()
    def add_automatic_server_group(self, name, client_scope=None, rules=None, service_commcells=None):
        """
        Creates an automatic server group
        Args:
            name (string):  name of the server group
            client_scope(dict):  client scope and corresponding entity name
                e.g. {"scope":"Clients of user","value": "admin"} or
                     {"scope":"Clients in this CommCell"}
            rules(list):  list of dictionaries of rules for server association
                e.g.  [{"rule_for":"Agents Installed","matches_with":"any in","value":["files","Protected files"]},
                {"rule_for":"Client Display Name ","matches_with":"contains","value":["clientName"]}]
                Note: 1. give path (in the form of list elements) for value in case for treeview
        """
        if not rules:
            raise CVWebAutomationException("You must provide rules in params")

        self.admin_console.click_button_using_text(self.admin_console.props['label.addServerGroup'])
        self.admin_console.fill_form_by_id('name', name)

        if not service_commcells and not client_scope:
            raise CVWebAutomationException("You must provide client scope in params if there is no service commcells")

        if not service_commcells:
            self.admin_console.select_radio(id="automatic")
            self.admin_console.wait_for_completion()
            self.__select_scope(client_scope)

        if service_commcells:
            self.__drop_down.select_drop_down_values(drop_down_id='GlobConfigInfoCommCellId', values=service_commcells)

        self.__add_rule(rules)

        self.admin_console.submit_form()

    def get_all_servers_groups(self, company=None):
        """ Returns all the server groups names present on server groups page

        Args:
            server_type (string): Server Type for filter
            company (string): Company to filter

        Returns:
            List: List of all the servers matching the given args
        """

        if company:
            self.__rtable.select_company(company)

        servergroup_names = self.__rtable.get_column_data("Name", fetch_all=True)
        return servergroup_names

    def delete_server_group(self, name: str, company: str = None):
        """
        Method to delete server group
        Args:
            name (str)      : name of the server group to delete
            company (str)   : name of the company server group belongs to
        """
        self.__rtable.select_company(company if company else 'All')
        self.__rtable.access_action_item(entity_name=name, action_item="Delete")
        self.__Rmodal_dialog.click_submit()

    @PageService()
    def open_create_access_node_dialog(self, name):
        """ Method to open Create access node dialog for a Server Group """
        self.__rtable.access_action_item(name, "Create access node")

    @PageService()
    def get_clients_list(self, name):
        """ Method to get names of all Clients in given Server group """
        self.open_server_group(name)
        self.__rtable.get_column_data(column_name='Name')

    @PageService()
    def is_serverGroup_exist(self, name):
        """Method to check if a server group exists"""
        return self.__rtable.is_entity_present_in_column(column_name= 'Name', entity_name= name)

    @PageService()
    def edit_sg_name(self, new_name):
        """
        Method to edit server group name from details page
        Args:
            new_name(str): new name of the server group
        """
        self.__page_container.edit_title(new_name)

    @PageService()
    def edit_association(self, name, servers):
        """
        Method to add manual server association
        Args:
            name(str): name of the server group
            servers(list): list of the servers to add
        """
        self.__rtable.access_action_item(entity_name=name, action_item="Edit associations")
        self.admin_console.wait_for_completion()
        for server in servers:
            self.__drop_down.search_and_select(select_value=server, id="selectedServers")
        self.__rmodalpanel.save()

    @PageService()
    def search_for(self, search_string: str) -> list:
        """
        Method to search a string in the search bar and return all the server groups listed
        Args:
            search_string(str): string to search for

        returns:
            list : list of server groups matching the string
        """
        self.__rtable.search_for(search_string)
        res = self.__rtable.get_column_data(column_name='Name')
        return res

    @PageService()
    def reset_filters(self):
        """Method to reset the filters applied on the page"""
        self.__rtable.reset_filters()

    @PageService()
    def action_push_network_configuration(self, server_group_name):
        """selects the push network configuration option for the given client

        Args:
            server_group_name (str): name of the server group

        Returns:
            None

        Raises:
            Exception

                if client_name is invalid

                if there is no push network configuration option for the client
        """
        self.__rtable.access_action_item(server_group_name, self.admin_console.props['action.commonAction.pushNetworkConf'])
        self.__Rmodal_dialog.click_submit()
        self.admin_console.check_error_message()
