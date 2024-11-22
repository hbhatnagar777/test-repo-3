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
        3 clients -- can be any clients in the commcell

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("[Network & Firewall] : Allowing same group to be used "
                     "in multiple topologies")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "NetworkClient1": None,
            "NetworkClient2": None,
            "NetworkClient3": None,
            "NetworkClient4": None
        }
        self._client_group_name1 = 'CG1_54017'
        self._client_group_name2 = 'CG2_54017'
        self._client_group_name3 = 'CG3_54017'
        self._client_group_name4 = 'CG4_54017'
        self._client_group_name5 = 'CG5_54017'
        self.commserv = None
        self._network = None
        self.topology_name1 = "TOPOLOGY1_54017"
        self.topology_name2 = "TOPOLOGY2_54017"

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
                                 self.tcinputs['NetworkClient3'],
                                 self.tcinputs['NetworkClient4']])

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

            self.client_group_obj1.add_clients([self.client_list[0]])

            self.client_group_obj2.add_clients([self.client_list[1]])

            self.client_group_obj3.add_clients([self.client_list[2]])

            self.client_group_obj4.add_clients([self.client_list[3]])

            self.client_group_obj5.add_clients([self.client_list[4]])

            self.log.info("Started executing testcase")

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.set_one_way({'clientName': self.commserv},
                                      {'clientName': self.tcinputs['NetworkClient4']})

            self._network.set_one_way({'clientName': self.commserv},
                                      {'clientGroupName': self._client_group_name5})

            self._network.topology_pre_settings(self.client_list)

            self.log.info("***Creating one-way topology with display type as Servers***")

            self._network.one_way_topology(self._client_group_name1,
                                           self._client_group_name2,
                                           self.topology_name1)

            self._network.push_topology(self.topology_name1)

            self.log.info("***Creating two-way topology***")

            self._network.two_way_topology(self._client_group_name3,
                                           self._client_group_name4,
                                           self.topology_name2)

            self._network.push_topology(self.topology_name2)

            self._network.options.sleep_time(10)

            self._network.serverbase.check_client_readiness(self.client_list)

            self._network.validate_one_way_topology(self.topology_name1)

            self._network.validate_two_way_topology(self.topology_name2)

            #self._network.validate_fwconfig_file(2, self.client_list[0], self.client_list[1])

            #self._network.validate_fwconfig_file(3, self.client_list[2], self.client_list[3])

            self._network.topology_post_settings()

            self.log.info("Modifying one-way topology by changing first client group")

            self._network.modify_topology(self.topology_name1,
                                          firewall_groups=[{'group_type': 2,
                                                            'group_name': self._client_group_name3,
                                                            'is_mnemonic': False},
                                                           {'group_type': 1,
                                                            'group_name': self._client_group_name2,
                                                            'is_mnemonic': False}],
                                          description="Modifying topology description")

            self._network.push_topology(self.topology_name1)

            self._network.topology_post_settings()

            #self._network.validate_fwconfig_file(2, self.client_list[2], self.client_list[1])

            #self._network.validate_fwconfig_file(3, self.client_list[2], self.client_list[3])

            self._network.topology_post_settings()

            self.client_group_obj1.refresh()

            if self.client_group_obj1.network.configure_network_settings is True:
                raise Exception("Group1 has network route settings enabled after removing "
                                "from topology though it is not a part of any other topology")

            self.log.info("Modifying second topology by changing client group")

            self._network.modify_topology(self.topology_name2,
                                          firewall_groups=[{'group_type': 2,
                                                            'group_name': self._client_group_name1,
                                                            'is_mnemonic': False},
                                                           {'group_type': 1,
                                                            'group_name': self._client_group_name4,
                                                            'is_mnemonic': False}],
                                          description="Modifying topology description")

            self._network.push_topology(self.topology_name2)

            self.client_group_obj3.refresh()

            if self.client_group_obj3.network.configure_network_settings is False:
                raise Exception("Group3 has network route settings disabled though "
                                "it's a part of other topology")

            self.log.info("Reverting back changes on second topology")

            self._network.modify_topology(self.topology_name2,
                                          firewall_groups=[{'group_type': 2,
                                                            'group_name': self._client_group_name3,
                                                            'is_mnemonic': False},
                                                           {'group_type': 1,
                                                            'group_name': self._client_group_name4,
                                                            'is_mnemonic': False}],
                                          description="Modifying topology description")

            self.log.info("Deleting second topology")

            self._network.delete_topology(self.topology_name2)

            self.client_group_obj3.refresh()

            if self.client_group_obj3.network.configure_network_settings is False:
                raise Exception("Group3 has network route settings disabled after "
                                "deleting topology though it's a part of another topology")

            self.client_group_obj4.refresh()

            if self.client_group_obj4.network.configure_network_settings is True:
                raise Exception("Group4 has network route settings enabled after "
                                "deleting topology though it's not a part of another topology")

            self.log.info("Creating a new topology using client group which is a part "
                          "of an existing topology")

            self._network.one_way_topology(self._client_group_name4,
                                           self._client_group_name3,
                                           self.topology_name2)

            self._network.push_topology(self.topology_name2)

            #self._network.validate_fwconfig_file(2, self.client_list[2], self.client_list[1])

            #self._network.validate_fwconfig_file(2, self.client_list[3], self.client_list[2])

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.delete_topology(self.topology_name1)
            self._network.delete_topology(self.topology_name2)
            self._network.cleanup_network()
            self._network.entities.cleanup()
