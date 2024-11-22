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
    This testcase verify silent install with One way topology
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Install]:Silent Installation on a Unix machine with One-Way(Client->CS) Firewall"
        self.tcinputs = {
            "portNumber": None
        }

        self.install_inputs = None
        self.unix_client_name = None
        self.unix_client_hostname = None
        self.client_group_name = None
        self.commserv = None
        self.time_stamp = None

        # Helper objects
        self.network_helper = None
        self.unix_machine_obj = None
        self.unix_install_helper = None
        self.config_json = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Now Running setup function")
        self.config_json = config.get_config()
        install_helper = InstallHelper(self.commcell)
        self.unix_machine_obj = install_helper.get_machine_objects(type_of_machines=2)[0]
        self.unix_install_helper = InstallHelper(self.commcell, self.unix_machine_obj)

        self.commserv = self.commcell.commserv_name
        self.network_helper = NetworkHelper(self)

        # Inputs required for firewall configuration during silent install
        self.install_inputs = {
            "firewallConnectionType": "2",
            "networkGateway": self.commcell.commserv_hostname,
            "enableFirewallConfig": "1",
            "showFirewallConfigDialogs": "1",
            "mediaPath": self.config_json.Install.media_path,
            "authCode": self.commcell.enable_auth_code(),
            "proxyHostname": self.commcell.commserv_hostname,
            "proxyPortNumber": "8403",
            "enableProxyClient": "1"
        }

        self.time_stamp = str(dt.now().microsecond)
        self.client_group_name = "client_group_" + self.time_stamp

        self.install_inputs.update({"clientGroupName": self.client_group_name})
        self.unix_client_name = self.config_json.Install.unix_client.client_name
        self.unix_client_hostname = self.config_json.Install.unix_client.machine_host
        self.log.info("Setup function executed")

    def run(self):
        """Run function """
        try:
            self.log.info("Inside run function")

            self.log.info("Step 1: Enable firewall on commserve")
            self.network_helper.enable_firewall([self.commserv], [8403])

            self.log.info("Step 2: Enable firewall on client and add inbound rule")
            port_number = int(self.tcinputs["portNumber"])
            firewall_rule = f"pass in proto tcp from any to any port = {port_number}"
            firewall_file_scan = self.unix_machine_obj.read_file("/etc/firewall/pf.conf")
            if firewall_rule not in firewall_file_scan:
                self.log.info("Adding firewall rule")
                executed_ops = [self.unix_machine_obj.execute(f"echo \"pass in proto tcp from any to any port = {port_number}\" "
                                                              ">> /etc/firewall/pf.conf"),
                                self.unix_machine_obj.execute("pfctl -nf /etc/firewall/pf.conf")]

                for outputs in executed_ops:
                    if outputs.exit_code != 0:
                        raise Exception("Failed to enable firewall on Solaris Machine")

            # Command to turn on Firewall Service on Solaris Machine
            self.unix_machine_obj.execute("svcadm enable firewall")

            self.log.info("Step 4: Create Dummy Unix Client with default port")
            self.commcell.clients.create_pseudo_client(client_name=self.unix_client_name,
                                                       client_hostname=self.unix_client_hostname,
                                                       client_type="unix")

            self.log.info("Step 5: Create client group and commserve group")
            self.commcell.client_groups.add(self.client_group_name, [self.unix_client_name])

            self.log.info("Step 6: Set one way network Topology from commserve group to client group")
            self.network_helper.set_one_way({"clientName": self.commserv}, {"clientGroupName": self.client_group_name})
            self.network_helper.push_config_clientgroup([self.client_group_name])

            self.log.info("Step 8: Perform silent install")
            fr = 'SP' + self.commcell.version.split('.')[1]

            # Creating Directory for Mounting
            self.unix_machine_obj.execute("umount /cvbuild")
            self.unix_machine_obj.remove_directory("/cvbuild")
            self.unix_install_helper.silent_install(client_name=self.unix_client_name,
                                                    tcinputs=self.install_inputs,
                                                    feature_release=fr)

            self.log.info("Step 9: Check readiness for client")
            client_obj = self.commcell.clients.get(self.unix_client_name)
            if client_obj.is_ready:
                self.log.info("Client is reachable from the CS")

        except Exception as excp:
            self.log.info("Exception: " + str(excp))
            self.network_helper.server.fail(excp)

        finally:
            self.log.info("Cleaning up")
            self.unix_machine_obj.execute("svcadm disable network/firewall")
            self.unix_install_helper.uninstall_client()
            self.network_helper.cleanup_network()
            self.commcell.client_groups.delete(self.client_group_name)
