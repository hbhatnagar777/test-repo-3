# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import importlib

parent_testcase_id = "71092"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """HS Automation: 1x: Offline platform upgrade using metadata.tar from cloud.commvault.com
    The Implementation is Inherited from TestCase 71092"""
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "71096"
        self.name = "HS Automation: 1x: Offline platform upgrade using metadata.tar from cloud.commvault.com"
        
    def setup(self):
        super().setup()
        
