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
    GET /drive/share
    GET /drive/share?shareId={{shareId}}
    POST /drive/share/{{shareId}}/action/createfolder
    POST /drive/share/{{shareId}}/file/{{FOLDERSHARE_GUID}}
    POST /drive/share/{{shareId}}/file/action/upload?uploadType=fullFile
    POST /drive/share/{{shareId}}/file/action/upload?uploadType=chunkedFile&forceRestart=true
    POST /drive/share/{{shareId}}/file/action/upload?uploadType=chunkedFile&requestId={{requestId}}
    POST /drive/file/{{SHAREFILE_GUID}}/action/share
    POST /drive/share/{{shareId}}/folder/{{FOLDERSHARE_GUID}}/action/list
    POST /drive/share/{{shareId}}/action/list?path=\
    POST /drive/share/{{shareId}}/folder/{{FOLDERSHARE_GUID}}/action/search
    POST /drive/share/{{shareId}}/action/search?path=\
    GET /drive/share/{{shareId}}/file/{{FOLDERSHARE_GUID}}
    GET /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}/versions
    GET /drive/share/{{shareId}}/file/versions?path=\DemoShareFolder\DemoFile1.doc
    GET /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}
    GET /drive/share/{{shareId}}/action/metadata?path=\DemoFile1.doc
    GET /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}/action/download
    GET /drive/share/{{shareId}}/action/download?path=\DemoFile1.doc
    GET /drive/share/{{shareId}}/file/version/{{SHAREFILE_GUID}}/action/download
    GET /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}
    GET /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}
    POST /drive/share/{{shareId}}/tags
    GET /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}/tags
    DELETE /drive/share/{{shareId}}/tags
    POST /drive/share/{{shareId}}/action/rename
    PUT /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}/action/rename
    POST /drive/share/{{shareId}}/action/move
    PUT /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}/action/move
    POST /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}/properties
    GET /drive/share/{{shareId}}/file/{{SHAREFILE_GUID}}/properties
    DELETE /drive/share/{{shareId}}/properties
    PUT /ShareFolder/{{shareId}}
    DELETE /drive/share/{{shareId}}/file/{{SHAREFOLDER2_GUID}}
    POST /drive/share/{{shareId}}/action/delete
    DELETE /ShareFolder/{{shareId}}
    DELETE /drive/file/{{FOLDERSHARE_GUID}}

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Edge Drive File and Folder Operations for Shares"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - JSON - Edge Drive File and Folder Operations for Shares"
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
            collection_json = 'EdgeDrive-FileandFolderOperationsforShares.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json},
                                     self.inputs, 3000)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
