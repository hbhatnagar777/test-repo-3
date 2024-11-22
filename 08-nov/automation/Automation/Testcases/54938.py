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

    GET /User/byName(userName='{{username}}')

    GET /UserGroup/byName(userGroupName='{{usergroup}}')

    GET /Client/byName(clientName='{{clientname}}')

    GET /instance/byName(clientName='{{clientname}}',appName=
    'Windows File System'),instanceName='DefaultInstanceName')

    POST /Client/byName(clientName='{{clientname}}')

    POST /Subclient/byName(clientName='{{clientname}}',appName=
    '{{appname}}',backupsetName='{{backupsetname}}',subclientName='{{subclientname}}')

    POST /User/byName(userName='{{username}}')

    DELETE /User/byName(userName='{{username}}')?newUserId=byName(userName=
    'admin')&newUserGroupId=byName(userGroupName='')

    POST /UserGroup/byName(userGroupName='{{userGroupName}}')

    DELETE /UserGroup/byName(userGroupName='{{userGroupName}}')?newUserId=
    byName(userName='admin')&newUserGroupId=byName(userGroupName='')

    POST /backupset/byName(clientName='{{ClientName}}',appName=
    'File System',backupsetName='{{NewbackupsetName_2}}')

    POST /Backupset/byName(clientName='{{ClientName}}',appName=
    'File System',backupsetName='{{backupsetName}}')/action/backup

    DELETE /Backupset/byName(clientName='{{ClientName}}',appName=
    'File System',backupsetName='{{backupsetName}}')

    POST /Subclient/byName(clientName='{{clientname}}',appName=
    'File System',backupsetName='defaultBackupSet',subclientName='{{subclientName}}')
    /action/backup?backupLevel=Synthetic_Full&runIncrementalBackup=True&incrementalLevel=BEFORE_SYNTH

    DELETE /Subclient/byName(clientName='{{clientname}}',appName='File System',
    backupsetName='defaultBackupSet',subclientName='{{subclientName}}')

TestCase:
    __init__()      --  initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases
from AutomationUtils import config
import base64

class TestCase(CVTestCase):
    """Class for executing set of REST APIs supporting names"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - JSON - Validation of byName APIs"
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
        config_json = config.get_config()
        self.server = ServerTestCases(self)
        if not config_json.PostmanVariables.userPassword:
            raise Exception("User password is not set")
        userpassword = base64.b64encode(config_json.PostmanVariables.userPassword.encode('utf-8')).decode('utf-8')
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword'],
                       "userPassword": userpassword,
                       "path": self.tcinputs['path']}

    def run(self):
        """Main function for test case execution"""

        try:
            collection_json = 'ByNameAPIs.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, self.inputs)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
