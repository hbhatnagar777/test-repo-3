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
    """Class for executing negative scenario for CV network connectivity with
       OS level firewall turned on

        Setup requirements to run this test case:
        2 clients -- can be combination of windows, mac and unix

        Make sure connectivity with remote client from controller with machine credentials

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Negative scenario] : CV N/W connectivity with OS level firewall turned on"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK

        self.client_list = []
        self.tunnel_ports = []
        self.tcinputs = {
            "FirewallClient1": None,
            "username": None,
            "password": None
            }
        self.fw_client_machine_obj = None
        self._network = None

    def setup(self):
        """Setup function of this test case"""
        self.client_list.extend([self.commcell.commserv_hostname,
                                 self.tcinputs['FirewallClient1']])

        self._network = NetworkHelper(self)

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]}])

        self._network.push_config_client(self.client_list)

    def run(self):
        """Run function """

        try:

            # perform check readiness on the input clients before proceeding
            # with further steps
            self._network.serverbase.check_client_readiness([self.tcinputs['FirewallClient1']])

            self.log.info("Started executing {0} testcase".format(self.id))

            self._network.set_one_way({'clientName': self.client_list[0]},
                                      {'clientName': self.client_list[1]})

            self._network.push_config_client(self.client_list)

            self._network.serverbase.check_client_readiness([self.tcinputs['FirewallClient1']])

            self.log.info("creating machine instance for client %s",
                          self.tcinputs['FirewallClient1'])
            self.fw_client_machine_obj = Machine(machine_name=self.tcinputs['FirewallClient1'],
                                                 username=self.tcinputs['username'],
                                                 password=self.tcinputs['password'])
            self.log.info("starting OS level firewall on client %s",
                          self.tcinputs['FirewallClient1'])
            self.fw_client_machine_obj.start_firewall()
            self.log.info("allowing 60 seconds for firewall to come up")
            time.sleep(60)
            try:
                self._network.serverbase.check_client_readiness([self.tcinputs['FirewallClient1']])
            except Exception as e:
                self.log.error("check readiness failed after turning on os level firewall")
        except Exception as excp:
            self._network.server.fail(excp)
        finally:
            if self.fw_client_machine_obj is not None:
                self.log.info("stopping OS level firewall on client %s",
                              self.tcinputs['FirewallClient1'])
                self.fw_client_machine_obj.stop_firewall()
            self._network.cleanup_network()
            self._network.entities.cleanup()
