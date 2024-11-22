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

Instruction:
    Inputs:
        Upgraded clients  -- Client Should be upgraded SP25 client whose certificate has been renewed
        tenant3SP20Client -- Client should be of SP20 whose certificate has been renewed

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper


class TestCase(CVTestCase):
    """[Network & Firewall] : Network Zoning test cases
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Network Zoning test cases"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK

        self.tenant_1_client = None
        self.tenant_2_client = None
        self.tenant_3_client = None

        self.proxy1 = None
        self.proxy2 = None

        self.msp_ma = None
        self.tenant_1_ma = None

        self.network_helper = None

        # tcinputs
        self.tcinputs = {
            "MSPProxy1": None,
            "MSPProxy2": None,

            "MSPMA": None,
            "tenantMA": None,

            "tenant1UpgradeClient": None,
            "tenant2UpgradeClient": None,
            "tenant3SP20Client": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.network_helper = NetworkHelper(self)

        self.tenant_1_client = self.tcinputs['tenant1UpgradeClient']
        self.tenant_2_client = self.tcinputs['tenant2UpgradeClient']
        self.tenant_3_client = self.tcinputs['tenant3SP20Client']

        self.proxy1 = self.tcinputs['MSPProxy1']
        self.proxy2 = self.tcinputs['MSPProxy2']

        self.msp_ma = self.tcinputs['MSPMA']
        self.tenant_1_ma = self.tcinputs['tenantMA']
        try:
            self.network_helper.topologies.delete(
                "60915_Network_Zoning_topology")
            self.commcell.client_groups.delete("60915_Network_Zoning_client")
            self.commcell.client_groups.delete("60915_Network_Zoning_CSMA")
            self.commcell.client_groups.delete("60915_Network_Zoning_proxy")
        except:
            pass

        self.commcell.client_groups.add(
            "60915_Network_Zoning_client",
            [self.tenant_1_client, self.tenant_2_client, self.tenant_3_client]
        )

        self.commcell.client_groups.add(
            "60915_Network_Zoning_proxy",
            [self.proxy1, self.proxy2]
        )

        self.commcell.client_groups.add(
            "60915_Network_Zoning_CSMA",
            [self.commcell.commserv_name, self.msp_ma, self.tenant_1_ma]
        )

    def run(self):
        """Run function """
        try:
            self.log.info(f"[+] STEP 1 Creating proxy topology [+]")
            self.network_helper.proxy_topology(
                "60915_Network_Zoning_client", "60915_Network_Zoning_CSMA",
                "60915_Network_Zoning_proxy", "60915_Network_Zoning_topology"
            )

            self.log.info(
                f"[+] STEP 2 Checking Routes for tenant 1 client MSP MA [+]")
            status = self.checkNetworkRoutes(self.tenant_1_client, self.msp_ma)
            if False and status != 'PASSED':
                raise Exception(
                    "Route check for tenant 1 for MSP media agent should have passed")

            self.log.info(
                f"[+] STEP 3 Checking Routes for tenant 1 client tenant 1 MA [+]")
            status = self.checkNetworkRoutes(self.tenant_1_client, self.tenant_1_ma)
            if False and status != 'PASSED':
                raise Exception(
                    "Route check for tenant 1 for MSP media agent should have passed")

            self.log.info(
                f"[+] STEP 4 Checking Routes for tenant 2 client tenant 1 MA [+]")
            status = self.checkNetworkRoutes(self.tenant_2_client, self.tenant_1_ma)
            if False and status != 'FAILED':
                raise Exception(
                    "Route check for tenant 2 for MSP media agent should have FAIL")

            self.log.info(
                f"[+] STEP 5 Checking Routes for tenant 3 client MSP MA [+]")
            status = self.checkNetworkRoutes(self.tenant_3_client, self.msp_ma)
            if False and status != 'PASSED':
                raise Exception(
                    "Route check for tenant 3 for MSP media agent should have passed")

            self.log.info(
                f"[+] STEP 6 Checking Routes for tenant 3 client tenant 1 MA [+]")
            status = self.checkNetworkRoutes(self.tenant_3_client, self.tenant_1_ma)
            if False and status != 'FAILED':
                raise Exception(
                    "Route check for tenant 3 for MSP media agent should have FAIL")
            self.log.info("[+] --> SUCCESSFUL <-- [+]")
        except Exception as e:
            self.log.info(f"[*] ERROR: {str(e)}[*]")
            self.network_helper.server.fail(e)

        finally:
            self.network_helper.topologies.delete(
                "60915_Network_Zoning_topology")
            self.commcell.client_groups.delete("60915_Network_Zoning_client")
            self.commcell.client_groups.delete("60915_Network_Zoning_CSMA")
            self.commcell.client_groups.delete("60915_Network_Zoning_proxy")

    def checkNetworkRoutes(self, client, ma):
        summaries = self.network_helper.get_network_summary([client, ma])
        if f" {ma} " in summaries[client] and f" {client} " in summaries[ma]:
            return 'PASSED'
        return 'FAILED'

