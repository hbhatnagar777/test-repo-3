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
    """Class for executing basic network case to validate persistent tunnel behavior

        Setup requirements to run this test case:
        1 client and 1 media agent in the commcell

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("[Network & Firewall] : Verify restart of services "
                     "on passive side brings up the persistent tunnels immediately")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkMediaAgent": None
           }
        self._client_group_name1 = 'CG1_63294'
        self._client_group_name2 = 'CG2_63294'
        self.commserv = None
        self._network = None
        self.client_group_obj = None
        self.topology_name = "TOPOLOGY_63294"
        self.client_groups = None
        self.client_group_obj1 = None
        self.client_group_obj2 = None

    def setup(self):
        """Setup function of this test case"""
        self.commserv = self.commcell.commserv_name

        self.client_list.extend([self.commserv,
                                 self.tcinputs['NetworkClient'],
                                 self.tcinputs['NetworkMediaAgent']])

        self._network = NetworkHelper(self)

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]},
                                             {'clientName': self.client_list[2]}])

        self._network.push_config_client([self.client_list[0],
                                          self.client_list[1],
                                          self.client_list[2]])

        self.client_groups = self._network.entities.create_client_groups([self._client_group_name1,
                                                                          self._client_group_name2])

        self.client_group_obj1 = self.client_groups[self._client_group_name1]['object']
        self.client_group_obj2 = self.client_groups[self._client_group_name2]['object']

    def run(self):
        """Run function"""

        try:

            self.client_group_obj1.add_clients([self.client_list[0],
                                                self.client_list[1]])

            self.client_group_obj2.add_clients([self.client_list[2]])

            self.log.info("Started executing testcase")

            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("***Creating one-way topology with display type as Servers***")

            self._network.one_way_topology(self._client_group_name1,
                                           self._client_group_name2,
                                           self.topology_name)

            self._network.push_topology(self.topology_name)

            self._network.options.sleep_time(10)

            self._network.serverbase.restart_services([self.tcinputs['NetworkClient']])

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.validate_one_way_topology(self.topology_name)

            self._network.serverbase.restart_services([self.tcinputs['NetworkMediaAgent']])

            self._network.enable_firewall([self.commserv,
                                           self.tcinputs['NetworkClient'],
                                           self.tcinputs['NetworkMediaAgent']],
                                          [8403, 8403, 8403])

            self._network.validate(
                [self.tcinputs['NetworkClient']], self.tcinputs['NetworkMediaAgent'],
                max_job_time=300)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.delete_topology(self.topology_name)
            self._network.cleanup_network()
            self._network.entities.cleanup()
