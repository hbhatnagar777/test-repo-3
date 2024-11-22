# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib

parent_testcase_id = "70455"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for HSX Platform upgrade from CC
    The Implementation is Inherited from TestCase 70455"""
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "70775"
        self.name = "Test Case for 1x: Disruptive OS only upgrade from CC"
        
    def setup(self):
        super().setup()
        self.update_cvfs = False
        self.update_os = True
        self.non_disruptive = False
        
