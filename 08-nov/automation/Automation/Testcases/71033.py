# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib

parent_testcase_id = "70959"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for the platform upgrade (CVFS + OS) on 
       Metallic HS3.x setup.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "71033"
        self.name = "Test Case for 3x: the platform upgrade (CVFS + OS) on Metallic setup."
        
    def setup(self):
        super().setup()
        self.update_cvfs = False
        self.update_os = True
        self.non_disruptive = False