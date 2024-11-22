# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing network operations

NetworkHelper is the only class defined in this file

NetworkHelper: Helper class to perform network operations

NetworkHelper:
    __init__()                      --  initializes network helper object

    enable_firewall()               -- Enables firewall on given machine list

    disable_firewall                -- disabls firewall on given machine list

    exclude_machine()               -- adds a machine to firewall exclusion list of remote
                                       client machine

    remove_machine()                -- removes machine from firewall exclusion list of remote
                                       client machine

    set_one_way()                   -- sets one-way firewall between two entities

    set_two_way()                   -- sets two-way firewall between two entities

    set_via_proxy()                 -- sets via proxy route between two entities

    push_config_client()            -- performs push network configuration on a list of clients

    push_config_clientgroup()       -- performs push network configuration on a list of
                                        client groups

    set_via_gateway()               -- sets via gateway route on a client/client group

    enable_proxy()                  -- marks a client/client group as proxy

    enable_roaming_client()         -- enables roaming client option on a client/client group

    set_tunnelport()                -- sets the specified port as tunnel port on given list of
                                        clients/client groups

    remove_network_config()         -- removes network configuration on the given list of
                                        clients/client groups

    set_gui_tppm()                  -- configure GUI tppm

    set_wswc_tppm()                 -- configure webserver-webconsole tppm

    outgoing_route_settings()       -- sets options for outgoing routes on client/client group

    validate()                      -- performs check readiness and backup , restore jobs
                                        on the client

    validate_with_plan()            -- performs check readiness and backup , restore jobs
                                        on the client

    validate_tunnel_port()          -- validates the default tunnel port set on the client
                                        or client group

    validate_keep_alive()           -- validates the default keep alive interval on the client
                                        or client group

    validate_tunnel_init()          -- validates the default tunnel init interval on the client
                                        or client group

    validate_other_defaults()       -- validates default values for force ssl, proxy, bind open
                                        ports and roaming client on a client or client group

    client_tunnel_port()            -- returns client tunnel port

    do_cvping()                     -- Does a cvping on the specified port on destination
                                        client from source client

    s_bind_to_interface()           -- Sets registry key sBindToInterface on the client and
                                        validates if client is using the specified interface

    cv_ip_info()                    -- Does a host name lookup for specified destination host
                                        from source

    cleanup_network()               --  handles all network clean-up part

    one_way_topology()              -- creates a one way network topology

    two_way_topology()              -- creates a two way network topology

    proxy_topology()                -- creates a proxy topology

    cascading_gateways_topology()   -- creates a cascading gateway topology

    delete_topology()               -- deletes a network topology

    push_topology()                 -- performs a push network topology

    modify_topology()               -- modifies properties of existing network topology

    set_network_throttle()          -- sets network throttling on client/client group

    remove_network_throttle()       -- removes network throttling on client/client group

    get_network_summary()           -- gets the network summary for a list of clients

    get_network_topology_id()       -- gets the id of a network topology

    run_server()                    -- Starts the server given with bat file path and command

    server_client_connection()      -- Initiates server/client connection on CVNetworkTestTool with specified options

    get_dips_client()               -- Gets Data interface pairs for a client

    add_dips()                      -- Adds data(backup) interface pairs on clients/client groups

    delete_dips()                   -- Deletes data(backup) interface pairs on clients/client groups

    email()                         -- Send an email to the respective recipients
"""

import re
import os
import time
import uuid

from cvpysdk.storage_pool import StoragePools
from cvpysdk.network_topology import NetworkTopologies
from cvpysdk.backup_network_pairs import BackupNetworkPairs
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import config
from Server.serverhelper import ServerTestCases
from Server.organizationhelper import OrganizationHelper
from Server.Plans.planshelper import PlansHelper
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
import smtplib

from . import networkconstants


class NetworkHelper(object):
    """Helper class to perform network operations"""

    def __init__(self, testcase):
        """Initializes networkhelper object """
        self.log = testcase.log
        self._testcase = testcase
        self.commcell = testcase.commcell
        self.storage_pool = StoragePools(self.commcell)
        self.organizationHelperObj = OrganizationHelper(self.commcell)
        self.serverbase = CommonUtils(self.commcell)
        self.server = ServerTestCases(self._testcase)
        self.options = OptionsSelector(self.commcell)
        self.entities = CVEntities(self._testcase)
        self.topologies = NetworkTopologies(self.commcell)
        self.backup_network_pairs = BackupNetworkPairs(self.commcell)
        self.post_trivial_list = None
        self.pre_trivial_list = None
        self.app_firewall_value1 = None
        self.app_firewall_value2 = None
        self.app_fwoutgoing_routes1 = None
        self.app_fwoutgoing_routes2 = None
        self.network_config = {
            "disable_firewall":
                {
                    "clients": [],
                    "ports": []
                },
            "delete_machine":
                {
                    "clients": []
                },
            "remove_network_config": {
                "entities": []
            },
            "s_bind_to_interface": {
                "client": ""
            }
        }

    def __repr__(self):
        """Representation string for the instance of the NetworkHelper class."""
        return "NetworkHelper class instance for test case: '{0}'".format(self._testcase.name)

    def __del__(self):
        """Cleaning up entities that were created during the test case"""
        self.log.info("Deleting any objects which were cerated by Network Helper object")
        self.entities.cleanup()

    def exclude_machine(self, clients, machine_to_exclude=None):
        """Adds machine to firewall exclusion list in all the given client list

             Args:
                clients               (list)   --  client list to add the exclusion

                machine_to_exclude    (str)   --  hostname or IP address of the machine to exclude

            Returns:
                None:
                    if machine is added successfully to firewall exclusion list

            Raises:
                Exception:
                    if any error occurred while adding firewall exclusion

        """
        for client in clients:
            # update cleanup dictionary before success to handle exception
            self.network_config['delete_machine']['clients'].append(client)

            # create a machine object to execute the command
            machine_obj = Machine(client, self.commcell)

            self.log.info("adding firewall exclusion on client {0}".format(client))
            machine_obj.add_firewall_machine_exclusion(machine_to_exclude)

    def enable_firewall(self, machine_names, tunnel_ports):
        """Adds inbound rule to allow port and start firewall service in all the given clients
             Args:
                machine_names   (list)   --  list of client names

                tunnel_ports    (list)   --  list of tunnel ports

            Returns:
                None:
                    if inbound rule is added and firewall is started successfully
            Raises:
                Exception:
                    if any error occurred while adding rule or starting firewall

        """
        for (machine_name, tunnel_port) in zip(machine_names, tunnel_ports):
            self.network_config['disable_firewall']['clients'].append(machine_name)
            self.network_config['disable_firewall']['ports'].append(str(tunnel_port))

            machine_obj = Machine(machine_name, self.commcell)

            self.log.info(
                "Adding firewall allow port rule on client {0}".format(machine_name))
            machine_obj.add_firewall_allow_port_rule(tunnel_port)

            self.log.info("starting firewall on client {0}".format(machine_name))
            machine_obj.start_firewall()

    def disable_firewall(self, machine_names, tunnel_ports):
        """removes inbound rule to allow port and stop firewall service in all the given clients
             Args:
                machine_names   (list)   --  list of client names

                tunnel_ports    (list)   --  list of tunnel ports

            Returns:
                None:
                    if inbound rule is removed and firewall is started successfully
            Raises:
                Exception:
                    if any error occurred while removing rule or stopping firewall

        """
        for (machine_name, tunnel_port) in zip(machine_names, tunnel_ports):
            try:
                machine_obj = Machine(machine_name, self.commcell)

                self.log.info("disabling firewall on client {0}".format(machine_name))
                machine_obj.stop_firewall()

                self.log.info(
                    "removing firewall allow port rule on client {0}".format(machine_name))
                machine_obj.remove_firewall_allow_port_rule(tunnel_port)

            except Exception as excp:
                self.log.error(excp)
                self.log.info("Using machine credentials to disable firewall")
                config_json = config.get_config()
                if not config_json.Network.username:
                    raise Exception("Username is missing in config.json. "
                                    "Please add username and password")
                cl_obj = self.commcell.clients.get(machine_name)
                machine_obj = Machine(cl_obj.client_hostname,
                                      username=config_json.Network.username,
                                      password=config_json.Network.password)
                machine_obj.stop_firewall()
                machine_obj.remove_firewall_allow_port_rule(tunnel_port)

    def email(self, fromaddr, toaddr, subject, body, files=()):
        """
        Send an email with the provided information.
            Args:
                fromaddr       (str)        -- From address
                toaddr         (list[str])  -- To address
                subject        (str)        -- Subject of email
                body           (str)        -- Body of email
                files          (list[str])  -- File name to be send as attachment

            Resturns:
                None

            Raises:
                Exception:
                    if any error occurred while sending email

        """
        try:
            msg = MIMEMultipart()
            msg['From'] = fromaddr
            msg['To'] = toaddr
            fr = 'SP' + self.commcell.version.split('.')[1]
            msg['Subject'] = fr + " " + subject
            msg.attach(MIMEText(body, 'html'))

            for f in files:
                attachment = open(f, "rb")
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= %s" % f)
                msg.attach(part)

            server = smtplib.SMTP("mail.commvault.com")
            text = msg.as_string()
            server.sendmail(fromaddr, toaddr.split(","), text)
            server.quit()
            self.log.info(f"Email sent successfully to {toaddr}")

        except Exception as excp:
            self.log.error(excp)

    def remove_machine(self, clients, excluded_machine=None):
        """removes machine from firewall exclusion list in all the given client list

             Args:
                clients             (list)  --  list of client names

                excluded_machine    (str)   --  hostname or IP address of the machine to exclude

            Returns:
                None:
                    if machine is removed successfully from firewall exclusion list

            Raises:
                Exception:
                    if any error occurred while removing firewall exclusion

        """
        for client in clients:
            try:
                machine_obj = Machine(client, self.commcell)
                self.log.info("removing firewall exclusion on client {0}".format(client))
                machine_obj.remove_firewall_machine_exclusion(excluded_machine)

            except Exception as excp:
                self.log.error(excp)

    def set_one_way(self, entity1, entity2):
        """Sets one-way firewall between two entities (client/client group)

        Args:
                entity1(dict)  -- dict of entity name
                {'clientName':val}

                entity2(dict)  -- dict of entity name
                {'clientGroupName':val}

                Note: pass the key name based on entity

            Example:
                entity1:
                {
                'clientName': 'centOS',
                }

                entity2:
                {
                'clientGroupName': 'Laptop Clients'
                }

        Raises:
                Exception:
                    if the required key is missing in the input value passed

        """
        self.log.info("Setting one-way firewall")
        try:
            obj1 = self._get_entity_object(entity1)
            if obj1[1] == 'client':
                self.network_config['remove_network_config']['entities']. \
                    append({'clientName': entity1['clientName']})
                incoming_connection1 = [
                    {
                        'state': 'BLOCKED',
                        'entity': entity1['clientName'],
                        'isClient': True
                    }]

            else:
                self.network_config['remove_network_config']['entities'].append(
                    {'clientGroupName': entity1['clientGroupName']})
                incoming_connection1 = [
                    {
                        'state': 'BLOCKED',
                        'entity': entity1['clientGroupName'],
                        'isClient': False
                    }]

            obj2 = self._get_entity_object(entity2)
            if obj2[1] == 'client':
                self.network_config['remove_network_config']['entities']. \
                    append({'clientName': entity2['clientName']})
                incoming_connection2 = [
                    {
                        'state': 'RESTRICTED',
                        'entity': entity2['clientName'],
                        'isClient': True
                    }]

            else:
                self.network_config['remove_network_config']['entities'].append(
                    {'clientGroupName': entity2['clientGroupName']})
                incoming_connection2 = [
                    {
                        'state': 'RESTRICTED',
                        'entity': entity2['clientGroupName'],
                        'isClient': False
                    }]

            self.log.info("Setting {0} as restricted on incoming connections of {1}"
                          "".format(list(entity2.values())[0], list(entity1.values())[0]))

            obj1[0].network.set_incoming_connections(
                incoming_connection2)

            self.log.info("Setting {0} as blocked on incoming connections of {1}"
                          "".format(list(entity1.values())[0], list(entity2.values())[0]))

            obj2[0].network.set_incoming_connections(incoming_connection1)

        except Exception as excp:
            self.log.exception("Exception raised with error {0}".format(excp))

    def set_two_way(self, entity1, entity2):
        """Sets two-way firewall between two client/client group

        Args:
                entity1(dict)  -- dict of entity name
                {'clientName':val}

                entity2(dict)  -- dict of entity name
                {'clientGroupName':val}

                Note: pass the key name based on entity

            Example:
                entity1:
                {
                'clientName': 'centOS',
                }

                entity2:
                {
                'clientGroupName': 'Laptop Clients'
                }

        Raises:
                Exception:
                    if the required key is missing in the input value passed

        """

        self.log.info("Setting two-way firewall")
        try:
            obj1 = self._get_entity_object(entity1)
            if obj1[1] == 'client':
                self.network_config['remove_network_config']['entities'].append({
                    'clientName': entity1['clientName']})
                incoming_connection1 = [
                    {
                        'state': 'RESTRICTED',
                        'entity': entity1['clientName'],
                        'isClient': True
                    }]

            else:
                self.network_config['remove_network_config']['entities'].append({
                    'clientGroupName': entity1['clientGroupName']})
                incoming_connection1 = [
                    {
                        'state': 'RESTRICTED',
                        'entity': entity1['clientGroupName'],
                        'isClient': False
                    }]

            obj2 = self._get_entity_object(entity2)
            if obj2[1] == 'client':
                self.network_config['remove_network_config']['entities'].append({
                    'clientName': entity2['clientName']})
                incoming_connection2 = [
                    {
                        'state': 'RESTRICTED',
                        'entity': entity2['clientName'],
                        'isClient': True
                    }]

            else:
                self.network_config['remove_network_config']['entities'].append({
                    'clientGroupName': entity2['clientGroupName']})
                incoming_connection2 = [
                    {
                        'state': 'RESTRICTED',
                        'entity': entity2['clientGroupName'],
                        'isClient': False
                    }]

            self.log.info("Setting {0} as restricted on incoming connections of {1}".
                          format(list(entity2.values())[0], list(entity1.values())[0]))
            obj1[0].network.set_incoming_connections(incoming_connection2)
            self.log.info("Setting {0} as restricted on incoming connections of {1}".
                          format(list(entity1.values())[0], list(entity2.values())[0]))
            obj2[0].network.set_incoming_connections(incoming_connection1)
            self.log.info("Setting done...")

        except Exception as excp:
            self.log.exception("Exception raised with error {0}".format(excp))

    def set_via_proxy(self, entity1, entity2, proxy):
        """Sets firewall via proxy between two client/client group

                Args:
                entity1(dict)  -- dict of entity name and it's type
                {'entity':val,'isClient':val}

                entity2(dict)  -- dict of entity name and it's type
                {'entity':val,'isClient':val}

                proxy(dict)    -- dict of entity name and it's type
                {'entity':val,'isClient':val}

            Example:

                {
                'entity': 'centOS',
                'isClient' : True
                }



        Raises:
                Exception:
                    if the required key is missing in the input value passed



        """

        try:
            self.log.info("Setting firewall via proxy between the clients")
            if entity1['isClient']:
                obj1 = self.commcell.clients.get(entity1['entity'])
                self.network_config['remove_network_config']['entities'].append({
                    'clientName': entity1['entity']})

            else:
                obj1 = self.commcell.client_groups.get(entity1['entity'])
                self.network_config['remove_network_config']['entities'].append({
                    'clientGroupName': entity1['entity']})

            if entity2['isClient']:
                obj2 = self.commcell.clients.get(entity2['entity'])
                self.network_config['remove_network_config']['entities'].append({
                    'clientName': entity2['entity']})

            else:
                obj2 = self.commcell.client_groups.get(entity2['entity'])
                self.network_config['remove_network_config']['entities'].append({
                    'clientGroupName': entity2['entity']})

            if proxy['isClient']:
                obj3 = self.commcell.clients.get(proxy['entity'])
                self.network_config['remove_network_config']['entities'].append({
                    'clientName': proxy['entity']})

            else:
                obj3 = self.commcell.client_groups.get(proxy['entity'])
                self.network_config['remove_network_config']['entities'].append({
                    'clientGroupName': proxy['entity']})

            incoming_connection = [
                {
                    'state': 'RESTRICTED',
                    'entity': entity1['entity'],
                    'isClient': entity1['isClient']
                },
                {
                    'state': 'RESTRICTED',
                    'entity': entity2['entity'],
                    'isClient': entity2['isClient']
                }
            ]

            obj3.network.proxy = True
            obj3.network.set_incoming_connections(incoming_connection)

            incoming_connection = [
                {
                    'state': 'BLOCKED',
                    'entity': proxy['entity'],
                    'isClient': proxy['isClient']
                }]

            obj1.network.set_incoming_connections(incoming_connection)
            obj2.network.set_incoming_connections(incoming_connection)

            outgoing_routes1 = [{
                'routeType': 'VIA_PROXY',
                'remoteEntity': entity1['entity'],
                'remoteProxy': proxy['entity'],
                'isClient': entity1['isClient']
            }]

            obj2.network.set_outgoing_routes(outgoing_routes1)

            outgoing_routes2 = [{
                'routeType': 'VIA_PROXY',
                'remoteEntity': entity2['entity'],
                'remoteProxy': proxy['entity'],
                'isClient': entity2['isClient']
            }]

            obj1.network.set_outgoing_routes(outgoing_routes2)
            self.log.info("Setting done...")

        except Exception as excp:
            self.log.exception("Exception raised with error {0}".format(excp))

    def push_config_client(self, clients):
        """Performs a push network configuration on the list of clients

            Args:
                clients : list of client names

                Example:
                    ["auto", "v11-restapi"]

        """

        self.log.info(
            "*" *
            10 +
            "Performing push network configuration on the list of clients" +
            "*" *
            10)

        for client in clients:
            self.log.info(
                "Performing push network configuration on Client {0}".format(client))

            _client_obj = self.commcell.clients.get(client)

            _client_obj.push_network_config()

    def push_config_clientgroup(self, clientgroups):
        """Performs a push network configuration on the list of client groups

        Args:
                clients : list of client names

                Example:
                    ["Testgp"]

        """

        self.log.info(
            "*" *
            10 +
            "Performing push network configuration on the list of client groups" +
            "*" *
            10)

        for clientgroup in clientgroups:
            self.log.info(
                "Performing push network configuration on Client Group {0}".format(clientgroup))

            _clientgroup_obj = self.commcell.client_groups.get(clientgroup)

            _clientgroup_obj.push_network_config()

    def set_via_gateway(self, entity1, entity2, gateway_info):
        """Sets the route via gateway

            Args:
                entity1(dict)  -- dict of entity name
                                This should be entity on which gateway route has to be defined.
                {'clientName':val} or {'clientGroupName':val}


                entity2(dict)  -- dict of client name and number of streams.
                                  Entity value can be a client name only.
                                  This is the remote entity for which gateway will be set.
                {'clientName':val,'streams':val}

                gateway_info(dict) -- dict of gateway port and gateway host
                {'gatewayPort':val,'gatewayHost':val}

            Example:
                entity1:
                {
                'clientName': 'Test'
                }

                entity2:
                {
                'clientName': 'centOS',
                'streams' : 2
                }

                entity3:
                {
                'gatewayPort': 443,
                'gatewayHost' : '1.2.3.4'
                }


        Raises:
                Exception:
                    if the required key is missing in the input value passed

        """

        try:
            obj = self._get_entity_object(entity1)
            self.log.info("Setting Gateway route on {0} {1}".
                          format(obj[1], list(entity1.values())[0]))
            outgoing_routes = [{
                'routeType': 'VIA_GATEWAY',
                'remoteEntity': entity2['clientName'],
                'streams': entity2['streams'],
                'gatewayPort': gateway_info['gatewayPort'],
                'gatewayHost': gateway_info['gatewayHost'],
                'isClient': True
            }]

            obj[0].network.set_outgoing_routes(outgoing_routes)

        except Exception as excp:
            self.log.exception("Exception raised with error {0}".format(excp))

    def enable_proxy(self, entity):
        """Marks a client or a client group as proxy

            Args:
                entity(dict)  -- dict of entity name

                {'clientName':val} or {'clientGroupName':val}

        """

        obj = self._get_entity_object(entity)
        self.log.info("Enabling proxy on {0} {1}".format(obj[1],
                                                         list(entity.values())[0]))
        obj[0].network.proxy = True

    def enable_roaming_client(self, entities):
        """Marks a client or a client group as roaming client

            Args:
                entity(dict)  -- list of dict of entity name

                Example:
                [{'clientName':val}, {'clientGroupName':val}]

        """
        for entity in entities:
            obj = self._get_entity_object(entity)

            self.log.info("Enabling roaming client on"
                          " {0} {1}".format(obj[1], list(entity.values())[0]))

            obj[0].network.roaming_client = True

    def set_tunnelport(self, entities, tunnelports):
        """Sets the specified port as the tunnel port on the given client/ client group

            Args:
                entities(dict)  -- list of dict of entity name
                [{'clientGroupName':val},{'clientName':val}]

                Note: pass the key name based on entity

                tunnelports   --  list of tunnel ports

                example:
                {
                'clientName': 'shezavm11',
                }
                ['9999','9999']

            Raises:
                Exception:
                    if the required key is missing in the input value passed

        """

        for (entity, tunnelport) in zip(entities, tunnelports):
            try:
                obj = self._get_entity_object(entity)

                self.log.info("Setting tunnel port for "
                              "{0} {1}".format(obj[1], list(entity.values())[0]))

                obj[0].network.tunnel_connection_port = tunnelport

            except Exception as excp:
                self.log.exception("Exception raised with error {0}".format(excp))

    def set_extra_ports(self, entity, is_group, port_pairs):
        """Adds extra ports to the incoming ports of network properties of a client/client group

                    Args:
                        entity(str)  -- Name of the client entity

                        is_group(bool)    -- Is a client group

                        port_pairs(list)  -- list of ports should be a list of dict containing
                                            start port and end port
                                            [{'startPort':val,'endPort':val}]
        """
        network_obj = None
        if is_group:
            client_group_obj = self.commcell.client_groups.get(entity)
            network_obj = client_group_obj.network
        else:
            client_obj = self.commcell.clients.get(entity)
            network_obj = client_obj.network
        network_obj.set_additional_ports(port_pairs)

    def remove_network_config(self, entities):
        """Removes network configuration on a client or client group

            Args:
                entities(dict)  -- list of dict of entity name
                [{'clientGroupName':val}, {'clientName':val}]

                Note: pass the key name based on entity

        """

        for entity in entities:
            obj = self._get_entity_object(entity)

            self.log.info("Removing network configuration on {0} {1}".format(
                obj[1], list(entity.values())[0]))

            obj[0].network.configure_network_settings = False

    def set_gui_tppm(self, entity1, entity2):
        """Sets one-way firewall between two clients and then sets GUI tppm between them

            Args:
                entity1(dict)  -- dict containing CS client name
                {'clientName':val}

                entity2(dict)  -- dict of proxy entity name and it's local port number
                {'proxyEntity':val,'portNumber':val}


            Example:

                entity1:
                {
                'clientName': 'v11-restapi'
                }

                entity2:
                {
                'proxyEntity': 'testproxy'
                'portNumber': 9999
                }


        Raises:
                Exception:
                    if the required key is missing in the input value passed


        """

        try:
            self.log.info("Setting GUI TPPM with proxy {0} and local port on proxy as {1}".
                          format(entity2['proxyEntity'], entity2['portNumber']))
            self.set_one_way({'clientName': entity1['clientName']},
                             {'clientName': entity2['proxyEntity']})

            self.enable_proxy({'clientName': entity2['proxyEntity']})

            obj = self.commcell.clients.get(entity1['clientName'])

            tppm = [{
                'tppmType': 'COMMSERVE',
                'portNumber': entity2['portNumber'],
                'proxyEntity': entity2['proxyEntity']
            }]

            obj.network.set_tppm_settings(tppm)

        except Exception as excp:
            self.log.exception("Exception raised with error {0}".format(excp))

    def set_wswc_tppm(self, entity1, entity2):
        """Sets one-way firewall between two clients and then sets webserver-webconsole
            tppm between them

                    Args:
                        entity1(dict)  -- dict containing webserver client name
                        {'webserver':val}

                        entity2(dict)  -- dict containing webconsole client name and
                                          it's local port number
                        {'webconsole':val,'portNumber':val}


                    Example:

                        entity1:
                        {
                        'webserver': 'v11-restapi'
                        }

                        entity2:
                        {
                        'webconsole': 'testproxy'
                        'portNumber': 9999
                        }


                Raises:
                        Exception:
                            if the required key is missing in the input value passed


                """

        try:
            self.log.info("Setting Webserver-Webconsole TPPM with webconsole {0} "
                          "and local port on webconsole as {1}".
                          format(entity2['webconsole'], entity2['portNumber']))
            self.set_one_way({'clientName': entity1['webserver'], },
                             {'clientName': entity2['webconsole']})

            obj = self.commcell.clients.get(entity1['webserver'])

            tppm = [{
                'tppmType': 'WEB_SERVER_FOR_IIS_SERVER',
                'portNumber': entity2['portNumber'],
                'proxyEntity': entity2['webconsole']
            }]

            obj.network.set_tppm_settings(tppm)

        except Exception as excp:
            self.log.exception("Exception raised with error {0}".format(excp))

    def validate(self, client_names,
                 media_agent, test_data_path=None, test_data_level=1, test_data_size=1000,
                 max_job_time=None):
        """Function to perform backup and restore jobs on a list of clients

                Args:
                        client_names(list)      -- list of client names

                        media_agent(str)        --  media agent to be used

                        test_data_path(str)     -- path to generate test data

                        test_data_level(int)    -- depth of folders under test data

                        test_data_size(int)     -- size of each test file to be generated in KB

                        max_job_time(int)       -- Maximum time the job should take in seconds

        """
        # create disk library
        disklibrary_inputs = {
            'disklibrary': {
                'name': "disklibrary_" + media_agent,
                'mediaagent': media_agent,
                'mount_path': self.entities.get_mount_path(media_agent),
                'username': '',
                'password': '',
                'cleanup_mount_path': True,
                'force': False,
            }
        }
        self.log.info("Creating disk library using media agent {0}".format(media_agent))
        self.entities.create(disklibrary_inputs)
        # create storage policy
        storagepolicy_inputs = {
            'target':
                {
                    'library': "disklibrary_" + media_agent,
                    'mediaagent': media_agent,
                    'force': False
                },
            'storagepolicy':
                {
                    'name': "storagepolicy_" + media_agent,
                    'dedup_path': None,
                    'incremental_sp': None,
                    'retention_period': 3,
                },
        }
        self.log.info("Creating storage policy using library {0}".
                      format("disklibrary_" + media_agent))
        self.entities.create(storagepolicy_inputs)

        for client_name in client_names:
            self.log.info("Creating subclient for client {0}".format(client_name))
            subclient_name = "subclient_" + client_name + self.options.get_custom_str()
            backupset_name = "backupset_" + client_name + self.options.get_custom_str()
            # create subclient
            subclient_inputs = {
                'target':
                    {
                        'client': client_name,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'storagepolicy': "storagepolicy_" + media_agent,
                        'force': True
                    },
                'backupset':
                    {
                        'name': backupset_name,
                        'on_demand_backupset': False,
                        'force': True,
                    },

                'subclient':
                    {
                        'name': subclient_name,
                        'client_name': client_name,
                        'backupset': backupset_name,
                        'data_path': test_data_path,
                        'level': test_data_level,
                        'size': test_data_size,
                        'description': "Automation - Target properties",
                        'subclient_type': None,
                    }
            }
            self.entities.create(subclient_inputs)

            self.log.info("Going to perform backup and restore jobs for client {0}".format(
                client_name))

            client_obj = self.commcell.clients.get(client_name)
            agent_obj = client_obj.agents.get('File System')
            backupset_obj = agent_obj.backupsets.get(backupset_name)
            subclient_obj = backupset_obj.subclients.get(subclient_name)

            self.log.info(
                "Going to trigger backup job on Subclient: {0}".format(subclient_name))

            start = time.time()
            job = self.serverbase.subclient_backup(subclient_obj, "full")
            end = time.time()
            self.log.info("Time taken for backup job: {0}".format(end - start))

            self.serverbase.backup_validation(job.job_id, "Full")

            job_throughput = (self.commcell.job_controller.get(job.job_id).details[
                'jobDetail']['detailInfo']['throughPut'])

            self.log.info("Throughput value: {0}".format(job_throughput))
            self.log.info("Successfully finished subclient full backup and validation")
            self.log.info("*" * 10 + " Run Restore out of place " + "*" * 10)
            # run restore in place job
            self.serverbase.subclient_restore_out_of_place(subclient_obj.content[0]
                                                           + "\\RESTOREDATA",
                                                           subclient_obj.content,
                                                           client_name,
                                                           subclient_obj)

            self.log.info("Successfully completed backup and restore jobs for client"
                          " {0}".format(client_name))

            if max_job_time and (end - start) > max_job_time:
                raise Exception(f"[TLE] Job Time: {end - start} | max job time: {max_job_time}")
            # return job_throughput
    
    def validate_settings_display(self, settings, setting_name, setting_value):
        # Define validators for each setting
        validators = {
            'Tunnel port': lambda x: str(x).isdigit() and 1 <= int(x) <= 65535,
            'Additional open port range': lambda x: bool(re.match(r'^(\d{1,5}\s*-\s*\d{1,5})(,\d{1,5}\s*-\s*\d{1,5})*$', x)) if x else True,
            'Bind all services to open ports only': lambda x: x in ['Yes', 'No'],
            'Keep-alive interval in seconds': lambda x: str(x).isdigit() and int(x) > 0,
            'Force SSL encryption in incoming tunnels': lambda x: x in ['Yes', 'No'],
            'Enable network gateway': lambda x: x in ['Yes', 'No'],
        }

        # Check if the setting to validate exists in the validators
        if setting_name not in validators:
            raise ValueError(f"Unknown setting: {setting_name}")

        # Retrieve the current value of the setting from the settings dictionary
        current_value = settings.get(setting_name)
        if current_value is None:
            raise ValueError(f"Setting '{setting_name}' not found in the provided settings")

        # Apply the validation function for the specific setting to the provided setting value
        is_valid = validators[setting_name](setting_value)
        if not is_valid:
            raise ValueError(f"Invalid value for setting '{setting_name}': {setting_value}")

        # Check if the provided setting value matches the current value
        assert str(setting_value) == str(current_value), f"Setting value mismatch: {setting_value} != {current_value}"
        self.log.info("Display setting is correct: {0} = {1}".format(setting_name, setting_value))

    def validate_with_plan(self, client_names,
                           media_agent, test_data_path=None, test_data_level=1, test_data_size=1000,
                           max_job_time=None):
        """Function to perform backup and restore jobs on a list of clients

                Args:
                        client_names(list)      -- list of client names

                        media_agent(str)        --  media agent to be used

                        test_data_path(str)     -- path to generate test data

                        test_data_level(int)    -- depth of folders under test data

                        test_data_size(int)     -- size of each test file to be generated in KB

                        max_job_time(int)       -- Maximum time the job should take in seconds

        """
        try:
            try:
                storage_pool_name = "storage_pool_" + media_agent + uuid.uuid4().hex[:5]
                plan_name = "plan_" + media_agent + uuid.uuid4().hex[:5]
                mount_path = self.entities.get_mount_path(media_agent)

                # create storage pool
                self.log.info(f"Creating Storage pool with name {storage_pool_name}")
                self.storage_pool.add(storage_pool_name, mount_path, media_agent)

                # create plan
                self.plans_helper = PlansHelper(
                    commserve=self._testcase.inputJSONnode['commcell']["webconsoleHostname"],
                    username=self._testcase.inputJSONnode['commcell']["commcellUsername"],
                    password=self._testcase.inputJSONnode['commcell']["commcellPassword"],
                    commcell_obj=self.commcell
                )
                self.log.info(f"Creating base plan with name {plan_name}")
                self.plans_helper.create_base_plan(plan_name, "Server", storage_pool_name)
                self.log.info(f"{plan_name} created successfully")
            except Exception as e:
                raise Exception("Error is not related to network testcase.\n Error: " + str(e))

            for client_name in client_names:
                self.log.info("Creating subclient for client {0}".format(client_name))
                subclient_name = "subclient_" + client_name + self.options.get_custom_str()
                backupset_name = "backupset_" + client_name + self.options.get_custom_str()
                # create subclient
                self.log.info(f"Creating backupset : {backupset_name} and subclient : {subclient_name}")
                subclient_inputs = {
                    'target':
                        {
                            'client': client_name,
                            'agent': "File system",
                            'instance': "defaultinstancename",
                            'storagepolicy': plan_name,
                            'force': True
                        },
                    'backupset':
                        {
                            'name': backupset_name,
                            'on_demand_backupset': False,
                            'force': True,
                        },

                    'subclient':
                        {
                            'name': subclient_name,
                            'client_name': client_name,
                            'backupset': backupset_name,
                            'data_path': test_data_path,
                            'level': test_data_level,
                            'size': test_data_size,
                            'description': "Automation - Target properties",
                            'subclient_type': None,
                            'force': True,
                        }
                }
                self.entities.create(subclient_inputs)

                self.log.info("Going to perform backup and restore jobs for client {0}".format(
                    client_name))

                client_obj = self.commcell.clients.get(client_name)
                agent_obj = client_obj.agents.get('File System')
                backupset_obj = agent_obj.backupsets.get(backupset_name)
                subclient_obj = backupset_obj.subclients.get(subclient_name)

                self.log.info(
                    "Going to trigger backup job on Subclient: {0}".format(subclient_name))

                try:
                    start = time.time()
                    job = self.serverbase.subclient_backup(subclient_obj, "full")
                    end = time.time()
                    self.log.info("Time taken for backup job: {0}".format(end - start))

                    self.serverbase.backup_validation(job.job_id, "Full")

                    job_throughput = (self.commcell.job_controller.get(job.job_id).details[
                        'jobDetail']['detailInfo']['throughPut'])

                    self.log.info("Throughput value: {0}".format(job_throughput))
                    self.log.info("Successfully finished subclient full backup and validation")
                    self.log.info("*" * 10 + " Run Restore out of place " + "*" * 10)
                    # run restore in place job
                    self.serverbase.subclient_restore_out_of_place(subclient_obj.content[0]
                                                                   + "\\RESTOREDATA",
                                                                   subclient_obj.content,
                                                                   client_name,
                                                                   subclient_obj)

                    self.log.info("Successfully completed backup and restore jobs for client"
                                  " {0}".format(client_name))
                except Exception as e:
                    raise Exception(str(e))
                
                finally:
                    self.log.info("Disassociating plan from subclient ", subclient_name)
                    subclient_obj.plan = None
                    if max_job_time and (end - start) > max_job_time:
                        raise Exception(f"[TLE] Job Time: {end - start} | max job time: {max_job_time}")

                    self.log.info(f"Deleting plan: {plan_name} and storage pool {storage_pool_name}")
                    self.plans_helper.delete_plan(plan_name)
                    self.storage_pool.delete(storage_pool_name)
        except Exception as e:
            self.log.info("[Soft error] : Something failed in clean up part. ")
        # return job_throughput

    def validate_tunnel_port(self, entities, validate_port=None):
        """Validates the default tunnel port on a client or client group

            Args:
                entities(dict)  -- list of dict of entity name
                {'clientGroupName':val}  or {'clientName':val}

                Note: pass the key name based on entity

             Raises:
                Exception:
                    if the required key is missing in the input value passed

        """

        for entity in entities:

            try:
                obj = self._get_entity_object(entity)

                self.log.info("Getting default tunnel port set on {0} {1} ".format(
                    obj[1], entity.values()))

                tunnel_port = obj[0].network.tunnel_connection_port

                self.log.info("Tunnel port is: {0}".format(tunnel_port))
                if validate_port:
                    network_summary = obj[0].get_network_summary()
                    setting_line = 'tunnel_ports=' + str(validate_port)
                    assert setting_line in network_summary, f"Failed to validate tunnel port {validate_port}"
                    self.log.info("Validated the tunnel port as {0}".format(validate_port))

                elif tunnel_port == networkconstants.TUNNEL_CONNECTION_PORT[0] or tunnel_port == \
                        networkconstants.TUNNEL_CONNECTION_PORT[1]:
                    self.log.info("Validated default tunnel port")
                else:
                    raise Exception(
                        "Failed to validate default tunnel port"
                    )

            except Exception as excp:
                self.log.exception("Exception raised with error {0}".format(excp))

    def validate_keep_alive(self, entities, validate_keep_alive=None):
        """Validates the default keep alive interval on a client or client group

                    Args:
                        entities(dict)  -- list of dict of entity name
                        {'clientGroupName':val}  or {'clientName':val}

                        Note: pass the key name based on entity

                     Raises:
                        Exception:
                            if the required key is missing in the input value passed
                """

        for entity in entities:

            try:
                obj = self._get_entity_object(entity)

                self.log.info("Getting default keep alive interval set on {0} {1}".format(
                    obj[1], list(entity.values())[0]))

                keep_alive = obj[0].network.keep_alive_seconds

                self.log.info("Keep alive interval is: {0}".format(keep_alive))

                if validate_keep_alive:
                    networt_summary = obj[0].get_network_summary()
                    setting_line = 'keepalive_interval=' + str(validate_keep_alive)
                    assert setting_line in networt_summary, f"Failed to validate keep alive interval {validate_keep_alive}"
                    self.log.info("Validated the keep alive as {0}".format(validate_keep_alive))

                elif keep_alive == networkconstants.KEEP_ALIVE_SECONDS:
                    self.log.info("Validated default keep alive interval")

                else:
                    raise Exception(
                        "Failed to validate default keep alive interval"
                    )

            except Exception as excp:
                self.log.exception("Exception raised with error {0}".format(excp))
                raise Exception(excp)

    def validate_tunnel_init(self, entities):
        """Validates the default tunnel init interval on a client or client group

                    Args:
                        entities(dict)  -- list of dict of entity name
                        {'clientGroupName':val}  or {'clientName':val}

                        Note: pass the key name based on entity

                     Raises:
                        Exception:
                            if the required key is missing in the input value passed

                """

        for entity in entities:

            try:
                obj = self._get_entity_object(entity)

                self.log.info("Getting default tunnel init interval set on"
                              " {0} {1}".format(obj[1], list(entity.values())[0]))

                tunnel_init = obj[0].network.tunnel_init_seconds

                self.log.info(
                    "Tunnel init interval is: {0}".format(tunnel_init))

                if tunnel_init == networkconstants.TUNNEL_INIT_SECONDS:
                    self.log.info("Validated default tunnel init interval")

                else:
                    raise Exception(
                        "Failed to validate default tunnel init interval"
                    )

            except Exception as excp:
                self.log.exception("Exception raised with error {0}".format(excp))
    
    def validate_other_settings(self, client_name, setting_name, setting_value):
        """Validates the value for force ssl, proxy, bind open ports on a client
            Args:
                client_name(str)  -- client name

                setting_name(str)  -- setting name

                setting_value(str) -- setting value
        """
        client = self.commcell.clients.get(client_name)
        network_summary = client.get_network_summary()
        self.log.info(network_summary)
        setting_line = setting_name + '=' + setting_value
        assert setting_line in network_summary, f"Failed to validate {setting_name} as {setting_value}"
        self.log.info(f"Validated {setting_name} as {setting_value}")

    def validate_other_defaults(self, entities):
        """Validates the default values for force ssl, proxy, bind open ports and roaming client
                    on a client or client group

                    Args:
                        entities(dict)  -- list of dict of entity name
                        {'clientGroupName':val}  or {'clientName':val}

                        Note: pass the key name based on entity

                     Raises:
                        Exception:
                            if the required key is missing in the input value passed

                """

        for entity in entities:

            try:
                obj = self._get_entity_object(entity)

                self.log.info("*" * 5 + "Validating default values for force_ssl, is_dmz, "
                                        "bind_open_ports and is_roaming set on"
                                        " {0} {1}".format(obj[1], list(entity.values())[0]) + 5 * "*")

                options_values = [networkconstants.FORCE_SSL,
                                  networkconstants.IS_DMZ,
                                  networkconstants.BIND_OPEN_PORTS_ONLY,
                                  networkconstants.IS_ROAMING_CLIENT]

                options_functions = [obj[0].network.force_ssl,
                                     obj[0].network.proxy,
                                     obj[0].network.bind_open_ports,
                                     obj[0].network.roaming_client]

                for (option_value, option_function) in zip(
                        options_values, options_functions):

                    option_val = option_function

                    if option_val == option_value:
                        self.log.info("Validated default value")

                    else:
                        raise Exception(
                            "Failed to validate default value"
                        )

            except Exception as excp:
                self.log.exception("Exception raised with error {0}".format(excp))

    def outgoing_route_settings(self, entity, **kwargs):
        """Sets tunnel connection protocol for outgoing routes on a client/client group

                Args:

                    entity                (dict)  -- dict of entity name
                                                    {'clientGroupName':val}  or {'clientName':val}

                    **kwargs              (dict)  -- Key value pairs for supported arguments


                    Supported arguments for **kwargs:

                    route_type            (str)   -- type of route that needs to be set

                    remote_entity         (str)   -- client/client group towards which
                                                     outgoing route is set

                    streams               (int)   -- total number of tunnels

                    is_client             (bool)  -- specify if remote entity is a client or
                                                     client group

                    force_all_data_traffic(bool)  -- set to true to force all data traffic
                                                     into tunnel

                    connection_protocol   (int)   -- type of tunnel connection protocol that
                                                     needs to be set

                    gateway_port          (int)   -- gateway port number if outgoing route is
                                                     via gateway

                    gateway_host          (str)   -- gateway ip if outgoing route is via gateway

                    remote_proxy          (str)   -- proxy entity if outgoing route is via proxy

                Valid values for route_type:
                'DIRECT'
                'VIA_GATEWAY'
                'VIA_PROXY'

                Valid values for connection_protocol:
                0: 'HTTP',
                1: 'HTTPS',
                2: 'HTTPS_AuthOnly',
                3: 'RAW_PROTOCOL'

        """

        obj = self._get_entity_object(entity)

        route_dict = {
            'routeType': kwargs.get('route_type', 'DIRECT'),
            'remoteEntity': kwargs['remote_entity'],
            'streams': kwargs.get('streams', 1),
            'gatewayPort': kwargs.get('gateway_port', 0),
            'gatewayHost': kwargs.get('gateway_host', ""),
            'isClient': kwargs['is_client'],
            'forceAllDataTraffic': kwargs.get('force_all_data_traffic', False),
            'connectionProtocol': kwargs.get('connection_protocol', 2),
            'remoteProxy': kwargs.get('remote_proxy', {})
        }

        self.log.info("Setting outgoing routes on {0} {1}".format(obj[1], entity))
        self.log.info("Tunnel connection protocol being set is: {0}".format(
            networkconstants.OUTGOING_CONNECTION_PROTOCOL[kwargs['connection_protocol']]))
        obj[0].network.set_outgoing_routes([route_dict])

    def get_network_summary(self, client_list):
        """ Gets the network summary for each client in the client list

        Args:
            client_list    (list)          --   List of client names(str)

        Returns:
            network_summary_dict(dict)      -   key = client_name
                                                value = network_summary

        Raises:
            Exception:
                client_list is empty
            Exception:
                Improper input. Check input

        """
        if len(client_list) == 0:
            raise Exception("Input is empty")

        for client_obj in client_list:
            if not isinstance(client_obj, str):
                raise Exception("Improper input. Check input")

        network_summary_dict = {}
        for client_name in client_list:
            client = self.commcell.clients.get(client_name)
            network_summary_dict[client_name] = client.get_network_summary()

        return network_summary_dict

    def _get_entity_object(self, entity):
        """Returns object for client or client group

            Raises:
                Exception:
                    if the required key is missing in the input value passed

        """

        try:
            if 'clientName' in entity:
                return self.commcell.clients.get(entity['clientName']), 'client'

            return self.commcell.client_groups.get(entity['clientGroupName']), 'client group'

        except Exception as excp:
            self.log.exception("Exception raised with error {0}".format(excp))

    def do_cvping(self, source, destination, port, family="", validate=False):
        """Does a cvping on the specified port on destination client from source client

                Args:
                    source      (str)       -- client name from where cvping will be executed

                    destination (str)       -- destination client

                    port        (int)       -- destination port

                    family      (str)       -- specifies type of family --- ipv4/ipv6/any
                                            Valid values are:  'UseIPv4', 'UseIPv6' or 'UseIPAny'

                    validate    (bool)      -- specified as true if cvping tool needs to be
                                                validated

                Raises:
                        Exception:
                            if cvping connection fails

        """

        if family:
            family = ('-{0}').format(family)

        source_obj = self.commcell.clients.get(source)
        destination_obj = self.commcell.clients.get(destination)
        machine_obj = Machine(source_obj)

        cvping_cmds = {
            'WINDOWS': r'cmd.exe /c "{0}\CVPing.exe" {1} {2} -port {3}',
            'UNIX': 'cd {0} && ./cvping {1} {2} {3}'
        }

        install_dir = machine_obj.join_path(source_obj.install_directory, 'Base')

        cvping_cmd = cvping_cmds.get(machine_obj.os_info).format(install_dir,
                                                                 destination_obj.client_hostname,
                                                                 family,
                                                                 port)

        self.log.info("Executing command: {0}".format(cvping_cmd))

        res1 = machine_obj.execute_command(cvping_cmd)

        if (re.search(r'\bConnection successful\b', res1.output) or
                re.search(r'\bSuccessfully connected\b', res1.output)):
            self.log.info("Connection successful with output: {0}".format(res1.output))
            return

        elif validate is True and not re.search(r'Trying to connect', str(res1.output)):
            raise Exception("CVPing tool execution failed")

        elif validate is False:
            raise Exception("Connection failed with error: {0} {1}".
                            format(res1.output, res1.exception_message))

        else:
            self.log.info("Output Received: {0}".format(res1.output))

    def s_bind_to_interface(self, client_name, interface):
        """Sets registry key sBindToInterface on the client and validates if client is using
            the specified interface

            Args:
                    client_name     (str) -- client name on which registry key needs to be set

                    interface       (str) -- client IP address to be used

                                                Example: "172.19.96.79"

                Raises:
                        Exception:
                            if services are not bind to specified interface

        """

        self.network_config['s_bind_to_interface']['client'] = client_name

        cl_obj = self.commcell.clients.get(client_name)

        cvd_port = cl_obj.cvd_port

        cmd_list = {
            'WINDOWS': 'netstat -ano | findstr {0} | findstr "LISTENING"',
            'UNIX': 'netstat -ano | grep {0} | grep "LISTEN"'
        }

        self.serverbase.check_client_readiness([client_name])

        cl_obj.add_additional_setting("~", "sBindToInterface", "STRING", interface)

        self.options.sleep_time(60)

        self.serverbase.restart_services([client_name])

        self.options.sleep_time(60)

        machine_obj = Machine(cl_obj)

        cmd = cmd_list.get(machine_obj.os_info).format(cvd_port)

        res = machine_obj.execute_command(cmd)

        output_list = {
            'WINDOWS': "  TCP    {0}:{1}     0.0.0.0:0              LISTENING",
            'UNIX': "tcp        0      0 {0}:{1}       0.0.0.0:*               LISTEN"
        }

        output_str = str(output_list.get(machine_obj.os_info).format(interface, cvd_port))

        if output_str.replace(" ", "") in str(res.output).replace(" ", ""):
            self.log.info("Services bind to IP address {0}".format(interface))

        else:
            raise Exception("Services not bound to specified IP {0} {1}".
                            format(res.output, res.exception_message))

    def _remove_s_bind_to_interface(self, client_name):
        """removes sBindToInterface key on the client and restarts services

                Args:
                    client_name (str)   -- client name on which registry key needs to be removed

        """

        if client_name:
            cl_obj = self.commcell.clients.get(client_name)

            cl_obj.delete_additional_setting("~", "sBindToInterface")

            self.options.sleep_time(30)

            self.serverbase.restart_services([client_name])

    def cv_ip_info(self, source, destination=None, family="IPv4"):
        """Does a host name lookup for specified destination host from source

            Args:
                    source      (str)      -- client name from where cvipinfo will be executed

                    destination (str)      -- destination client. If not provided, LocalHost is used

                    family      (str)      -- specifies if it will be ipv4 or ipv6

                Raises:
                        Exception:
                            if cvipinfo  execution fails

        """

        host = ""
        if destination is not None:
            destination_obj = self.commcell.clients.get(destination)
            host = destination_obj.client_hostname

        source_obj = self.commcell.clients.get(source)

        machine_obj = Machine(source_obj)

        cvipinfo_cmds = {
            'WINDOWS': r'cmd.exe /c "{0}\CVIPInfo.exe" {1} {2}',
            'UNIX': 'cd {0} && ./CVIPInfo {1} {2}'
        }

        install_dir = machine_obj.join_path(source_obj.install_directory, 'Base')

        cvipinfo_cmd = cvipinfo_cmds.get(machine_obj.os_info).format(install_dir,
                                                                     family,
                                                                     host)

        self.log.info("Executing Command {0}".format(cvipinfo_cmd))

        res1 = machine_obj.execute_command(cvipinfo_cmd)

        if re.search(r'Testing Addresses:', str(res1.output)):
            self.log.info("Successfully executed CVIPinfo: {0}".format(res1.output))
            return res1.output

        else:
            raise Exception("Failed to execute CVIPInfo: {0} {1}".
                            format(res1.output, res1.exception_message))

    def client_tunnel_port(self, client):
        """Returns tunnel port of the client

                Args:
                    client      (str)      -- client name for which tunnel port needs
                                              to be determined

        """
        client_obj = self.commcell.clients.get(client)
        tunnel_port = client_obj.network.tunnel_connection_port
        self.log.info("Tunnel port for client {0} is {1}".format(client, tunnel_port))
        return tunnel_port

    def cleanup_network(self):
        """Does all the clean up for any test case

        """
        self.log.info("*" * 10 + "Starting network clean-up phase" + "*" * 10)

        self.disable_firewall(
            self.network_config.get('disable_firewall').get('clients', []),
            self.network_config.get('disable_firewall').get('ports', []))

        self.remove_machine(self.network_config.get('delete_machine').get('clients', []))

        self.remove_network_config(self.network_config.get(
            'remove_network_config').get('entities', []))

        self._remove_s_bind_to_interface(self.network_config.get('s_bind_to_interface').
                                         get('client'))

        self.push_config_client(self.network_config.get('delete_machine').get('clients', []))

        self.log.info("Network clean-up phase completed")

        self.network_config = {
            "disable_firewall": {
                "clients": [],
                "ports": []
            },
            "delete_machine": {
                "clients": []
            },
            "remove_network_config": {
                "entities": []
            },
            "s_bind_to_interface": {
                "client": ""
            }
        }

    def is_mnemonic_client_grp(self, client_grp_list):
        """Checks if the client is a mnemonic grp or not

                Args:
                    client_grp_list     (list)    -- list of client names

                Returns:
                    is_mnemonic_dict    (dict)    -- key - client_name
                                                     value(bool) - is mnemonic or not
        """
        mnemonic_grp_set = {'My CommServe Computer and MediaAgents', 'My CommServe Computer',
                            'My MediaAgents'}

        is_mnemonic_dict = {}
        for client_grp in client_grp_list:
            is_mnemonic_dict[client_grp] = False
            if client_grp in mnemonic_grp_set:
                is_mnemonic_dict[client_grp] = True

        return is_mnemonic_dict

    def one_way_topology(self, client_group1, client_group2, topology_name, display_type=0, encrypt_traffic=0,
                         number_of_streams=1, connection_protocol=2):
        """Creates one-way network topology

                Args:
                    client_group1      (str)      -- client group name for topology creation

                    client_group2      (str)      -- client group name for topology creation

                    topology_name      (str)      -- name of topology that will be created

                    display_type       (int)      -- display type 1 for laptops, 0 for servers

                    encrypt_traffic    (int)      -- Encrypt the traffic

                    number_of_streams  (int)      -- Set number of streams

                    connection_protocol (int)     -- Set connection protocol to httpsa

                    display_type:
                        0 --- servers
                        1 --- laptops

        """

        if self.topologies.has_network_topology(topology_name):
            self.topologies.delete(topology_name)

        is_mnemonic_dict = self.is_mnemonic_client_grp([client_group1, client_group2])
        is_smart_topology = any(is_mnemonic_dict.values())

        self.log.info("Creating one-way topology between client groups {0} and {1}".
                      format(client_group1, client_group2))

        self.topologies.add(topology_name,
                            [{'group_type': 2, 'group_name': client_group1,
                              'is_mnemonic': is_mnemonic_dict[client_group1]},
                             {'group_type': 1, 'group_name': client_group2,
                              'is_mnemonic': is_mnemonic_dict[client_group2]}],
                            topology_description="This is a test for validating "
                                                 "one way network topology",
                            topology_type=2,
                            display_type=display_type,
                            is_smart_topology=is_smart_topology,
                            encrypt_traffic=encrypt_traffic,
                            number_of_streams=number_of_streams,
                            connection_protocol=connection_protocol)

        self.log.info("Created one-way topology")

    def two_way_topology(self, client_group1, client_group2, topology_name, display_type=0, encrypt_traffic=0,
                         number_of_streams=1, connection_protocol=2):
        """Creates two-way network topology

                Args:
                    client_group1      (str)      -- client group name for topology creation

                    client_group2      (str)      -- client group name for topology creation

                    topology_name      (str)      -- name of topology that will be created

                    display_type       (int)      -- display type 1 for laptops, 0 for servers

                    encrypt_traffic    (int)      -- Encrypt the traffic

                    number_of_streams  (int)      -- Set number of streams

                    connection_protocol (int)     -- Set connection protocol to httpsa

                    display_type:
                        0 --- servers
                        1 --- laptops

        """

        if self.topologies.has_network_topology(topology_name):
            self.topologies.delete(topology_name)

        is_mnemonic_dict = self.is_mnemonic_client_grp([client_group1, client_group2])
        is_smart_topology = any(is_mnemonic_dict.values())

        self.log.info("Creating two-way topology between client groups {0} and {1}".
                      format(client_group1, client_group2))

        self.topologies.add(topology_name,
                            [{'group_type': 2, 'group_name': client_group1,
                              'is_mnemonic': is_mnemonic_dict[client_group1]},
                             {'group_type': 1, 'group_name': client_group2,
                              'is_mnemonic': is_mnemonic_dict[client_group2]}],
                            topology_description="This is a test for validating "
                                                 "two way network topology",
                            topology_type=3,
                            is_smart_topology=is_smart_topology,
                            display_type=display_type,
                            encrypt_traffic=encrypt_traffic,
                            number_of_streams=number_of_streams,
                            connection_protocol=connection_protocol)

        self.log.info("Created two-way topology")

    def proxy_topology(self, client_group1, client_group2, client_group3, topology_name,
                       wildcard=False, display_type=0, encrypt_traffic=0, number_of_streams=1, connection_protocol=2):
        """Creates proxy network topology

                Args:
                    client_group1      (str)      -- client group name for topology creation

                    client_group2      (str)      -- client group name for topology creation

                    client_group3      (str)      -- client group name for topology creation

                    topology_name      (str)      -- name of topology that will be created

                    wildcard           (boolean)  -- specify wildcard option

                    display_type       (int)      -- display type 1 for laptops, 0 for servers

                    encrypt_traffic    (int)      -- Encrypt the traffic

                    number_of_streams  (int)      -- Set number of streams

                    connection_protocol (int)     -- Set connection protocol to httpsa

                    display_type:
                        0 --- servers
                        1 --- laptops

        """

        if self.topologies.has_network_topology(topology_name):
            self.topologies.delete(topology_name)

        is_mnemonic_dict = self.is_mnemonic_client_grp([client_group1, client_group2, client_group3])
        is_smart_topology = any(is_mnemonic_dict.values())

        self.log.info("Creating proxy topology between client groups {0}, {1} and {2}".
                      format(client_group1, client_group2, client_group3))

        self.topologies.add(topology_name,
                            [{'group_type': 2, 'group_name': client_group1,
                              'is_mnemonic': is_mnemonic_dict[client_group1]},
                             {'group_type': 1, 'group_name': client_group2,
                              'is_mnemonic': is_mnemonic_dict[client_group2]},
                             {'group_type': 3, 'group_name': client_group3,
                              'is_mnemonic': is_mnemonic_dict[client_group3]}],
                            topology_description="This is a test for validating "
                                                 "proxy network topology",
                            topology_type=1, use_wildcard=wildcard,
                            is_smart_topology=is_smart_topology,
                            display_type=display_type,
                            encrypt_traffic=encrypt_traffic,
                            number_of_streams=number_of_streams,
                            connection_protocol=connection_protocol)

        self.log.info("Created Proxy topology")

    def cascading_gateways_topology(self, client_group1, client_group2, client_group3,
                                    client_group4, topology_name, display_type=0,
                                    encrypt_traffic=0, number_of_streams=1, connection_protocol=2):
        """Creates cascading gateways network topology

                Args:
                    client_group1      (str)      -- client group name for topology creation
                    (Trusted Client Group1)
                    client_group2      (str)      -- client group name for topology creation
                    (Trusted Client Group2)
                    client_group3      (str)      -- client group name for topology creation
                    (DMZ Group near Trusted Client Group1)
                    client_group4      (str)      -- client group name for topology creation
                    (DMZ Group near Trusted Client Group2)
                    topology_name      (str)      -- name of topology that will be created

                    encrypt_traffic    (int)      -- Encrypt the traffic

                    number_of_streams  (int)      -- Set number of streams

                    connection_protocol (int)     -- Set connection protocol to httpsa

                    display_type:
                        0 --- servers
                        1 --- laptops


        """
        if self.topologies.has_network_topology(topology_name):
            self.topologies.delete(topology_name)

        is_mnemonic_dict = self.is_mnemonic_client_grp([client_group1, client_group2, client_group3, client_group4])
        is_smart_topology = any(is_mnemonic_dict.values())

        self.log.info("Creating cascading gateways topology between "
                      "client groups {0}, {1}, {2} and {3}".
                      format(client_group1, client_group2, client_group3, client_group4))

        self.topologies.add(topology_name,
                            [{'group_type': 2, 'group_name': client_group1,
                              'is_mnemonic': is_mnemonic_dict[client_group1]},
                             {'group_type': 1, 'group_name': client_group2,
                              'is_mnemonic': is_mnemonic_dict[client_group2]},
                             {'group_type': 3, 'group_name': client_group3,
                              'is_mnemonic': is_mnemonic_dict[client_group3]},
                             {'group_type': 4, 'group_name': client_group4,
                              'is_mnemonic': is_mnemonic_dict[client_group4]}],
                            topology_description="This is a test for validating cascading "
                                                 "gateway network topology.",
                            topology_type=4,
                            display_type=display_type,
                            encrypt_traffic=encrypt_traffic,
                            number_of_streams=number_of_streams,
                            connection_protocol=connection_protocol)

        self.log.info("Created cascading gateways")

    def validate_one_way_topology(self, topology_name):
        """Validates if topology created is one-way

                Args:

                    topology_name      (str)      -- name of the topology created

        """

        self.log.info("Validating topology name")
        if self.topologies.has_network_topology(topology_name):
            self.log.info("Network Topology {0} was created successfully".format(topology_name))

        else:
            raise Exception("Topology creation for {0} failed".format(topology_name))

        topology_obj = self.topologies.get(topology_name)

        self.log.info("Validating topology type")

        if topology_obj.network_topology_type == 2:
            self.log.info("Validated Created topology type is one-way")

        else:
            raise Exception("Created topology type doesn't match with the specified topology")

        self.log.info("Validating topology description")

        if topology_obj.description == "This is a test for validating one way network topology":
            self.log.info("Validated description")

        else:
            raise Exception("Mismatch in description")

    def validate_two_way_topology(self, topology_name):
        """Validates if topology created is two-way

                 Args:

                    topology_name      (str)      -- name of the topology created

        """

        if self.topologies.has_network_topology(topology_name):
            self.log.info("Network Topology {0} was created successfully".format(topology_name))

        else:
            raise Exception("Topology creation for {0} failed".format(topology_name))

        topology_obj = self.topologies.get(topology_name)

        if topology_obj.network_topology_type == 3:
            self.log.info("Validated Created topology type is two-way")

        else:
            raise Exception("Created topology type doesn't match with the specified topology")

        if topology_obj.description == "This is a test for validating two way network topology":
            self.log.info("Validated description")

        else:
            raise Exception("Mismatch in description")

    def validate_proxy_topology(self, topology_name):
        """validates if topology created is proxy topology

                Args:

                    topology_name      (str)      -- name of the topology created

        """

        if self.topologies.has_network_topology(topology_name):
            self.log.info("Network Topology {0} was created successfully".format(topology_name))

        else:
            raise Exception("Topology creation for {0} failed".format(topology_name))

        topology_obj = self.topologies.get(topology_name)

        if topology_obj.network_topology_type == 1:
            self.log.info("Validated Created topology type is proxy")

        else:
            raise Exception("Created topology type doesn't match with the specified topology")

        if topology_obj.description == "This is a test for validating proxy network topology":
            self.log.info("Validated description")

        else:
            raise Exception("Mismatch in description")

    def validate_cascading_gateways_topology(self, topology_name):
        """validates if topology created is cascading_gateways_topology

                Args:

                    topology_name      (str)      -- name of the topology created

        """

        if self.topologies.has_network_topology(topology_name):
            self.log.info("Network Topology {0} was created successfully".format(topology_name))

        else:
            raise Exception("Topology creation for {0} failed".format(topology_name))

        topology_obj = self.topologies.get(topology_name)

        if topology_obj.network_topology_type == 4:
            self.log.info("Validated Created topology type is cascading gateways topology")

        else:
            raise Exception("Created topology type doesn't match with the specified topology")

        if topology_obj.description == ("This is a test for validating cascading gateway "
                                        "network topology."):
            self.log.info("Validated description")

        else:
            raise Exception("Mismatch in description")

    def validate_fwconfig_file(self, topology_type, client1, client2, client3=None, wildcard=0):
        """Validates FwConfig.txt files pushed on the clients

                Args:

                    topology_type      (int)      -- type of topology

                    client1            (str)      -- client added to the group

                    client2            (str)      -- client added to the group

                    client3            (str)      -- client added to the group

                    wildcard           (int)      -- specify if wildcard is selected


        """

        client1_obj = self.commcell.clients.get(client1)
        client2_obj = self.commcell.clients.get(client2)
        machine_obj1 = Machine(client1_obj)
        machine_obj2 = Machine(client2_obj)

        client1_base_path = machine_obj1.join_path(client1_obj.install_directory, 'Base')
        client2_base_path = machine_obj2.join_path(client2_obj.install_directory, 'Base')

        client1_guid = self.commcell.clients.get(client1).client_guid
        client2_guid = self.commcell.clients.get(client2).client_guid
        if client3:
            client3_obj = self.commcell.clients.get(client3)
            machine_obj3 = Machine(client3_obj)
            client3_base_path = machine_obj3.join_path(client3_obj.install_directory, 'Base')
            client3_guid = self.commcell.clients.get(client3).client_guid

        route2 = ""
        file = None
        success = False
        found = None
        self.log.info("Validating routes on client2 {0}".format(client2))
        route = client2 + " " + client1
        if topology_type in (2, 1):
            route2 = " remote_guid=" + client1_guid + " type=passive"

        elif topology_type == 3:
            route2 = (" remote_guid=" + client1_guid + " type=ondemand proto=httpsa cvfwd=" +
                      client1_obj.client_hostname + ":")

        elif topology_type == 0:
            route2 = (" remote_guid=" + client1_guid + " type=throttling proto=http cvfwd=" +
                      client1_obj.client_hostname + ":0 cvd_port=")

        file_path = machine_obj2.join_path(client2_base_path, "FwConfig.txt")

        self.log.info("The file path is {0}".format(file_path))

        file = machine_obj2.read_file(file_path)

        self.log.info("Contents of FwConfig.txt file on client {0} are:\n {1}".
                      format(client2, file))

        file_list = file.split("\n")

        success = self.find_route(file_list, route, route2)

        if success is True:

            self.log.info("Validating routes on client1 {0}".format(client1))

            route = client1 + " " + client2
            if topology_type in (2, 1):
                route2 = (" remote_guid=" + client2_guid + " type=persistent proto=httpsa cvfwd="
                          + client2_obj.client_hostname + ":")

            elif topology_type == 3:
                route2 = (" remote_guid=" + client2_guid + " type=ondemand proto=httpsa cvfwd="
                          + client2_obj.client_hostname + ":")

            elif topology_type == 0:
                route2 = (" remote_guid=" + client2_guid + " type=throttling proto=http cvfwd=" +
                          client2_obj.client_hostname + ":0 cvd_port=")

            file_path = machine_obj1.join_path(client1_base_path, "FwConfig.txt")

            self.log.info("The file path is {0}".format(file_path))

            file = machine_obj1.read_file(file_path)

            self.log.info("Contents of FwConfig.txt file on client {0} are:\n {1}".
                          format(client1, file))

            file_list = file.split("\n")

            success = self.find_route(file_list, route, route2)

            if success is True and topology_type == 1 and wildcard == 0 and client3:
                self.log.info("Validating proxy route on client1 {0}".format(client1))
                route = (client1 + " " + client3 + " proxy=" + client2 +
                         " remote_guid=" + client3_guid)

                success = self.find_proxy_route(file_list, route)

                if success is False:
                    self.log.error("Validation of proxy route Failed on client {0}" % (client1))

            if success is True and wildcard == 1 and topology_type == 1:
                route = client1 + " *" + " proxy=" + client2

                success = self.find_proxy_route(file_list, route)

                if success is False:
                    self.log.error("Validation of proxy route Failed on client {0}" % (client1))

        if success is not True:
            raise Exception("Validation of FwConfig.txt files Failed for "
                            "clients {0} {1}".format(client1, client2))

        self.log.info("Validation of FwConfig.txt files completed successfully "
                      "for clients {0} and {1}".format(client1, client2))

    def find_route(self, file_list, route, route2):
        """Searches for a route pattern in FwConfig.txt file in client's  base folder

                Args:

                    file_list     (list)     -- file contents in form of list

                    route         (str)      -- route1 that needs to be searched

                    route2        (str)      -- route2 that needs to be searched

        """
        for line in file_list:
            found = (line).find(route)
            if found > -1:
                self.log.info("Route found in file is : [{0}]".format(line))
                if route2.lower() in line.lower():
                    self.log.info("Validation of route succeeded.")
                    return True
        return False

    def find_proxy_route(self, file_list, route):
        """Searches for a route pattern in FwConfig.txt file in client's  base folder

                Args:

                    file_list     (list)     -- file contents in form of list

                    route         (str)      -- route1 that needs to be searched

        """
        found = None
        for line in file_list:
            found = (line.lower()).find(route.lower())
            if found > -1:
                self.log.info("Route found in file is : [{0}]".format(line))
                self.log.info("Validation of route [{0}] succeeded "
                              "on Client".format(route))
                return True
        if found <= -1:
            return False

    def delete_topology(self, topology_name):
        """Deletes the specified network topology

                Args:

                    topology_name      (str)      -- name of the topology created

        """

        if self.topologies.has_network_topology(topology_name):
            self.log.info("Deleting topology {0}".format(topology_name))
            self.topologies.delete(topology_name)

    def push_topology(self, topology_name):
        """Performs a push network configuration on the specified topology

            Args:

                    topology_name      (str)      -- name of the topology created

        """

        if self.topologies.has_network_topology(topology_name):
            self.log.info("Going to perform a push network configuration "
                          "on network topology {0}".format(topology_name))
            topology_obj = self.topologies.get(topology_name)
            topology_obj.push_network_config()

    def topology_pre_settings(self, client_list):
        """Does pre-settings on the list of clients for verification purpose

                Args:

                    client_list     (list)      -- list of clients on which setting needs to be done

        """
        for client in client_list:
            client_obj = self.commcell.clients.get(client)
            client_obj.network.configure_network_settings = True
            self.network_config['remove_network_config']['entities'].append({
                'clientName': client})

        self.log.info("Querying DB to get values for isTrivialConfig flag for all the clients")

        self.pre_trivial_list = (self.options.exec_commserv_query('select isTrivialConfig from '
                                                                  'APP_FWTrivialConfig where '
                                                                  'clientId > 0')[0])
        self.log.info("Querying DB to get values for APP_Firewall")

        self.app_firewall_value1 = self.options.exec_commserv_query('select * from APP_Firewall '
                                                                    'where flag=0')

        self.log.info("Querying DB to get values for App_FWOutGoingRoutes")

        self.app_fwoutgoing_routes1 = self.options.exec_commserv_query('select * from '
                                                                       'App_FWOutGoingRoutes '
                                                                       'where flag=0')

        self.log.info(self.pre_trivial_list)

    def topology_post_settings(self):
        """Verifies modification in topology does not affect existing settings on client level

        """
        self.log.info("Querying DB to get values for isTrivialConfig flag for all the clients")

        self.post_trivial_list = (self.options.exec_commserv_query('select isTrivialConfig from '
                                                                   'APP_FWTrivialConfig '
                                                                   'where clientId > 0')[0])

        self.log.info(self.post_trivial_list)

        if str(self.pre_trivial_list) == str(self.post_trivial_list):
            self.log.info("Values are not modified with changes in topology")

        else:
            raise Exception("Original values for client level network settings seems "
                            "to have been modified after configuring topology")

        self.log.info("Querying DB to get values for APP_Firewall")

        self.app_firewall_value2 = self.options.exec_commserv_query('select * from APP_Firewall '
                                                                    'where flag=0')

        self.log.info(self.app_firewall_value2)

        if str(self.app_firewall_value1) == str(self.app_firewall_value2):
            self.log.info("Values are not modified with changes in topology")

        else:
            raise Exception("Original values for app_firewall table seems "
                            "to have been modified after configuring topology")

        self.log.info("Querying DB to get values for App_FWOutGoingRoutes")

        self.app_fwoutgoing_routes2 = self.options.exec_commserv_query('select * from '
                                                                       'App_FWOutGoingRoutes '
                                                                       'where flag=0')
        self.log.info(self.app_fwoutgoing_routes2)

        if str(self.app_fwoutgoing_routes1) == str(self.app_fwoutgoing_routes2):
            self.log.info("Values are not modified with changes in topology")

        else:
            raise Exception("Original values for App_FWOutGoingRoutes table seems "
                            "to have been modified after configuring topology")

    def modify_topology(self, topology_name, firewall_groups=None, **kwargs):
        """Modifies existing network topology properties

                Args:

                    topology_name     (str)      -- name of topology that needs to be modified

                    firewall_groups   (list of dict) -- client group names to modify

                    **kwargs             (dict)  -- Key value pairs for supported arguments

                Supported arguments:

                network_topology_name   (str)       --  new name of the network topology

                description             (str)       --  description for the network topology

                topology_type           (int)       -- network topology type

                wildcard_proxy          (boolean)   -- option to use wildcard proxy for
                                                     proxy type topology

                is_smart_topology       (boolean)   -- specified as true for smart topology

                Possible input values:

                topology_type :
                1 --- for proxy topology
                2 --- for one-way topology
                3 --- for two-way topology

                group_type for client_groups:
                2: first client group in GUI screen
                1: second client group in GUI screen
                3: third client group in GUI screen

                is_mnemonic for client_groups:
                True: if the specified group is a mnemonic
                False: if the specified group is a client group

        """

        self.log.info("Modifying topology")

        topology_obj = self.topologies.get(topology_name)

        topology_obj.update(firewall_groups, **kwargs)

    def get_wildcard_proxy(self, topology_name):
        """Returns the value of wildcard proxy for a topology

                Args:

                    topology_name    (str)    -- network topology name

        """

        return self.topologies.get(topology_name).wildcard_proxy

    def set_network_throttle(self, entity, remote_clients=None, remote_clientgroups=None,
                             throttle_rules=None):
        """Configures network throttling on a client or a client group

                Args:


                    entity                  (dict)      -- client/client group on which
                                                           throttling needs to be set

                    {'clientName':val}  or {'clientGroupName': val}

                    remote_clients          (list)     -- list of clients towards which throttling
                                                          will be set

                    remote_clientgroups     (list)     -- list of client groups towards which
                                                          throttling will be set

                    throttle_rules          (list of dict) --  list of throttle rules

                    Supported keys:
                    "sendRate"
                    "sendEnabled"
                    "receiveEnabled"
                    "recvRate"
                    "days"
                    "isAbsolute"
                    "startTime"
                    "endTime"
                    "sendRatePercent"
                    "recvRatePercent"

        """

        obj = self._get_entity_object(entity)

        self.log.info("Setting network throttling on {0}  {1}".format(obj[1], entity))

        if remote_clients is not None:
            obj[0].network_throttle.remote_clients = remote_clients

        if remote_clientgroups is not None:
            obj[0].network_throttle.remote_client_groups = remote_clientgroups

        obj[0].network_throttle.share_bandwidth = True

        if throttle_rules is not None:
            obj[0].network_throttle.throttle_schedules = throttle_rules

        self.log.info("Network throttling set")

    def validate_throttle_schedules(self, client):
        """Validates throttle schedules on the client

                Args:

                    client     (str)   -- client on which throttle is enabled

        """

        rules_list = ['[throttling]', 'group1_remote_clients=', 'group1_sun_00:00=',
                      'group1_mon_00:00=', 'group1_tue_00:00=', 'group1_wed_00:00=',
                      'group1_thu_00:00=', 'group1_fri_00:00=', 'group1_sat_00:00=']

        client_obj = self.commcell.clients.get(client)
        machine_obj = Machine(client_obj)
        client_base_path = machine_obj.join_path(client_obj.install_directory, 'Base')

        file_path = machine_obj.join_path(client_base_path, "FwConfig.txt")

        self.log.info("The file path is {0}".format(file_path))

        file = machine_obj.read_file(file_path)

        self.log.info("Contents of FwConfig.txt file on client {0} are:\n {1}".
                      format(client, file))

        file_list = file.split("\n")

        for route in rules_list:

            success = self.find_proxy_route(file_list, route)

            if success is not True:
                raise Exception("Validation of FwConfig.txt files Failed for "
                                "client {0} ".format(client))

        self.log.info("Validation of FwConfig.txt files completed successfully "
                      "for client {0}".format(client))

    def remove_network_throttle(self, entities):
        """Removes network throttle on a given client/client group

                Args:
                    entities(dict)  -- list of dict of entity name
                [{'clientGroupName':val}, {'clientName':val}]

                Note: pass the key name based on entity
        """
        for entity in entities:
            obj = self._get_entity_object(entity)
            self.log.info("Removing network throttle on {0} {1}".format(obj[1], entity))
            obj[0].network_throttle.enable_network_throttle = False

    def get_network_topology_id(self, topology_name):
        """Returns the network topology id

        Args:
            topology_name(str)  -- Name of network topology

        Returns:
            Network topology id

        """
        return self.topologies.get(topology_name).network_topology_id

    def run_server(self, server_bat_file_path, command):
        """ Starts the server given with bat file path and command

        Args:
            server_bat_file_path(str):      Path of the bat file to be created
            command(str):                   server command to be run

        """
        commcell_machine_obj = Machine(self.commcell.commserv_name, self.commcell)
        if commcell_machine_obj.os_info == "UNIX":
            # Just execute the command on unix machine
            commcell_machine_obj.execute_command(command)
        else:
            commcell_machine_obj.create_file(server_bat_file_path, command)
            commcell_machine_obj.execute_command('start {}'.format(server_bat_file_path))

    def server_client_connection(self, client_hostname,
                                 server_bat_file_path,
                                 port_number=None,
                                 inter_buffer_delay=None,
                                 buffer_count=None,
                                 buffer_size=None,
                                 firewalled=False,
                                 is_unix_client=False):
        """Initiates server/client connection on CVNetworkTestTool with specified options

        Args:
            client_hostname(str):       Client ip address
            server_bat_file_path(str):  Path of the bat file to be created
            port_number(int):           port number to host on
            inter_buffer_delay(int):    inter buffer delay
            buffer_count(int):          buffer count to be sent between server/client
            buffer_size(int):           size of buffer
            firewalled(bool):           firewall option
            is_unix_client(bool):       if client is unix machine

        Returns:
            Output of command line on client

        """
        commcell_machine_obj = Machine(self.commcell.commserv_name, self.commcell)
        # server bindIP
        server_command = "cvnetworktesttool"
        if commcell_machine_obj.os_info == "UNIX":
            cs_install_directory = self.commcell.clients.get(self.commcell.commserv_name).install_directory
            server_command = commcell_machine_obj.join_path(cs_install_directory, 'Base', 'CvNetworkTestTool')
        if firewalled:
            server_command += ' -server -BindIP 127.0.0.1'
        else:
            server_command += ' -server -bindip ' + commcell_machine_obj.ip_address

        if port_number:
            server_command += ' -srvport ' + str(port_number)

        self.run_server(server_bat_file_path, server_command)

        # target client object
        commcell_machine_obj = Machine(self.commcell.commserv_name, self.commcell)
        target_client_obj = Machine(client_hostname, self.commcell)
        client_command = 'cvnetworktesttool'
        if is_unix_client:
            target_client = self.commcell.clients.get(client_hostname)
            client_command = '{}/Base/CvNetworkTestTool'.format(target_client.install_directory)

        client_command += ' -client -srvhostname {0}'.format(commcell_machine_obj.ip_address)
        if port_number:
            client_command += ' -srvport ' + str(port_number)

        if buffer_size:
            client_command += ' -buffsizeclienttoserver' + str(buffer_size)
            client_command += ' -buffsizeservertoclient' + str(buffer_size)

        if firewalled:
            client_command += ' -srvclientname ' + self.commcell.commserv_name

        if inter_buffer_delay:
            client_command += ' -interbufferdelay ' + str(inter_buffer_delay)

        if buffer_count:
            client_command += ' -buffercount ' + str(buffer_count)
        output = target_client_obj.execute_command(client_command).output
        return output

    def get_dips_client(self, client_name):
        """Gets Data interface pairs for a client

        Returns:

            list - list of interfaces with source and destination

        Raises:
                SDKException:
                    if response is not received

        """
        return self.backup_network_pairs.get_backup_interface_for_client(client_name)

    def add_dips(self, interface_pairs_list):
        """Adds data(backup) interface pairs on clients/client groups

                    Args:
                        interface_pairs_list (list)  --  list of tuples containing dict of source and destination

                        Example:
                        [({'client': 'featuretest', 'srcip': '1.1.1.1'},
                        {'client': 'SP9client', 'destip': '1.1.1.1'}),
                        ({'client': 'featuretest', 'srcip': '1.1.1.1'},
                        {'clientgroup': 'G1', 'destip': 'No Default Interface'}),
                        ({'clientgroup': 'G2', 'srcip': '1.1.1.1/16'},
                        {'clientgroup': 'G3', 'destip': '172.19.0.*'})]

                        Note: 0th index should be source with key 'srcip' and 1st index
                        should be destination with key 'destip'

                              entities should be passed with key client/clientgroup

                    Raises:
                        SDKException:
                            if input is not correct

                            if response is not received

                """
        self.backup_network_pairs.add_backup_interface_pairs(interface_pairs_list)

    def delete_dips(self, interface_pairs_list):
        """Deletes data(backup) interface pairs on clients/client groups

                    Args:
                        interface_pairs_list (list)  --  list of tuples containing dict of source and destination

                        Example:
                        [({'client': 'featuretest', 'srcip': '1.1.1.1'},
                        {'client': 'SP9client', 'destip': '1.1.1.1'}),
                        ({'client': 'featuretest', 'srcip': '1.1.1.1'},
                        {'clientgroup': 'G1', 'destip': 'No Default Interface'}),
                        ({'clientgroup': 'G2', 'srcip': '1.1.1.1/16'},
                        {'clientgroup': 'G3', 'destip': '172.19.0.*'})]

                        Note: 0th index should be source with key 'srcip' and 1st index
                        should be destination with key 'destip'

                              entities should be passed with key client/clientgroup

                    Raises:
                        SDKException:
                            if input is not correct

                            if response is not received

                """
        self.backup_network_pairs.delete_backup_interface_pairs(interface_pairs_list)
