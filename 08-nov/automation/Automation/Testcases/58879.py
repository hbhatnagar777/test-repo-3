# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case

"""

import time
from datetime import datetime as dt
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.machine import Machine
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """
    This testcase verify silent install with Network Gateway topology
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Interactive install of a client  via network gateways"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK

        # tcinputs
        self.tcinputs = {
            "install_client_hostname": None,
            "install_client_username": None,
            "install_client_password": None,

            "proxy_name": None,
            "proxyPortNumber": None,

            "commservePassword": None,
            "commserveUsername": None
        }
        self.commserve = None
        self.client_name = None
        self.client_hostname = None
        self.proxy_name = None
        self.proxy_name1 = None

        # Time stamp
        self.time_stamp = str(dt.now().microsecond)

        # Groups
        self.client_group_name = None
        self.cs_group_name = None
        self.proxy_group_name = None
        self.topology_name = None

        # Helper
        self._network = None
        self.windows_machine = None
        self.windows_install_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.windows_machine = Machine(machine_name=self.tcinputs["install_client_hostname"],
                                       username=self.tcinputs["install_client_username"],
                                       password=self.tcinputs["install_client_password"])
        self.windows_install_helper = InstallHelper(self.commcell, self.windows_machine)
        self._network = NetworkHelper(self)

        # entity name
        self.commserve = self.commcell.commserv_name
        self.proxy_name = self.tcinputs['proxy_name'].split(';')[0]
        self.proxy_name1 = self.tcinputs['proxy_name'].split(';')[1]

        # tcinputs
        self.tcinputs["force_ipv4"] = "1"
        self.tcinputs["firewallConnectionType"] = '2'
        self.tcinputs["enableFirewallConfig"] = "1"
        self.tcinputs["showFirewallConfigDialogs"] = "1"
        self.tcinputs["proxyHostname"] = self.commcell.clients.get(self.proxy_name).client_hostname
        self.tcinputs["enableProxyClient"] = "1"

    def run(self):
        """Run function """
        try:
            self.single_network_gateway()
            self.multiple_network_gateway()
            self.negative_multiple_network_gateway()
            self.smart_topology()
        except Exception as excp:
            self.log.info("Exception: " + str(excp))
            self._network.server.fail(excp)

    def single_network_gateway(self):
        try:
            ###########################################################################################################
            #                            SINGLE GATEWAY, ONE WAY NETWORK TOPOLOGY                                     #
            ###########################################################################################################

            # Setting tcinputs
            networkgateway = self.commcell.clients.get(self.proxy_name).client_hostname + ':' \
                             + self.tcinputs['proxyPortNumber'].split(';')[0]

            self.log.info("Step 1: enable firewall wall at commserve, proxy, and client, add inbound rules to client")
            self._network.enable_firewall([self.commserve, self.proxy_name], [8399, 8403])

            self.windows_machine.start_firewall()

            self.log.info("Step 2: Create client Groups")
            self.create_groups(networkgateway)
            self.commcell.client_groups.add(self.proxy_group_name, [self.proxy_name])

            self.log.info("Step 3: Check readiness for all proxy and commserve")
            self._network.serverbase.check_client_readiness([self.proxy_name, self.commserve])

            self.log.info("Step 4: Create network topology")
            self._network.proxy_topology(self.client_group_name,
                                         self.cs_group_name,
                                         self.proxy_group_name,
                                         self.topology_name)

            self.log.info("Step 5: Perform Silent Install")
            fr = 'SP' + self.commcell.version.split('.')[1]
            self.windows_install_helper.silent_install(tcinputs=self.tcinputs,
                                                       client_name=self.client_name,
                                                       feature_release=fr)

            self.log.info("Step 6: Check client readiness, group and teardown")
            self.check_and_clean_up()
            self.log.info("Step #: Single gateway topology is successfull")



        finally:
            self.clean_up()

    def multiple_network_gateway(self):
        try:
            ###########################################################################################################
            #                                         MULTIPLE GATEWAY TOPOLOGY                                       #
            ###########################################################################################################

            # Setting tcinputs
            self.tcinputs["proxyHostname"] = self.commcell.clients.get(self.proxy_name).client_hostname \
                                             + ';' + self.commcell.clients.get(self.proxy_name1).client_hostname

            networkgateway = self.commcell.clients.get(self.proxy_name).client_hostname + ':' + self.tcinputs[
                'proxyPortNumber'].split(';')[0]
            networkgateway += ';'
            networkgateway += self.commcell.clients.get(self.proxy_name1).client_hostname + ':' + self.tcinputs[
                'proxyPortNumber'].split(';')[1]

            self.log.info("Step 1: enable firewall wall at commserve, proxy, and client, add inbound rules to client")
            self._network.enable_firewall([self.commserve, self.proxy_name],
                                          [8399, 8403])

            # self.windows_machine.start_firewall()

            self.log.info("Step 2: Create client Groups")
            self.create_groups(networkgateway)
            self.commcell.client_groups.add(self.proxy_group_name, [self.proxy_name, self.proxy_name1])

            self.log.info("Step 3: Check readiness for all proxy and commserve")
            self._network.serverbase.check_client_readiness(
                [self.proxy_name, self.proxy_name1, self.commserve])

            self.log.info("Step 4: Create network topology")
            self._network.proxy_topology(self.client_group_name,
                                         self.cs_group_name,
                                         self.proxy_group_name,
                                         self.topology_name)

            self.log.info("Step 5: Perform Silent Install")
            fr = 'SP' + self.commcell.version.split('.')[1]
            self.windows_install_helper.silent_install(tcinputs=self.tcinputs,
                                                       client_name=self.client_name,
                                                       feature_release=fr)

            self.log.info("Step 6: Check client readiness, group and teardown")
            self.check_and_clean_up()
            self.log.info("Step #: Multiple gateway topology is successfull")


        finally:
            self.clean_up()

    def negative_multiple_network_gateway(self):
        try:
            ###########################################################################################################
            #                     NEGATIVE TEST CASE  MULTIPLE GATEWAY TOPOLOGY                                       #
            ###########################################################################################################

            self.tcinputs["proxyHostname"] = self.commcell.clients.get(self.proxy_name).client_hostname \
                                             + ';' + self.commcell.clients.get(self.proxy_name1).client_hostname \
                                             + ';' + self.commcell.clients.get(
                self.tcinputs['proxy_name'].split(';')[2]).client_hostname
            # Setting extra tcinputs
            networkgateway = self.commcell.clients.get(self.proxy_name).client_hostname + ':' + self.tcinputs[
                'proxyPortNumber']
            networkgateway += ';'
            networkgateway += self.commcell.clients.get(self.proxy_name1).client_hostname + ':' + self.tcinputs[
                'proxyPortNumber'].split(';')[1]

            self.log.info("Step 1: enable firewall wall at commserve, proxy, and client, add inbound rules to client")
            self._network.enable_firewall([self.commserve, self.proxy_name],
                                          [8399, 8403])

            # self.windows_machine.start_firewall()

            self.log.info("Step 2: Create client Groups")
            self.create_groups(networkgateway)
            self.commcell.client_groups.add(self.proxy_group_name, [self.proxy_name, self.proxy_name1])

            self.log.info("Step 3: Check readiness for all proxy and commserve")
            self._network.serverbase.check_client_readiness(
                [self.proxy_name, self.proxy_name1, self.commserve])

            self.log.info("Step 4: Create network topology")
            self._network.proxy_topology(self.client_group_name,
                                         self.cs_group_name,
                                         self.proxy_group_name,
                                         self.topology_name)
            # Turn off the services in Proxy 2
            proxy_2_cl_obj = self.commcell.clients.get(self.proxy_name1)
            proxy_2_cl_obj._service_operations(service_name='ALL', operation='STOP')

            self.log.info("Step 5: Perform Silent Install")
            fr = 'SP' + self.commcell.version.split('.')[1]
            self.windows_install_helper.silent_install(tcinputs=self.tcinputs,
                                                       client_name=self.client_name,
                                                       feature_release=fr)

            self.log.info("Step 6: Check readiness for client ")
            self._network.serverbase.check_client_readiness([self.commserve, self.client_name])

            self.log.info("Step 6: Check client readiness, group and teardown")
            self.check_and_clean_up()
            self.log.info("Step #: Negative test for gateway topology is successfull")

        finally:
            self.clean_up()

    def smart_topology(self):
        try:
            ###########################################################################################################
            #                                 SMART NETWORK TOPOLOGY                                                  #
            ###########################################################################################################

            # Setting extra tcinputs
            networkgateway = self.commcell.clients.get(self.proxy_name).client_hostname

            self.log.info("Step 1: enable firewall wall at commserve, proxy, and client, add inbound rules to client")
            self._network.enable_firewall([self.commserve, self.proxy_name], [8399, 8403])

            self.log.info("Step 2: Create client Groups")
            self.create_groups(networkgateway)
            self.commcell.client_groups.add(self.proxy_group_name, [self.proxy_name])

            self.log.info("Step 3: Check readiness for all clients")
            self._network.serverbase.check_client_readiness([self.proxy_name, self.commserve])

            self.log.info("Step 4: Create network topology")
            self._network.proxy_topology(self.client_group_name,
                                         "My CommServe Computer",
                                         self.proxy_group_name,
                                         self.topology_name)

            self.log.info("Step 5: Perform Silent Install")
            fr = 'SP' + self.commcell.version.split('.')[1]
            self.windows_install_helper.silent_install(tcinputs=self.tcinputs,
                                                       client_name=self.client_name,
                                                       feature_release=fr)

            self.log.info("Step 6: Check client readiness, group and teardown")
            self.check_and_clean_up()
            self.log.info("Step #: Smart topology is successfull")
            self._network.cleanup_network()

        finally:
            self.clean_up()

    def check_and_clean_up(self):
        time.sleep(300)
        self._network.serverbase.check_client_readiness([self.client_name])
        self.log.info(" Check if client is added to client group")
        if self.client_name not in self.commcell.client_groups.get(self.client_group_name).associated_clients:
            self.log.info("Client not added to client group")
            raise Exception("Client not added to client group")
        self._network.cleanup_network()
        self.windows_install_helper.uninstall_client()

    def create_groups(self, networkgateway):
        self.time_stamp = str(dt.now().microsecond)
        self.client_name = "test_58879_" + self.time_stamp
        self.proxy_group_name = "cg_58879_proxy_" + self.time_stamp
        self.cs_group_name = "cg_58879_commserve_" + self.time_stamp
        self.client_group_name = "cg_58879_client_" + self.time_stamp
        self.topology_name = "gateway_test_58879_" + self.time_stamp

        self.tcinputs["networkGateway"] = networkgateway
        self.tcinputs["clientGroupName"] = self.client_group_name

        self.commcell.client_groups.add(self.client_group_name, [])
        self.commcell.client_groups.add(self.cs_group_name, [self.commserve])

    def clean_up(self):
        self._network.cleanup_network()
        self.commcell.client_groups.delete(self.client_group_name)
        self.commcell.client_groups.delete(self.proxy_group_name)
        self.commcell.client_groups.delete(self.cs_group_name)

