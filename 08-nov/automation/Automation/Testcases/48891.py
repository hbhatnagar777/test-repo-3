# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
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
    """Class for executing basic network case to validate
    Backward Compatibility - One Way Firewall CS->CC - Acceptance validation

        Setup requirements to run this test case:
        3 clients (mix of v9/v10/v11) -- can be combination of windows, mac and unix

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("[Firewall] : Backward Compatibility - "
                     "One Way Firewall CS->CC - Acceptance validation")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "NetworkClientv9": None,
            "NetworkClientv10": None,
            "NetworkClientv11": None
        }
        self._client_group_name = "CG_48891_CL"
        self._cs_client_group = "CG_48891_CS"
        self.commserv = None
        self._network = None
        self.client_group_obj = None
        self.topology_name = "TOPOLOGY_48891"
        self.client_groups = None
        self.client_group_obj1 = None
        self.client_group_obj2 = None

    def setup(self):
        """Setup function of this test case"""

        self.commserv = self.commcell.commserv_name

        self.client_list.extend([self.commserv,
                                 self.tcinputs['NetworkClientv9'],
                                 self.tcinputs['NetworkClientv10'],
                                 self.tcinputs['NetworkClientv11']])

        self._network = NetworkHelper(self)

        self.client_groups = self._network.entities.create_client_groups([self._client_group_name,
                                                                          self._cs_client_group])

        self.client_group_obj1 = self.client_groups[self._client_group_name]['object']
        self.client_group_obj2 = self.client_groups[self._cs_client_group]['object']

    def run(self):
        """Run function """

        try:
            self.client_group_obj1.add_clients([self.client_list[1],
                                                self.client_list[2],
                                                self.client_list[3]])

            self.client_group_obj2.add_clients([self.client_list[0]])

            self.log.info("Started executing testcase")

            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("***Creating one-way topology from CS-->Clients***")

            self._network.one_way_topology(self._cs_client_group,
                                           self._client_group_name,
                                           self.topology_name)

            self._network.serverbase.restart_services([self.tcinputs['NetworkClientv10'],
                                                       self.tcinputs['NetworkClientv11']])

            self._network.push_topology(self.topology_name)

            self._network.options.sleep_time(10)

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.validate([self.tcinputs['NetworkClientv10']],
                                             self.commserv)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.delete_topology(self.topology_name)
            self._network.cleanup_network()
            self._network.entities.cleanup()
