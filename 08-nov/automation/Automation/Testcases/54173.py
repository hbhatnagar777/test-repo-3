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
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case

    Test Case:
        [Network & Firewall] : Routes generation validation after the hard deleting a proxy

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.clientgroup import ClientGroups
from Server.Network.networkhelper import NetworkHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)       -   name of this test case
                applicable_os       (str)       —   applicable os for this test case
                                                            Ex: self.os_list.WINDOWS
                 product            (str)       —   applicable product for this test case
                                                                 Ex: self.products_list.FILESYSTEM
                features            (str)       —   qcconstants feature_list item
                                                             Ex: self.features_list.DATAPROTECTION
                show_to_user        (bool)      —   test case flag to determine if the test case is
                                                             to be shown to user or not
                Accept:
                                       True     –   test case will be shown to user from commcell gui
                                       False    –   test case will not be shown to user
                default: False
                tcinputs            (dict)      -   test case inputs with input name as dict key
                                                    and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Routes generation validation after the hard deleting a proxy"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
        }

        self.network_helper = None
        self.client_grp_map = None

        # Clients
        self.pseudoclient1 = "pseudoclient1"
        self.pseudoclient2 = "pseudoclient2"
        self.proxyclient = "proxyclient"
        self.client_names_list = [self.pseudoclient1, self.pseudoclient2,
                                  self.proxyclient]
        # Client Groups
        self.clientgrp1 = 'clientgrp1'
        self.clientgrp2 = 'clientgrp2'
        self.proxygrp = 'proxygrp'
        self.client_grp_list = [self.clientgrp1, self.clientgrp2, self.proxygrp]

        self.network_topology_name = "Test_topology_54173"

    def setup(self):
        """Setup function of this test case"""
        try:
            self.network_helper = NetworkHelper(self)
            self.clients_obj = self.commcell.clients

            # Create pseudo clients for the test case
            self.log.info("Creating pseudo clients for test case")
            for client_name in self.client_names_list:
                self.clients_obj.create_pseudo_client(client_name)

            # Create Client groups
            # Client grp list
            self.clients_grps_obj = self.commcell.client_groups
            for client_grp, client_name in zip(self.client_grp_list, self.client_names_list):
                self.log.info('Creating client group: {0} with client: {1}'.format(client_grp, client_name))
                self.clients_grps_obj.add(client_grp, clients=[client_name])

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()

    def run(self):
        """Run function of this test case"""
        self.log.info("Started executing testcase 54173")
        try:
            # Create network topology with proxy
            self.log.info("Creating network topology: {}".format(self.network_topology_name))
            self.network_helper.proxy_topology(*self.client_grp_list, topology_name=self.network_topology_name)

            # Push Configuration
            self.network_helper.push_config_clientgroup(self.client_grp_list)

            # Hard Delete Proxy client
            self.commcell.clients.delete(self.proxyclient)
            self.log.info("Proxy client: {} deleted".format(self.proxyclient))
            self.client_names_list.remove(self.proxyclient)

            # Push Configuration to other two groups after removing proxy client
            self.network_helper.push_config_clientgroup(self.client_grp_list[:2])

            # Get network summary and Check
            changed_client_summary = self.network_helper.get_network_summary(self.client_names_list)
            if not changed_client_summary[self.pseudoclient1] or not changed_client_summary[self.pseudoclient2]:
                raise Exception('Network Summary Empty')

            if self.proxyclient in changed_client_summary[self.pseudoclient1] or self.proxyclient in \
                    changed_client_summary[self.pseudoclient2]:
                raise Exception('Network Summary unchanged after removing proxy')

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""

        self.log.info("Deleting clients")
        for client_name in self.client_names_list:
            if self.commcell.clients.has_client(client_name):
                self.commcell.clients.delete(client_name)

        if self.network_helper is not None:
            # Delete topology
            self.network_helper.delete_topology(self.network_topology_name)
            self.network_helper.cleanup_network()

        self.log.info("Deleting client groups")
        for client_group in self.client_grp_list:
            if self.clients_grps_obj.has_clientgroup(client_group):
                self.clients_grps_obj.delete(client_group)

        if self.network_helper.entities is not None:
            self.network_helper.entities.cleanup()
