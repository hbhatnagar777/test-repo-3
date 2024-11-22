# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for Cluster Deployment for HSX 2.X
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample input json
"69119": {
          "CVBackupAdminPassword": "password",
          "RevertSnapshots":true/false, 
          "CreateSnapshots":true/false,
          "CleanupFromCs":true/false,
          "IsoKey": "3.2312",
          "IsoDatastore":null,
          "ClusterName": ,
          "VMNames": [
            "vm-name-1",
            "vm-name-2",
            "vm-name-3"
        ],
        "HostNames": [
          "hostname1",
          "hostname2",
          "hostname3"
        ],
          "BlockName": "",
          "DPIPs": <list of dpips>,
          "SPIPs": <list of spips>,
          "Gateway": "gateway ip",
          "DNSs": <list of dnsses>,
          "DPNetmask": "data protection netmask",
          "SPNetmask": "storage pool netmask",
          "DPIFs": [
            "dp interface name",
            "dp interface name"
          ],
          "SPIFs": [
            "sp interface name",
            "sp interface name"
          ]
        }
"""
# The following keys must be present under HyperScale key
# in config.json file
vmconfig_help = '''
"HyperScale": {
    "Credentials": {
        "User": "default hyperscale username",
        "Password": "default hyperscale password"
    },
    "VMConfig": {
        "ServerHostName": "Host name of the VM server",
        "Username": "Login user for the VM server",
        "Password": "password for the user"
    }
}
'''

import importlib

parent_testcase_id = "69032"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for Cluster Deployment
    The Implementation is Inherited from TestCase 69032"""
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "69119"
        self.name = "Test Case for Cluster Deployment HSX 2.X"
        self.successful = False

