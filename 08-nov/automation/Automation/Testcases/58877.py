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
    setup()         --  setup function of this test casesiletn
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case

    Test Case:
            This test case verifies interactive install of a client with one-way network route from client to CS

    Instructions:
            Inputs:
                "install_client_hostname": hostname of the client where install has to take place,
                "install_client_username": Username of the target client,
                "install_client_password": Password of the target client,

                "commserveHostname": Hostname of the CS,
                "commservePassword": Password of the CS,
                "commserveUsername": Username of the CS,

                "portNumber":  tunnel port
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.clientgroup import ClientGroups
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.machine import Machine
from Install.install_helper import InstallHelper
from datetime import datetime


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)   -   name of this test case

                applicable_os       (str)   —   applicable os for this test case
                                                            Ex: self.os_list.WINDOWS
                product             (str)   —   applicable product for this test case
                                                                 Ex: self.products_list.FILESYSTEM
                features            (str)   —   qcconstants feature_list item
                                                             Ex: self.features_list.DATAPROTECTION
                show_to_user       (bool)   —   test case flag to determine if the test case is
                                                             to be shown to user or not
                Accept:
                                    True    –   test case will be shown to user from commcell gui
                                    False   –   test case will not be shown to user
                default: False

                tcinputs            (dict)  -   test case inputs with input name as dict key
                                                    and value as input type
        """
        try :
            super(TestCase, self).__init__()
            self.name = "[Network & Firewall] : Interactive install of a client with one-way network route from client to CS"
            self.applicable_os = self.os_list.WINDOWS
            self.product = self.products_list.COMMSERVER
            self.show_to_user = True
            self.tcinputs = {
                "install_client_hostname": None,
                "install_client_username": None,
                "install_client_password": None,

                "commserveHostname": None,
                "commservePassword": None,
                "commserveUsername": None,

            }

            self.windows_client_name = "client_58877_" + str(datetime.now().microsecond)
            self.dummy_host_name = None
            self.clientgrp = None

            # Helper objects
            self.network_helper = None
            self.windows_machine = None
            self.windows_install_helper = None
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()


    def setup(self):
        """Setup function of this test case"""
        try:
            self.windows_machine = Machine(
                machine_name=self.tcinputs["install_client_hostname"],
                username=self.tcinputs["install_client_username"],
                password=self.tcinputs["install_client_password"])
            self.windows_install_helper = InstallHelper(self.commcell, self.windows_machine)
            self.commserv = self.commcell.commserv_name
            self.network_helper = NetworkHelper(self)

            self.clientgrp = "ClientGrp_58877"
            self.commserve = self.tcinputs['commserveHostname']

            self.clientgrp = "clientgrp_58877"

            self.tcinputs["force_ipv4"] = "1"
            self.tcinputs["firewallConnectionType"] = "2"
            self.tcinputs["networkGateway"] = self.tcinputs["commserveHostname"]
            self.tcinputs["firewallConnectionType"] = 2
            self.tcinputs["httpProxyConfigurationType"] = 0
            self.tcinputs["enableFirewallConfig"] = "1"
            self.tcinputs["showFirewallConfigDialogs"] = "1"
            self.tcinputs["enableProxyClient"] = "1"
            self.tcinputs["proxyHostname"] = self.tcinputs["commserveHostname"]
            self.tcinputs["proxyPortNumber"] = self.tcinputs.get("portNumber", "8403")
            self.network_helper.remove_network_config([{'clientName': self.commserv}])

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()

    def run(self):

        try:
            self.log.info("Inside run function")

            self.log.info("Step 1: Enable firewall on client")
            self.windows_machine.start_firewall()

            self.log.info("Step 2: Enable firewall on CS and add inbound rule")
            self.network_helper.enable_firewall([self.commserv], [self.tcinputs.get("portNumber", "8403")])

            self.log.info("Step 3: Perform silent install")
            fr = 'SP' + self.commcell.version.split('.')[1]

            self.windows_install_helper.silent_install(client_name=self.windows_client_name,
                                                       tcinputs=self.tcinputs,
                                                       feature_release=fr)

            self.log.info("Step 4: Check client entry")
            self.commcell.refresh()
            if self.commcell.clients.has_client(self.windows_client_name):
                self.log.info("Verified client added")
            else :
                raise Exception("Client could not be created")

            self.log.info("Step 5 : Create Clientgroup with one-way network route from CG to CS")
            self.commcell.refresh()
            self.commcell.client_groups.add(self.clientgrp, [self.windows_client_name])
            self.network_helper.set_one_way({"clientName": self.commserv}, {"clientGroupName": self.clientgrp})
            self.network_helper.push_config_clientgroup([self.clientgrp])

            self.log.info("Step 6: Verify push config")
            summary = self.network_helper.get_network_summary([self.windows_client_name])
            if summary[self.windows_client_name].find("type=persistent") == -1:
                raise Exception("Incorrect Network Summary")
            else:
                self.log.info("Network Summary verified")

            self.log.info("Step 7: Verify Check Readines")
            self.commcell.refresh()
            self.network_helper.serverbase.check_client_readiness([self.windows_client_name])

        except Exception as exp:
                self.log.error('Failed to execute test case with error: %s', exp)
                self.result_string = str(exp)
                self.status = constants.FAILED
                self.tear_down()

    def tear_down(self):
        """Tear down function of this test case"""

        self.log.info("Deleting client group")
        self.network_helper.cleanup_network()
        if self.commcell.client_groups.has_clientgroup(self.clientgrp):
            self.commcell.client_groups.delete(self.clientgrp)
        if self.windows_machine is not None:
            self.windows_machine.stop_firewall()
        self.windows_install_helper.uninstall_client()