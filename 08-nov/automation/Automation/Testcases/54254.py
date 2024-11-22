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
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing network case to validate Cascading gateways topology

        Setup requirements to run this test case:
        7 clients -- can be any clients in the commcell (windows+unix)

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Cascading gateways topology"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "NetworkClient1": None,
            "NetworkClient2": None,
            "NetworkProxy1": None,
            "NetworkProxy2": None,
            "NetworkProxy3": None,
            "NetworkProxy4": None,
            "NetworkProxy5": None,
        }
        self._client_group_name1 = 'Trusted Client Group1-54254'
        self._client_group_name2 = 'Trusted Client Group2-54254'
        self._client_group_name3 = 'DMZ group near Trusted Client Group1-54254'
        self._client_group_name4 = 'DMZ group near Trusted Client Group2-54254'
        self.commserv = None
        self._network = None
        self.entities = None

        self.topology_name = "Cascading_Gateway_Topology_54254"
        self.client_groups = None
        self.client_group_obj1 = None
        self.client_group_obj2 = None
        self.client_group_obj3 = None
        self.client_group_obj4 = None

    def setup(self):
        """Setup function of this test case"""
        self.commserv = self.commcell.commserv_name
        self._network = NetworkHelper(self)
        self.entities = self._network.entities

        self.client_list.extend([self.commserv,
                                 self.tcinputs['NetworkClient1'],
                                 self.tcinputs['NetworkClient2'],
                                 self.tcinputs['NetworkProxy1'],
                                 self.tcinputs['NetworkProxy2'],
                                 self.tcinputs['NetworkProxy3'],
                                 self.tcinputs['NetworkProxy4'],
                                 self.tcinputs['NetworkProxy5']
                                 ])

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]},
                                             {'clientName': self.client_list[2]},
                                             {'clientName': self.client_list[3]},
                                             {'clientName': self.client_list[4]},
                                             {'clientName': self.client_list[5]},
                                             {'clientName': self.client_list[6]},
                                             {'clientName': self.client_list[7]}
                                             ])

        self._network.push_config_client([self.client_list[0],
                                          self.client_list[1],
                                          self.client_list[2],
                                          self.client_list[3],
                                          self.client_list[4],
                                          self.client_list[5],
                                          self.client_list[6],
                                          self.client_list[7]
                                          ])

        self.client_groups = self._network.entities.create_client_groups([self._client_group_name1,
                                                                          self._client_group_name2,
                                                                          self._client_group_name3,
                                                                          self._client_group_name4])

        self.client_group_obj1 = self.client_groups[self._client_group_name1]['object']
        self.client_group_obj2 = self.client_groups[self._client_group_name2]['object']
        self.client_group_obj3 = self.client_groups[self._client_group_name3]['object']
        self.client_group_obj4 = self.client_groups[self._client_group_name4]['object']

    def run(self):
        """Run function"""

        try:

            self.log.info("Started executing testcase")

            self.client_group_obj1.add_clients([self.client_list[1]])

            self.client_group_obj2.add_clients([self.client_list[2], self.client_list[0]])

            self.client_group_obj3.add_clients([self.client_list[3],
                                                self.client_list[5],
                                                self.client_list[6]])

            self.client_group_obj4.add_clients([self.client_list[4],
                                                self.client_list[7]])

            self._network.set_one_way({'clientName': self.client_list[0]},
                                      {'clientName': self.client_list[4]})

            self._network.set_one_way({'clientName': self.client_list[0]},
                                      {'clientGroupName': self._client_group_name1})

            self._network.topology_pre_settings(self.client_list)

            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("***Creating cascading gateways topology with display type as Servers***")

            self._network.cascading_gateways_topology(self._client_group_name1,
                                                      self._client_group_name2,
                                                      self._client_group_name3,
                                                      self._client_group_name4,
                                                      self.topology_name)

            self._validate()

            self._network.delete_topology(self.topology_name)

            self.log.info("***Creating cascading gateways topology again with display "
                          "type as Laptops***")

            self._network.cascading_gateways_topology(self._client_group_name1,
                                                      self._client_group_name2,
                                                      self._client_group_name3,
                                                      self._client_group_name4,
                                                      self.topology_name,
                                                      display_type=1)

            self._validate()

            self.log.info("*****Setting number of tunnels to 8 on all groups*****")

            cg_obj_list = [self.client_group_obj1,
                          self.client_group_obj2,
                          self.client_group_obj3,
                          self.client_group_obj4]

            for cg_obj in cg_obj_list:
                cg_obj.refresh()
                properties = cg_obj.properties
                for outgoing_routes in properties['firewallConfiguration']['firewallOutGoingRoutes']:
                    if 'numberOfStreams' in outgoing_routes['fireWallOutGoingRouteOptions']:
                        outgoing_routes['fireWallOutGoingRouteOptions']['numberOfStreams'] = 8
                cg_obj.update_properties(properties)

            self.log.info("Number of tunnels set to 8 on all groups")

            clients_summary = self._network.get_network_summary([self.client_list[1],
                                                                 self.client_list[0],
                                                                 self.client_list[3]])

            self.log.info("Verify 8 streams are set for client in each group")
            for client_name, summary in clients_summary.items():
                self.log.info("Summary for Client: {0}".format(client_name))
                self.log.info("Summary: {0}".format(summary))
                if summary.find("streams=8") == -1:
                    raise Exception("Streams for client was not set to 8")

            self._network.push_topology(self.topology_name)
            self._network.options.sleep_time(10)
            self._network.serverbase.check_client_readiness(self.client_list)
            self._network.validate([self.client_list[1]], self.client_list[0], test_data_path="C:\\testData_54254")

            self._network.modify_topology(self.topology_name,
                                          [{'group_type': 2, 'group_name': self._client_group_name1,
                                            'is_mnemonic': False},
                                           {'group_type': 4, 'group_name': self._client_group_name3,
                                            'is_mnemonic': False},
                                           {'group_type': 1, 'group_name': self._client_group_name2,
                                            'is_mnemonic': False},
                                           {'group_type': 3, 'group_name': self._client_group_name4,
                                            'is_mnemonic': False}],
                                          topology_type=4,
                                          is_smart_topology=False, topology_description="Updated topology")

            self._network.delete_topology(self.topology_name)

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            self.status = constants.PASSED
            self._network.server.fail(excp)

        finally:
            self._network.delete_topology(self.topology_name)
            self._network.cleanup_network()
            self._network.entities.cleanup()

    def _validate(self):
        """validation of created topology routes"""
        self._network.push_topology(self.topology_name)

        self._network.options.sleep_time(10)

        self._network.serverbase.check_client_readiness(self.client_list)

        self._network.validate_cascading_gateways_topology(self.topology_name)

        self._network.topology_post_settings()

        self.client_group_obj3.refresh()
        self.client_group_obj4.refresh()

        if not self.client_group_obj3.network.proxy:
            raise Exception("isDMZ option is not set on proxy client group")

        if not self.client_group_obj4.network.proxy:
            raise Exception("isDMZ option is not set on proxy client group")

        if self.client_group_obj3.network.lockdown:
            raise Exception("Lockdown option is set to 1 on proxy client group")

        if self.client_group_obj4.network.lockdown:
            raise Exception("Lockdown option is set to 1 on proxy client group")

        #self._network.validate_fwconfig_file(2, self.client_list[1],
        #                                     self.client_list[3])

        #self._network.validate_fwconfig_file(2, self.client_list[3],
        #                                     self.client_list[4])

        #self._network.validate_fwconfig_file(2, self.client_list[2],
        #                                     self.client_list[4])

        #self._network.validate_fwconfig_file(1, self.client_list[3],
        #                                     self.client_list[4],
        #                                     self.client_list[2])

        #self._network.validate_fwconfig_file(1, self.client_list[1],
        #                                     self.client_list[3],
        #                                     self.client_list[2])

        #self._network.validate_fwconfig_file(1, self.client_list[2],
        #                                     self.client_list[4],
        #                                     self.client_list[1])
