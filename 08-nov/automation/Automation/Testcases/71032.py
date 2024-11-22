# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib

parent_testcase_id = "69125"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for Add Node
       on HSX 3.x for a Metallic Configuration
    """
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "71032"
        self.name = "Test Case for 3x: Metallic Add Node configuration"
        
    def setup(self):
        super().setup()
        self.update_cvfs = False
        self.update_os = True
        self.non_disruptive = False