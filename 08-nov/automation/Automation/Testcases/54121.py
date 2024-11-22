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

import time
from AutomationUtils.machine import Machine
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase

class TestCase(CVTestCase):
    """
    [Network & Firewall] : Scale test with bad DNS entries
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Scale test with bad DNS entries"
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkProxy": None
        }
        self._network = None
        self.proxy_obj = None
        self.proxy_machine = None
        self.option_selector = None
        self.query = None
        self.client_hostname = None
        self.client = None
        self.proxy = None
        self.cs = None
        self.original_content = ""
        self.overload_content = ""
        self.path = ""

    def setup(self):
        """Setup function of this test case"""
        self.log.info(f"[+] Creating client & helper objects [+]")
        self._network = NetworkHelper(self)
        self.client = self.tcinputs["NetworkClient"]
        self.proxy = self.tcinputs["NetworkProxy"]
        self.cs = self.commcell.commserv_name
        self.proxy_obj = self.commcell.clients.get(self.proxy)
        self.proxy_machine = Machine(self.proxy_obj)
        self.option_selector = OptionsSelector(self.commcell)
        self._network.remove_network_config(
            [
                {'clientName': self.client},
                {'clientName': self.proxy},
                {'clientName': self.cs}
            ]
        )
        self.path = self.proxy_obj.install_directory + "\\Base\\FwConfigLocal.txt"
        self.original_content = self.proxy_machine.read_file(self.path)

    def run(self):
        try:
            self.log.info("[+] Creating client groups and adding clients [+]")
            self.commcell.client_groups.add(
                "Internal_CG", [self.client])
            self.commcell.client_groups.add(
                "Proxy_CG", [self.proxy])
            self.commcell.client_groups.add("External_CG", [self.cs])

            self.log.info("[+] Creating one way forwarding topology [+]")
            self._network.topologies.add(
                "OneWay_Forwarding_Topology", [
                    {'group_type': 1, 'group_name': "External_CG",
                     'is_mnemonic': False},
                    {'group_type': 2, 'group_name': "Internal_CG",
                     'is_mnemonic': False},
                    {'group_type': 3, 'group_name': "Proxy_CG", 'is_mnemonic': False}
                ],
                topology_type=5,
                topology_description="This is a test for validating One-way firewall topology."
            )
            self.log.info(f"[+] Performing check readiness on {self.proxy} [+]")
            self._network.serverbase.check_client_readiness([self.proxy])

            self.log.info("[+] Adding invalid passive routes on proxy [+]")
            self.overload_content = "[outgoing]\n"
            for i in range(100):
                self.overload_content += f"{self.proxy} c{i} remote_guid=7575DAEC-F7D7-48CE-AD8D-0000000000{i:02d} type=passive\n"

            self.proxy_machine.create_file(self.path, self.overload_content)
            time.sleep(30)

            self.commcell.refresh()
            self.log.info(f"[+] Performing check readiness on {self.proxy} [+]")
            self._network.serverbase.check_client_readiness([self.proxy, self.client])
            self.log.info("[+] >> SUCCESSFUL << [+]")

        except Exception as e:
            self.log.info(f"[+] failed with error: {str(e)} [+]")

        finally:
            self.proxy_machine.create_file(self.path, self.original_content)
            self.commcell.client_groups.delete('Internal_CG')
            self.commcell.client_groups.delete('Proxy_CG')
            self.commcell.client_groups.delete('External_CG')
            self._network.cleanup_network()
