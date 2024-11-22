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
from Application.CloudApps.csdb_helper import CSDBHelper
from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from AutomationUtils import constants
from AutomationUtils.database_helper import MSSQL


class TestCase(CVTestCase):
    """
       Class for Retention verification of Active Directory
    """
    TestStep = TestStep()

    def __init__(self):
        """ Initializes test case class object """
        super().__init__()
        self.name = "SharePoint Licensing case"
        self.client_name = None
        self.sp_client_object = None
        self.client_id = None
        self.backupset_id = None
        self.csdb_helper = None
        self.utils = TestCaseUtils(self)
        self.member_count = None
        self.db_helper = None

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.office_365_plan = [(self.tcinputs.get('Office365Plan'),
                                                      int(self.sp_client_object.cvoperations.get_plan_obj
                                                          (self.tcinputs.get('Office365Plan')).plan_id))]
            self.sp_client_object.site_url = self.tcinputs.get("SiteUrl", "")
            self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
            self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
            self.log.info('SharePoint client object created.')
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @TestStep
    def get_user_from_cloudapplicensing(self):
        """
        Verify if license user data get populated in CSDB

        Returns:
            users(list)      : List of users
        """

        users = self.csdb_helper.get_cloudappslicensing_user(backupset_id=self.backupset_id)
        self.log.info(users)
        if users == [['']]:
            raise Exception("User not get populated in CSDB CloudAppLicensing Table")

        if len(users) != self.member_count:
            self.log.info(f" Users are {users}")
            raise Exception("All the members of the site does not get populated in the CloudAppsLicensingInfo Table "
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
            raise Exception("User not get populated in CSDB CloudAppLicensing Table")

        return users

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
    def verify_users(self, users_currentusage=None, user_cloudapplicensing=None):
        """
        Method is used to verify the same license user get populate in lic_curretUsage table and
        CloudAppLicensingInfo table in CSDB

        Args:
            users_currentusage(list)        : list of license users in lic_currentusage Table

            user_cloudapplicensing(list)    : list of license users in CloudAppsLicensingInfo Table

        """
        self.log.info("Sorting the users list")
        users_currentusage.sort()
        user_cloudapplicensing.sort()
        self.log.info("Verifying if the user list are same")
        if user_cloudapplicensing != users_currentusage:
            self.log.info(f"Users in lic_currentUsage table is {users_currentusage}")
            self.log.info(f"Users in CloudAppLicensingTable table is {user_cloudapplicensing}")

            raise Exception("The user in both the CSDB table does not match")
        else:
            self.log.info("Test case successfully passed")

    @TestStep
    def deleting_client(self):
        """
        Method is used to delete the client and check if entry get removed from lic_CurrentUsage
        """
        self.log.info("Deleting the pseudo client ")
        self.sp_client_object.cvoperations.delete_share_point_pseudo_client(client_name=self.client_name)
        self.update_lic_currentusage()
        lic_current_user = self.get_user_from_lic_currentusage(check_for_empty_list=False)
        self.log.info("Verifying if license user get removed from the lic_CurrentUsage table")
        if lic_current_user == [['']]:
            self.log.info("Teardown function completed Successfully ")
        else:
            self.log.info(f"user present in table {lic_current_user}")
            self.log.info("User does not get removed from lic_CurrentUsage table in CSDB")

    @TestStep
    def run_license_collection(self):
        """
        Run the license collection job and wait for job to complete

        """
        try:

            self.sp_client_object.cvoperations.subclient.refresh_license_collection()
            query = (f"select cast(cast(attrVal as varchar(max)) as xml)."
                     "value('(App_LicensingCollectionState)[1]/@licensingStatus', 'BIGINT')"
                     "from APP_BackupSetProp(nolock) where attrName = 'SharePoint License Collection State' and "
                     f"modified = 0 and componentNameId = '{self.backupset_id}'")

            current_time = time.time()
            end_time = current_time + 2000

            while current_time <= end_time:

                self.log.info("verifying the license collection process get completed")
                self.csdb.execute(query)
                output = self.csdb.fetch_all_rows()

                if output[0][0] == '2':
                    self.log.info("license collection process get completed")
                    return
                self.log.info("wait for [60] Seconds before next try")
                time.sleep(60)

            self.log.info("The license collection process does not get completed within 30 minutes ")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    @TestStep
    def add_user_run_backup(self):
        """
        Method is used to add the site and run the backup job
        """
        # Adding the site for backup
        self.sp_client_object.cvoperations.browse_for_sp_sites()
        self.sp_client_object.cvoperations.associate_content_for_backup(
            self.sp_client_object.office_365_plan[0][1])

        # Running the backup job
        self.log.info("running the backup job")
        self.sp_client_object.cvoperations.run_backup()

    def setup(self):
        self.log.info("executing the setup function")
        self.init_tc()

        # creating a sharepoint pseudo client
        self.sp_client_object.cvoperations.add_share_point_pseudo_client()

        # getting the backupset and client id
        self.log.info("Getting the client_id and backupset_id")
        self.client_id = int(self.sp_client_object.cvoperations.client.client_id)
        self.backupset_id = int(self.sp_client_object.cvoperations.backupset.backupset_id)
        self.log.info(f"client_id: {self.client_id} and backupset_id: {self.backupset_id}")
        self.csdb_helper = CSDBHelper(self)
        self.db_helper = MSSQL(self.tcinputs["sqlInstanceName"],
                               self.tcinputs["SqlUserName"],
                               self.tcinputs["SqlPassword"],
                               "CommServ")
        self.member_count = int(self.tcinputs["MemberCount"])
        self.client_name = self.tcinputs["PseudoClientName"]

    def run(self):
        """ Main function for test case execution """
        try:
            self.log.info("executing run function of the testcase")

            self.add_user_run_backup()

            # Running the manual discovery
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)

            # Running the license collection job
            self.log.info("Running the license status update job")

            self.run_license_collection()
            # getting the user form the CloudAppLicensingInfo Table
            cloud_appuser = self.get_user_from_cloudapplicensing()

            self.update_lic_currentusage()

            lic_current_user = self.get_user_from_lic_currentusage()

            self.verify_users(users_currentusage=lic_current_user, user_cloudapplicensing=cloud_appuser)

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
