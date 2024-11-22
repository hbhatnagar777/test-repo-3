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
    POST /drive/action/share
    POST /drive/share/{{shareId}}/file/action/upload?uploadType=fullFile
    GET /drive/publicshare/{{shareId}}/action/metadata?path=\DemoFile1.doc
    GET /drive/publicshare/{{shareId}}/file/{{PUBLICSHAREFILE_GUID}}/action/preview
    GET /drive/publicshare/{{shareId}}/action/preview?path=\DemoFile1.doc
    GET /drive/publicshare/{{shareId}}/action/download?path=\DemoFile1.doc
    GET /drive/publicshare/{{shareId}}/action/metadata?path=\DemoFile1.doc
    GET /drive/publicshare/{{shareId}}/file/version/{{versionId}}/action/preview
    GET /drive/publicshare/{{shareId}}/file/version/{{versionId}}/action/download
    POST /drive/share/{{shareId}}/file/{{PUBLICSHAREFILE_GUID}}/properties
    GET /drive/publicshare/{{shareId}}/file/{{PUBLICSHAREFILE_GUID}}/properties
    DELETE /drive/share/{{shareId}}/properties
    POST /drive/share/{{shareId}}/tags
    GET /drive/publicshare/{{shareId}}/file/{{PUBLICSHAREFILE_GUID}}/tags
    DELETE /drive/share/{{shareId}}/tags
    DELETE /ShareFolder/{{shareId}}
    DELETE /drive/file/{{PUBLICSHAREFOLDER_GUID}}

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Edge Drive File and Folder Operations
    for Public Shares"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - JSON - Edge Drive File and Folder Operations for Public Shares"
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
            collection_json = 'EdgeDrive-FileandFolderOperationsforPublicShares.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json},
                                     self.inputs, 3000)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
