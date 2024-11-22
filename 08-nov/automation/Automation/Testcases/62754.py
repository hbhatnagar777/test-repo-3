# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for HS1.5 to test absence of drill hole reg keys
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    cleanup()                       --  Cleans up the test case resources and directories

    tear_down()                     --  Tear down function of this test case
      
    run()                           --  run function of this test case
      

Sample input json
"62754": {
            "ControlNodes": {
              "MA1": "name",
              "MA2": "name",
              "MA3": "name"
            },
            "StoragePoolName": "name",
            "SqlLogin": login,
            "SqlPassword": password
         }

"""

from HyperScale.HyperScaleUtils.base_test_cases.drill_hole_test_case import DrillHoleTestCase
from AutomationUtils import constants

class TestCase(DrillHoleTestCase):

    def __init__(self):
        """Initialization function"""
        super().__init__()
        self.name = "Test Case for HS 1.5 to test absence of drill hole reg keys"
    
    def cleanup(self):
        """Cleans up the test case resources and directories"""
        self.log.info(f"Cleaning up {self.storage_pool_name}")
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name,
                                                         self.sql_login, self.sql_sq_password)
        self.log.info("Storage pool cleaned up")

    def tear_down(self):
        """Tear down function for this test case"""
        if self.successful:
            self.log.info(f"Test case successful. Cleaning up the entities created.")
            self.cleanup()
        else:
            self.log.warning("Not cleaning up as the run was not successful")
            self.status = constants.FAILED
    
    def run(self):
        try:
            # 0. Cleanup previous runs' entities
            self.log.info("Running cleanup before run")
            self.cleanup()
        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
            return
        super().run()
