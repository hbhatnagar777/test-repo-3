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
    GET /StoragePool
    POST /v2/Plan
    GET /v2/Plan
    GET /v2/Plan/{{planId}}
    GET /v2/Plan/{{planId}}
    PUT /v2/Plan/{{planId}}
    PUT /v2/Plan/{{planId}}/Users
    PUT /v2/Plan/{{planId}}/sla
    PUT /Plan/{{planId}}/Clients
    GET /v2/Plan/{{planId}}/Clients
    PUT /v2/Plan/{{planId}}/Alerts
    GET /Plan/43/Alerts?type=MSP&subType=Laptop&propertyLevel=10
    PUT /v2/Plan/{{planId}}/Options
    PUT /v2/Plan/{{planId}}/Storage/Modify
    GET /Plan/{{planId}}/Storage
    GET /Plan/{{planId}}/Features
    GET /v2/Plan/{{planId}}/Operations
    GET /v2/Plan/{{planId}}/AccessPolicies
    GET /v2/Plan/{{planId}}/EdgeDrive
    POST /Security
    GET /Security/158/{{planId}}
    GET /Plan/{{planId}}/Subclients
    DELETE /v2/Plan/{{planId}}?confirmDelete=true

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Plan operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - Plan Operations with JSON"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = False
        self._restapi = None
        self.server = None
        self.inputs = None

    def setup(self):
        """Setup function of this test case"""
        self._restapi = RESTAPIHelper()
        self.server = ServerTestCases(self)
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword']}

    def run(self):
        """Main function for test case execution"""

        try:
            collection_json = 'PlanOperations.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, self.inputs)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()