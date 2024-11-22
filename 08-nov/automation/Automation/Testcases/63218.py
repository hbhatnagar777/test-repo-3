# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for HSX Ransomware Protection Validation 
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    tear_down()                     --  Tear down function of this test case
      
    fail_test_case()                --  Prints failure reason, sets the result string

    run()                           --  run function of this test case
      

Sample input json
"63218": {
            "Nodes": [
              "ma_name_1",
              "ma_name_2",
              "ma_name_3"
            ],
            "NodeUser": "user",
            "NodePassword": "password",
         }

"""

from typing import Dict

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.unix_ransomware_helper import UnixRansomwareHelper

class TestCase(CVTestCase):
    """Hyperscale test class for HSX Ransomware Protection Validation"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX Ransomware Protection Validation"
        self.result_string = ""
        self.backupset_obj = ""
        self.subclient_obj = ""
        self.client = ""
        self.subclient_name = ""
        self.storage_policy = ""
        self.mas = []
        self.storage_pool_name = ""
        self.storage_policy_name = ""
        self.policy = ""
        self.hyperscale_helper = None
        self.tcinputs = {
            "Nodes": [
            ],
            "NodeUser": None,
            "NodePassword": None,
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        
        # MA setup
        self.node_user = self.tcinputs["NodeUser"]
        self.node_password = self.tcinputs["NodePassword"]
        self.mas = self.tcinputs["Nodes"]
        self.ma_machines: Dict[str, UnixMachine] = {}
        self.rw_helpers: Dict[str, UnixRansomwareHelper] = {}
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            # username/password is necessary as MAs will be marked in maintenance mode
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(ma_name, username=self.node_user, password=self.node_password)
            self.ma_machines[ma_name] = machine
            self.rw_helpers[ma_name] = UnixRansomwareHelper(machine, self.commcell, self.log)

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info(f"Test case successful.")
        else:
            self.log.warning("Test case was not successful")
            self.status = constants.FAILED
   
    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:

                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason
    
    def run(self):
        """ run function of this test case"""
        try: 

            # 1. Check if storage pool exists over the nodes
            self.log.info(f"Checking if storage pool exists over the nodes: {self.mas}")
            self.storage_pool_name = self.hyperscale_helper.get_storage_pool_from_media_agents(self.mas)
            if not self.storage_pool_name:
                reason = f"Unable to find storage pool over the nodes"
                return self.fail_test_case(reason)
            self.log.info(f"Found the storage pool: {self.storage_pool_name}")

            # 2. Check if rwp is enabled on all nodes
            self.log.info(f"Checking if ransomware protection is enabled on all nodes")
            for ma in self.mas:
                if not self.rw_helpers[ma].ransomware_protection_status():
                    reason = f"Ransomware protection disabled on {ma}"
                    return self.fail_test_case(reason)
            self.log.info(f"Ransomware protection enabled on all nodes")

            # 3. Run the validation suite
            self.log.info(f"Running ransomware protection validation suite")
            result = UnixRansomwareHelper.hsx_rwp_validation_suite(self.mas, self.ma_machines, self.hyperscale_helper, self.rw_helpers)
            if not result:
                reason = "Failed to validate ransomware protection"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified ransomware protection")

            self.successful = True
            self.log.info(f"Ransomware protection validation successful")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
