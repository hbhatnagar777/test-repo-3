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

from datetime import datetime as dt
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from Install.install_helper import InstallHelper
from AutomationUtils import config


class TestCase(CVTestCase):
    """
    This testcase verify silent install with Network Gateway topology
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Solaris Firewall using proxy machine"
        self.tcinputs = {
            "proxy_name": None,
            "proxyPortNumber": None
        }
        self.commserve = None
        self.client_name = None
        self.proxy_name = None
        self.proxy_hostname = None
        self.proxy_port = None
        self.proxy_machine = None
        self.unix_machine = None
        self.install_inputs = None

        # Time stamp
        self.time_stamp = str(dt.now().microsecond)

        # Groups
        self.client_group_name = None
        self.cs_group_name = None
        self.proxy_group_name = None
        self.topology_name = None

        # Helper
        self.unix_install_helper = None
        self.network_helper = None
        self.config_json = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Now Running setup function")

        self.log.info("Creating Solaris Machine Object in order to Perform Installation")
        self.config_json = config.get_config()
        install_helper = InstallHelper(self.commcell)
        self.unix_machine = install_helper.get_machine_objects(type_of_machines=2)[0]
        self.unix_install_helper = InstallHelper(self.commcell, self.unix_machine)

        # Get Proxy Details
        self.proxy_name = self.tcinputs.get("proxy_name")
        self.proxy_port = self.tcinputs.get("proxyPortNumber")
        self.proxy_hostname = self.commcell.clients.get(self.proxy_name).client_hostname

        self.network_helper = NetworkHelper(self)
        self.commserve = self.commcell.commserv_name

        self.install_inputs = {
            "enableProxyClient": "1",
            "firewallConnectionType": "2",
            "enableFirewallConfig": "1",
            "showFirewallConfigDialogs": "1",
            "proxyHostname": self.proxy_hostname,
            "proxyPortNumber": self.proxy_port,
            "authCode": self.commcell.enable_auth_code(),
            "mediaPath": self.config_json.Install.media_path,
            "networkGateway": self.proxy_hostname + ':' + str(self.proxy_port)
        }

    def run(self):
        """Run function """
        try:
            # SINGLE GATEWAY, ONE WAY NETWORK TOPOLOGY
            self.log.info("Step 1: enable firewall wall at commserve, proxy, and client, add inbound rules to client")
            self.network_helper.enable_firewall([self.commserve, self.proxy_name], [8399, 8403])

            self.log.info("Step 2: Create client Groups")
            self.create_groups()
            self.commcell.client_groups.add(self.proxy_group_name, [self.proxy_name])

            self.log.info("Step 3: Check readiness for all proxy and commserve")
            self.network_helper.serverbase.check_client_readiness([self.proxy_name, self.commserve])

            self.log.info("Step 4: Create network topology")
            self.network_helper.proxy_topology(self.client_group_name,
                                               self.cs_group_name,
                                               self.proxy_group_name,
                                               self.topology_name)

            self.log.info("Step 5: Perform Silent Install")
            install_helper = InstallHelper(self.commcell, self.unix_machine)
            install_helper.silent_install(tcinputs=self.install_inputs,
                                          client_name=self.client_name)

            self.log.info("Step 6: Check client readiness, group and teardown")
            self.check_and_clean_up()
            self.log.info("Single gateway topology is successfull")

        except Exception as excp:
            self.log.info("Exception: " + str(excp))
            self.network_helper.server.fail(excp)

        finally:
            self.network_helper.cleanup_network()
            self.unix_machine.execute("svcadm disable network/firewall")
            self.unix_install_helper.uninstall_client()
            self.commcell.client_groups.delete(self.client_group_name)
            self.commcell.client_groups.delete(self.proxy_group_name)
            self.commcell.client_groups.delete(self.cs_group_name)

    def check_and_clean_up(self):
        # Check Readiness of the Client
        self.log.info("Checking readiness for client")
        client_obj = self.commcell.clients.get(self.client_name)
        if client_obj.is_ready:
            self.log.info("Client is reachable from the CS")

        self.log.info(" Check if client is added to client group")
        if self.client_name not in self.commcell.client_groups.get(self.client_group_name).associated_clients:
            self.log.info("Client not added to client group")
            raise Exception("Client not added to client group")
        self.network_helper.cleanup_network()

    def create_groups(self):
        self.time_stamp = str(dt.now().microsecond)
        self.client_name = "solaris_test_" + self.time_stamp
        self.proxy_group_name = "proxy_group_" + self.time_stamp
        self.cs_group_name = "cs_group_" + self.time_stamp
        self.client_group_name = "client_group_" + self.time_stamp
        self.topology_name = "solaris_gateway_test"

        self.install_inputs.update({"clientGroupName": self.client_group_name})

        self.commcell.client_groups.add(self.client_group_name, [])
        self.commcell.client_groups.add(self.cs_group_name, [self.commserve])
