# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import time

from Application.CloudApps.cloud_connector import CloudConnector
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Application.CloudApps import constants as cloud_apps_constants
from Reports.utils import TestCaseUtils
from Application.CloudApps.csdb_helper import CSDBHelper
from AutomationUtils import constants
from AutomationUtils.database_helper import MSSQL


class TestCase(CVTestCase):
    """
    Class for executing this test case
    """
    TestStep = TestStep()

    def __init__(self):
        """ Initializes test case class object """
        super().__init__()
        self.name = "OneDrive Licensing case"
        self.client_name = None
        self.cvcloud_object = None
        self.utils = TestCaseUtils(self)
        self.subclient_id = None
        self.client_id = None
        self.csdb_helper = None
        self.member_count = None
        self.db_helper = None

    @TestStep
    def _initialize_sdk_objects(self):
        """Initializes the sdk objects after client creation"""

        self.log.info(f'Create client object for: {self.client_name}')
        self._client = self.commcell.clients.get(self.client_name)

        self.log.info(f'Create agent object for: {cloud_apps_constants.ONEDRIVE_AGENT}')
        self._agent = self._client.agents.get(cloud_apps_constants.ONEDRIVE_AGENT)

        self.log.info(f'Create instance object for: {cloud_apps_constants.ONEDRIVE_INSTANCE}')
        self._instance = self._agent.instances.get(cloud_apps_constants.ONEDRIVE_INSTANCE)

        self.log.info(f'Create backupset object for: {cloud_apps_constants.ONEDRIVE_BACKUPSET}')
        self._backupset = self._instance.backupsets.get(cloud_apps_constants.ONEDRIVE_BACKUPSET)

        self.log.info(f'Create sub-client object for: {cloud_apps_constants.ONEDRIVE_SUBCLIENT}')
        self._subclient = self._backupset.subclients.get(cloud_apps_constants.ONEDRIVE_SUBCLIENT)

    @TestStep
    def run_discovery_wait(self):
        """
        Method run the discovery and wait till discovery gets completed
        """
        # Run discovery
        self.log.info(f'Running the discovery')
        self.subclient.run_subclient_discovery()

        self.log.info("Wait for discovery")
        self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

        # Verify discovery
        self.log.info(f'Verifying the discovery')
        status, res = self.subclient.verify_discovery_onedrive_for_business_client()
        if status:
            self.log.info("Discovery successful")
        else:
            raise Exception("Discovery is not successful")

    @TestStep
    def add_user_do_backup(self):
        """
        Method is used to add the user and perform backup
        """
        self.log.info("Adding the user for backup")
        self.subclient.add_users_onedrive_for_business_client(self.tcinputs["Users"], self.tcinputs["O365Plan"])

        self.log.info("User added successfully")
        self.log.info("starting the backup job")
        backup_job = self.client.backup_all_users_in_client()

        self.log.info(f"job id is: {backup_job.job_id}")
        self.log.info("Waiting for the job to complete..")
        backup_job.wait_for_completion()

        self.log.info("Backup completed ")

    @TestStep
    def update_lic_currentusage(self):
        """
        method run the script to upate the lic_currentusage table
        """

        query = ("DECLARE @isMasterSPRunning INT=0   SELECT @isMasterSPRunning = CONVERT(INT, value) "
                 "FROM GXGlobalParam WITH (NOLOCK) WHERE name = 'LicCalcUsageMasterSPRunning'  "
                 "IF @isMasterSPRunning = 1  BEGIN   WHILE @isMasterSPRunning = 1  "
                 "BEGIN WAITFOR DELAY '00:00:05' SET @isMasterSPRunning = 0  "
                 "SELECT @isMasterSPRunning = CONVERT(INT, value) FROM GXGlobalParam WITH (NOLOCK) "
                 "WHERE name = 'LicCalcUsageMasterSPRunning'  END  END  "
                 "ELSE   BEGIN   EXEC LicCalcUsageMaster @nCallerType = 2 END ")

        self.log.info("Executing the script to update lic_currentusage table")
        self.db_helper.execute(query)
        time.sleep(40)
        self.log.info("Script executed Successfully")

    @TestStep
    def get_cloudapp_user(self):
        """
        method is used to get the license user form the App_CloudAppUserDetails table
        """
        users = self.csdb_helper.get_cloudappuser_detail(subclient_id=self.subclient_id)
        self.log.info(users)

        if users == [['']]:
            raise Exception('There is no licensing user for the client')
        if len(users) != self.member_count:
            self.log.info(f" Users are {users}")
            raise Exception("All the Users does not get populated in the CloudAppsLicensingInfo Table "
                            "in CSDB ")
        return users

    @TestStep
    def get_user_from_lic_currentusage(self, check_for_empty_list=True):
        """
        verify if the user get populated in the lic_CurrentUsage table
        Args:
            check_for_empty_list(bool)         : if True return exception that list is empty

        Returns:
             users(list)                       : list of users
        """

        users = self.csdb_helper.get_lic_currentusage_user(client_id=self.client_id)
        self.log.info(users)
        if users == [['']] and check_for_empty_list:
            raise Exception("User not get populated in CSDB lic_CurrentUsage table")

        return users

    @TestStep
    def verify_users(self, users_currentusage=None, user_cloudapp=None):
        """
        Method is used to verify the same license user get populate in lic_curretUsage table and
        CloudAppLicensingInfo table in CSDB

        Args:
            users_currentusage(list)        : list of license users in lic_currentusage Table

            user_cloudapp(list)    : list of license users in App_CloudAppUserDetails Table

        """
        self.log.info("Sorting the users list")
        users_currentusage.sort()
        user_cloudapp.sort()
        self.log.info("Verifying if the user list are same")
        if user_cloudapp != users_currentusage:
            self.log.info(f"Users in lic_currentUsage table is {users_currentusage}")
            self.log.info(f"Users in CloudAppLicensingTable table is {user_cloudapp}")

            raise Exception("The user in both the CSDB table does not match")
        else:
            self.log.info("Test case successfully passed")

    @TestStep
    def deleting_client(self):
        """
        Method is used to delete the client and check if entry get removed from lic_CurrentUsage
        """
        self.log.info("Deleting the pseudo client ")
        self.commcell.clients.delete(client_name=self.client_name)
        self.update_lic_currentusage()
        lic_current_user = self.get_user_from_lic_currentusage(check_for_empty_list=False)
        self.log.info("Verifying if license user get removed from the lic_CurrentUsage table")
        if lic_current_user == [['']]:
            self.log.info("Teardown function completed Successfully ")
        else:
            self.log.info(f"user present in table {lic_current_user}")
            self.log.info("User does not get removed from lic_CurrentUsage table in CSDB")

    def setup(self):
        """
        Setup function of this test case
        """
        self.log.info("setup function of the case")
        self.client_name = "OD_70633"
        self.log.info(f'Checking if OneDrive client : {self.client_name} already exists')
        if self.commcell.clients.has_client(self.client_name):
            self.log.info(f'OneDrive client : {self.client_name} already exists, deleting the client')
            self.commcell.clients.delete(self.client_name)
            self.log.info(f'Successfully deleted OneDrive client : {self.client_name} ')
        else:
            self.log.info(f'OneDrive client : {self.client_name} does not exists')
        self.log.info(f'Creating new OneDrive client : {self.client_name}')
        self.commcell.clients.add_onedrive_for_business_client(client_name=self.client_name,
                                                     server_plan=self.tcinputs.get('ServerPlanName'),
                                                     azure_directory_id=self.tcinputs.get("azure_directory_id"),
                                                     azure_app_id=self.tcinputs.get("application_id"),
                                                     azure_app_key_id=self.tcinputs.get("application_key_value"),
                                                     **{
                                                         'index_server': self.tcinputs.get('IndexServer'),
                                                         'access_nodes_list': [self.tcinputs.get('AccessNode')]
                                                     })

        # Verify client creation
        if self.commcell.clients.has_client(self.client_name):
            self.log.info("Client is created.")

        self._initialize_sdk_objects()
        self.client_id = self.client.client_id
        self.subclient_id = self.subclient.subclient_id
        self.log.info(f"client id : {self.client_id} and subclient id : {self.subclient_id}")
        self.cvcloud_object = CloudConnector(self)
        self.csdb_helper = CSDBHelper(self)
        self.db_helper = MSSQL(self.tcinputs["sqlInstanceName"],
                               self.tcinputs["SqlUserName"],
                               self.tcinputs["SqlPassword"],
                               "CommServ")
        self.member_count = int(self.tcinputs["MemberCount"])

    def run(self):
        """ Main function for test case execution """
        try:
            self.log.info("Executing run function of the testcase")
            self.run_discovery_wait()
            self.add_user_do_backup()
            self.run_discovery_wait()

            cloudappuser = self.get_cloudapp_user()
            self.update_lic_currentusage()

            lic_current_user = self.get_user_from_lic_currentusage()
            self.verify_users(users_currentusage=lic_current_user, user_cloudapp=cloudappuser)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ Teardown function of this test case """
        self.log.info("Executing tear down function")
        if self.status == constants.PASSED:
            self.log.info("Testcase passed")
            self.deleting_client()
        else:
            self.log.info("Testcase failed")
