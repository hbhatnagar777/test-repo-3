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

import time


class TestCase(CVTestCase):
    """Class for executing negative scenario for CV network connectivity
       with passive connection

        Setup requirements to run this test case:
        1 Windows client
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Negative scenario] : CV network connectivity with passive connection"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK

        self.client_list = []
        self.tunnel_ports = []
        self.tcinputs = {
            "FirewallClient1": None
            }
        self._network = None

    def setup(self):
        """Setup function of this test case"""
        self.client_list.extend([self.commcell.commserv_hostname,
                                 self.tcinputs['FirewallClient1']])

        self._network = NetworkHelper(self)

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]}])

        self._network.push_config_client(self.client_list)

    def run(self):
        """Run function """

        try:

            # perform check readiness on the input clients before proceeding
            # with further steps
            self._network.serverbase.check_client_readiness([self.tcinputs['FirewallClient1']])

            self.log.info("Started executing {0} testcase".format(self.id))

            incoming_connection1 = [
                {
                    'state': 'BLOCKED',
                    'entity': self.tcinputs['FirewallClient1'],
                    'isClient': True
                }]
            self.commcell.commserv_client.network.set_incoming_connections(incoming_connection1)
            self._network.push_config_client(self.client_list)

            self.log.info("allowing 30 seconds for rules to get effective")
            time.sleep(30)

            self.log.info("restarting CV services on client %s", self.tcinputs['FirewallClient1'])
            client_obj = self.commcell.clients.get(self.tcinputs['FirewallClient1'])
            client_obj.restart_services()

            check_readiness = True
            try:
                self._network.serverbase.check_client_readiness([self.tcinputs['FirewallClient1']])
            except Exception as excp:
                check_readiness = False
                self.log.info("check readiness failed as expected")

            if check_readiness:
                raise Exception("check readiness didn't fail as expected")

        except Exception as excp:
            self._network.server.fail(excp)
        finally:
            self._network.remove_network_config([{'clientName': self.client_list[0]},
                                                 {'clientName': self.client_list[1]}])
            self._network.push_config_client(self.client_list)

            self._network.cleanup_network()
            self._network.entities.cleanup()
