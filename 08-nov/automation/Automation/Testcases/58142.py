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
from AutomationUtils.machine import Machine

import time


class TestCase(CVTestCase):
    """Class for executing basic network case to validate n/w connectivity
                     with tunnel port already used"

        Setup requirements to run this test case:
        1 window client
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("[Negative scenario] : validation of n/w connectivity"
                     " with tunnel port already used")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK

        self.client_list = []
        self.tunnel_ports = []
        self.tcinputs = {
            "FirewallClient1": None,
            "tunnelport1": None,
            }

    def setup(self):
        """Setup function of this test case"""
        self.client_list.extend([self.commcell.commserv_hostname,
                                 self.tcinputs['FirewallClient1']])

        self.tunnel_ports.extend([9999, self.tcinputs['tunnelport1']])

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
            self.log.info("creating machine instance for client")
            machine_obj = Machine(self.client_list[1], self.commcell)
            client_obj = self.commcell.clients.get(self.client_list[1])

            cvfwd_log_file = machine_obj.join_path(client_obj.log_directory, "cvfwd.log")

            self.log.info("Started executing {0} testcase".format(self.id))
            self._network.set_tunnelport([{'clientName': self.client_list[0]},
                                          {'clientName': self.client_list[1]}],
                                         self.tunnel_ports)

            self._network.set_one_way({'clientName': self.client_list[0]},
                                      {'clientName': self.client_list[1]})

            self._network.push_config_client(self.client_list)

            self.log.info("allowing some time after one way firewall")
            time.sleep(60)

            expected_pattern = "IPv4 port {0} is in use".format(self.tcinputs['tunnelport1'])
            self.log.info("reading cvd log file %s", cvfwd_log_file)
            matched_lines = machine_obj.read_file(cvfwd_log_file, search_term=expected_pattern)
            if matched_lines:
                self.log.info("expected error found in cvfwd log on client")
            else:
                self.log.error("expected error was not found in cvfwd log. Expected pattern:%s",
                                expected_pattern)

            try:
                self._network.serverbase.check_client_readiness([self.tcinputs['FirewallClient1']])
            except Exception as e:
                raise Exception("check readiness failed. fall back tunnel port may not be used")

            self.log.info("check readiness passed with fall back tunnel port as expected.")

        except Exception as excp:
            self._network.server.fail(excp)
        finally:
            self._network.cleanup_network()
            self._network.entities.cleanup()
