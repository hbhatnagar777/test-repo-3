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

Testcase used to run cleanup after locust CRUD case execution

Input - Pattern : (str) Substring to match in the name of the entities

"""

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.exception import SDKException
from Server.RestAPI.Locust.Locust_testcase import locust_helper

class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Locust load testing tool"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[REST API - Locust] - Clearing the entries in the commcell due to locust testcase"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.users = None
        self.user_groups = None
        self.companies = None
        self.roles = None
        self.plans = None
        self.fileName = __file__

    def setup(self):
        """Setup function of this test case"""
        self.users = self.commcell.users
        self.user_groups = self.commcell.user_groups
        self.companies = self.commcell.organizations
        self.roles = self.commcell.roles
        self.plans = self.commcell.plans
        self.client_groups = self.commcell.client_groups
        self.pattern = self.tcinputs.get("pattern", "locust")
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword']
                       }
        self.locust_instance = locust_helper.Locust_Helper(self.inputs)

    def run(self):
        """Main function for test case execution"""
        entities = ["organizations", "users", "usergroups", "roles", "plans", "clientgroups", "storagepolicies"]
        for i in entities:
            self.locust_instance.delete_entities(i, pattern=self.pattern)