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
    """Class for executing network case to validate same client group in multiple network topologies

        Setup requirements to run this test case:
        3 clients -- can be any client in the commcell

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("[Network & Firewall] : Allowing same group to be used in "
                     "multiple topologies (proxy topology)")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "NetworkClient1": None,
            "NetworkClient2": None,
            "NetworkClient3": None
        }
        self._client_group_name1 = 'CG1_54018'
        self._client_group_name2 = 'CG2_54018'
        self._client_group_name3 = 'CG3_54018'
        self._client_group_name4 = 'CG4_54018'
        self._client_group_name5 = 'CG5_54018'
        self.commserv = None
        self._network = None
        self.topology_name1 = "TOPOLOGY1_54018"
        self.topology_name2 = "TOPOLOGY2_54018"
        self.client_groups = None
        self.client_group_obj1 = None
        self.client_group_obj2 = None
        self.client_group_obj3 = None
        self.client_group_obj4 = None
        self.client_group_obj5 = None

    def setup(self):
        """Setup function of this test case"""
        self.commserv = self.commcell.commserv_name

        self.client_list.extend([self.commserv,
                                 self.tcinputs['NetworkClient1'],
                                 self.tcinputs['NetworkClient2'],
                                 self.tcinputs['NetworkClient3']])

        self._network = NetworkHelper(self)

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]},
                                             {'clientName': self.client_list[2]},
                                             {'clientName': self.client_list[3]}])

        self._network.push_config_client([self.client_list[0],
                                          self.client_list[1],
                                          self.client_list[2],
                                          self.client_list[3]])

        self.client_groups = self._network.entities.create_client_groups([self._client_group_name1,
                                                                          self._client_group_name2,
                                                                          self._client_group_name3,
                                                                          self._client_group_name4,
                                                                          self._client_group_name5])

        self.client_group_obj1 = self.client_groups[self._client_group_name1]['object']
        self.client_group_obj2 = self.client_groups[self._client_group_name2]['object']
        self.client_group_obj3 = self.client_groups[self._client_group_name3]['object']
        self.client_group_obj4 = self.client_groups[self._client_group_name4]['object']
        self.client_group_obj5 = self.client_groups[self._client_group_name5]['object']

    def run(self):
        """Run function"""

        try:

            self.client_group_obj1.add_clients([self.client_list[1]])

            self.client_group_obj2.add_clients([self.client_list[2]])

            self.client_group_obj3.add_clients([self.client_list[3]])

            self._network.topology_pre_settings(self.client_list)

            self.log.info("Started executing testcase")

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.proxy_topology(self._client_group_name1,
                                         self._client_group_name2,
                                         self._client_group_name3,
                                         self.topology_name1)

            self._network.push_topology(self.topology_name1)

            self._network.options.sleep_time(10)

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.validate_proxy_topology(self.topology_name1)

            #self._network.validate_fwconfig_file(1, self.client_list[1],
            #                                     self.client_list[3],
            #                                     self.client_list[2])
            #self._network.validate_fwconfig_file(1, self.client_list[2],
            #                                     self.client_list[3],
            #                                     self.client_list[1])

            self._network.proxy_topology(self._client_group_name1,
                                         self._client_group_name5,
                                         self._client_group_name4,
                                         self.topology_name2)

            self.log.info("Modifying topology1 and enabling wildcard proxy option")

            self._network.modify_topology(self.topology_name1,
                                          description="Modifying topology description",
                                          wildcard_proxy=True)

            self._network.push_topology(self.topology_name1)

            #self._network.validate_fwconfig_file(1, self.client_list[1],
            #                                     self.client_list[3],
            #                                     self.client_list[2],
            #                                     wildcard=1)

            self._network.topology_post_settings()

            self.log.info("Validating wild card proxy option is set on the topologies")

            if not self._network.get_wildcard_proxy(self.topology_name1):
                raise Exception("Wildcard proxy option was not set on first topology")

            if not self._network.get_wildcard_proxy(self.topology_name2):
                raise Exception("Wildcard proxy option was not automatically set on "
                                "second topology having the same group")

            self.log.info("Changing first client group of topology1")

            self._network.modify_topology(self.topology_name1,
                                          firewall_groups=[{'group_type': 2,
                                                            'group_name': self._client_group_name4,
                                                            'is_mnemonic': False},
                                                           {'group_type': 1,
                                                            'group_name': self._client_group_name2,
                                                            'is_mnemonic': False},
                                                           {'group_type': 3,
                                                            'group_name': self._client_group_name3,
                                                            'is_mnemonic': False}],
                                          description="Modifying topology description")

            self.log.info("Verifying wildcard proxy option on topologies")

            if self._network.get_wildcard_proxy(self.topology_name1):
                raise Exception("Wildcard proxy option was not reset on first topology with change "
                                "in client group")

            if not self._network.get_wildcard_proxy(self.topology_name2):
                raise Exception("Wildcard proxy option was removed on second"
                                "topology without modification on it's client group")

            self.log.info("Changing proxy client group for topology2")

            self._network.modify_topology(self.topology_name2,
                                          firewall_groups=[{'group_type': 2,
                                                            'group_name': self._client_group_name1,
                                                            'is_mnemonic': False},
                                                           {'group_type': 1,
                                                            'group_name': self._client_group_name5,
                                                            'is_mnemonic': False},
                                                           {'group_type': 3,
                                                            'group_name': self._client_group_name3,
                                                            'is_mnemonic': False}],
                                          description="Modifying topology description",
                                          wildcard_proxy=True)

            self.log.info("Validating isDMZ option is set on the proxy client group")

            self.client_group_obj3.refresh()

            if not self.client_group_obj3.network.proxy:
                raise Exception("isDMZ option is not set on proxy client group")

            self._network.delete_topology(self.topology_name2)

            self._network.topology_post_settings()

            self.log.info("Validating isDMZ option is retained on the client group after "
                          "deletion of one of the topologies since client group is a part "
                          "of another proxy topology")

            self.client_group_obj3.refresh()

            if not self.client_group_obj3.network.proxy:
                raise Exception("isDMZ option was reset on the proxy client group "
                                "after deletion of one of the topologies")

            self._network.topology_post_settings()

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.delete_topology(self.topology_name1)
            self._network.delete_topology(self.topology_name2)
            self._network.cleanup_network()
            self._network.entities.cleanup()
