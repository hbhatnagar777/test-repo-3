# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

r""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

APIs being validated inside collection file:
    GET /drive
    POST /drive/file/{{RootGuid}}
    POST /drive/file/{{FILE_GUID}}/Discussion
    POST /drive/file/{{FILE_GUID}}/Discussion/{{discussionId}}/Comment
    GET /drive/file/{{FILE_GUID}}/Discussion?depth=0
    GET /drive/file/{{FILE_GUID}}/Discussion/{{discussionId}}?depth=0
    GET /drive/file/{{FILE_GUID}}/Discussion/{{discussionId}}/Comment/{{commentId}}
    GET /drive/file/{{FILE_GUID}}/Discussion/{{discussionId}}/Comment/{{commentId}}/Replies?depth=0
    PUT /drive/file/{{FILE_GUID}}/Discussion/{{discussionId}}/Comment/{{commentId}}
    DELETE /drive/file/{{FILE_GUID}}/Discussion/{{discussionId}}/Comment/{{commentId}}
    DELETE /drive/file/{{FILE_GUID}}/Discussion/{{discussionId}}
    DELETE /drive/file/{{FILE_GUID}}

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Edge drive discussion Operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - JSON - Edge Drive Discussion Operations"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = False
        self.tcinputs = {
            "Username": None,
            "Password": None
        }
        self._restapi = None
        self.server = None
        self.inputs = None

    def setup(self):
        """Setup function of this test case"""
        self._restapi = RESTAPIHelper()
        self.server = ServerTestCases(self)
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.tcinputs['Username'],
                       "password": self.tcinputs['Password']}

    def run(self):
        """Main function for test case execution"""

        try:
            collection_json = 'EdgeDrive-DiscussionOperations.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json},
                                     self.inputs, 1000)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
