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
    #User token APIs
    POST   {{ServerURL}}/ApiToken/User
    GET    {{ServerURL}}/ApiToken/User/{{userId}}
    PUT    {{ServerURL}}/ApiToken/User/Session/{{sessionId}}
    DELETE {{ServerURL}}/ApiToken/User/Session/{{sessionId}}

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing REST APIs for a user Access token"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Manage Authtokens for a user using REST APIs"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = False
        self.tcinputs = {
            "userId": None,
            "ServerURL2": None
        }
        self._restapi = None
        self.server = None
        self.inputs = None

    def setup(self):
        """Setup function of this test case"""
        self._restapi = RESTAPIHelper()
        self.server = ServerTestCases(self)
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword'],
                       "userId": self.tcinputs['userId'],
                       "ServerURL2": self.tcinputs['ServerURL2']}

    def run(self):
        """Main function for test case execution"""
        try:
            collection_json = 'AccessToken.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json},
                                     self.inputs)
        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()