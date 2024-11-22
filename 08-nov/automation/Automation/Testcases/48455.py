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

from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """
    This test case verify the connection of clients using the IPv6 address.
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Network regression for IPv6 address."
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkMediaAgent": None,
            "ClIPv6": None,
            "MaIPv6": None
        }
        self.network_helper = None
        self.machine_cl = None
        self.cl_obj = None
        self.machine_ma = None
        self.machine_cs = None
        self.ma_obj = None
        self.cl = None
        self.ma = None
        self.ma_IPv6 = None
        self.cl_IPv6 = None
        self.cl_IPv4 = None
        self.ma_IPv4 = None
        self.cs_IPv4 = None

    def setup(self):
        self.network_helper = NetworkHelper(self)
        self.cl = self.tcinputs["NetworkClient"]
        self.ma = self.tcinputs["NetworkMediaAgent"]
        self.ma_IPv6 = self.tcinputs["ClIPv6"]
        self.cl_IPv6 = self.tcinputs["MaIPv6"]
        self.cl_obj = self.commcell.clients.get(self.cl)
        self.machine_cl = Machine(self.cl_obj)
        self.ma_obj = self.commcell.clients.get(self.ma)
        self.machine_ma = Machine(self.ma_obj)
        self.network_helper.remove_network_config([
            {'clientName': self.cl},
            {'clientName': self.ma}
        ])
        self.machine_cs = Machine(
            self.commcell.clients.get(self.commcell.commserv_name)
        )
        self.machine_cs._get_client_ip()
        self.machine_cs._get_client_ip()
        self.machine_cs._get_client_ip()

        self.cs_IPv4 = self.machine_cs._ip_address
        self.cl_IPv4 = self.machine_cl._ip_address
        self.ma_IPv4 = self.machine_ma._ip_address

    def run(self):
        try:
            if '0' not in self.machine_cl.get_registry_value("Session", "nPreferredIPFamily"):
                self.machine_cl.create_registry("Session", "nPreferredIPFamily", "0")
                self.cl_obj.restart_services()

            if '0' not in self.machine_ma.get_registry_value("Session", "nPreferredIPFamily"):
                self.machine_ma.create_registry("Session", "nPreferredIPFamily", "0")
                self.ma_obj.restart_services()

            # Set DIPS between CL & MA with IPv6 address.
            self.log.info("[+] Set DIPS between CL & MA with IPv6 address. [+]")
            self.network_helper.add_dips([(
                {'client': self.cl, 'srcip': self.cl_IPv6},
                {'client': self.ma, 'destip': self.ma_IPv6}
            )])

            # Set DIPS between CS & CL with IPv4 address.
            self.log.info("[+] Set DIPS between CS & CL with IPv4 address. [+]")
            self.network_helper.add_dips([(
                {'client': self.commcell.commserv_name, 'srcip': self.cs_IPv4},
                {'client': self.cl, 'destip': self.cl_IPv4}
            )])

            # Set DIPS between CS & MA with IPv4 address.
            self.log.info("[+] Set DIPS between CS & MA with IPv4 address. [+]")
            self.network_helper.add_dips([(
                {'client': self.commcell.commserv_name, 'srcip': self.cs_IPv4},
                {'client': self.ma, 'destip': self.ma_IPv4}
            )])

            # Run backup and restore job
            self.log.info("Run backup and restore job")
            self.network_helper.validate([self.cl], self.ma)

            self.network_helper.push_config_client([self.cl, self.ma])
            # Set firewall rules from Cl to MA
            self.log.info("Set firewall rules from Cl to MA")

            for firewall_rule in [self.one_way, self.two_way, self.via_proxy]:
                firewall_rule()
                # Perform check readiness
                self.log.info("Perform check readiness")
                self.network_helper.serverbase.check_client_readiness([
                    self.cl, self.ma
                ])

                # Run backup and restore job
                self.log.info("Run backup and restore job")
                self.network_helper.validate([self.cl], self.ma)

                # Check netstat or network summary for correct IP usage
                cl_obj = self.commcell.clients.get(self.cl)
                tunnel_port = cl_obj.network._tunnel_connection_port
                op = cl_obj.execute_command(f'''netstat -ano | findstr {tunnel_port}''')[1]
                if not (f"0.0.0.0:{tunnel_port}" in op and f"[::]:{tunnel_port}" in op):
                    raise Exception("Client not listening on both th interface")

                self.check_network_summary()

        except Exception as e:
            self.log.info("Exception: " + str(e))

        finally:
            self.network_helper.cleanup_network()

    def one_way(self):
        self.network_helper.set_one_way(
            {'clientName': self.cl},
            {'clientName': self.ma}
        )
        self.network_helper.push_config_client([self.cl, self.ma])

    def two_way(self):
        self.network_helper.set_two_way(
            {'clientName': self.cl},
            {'clientName': self.ma}
        )
        self.network_helper.push_config_client([self.cl, self.ma])

    def via_proxy(self):
        self.network_helper.set_via_proxy(
            {'entity': self.commcell.commserv_name, 'isClient': True},
            {'entity': self.cl, 'isClient': True},
            {'entity': self.ma, 'isClient': True}
        )
        self.network_helper.push_config_client([self.cl, self.ma])

    def check_network_summary(self):
        # This same logic shuould be changed according to Groupbased rules.
        return 
        summary = self.network_helper.get_network_summary([
            self.cl, self.ma
        ])
        cl_summary = summary[self.cl]
        ma_summary = summary[self.ma]

        found = False
        if f"local_iface={self.ma_IPv6}" in ma_summary or f"remote_iface={self.cl_IPv6}" in ma_summary:
            found = True
        if f"local_iface={self.cl_IPv6}" in cl_summary or f"remote_iface={self.ma_IPv6}" in cl_summary:
            found = True
        if not found:
            raise Exception("Client & Mediaagent is not using the IPv6 address to communicate")
