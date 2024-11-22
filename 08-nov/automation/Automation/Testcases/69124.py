# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test Case for HSX add node for HSX 2.X
Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    run()                           --  run function of this test case

Sample input json
"69124": {
            "ControlNodes": [
                "MA1": "name",
                "MA2": "name",
                "MA3": "name"
            },
            "CacheNode": {
                "name": "name",
                "username": "username",
                "password": "password"
            },
            "AddNode": {
                "name": "name",
                "username": "username",
                "password": "password",
            },
            "StoragePoolName": "name",
            "workflow_name": "workflow_name",
            "SqlLogin": login, (OPTIONAL)
            "SqlPassword": password (OPTIONAL)
            }
"""
# The following keys must be present under HyperScale key
# in config.json file
vmconfig_help = '''
"HyperScale": {
    ...,
    "Credentials": {
        "User": "default username for MA"
        "Password": "default password for MA"
    }
    "VMConfig": {
        "ServerHostName": "Host name of the VM server",
        "Username": "Login user for the VM server",
        "Password": "password for the user"
    }
}
'''

import importlib

parent_testcase_id = "64166"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for HSX 2.X Add node
    The Implementation is Inherited from TestCase 64166"""
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "69124"
        self.name = "Test Case for Add node HSX 2.X"
