# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib

parent_testcase_id = "70797"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for Checksum validation
    The Implementation is Inherited from TestCase 70797"""
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "71036"
        self.name = "Test Case for 3x: CVFS checksum validation"
        
    def setup(self):
        super().setup()
        
