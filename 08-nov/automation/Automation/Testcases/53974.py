# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

"""Main file for executing this test case

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
    """Class for executing basic network throttle functionality

        Setup requirements to run this test case:
        3 clients -- can be any client in the commcell
        NetworkClient1 should have media agent package installed

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("[Network & Firewall] : Validation for basic "
                     "throttling functionality")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "NetworkClient1": None,
            "NetworkClient2": None,
            "NetworkClient3": None
        }
        self.commserv = None
        self._network = None
        self._client_group_name = 'CG_53974'
        self.client_group_obj = None
        self.client_groups = None

    def setup(self):
        """Setup function of this test case"""

        self.client_list.extend([self.tcinputs['NetworkClient1'],
                                 self.tcinputs['NetworkClient2'],
                                 self.tcinputs['NetworkClient3']])

        self._network = NetworkHelper(self)

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]},
                                             {'clientName': self.client_list[2]}])

        self._network.push_config_client([self.client_list[0],
                                          self.client_list[1],
                                          self.client_list[2]])

        self.client_groups = self._network.entities.create_client_groups([self._client_group_name])

        self.client_group_obj = self.client_groups[self._client_group_name]['object']

    def run(self):
        """Run function"""

        try:

            self.log.info("Started executing testcase")

            self.client_group_obj.add_clients([self.client_list[2]])
            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("Setting Absolute Network Throttling")

            self._network.set_network_throttle({'clientName': self.client_list[0]},
                                               remote_clients=[self.client_list[1]],
                                               remote_clientgroups=[self._client_group_name],
                                               throttle_rules=[{"sendRate": 102400,
                                                                "sendEnabled": True,
                                                                "receiveEnabled": True,
                                                                "recvRate": 102400,
                                                                "days": '1111111',
                                                                "isAbsolute": True}])

            self._network.push_config_client([self.client_list[0],
                                              self.client_list[1],
                                              self.client_list[2]])

            self._network.serverbase.restart_services([self.tcinputs['NetworkClient1'],
                                                       self.tcinputs['NetworkClient2'],
                                                       self.tcinputs['NetworkClient3']])

            #self._network.validate_fwconfig_file(0, self.client_list[0], self.client_list[1])

            #self._network.validate_fwconfig_file(0, self.client_list[0], self.client_list[2])

            self._network.validate_throttle_schedules(self.client_list[0])

            self._network.validate([self.client_list[1], self.client_list[2]],
                                   self.client_list[0],
                                   test_data_level=2,
                                   test_data_size=20000)

            self._network.remove_network_throttle([{'clientGroupName': self._client_group_name},
                                                   {'clientName': self.client_list[0]},
                                                   {'clientName': self.client_list[1]}])

            self._network.push_config_client([self.client_list[0],
                                              self.client_list[1],
                                              self.client_list[2]])

            self.log.info("Setting Relative Network Throttling")

            self._network.set_network_throttle({'clientName': self.client_list[0]},
                                               remote_clients=[self.client_list[1]],
                                               remote_clientgroups=[self._client_group_name],
                                               throttle_rules=[{"sendRate": 102400,
                                                                "sendEnabled": True,
                                                                "receiveEnabled": True,
                                                                "recvRate": 102400,
                                                                "days": '1111111',
                                                                "isAbsolute": False,
                                                                "sendRatePercent": 40,
                                                                "recvRatePercent": 40}])

            self._network.push_config_client([self.client_list[0],
                                              self.client_list[1],
                                              self.client_list[2]])

            self._network.serverbase.restart_services([self.tcinputs['NetworkClient1'],
                                                       self.tcinputs['NetworkClient2'],
                                                       self.tcinputs['NetworkClient3']])

            #self._network.validate_fwconfig_file(0, self.client_list[0], self.client_list[1])

            #self._network.validate_fwconfig_file(0, self.client_list[0], self.client_list[2])

            self._network.validate_throttle_schedules(self.client_list[0])

            self._network.validate([self.client_list[1], self.client_list[2]],
                                   self.client_list[0],
                                   test_data_level=2,
                                   test_data_size=20000)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.remove_network_throttle([{'clientGroupName': self._client_group_name},
                                                   {'clientName': self.client_list[0]},
                                                   {'clientName': self.client_list[1]}])
            self._network.cleanup_network()
            self._network.entities.cleanup()
            self._network.push_config_client([self.client_list[0],
                                              self.client_list[1],
                                              self.client_list[2]])
