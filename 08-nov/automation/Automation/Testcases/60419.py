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

    PUT /v4/Commcell/Restore/Action/Disable?enableAfterADelay=-87580831
    PUT /v4/Commcell/Restore/Action/Enable
    PUT /v4/Commcell/Backup/Action/Disable?enableAfterADelay=1900063997
    PUT /v4/Commcell/Backup/Action/Enable
    PUT /v4/Commcell/Scheduler/Action/Disable?enableAfterADelay=1900063997
    PUT /v4/Commcell/Scheduler/Action/Enable
    PUT /v4/Commcell/DataAging/Action/Disable?enableAfterADelay=1900063997
    PUT /v4/Commcell/DataAging/Action/Enable
    PUT /v4/Commcell/DDB/Action/Disable?enableAfterADelay=1900063997
    PUT /v4/Commcell/DDB/Action/Enable
    PUT /v4/Commcell/DataVerification/Action/Disable?enableAfterADelay=1900063997
    PUT /v4/Commcell/DataVerification/Action/Enable
    PUT /v4/Commcell/AuxillaryCopy/Action/Disable?enableAfterADelay=1900063997
    PUT /v4/Commcell/AuxillaryCopy/Action/Enable
    PUT /v4/Commcell/ContentIndexing/Action/Disable?enableAfterADelay=1900063997
    PUT /v4/Commcell/ContentIndexing/Action/Enable
    PUT /v4/Commcell/AllJobActivity/Action/Disable?enableAfterADelay=1900063997
    PUT /v4/Commcell/AllJobActivity/Action/Enable

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs for PAPI Commcell Activity Control"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[PAPI] : Simplified Commcell Activity Control APIs"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = False

    def setup(self):
        """Setup function of this test case"""
        self._restapi = RESTAPIHelper()
        self.server = ServerTestCases(self)
        base_url = 'https://' + self.inputJSONnode['commcell']['webconsoleHostname'] + '/commandcenter/api/v4'
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword'],
                       "baseUrl": base_url}

    def run(self):
        """Main function for test case execution"""

        try:
            collection_json = 'PAPICommcellActivityControl.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, self.inputs)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
