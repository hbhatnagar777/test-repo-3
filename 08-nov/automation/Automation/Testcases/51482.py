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
    POST /CommServ/MetricsReporting
    GET  /CommServ/MetricsReporting?isPrivateCloud=False
    POST /CommServ/CustomCalendar
    GET /CommServ/CustomCalendar
    POST /CommServ/CustomCalendar (deletion)
    POST /EmailServer
    GET /EmailServer
    GET /CommServ/DataInterfacePairs/HostInterfaces?hostId={{clientId}}
    GET /Commcell/InternetOptions/Proxy
    POST /Commcell/InternetOptions/Proxy
    GET /Commcell/InternetOptions/Proxy
    POST /OperationWindow
    GET /OperationWindow/OpWindowList?clientId={{clientId}}
    DELETE /OperationWindow/{{ruleId}}
    POST /CommServ/SNMPV3Configuration
    GET /CommServ/SNMPV3Configuration
    POST /CommServ/SNMPV3Configuration (deletion)
    POST /CommServ/AuditTrail
    GET /CommServ/AuditTrail
    POST /CommServ/JobManagementSetting
    GET  /CommServ/JobManagementSetting

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Control Panel Options"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - Control Panel Options with JSON"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = False

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
            collection_json = 'ControlPanelOptions.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, self.inputs)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
