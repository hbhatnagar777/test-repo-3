# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

import time
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from Server.CVFailover.cslivesynchelper import LiveSync
from cvpysdk.commcell import Commcell


class TestCase(CVTestCase):
    """ Production Failover cycle
    """
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall]:Production Failover cycle"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "cs_hostname": None,
            "cs_username": None,
            "cs_password": None,
            "active_node_name": None,
            "passive_node_name": None
        }
        self.network_helper = None
        self.active_node_name = None
        self.passive_node_name = None
        self.active_node = None
        self.passive_node = None
        self.active_node_hostname = None
        self.passive_node_hostname = None
        self.username = None
        self.passwd = None

    def setup(self):
        # Initialising variables
        self.log.info("Initialising variables")
        self.active_node_name = self.tcinputs["active_node_name"]
        self.passive_node_name = self.tcinputs["passive_node_name"]
        self.active_node_hostname = self.tcinputs["cs_hostname"]
        self.username = self.tcinputs["cs_hostname"]
        self.active_node_hostname = self.tcinputs["cs_hostname"]

        # Creating commcell object & helper objects
        self.log.info("Creating commcell object & helper objects")
        self.commcell = Commcell(self.active_node_hostname, self.username, self.passwd)
        self.network_helper = NetworkHelper(self)
        self.passive_node = LiveSync(self, self.passive_node_name)

        # Getting the passive node hostname
        self.log.info("Getting the passive node hostname")
        self.passive_node_hostname = self.passive_node.client_obj.client_hostname

        # Enabling firewall
        self.log.info("Enabling Firewall")
        self.network_helper.enable_firewall(
            [self.passive_node_name, self.active_node_name,
             self.passive_node_name, self.passive_node_name],
            [8403, 8405, 8403, 8405]
        )

    def run(self):
        try:
            self.log.info(f"[+] Performing a Production failover from {self.passive_node_name}[+]")
            self.passive_node.production_failover(self.passive_node_name)

            self.log.info(f"[+] Sleeping for 2700 seconds[+]")
            time.sleep(2700)

            self.log.info(f"[+] Creating commcell object & helper objects  [+]")
            self.commcell = Commcell(self.passive_node_hostname, self.username, self.passwd)
            self.network_helper = NetworkHelper(self)
            self.passive_node = LiveSync(self, self.passive_node_name)

            self.log.info("[+] Fetching the failover details [+]")
            details = self.passive_node.latest_failover_details()
            self.log.info(f"[+] Details are as follows {details}[+]")

            if "SUCCEEDED" not in details["endDetail"]:
                raise Exception(f"Failed to perform Production failover!\n{details['endDetail']}")

            node_info = self.passive_node.get_node_info()
            self.log.info(f"{node_info}")
            if "Active" not in node_info:
                raise Exception(f"{self.passive_node_name} should is not active")

            node_info = self.passive_node.get_node_info(f"{self.active_node_name}")
            self.log.info(f"{node_info}")
            if "Passive" not in node_info:
                raise Exception(f"{self.active_node.node_name} should is not passive")

            self.log.info(f"[+] Performing a Production failover from {self.active_node_name}[+]")
            self.passive_node.production_failover(self.active_node_name)

            self.log.info(f"[+] Sleeping for 2700 seconds[+]")
            time.sleep(2700)

            self.log.info(f"[+] Creating commcell object & helper objects  [+]")
            self.commcell = Commcell(self.active_node_hostname, self.username, self.passwd)
            self.network_helper = NetworkHelper(self)
            self.passive_node = LiveSync(self, self.passive_node_name)

            self.log.info("[+] Fetching the failover details [+]")
            details = self.passive_node.latest_failover_details()
            self.log.info(f"[+] Details are as follows {details}[+]")

            if "SUCCEEDED" not in details["endDetail"]:
                raise Exception(f"Failed to perform Production failover!\n{details['endDetail']}")

            node_info = self.passive_node.get_node_info()
            self.log.info(f"{node_info}")
            if "Passive" not in node_info:
                raise Exception(f"{self.passive_node_name} should is not passive")

            node_info = self.passive_node.get_node_info(f"{self.active_node_name}")
            self.log.info(f"{node_info}")
            if "Active" not in node_info:
                raise Exception(f"{self.active_node.node_name} should is not active")

        except Exception as e:
            self.log.info(f"Failed with Exception : {str(e)}")

        finally:
            self.network_helper.cleanup_network()
