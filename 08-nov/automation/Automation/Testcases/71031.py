# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib

parent_testcase_id = "69121"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for Image / Install / Deploy / Create Storage Pool 
       process on HSX 3.x for a Metallic Configuration
    """
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "71031"
        self.name = "Test Case for 3x: Image / Install / Deploy / Create Storage Pool on HS3.x Metallic configuration"
        
    def setup(self):
        super().setup()
        self.update_cvfs = False
        self.update_os = True
        self.non_disruptive = False
        