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
    """Class for executing basic network case to validate GUI TPPM

        Setup requirements to run this test case:
        1 client -- this client will be used as proxy client to
        forward connections to port 8401

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Firewall] : GUI TPPM validation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "ProxyClient": None,
            "TppmPort": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.commserv = self.commcell.commserv_name

        self.client_list.extend([self.commserv, self.tcinputs['ProxyClient']])

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

            self._network.set_gui_tppm({'clientName': self.commserv},
                                       {'proxyEntity': self.tcinputs['ProxyClient'],
                                        'portNumber': self.tcinputs['TppmPort']})

            self._network.push_config_client([self.client_list[1],
                                              self.client_list[0]])

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.exclude_machine(self.client_list)

            self._network.enable_firewall([self.tcinputs['ProxyClient'],
                                           self.tcinputs['ProxyClient'],
                                           self.commserv],
                                          [8403, 8408, 8403])

            self.log.info("Performing check readiness after enabling windows firewall")

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.do_cvping(self.client_list[1],
                                    self.client_list[0],
                                    8403)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()
