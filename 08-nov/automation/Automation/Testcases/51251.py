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
    POST /contentstore/action/share
    GET /contentstore/share
    GET /contentstore/share?shareId={{shareId}}
    POST /contentstore/share/{{shareId}}/action/createfolder
    POST /contentstore/share/{{shareId}}/file/{{FOLDERSHARE_GUID}}
    POST /contentstore/share/{{shareId}}/file/action/upload?uploadType=fullFile
    POST /contentstore/share/{{shareId}}/file/action/upload?uploadType=chunkedFile&forceRestart=true
    POST /contentstore/share/{{shareId}}/file/action/upload?uploadType=chunkedFile&requestId={{requestId}}
    POST /contentstore/file/{{SHAREFILE_GUID}}/action/share
    POST /contentstore/share/{{shareId}}/folder/{{FOLDERSHARE_GUID}}/action/list
    POST /contentstore/share/{{shareId}}/action/list?path=\
    POST /contentstore/share/{{shareId}}/folder/{{FOLDERSHARE_GUID}}/action/search
    POST /contentstore/share/{{shareId}}/action/search?path=\
    GET /contentstore/share/{{shareId}}/file/{{FOLDERSHARE_GUID}}
    GET /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}/action/preview
    GET /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}
    GET /contentstore/share/{{shareId}}/action/metadata?path=\DemoFile1.doc
    GET /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}/action/download
    GET /contentstore/share/{{shareId}}/action/download?path=\DemoFile1.doc
    GET /contentstore/share/{{shareId}}/file/version/{{SHAREFILE_GUID}}/action/download
    GET /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}
    GET /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}
    POST /contentstore/share/{{shareId}}/tags
    GET /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}/tags
    DELETE /contentstore/share/{{shareId}}/tags
    POST /contentstore/share/{{shareId}}/action/rename
    PUT /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}/action/rename
    POST /contentstore/share/{{shareId}}/action/move
    PUT /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}/action/move
    POST /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}/properties
    GET /contentstore/share/{{shareId}}/file/{{SHAREFILE_GUID}}/properties
    DELETE /contentstore/share/{{shareId}}/properties
    PUT /ShareFolder/{{shareId}}
    DELETE /contentstore/share/{{shareId}}/file/{{SHAREFOLDER2_GUID}}
    POST /contentstore/share/{{shareId}}/action/delete
    DELETE /ShareFolder/{{shareId}}
    DELETE /contentstore/file/{{FOLDERSHARE_GUID}}

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for ObjectStore File and Folder Operations for Shares"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - JSON - ObjectStore File and Folder Operations for Shares"
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
            collection_json = 'ObjectStore-FileandFolderOperationsforShares.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json},
                                     self.inputs, 3000)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
