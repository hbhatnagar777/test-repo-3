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
from Server.Network import networkconstants


class TestCase(CVTestCase):
    """Class for executing basic network case to check shostname connectivity

        Setup requirements to run this test case:
        2 clients -- can be combination of windows, mac and unix

        Make sure sHOSTNAME under Machines in registry for one of the client
        is a bogus value.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("[Firewall] : validation of shostname  on a "
                     "client with one-way firewall(CS-->CC)")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK

        self.client_list = []
        self.tunnel_ports = []
        self.tcinputs = {
            "FirewallClient1": None,
            "FirewallClient2": None,
            "tunnelport1": None,
            "tunnelport2": None
            }

    def setup(self):
        """Setup function of this test case"""
        self.client_list.extend([self.tcinputs['FirewallClient1'],
                                 self.tcinputs['FirewallClient2']])

        self.tunnel_ports.extend([self.tcinputs['tunnelport1'],
                                  self.tcinputs['tunnelport2']])

        self._network = NetworkHelper(self)

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]}])

        self._network.push_config_client(self.client_list)

    def run(self):
        """Run function """

        try:

            # perform check readiness on the input clients before proceeding
            # with further steps
            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("Started executing {0} testcase".format(self.id))

            self._network.set_tunnelport([{'clientName': self.client_list[0]},
                                          {'clientName': self.client_list[1]}],
                                         self.tunnel_ports)

            self._network.set_one_way({'clientName': self.tcinputs['FirewallClient1']},
                                      {'clientName': self.tcinputs['FirewallClient2']})

            self._network.push_config_client(self.client_list)

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.exclude_machine(self.client_list)

            self._network.enable_firewall(self.client_list, self.tunnel_ports)

            self._network.options.sleep_time(networkconstants.NEWTWORK_TIMEOUT_SEC)

            self.log.info("Performing check readiness after enabling "
                          "windows firewall")

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.validate([self.client_list[1]], self.client_list[0])

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()
            self._network.entities.cleanup()
