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
from Server.Network import networkconstants


class TestCase(CVTestCase):
    """Class for executing basic network case to validate acceptance
        case for two way firewall CS<-->CC

        Setup requirements to run this test case:
        3 clients -- can be combination of windows, mac and unix

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Firewall] : Two Way Firewall - Acceptance validation (win, mac and unix)"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.client_list = []
        self.tcinputs = {
            "FirewallClient2": None,
            "FirewallClient3": None,
            "FirewallClient4": None
        }
        self._client_group_name = networkconstants.CLIENT_GROUP_NAME[2]
        self._cs_client_group = networkconstants.CS_CLIENT_GROUP_NAME[2]

    def setup(self):
        """Setup function of this test case"""
        self.commserv = self.commcell.commserv_name
        self.client_list.extend([self.commserv,
                                 self.tcinputs['FirewallClient2'],
                                 self.tcinputs['FirewallClient3'],
                                 self.tcinputs['FirewallClient4']])

        self._network = NetworkHelper(self)

        self._network.remove_network_config([{'clientName': self.client_list[0]},
                                             {'clientName': self.client_list[1]},
                                             {'clientName': self.client_list[2]},
                                             {'clientName': self.client_list[3]}])

        self._network.entities.create_client_groups([self._client_group_name,
                                                     self._cs_client_group])

        self.client_group_obj = self.commcell.client_groups.get(self._client_group_name)
        self.cs_client_group_obj = self.commcell.client_groups.get(self._cs_client_group)

    def run(self):
        """Run function """

        try:

            # perform check readiness on the input clients before proceeding
            # with further steps
            self._network.serverbase.check_client_readiness(self.client_list)

            self.log.info("Started executing {0} testcase".format(self.id))

            self._network.set_two_way({'clientName': self.tcinputs['FirewallClient2']},
                                      {'clientName': self.commserv})

            self._network.push_config_client([self.commserv,
                                              self.tcinputs['FirewallClient2']])

            self._network.serverbase.check_client_readiness([self.commserv,
                                                             self.tcinputs['FirewallClient2']])

            self.log.info("Adding client {0} to client group".format(
                self.tcinputs['FirewallClient3']))

            self.client_group_obj.add_clients([self.tcinputs['FirewallClient3']])

            self.cs_client_group_obj.add_clients([self.commserv])

            # set two-way firewall between client group and CS
            self._network.set_two_way({'clientGroupName': self._client_group_name},
                                      {'clientName': self.commserv})

            self._network.push_config_clientgroup([self._client_group_name])

            self._network.push_config_client([self.commserv])

            self._network.serverbase.check_client_readiness([self.commserv,
                                                             self.tcinputs['FirewallClient3']])

            self.log.info("Adding client {0} to client group for validating inherited rules"
                          .format(self.tcinputs['FirewallClient4']))

            self.client_group_obj.add_clients([self.tcinputs['FirewallClient4']])

            self._network.options.sleep_time(networkconstants.NEWTWORK_TIMEOUT_SEC)

            self._network.exclude_machine(self.client_list)

            self.log.info("Validating network rules are inherited on client {0}"
                          .format(self.tcinputs['FirewallClient4']))

            self._network.enable_firewall([self.commserv,
                                           self.tcinputs['FirewallClient4'],
                                           self.tcinputs['FirewallClient4']],
                                          [8403, 8403, 8408])

            self._network.serverbase.check_client_readiness([self.commserv,
                                                             self.tcinputs['FirewallClient4']])

            self.log.info("Validating network default options")

            self._network.validate_tunnel_port([{'clientName': self.client_list[0]},
                                                {'clientGroupName': self._client_group_name}])

            self._network.validate_keep_alive([{'clientName': self.client_list[0]},
                                               {'clientGroupName': self._client_group_name}])

            self._network.validate_tunnel_init([{'clientName': self.client_list[0]},
                                                {'clientGroupName': self._client_group_name}])

            self._network.validate_other_defaults([{'clientName': self.client_list[0]},
                                                   {'clientGroupName': self._client_group_name}])

            self.log.info("Completed validation of default options")

            self._network.disable_firewall([self.commserv,
                                            self.tcinputs['FirewallClient4'],
                                            self.tcinputs['FirewallClient4']],
                                           [8403, 8403, 8408])

            self.log.info("Removing client {0} from client group to validate "
                          "if rules are removed".format(self.tcinputs['FirewallClient4']))

            self.client_group_obj.remove_clients([self.tcinputs['FirewallClient4']])

            self._network.options.sleep_time(networkconstants.NEWTWORK_TIMEOUT_SEC)

            self.log.info("Validating network rules are removed from client {0}"
                          .format(self.tcinputs['FirewallClient4']))

            self._network.serverbase.check_client_readiness(
                [self.tcinputs['FirewallClient4']])
            self._network.serverbase.restart_services([self.tcinputs['FirewallClient2'],
                                                       self.tcinputs['FirewallClient3']])

            self._network.enable_firewall([self.commserv,
                                           self.tcinputs['FirewallClient2'],
                                           self.tcinputs['FirewallClient3'],
                                           self.tcinputs['FirewallClient2'],
                                           self.tcinputs['FirewallClient3']],
                                          [8403, 8403, 8403, 8408, 8408])

            self.log.info(
                "Performing check readiness after enabling firewall")

            self._network.serverbase.check_client_readiness(
                [self.client_list[0], self.client_list[1], self.client_list[2]])

            self._network.validate([self.tcinputs['FirewallClient2'],
                                    self.tcinputs['FirewallClient3']], self.commserv)

            self._network.cleanup_network()

            self.log.info("Starting Client group to Client group Validation")

            self._network.exclude_machine(self.client_list)

            self._network.set_two_way({'clientGroupName': self._client_group_name},
                                      {'clientGroupName': self._cs_client_group})

            self._network.push_config_clientgroup([self._client_group_name,
                                                   self._cs_client_group])

            self._network.serverbase.restart_services([self.tcinputs['FirewallClient3']])

            self._network.enable_firewall([self.tcinputs['FirewallClient3'],
                                           self.tcinputs['FirewallClient3'],
                                           self.commserv],
                                          [8403, 8408, 8403])

            self._network.serverbase.check_client_readiness(
                [self.tcinputs['FirewallClient3'], self.commserv])

            self._network.validate([self.tcinputs['FirewallClient3']], self.commserv)

        except Exception as excp:
            self._network.server.fail(excp)

        finally:
            self._network.cleanup_network()
            self._network.entities.cleanup()
