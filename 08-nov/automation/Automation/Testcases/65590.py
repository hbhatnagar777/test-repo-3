# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" This TC is designed to ensure that min, max and storage class validation of DDB sealing frequency configuration are tested and validated this is config only case.

Prerequisite-> Cloud storage account credentials should be already saved, azure account is needed for Case-4 and 5

TestCase: Class for executing this test case

    __init__()      -- Initializing the Test case file

    init_tc()       -- Initial configuration for the test case

    setup()         -- Initializes pre-requisites for this test case

    create_cloud_storage() -- creates a new cloud storage

    validate_storage_creation() -- validates whether a cloud storage is created or not

    enable_worm_lock() -- enables the worm lock on storage

    create_server_plan() -- to create a new server plan

    validate_plan_creation() -- Validates if the plan is created or not

    set_retention_on_storage() -- sets retention on storage pool

    validate_seal_frequency_and_retention() -- validates retention and seal frequency from csdb

    create_storage_and_plan() -- creates storage and plan

    validate_plan_deletion() -- Validates if the plan is deleted or not

    validate_storage_deletion() -- Validates if the storage is deleted or not

    delete_plan()    -- Deletes the plan with the given name

    delete_storage()    -- Deletes the storage with the given name

    cleanup()            -- Cleaning up entities created by testcase

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
          "accountName": In case of azure , if authentication type is "IAM AD application" / "IAM VM Role"
          "region": Depends on the cloud vendor (str), if mandatory, then provide
                    Name of the geographical region for storage,
          "Authentication_azure": Authentication type to be used for azure account,  eg-"Access key and Account name"
          "accountName_azure": In case of azure , if authentication type is "IAM AD application" / "IAM VM Role"
          "region_azure":  Name of the geographical region for storage,
          "CloudContainer_azure": Name of the cloud container (str),
          "CloudCredentials_azure": Already saved credentials for azure,
          "cloud_ddb_path": Cloud Ddb location for case-1 and case-2 storage for unix MA
                            (required - if the MA provided is Unix/Linux, else optional)


             *****In case of Unix/Linux MA, provide LVM enabled dedup paths*****
        }

Steps:
    Base Step for all cases:-   Create a deduplication enabled storage pool. Associate a copy to this pool.
                                Enable H/w WORM lock on the pool

    Case1: Min seal frequency

            Set retention on the pool as 1D
            Validate seal frequency is set as 7 days
            Update retention to the value of 7 days (increase in retention should be allowed)
            Seal frequency should not change and stay as 7 days.
            Try lowering the retention, and we should get an error that it is not allowed (reduce to 5D)
            Increase retention to the value of 8 days, seal frequency should get updated to 8 days.
            along with points added

    Case2: Max seal frequency

            Set retention on the pool as 364D
            Validate seal frequency is set as 364 days
            Update retention to the value of 365days (increase in retention should be allowed)
            Seal frequency should change 365 days.
            Update retention to the value of 366days (increase in retention should be allowed)
            Seal frequency should not change and stay as 365 days.
            Try lowering the retention, and we should get an error that it is not allowed (reduce to 365D)
            Increase retention to the value of 3650 days, seal frequency should stay 365 days.
                (Updating retention should not return overflow error.)

    Case3: Seal frequency should change with retention

            Set retention on the pool as 7D
            Validate seal frequency is set as 7 days
            Update retention to the value of 30 days (increase in retention should be allowed)
            Seal frequency should change 30 days.
            Update retention to the value of 180 days (increase in retention should be allowed)
            Seal frequency should change to 180 days.

    Case 4: Min days to keep as per storage class -> Azure Cool

            Create a dedupe pool with Azure cool
            Min WORM lock days should be 30 days i.e.
            Set retention to 7 days then seal frequency should be 23 days.
            Increase retention to 15 days seal frequency should be 15 days.
            Increase retention to 16 days seal frequency should be 16 days.
            Increase retention to 30 days and seal frequency should be 30 days.
            Increase retention to 366 days and seal frequency should cap at 365 days.

    Case 5: Min days to keep as per storage class -> Azure Archive

            Create a dedupe pool with Azure archive
            Min WORM lock days should be 180 days i.e.
            Set retention to 7 days then seal frequency should be 173 days.
            Increase retention to 30 days seal frequency should be 150 days.
            Increase retention to 90 days seal frequency should be 90 days.
            Increase retention to 91 days and seal frequency should be 91 days.
            Increase retention to 366 days and seal frequency should cap at 365 days.

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()

        self.name = "Acceptance WORM config for DDB sealing frequency - CC"
        self.browser = None
        self.admin_console = None
        self.storage_helper = None
        self.plans_page = None
        self.plan_helper = None
        self.mm_helper = None
        self.client_machine = None
        self.ma_machine = None
        self.path = None
        self.retention_dict = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent": None,
            "CloudType": None,
            "CloudServerName": None,
            "CloudContainer": None,
            "Authentication_azure": None,
            "region_azure": None,
            "CloudContainer_azure": None
        }
        self.storage_name1 = None
        self.storage_name2 = None
        self.storage_name3 = None
        self.storage_name4 = None
        self.storage_name5 = None
        self.plan_name1 = None
        self.plan_name2 = None
        self.plan_name3 = None
        self.plan_name4 = None
        self.plan_name5 = None
        self.ddb_location1 = None
        self.ddb_location2 = None
        self.ddb_location3 = None
        self.ddb_location4 = None
        self.ddb_location5 = None
        self.expected_error_str = None
        self.isWormEnabledFlag = None
        self.authentication = None
        self.storageClass = None
        self.region = None
        self.dedup_provided = False
        self.cred_details = {}
        self.creds = None
        self.cred_details_azure = {}
        self.creds_azure = None

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
        self.expected_error_str = "Specifying a retention value lower than the current value is not allowed as the Compliance lock is enabled"
        self.storage_helper = StorageMain(self.admin_console)
        self.plan_helper = PlanMain(self.admin_console, commcell=self.commcell)
        self.plans_page = Plans(self.admin_console)
        options_selector = OptionsSelector(self.commcell)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent'])
        self.storage_name1 = f"Worm-Cloud-1-{self.id}"
        self.storage_name2 = f"Worm-Cloud-2-{self.id}"
        self.storage_name3 = f"Worm-Cloud-3-{self.id}"
        self.storage_name4 = f"Worm-Cloud-4-{self.id}"
        self.storage_name5 = f"Worm-Cloud-5-{self.id}"
        self.plan_name1 = f"Worm-Plan-1-{self.id}"
        self.plan_name2 = f"Worm-Plan-2-{self.id}"
        self.plan_name3 = f"Worm-Plan-3-{self.id}"
        self.plan_name4 = f"Worm-Plan-4-{self.id}"
        self.plan_name5 = f"Worm-Plan-5-{self.id}"

        if self.tcinputs.get("cloud_ddb_path"):
            self.dedup_provided = True

        if "unix" in self.ma_machine.os_info.lower():
            if self.dedup_provided:
                self.log.info('Unix/Linux MA provided, assigning user defined dedup locations')
                self.ddb_location1 = self.tcinputs["cloud_ddb_path"]
                self.ddb_location2 = self.tcinputs["cloud_ddb_path"]
                self.ddb_location3 = self.tcinputs["cloud_ddb_path"]
                self.ddb_location4 = self.tcinputs["cloud_ddb_path"]
                self.ddb_location5 = self.tcinputs["cloud_ddb_path"]

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
                self.ddb_location3 = self.tcinputs["cloud_ddb_path"]
                self.ddb_location4 = self.tcinputs["cloud_ddb_path"]
                self.ddb_location5 = self.tcinputs["cloud_ddb_path"]
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
                self.ddb_location3 = self.ma_machine.join_path(self.path, str(self.id), 'DDB3')
                self.ddb_location4 = self.ma_machine.join_path(self.path, str(self.id), 'DDB4')
                self.ddb_location5 = self.ma_machine.join_path(self.path, str(self.id), 'DDB5')

        self.log.info('selected ddb location for Case1: %s', self.ddb_location1)
        self.log.info('selected ddb location for Case2: %s', self.ddb_location2)
        self.log.info('selected ddb location for Case3: %s', self.ddb_location3)
        self.log.info('selected ddb location for Case4: %s', self.ddb_location4)
        self.log.info('selected ddb location for Case5: %s', self.ddb_location5)

    def create_cloud_storage(self, storage_name_provided, dedup_path_provided=None, azure_class=None):
        """ creates a new cloud storage

            Args:
                storage_name_provided - name for cloud storage to be created

                dedup_path_provided - ddb path (in case of dedupe storage only)

                azure_class - storage class for azure storage only

        """

        self.log.info("Adding a new cloud storage: %s", storage_name_provided)
        ma_name = self.commcell.clients.get(self.tcinputs['MediaAgent']).display_name
        if azure_class:
            self.log.info("--------Creating azure storage--------")
            self.storage_helper.add_cloud_storage(cloud_storage_name=storage_name_provided, media_agent=ma_name,
                                                  cloud_type="Microsoft Azure Storage",
                                                  server_host="blob.core.windows.net",
                                                  auth_type=self.tcinputs['Authentication_azure'],
                                                  container=self.tcinputs['CloudContainer_azure'],
                                                  storage_class=azure_class,
                                                  region=self.tcinputs['region_azure'],
                                                  saved_credential_name=self.creds_azure,
                                                  deduplication_db_location=dedup_path_provided,
                                                  cred_details=self.cred_details_azure)
        else:
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

    def enable_worm_lock(self, storage_name_provided, retention_days):
        """Enables the worm lock on the storage

            Args:
                storage_name_provided - name of the storage

                retention_days - number of retention days
        """

        self.retention_dict = {'period': 'Day(s)', 'value': retention_days}
        self.log.info("Enabling worm on cloud storage: %s", storage_name_provided)
        self.storage_helper.cloud_worm_storage_lock(cloud_storage=storage_name_provided,
                                                    retention_period=self.retention_dict)
        self.log.info("Enabled worm on cloud storage: %s", storage_name_provided)

    def create_server_plan(self, plan_name_provided, storage_name_provided, archive_storage=False):
        """Creates a plan with a given name and storage

            Args:
                plan_name_provided -  name of the plan to be created

                storage_name_provided - name of the storage to be associated with plan

                archive_storage - True, if plan is associated to archive tier storage

        """

        storage_dict = {'pri_storage': storage_name_provided}
        self.log.info("Adding a new plan: %s", plan_name_provided)
        self.admin_console.navigator.navigate_to_plan()

        if archive_storage:
            storage_dict['pri_storage_type'] = 'Archive'

        self.plans_page.create_server_plan(plan_name=plan_name_provided, storage=storage_dict)
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

    def set_retention_on_storage(self, storage_name_provided, ret_number, ret_unit):
        """ Sets retention on storage pool

            Args:
                storage_name_provided - name of the storage

                ret_number - number of (days/week/month/year) as per retention unit

                ret_unit - retention unit (days/week/month/year)

        """

        self.log.info("Trying to set retention on storage {0} (WORM enabled) to {1} {2}".format(storage_name_provided,
                                                                                                ret_number, ret_unit))
        notification_text = self.storage_helper.modify_retention_on_worm_cloud_storage(
            cloud_storage=storage_name_provided,
            ret_unit=ret_unit, ret_number=ret_number)

        if self.expected_error_str in notification_text:
            self.log.info(notification_text)

    def validate_seal_frequency_and_retention(self, storage_name_provided, expected_retention, expected_seal_frequency):
        """Validates retention and seal frequency from csdb

            Args:
                storage_name_provided - name of the storage

                expected_retention - expected value for the retention (Days)

                expected_seal_frequency - expected value for seal frequency (Days)

        """

        query = """SELECT AG.name AS StorageName , ATK.numPeriod AS sealFrequencyInDays, AR.retentionDays AS Retention,
                AGC.flags & 16777216 AS IsWormEnabled FROM  archTask ATK INNER JOIN archGroupCopy AGC 
                ON ATK.id=AGC.sealStoreTaskId 
                INNER JOIN archAgingRule AR ON AR.copyId = AGC.id
                INNER JOIN archGroup AG ON AGC.id = AG.defaultCopy 
                WHERE AG.name ='{0}' """.format(storage_name_provided)

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)

        error_message = ""
        if int(cur[1]) != int(expected_seal_frequency):
            error_message += "Seal frequency should be set as {0},".format(expected_seal_frequency)

        if int(cur[2]) != int(expected_retention):
            error_message += "Retention should be set as {0},".format(expected_retention)

        if int(cur[3]) != self.isWormEnabledFlag:
            error_message += "Worm lock flag is not set"

        if error_message != "":
            raise Exception(error_message)

        self.log.info("Retention is {0} and seal frequency is {1}".format(expected_retention, expected_seal_frequency))

    def create_storage_and_plan(self, storage_name, dedup_path, plan_name, azure_class=None):
        """ creates storage and plan

            Args:
                storage_name - name of the storage

                dedup_path - ddb location for storage

                plan_name - name of the plan

                azure_class - storage class for azure cloud storage only

        """

        archive_storage = False
        self.create_cloud_storage(storage_name, dedup_path, azure_class=azure_class)
        self.validate_storage_creation(storage_name)

        if azure_class == "Archive":
            archive_storage = True
        self.create_server_plan(plan_name, storage_name, archive_storage)
        self.validate_plan_creation(plan_name)

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

        if self.plans_page.is_plan_exists(self.plan_name4):
            self.delete_plan(self.plan_name4)

        if self.plans_page.is_plan_exists(self.plan_name5):
            self.delete_plan(self.plan_name5)

        if self.storage_helper.has_cloud_storage(self.storage_name1):
            self.delete_storage(self.storage_name1)

        if self.storage_helper.has_cloud_storage(self.storage_name2):
            self.delete_storage(self.storage_name2)

        if self.storage_helper.has_cloud_storage(self.storage_name3):
            self.delete_storage(self.storage_name3)

        if self.storage_helper.has_cloud_storage(self.storage_name4):
            self.delete_storage(self.storage_name4)

        if self.storage_helper.has_cloud_storage(self.storage_name5):
            self.delete_storage(self.storage_name5)

        self.log.info("**********Cleanup completed**********")

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

            if self.tcinputs.get("accountName_azure"):
                self.cred_details_azure["accountName"] = self.tcinputs["accountName_azure"]
                self.cred_details_azure["accountName"] = self.tcinputs["accountName_azure"]

            if self.tcinputs.get("CloudCredentials_azure"):
                self.creds_azure = self.tcinputs['CloudCredentials_azure']

            self.log.info("-------Case 1 execution starts here--------")
            self.create_storage_and_plan(self.storage_name1, self.ddb_location1, self.plan_name1)
            self.enable_worm_lock(self.storage_name1, retention_days="1")
            self.validate_seal_frequency_and_retention(self.storage_name1, expected_seal_frequency=7,
                                                       expected_retention=1)
            self.set_retention_on_storage(self.storage_name1, ret_unit='Week(s)', ret_number=1)
            self.validate_seal_frequency_and_retention(self.storage_name1, expected_seal_frequency=7,
                                                       expected_retention=7)
            self.log.info("Trying to lower the retention period on pool")
            self.set_retention_on_storage(storage_name_provided=self.storage_name1, ret_unit='Day(s)', ret_number=5)
            self.validate_seal_frequency_and_retention(self.storage_name1, expected_seal_frequency=7,
                                                       expected_retention=7)
            self.log.info("As expected, retention was not lowered.")
            self.set_retention_on_storage(storage_name_provided=self.storage_name1, ret_unit='Day(s)', ret_number=8)
            self.validate_seal_frequency_and_retention(self.storage_name1, expected_seal_frequency=8,
                                                       expected_retention=8)

            self.log.info("-------Case 2 execution starts here--------")
            self.create_storage_and_plan(self.storage_name2, self.ddb_location2, self.plan_name2)
            self.enable_worm_lock(self.storage_name2, retention_days="364")
            self.validate_seal_frequency_and_retention(self.storage_name2, expected_seal_frequency=364,
                                                       expected_retention=364)
            self.set_retention_on_storage(storage_name_provided=self.storage_name2, ret_unit='Day(s)', ret_number=365)
            self.validate_seal_frequency_and_retention(self.storage_name2, expected_seal_frequency=365,
                                                       expected_retention=365)
            self.set_retention_on_storage(self.storage_name2, ret_unit='Year(s)', ret_number=1)
            self.validate_seal_frequency_and_retention(self.storage_name2, expected_seal_frequency=365,
                                                       expected_retention=365)
            self.set_retention_on_storage(storage_name_provided=self.storage_name2, ret_unit='Day(s)', ret_number=366)
            self.validate_seal_frequency_and_retention(self.storage_name2, expected_seal_frequency=365,
                                                       expected_retention=366)
            self.log.info("Trying to lower the retention period on pool")
            self.set_retention_on_storage(storage_name_provided=self.storage_name2, ret_unit='Year(s)', ret_number=1)
            self.validate_seal_frequency_and_retention(self.storage_name2, expected_seal_frequency=365,
                                                       expected_retention=366)
            self.log.info("As expected, retention was not lowered.")
            self.set_retention_on_storage(storage_name_provided=self.storage_name2, ret_unit='Year(s)', ret_number=10)
            self.validate_seal_frequency_and_retention(self.storage_name2, expected_seal_frequency=365,
                                                       expected_retention=3650)

            self.log.info("-------Case 3 execution starts here--------")
            self.create_storage_and_plan(self.storage_name3, self.ddb_location3, self.plan_name3)
            self.enable_worm_lock(self.storage_name3, retention_days="7")
            self.validate_seal_frequency_and_retention(self.storage_name3, expected_seal_frequency=7,
                                                       expected_retention=7)
            self.set_retention_on_storage(self.storage_name3, ret_unit='Day(s)', ret_number=30)
            self.validate_seal_frequency_and_retention(self.storage_name3, expected_seal_frequency=30,
                                                       expected_retention=30)
            self.set_retention_on_storage(self.storage_name3, ret_unit='Month(s)', ret_number=1)
            self.validate_seal_frequency_and_retention(self.storage_name3, expected_seal_frequency=30,
                                                       expected_retention=30)
            self.set_retention_on_storage(self.storage_name3, ret_unit='Day(s)', ret_number=180)
            self.validate_seal_frequency_and_retention(self.storage_name3, expected_seal_frequency=180,
                                                       expected_retention=180)
            self.set_retention_on_storage(self.storage_name3, ret_unit='Month(s)', ret_number=6)
            self.validate_seal_frequency_and_retention(self.storage_name3, expected_seal_frequency=182,
                                                       expected_retention=182)

            self.log.info("-------Case 4 execution starts here--------")
            self.create_storage_and_plan(self.storage_name4, self.ddb_location4, self.plan_name4, azure_class="Cool")
            self.enable_worm_lock(self.storage_name4, retention_days="7")
            self.validate_seal_frequency_and_retention(self.storage_name4, expected_seal_frequency=23,
                                                       expected_retention=7)
            self.set_retention_on_storage(self.storage_name4, ret_unit='Day(s)', ret_number=15)
            self.validate_seal_frequency_and_retention(self.storage_name4, expected_seal_frequency=15,
                                                       expected_retention=15)
            self.set_retention_on_storage(storage_name_provided=self.storage_name4, ret_unit='Day(s)', ret_number=16)
            self.validate_seal_frequency_and_retention(self.storage_name4, expected_seal_frequency=16,
                                                       expected_retention=16)
            self.set_retention_on_storage(storage_name_provided=self.storage_name4, ret_unit='Day(s)', ret_number=30)
            self.validate_seal_frequency_and_retention(self.storage_name4, expected_seal_frequency=30,
                                                       expected_retention=30)
            self.set_retention_on_storage(storage_name_provided=self.storage_name4, ret_unit='Month(s)', ret_number=1)
            self.validate_seal_frequency_and_retention(self.storage_name4, expected_seal_frequency=30,
                                                       expected_retention=30)
            self.set_retention_on_storage(storage_name_provided=self.storage_name4, ret_unit='Day(s)', ret_number=35)
            self.validate_seal_frequency_and_retention(self.storage_name4, expected_seal_frequency=35,
                                                       expected_retention=35)
            self.set_retention_on_storage(storage_name_provided=self.storage_name4, ret_unit='Day(s)', ret_number=366)
            self.validate_seal_frequency_and_retention(self.storage_name4, expected_seal_frequency=365,
                                                       expected_retention=366)

            self.log.info("-------Case 5 execution starts here--------")
            self.create_storage_and_plan(self.storage_name5, self.ddb_location5, self.plan_name5,
                                         azure_class="Archive")
            self.enable_worm_lock(self.storage_name5, retention_days="7")
            self.validate_seal_frequency_and_retention(self.storage_name5, expected_seal_frequency=173,
                                                       expected_retention=7)
            self.set_retention_on_storage(storage_name_provided=self.storage_name5, ret_unit='Day(s)', ret_number=30)
            self.validate_seal_frequency_and_retention(self.storage_name5, expected_seal_frequency=150,
                                                       expected_retention=30)
            self.set_retention_on_storage(self.storage_name5, ret_unit='Month(s)', ret_number=1)
            self.validate_seal_frequency_and_retention(self.storage_name5, expected_seal_frequency=150,
                                                       expected_retention=30)
            self.set_retention_on_storage(storage_name_provided=self.storage_name5, ret_unit='Day(s)', ret_number=90)
            self.validate_seal_frequency_and_retention(self.storage_name5, expected_seal_frequency=90,
                                                       expected_retention=90)
            self.set_retention_on_storage(storage_name_provided=self.storage_name5, ret_unit='Month(s)', ret_number=3)
            self.validate_seal_frequency_and_retention(self.storage_name5, expected_seal_frequency=91,
                                                       expected_retention=91)
            self.set_retention_on_storage(storage_name_provided=self.storage_name5, ret_unit='Day(s)', ret_number=91)
            self.validate_seal_frequency_and_retention(self.storage_name5, expected_seal_frequency=91,
                                                       expected_retention=91)
            self.set_retention_on_storage(storage_name_provided=self.storage_name5, ret_unit='Day(s)', ret_number=366)
            self.validate_seal_frequency_and_retention(self.storage_name5, expected_seal_frequency=365,
                                                       expected_retention=366)

            self.cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)
