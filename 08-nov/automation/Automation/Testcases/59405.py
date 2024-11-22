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

            POST /Login
            GET /SaveAsyncProcProgress
            GET /isAwsSignatureValid
            POST /RenewLoginToken
            GET /getOemId
            POST /getOemId
            GET /getDomains
            POST /getDomains
            POST /RegisterUser
            POST /ResetPassword
            POST /doWebSearch
            POST /Stream/doWebSearch/CaseManager
            GET /getUserNameForLegacyDN
            GET /GetCSVersion
            POST /GetCSVersion
            POST /ChangeExpiredPassword
            GET /Recall
            GET /Stream/Recall
            POST /SendEmail
            POST /getComplianceSearchUrls
            POST /getDocumentationLink
            POST /GetUserRegistrationFlag
            POST /GetfeedbackURL
            POST /SetEULAFlag
            POST /getStats
            POST /FetchGUID
            POST /UpdateItems
            POST /DeleteItems
            POST /InsertNewItems
            GET /getUserSmtp
            POST /EraseItems
            POST /PruneDeletedItems
            POST /ProcessCollect
            POST /DeleteCollectResponse
            POST /PollCollectStatus
            POST /RestoreDeletedItems
            POST /CloudConnector/Application/Login
            POST /CloudConnector/Application/Open
            GET /getWADomains
            GET /getWAEngineURL
            POST /ThirdParty/SAML/App
            GET /MobileDevices
            GET /MobileActions
            POST /MobileActions
            POST /addWAData
            POST /CopyToRSolr
            GET /getCommServTimeTimeZone
            POST /getCommServTimeTimeZone
            POST /isMetricsAccessible
            GET /getWebPrintStatus
            GET /GetAllowedAppTypesForAdminDelete
            POST /ProcessRetentionRules
            POST /UpdateMetadata
            POST /UpdatePath
            GET /getWebServiceMaxConnections
            GET /GetFolders
            POST /user/Password/ForgotRequest
            POST /user/Password/Forgot
            GET /cache/metaInfo
            GET /cache/refresh
            GET /cache/removekeys
            POST /cache/dump
            POST /SoftwareStoreItem
            GET /GetCustomerLicenseUsage
            GET /RegisterProxy
            GET /getADUsersOfGroup
            POST /ProcessExchangeIdxRetentionRules
            POST /SubmitTransaction
            POST /DeleteProperties
            POST /InsertExtents
            POST /IndexContentForEdge
            GET /GetVersionInfo
            POST /CreateCITask
            POST /EndCITask
            POST /DoCITask
            GET /Commcell/SSO/OpenId/Redirect
            GET /MQ/ConnectString
            GET /Discussion/Enabled
            GET /dblayer/GetDelimiter
            GET /dblayer/GetBulkDeleteThreshold
            GET /dblayer/GetEdgeDriveSubClient
            GET /dblayer/GetCaseSensitivity
            GET /dblayer/GetEnablePermissionCheck
            GET /dblayer/GetIndexingClientType
            POST /dblayer/GetCIServer
            GET /dblayer/GetPublicSharingUserId
            GET /dblayer/GetGroupIdsOfUser
            GET /Commcell/CloudRegistration
            POST /Commcell/CloudRegistration
            POST /ProcessExchangeIdxReparation
            GET /UsernameByEmail
            POST /dcube/syncdsstatus
            POST /EraseByQuery
            POST /indexing/uns/collection
            POST /indexing/uns/role/collection
            POST /indexing/uns/collection/batch
            POST /Stream/ExportSearchResults
            POST /LoginToWebClientUsingWebConsole
            POST /indexing/uns/import
            POST /uns/DeleteDocuments
            GET /Security/TwoFactorAuth/Pin
            GET /Security/TwoFactorAuth/Status
            POST /PopulateExchangeIdxStats
            GET /ThirdParty/CAS/App
            POST /Office365/ProcessIdxRetentionRules
            POST /Office365/PopulateIdxStats
            POST /ConvertBrowseRequest
            GET /help
            GET /GetReadmePreview
            POST /RegisterClient
            POST /download/postprocess
            HEAD /ServiceCommcell/WebPackage
            GET /ServiceCommcell/WebPackage
            GET /multicommcell/CommcellType
            POST /Job/action/oncomplete
            POST /ContentIndexing/ProcessPreviewRetention
            GET /indexing/OperationStatus
            POST /indexing/uns/deletecollection
            GET /CloudService/Routing
            GET /CommcellRedirect/isEnabled
            GET /CommcellRedirect/RedirectListForUser
            GET /CommcellRedirect/Multicommcell
            #region diagnostic APIs
            GET /Status
            POST /Status
            GET /WebServiceStatus
            POST /WebServiceStatus
            GET /ShareFolderStatus/[0-9]+
            GET /CommServ/LongUrl/.+
            POST /Test/Echo
            GET /Test/EchoString/.+
            GET /stream/publicshare/.+
            GET /publicshare/.+
            GET /drive/publicshare/.+
            GET /contentstore/publicshare/.+
            POST /publicshare/.+
            POST /drive/publicshare/.+
            POST /contentstore/publicshare/.+
            GET /CvaccountsUrl
            POST /User/[0-9]+/ChangeExpiredPassword
            POST /ChangeExpiredPassword
            GET /cvauth/.+
            POST /cvauth/.+

TestCase:
    __init__()      --  initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing set of REST APIs which doesn't require authentication"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REST API - Validation of unauthenticated APIs"
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
        self.server = ServerTestCases(self)
        self.inputs = {"webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
                       "username": self.inputJSONnode['commcell']['commcellUsername'],
                       "password": self.inputJSONnode['commcell']['commcellPassword']}

    def run(self):
        """Main function for test case execution"""

        try:
            collection_json = 'UnauthenticatedAPIs.collection.json'
            # Start newman execution
            self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, self.inputs)

        except Exception as excp:
            self.server.fail(excp)

        finally:
            self._restapi.clean_up()
