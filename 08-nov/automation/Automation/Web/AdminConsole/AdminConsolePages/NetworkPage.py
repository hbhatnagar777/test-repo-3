# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the functions that can be performed on the Network Topologies and
Backup Networks Page

class:
    NetworkPage()

Functions:
    add_topology()              - Add a new network topology

    edit_topology()             - Edit a network topology

    delete_topology()           - Delete a network topology

    download_network_summary()  - Download network summary of a client in network topology

class:
    BackupNetworks

Functions:
    get_all_backupnetworks()    - Return the list of backup network pairs

    add_backupnetworks()        - Add a new backup network pair

    edit_backupnetworks()       - Edit a backup network pair

    delete_backupnetworks()     - Delete a backup network pair
    

"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.Components.table import Rtable, CVTable
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.panel import ModalPanel, DropDown, RModalPanel, RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.dropdown import CVDropDown
from Web.AdminConsole.adminconsole import AdminConsole
import time


class NetworkPage:
    """Class for the Network page in command center"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = self._admin_console.driver
        self._admin_console.load_properties(self, unique=True)
        self.log = self._admin_console.log
        self.__table = Rtable(self._admin_console)
        self.__panel = ModalPanel(self._admin_console)
        self.__rpanel = RModalPanel(self._admin_console)
        self.__dialog = RModalDialog(self._admin_console)
        self._cvtable = CVTable(self._admin_console)
        self.__dropdown = DropDown(self._admin_console)
        self.__rdropdown = RDropDown(self._admin_console)
        self.__wizard = Wizard(self._admin_console)

        self._three_group_topologies = [
            "Network gateway", "One-way forwarding"]
        self._four_group_topologies = ["Cascading gateways"]
        self.options = {
            "1": "firstGroupOptions",
            "2": "secondGroupOptions",
            "3": "thirdGroupOptions",
            "4": "fourthGroupOptions"
        }
        self.topology_labels = {
            "One-way": "label.oneway",
            "Two-way": "label.twoway",
            "Network gateway": "label.viaNetworkGateway",
            "Cascading gateways": "label.cascadingGateways",
            "One-way forwarding": "label.onewayforwarding"
        }
        self.protocol_labels = {
            "Encrypted": "label.protocolEncrypted",
            "Authenticated": "label.protocolAuthenticated",
            "Regular": "label.protocolRegular",
            "Raw": "label.protocolRaw"
        }

        self.dropdown_ids = ["EXTERNAL", "INTERNAL", "PROXIES",
                             "PROXY_PERIMETER"]
        self._cvdropdown = CVDropDown(self._admin_console)

    @WebAction()
    def check_advanced_settings_disabled_topology(self, group_type):
        """Method to check if the advanced properties of topologies page for a particular client group
        is disabled
        Args:
            group_type (str) : Client group number
        """
        xp = f'//div[@id="advancedOptions_Group{group_type}"][@disabled]'
        self._admin_console.scroll_into_view(xp)
        if self._driver.find_element(By.XPATH, xp):
            return True
        return False

    @PageService()
    def click_topologies(self):
        """Click the tab Network topologies"""
        self._admin_console.access_tile('tileMenuSelection_networkTopologies')

    @PageService()
    def delete_topology(self, topology_name: str):
        """Delete the topology
        Args:
            topology_name : Name of the topology which has to be deleted
        """
        self.__table.access_action_item(
            topology_name, self._admin_console.props["NetworkPage"]["action.delete"])
        if self._admin_console.ext == ".properties":
            self.__dialog.type_text_and_delete("DELETE")
        else:
            self.__dialog.type_text_and_delete(self._admin_console.props["NetworkPage"]["button.deleteNwTopology"].upper(),
                                               button_name=self._admin_console.props["NetworkPage"]["button.deleteNwTopology"])

    @PageService()
    def add_topology(self, topology_name: str, topology_type: str, client_group_list: list,
                     client_type: str = "servertype", https: bool = False, wildcard_proxy: bool = False):
        """
        Add a topology in command center

        Supported Args :-

        topology_name               : Name of topology

        topology_type               : Type of topology (One-way, Two-way, Network gateway, Cascading gateways, One-way
                                        forwarding

        client_group_list           : List of clients groups in order of the topology

        example : for one-way ["SourceGroup", "DestinationGroup"]
                : for Network_gateway, One-way forwarding ["SourceGroup", "DestinationGroup", "ProxyGroup"]
                : for Cascading-gateways ["SourceGroup", "DestinationGroup", "ServerGateways", "DmzGateways"]

        client_type (str)           : Type of the client group

        https (boolean)             : True, if the topology has to be encrypted

        wildcard_proxy (boolean)    : True, if the proxy is of type wildcard

        """
        self.__table.access_toolbar_menu(
            self._admin_console.props["NetworkPage"]["pageHeader.addTopology"])
        client_type_label = self._admin_console.props["NetworkPage"]["label.clientType.servers"]
        if client_type != "servertype":
            client_type_label = self._admin_console.props["NetworkPage"]["label.clientType.laptops"]
        self.__wizard.fill_text_in_field(id="topologyName", text=topology_name)
        self.__wizard.select_radio_button(label=client_type_label)
        topology_type_label = self.topology_labels[topology_type]
        self.__wizard.select_drop_down_values(id="topologyType",
                                              values=[self._admin_console.props["NetworkPage"][topology_type_label]])
        # Click Next to select the client groups
        self.__wizard.click_button(id="Next")
        self._admin_console.wait_for_completion()
        for count, cg in enumerate(client_group_list):
            self.__rdropdown.select_drop_down_values(drop_down_id=self.dropdown_ids[count],
                                                     values=[cg])

            if wildcard_proxy:
                advanced_label = self._admin_console.props["NetworkPage"]["label.advanced"]
                self.__wizard.enable_toggle(advanced_label, index=1)
                # Enable the force servers toggle
                toggle_label_wildcardproxy = self._admin_console.props["NetworkPage"]["label.servertext"].replace(".",
                                                                                                                  "")
                self.__wizard.enable_toggle(toggle_label_wildcardproxy)
        # Click Next
        self.__wizard.click_button(id='Next')
        self._admin_console.wait_for_completion()
        if https:
            encrypt_toggle_label = self._admin_console.props["NetworkPage"]['label.encryptTraffic']
            self.__wizard.enable_toggle(encrypt_toggle_label)
        self.__wizard.click_button(id="Submit")
        self._admin_console.wait_for_completion()

    @PageService()
    def edit_topology(self, topology_name: str, firewall_groups: list = None, **kwargs):
        """
        Method to edit the topology in adminconsole

        Arguments :-

        topology_name: Name of the topology to edit

        firewall_groups(list of dict)  --   client group names and client group types

        For eg:
                [{'group_type':2, 'group_name': "test1", 'is_mnemonic': False, tunnelport: "2500", keepalive: "170"},
                {'group_type':1, 'group_name': "test2", 'is_mnemonic': False,  tunnelport: "2500", keepalive: "170"},
                {'group_type':3, 'group_name': "test3", 'is_mnemonic': False, tunnelport: "2500", keepalive: "170"},
                {'group_type':4, 'group_name': "test4", 'is_mnemonic': False, tunnelport: "2500", keepalive: "170"}]

        kwargs             (dict)          --       Key value pairs for supported arguments

        Supported Arguments :-

        TunnelProtocol     (str)           --       Protocol to be selected from dropdown

        Streams            (str)           --       Number of tunnels in topology

        EncryptTraffic     (bool)          --       Enable or disable encrypt network route option

        CgChanges          (bool)          --       'True' for changing the client groups of the topology

        ModifyTopologyType (str)           --        Value for modification of topology type

        ModifyTopologyName (bool)          --       Value for modification of the topology name

        ModifyClientType   (str)           --       Value of the radio button Client type : For servers - servertype 
                                                    else clienttype
        """
        self.__table.access_link(topology_name)

        if firewall_groups:
            group_count = len(firewall_groups)
            toggle_indeces = [1, group_count, 2, 3]
        CG = kwargs.get('CgChanges')

        # Client type if provided has to be updated
        clientType = kwargs.get("ModifyClientType")

        if clientType:
            client_type_label = self._admin_console.props["NetworkPage"]["label.clientType.servers"]
            if clientType != "servertype":
                client_type_label = self._admin_console.props["NetworkPage"]["label.clientType.laptops"]
            self.__wizard.select_radio_button(label=client_type_label)

        # Topology type if provided it has to be updated
        if kwargs.get("ModifyTopologyType"):
            topology_type = kwargs.get("ModifyTopologyType")
            topology_type_label = self.topology_labels[topology_type]
            self.__wizard.select_drop_down_values(id="topologyType",
                                                  values=[
                                                      self._admin_console.props["NetworkPage"][topology_type_label]])
        if kwargs.get("ModifyTopologyName"):
            self.__wizard.fill_text_in_field(
                id="topologyName", text=kwargs.get("ModifyTopologyName"))

        # Click Next
        self.__wizard.click_button(id='Next')
        self._admin_console.wait_for_completion()
        if firewall_groups:
            for count, client_group in enumerate(firewall_groups):
                # If particular client group itself should be changed
                cg_type = client_group.get("group_type")
                if CG:
                    self.__rdropdown.select_drop_down_values(drop_down_id=self.dropdown_ids[int(cg_type) - 1],
                                                             values=[client_group.get('group_name')])

                is_mnemonic = client_group.get('is_mnemonic', False)

                if not is_mnemonic:
                    advanced_label = self._admin_console.props["NetworkPage"]["label.advanced"]
                    self.__wizard.enable_toggle(
                        advanced_label, index=toggle_indeces[int(cg_type) - 1])

                    # Edit the settings only if provided in the inputs
                    tunnel_port = client_group.get('tunnelport')

                    keep_alive_interval = client_group.get('keepalive')

                    if tunnel_port:
                        self.__wizard.fill_text_in_field(id=f"{self.dropdown_ids[int(cg_type) - 1]}-tunnelPort",
                                                         text=tunnel_port)
                    if keep_alive_interval:
                        self.__wizard.fill_text_in_field(id=f"{self.dropdown_ids[int(cg_type) - 1]}-keepAliveInterval",
                                                         text=keep_alive_interval)
                else:
                    # Check if the advanced settings is actually disabled when CG is smart
                    self.check_advanced_settings_disabled_topology(
                        client_group.get('group_type'))

        self.__wizard.click_button(id='Next')
        self._admin_console.wait_for_completion()
        # If tunnel protocol or streams have to be updated
        tunnel_protocol = kwargs.get("TunnelProtocol")
        streams = kwargs.get("Streams")

        if streams:
            self.__wizard.fill_text_in_field(
                id="tunnelsPerRoute", text=streams)

        encrypt_traffic = kwargs.get("EncryptTraffic")

        if encrypt_traffic is not None:

            encrypt_toggle_label = self._admin_console.props["NetworkPage"]['label.encryptTraffic']
            if encrypt_traffic:
                self.__wizard.enable_toggle(encrypt_toggle_label)
            else:
                self.__wizard.disable_toggle(encrypt_toggle_label)

        if tunnel_protocol:
            tunnel_protocol_label = self.protocol_labels[tunnel_protocol]
            self.__wizard.select_drop_down_values(id="tunnelProtocol", values=[
                self._admin_console.props["NetworkPage"][tunnel_protocol_label]])
        self.__wizard.click_button(id="Submit")
        self._admin_console.wait_for_completion()

    @PageService()
    def download_network_summary(self, client_name):
        """Download the network summary of a client
            Args:
                client_name: Name of the client whose summary is to be downloaded
        """
        self.__table.access_toolbar_menu(
            self._admin_console.props["NetworkPage"]["pageHeader.downloadFWSummary"])
        self.__wizard.select_drop_down_values(
            "ServersDropdown", values=[client_name])
        self.__dialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def remove_fwconfig_files(self):
        """Remove the fwconfig files downloaded"""
        import fnmatch
        import os
        for rootDir, subdirs, filenames in os.walk(os.getcwd()):
            for filename in fnmatch.filter(filenames, 'FwConfig*'):
                try:
                    os.remove(os.path.join(os.getcwd(), filename))
                except OSError:
                    self.log.info("Error while deleting file")

    @WebAction()
    def _delete_interfaces(self, interface):
        """Method to delete the first dips config between two client computer when inside the panel"""
        self.__panel._expand_accordion('Select network pairs')
        self._cvtable.access_action_item(interface, "Remove")
        self.__panel.submit()
        self.__panel.submit()

    @PageService()
    def click_dips(self):
        """Click the DIP tile in network page"""
        self._admin_console.access_tile('tileMenuSelection_backupNetworks')

    @PageService()
    def create_dips(self, cg1, cg2, interface1="No Default Interface",
                    interface2="No Default Interface", **kwargs):
        """Select the pair of computer for DIPs

            Args:
                cg1 -- Client group/ Client
                cg2 -- Another client group/Client

                **kwargs -- Keyword arguements

                Supported kwargs are:

                Wildcard1 -- wildcard filter for the first client group

                Wildcard2 -- wildcard filter for the second client group
        """

        wildcard1 = kwargs.get('Wildcard1')
        wildcard2 = kwargs.get('Wildcard2')
        self._admin_console.select_hyperlink('Add')
        self.__panel.search_and_select(None, cg1, id="s2id_firstComputer")
        self.__panel.search_and_select(None, cg2, id="s2id_secondComputer")

        try:
            self.__panel._expand_accordion('Select network pairs')
            self._admin_console.select_hyperlink('Add network pairs')
            if wildcard1:
                self._cvdropdown.enter_value_in_dropdown(
                    "interface1", wildcard1)
                time.sleep(2)
            else:
                if interface1 != 'No Default Interface':
                    self._cvdropdown.select_value_from_dropdown(
                        "interface1", interface1)

            if wildcard2:
                self._cvdropdown.enter_value_in_dropdown(
                    "interface2", wildcard2)
                time.sleep(2)
            else:
                # Click the dropdown of selecting the Network interface
                if interface2 != 'No Default Interface':
                    self._cvdropdown.select_value_from_dropdown(
                        "interface2", interface2)

            # Enable the dip
            self._admin_console.checkbox_select('status')
            self.__panel.submit()
            self.__panel.submit()

        except Exception as e:
            raise Exception(e)

    @PageService()
    def delete_dips(self, cg1, cg2, interface):
        """Delete the data interface pairs configured through the automation

            Inputs --

             cg1 -> Client group/Client name 1

             cg2 ->  Client group/Client name 2
        """
        self._admin_console.select_hyperlink('Add')
        self.__panel.search_and_select(None, cg1, id="s2id_firstComputer")
        self.__panel.search_and_select(None, cg2, id="s2id_secondComputer")
        self._delete_interfaces(interface)


class BackupNetworks:
    """Class for Data Interface Pairs aka Backup Networks"""

    def __init__(self, admin_console):
        """Initialize the class with adminconsole object"""
        self._adminconsole = admin_console
        self._table = Rtable(admin_console)
        self._wizard = Wizard(admin_console)
        self._rmodalpanel = RModalPanel(admin_console)
        self._dialog = RModalDialog(admin_console)
        self.log = self._adminconsole.log
        self._interface_input_id_1 = "interfaceOnSourceComputer"
        self._interface_input_id_2 = "interfaceOnDestinationComputer"
        self._edit_interface_input_id1 = "editedInterfaceOnSourceComputer"
        self._edit_interface_input_id2 = "editedInterfaceOnDestinationComputer"

    def get_all_backupnetworks(self):
        """This function returns all the backup networks listed in table"""
        return self._table.get_table_data(all_pages=False)

    @WebAction()
    def __select_interfaces(self, interface1=None, interface2=None, edit=False):
        """Search and select the interfaces from the autocomplete dropdown
        Args:
            interface1 (str) : Interface/Wildcard of the first entity

            interface2 (str) : Interface/Wildcard of the second entity

            edit (bool) - True if we are in edit modal panel
        """
        interface1_id = self._interface_input_id_1 if not edit else self._edit_interface_input_id1
        interface2_id = self._interface_input_id_2 if not edit else self._edit_interface_input_id2

        if interface1:
            self._rmodalpanel.search_and_select(
                select_value=interface1, id=interface1_id)
        else:
            self._rmodalpanel._RModalPanel__clear_input_field(f"//*[@id='{interface1_id}' and contains(@class, 'MuiInputBase-input')]")
        # Second interface
        if interface2:
            self._rmodalpanel.search_and_select(
                select_value=interface2, id=interface2_id)
        else:
            self._rmodalpanel._RModalPanel__clear_input_field(
                f"//*[@id='{interface2_id}' and contains(@class, 'MuiInputBase-input')]")


    @PageService()
    def add_backupnetworks(self, entity1: str, entity2: str, interface1: str = None, interface2: str = None):
        """
        Add a new backup network pair in command center
        Args:
            entity1: First input a server or a server group

            entity2: Second input a different server or a server group

            interface1: Interface to be selected for the first entity

            interface2: Interface to be selected for the second entity

        """
        # Click Add in the backup networks page
        self._table.access_toolbar_menu(
            self._adminconsole.props["label.addInterfacePairs"])
        try:
            self._rmodalpanel.search_and_select(
                select_value=entity1, id="computerOne")
            self._rmodalpanel.search_and_select(
                select_value=entity2, id="computerTwo")

            # Click Next to select Interfaces
            self._wizard.click_button(id='Next')
            self._adminconsole.check_for_react_errors(raise_error=True)
            self._adminconsole.wait_for_completion()
            self.__select_interfaces(interface1, interface2)

            # Add the pair
            self._wizard.click_add_icon()
            self._adminconsole.check_for_react_errors(raise_error=True)

            # Move to the confirm page
            self._wizard.click_button(id='Next')
            self._adminconsole.check_for_react_errors(raise_error=True)
            self._wizard.click_button(id="Submit")
            self._adminconsole.check_for_react_errors(raise_error=True)
        except Exception as e:
            self._wizard.click_cancel()
            raise Exception(e)

    @PageService()
    def edit_backupnetworks(self, entity1: str, entity2: str, interface1: str = None, interface2: str = None, disable: bool = False):
        """
        Edit the backup network
        Args:
            entity1: First input a server or a server group

            entity2: Second input a different server or a server group

            interface1: Interface to be selected for the first entity

            interface2: Interface to be selected for the second entity

            disable: Boolean value to enable/disable the network pair
        """
        try:
            self._table.access_action_item(
                entity1 + " and " + entity2, "Edit", search=False)
            self._dialog.click_button_on_dialog(aria_label="Modify")
            # Edit the interfaces if arguments are passed
            if interface1 and interface2:
                self.__select_interfaces(interface1, interface2, edit=True)
            self._dialog.click_button_on_dialog(aria_label="Save")

            # Enable or disable the backup networks
            self._dialog.click_button_on_dialog(aria_label="Modify")
            if disable:
                self._wizard.checkbox.uncheck(
                    id=f"{interface1}_{interface2}_status")
            else:
                self._wizard.checkbox.check(
                    id=f"{interface1}_{interface2}_status")
            self._dialog.click_button_on_dialog(aria_label="Save")
            self._rmodalpanel.save()
        except Exception as e:
            self._wizard.click_cancel()
            raise Exception(e)

    @PageService()
    def delete_backupnetworks(self, entity1: str, entity2: str):
        """Delete the backup network pair
            Args:
                entity1 - Name of the first entity : client or client group

                entity2 - Name of the second entity : client or client group
        """
        self._table.access_action_item(
            entity1 + " and " + entity2, "Delete", search=False)
        self._dialog.type_text_and_delete("DELETE")
