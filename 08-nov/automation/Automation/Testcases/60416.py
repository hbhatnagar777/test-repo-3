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
    GET /v4/EmailServer
    POST /v4/EmailServer
    POST /v4/EmailServer/Action/Test
    PUT /v4/EmailServer


TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases
from AutomationUtils import config


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for PAPI Email Server"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[PAPI] : Simplified Email Server APIs"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = False

    def setup(self):
        """Setup function of this test case"""
        self._restapi = RESTAPIHelper()
        self.server = ServerTestCases(self)
        config_json = config.get_config()
        if not config_json.PostmanVariables.smtpHostname:
            raise Exception("Variables not set")
        smtpHostname = config_json.PostmanVariables.smtpHostname
        base_url = 'https://' + self.inputJSONnode['commcell']['webconsoleHostname'] + '/commandcenter/api/v4'
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword'],
                       "baseUrl": base_url,
                       "smtpHostname": smtpHostname}

    def run(self):
        """Main function for test case execution"""

        try:
            collection_json = 'PAPIEmailServer.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, self.inputs)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()