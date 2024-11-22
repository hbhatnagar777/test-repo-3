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
    """Class for executing basic network case to validate FwConfigLocal file upgrade case
        Note: This test case requires pre-configuration in FwConfigLocal file on CS and client

        Setup requirements to run this test case:
        1 client -- routes between CS and this client should already be
        present in FwConfigLocal file on the setups.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Firewall] : FwConfigLocal.txt  file validation for service pack upgrades."
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "FirewallClient": None,
            "TunnelPort": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.commserv = self.commcell.commserv_name

        self.client_list.extend([self.commserv, self.tcinputs['FirewallClient']])

        self._network = NetworkHelper(self)

    def run(self):
        """Run function """

        try:

            # perform check readiness on the input clients before proceeding
            # with further steps
            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("Started executing testcase")

            self._network.exclude_machine(self.client_list)

            self._network.enable_firewall([self.tcinputs['FirewallClient'],
                                           self.commserv],
                                          [self.tcinputs['TunnelPort'],
                                           8403])

            self._network.do_cvping(self.client_list[0],
                                    self.client_list[1],
                                    self.tcinputs['TunnelPort'])

            self.log.info("Performing check readiness after enabling windows firewall")

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.validate([self.client_list[1]], self.commserv)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()

