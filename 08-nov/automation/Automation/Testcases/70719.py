# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Testcase for validating platform upgrade post OS upgrade for HSX 3.x

    Sample Input json

    "70719": 
            {
                "VMDict": {
                    "VMName":"Hostname"
                },
                "NodeUsername": "",
                "NodePassword": "",
                "SqlLogin": "",
                "SqlPassword": ""
            }
"""

import importlib

parent_testcase_id = "70718"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for Platform version validation post OS upgrade for HSX 3.x
    The Implementation is Inherited from TestCase 70718"""
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "70719"
        self.name = "Testcase for validating platform upgrade post OS upgrade for HSX 3.x"
        self.successful = False