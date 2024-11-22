# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

API being validated inside collection file:

    GET Intent for NLP global search

Intent Categories being verified:

    ADD
    NAVIGATE
    EDIT
    CHECK READINESS
    VIEW JOBS
    SEND LOGS
    RESTORE
    INSTALL SOFTWARE
    UPGRADE/UNINSTALL SOFTWARE
    REPAIR SOFTWARE
    DOWNLOAD SOFTWARE
    BACKUP
    RETIRE
    RUN
    DELETE
    CHANGE COMPANY
    REPLICATION
    DEACTIVATE
    CLONE
    RELEASE LICENSE
    PUSH NETWORK CONFIGURATION
    RECONFIGURE
    INSTALL/UPGRADE/UNINSTALL VAIO
    COMMCELL ACTIONS (Entity independent)
    MISCELLANEOUS VIEW COMMANDS

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases

class TestCase(CVTestCase):
    """Class for executing set of REST APIs for NLP Global Search Intent mapping validation"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - NLP In Global Search"
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
            collection_json = 'NLPGlobalSearchCollection.collection.json'
            # Our api to test is at http://<webserver>/adminconsole/intent.do?command=
            endpoint_url = 'http://' + self.inputs["webserver"] + '/adminconsole'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json},
                                     self.inputs,
                                     custom_endpoint=endpoint_url,
                                     run_flags=["insecure"])

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
