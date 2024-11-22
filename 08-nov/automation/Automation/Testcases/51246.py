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
    POST /drive/action/createfolder
    GET /drive/file/{{FOLDER_GUID}}
    GET /drive/action/metadata?path=\{{FolderName}}
    POST /drive/file/action/upload?uploadType=fullFile
    POST /drive/file/action/upload?uploadType=chunkedFile&forceRestart=true
    POST /drive/file/action/upload?uploadType=chunkedFile&requestId={{RequestId}}
    GET /drive/file/{{FILE1_GUID}}/action/download
    GET /drive/action/download?path=\DemoFolder\DemoFile1.doc
    GET /drive/file/{{FILE1_GUID}}/action/preview
    POST /drive/action/rename
    PUT /drive/file/{{FILE1_GUID}}/action/rename
    POST /drive/file/{{FILE1_GUID}}/properties
    GET /drive/file/{{FILE1_GUID}}/properties?propertyFilter=testproperty1
    DELETE /drive/properties
    POST /drive/tags
    GET /drive/file/{{FILE1_GUID}}/tags
    DELETE /drive/tags
    GET /drive/file/{{FILE1_GUID}}/versions
    GET /drive/file/versions?path=\{{FolderName}}\DemoFile1Renamed.doc
    GET /drive/file/version/{{versionId}}/action/download
    DELETE /drive/file/{{FILE1_GUID}}
    POST /drive/action/move
    PUT /drive/file/{{FILE2_GUID}}/action/move
    POST /drive/folder/{{RootGuid}}/action/search
    POST /drive/folder/{{RootGuid}}/action/list
    POST /drive/action/list?path=\
    POST /drive/action/delete
    DELETE /drive/file/{{FOLDER_GUID}}
    DELETE /drive/file/{{FILE2_GUID}}

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Edge Drive File and Folder Operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - JSON - Edge Drive File and Folder Operations"
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
            collection_json = 'EdgeDrive-FileandFolderOperations.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json},
                                     self.inputs, 3000)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
