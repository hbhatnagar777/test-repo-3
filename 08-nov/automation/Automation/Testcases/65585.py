# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" This test case is for WORM enabled cloud Storage (object lock).

Prerequisite-> Cloud storage account (object lock) credentials should be already saved

TestCase: Class for executing this test case

    __init__()      -- Initializing the Test case file

    init_tc()       -- Initial configuration for the test case

    setup()         -- Initializes pre-requisites for this test case

    validate_plan_deletion() -- Validates if the plan is deleted or not

    validate_storage_deletion() -- Validates if the storage is deleted or not

    delete_plan()    -- Deletes the plan with the given name

    delete_storage()    -- Deletes the storage with the given name

    cleanup()            -- Cleaning up entities created by testcase

    create_cloud_storage() -- creates a new cloud storage

    validate_storage_creation() -- validates whether a cloud storage is created or not

    enable_worm_lock() -- enables the worm lock on storage

    verify_flag_values_storage() -- verifies csdb flag values for storage after enabling worm

    create_server_plan() -- creates a new server plan

    validate_plan_creation() -- Validates if the plan is created or not

    verify_flag_values_plan() -- verifies the csdb flag values of plan

    set_retention_on_storage() -- sets retention on storage pool

    set_retention_on_plan() -- sets retention on plan

    run()           --  run function of this test case

Sample Input JSON:
        {
          "ClientName": Name of the Client (str),
          "MediaAgent": Name of the mediaAgent (str),
          "CloudType": Name of the cloud vendor (str),
          "CloudServerName": Name of the server host (str)
                            for example:- In case of Azure(vendor), the server host is - "blob.core.windows.net",
          "CloudContainer": Name of the cloud container (str),
          "StorageClass": - Depends on the cloud vendor (str), if mandatory, then provide
                        Refer https://documentation.commvault.com/v11/essential/supported_cloud_storage_products.html
          "CloudCredentials": Name of the cloud credentials (str) - name by which it is already saved
          "Authentication": Depends on the cloud vendor (str), if mandatory, then provide
                            Authentication type to be used for authenticating the storage account (str)
          "accountName": In case of azure , if authentication is "IAM AD application" / "IAM VM Role"
          "region": Depends on the cloud vendor (str), if mandatory, then provide
                    Name of the geographical region for storage,
          "cloud_ddb_path": Cloud Ddb location for case-1 and case-2 storage for unix MA
                            (required - if the MA provided is Unix/Linux, else optional)


             *****In case of Unix/Linux MA, provide LVM enabled dedup paths*****
        }

Steps:

    Case1:
        Create a storage pool with deduplication enabled
        Enable worm, set retention of 1 day.
        Check DB for the worm copy flag, storage is marked with object lock flag, micro pruning is disabled
        and seal frequency is set as per retention on pool ( in this case it should be 7 days).
        Create first copy associated to the pool.
        Ensure copy creation is successful, worm copy flag is set and override retention is not set on the copy.

    Case2:
        Create a storage pool with deduplication enabled
        Associate a copy to it and set retention value of 30 days.
        Enable H/w worm on the pool and set retention as 1 day.
        Check DB for the worm copy flag, storage is marked with object lock flag, micro pruning is disabled
        and seal frequency is set as per retention on pool (7 days in this case).
        Ensure copy is marked with worm copy flag and override retention is not set on the copy, also the
        retention value should be updated to pool retention i.e. 1D.

    Case3:
        Create a non-dedupe pool
        Associate a Copy to it.
        Enable hardware WORM and ensure no seal frequency is set and micro pruning is disabled on the mountpath(s).
        Try increasing retention it should be not allowed on pool but only dependant copies.
        Reduce retention; it should return an error.

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVWebAutomationException
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()

        self.name = "Acceptance WORM Object Lock config only -- CC"
        self.browser = None
        self.admin_console = None
        self.rmodal_dialog = None
        self.storage_helper = None
        self.mm_helper = None
        self.plans_page = None
        self.plan_helper = None
        self.client_machine = None
        self.ma_machine = None
        self.path = None
        self.retention_dict = None
        self.ddb_location1 = None
        self.ddb_location2 = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent": None,
            "CloudType": None,
            "CloudServerName": None,
            "CloudContainer": None
        }
        self.storage_name3 = None
        self.storage_name2 = None
        self.storage_name1 = None
        self.plan_name1 = None
        self.plan_name2 = None
        self.plan_name3 = None
        self.storage_dict1 = None
        self.storage_dict2 = None
        self.storage_dict3 = None
        self.isWormEnabledFlag = None
        self.overrideRetentionFlag = None
        self.isObjectWormEnabledFlag = None
        self.RetentionDays = None
        self.PlanRetentionDays2 = None
        self.PlanRetentionDays3 = None
        self.expected_error_str = None
        self.authentication = None
        self.storageClass = None
        self.region = None
        self.dedup_provided = False
        self.cred_details = {}
        self.creds = None

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.init_tc()
        self.isWormEnabledFlag = 16777216
        self.overrideRetentionFlag = 0
        self.isObjectWormEnabledFlag = 8388608
        self.RetentionDays = "1"
        self.PlanRetentionDays2 = "30"
        self.PlanRetentionDays3 = "15"
        self.expected_error_str = "Reducing the basic or extended retention of a worm storage policy copy is not allowed."
        self.storage_helper = StorageMain(self.admin_console)
        self.plan_helper = PlanMain(self.admin_console, commcell=self.commcell)
        self.plans_page = Plans(self.admin_console)
        self.rmodal_dialog = RModalDialog(self.admin_console)
        options_selector = OptionsSelector(self.commcell)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent'])
        self.storage_name1 = f"Worm-Cloud-1-{self.id}"
        self.storage_name2 = f"Worm-Cloud-2-{self.id}"
        self.storage_name3 = f"Worm-Cloud-3-{self.id}"
        self.plan_name1 = f"Worm-Plan-1-{self.id}"
        self.plan_name2 = f"Worm-Plan-2-{self.id}"
        self.plan_name3 = f"Worm-Plan-3-{self.id}"
        self.storage_dict1 = {'pri_storage': self.storage_name1}
        self.storage_dict2 = {'pri_storage': self.storage_name2, 'pri_ret_period': self.PlanRetentionDays2,
                              'ret_unit': 'Day(s)'}
        self.storage_dict3 = {'pri_storage': self.storage_name3, 'pri_ret_period': self.PlanRetentionDays3,
                              'ret_unit': 'Day(s)'}

        if self.tcinputs.get("cloud_ddb_path"):
            self.dedup_provided = True

        if "unix" in self.ma_machine.os_info.lower():
            if self.dedup_provided:
                self.log.info('Unix/Linux MA provided, assigning user defined dedup locations')
                self.ddb_location1 = self.tcinputs["cloud_ddb_path"]
                self.ddb_location2 = self.tcinputs["cloud_ddb_path"]
            else:
                self.log.error(
                    f"LVM enabled dedup path must be an input for Unix MA {self.tcinputs['MediaAgent']}")
                Browser.close_silently(self.browser)
                raise Exception(
                    f"Please provide LVM enabled dedup path as input for Unix MA {self.tcinputs['MediaAgent']}")
        else:
            if self.dedup_provided:
                self.log.info('Windows MA provided, assigning user defined dedup location')
                self.ddb_location1 = self.tcinputs["cloud_ddb_path"]
                self.ddb_location2 = self.tcinputs["cloud_ddb_path"]
            else:
                self.log.info('Windows MA provided, creating dedup locations')
                self.log.info('Selecting drive in the MA machine based on space available')
                ma_drive = options_selector.get_drive(self.ma_machine)
                if ma_drive is None:
                    Browser.close_silently(self.browser)
                    raise Exception("No free space for hosting ddb and mount paths")
                self.log.info('selected drive: %s', ma_drive)
                self.path = self.ma_machine.join_path(ma_drive, f"Automation_DDB")
                self.ddb_location1 = self.ma_machine.join_path(self.path, str(self.id), 'DDB1')
                self.ddb_location2 = self.ma_machine.join_path(self.path, str(self.id), 'DDB2')

        self.log.info('selected ddb location for Case1: %s', self.ddb_location1)
        self.log.info('selected ddb location for Case2: %s', self.ddb_location2)

    def validate_plan_deletion(self, plan_name_provided):
        """Validates if the plan is deleted or not

            Args:
                  plan_name_provided - name of the plan whose deletion needs to be validated

        """

        exist = self.plans_page.is_plan_exists(plan_name_provided)
        if not exist:
            self.log.info(f"Validated deletion of plan {plan_name_provided}")
        else:
            raise Exception(f'Raising error - {plan_name_provided} still exist on CC')

    def validate_storage_deletion(self, storage_name_provided):
        """Validates if the storage is deleted or not

            Args:
                storage_name_provided- name of the storage whose deletion needs to be validated

        """
        exist = self.storage_helper.has_cloud_storage(storage_name_provided)
        if not exist:
            self.log.info(f"Validated deletion of storage {storage_name_provided}")
        else:
            raise Exception(f'Raising error- {storage_name_provided} still exist on CC')

    def delete_plan(self, plan_name_provided):
        """Deletes the plan with the given name

            Args:
                plan_name_provided- name of the plan to be deleted

        """

        self.log.info(f"Deleting plan {plan_name_provided}")
        self.plans_page.delete_plan(plan_name_provided)
        self.validate_plan_deletion(plan_name_provided)

    def delete_storage(self, storage_name_provided):
        """Deletes the storage with given name

            Args:
                  storage_name_provided- name of the storage to be deleted

        """

        self.log.info(f"Deleting storage {storage_name_provided}")
        self.storage_helper.delete_cloud_storage(storage_name_provided)
        self.validate_storage_deletion(storage_name_provided)

    def cleanup(self):
        """Cleaning up entities created by testcase"""

        self.log.info("**********Cleanup Started**********")

        if self.plans_page.is_plan_exists(self.plan_name1):
            self.delete_plan(self.plan_name1)

        if self.plans_page.is_plan_exists(self.plan_name2):
            self.delete_plan(self.plan_name2)

        if self.plans_page.is_plan_exists(self.plan_name3):
            self.delete_plan(self.plan_name3)

        if self.storage_helper.has_cloud_storage(self.storage_name1):
            self.delete_storage(self.storage_name1)

        if self.storage_helper.has_cloud_storage(self.storage_name2):
            self.delete_storage(self.storage_name2)

        if self.storage_helper.has_cloud_storage(self.storage_name3):
            self.delete_storage(self.storage_name3)

        self.log.info("**********Cleanup completed**********")

    def create_cloud_storage(self, storage_name_provided, dedup_path_provided=None):
        """ creates a new cloud storage

            Args:
                storage_name_provided - name for cloud storage to be created

                dedup_path_provided - ddb path (in case of dedupe storage only)

        """

        self.log.info("Adding a new cloud storage: %s", storage_name_provided)
        ma_name = self.commcell.clients.get(self.tcinputs['MediaAgent']).display_name
        self.storage_helper.add_cloud_storage(cloud_storage_name=storage_name_provided, media_agent=ma_name,
                                              cloud_type=self.tcinputs['CloudType'],
                                              server_host=self.tcinputs['CloudServerName'],
                                              auth_type=self.authentication,
                                              container=self.tcinputs['CloudContainer'],
                                              storage_class=self.storageClass,
                                              region=self.region,
                                              saved_credential_name=self.creds,
                                              deduplication_db_location=dedup_path_provided,
                                              cred_details=self.cred_details)
        self.log.info('successfully created cloud storage: %s', storage_name_provided)

    def validate_storage_creation(self, storage_name_provided):
        """Validates if cloud storage is created or not

            Args:
                storage_name_provided - name of the storage whose creation needs to be validated

        """

        exist = self.storage_helper.has_cloud_storage(storage_name_provided)
        if exist:
            self.log.info(f"Created cloud storage {storage_name_provided} is being shown on web page")
        else:
            raise Exception(f'Created cloud storage {storage_name_provided} is not being shown on web page')

    def enable_worm_lock(self, storage_name_provided):
        """Enables the worm lock on the storage

            Args:
                storage_name_provided - name of the storage

        """

        self.retention_dict = {'period': 'Day(s)', 'value': self.RetentionDays}
        self.log.info("Enabling worm on cloud storage: %s", storage_name_provided)
        self.storage_helper.cloud_worm_storage_lock(cloud_storage=storage_name_provided,
                                                    retention_period=self.retention_dict)
        self.log.info("Enabled worm on cloud storage: %s", storage_name_provided)

    def verify_flag_values_storage(self, storage_name_provided, seal_frequency_check=True):
        """Verifies csdb flag values for storage after enabling worm

            Args:
                storage_name_provided - name of the storage

                seal_frequency_check - True, in case of dedupe storage, else False

        """

        query = """SELECT	AG.name AS StorageName , AR.retentionDays AS StorageRetention, AGC.flags & 16777216 AS 
        IsWormEnabled , ATK.numPeriod AS sealFrequencySetInDays , Ml.LibraryId, ML.AliasName AS LibraryName , 
        ML.LibraryAttribute & 8388608 As IsObjectWORMEnabled , MP.Attribute & 32 AS IsCloudMicroPruningEnabled
        FROM MMMountPath MP INNER JOIN MMLibrary ML ON MP.LibraryId = ML.LibraryId
        INNER JOIN MMMasterPool MMP ON ML.LibraryId = MMP.LibraryId 
        INNER JOIN MMDrivePool MDP ON MMP.MasterPoolId = MDP.MasterPoolId 
        INNER JOIN MMDataPath DP ON MDP.DrivePoolID = DP.DrivePoolId 
        INNER JOIN archGroupCopy AGC ON DP.CopyId= AGC.id 
        INNER JOIN archAgingRule AR ON AR.copyId = AGC.id 
        INNER JOIN archTask ATK ON ATK.id=AGC.sealStoreTaskId 
        INNER JOIN archGroup AG ON AGC.id = AG.defaultCopy 
        WHERE AG.name ='{0}' """.format(storage_name_provided)

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)

        if (int(cur[2]) == self.isWormEnabledFlag and (
                not seal_frequency_check or int(cur[3]) == 7) and
                int(cur[6]) == self.isObjectWormEnabledFlag and int(cur[7]) == 0):
            self.log.info("Flags are set as needed on storage")

        else:
            error_message = ""
            if int(cur[2]) != self.isWormEnabledFlag:
                error_message += "Worm flag, "
            if int(cur[3]) != 7:
                error_message += "Seal frequency, "
            if int(cur[6]) != self.isObjectWormEnabledFlag:
                error_message += "Object lock flag, "
            if int(cur[7]) != 0:
                error_message += "Micro Pruning,"
            error_message += "is not set as needed on storage {0}".format(storage_name_provided)
            raise Exception(error_message)

    def create_server_plan(self, plan_name_provided, storage_dict_provided):
        """creates a new server plan

            Args:
                plan_name_provided -  name of the plan to be created

                storage_dict_provided -  dictionary for specifying retention period
                                        {'pri_storage': None,
                                         'pri_ret_period':'30',
                                         'snap_pri_storage': None,
                                         'sec_storage': None,
                                         'sec_ret_period':'45',
                                         'ret_unit':'Day(s)'}
        """

        self.log.info("Adding a new plan: %s", plan_name_provided)
        self.admin_console.navigator.navigate_to_plan()
        self.plans_page.create_server_plan(plan_name=plan_name_provided, storage=storage_dict_provided)
        self.log.info('successfully created plan: %s', plan_name_provided)

    def validate_plan_creation(self, plan_name_provided):
        """Validates if the plan is created or not

            Args:
                plan_name_provided - name of the plan whose creation needs to be validated

        """

        exist = self.plans_page.is_plan_exists(plan_name_provided)
        if exist:
            self.log.info("Created plan is being shown on web page")
        else:
            raise Exception('Created plan is not being shown on web page')

    def verify_flag_values_plan(self, plan_name_provided, return_retention_value=False, check_override_retention=True,
                                check_worm_flag=True):
        """verifies the csdb flag values for a plan

            Args:
                plan_name_provided - name of the plan

                return_retention_value - True, if retention value needs to be returned

                check_override_retention- True, if override retention flag needs to be checked

                check_worm_flag- True, if worm flag needs to be checked

            Returns:
                retention value (days) if return_retention_value is True
        """

        query = """SELECT agc.id,agc.flags & 16777216 AS IsWormEnabled, 
                    agc.extendedFlags & 2048 as IsOverrideRetentionSet, ar.retentionDays AS StorageRetention 
                    FROM archGroupCopy agc INNER JOIN archGroup ag ON ag.id = agc.archGroupId
                    INNER JOIN archAgingRule ar ON ar.copyId = agc.id 
                    WHERE ag.name = '{0}' """.format(plan_name_provided)

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)

        if (not check_worm_flag or int(cur[1]) == self.isWormEnabledFlag) and (
                not check_override_retention or int(cur[2]) == self.overrideRetentionFlag) and (
                return_retention_value or int(cur[3]) == 1):
            self.log.info("Flags are set as needed on plan %s", plan_name_provided)

        else:
            error_message = ""
            if int(cur[1]) != self.isWormEnabledFlag:
                error_message += "Worm flag, "
            if int(cur[2]) != self.overrideRetentionFlag:
                error_message += "Override retention flag, "
            if int(cur[3]) != 1:
                error_message += "Retention,"
            error_message += "is not set as needed on plan {0}".format(plan_name_provided)
            raise Exception(error_message)

        if return_retention_value:
            return int(cur[3])

    def set_retention_on_storage(self, storage_name_provided, ret_number, ret_unit):
        """ Sets retention on storage pool

            Args:
                storage_name_provided - name of the storage

                ret_number - number of (days/week/month/year) as per retention unit

                ret_unit - retention unit (days/week/month/year)

        """

        self.log.info("Trying to modify retention on storage %s (WORM enabled)", storage_name_provided)
        self.storage_helper.modify_retention_on_worm_cloud_storage(cloud_storage=storage_name_provided,
                                                                   ret_unit=ret_unit, ret_number=ret_number)

    def set_retention_on_plan(self, plan_name_provided, new_retention_period, waitForCompletion=True):
        """ Sets retention on plan

            Args:
                plan_name_provided = name of the plan

                new_retention_period = number of retention days

                waitForCompletion = False, if wait for completion not needed after clicking Yes

        """
        self.log.info("Trying to modify retention on plan %s (WORM enabled)", plan_name_provided)
        notification_text = self.plan_helper.modify_retention_on_copy(plan_name=plan_name_provided, copy_name='Primary',
                                                                      ret_days=new_retention_period,
                                                                      ret_unit='Day(s)',
                                                                      waitForCompletion=waitForCompletion)
        if self.expected_error_str in notification_text:
            self.log.info(notification_text)
        elif notification_text:
            raise Exception(notification_text)

    def run(self):
        """run function of this test case"""

        try:
            self.cleanup()

            if self.tcinputs.get("Authentication"):
                self.authentication = self.tcinputs["Authentication"]

            if self.tcinputs.get("StorageClass"):
                self.storageClass = self.tcinputs["StorageClass"]

            if self.tcinputs.get("region"):
                self.region = self.tcinputs["region"]

            if self.tcinputs.get("accountName"):
                self.cred_details["accountName"] = self.tcinputs["accountName"]

            if self.tcinputs.get("CloudCredentials"):
                self.creds = self.tcinputs['CloudCredentials']

            self.log.info("-------Case 1 execution starts here--------")
            self.create_cloud_storage(self.storage_name1, self.ddb_location1)
            self.validate_storage_creation(self.storage_name1)
            self.enable_worm_lock(self.storage_name1)
            self.verify_flag_values_storage(self.storage_name1)
            self.create_server_plan(self.plan_name1, self.storage_dict1)
            self.validate_plan_creation(self.plan_name1)
            self.verify_flag_values_plan(self.plan_name1)

            self.log.info("-------Case 2 execution starts here--------")
            self.create_cloud_storage(self.storage_name2, self.ddb_location2)
            self.validate_storage_creation(self.storage_name2)
            self.create_server_plan(self.plan_name2, self.storage_dict2)
            self.validate_plan_creation(self.plan_name2)
            retention_on_plan = self.verify_flag_values_plan(self.plan_name2, check_override_retention=False,
                                                             return_retention_value=True,
                                                             check_worm_flag=False)
            if retention_on_plan != int(self.PlanRetentionDays2):
                raise Exception("Retention on plan %s is not set as 30 days", self.plan_name2)
            self.log.info("Retention on plan %s is set as 30 days successfully", self.plan_name2)
            self.enable_worm_lock(self.storage_name2)
            self.verify_flag_values_storage(self.storage_name2)
            self.verify_flag_values_plan(self.plan_name2)
            self.log.info("Retention on plan %s is changed to 1 day", self.plan_name2)

            self.log.info("-------Case 3 execution starts here--------")
            self.create_cloud_storage(self.storage_name3)
            self.validate_storage_creation(self.storage_name3)
            self.create_server_plan(self.plan_name3, self.storage_dict3)
            self.validate_plan_creation(self.plan_name3)
            self.enable_worm_lock(self.storage_name3)
            self.verify_flag_values_storage(self.storage_name3, seal_frequency_check=False)
            try:
                # This should not be allowed for non dedup storage only
                self.set_retention_on_storage(storage_name_provided=self.storage_name3, ret_unit='Day(s)', ret_number=1)
                raise Exception('Raising error because modifying retention on Non dedup pool should not be allowed.')
            except CVWebAutomationException as e:
                self.log.info("As stated, modifying Retention on Non dedup pool is not allowed.")
            increase_retention_value = int(self.PlanRetentionDays3) + 1
            decrease_retention_value = increase_retention_value - 2
            self.set_retention_on_plan(self.plan_name3, increase_retention_value)
            new_set_retention = self.verify_flag_values_plan(self.plan_name3, return_retention_value=True,
                                                             check_override_retention=False)
            if new_set_retention == increase_retention_value:
                self.log.info("Retention increased successfully on Plan %s", self.plan_name3)
            else:
                raise Exception("Retention not increased on plan %s", self.plan_name3)
            self.set_retention_on_plan(self.plan_name3, decrease_retention_value, waitForCompletion=False)
            new_set_retention = self.verify_flag_values_plan(self.plan_name3, return_retention_value=True,
                                                             check_override_retention=False)
            if new_set_retention == decrease_retention_value:
                raise Exception("Retention decreased on plan %s", self.plan_name3)
            else:
                self.log.info("Retention cannot be reduced on plan %s", self.plan_name3)

            self.cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)
