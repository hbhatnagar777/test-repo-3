# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

APIs being validated inside collection file:


TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.RestAPI.Locust.Locust_testcase import locust_helper
from cvpysdk.commcell import Commcell
import AutomationUtils.constants as ac
import os
import subprocess
import json
import sys


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Locust load testing tool"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[REST API - LOCUST] Performance testing for Fileserver Page APIs"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = False
        self._locusttester = None
        self.inputJSON = None
        self.headlessPath = None
        self.server = None
        self.inputs = None
        self.fileName = __file__

    def setup(self):
        """Setup function of this test case"""
        self.server = ServerTestCases(self)
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword'],
                       "threads": self.tcinputs.get("threads", "1"),
                       "spawnRate": self.tcinputs.get("spawnRate", "1"),
                       "minutes": self.tcinputs.get("minutes", "1"),
                       "apiList": "get_client_server,get_client_details,get_client_shares,get_vmallocationpolicy,get_slaconfig,get_client_hierarchy,get_backupsets,get_subclient_fileserver,get_jobs_calendar",
                       "email": self.tcinputs["email"],
                       "fileName": self.fileName,
                       "get_client_servers": {
                           "Hiddenclients": "false",
                           "includeIdaSummary": "true",
                           "propertyLevel": "10",
                           "excludeInfrastructureClients": "false",
                           "infrastructureMachineFilter": 1,
                           "fq": "clientProperties.isServerClient=true",
                           "start": 0,
                           "limit": 20,
                           "sort": "client.clientEntity.displayName:1",
                           "fl": "clientProperties.client,clientProperties.clientProps,overview"
                       }
                       }
        apis = self.inputs.get("apiList").split(",")
        for i in apis:
            if i in self.tcinputs:
                self.inputs[i] = self.tcinputs[i]

    def run(self):
        """Main function for test case execution"""

        try:
            locust_instance = locust_helper.Locust_Helper(self.inputs)
            locust_instance.locust_execute()

        except Exception as excp:
            self.server.fail(excp)
