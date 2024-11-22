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
    PUT /contentstore?type=testcontentstore
    POST /contentstore/file/{{RootGuid}}
    POST /contentstore/action/createfolder
    GET /contentstore/file/{{FOLDER_GUID}}
    GET /contentstore/action/metadata?path=\{{FolderName}}
    POST /contentstore/file/action/upload?uploadType=fullFile
    POST /contentstore/file/action/upload?uploadType=chunkedFile&forceRestart=true
    POST /contentstore/file/action/upload?uploadType=chunkedFile&requestId={{RequestId}}
    GET /contentstore/file/{{FILE1_GUID}}/action/download
    GET /contentstore/action/download?path=\DemoFolder\DemoFile1.doc
    GET /contentstore/file/{{FILE1_GUID}}/action/preview
    POST /contentstore/action/rename
    PUT /contentstore/file/{{FILE1_GUID}}/action/rename
    POST /contentstore/file/{{FILE1_GUID}}/properties
    GET /contentstore/file/{{FILE1_GUID}}/properties?propertyFilter=testproperty1
    DELETE /contentstore/properties
    POST /contentstore/tags
    GET /contentstore/file/{{FILE1_GUID}}/tags
    DELETE /contentstore/tags
    GET /contentstore/file/{{FILE1_GUID}}/versions
    GET /contentstore/file/versions?path=\{{FolderName}}\DemoFile1Renamed.doc
    GET /contentstore/file/version/{{versionId}}/action/download
    DELETE /contentstore/file/{{FILE1_GUID}}
    POST /contentstore/action/move
    PUT /contentstore/file/{{FILE2_GUID}}/action/move
    POST /contentstore/folder/{{RootGuid}}/action/search
    POST /contentstore/folder/{{RootGuid}}/action/search
    POST /contentstore/folder/{{RootGuid}}/action/list
    POST /contentstore/action/list?path=\
    POST /contentstore/action/delete
    DELETE /contentstore/file/{{SECONDFOLDER_GUID}}
    DELETE /contentstore/file/{{FOLDER_GUID}}

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for ObjectStore File and Folder Operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - JSON - ObjectStore File and Folder Operations"
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
            collection_json = 'ObjectStore-FileandFolderOperations.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json},
                                     self.inputs, 3000)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
