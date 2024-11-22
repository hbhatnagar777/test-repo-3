# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()          --  initialize TestCase class
    setup()             --  setup function of this test case
    run()               --  run function of this test case
"""

import time
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Server.CVFailover.cslivesynchelper import LiveSync


class TestCase(CVTestCase):
    """Class for executing DR backup Production Failover case"""
    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "CVFailover - Production Failover and Failback"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.CVFAILOVER
        self.show_to_user = True
        self.tcinputs = {
            "active_node_name": None,
            "passive_node_name": None,
            "active_machine_hostname": None,
            "active_machine_username": None,
            "active_machine_password": None
        }
        self.active_node_name = None
        self.passive_node_name = None
        self.active_node = None
        self.passive_node = None

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.log = logger.get_log()
        self.active_node_name = self.tcinputs["active_node_name"]
        self.passive_node_name = self.tcinputs["passive_node_name"]
        hostname, username, passwd = self.tcinputs["active_machine_hostname"],\
                                     self.tcinputs["active_machine_username"], \
                                     self.tcinputs["active_machine_password"]
        self.active_node = LiveSync(self, node_name=self.active_node_name,
                                    machine_hostname=hostname,
                                    machine_username=username,
                                    machine_passwod=passwd)
        self.passive_node = LiveSync(self, self.passive_node_name)
        
    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("[+] Performing a Production failover [+]")
            output = self.active_node.production_failover(self.passive_node_name, wait_for_completion=True)
            if output[0] != 0:
                raise Exception(f"Production Failover failed with error: \n {output[1]}")
            details = self.active_node.latest_failover_details()
            if "SUCCEEDED" not in details["endDetail"]:
                raise Exception(f"Failed to perform Production failover to {self.passive_node_name}.\n"
                                f"{details['endDetails']} ")
            active_node_role = self.active_node.get_node_info(self.active_node_name)
            passive_node_role = self.active_node.get_node_info(self.passive_node_name)
            if active_node_role == "Stand By" and passive_node_role == "Production Node":
                self.log.info(f"Production Failover to node {self.passive_node_name} succeeded")
            else:
                raise Exception(f"Failed to perform Production failover to {self.passive_node_name}.\n"
                                f"{self.active_node_name} -- {active_node_role} \n"
                                f"{self.passive_node_name} -- {passive_node_role}")
            time.sleep(120)
            self.log.info("[+] Performing a Production failback [+]")
            output = self.active_node.production_failover(self.active_node_name, wait_for_completion=True)
            if output[0] != 0:
                raise Exception(f"Production Failover failed with error: \n {output[1]}")
            details = self.active_node.latest_failover_details()
            if "SUCCEEDED" not in details["endDetail"]:
                raise Exception(f"Failed to perform production failover from {self.passive_node_name}.\n"
                                f"{details['endDetails']} ")
            active_node_role = self.active_node.get_node_info(self.active_node_name)
            passive_node_role = self.active_node.get_node_info(self.passive_node_name)
            if active_node_role == "Production Node" and passive_node_role == "Stand By":
                self.log.info(f"Production Failback from node {self.passive_node_name} succeeded")
            else:
                raise Exception(f"Failed to perform Production failback from {self.passive_node_name}.\n"
                                f"{self.active_node_name} -- {active_node_role} \n"
                                f"{self.passive_node_name} -- {passive_node_role}")
        except Exception as excep:
            self.log.error(excep)
