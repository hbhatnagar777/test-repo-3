# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for 2x: Platform upgrade post refresh node

Sample input json
"71112": {
            "Nodes": [
              "MA1",
              "MA2",
              "MA3"
            ],
            "CacheNode": {
              "name": "name",
              "username": "username",
              "password": "password"
            },
            "StoragePoolName": "name",
            "UpgradeCVFS": None,    (Optional)
            "UpgradeOS": None       (Optional)
        }
"""

import importlib

parent_testcase_id = "70455"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Test Case for 3x: Platform upgrade post refresh nodes
    The Implementation is Inherited from TestCase 70455"""
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "71112"
        self.name = "Test Case for 3x: Platform upgrade post refresh node"
      
    def setup(self):
        super().setup()
        self.update_cvfs = True
        self.update_os = True
        self.non_disruptive = False
