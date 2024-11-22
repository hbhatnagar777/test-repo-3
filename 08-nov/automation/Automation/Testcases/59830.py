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
    GET CommServ
    GET CommServ/Anomaly/Entity/Count
    GET CommServ/Anomaly/Entity/Count?anomalousEntityType={0}
    GET office365/entities?agentType=4
    POST Cloud Library
    GET Library?libraryType=All
    DELETE Cloud Library
    POST Library?Action=detect
    POST Library?Action=configureTape
    POST Application
    PUT Plan/{0}/clients
    GET StoragePolicy/Infrastructurepool?planId={0}
    GET v2/Plan
    POST v2/Plan
    GET v2/Plan/{0}?propertyLevel=20
    DELETE Plan/{0}?confirmDelete=true&prune=true
    GET StoragePolicy
    GET V2/StoragePolicy/{0}/Copy/{1}
    GET StoragePolicy/{0}
    GET Subclient/{subclientId}
    POST Subclient/{subclientId}
    GET Subclient?clientId={0}&PropertyLevel=20&applicationId={1}&includeVMPseudoSubclients=false
    GET Subclient?clientId=0&PropertyLevel=20&applicationId=106&includeVMPseudoSubclients=false
    GET Client?propertylevel=20&filterOptions/allEntities=true
    GET Client?propertylevel=20&filterOptions/allEntities=true&
        extendedFilter/propertiesFilter/firewallConfiguration=true
    GET Client/byName(clientName='{clientName}')
    GET ClientGroup/byName(clientGroupName='{clientGroupName}')
    GET job/{0}
    GET Events?userId={0}&fromTime={1}&toTime={2}&
        showInfo={3}&showMinor={4}&showMajor={5}&showCritical={6}
    GET UsersAndGroups
    GET User?Level=50
    GET usergroup?level=10&flag=5
    GET StoragePool
    GET StoragePool/{0}
    POST StoragePool?Action=create

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases
from base64 import b64encode

class TestCase(CVTestCase):
    """Class for executing set of REST APIs for Metallic operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - Metallic Rest API Operations with JSON"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = False
        self.tcinputs = {
            "MAClientName": None,
            "BucketName": None,
            "ServiceHost": None,
            "AccessKey": None,
            "SecretKey": None,
            "VsaHypervisorClientName": None,
            "VsaClientUserName": None,
            "VsaClientPassword": None,
            "Office365Client": None,
            "ClientName": None,
            "LibraryName": None,
            "PlanName": None
        }
        self._restapi = None
        self.server = None
        self.inputs = None

    def setup(self):
        """Setup function of this test case"""
        self._restapi = RESTAPIHelper()
        self.server = ServerTestCases(self)
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword']
                       }
        self.tcinputs["SecretKey"] = b64encode(self.tcinputs["SecretKey"].encode()).decode()
        self.tcinputs["VsaClientPassword"] = b64encode(
                                        self.tcinputs["VsaClientPassword"].encode()).decode()
        self.inputs.update(self.tcinputs)

    def run(self):
        """Main function for test case execution"""

        try:
            collection_json = 'MetallicOperations.collection.json'
            # Start newman execution
            self._restapi.run_newman(
                {'tc_id': self.id, 'c_name': collection_json}, self.inputs, delay=500)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
