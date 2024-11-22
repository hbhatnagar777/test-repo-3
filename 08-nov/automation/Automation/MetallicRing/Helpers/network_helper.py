# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for performing network related operations in Metallic Ring

    NetworkRingHelper:

        __init__()                          --  Initializes Network Ring Helper

        start_task                          --  Starts the network related ring tasks on the commcell

        create_oneway_topology              --  Creates oneway network topology

        create_gateway_topology             --  Creates network gateway topology

        check_communication_with_cs         --  checks communication between Commserv and all the infrastructure clients

        check_readiness                     --  Checks readiness for the clients in the commcell

        create_firewall_client_group        --  Creates the firewall smart client group

"""
from AutomationUtils.config import get_config
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs
from cvpysdk.network import Network
from cvpysdk.network_topology import NetworkTopologies

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring
_NW_CONFIG = get_config(json_path=cs.NETWORK_CONFIG_FILE_PATH)
_GT_KEY = "group_type"
_GN_KEY = "group_name"
_MNEMONIC_KEY = "is_mnemonic"


class NetworkRingHelper(BaseRingHelper):
    """ helper class for performing network related operations in Metallic Ring"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.clients = self.commcell.clients
        self.client_groups = self.commcell.client_groups
        self.nw_topologies = NetworkTopologies(self.commcell)

    def start_task(self):
        """
        Starts the network related ring tasks on the commcell
        """
        try:
            self.log.info("Starting Network Ring helper task")
            self.check_communication_with_cs()
            client_groups = _NW_CONFIG.client_groups
            for client_group in client_groups:
                self.log.info(f"Creating client group with name - [{client_group.client_group_name}]")
                if not self.client_groups.has_clientgroup(client_group.client_group_name):
                    rule_list = []
                    for cg_filter in client_group.filters:
                        if hasattr(cg_filter, "filter_value"):
                            if hasattr(cg_filter, "value"):
                                self.log.info("Client group has filter value and value set")
                                rule_list.append(
                                    self.client_groups.create_smart_rule(filter_rule=cg_filter.filter_rule,
                                                                         filter_condition=cg_filter.filter_condition,
                                                                         filter_value=cg_filter.filter_value,
                                                                         value=cg_filter.value))
                                self.log.info("Smart rule request created and added to rules list")
                            else:
                                self.log.info("Client group has no value set")
                                if cg_filter.filter_rule == cs.CG_ASSOC_CG_KEY:
                                    self.log.info(f"Filter rule is [{cs.CG_ASSOC_CG_KEY}]")
                                    cg_obj = self.client_groups.get(cg_filter.filter_value)
                                    rule_list.append(
                                        self.client_groups.create_smart_rule(filter_rule=cg_filter.filter_rule,
                                                                             filter_condition=cg_filter.filter_condition,
                                                                             filter_value=cg_filter.filter_value,
                                                                             value=cg_obj.clientgroup_id))
                                    self.log.info("Smart rule request created and added to rules list")
                                else:
                                    filter_value = cg_filter.filter_value
                                    if cg_filter.filter_value == cs.CG_VALUE_RING:
                                        filter_value = str(_CONFIG.id)
                                        if len(filter_value) <= 2:
                                            filter_value = f"0{filter_value}"
                                    rule_list.append(
                                        self.client_groups.create_smart_rule(filter_rule=cg_filter.filter_rule,
                                                                             filter_condition=cg_filter.filter_condition,
                                                                             filter_value=filter_value,
                                                                             value=filter_value))
                                    self.log.info("Smart rule request created and added to rules list")
                        else:
                            self.log.info("Client group has no filter value or value set")
                            rule_list.append(
                                self.client_groups.create_smart_rule(filter_rule=cg_filter.filter_rule,
                                                                     filter_condition=cg_filter.filter_condition))
                            self.log.info("Smart rule request created and added to rules list")
                    sclient_groups_list = self.client_groups.merge_smart_rules(rule_list, op_value=client_group.criteria)
                    scope_value = client_group.scope_value
                    if client_group.scope_value == cs.CG_SCOPE_COMMCELL:
                        scope_value = _CONFIG.commserv.client_name
                    elif client_group.scope_value == cs.CG_SCOPE_USER:
                        scope_value = _CONFIG.commserv.new_username
                    self.create_firewall_client_group(client_group.client_group_name, sclient_groups_list,
                                                      client_group.client_scope, scope_value)

            one_way_topologies = _NW_CONFIG.topologies.OneWay
            for one_way in one_way_topologies:
                self.log.info(f"Creating oneway network topology- [{one_way.topology_name}]")
                if not self.nw_topologies.has_network_topology(one_way.topology_name):
                    self.create_oneway_topology(one_way.topology_name, one_way.servers, one_way.DMZ_gateways)
                    self.log.info(f"Created oneway network topology- [{one_way.topology_name}]")
                else:
                    self.log.info(f"Topology with given name already exists - [{one_way.topology_name}]")

            nw_gateway_topologies = _NW_CONFIG.topologies.Network_Gateway
            for nw_gateway in nw_gateway_topologies:
                self.log.info(f"Creating network gateway topology- [{nw_gateway.topology_name}]")
                if not self.nw_topologies.has_network_topology(nw_gateway.topology_name):
                    self.create_gateway_topology(nw_gateway.topology_name, nw_gateway.servers,
                                                 nw_gateway.DMZ_gateways, nw_gateway.Infrastructure_machines)
                    self.log.info(f"Created network gateway topology- [{nw_gateway.topology_name}]")
                else:
                    self.log.info(f"Topology with given name already exists - [{nw_gateway.topology_name}]")
            self.check_communication_with_cs()
            self.log.info("All Network ring related tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute network helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def create_oneway_topology(self, topology_name, servers, dmz_gateway_servers, encrypt_traffic=1):
        """
        Creates one way topology
        Args:
            topology_name(str)              -   Name of the topology
            servers(str)                    -   server group name to be used
            dmz_gateway_servers(str)        -   dmz gateway servers group name
            encrypt_traffic                 -   set 1 or 0 to encrypt network traffic or disable it
        """
        self.log.info(f"Request received to create network topology - [{topology_name}]")
        if self.nw_topologies.has_network_topology(topology_name):
            raise Exception(f"Topology with given name [{topology_name}] already exists.")
        cgs = [{_GT_KEY: 2, _GN_KEY: servers, _MNEMONIC_KEY: False},
               {_GT_KEY: 1, _GN_KEY: dmz_gateway_servers, _MNEMONIC_KEY: False}]
        topology = self.nw_topologies.add(topology_name, topology_type=2, client_groups=cgs,
                                          encrypt_traffic=encrypt_traffic)
        self.log.info(f"Network topology - [{topology_name}] created. Pushing network configurations")
        topology.push_network_config()
        self.log.info("Network configuration pushed successfully")

    def create_gateway_topology(self, topology_name, servers, network_gateway,
                                infrastructure_machines, encrypt_traffic=1):
        """
        Creates network gateway topology
        Args:
            topology_name(str)                  -   name of the topology to be created
            servers(str)                        -   Server group name
            network_gateway(str)                -   network gateway name
            infrastructure_machines(str)        -   Infrastructure client group name
            encrypt_traffic(str)                -   set 1 or 0 to encrypt network traffic or disable it
        """
        self.log.info(f"Request received to create network topology - [{topology_name}]")
        if self.nw_topologies.has_network_topology(topology_name):
            raise Exception(f"Topology with given name [{topology_name}] already exists.")
        cgs = [{_GT_KEY: 2, _GN_KEY: servers, _MNEMONIC_KEY: False},
               {_GT_KEY: 1, _GN_KEY: infrastructure_machines, _MNEMONIC_KEY: False},
               {_GT_KEY: 3, _GN_KEY: network_gateway, _MNEMONIC_KEY: False}]

        topology = self.nw_topologies.add(topology_name, topology_type=1, client_groups=cgs,
                                          encrypt_traffic=encrypt_traffic)
        self.log.info(f"Network topology - [{topology_name}] created. Pushing network configurations")
        topology.push_network_config()
        self.log.info("Network configuration pushed successfully")

    def check_communication_with_cs(self):
        """checks communication between commserve and the infrastructure clients in the commcell"""
        self.log.info("Checking communication for clients with CS")
        mas = _CONFIG.media_agents
        ma_clients = []
        for media_agent in mas:
            ma_clients.append(media_agent.client_name)
        self.log.info(f"Checking communication for media agents clients with CS - [{ma_clients}]")
        self.check_readiness(ma_clients)
        self.log.info("Check readiness for Media agent clients complete")

        wcs = _CONFIG.web_consoles
        wc_clients = []
        for web_console in wcs:
            wc_clients.append(web_console.client_name)
        self.log.info(f"Checking communication for web console clients with CS - [{wc_clients}]")
        self.check_readiness(wc_clients)
        self.log.info("Check readiness for web console clients complete")

        wss = _CONFIG.web_servers
        ws_clients = []
        for web_server in wss:
            ws_clients.append(web_server.client_name)
        self.log.info(f"Checking communication for web server clients with CS - [{ws_clients}]")
        self.check_readiness(ws_clients)
        self.log.info("Check readiness for web server clients complete")
        if self.ring.provision_type != cs.RingProvisionType.CUSTOM.value:
            nps = _CONFIG.network_proxies
            np_clients = []
            for network_proxy in nps:
                np_clients.append(network_proxy.client_name)
            self.log.info(f"Checking communication for network proxy clients with CS - [{np_clients}]")
            self.check_readiness(np_clients)
            self.log.info("Check readiness for network proxy clients complete")

        iss = _CONFIG.index_servers
        is_client_nodes = []
        for is_config in iss:
            nodes = is_config.nodes
            for node in nodes:
                is_client_nodes.append(node)
        self.log.info(f"Checking communication for index server clients with CS - [{is_client_nodes}]")
        self.check_readiness(is_client_nodes)
        self.log.info("Check readiness for index server node clients complete")

    def check_readiness(self, clients):
        """Checks readiness for a list of clients passed
            Args:
                clients (list)    --    List of clients for which readiness has to be checked
        """
        for client in clients:
            if not self.clients.has_client(client):
                raise Exception("Client with given name doesn't exist")
            client_object = self.clients.get(client)
            if not client_object.is_ready:
                raise Exception(f"Please check if client [{client}] is reachable from CS")
            self.log.info(f"Client [{client}] is ready")

    def create_firewall_client_group(self, client_group_name, sclient_groups_list, scope, scope_value):
        """
        Creates firewall smart client groups
        Args:
            client_group_name(str)          -   Name of the client group
            sclient_groups_list(dict)       -   Dict of smart client rule list
            scope(str)                      -   scope of the client group
            scope_value(str)                -   value for client group scope
        """
        self.log.info(f"Request received to create new firewall client group - [{client_group_name}]")
        if self.client_groups.has_clientgroup(client_group_name):
            raise Exception(f"Client group with name {client_group_name} already exists")
        cg = self.client_groups.add(client_group_name, clientgroup_description=client_group_name,
                                    scg_rule=sclient_groups_list,
                                    client_scope=scope,
                                    client_scope_value=scope_value)
        self.log.info(f"Firewall client group [{client_group_name}] created successfully")
        network = Network(cg)
        network.force_ssl = True
        if not network.force_ssl:
            raise Exception(f"Failed to set Force ssl property for client group [{client_group_name}]")
        self.log.info(f"Force ssl network property set on the client group - [{client_group_name}]")
