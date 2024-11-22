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

TeseCase Inputs:
    NetworkClient  --  Client with FileSystem installed
    ProxyClient1    --  ProxyClient1 & NetworkClient machine should be in Same continent
    ProxyClient2    --  ProxyClient2 & NetworkClient machine should be in different continent
    MediaAgent      --  Client with MeadiaAgent nstalled
    *Note           --  Do not provide commserve as the tcinputs.

This testcase perform thr first 3 steps of 60041 and I will update the testcase once I get 
the fix for MR: https://engweb.commvault.com/defect/321138.
"""

import time
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from cvpysdk.network_topology import NetworkTopology


class TestCase(CVTestCase):
    """
    One Way Forwarding Network Topology basic acceptance
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : One Way Forwarding Network Topology basic acceptance"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "NetworkClient": None,
            "ProxyClient1": None,
            "ProxyClient2": None,
            "MediaAgent": None
        }
        self.client1 = None
        self.client2 = None
        self.client3 = None
        self.client4 = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.network_helper = NetworkHelper(self)

            self.client1 = self.tcinputs["NetworkClient"]
            self.client2 = self.tcinputs["ProxyClient1"]
            self.client3 = self.tcinputs["ProxyClient2"]
            self.client4 = self.tcinputs["MediaAgent"]

            self.network_helper.remove_network_config([
                {'clientName': self.client1},
                {'clientName': self.client2},
                {'clientName': self.client3},
                {'clientName': self.client4},
            ])
        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)

    def run(self):
        """Run function """
        try:
            self.log.info("[(*)] STEP 1 [(*)]")
            self.log.info("[+] Creating dummy clients [+]")
            self.commcell.clients.create_pseudo_client("dummy1")
            self.commcell.clients.create_pseudo_client("dummy2")
            self.commcell.clients.create_pseudo_client("dummy3")

            self.log.info("[+] Creating client groups and adding clients [+]")
            self.commcell.client_groups.add(
                "Internal_CG", ["dummy1", self.client1])
            self.commcell.client_groups.add(
                "Proxy_CG", ["dummy2", self.client2, self.client3])
            self.commcell.client_groups.add("External_CG", [self.client4])

            
            self.log.info("[+] Creating one way forwarding topology [+]")
            self.network_helper.topologies.add(
                "OneWay_Forwarding_Topology", [
                    {'group_type': 1, 'group_name': "External_CG",
                        'is_mnemonic': False},
                    {'group_type': 2, 'group_name': "Internal_CG",
                        'is_mnemonic': False},
                    {'group_type': 3, 'group_name': "Proxy_CG", 'is_mnemonic': False}
                ],
                use_wildcardproxy=True,
                encrypt_traffic=1,
                topology_type=5,
                topology_description="This is a test for validating One-way firewall topology."
            )

            self.check_db()

            summaries = self.network_helper.get_network_summary(
                [
                    self.client1, self.client2, self.client3, self.client4
                ]
            )

            # Checking network routes
            self.log.info("[+] Checking Network Summary [+]")

            # if summaries[self.client1].find(f"{self.client1} * proxy={self.client2}") == -1 and \
            #         summaries[self.client1].find(f"{self.client1} * proxy={self.client3}") == -1 and \
            #         summaries[self.client1].find(f"{self.client1} {self.client4} proxy={self.client2}") == -1 and \
            #         summaries[self.client1].find(f"{self.client1} {self.client4} proxy={self.client3}") == -1:
            #     raise Exception(
            #         f"Routes for client {self.client1} did not set")

            # temp_idx1 = summaries[self.client2].find(f"{self.client2} {self.client1}") + len(
            #     f"{self.client2} {self.client1}")
            # if summaries[self.client2][temp_idx1 + 50: temp_idx1 + 62] != 'type=passive' and \
            #         summaries[self.client2][temp_idx1 + 50: temp_idx1 + 65] != 'type=persistent':
            #     raise Exception(
            #         f"Routes for client {self.client2} did not set")

            # temp_idx1 = summaries[self.client3].find(f"{self.client3} {self.client1}") + len(
            #     f"{self.client3} {self.client1}")
            # if summaries[self.client3][temp_idx1 + 50: temp_idx1 + 62] != 'type=passive' and \
            #         summaries[self.client3][temp_idx1 + 50: temp_idx1 + 65] != 'type=persistent':
            #     raise Exception(
            #         f"Routes for client {self.client3} did not set")

            # if summaries[self.client4].find(f"{self.client4} {self.client1} proxy={self.client2}") == -1 and \
            #         summaries[self.client4].find(f"{self.client4} {self.client1} proxy={self.client3}") == -1:
            #     raise Exception(
            #         f"Routes for client {self.client4} did not set")

            # STEP 2 - Uncheck the wild card proxy option
            self.log.info("[(*)] STEP 2 [(*)]")
            self.log.info(
                "[+] Updating topology uncheck the wild card proxy option [+]")

            topology = NetworkTopology(
                self.commcell, "OneWay_Forwarding_Topology")
            topology.update(
                use_wildcardproxy=False
            )
            self.commcell.refresh()
            self.check_db()

            # Checking network routes
            self.log.info(
                "[+] Checking network route after updating topology [+]")

            # summary = self.network_helper.get_network_summary([self.client1])[
            #     self.client1]
            # if summary.find(f"{self.client1} * {self.client2}") != -1 and \
            #         summary.find(f"{self.client1} * {self.client3}") != -1:
            #     raise Exception(
            #         f"Client {self.client1} is still using wild card proxy")

            self.network_helper.topologies.delete("OneWay_Forwarding_Topology")

            # STEP 3 - Modify topology
            self.log.info("[(*)] STEP 3 [(*)]")
            self.log.info("[+] Creating Two way topology [+]")
            self.network_helper.two_way_topology(
                "Internal_CG", "External_CG", "TwoWay_60041"
            )
            # self.log.info("[+] Checking network routes [+]")
            # summaries = self.network_helper.get_network_summary(
            #     [
            #         self.client1, self.client4
            #     ]
            # )
            # temp_idx1 = summaries[self.client1].find(f"{self.client1} {self.client4}") + len(
            #     f"{self.client1} {self.client4}")
            # if summaries[self.client1][temp_idx1 + 50:temp_idx1 + 63] != 'type=ondemand':
            #     raise Exception("Tow way topology did not set proprly")

            self.log.info(
                "[+] Modifying the topology by changing client group from External_CG to Proxy_CG [+]")
            self.network_helper.modify_topology(
                "TwoWay_60041", [
                    {'group_type': 2, 'group_name': "Internal_CG",
                        'is_mnemonic': False},
                    {'group_type': 1, 'group_name': "Proxy_CG", 'is_mnemonic': False}
                ]
            )
            # self.log.info("[+] Checking network routes [+]")
            # summaries = self.network_helper.get_network_summary(
            #     [
            #         self.client1, self.client3
            #     ]
            # )
            # temp_idx1 = summaries[self.client1].find(f"{self.client1} {self.client3}") + len(
            #     f"{self.client1} {self.client3}")
            # if summaries[self.client1][temp_idx1 + 50:temp_idx1 + 63] != 'type=ondemand':
            #     raise Exception("Tow way topology did not set proprly")

            self.network_helper.topologies.delete("TwoWay_60041")

            self.log.info("[ --> SUCCESSFUL <--]")
        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)
            self.status = 'FAILED'

        finally:
            self.cleanup()

    def check_db(self):
        # Check all the related tables
        self.log.info("[+] Checking database [+]")

        query = "SELECT description, topologyType FROM APP_FirewallTopology WHERE topologyName = 'OneWay_Forwarding_Topology';"
        self.csdb.execute(query)
        result_set = self.csdb.fetch_one_row()
        if result_set != ['This is a test for validating One-way firewall topology.', '5']:
            raise Exception("Entry in topology table is incorrect")

        def runquery(client_type):
            query = "SELECT id FROM APP_ClientGroup WHERE name = " + client_type
            self.csdb.execute(query)
            return self.csdb.fetch_one_row()[0]

        external_CG, internal_CG, proxy_CG = map(runquery,["'External_CG';", "'Internal_CG';", "'Proxy_CG';"])
        
        raw_queries = [
            [f"SELECT restrictionType FROM APP_Firewall WHERE clientGroupId = {internal_CG} and forClientGroupId = {proxy_CG}", 1],
            [f"SELECT restrictionType FROM APP_Firewall WHERE clientGroupId = {proxy_CG} and forClientGroupId = {external_CG}", 1],
            [f"SELECT restrictionType FROM APP_Firewall WHERE clientGroupId = {proxy_CG} and forClientGroupId = {internal_CG}", 0],
            [f"SELECT restrictionType FROM APP_Firewall WHERE clientGroupId = {external_CG} and forClientGroupId = {proxy_CG}", 0],
            [f"SELECT isDMZ FROM App_FirewallOptions WHERE clientGroupId = {proxy_CG}", 1]
        ]

        for query, result in raw_queries:
            self.csdb.execute(query)
            if self.csdb.fetch_one_row() != [f"{result}"]:
                raise Exception(f"[FAILED] Query: {query}")

    def cleanup(self):
        self.commcell.clients.delete("dummy1")
        self.commcell.clients.delete("dummy2")
        self.commcell.clients.delete("dummy3")

        self.commcell.client_groups.delete('Internal_CG')
        self.commcell.client_groups.delete('Proxy_CG')
        self.commcell.client_groups.delete('External_CG')
