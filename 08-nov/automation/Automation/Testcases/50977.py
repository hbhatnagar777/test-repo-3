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
    GET Schedules
    POST Schedule Policy
    GET Schedule Properties
    GET Schedule Policies
    GET Schedule Policy Properties
    POST Schedule Disable
    POST Schedule Enable
    POST Schedule Policy Add Entity
    DELETE Schedule Policy Entity
    POST Schedule Policy Exclude Entity
    POST Schedule Policy Add Agent
    DELETE Schedule Policy Agent
    POST Schedule Pattern
    GET Task Details
    PUT Update Schedule Policy Entity/Agent Associations
    DELETE Schedule Policy

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Schedule and Schedule Policy Operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - Schedule and Schedule Policy Operations with JSON"
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
            collection_json = 'ScheduleandSchedulePolicyOperations.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, self.inputs)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
