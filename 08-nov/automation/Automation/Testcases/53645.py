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


class TestCase(CVTestCase):
    """Class for executing basic network case to validate different types of tunnel connection
        protocols for outgoing routes with two-way firewall

        Setup requirements to run this test case:
        3 clients -- can be any client in the commcell

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("[Network & Firewall] : Tunnel connection protocol "
                     "validation(HTTPS, HTTPSA and RAW) and multistreams "
                     "with two-way firewall")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "FirewallClient1": None,
            "FirewallClient2": None,
            "FirewallClient3": None
        }
        self._client_group_name = 'CG_53645'
        self.commserv = None
        self._network = None
        self.client_group_obj = None

    def setup(self):
        """Setup function of this test case"""
        self.commserv = self.commcell.commserv_name

        self.client_list.extend([self.commserv,
                                 self.tcinputs['FirewallClient1'],
                                 self.tcinputs['FirewallClient2'],
                                 self.tcinputs['FirewallClient3']])

        self._network = NetworkHelper(self)

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]},
                                             {'clientName': self.client_list[2]},
                                             {'clientName': self.client_list[3]}])

        self._network.entities.create_client_groups([self._client_group_name])

        self.client_group_obj = self.commcell.client_groups.get(self._client_group_name)

    def run(self):
        """Run function"""

        try:

            # perform check readiness on the input clients before proceeding
            # with further steps
            self.client_group_obj.add_clients([self.client_list[3]])

            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("Started executing testcase")

            self._network.set_two_way({'clientName': self.commserv},
                                      {'clientName': self.tcinputs['FirewallClient1']})

            self._network.set_two_way({'clientName': self.tcinputs['FirewallClient2']},
                                      {'clientName': self.commserv})

            self._network.set_two_way({'clientName': self.commserv},
                                      {'clientGroupName': self._client_group_name})

            self._network.outgoing_route_settings({'clientName': self.tcinputs['FirewallClient1']},
                                                  is_client=True,
                                                  remote_entity=self.commserv,
                                                  connection_protocol=1,
                                                  streams=4)

            self._network.outgoing_route_settings({'clientName': self.commserv},
                                                  is_client=True,
                                                  remote_entity=self.tcinputs['FirewallClient1'],
                                                  connection_protocol=1,
                                                  streams=4)

            self._network.outgoing_route_settings({'clientName': self.commserv},
                                                  is_client=True,
                                                  remote_entity=self.tcinputs['FirewallClient2'],
                                                  connection_protocol=2,
                                                  streams=4)

            self._network.outgoing_route_settings({'clientName': self.tcinputs['FirewallClient2']},
                                                  is_client=True,
                                                  remote_entity=self.commserv,
                                                  connection_protocol=2,
                                                  streams=4)

            self._network.outgoing_route_settings({'clientGroupName': self._client_group_name},
                                                  is_client=True,
                                                  remote_entity=self.commserv,
                                                  connection_protocol=3,
                                                  streams=4)

            self._network.outgoing_route_settings({'clientName': self.commserv},
                                                  is_client=False,
                                                  remote_entity=self._client_group_name,
                                                  connection_protocol=3,
                                                  streams=4)

            self._network.push_config_client([self.tcinputs['FirewallClient1'],
                                              self.tcinputs['FirewallClient2'],
                                              self.commserv])

            self._network.push_config_clientgroup([self._client_group_name])

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.exclude_machine(self.client_list)

            client1_port = self._network.client_tunnel_port(self.tcinputs['FirewallClient1'])

            client2_port = self._network.client_tunnel_port(self.tcinputs['FirewallClient2'])

            client3_port = self._network.client_tunnel_port(self.tcinputs['FirewallClient3'])

            self._network.enable_firewall([self.tcinputs['FirewallClient1'],
                                           self.tcinputs['FirewallClient2'],
                                           self.tcinputs['FirewallClient3'],
                                           self.commserv],
                                          [client1_port, client2_port, client3_port, 8403])

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.validate([self.client_list[1],
                                    self.client_list[2],
                                    self.client_list[3]],
                                   self.commserv,
                                   test_data_level=2,
                                   test_data_size=50000)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()
            self._network.entities.cleanup()
