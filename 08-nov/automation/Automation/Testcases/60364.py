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
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Install.install_helper import InstallHelper
from Server.Network.networkhelper import NetworkHelper


class TestCase(CVTestCase):
    """
    [Network & Firewall] : Automate upgrade test case for CS with name 'commcell'
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Automate upgrade test case for CS with name 'CommCell'"
        self.product = self.products_list.COMMSERVER
        self.tcinputs = {
            "csMachineHostName": None,
            "csMachineUsername": None,
            "csMachinePassword": None,

            "clientMachineName": None,
            "clientMachineUsername": None,
            "clientMachinePassword": None
        }
        self.client_install_helper = None
        self.commserve_install_helper = None
        self.commserve_machine = None
        self.client_machine = None
        self.network_helper = None

    def setup(self):
        self.log.info("[+] Creating machine & helper objects [+]")
        self.commserve_machine = Machine(
            machine_name=self.tcinputs["csMachineHostName"],
            username=self.tcinputs["csMachineUsername"],
            password=self.tcinputs["csMachinePassword"])
        self.commserve_install_helper = InstallHelper(self.commcell, self.commserve_machine)

        self.client_machine = Machine(
            machine_name=self.tcinputs["clientMachineName"],
            username=self.tcinputs["clientMachineUsername"],
            password=self.tcinputs["clientMachinePassword"])
        self.client_install_helper = InstallHelper(self.commcell, self.client_machine)

        self.tcinputs["force_ipv4"] = "1"
        self.tcinputs["csClientName"] = "CommCell"
        self.tcinputs["commserveUsername"] = "admin"
        self.tcinputs["csHostname"] = self.tcinputs["csMachineHostName"]
        self.tcinputs["instance"] = "Instance001"

    def run(self):
        try:
            self.log.info("[+] Installing SP20 Commserve [+]")
            self.commserve_install_helper.install_commserve(
                install_inputs=self.tcinputs,
                feature_release='SP20'
            )

            self.log.info("[+] Turning off the firewall if turned ON [+]")
            self.commserve_machine.stop_firewall()
            time.sleep(180)

            self.log.info("[+] Installing SP20 Client [+]")
            try:
                self.commcell = Commcell(self.tcinputs["csMachineHostName"], 'admin', "#####")
            except:
                self.commcell = Commcell(self.tcinputs["csMachineHostName"] + ":83", 'admin', "#####")
            self.tcinputs["authCode"] = self.commcell.enable_auth_code()
            self.client_install_helper.silent_install(
                "Test_60364", self.tcinputs, feature_release='SP20'
            )
            time.sleep(180)

            self.commcell.refresh()
            if self.commcell.clients.has_client('Test_60364'):
                self.log.info("Verified client added")
            else:
                raise Exception("Client is not showing in commcell")

            self.network_helper = NetworkHelper(self)
            self.log.info("[+] Performing CCR on client & commserve [+]")
            self.network_helper.serverbase.check_client_readiness(
                ['Test_60364', 'CommCell']
            )

            self.log.info("[+] Upgrading SP20 commserve to SP24 [+]")
            self.commserve_install_helper.install_commserve(
                install_inputs=self.tcinputs,
                feature_release='SP24'
            )

            self.log.info("[+] Upgrading SP20 client to SP24 [+]")
            self.client_install_helper.silent_install(
                "Test_60364", self.tcinputs, feature_release='SP24'
            )

            self.log.info("[+] Performing CCR on client & commserve [+]")
            self.network_helper.serverbase.check_client_readiness(
                ['Test_60364', 'CommCell']
            )

            self.log.info("[+] Running backup & restore job [+]")
            self.network_helper.validate(['Test_60364'], 'CommCell')

            self.log.info("[+] Checking cvd log for built-in certificate [+]")
            self.commserve_machine = Machine(self.commcell.clients.get("CommCell"))
            found = self.commserve_machine.check_if_pattern_exists_in_log(
                        "Only built-in certificate loaded", "CVD.log")
            if found:
                raise Exception("[*]ERROR: Built-in certtificate is loaded[*]")
                
            self.log.info("[+] Completed successfully [+]")
        except Exception as e:
            self.log.info("Exception: " + str(e))
        finally:
            self.log.info("[+] Uninstalling Commserve [+]")
            self.commserve_install_helper.uninstall_client()

            self.log.info("[+] Uninstalling Client [+]")
            self.client_install_helper.uninstall_client()
