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

This testcase verifies QOS with network routes.

Input parameters:
    NetworkClient:  client name of the network client

    NetworkMediaAgent:  Client Name of the media agent

    NetworkClientLinux:  linux client name of the network client

Make sure the inputs are valid and hostnames in commcell correct for these clients before running the test case.

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """
    Verify QOS with network routes.
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Verify QOS with network routes."
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkMediaAgent": None,
            "NetworkClientLinux": None
        }
        self.network_helper = None
        self.cl = None
        self.ma = None
        self.cl_obj = None
        self.machine_cl = None
        self.ma_obj = None
        self.machine_ma = None
        self.linux_client = None
        self.clientgrp = "58968_Clients"
        self.ma_grp = "58968_MediaAgents"
        self.cs_grp = "58968_CS"
        self.topology_Name = "TEST_TOPOLOGY"

    def setup(self):
        """Initiatialize the objects and create client group"""
        self.network_helper = NetworkHelper(self)
        self.cl = self.tcinputs["NetworkClient"]
        self.ma = self.tcinputs["NetworkMediaAgent"]
        self.linux_client = self.tcinputs["NetworkClientLinux"]
        self.cl_obj = self.commcell.clients.get(self.cl)
        self.machine_cl = Machine(self.cl_obj)
        self.ma_obj = self.commcell.clients.get(self.ma)
        self.machine_ma = Machine(self.ma_obj)
        self.linux_client_obj = self.commcell.clients.get(self.linux_client)
        self.linux_machine_obj = Machine(self.linux_client_obj)

        self.clients_grps = self.commcell.client_groups
        groups = self.network_helper.entities.create_client_groups([self.clientgrp, self.ma_grp, self.cs_grp])
        groups[self.clientgrp]['object'].add_clients([self.cl, self.linux_client])
        groups[self.ma_grp]['object'].add_clients([self.ma])

    def __check_readiness_and_trigger_jobs(self):
        """
        Check readiness and trigger jobs
        """
        self.log.info("Perform check readiness before qosDscp value being set")
        self.network_helper.serverbase.check_client_readiness([
            self.cl, self.linux_client, self.ma
        ])

        self.log.info("Run backup and restore job")
        self.network_helper.validate([self.cl, self.linux_client], self.ma)

    def run(self):
        try:
            self.log.info("[+] Setting qosDscp  key on client machine. [+]")
            self.machine_cl.create_registry("Session", "qosDscp", 30, "DWord")
            self.linux_machine_obj.create_registry("Session", "qosDscp", 2, "DWord")
            # We don't need to restart for this key.
            # self.cl_obj.restart_services()
            # self.linux_client_obj.restart_services()
            self.log.info("[+] Setting qosDscp  key on media-agent machine. [+]")
            self.machine_ma.create_registry("Session", "qosDscp", 30, "DWord")

            for firewall_rule_validation in [self.one_way, self.via_proxy]:
                firewall_rule_validation()

        except Exception as e:
            self.log.info("Failure in testcase : Exception: " + str(e))
            raise Exception(e)

        finally:
            self.network_helper.cleanup_network()
            del self.network_helper
            self.machine_cl.remove_registry("Session", "qosDscp")
            self.machine_ma.remove_registry("Session", "qosDscp")
            self.linux_machine_obj.remove_registry("Session", "qosDscp")

    def one_way(self):
        """Create a oneway between client and media agent
            and start the validate jobs
        """
        try:
            self.network_helper.one_way_topology(self.clientgrp, self.ma_grp, self.topology_Name)
            self.network_helper.push_config_client([self.cl, self.ma, self.linux_client])

            self.__check_readiness_and_trigger_jobs()
            self.network_helper.delete_topology(self.topology_Name)
        except Exception as e:
            self.log.info("Failure during oneway topology and validation : Exception: " + str(e))
            raise Exception(e)

    def via_proxy(self):
        """Create a proxy topology between client and media agent
            and start the validate jobs
        """
        self.network_helper.proxy_topology(self.clientgrp, self.ma_grp, self.cs_grp, self.topology_Name)
        self.network_helper.push_config_client([self.cl, self.ma, self.linux_client])
        self.__check_readiness_and_trigger_jobs()
        self.network_helper.delete_topology(self.topology_Name)