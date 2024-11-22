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
    """Class for executing basic network case to check roaming client option

        Setup requirements to run this test case:
        2 clients -- can be combination of windows, mac and unix

        one of the input client should be laptop client

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Firewall] : Verify bypassable flag (roaming client option)"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tunnel_ports = []
        self.tcinputs = {
            "FirewallClient1": None,
            "FirewallClient2": None
        }

        self._client_group_name = networkconstants.CLIENT_GROUP_NAME[4]

    def setup(self):
        """Setup function of this test case"""
        self.commserv = self.commcell.commserv_name

        self.client_list.extend([self.commserv,
                                 self.tcinputs['FirewallClient1'],
                                 self.tcinputs['FirewallClient2']])

        self._network = NetworkHelper(self)

        self._network.entities.create_client_groups([self._client_group_name])

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]},
                                             {'clientName': self.client_list[2]}])

        self._network.push_config_client(self.client_list)

        self.client_group_obj = self.commcell.client_groups.\
                                    get(self._client_group_name)

    def run(self):
        """Run function """

        try:

            # perform check readiness on the input clients before proceeding
            # with further steps
            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("Started executing {0} testcase".format(self.id))

            self.client_group_obj.add_clients([self.client_list[2]])

            self._network.set_one_way({'clientName': self.commserv},
                                      {'clientName': self.client_list[1]})

            self._network.set_two_way({'clientName': self.commserv},
                                      {'clientGroupName': self._client_group_name})

            self._network.enable_roaming_client([{'clientName': self.client_list[1]},
                                                 {'clientGroupName': self._client_group_name}])

            self._network.push_config_client([self.client_list[1], self.client_list[0]])

            self._network.push_config_clientgroup([self._client_group_name])

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.exclude_machine(self.client_list)
            
            self._network.enable_firewall([self.tcinputs['FirewallClient1'],
                                           self.tcinputs['FirewallClient2'],
                                           self.tcinputs['FirewallClient1'],
                                           self.tcinputs['FirewallClient2'],
                                           self.commserv],
                                           [8403, 8403, 8408, 8408, 8403])

            self.log.info("Performing check readiness after enabling firewall")

            self._network.options.sleep_time(networkconstants.NEWTWORK_TIMEOUT_SEC)

            self._network.serverbase.check_client_readiness(self.client_list)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()
            self._network.entities.cleanup()
