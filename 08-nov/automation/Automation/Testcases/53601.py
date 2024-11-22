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

    """Class for executing validation for prevention of client side orphaning

        Setup requirements to run this test case:
        1 client

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Validation for prevention of client side orphaning"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "FirewallClient1": None
        }
        self.client_list = []

        self._client_group_name = "CG_53601"

        self.client_group_obj = None
        self._network = None
        self.commserv = ""

    def setup(self):
        """Setup function of this test case"""

        self._network = NetworkHelper(self)

        self.commserv = self.commcell.commserv_name

        self.client_list.extend([self.commserv,
                                 self.tcinputs['FirewallClient1']])

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]}])

        self._network.entities.create_client_groups([self._client_group_name])

        self.client_group_obj = self.commcell.client_groups.get(self._client_group_name)

    def run(self):
        """Run function """

        try:
            self._network.serverbase.check_client_readiness(self.client_list)

            self.client_group_obj.add_clients([self.client_list[1]])

            self.log.info("Started executing testcase")

            self._network.set_one_way({'clientName': self.commserv},
                                      {'clientGroupName': self._client_group_name})

            self._network.push_config_clientgroup([self._client_group_name])

            self._network.push_config_client([self.commserv])

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.exclude_machine(self.client_list)

            self._network.enable_firewall([self.commserv,
                                           self.client_list[1]],
                                          [8403, 8403])

            self._network.serverbase.check_client_readiness(self.client_list)
            # remove client from the group to remove firewall routes
            self.client_group_obj.remove_clients([self.client_list[1]])

            self._network.push_config_client([self.client_list[1]])

            self._network.options.sleep_time(60)
            # check client readiness with fallback route
            self._network.serverbase.check_client_readiness(self.client_list)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()
            self._network.entities.cleanup()
