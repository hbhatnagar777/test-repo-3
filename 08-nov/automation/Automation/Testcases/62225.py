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
from AutomationUtils import logger, config
from AutomationUtils.cvtestcase import CVTestCase
from Server.CVFailover.cslivesynchelper import LiveSync
class TestCase(CVTestCase):
    """Class for executing Production Maintenance Failover case"""
    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "CVFailover - Production Maintenance Failover and Failback"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.CVFAILOVER
        self.show_to_user = True
        self.tcinputs = {
            "active_node_name": None,
            "passive_node_name": None,
            "active_machine_hostname": None,
            "active_machine_username": None,
            "active_machine_password": None,
            "passive_machine_hostname": None,
            "passive_machine_username": None,
            "passive_machine_password": None
        }
        self.active_node_name = None
        self.passive_node_name = None
        self.active_node = None
        self.passive_node = None
        self.active_node_failover_instance = "Instance002"

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.log = logger.get_log()
        self.active_node_name = self.tcinputs["active_node_name"]
        self.passive_node_name = self.tcinputs["passive_node_name"]
        hostname, username, passwd = self.tcinputs["active_machine_hostname"], \
                                     self.tcinputs["active_machine_username"], \
                                     self.tcinputs["active_machine_password"]
        self.active_node = LiveSync(self, node_name=self.active_node_name,
                                    machine_hostname=hostname,
                                    machine_username=username,
                                    machine_passwod=passwd)
        hostname, username, passwd = self.tcinputs["passive_machine_hostname"], \
                                     self.tcinputs["passive_machine_username"], \
                                     self.tcinputs["passive_machine_password"]
        self.passive_node = LiveSync(self, node_name=self.passive_node_name,
                                     machine_hostname=hostname,
                                     machine_username=username,
                                     machine_passwod=passwd)
        config_json = config.get_config()
        if config_json.cslivesync.active_node_failover_instance:
            self.active_node_failover_instance = config_json.cslivesync.active_node_failover_instance

    def run(self):
        """Execution method for this test case"""
        try:
            out = self.active_node.execute_command("commvault stop -all")
            if out[0] != 0:
                raise Exception(f"Service stop failed on active node {self.active_node_name}")
            self.log.info("[+] Performing a Unplanned Production failover [+]")
            output = self.passive_node.unplanned_production_failover(self.passive_node_name, wait_for_completion=True)
            if output[0] != 0:
                raise Exception(f"Production Failover failed with error: \n {output[1]}")
            details = self.passive_node.latest_failover_details()
            if "SUCCEEDED" not in details["endDetail"]:
                raise Exception(f"Failed to perform unplanned Production failover to {self.passive_node_name}.\n"
                                f"{details['endDetails']} ")
            passive_node_role = self.passive_node.get_node_info(self.passive_node_name)
            active_node_role = self.passive_node.get_node_info(self.active_node_name)
            if active_node_role == "Stand By" and passive_node_role == "Production Node":
                self.log.info(f"Unplanned Production Failover to node {self.passive_node_name} succeeded")
            else:
                raise Exception(f"Failed to perform unplanned Production failover to {self.passive_node_name}.\n"
                                f"{self.active_node_name} -- {active_node_role} \n"
                                f"{self.passive_node_name} -- {passive_node_role}")
            time.sleep(120)
            out = self.active_node.execute_command(f"commvault start -instance {self.active_node_failover_instance}")
            if out[0] != 0:
                raise Exception(f"Service start failed on standby node {self.active_node_name}")
            time.sleep(300)
            self.log.info("[+] Performing a Production failover [+]")
            output = self.passive_node.production_failover(self.active_node_name, wait_for_completion=True)
            if output[0] != 0:
                raise Exception(f"Production Failover failed with error: \n {output[1]}")
            details = self.passive_node.latest_failover_details()
            if "SUCCEEDED" not in details["endDetail"]:
                raise Exception(f"Failed to perform unplanned Production failover to {self.passive_node_name}.\n"
                                f"{details['endDetails']} ")
            passive_node_role = self.passive_node.get_node_info(self.passive_node_name)
            active_node_role = self.passive_node.get_node_info(self.active_node_name)
            if active_node_role == "Production Node" and passive_node_role == "Stand By":
                self.log.info(f"Unplanned Production Failover to node {self.passive_node_name} succeeded")
            else:
                raise Exception(f"Failed to perform Production Maintenance failover to {self.passive_node_name}.\n"
                                f"{self.active_node_name} -- {active_node_role} \n"
                                f"{self.passive_node_name} -- {passive_node_role}")
        except Exception as excep:
            self.log.error(excep)
