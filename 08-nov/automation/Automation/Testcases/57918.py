# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """ Production Failover cycle  """
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall]:Production Failover cycle"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "active_machine_hostname": None,
            "active_machine_username": None,
            "active_machine_password": None,

            "passive_machine_hostname": None,
            "passive_machine_username": None,
            "passive_machine_password": None,

            "passive_node_name": None
        }
        self.active_machine = None
        self.passive_machine = None
        self.passive_node_name = None
        self.active_path1 = None
        self.passive_path1 = None
        self.active_path2 = None
        self.passive_path2 = None

    def setup(self):
        # Initialising variables
        self.passive_node_name = self.tcinputs["passive_node_name"]
        self.active_machine = Machine(
            machine_name=self.tcinputs["active_machine_hostname"],
            username=self.tcinputs["active_machine_username"],
            password=self.tcinputs["active_machine_password"]
        )

        self.passive_machine = Machine(
            machine_name=self.tcinputs["passive_machine_hostname"],
            username=self.tcinputs["passive_machine_username"],
            password=self.tcinputs["passive_machine_password"]
        )

        self.active_path1 = f'{self.active_machine.get_registry_value("Base", "dBASEHOME")}\\gxadmin.exe'
        self.active_path1 = self.active_path1.replace("Program Files", '"Program Files"')
        self.active_path2 = self.active_path1.replace("ContentStore", "ContentStore2")

        self.passive_path1 = f'{self.passive_machine.get_registry_value("Base", "dBASEHOME")}\\gxadmin.exe'
        self.passive_path1 = self.passive_path1.replace("Program Files", '"Program Files"')
        self.passive_path2 = self.passive_path1.replace("ContentStore", "ContentStore2")

    def run(self):
        try:
            # Stop all commvault services
            self.log.info(f"Stopping the services on instance001")
            self.log.info(f"\n{self.active_path1} -console -stopsvcgrp All\n")
            op = self.active_machine.execute_command(self.active_path1 + r" -console -stopsvcgrp All")
            self.log.info(f"{op.output}")

            self.log.info(f"Stopping the services on instance002")
            self.log.info(f"\n{self.active_path2} -console -stopsvcgrp All\n")
            op = self.active_machine.execute_command(self.active_path2 + r" -console -stopsvcgrp All")
            self.log.info(f"{op.output}")

            # Machine object for passive node
            self.log.info("Executing\n" + self.passive_path2
                          + f' -console -failover -execute -type "Production" -destNode {self.passive_node_name} -skipConfirmation')
            op = self.passive_machine.execute_command(self.passive_path2 + f' -console -failover -execute -type "Production" -destNode {self.passive_node_name} -skipConfirmation')
            self.log.info(f"{op.output}")

            # Active node start instance 2 services
            self.log.info("Executing: \n" + self.active_path2 + " -console -startsvcgrp All")
            op = self.active_machine.execute_command(self.active_path2 + " -console -startsvcgrp All")
            self.log.info(f"{op.output}")

            # Verify node status
            self.log.info("Executing: \n" + self.active_path2
                          + f" -console -failover -getnodeinfo -nodeName {self.passive_node_name}")
            op = self.active_machine.execute_command(self.active_path2 + f" -console -failover -getnodeinfo -nodeName {self.passive_node_name}")
            self.log.info(f"{op.output}")
            if "Active" not in op.output:
                raise Exception("Test case failed. Passive node can not become active.")

        except Exception as e:
            self.log.info(f"Failed with Exception : {str(e)}")
