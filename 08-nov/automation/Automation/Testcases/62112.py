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

    POST Login
    POST Create Company
    POST Create Tenant Admin
    GET Tenant User Properties
    POST Login as Tenant Admin
    GET Company Listing
    GET Company Details
    GET Tenant Admin Properties
    PUT Modify Created User
    POST Re-login as admin
    POST Deactivate Company
    DELETE Delete Company
    POST Try to create tenant user with deleted company
    GET Try to fetch tenant user of deleted company
    POST Logout



TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases
from AutomationUtils import config
import base64

class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Company User Operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API : Company User Operations (Tenant Admin)"
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
        config_json = config.get_config()
        self.server = ServerTestCases(self)
        if not config_json.PostmanVariables.userPassword:
            raise Exception("User password is not set")
        userPassword = base64.b64encode(config_json.PostmanVariables.userPassword.encode('utf-8')).decode('utf-8')
        self.server = ServerTestCases(self)
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword'],
                       "userPassword": userPassword
                       }


    def run(self):
        """Main function for test case execution"""

        try:
            collection_json = 'CompanyUserOperations.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, self.inputs)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
