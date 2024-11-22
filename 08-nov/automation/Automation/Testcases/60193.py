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

    POST http://{{CloudHostname}}/webconsole/api/Organization
    GET http://{{CloudHostname}}/webconsole/api/User/byName
        (userName='{{providerDomainName}}\{{providerDomainName}}')
    POST http://{{CloudHostname}}/webconsole/api/User/{{userId}}
    POST http://{{CloudHostname}}/webconsole/api/Login
    POST http://{{MSPHostname}}/webconsole/api/Login
    GET http://{{MSPHostname}}/webconsole/api/Commcell/MetaData
    GET http://{{CloudHostname}}/webconsole/api/CloudService/Routing?username={{CloudUser}}
    POST http://{{CloudHostname}}/webconsole/api/CloudService/Subscription
    POST http://{{MSPHostname}}/webconsole/api/CloudService/Subscription/Details
    GET http://{{MSPHostname}}/webconsole/api/CloudService/CompletedSetups
    GET http://{{MSPHostname}}/webconsole/api/Commcell/SamlToken
    GET http://{{CloudHostname}}/webconsole/api/GetUserMappings
    GET http://{{CloudHostname}}/webconsole/api/GetUserMappings
    GET http://{{CloudHostname}}/webconsole/api/Organization
    GET http://{{CloudHostname}}/webconsole/api/commserv
    GET http://{{CloudHostname}}/webconsole/api/user
    GET http://{{MSPHostname}}/webconsole/api/CloudServices/Registered
    GET http://{{MSPHostname}}/webconsole/api/Commcell/MetaData
    POST http://{{CloudHostname}}/webconsole/api/CloudService/Unsubscribe
    POST http://{{MSPHostname}}/webconsole/api/CloudService/Subscription/Details
    POST http://{{CloudHostname}}/webconsole/api/Organization/{{providerId}}/action/deactivate
    DELETE http://{{CloudHostname}}/webconsole/api/organization/{{providerId}}
    POST http://{{MSPHostname}}/webconsole/api/Logout
    POST http://{{CloudHostname}}/webconsole/api/Logout


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
    """Class for executing set of REST APIs for Neo"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("[Neo]: Linking, unlinking and redirection to metallic"
                     "services via REST api")
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = False
        self.tcinputs = {
            "CloudHostname": None,
            "CloudUser": None,
            "CloudPassword": None,
            "MSPHostname": None,
            "MSPUser": None,
            "MSPPassword": None
        }
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
        NewPassword = base64.b64encode(config_json.PostmanVariables.userPassword.encode('utf-8')).decode('utf-8')
        self.server = ServerTestCases(self)
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword'],
                       "CloudHostname": self.tcinputs['CloudHostname'],
                       "CloudUser": self.tcinputs['CloudUser'],
                       "CloudPassword": self.tcinputs['CloudPassword'],
                       "MSPHostname": self.tcinputs['MSPHostname'],
                       "MSPUser": self.tcinputs['MSPUser'],
                       "MSPPassword": self.tcinputs['MSPPassword'],
                       "NewPassword": NewPassword}

    def run(self):
        """Main function for test case execution"""

        try:
            collection_json = 'Neo_Metallic.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json},
                                     self.inputs)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
