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
    This testcase verify silent install with One way topology
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Network & Firewall]:Interactive install of a client with one-way network route from CS to client"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "install_client_hostname": None,
            "install_client_username": None,
            "install_client_password": None,

            "commservePassword": None,
            "commserveUsername": None,

            "portNumber": None
        }

        self.dummy_client_name = None
        self.dummy_host_name = None
        self.client_group_name = None
        self.commserv = None
        self.clientCSName = None
        self.time_stamp = None

        # Helper objects
        self._network = None
        self.windows_machine = None
        self.windows_install_helper = None

    # noinspection PyTypeChecker
    def setup(self):
        """Setup function of this test case"""
        self.log.info("running setup function")
        self.windows_machine = Machine(
                                machine_name=self.tcinputs["install_client_hostname"],
                                username=self.tcinputs["install_client_username"],
                                password=self.tcinputs["install_client_password"])
        self.windows_install_helper = InstallHelper(self.commcell, self.windows_machine)

        self.commserv = self.commcell.commserv_name
        self._network = NetworkHelper(self)

        # Set tcinputs
        self.tcinputs["force_ipv4"] = "1"
        self.tcinputs["firewallConnectionType"] = "1"
        self.tcinputs["networkGateway"] = self.tcinputs["portNumber"]
        self.tcinputs["enableFirewallConfig"] = "1"
        self.tcinputs["showFirewallConfigDialogs"] = "1"

        self.time_stamp = str(dt.now().microsecond)
        self.tcinputs["clientGroupName"] = "cg_58878_clients" + self.time_stamp

        self.client_group_name = self.tcinputs["clientGroupName"]
        self.dummy_client_name = "test_58878_" + self.time_stamp
        self.clientCSName = "cg_58878_commserve" + self.time_stamp
        self.dummy_host_name = self.tcinputs["install_client_hostname"]
        self.log.info("Setup function executed")

    # noinspection PyTypeChecker
    def run(self):
        """Run function """

        try:
            self.log.info("Inside run function")

            self.log.info("Step 1: Enable firewall on commserve")
            self._network.enable_firewall([self.commserv], [8399])

            self.log.info("Step 2: Enable firewall on client and add inbound rule")
            self.windows_machine.add_firewall_allow_port_rule(int(self.tcinputs["portNumber"]))

            self.log.info("Step 4: Create Dummy Client with default port")
            self.commcell.clients.create_pseudo_client(self.dummy_client_name, self.dummy_host_name)

            self.log.info("Step 4.1: setting tunnel port")
            self._network.set_tunnelport([{'clientName': self.dummy_client_name}], [int(self.tcinputs["portNumber"])])

            self.log.info("Step 5: Create client group and commserve group")
            self.commcell.client_groups.add(self.client_group_name, [self.dummy_client_name])
            self.commcell.client_groups.add(self.clientCSName, [self.commserv])

            self.log.info("Step 6: Set one way network Topology from commserve group to client group")
            topology_name = "cs_to_cl_58878_" + self.time_stamp
            self._network.one_way_topology(self.clientCSName, self.client_group_name, topology_name)

            self.log.info("Step 7: Validate oneway network topology")
            self._network.validate_one_way_topology(topology_name)

            self.log.info("Step 8: Perform silent install")
            fr = 'SP' + self.commcell.version.split('.')[1]
            
            self.windows_install_helper.silent_install(client_name=self.dummy_client_name,
                                                       tcinputs=self.tcinputs,
                                                       feature_release=fr)

            self.log.info("Step 9: Check readiness for client")
            time.sleep(5)
            self._network.serverbase.check_client_readiness([self.dummy_client_name])

            networksummary = self._network.get_network_summary([self.dummy_client_name])[self.dummy_client_name]
            self.validate_network_summary(networksummary)
            pass
        except Exception as excp:
            self.log.info("Exception: " + str(excp))
            self._network.server.fail(excp)

        finally:
            self.log.info("Cleaning up")
            self._network.cleanup_network()
            self.commcell.client_groups.delete(self.client_group_name)
            self.commcell.client_groups.delete(self.clientCSName)
            self.commcell.clients.delete(self.dummy_client_name)
            self.windows_install_helper.uninstall_client()

    def validate_network_summary(self, networksummary):
        """
        This method check if type=passive or not
        """
        if not ('type=passive' in str(networksummary)):
            raise Exception("Network tunnel type should be passive")
