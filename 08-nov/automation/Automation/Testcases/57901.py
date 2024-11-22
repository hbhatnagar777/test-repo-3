# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from AutomationUtils.machine import Machine
import socket
""""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case
    Test Case:
            [Network & Firewall] : Verify the behavior of outgoing network option - "Force all data (along with control) into tunnel" at network topology level.
    Instructions:
            Inputs:
                Source client - Any client
                Destination client - Media Agent
                Source Hostname - Hostname of the source client
                Destination Hostname - Hostname of the destination client
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.clientgroup import ClientGroups
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.idautils import CommonUtils
class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)   -   name of this test case
                applicable_os       (str)   —   applicable os for this test case
                                                            Ex: self.os_list.WINDOWS
                product             (str)   —   applicable product for this test case
                                                                 Ex: self.products_list.FILESYSTEM
                features            (str)   —   qcconstants feature_list item
                                                             Ex: self.features_list.DATAPROTECTION
                show_to_user       (bool)   —   test case flag to determine if the test case is
                                                             to be shown to user or not
                Accept:
                                    True    –   test case will be shown to user from commcell gui
                                    False   –   test case will not be shown to user
                default: False
                tcinputs            (dict)  -   test case inputs with input name as dict key
                                                    and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Verify the behavior of outgoing network option - \"Force all data (along with control) into tunnel\" at network topology level."
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
            "source_ma": None,
            "destination_client": None
        }
        self.tc_subclient = None
        self.tc_storagepolicy = None
        self.network_helper = None
        self.client_grp_map = None
        self.client_hostname = None
        self.serverbase = None
        self.cs_hostname = None
        self.client_hostname = None
        self.machine_a = None
        self.machine_b = None
        self.clientgrp_a = 'clientgrpA_57901'
        self.clientgrp_b = 'clientgrpB_57901'
        self.test_subclient = "test_subclient_57901"
        self.start_port = 1024
        self.end_port = 1025
        self.network_topology_name = "Test_topology_57901"
    def get_hostnames(self, machine_obj):
        cmd = "ipconfig"
        res = machine_obj.execute_command(cmd).output.split("\n")
        hostnames = []
        for item in res :
            if item.find("IPv4 Address") != -1:
                hostname = item[item.find(":") + 1:]
                hostnames.append(hostname.strip())
        return hostnames
    def check_port(self):
        tunnel_port = self.client_b_obj.network.tunnel_connection_port
        hostnames_a = self.get_hostnames(self.machine_a)
        hostnames_b = self.get_hostnames(self.machine_b)
        self.log.info("Client A hostnames : {0}".format(str(hostnames_a)))
        self.log.info("Client B hostnames : {0}".format(str(hostnames_b)))
        cmd = 'netstat -ano'
        self.serverbase.restart_services([self.client_b])
        self.serverbase.check_client_readiness([self.client_b])
        self.machine_b.add_firewall_allow_port_rule(tunnel_port)
        self.machine_b.start_firewall()
        res = self.machine_b.execute_command(cmd).output
        self.log.info("Netstat output : {0}".format(res))
        res = res.replace(" ", "")
        entries = res.split("\n")
        expected_outputs = []
        for hostname_a in hostnames_a :
            for hostname_b in hostnames_b :
                expected_outputs.append("TCP{0}:{1}{2}".format(hostname_b, tunnel_port, hostname_a))
        self.log.info("Checking for one of the following entries in netstat output: \n{0}".format(str(expected_outputs)))
        for entry in entries:
            for expected_output in expected_outputs:
                if entry.find(expected_output) != -1:
                    return True
        return False
    def setup(self):
        """Setup function of this test case"""
        try:
            self.network_helper = NetworkHelper(self)
            self.serverbase = CommonUtils(self.commcell)
            self.clients_obj = self.commcell.clients
            self.entities = self.network_helper.entities
            # Client names
            self.client_a = self.tcinputs['destination_client'].lower()
            self.client_b = self.tcinputs['source_ma'].lower()
            self.client_b_obj = self.commcell.clients.get(self.client_b)
            self.client_a_obj = self.commcell.clients.get(self.client_a)
            self.machine_a = Machine(self.client_a_obj)
            self.machine_b = Machine(self.client_b_obj)
            # Create Client groups
            self.client_names_list = [self.client_a, self.client_b]
            # Client grp list
            self.client_grp_list = [self.clientgrp_a, self.clientgrp_b]
            self.clients_grps_obj = self.commcell.client_groups
            for client_grp, client_name in zip(self.client_grp_list, self.client_names_list):
                self.log.info('Creating client group: {0} with client: {1}'.format(client_grp, client_name))
                self.clients_grps_obj.add(client_grp, clients=[client_name])
            self.clientgrp_a_obj = self.commcell.client_groups.get(self.clientgrp_a)
            self.network_helper.remove_network_config([{'clientName': self.client_a},
                                                       {'clientName': self.client_b}])
            
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()
    def run(self):
        """Run function of this test case"""
        self.log.info('*' * 10 + "Started executing testcase 57901" + '*' * 10)
        try:
            # CLIENT GROUP LEVEL
            # Set one way between clientgrp_a and clientgrp_b
            self.network_helper.one_way_topology(self.clientgrp_a,
                                                self.clientgrp_b,
                                                self.network_topology_name,
                                                 0)
            self.network_helper.set_extra_ports(self.clientgrp_b, True, [{"startPort" : self.start_port, "endPort" : self.end_port}])
            # Push Configuration
            self.network_helper.push_config_clientgroup(self.client_grp_list)
            # Check summary for extra ports
            # clients_summary = self.network_helper.get_network_summary(self.client_names_list)
            # client_a_summary = clients_summary[self.client_a].lower()
            # client_b_summary = clients_summary[self.client_b].lower()
            # if ((self.client_a + " " + self.client_b) not in client_a_summary
            #         or 'extraports={0}-{1}'.format(self.start_port, self.end_port) not in
            #         client_a_summary):
            #     raise Exception("Network summary incorrect on client_a. extraports missing")
            # if ((self.client_b + " " + self.client_a) not in client_b_summary
            #         or '{0}-{1}'.format(self.start_port, self.end_port) not in
            #         client_b_summary):
            #     raise Exception("Network summary incorrect on client_b. data_ports missing.")
            self.log.info("Forcing all data traffic through tunnel on clientgrp: {0}".format(self.clientgrp_a))
            # self.log.info("Enabling firewall on client machine")
            # self.network_helper.enable_firewall([self.client_b], [8403])
            self.clientgrp_a_obj.refresh()
            properties = self.clientgrp_a_obj.properties
            properties['firewallConfiguration']['firewallOutGoingRoutes'][0]['fireWallOutGoingRouteOptions']['forceAllBackupRestoreDataTraffic'] = True
            self.clientgrp_a_obj.update_properties(properties)
            # Push Configuration
            self.network_helper.push_config_clientgroup(self.client_grp_list)
            #Check for extra ports
            # clients_summary = self.network_helper.get_network_summary(self.client_names_list)
            # client_a_summary = clients_summary[self.client_a].lower()
            # client_b_summary = clients_summary[self.client_b].lower()
            # if ((self.client_a + " " + self.client_b) not in client_a_summary
            #         or 'extraports={0}-{1}'.format(self.start_port, self.end_port) in
            #         client_a_summary):
            #     raise Exception("Network summary incorrect on client_a. extraports present")
            # if ((self.client_b + " " + self.client_a) not in client_b_summary
            #         or '{0}-{1}'.format(self.start_port, self.end_port) not in
            #         client_b_summary):
            #     raise Exception("Network summary incorrect on client_b. data_ports missing.")
            # port_res = self.check_port()
            # if port_res :
            #     self.log.info("Verified data pasing through tunel port only")
            # else :
            #     raise Exception("Data Pasing through ports other than the tunnel port")
            
            # Run backup job
            self.network_helper.validate_with_plan([self.client_a], self.client_b)
            self.log.info("*" * 10 + " Part 1 :TestCase {0} successfully passed for Client Group Level! ".format(
                self.id) + "*" * 10)
            self.log.info("Deleting client groups")
            for client_group in self.client_grp_list:
                if self.clients_grps_obj.has_clientgroup(client_group):
                    self.clients_grps_obj.delete(client_group)
            self.network_helper.remove_network_config([{'clientName': self.client_a},
                                                       {'clientName': self.client_b},
                                                       ])
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()
    def tear_down(self):
        """Tear down function of this test case"""
        self.network_helper.cleanup_network()
        self.log.info("Deleting client groups")
        for client_group in self.client_grp_list:
            if self.clients_grps_obj.has_clientgroup(client_group):
                self.clients_grps_obj.delete(client_group)
        self.entities.cleanup()