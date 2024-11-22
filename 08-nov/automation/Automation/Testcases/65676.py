# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Azure Data Lake Acceptance case for Metallic Hub

TestCase:
    __init__()                  --  Initialize TestCase class

    setup()                     --  Setup function of this test case

    run()                       --  run function of this test case

    create_tenant()             --  Create a new tenant for the automation

    configure_new_client()      --  Configures new Azure Data Lake object storage client

    change_content()            --  Change the default content from All contents to specified content

    run_backup()                --  Runs Backup and waits for backup job to finish

    run_restore()               --  Runs a Restore from Admin Console

    cleanup()                   --  Deletes the Azure Blob ObjectStorage Account

    validate_data()             -- Validates restored files by checking if the files exists and comparing sizes


Input Example:

    "testCases":
            {
                "65676": {
                      "accountName": STORAGE ACCOUNT NAME,
                      "accountKey": ACCESS KEY FOR STORAGE ACCOUNT,
                      "byos_account_name": NAME FOR BYOS ACCOUNT,
                      "byos_access_key": ACCESS KEY FOR BYOS ACCOUNT ,
                      "full_bkp_content": BACKUP CONTENT,
                      "incr_bkp_content": NEW CONTENT TO BE ADDED,
                      "tenant_id": TENANT ID,
                      "application_id": APPLICATION ID,
                      "app_password" : APPLICATION PASSWORD,
                      "subscription_id": SUBSCRIPTION ID
                }
            }

"""
import time
import datetime
from AutomationUtils import machine
from cvpysdk.commcell import Commcell
from Database.dbhelper import DbHelper
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import Browser
from Metallic.hubutils import HubManagement
from Web.Common.page_object import TestStep
from AutomationUtils.config import get_config
from Web.Common.cvbrowser import BrowserFactory
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.ObjectStorage.content_group import ContentGroup
from Web.AdminConsole.ObjectStorage.object_storage import ObjectStorage
from Web.AdminConsole.ObjectStorage.object_details import ObjectDetails
from Application.CloudStorage.azure_helper import AzureHelper, AzureDataLakeHelper
from Web.AdminConsole.Hub.CCObjectStorage.object_storage import RAzureObjectStorageInstance


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """ Initialise the test case class object """
        super().__init__()

        self.name = "Azure Data Lake Acceptance with IAM AD authentication for Metallic using Infrastructure Nodes"
        self.hub_management = None
        self.config = None
        self.company_name = None
        self.tenant_user_name = None
        self.tenant_password = None
        self.commcell = None
        self.browser = None
        self.admin_console = None
        self.client_name = None
        self.plan = None
        self.common_dir_path = None
        self.controller_object = None
        self.db_helper = None
        self.original_data_path = None
        self.restored_data_path = None
        self.is_byos_bucket_deleted = False
        self.content_group_name = 'default'
        self.content_group = None
        self.utils = TestCaseUtils(self)
        self.backup_job_list = set()
        self.azure_helper = None
        self.azure_dl_helper = None
        self.byos_azure_helper = None
        self.bucket_name = None
        self.object_details = None
        self.navigator = None
        self.object_storage = None
        self.page_container = None
        self.byos_bucket_name = None
        self.oss_metallic_helper = None
        self.account_name = None
        self.a_metadata = None
        self.b_metadata = None
        self.driver = None
        self.tcinputs = {
            "accountName": None,
            "accountKey": None,
            "byos_account_name": None,
            "byos_access_key": None,
            "full_bkp_content": None,
            "incr_bkp_content": None,
            "tenant_id": None,
            "application_id": None,
            "app_password": None,
            "subscription_id": None
        }

    def setup(self):
        """ Set up functions of this test case """

        # Delete existing tenants and create a new one for every run
        self.hub_management = HubManagement(testcase_instance=self, commcell=self.commcell.webconsole_hostname)
        self.hub_management.delete_companies_with_prefix(prefix='AzureDataLake-IAM-AD')
        self.create_tenant()

        # Initialize Helpers
        self.config = get_config()
        self.tenant_password = self.config.Metallic.tenant_password
        self.commcell = Commcell(webconsole_hostname=self.commcell.webconsole_hostname,
                                 commcell_username=self.tenant_user_name,
                                 commcell_password=self.tenant_password)

        self.azure_helper = AzureHelper(account_name=self.tcinputs["accountName"],
                                        access_key=self.tcinputs["accountKey"])
        self.azure_dl_helper = AzureDataLakeHelper(account_name=self.tcinputs["accountName"],
                                                   access_key=self.tcinputs["accountKey"])
        self.byos_azure_helper = AzureHelper(account_name=self.tcinputs.get('byos_account_name'),
                                             access_key=self.tcinputs.get('byos_access_key'))
        self.common_dir_path = self.azure_dl_helper.common_dir_path
        self.controller_object = machine.Machine()
        self.db_helper = DbHelper(self.commcell)

        # Log in to the command center with the tenant creds
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

        self.admin_console.login(username=self.tenant_user_name,
                                 password=self.tenant_password,
                                 stay_logged_in=True)
        self.admin_console.wait_for_completion()

        # Initialize variables and objects
        self.account_name = self.tcinputs.get("accountName")
        self.client_name = f'azure-datalake-client{str(int(time.time()))}'
        self.plan = f'azure-datalake-plan{str(int(time.time()))}'
        self.bucket_name = self.tcinputs["incr_bkp_content"]

        self.navigator = self.admin_console.navigator
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.page_container = PageContainer(self.admin_console)

    def create_tenant(self):
        """ Creates a tenant """

        self.company_name = datetime.datetime.now().strftime("AzureDataLake-IAM-AD-%d-%B-%H-%M")
        user_firstname = "AzureDataLake" + str(int(time.time()))
        user_lastname = "user"
        user_email = user_firstname + user_lastname + '@domain.com'
        user_phone_number = '00000000'
        user_country = self.tcinputs.get("UserCountry", "United States")
        self.log.info(f"Creating Tenant with Company name {self.company_name}")

        # Create a tenant and get password that is returned
        self.tenant_user_name = self.hub_management.create_tenant(
            company_name=self.company_name,
            email=user_email,
            first_name=user_firstname,
            last_name=user_lastname,
            phone_number=user_phone_number,
            country=user_country
        )

        time.sleep(30)

    @test_step
    def configure_new_client(self):
        """ Configures New Azure Data Lake Object Storage Client """

        self.byos_bucket_name = f'datalake-byos-{int(time.time())}'
        self.oss_metallic_helper = RAzureObjectStorageInstance(admin_console=self.admin_console,
                                                               vendor_type='Azure Data Lake Storage Gen2',
                                                               commcell=self.commcell)
        self.oss_metallic_helper.configure(byos_storage_name=self.byos_bucket_name,
                                           byos_account_name=self.tcinputs.get('byos_account_name'),
                                           plan_name=self.plan,
                                           client_name=self.client_name,
                                           auth_type='IAM AD application',
                                           account_name=self.account_name,
                                           tenant_id=self.tcinputs.get('tenant_id'),
                                           vendor_name='Azure Data Lake Storage Gen2',
                                           backup_method='Infrastructure',
                                           app_password=self.tcinputs.get('app_password'),
                                           application_id=self.tcinputs.get('application_id'),
                                           subscription_id=self.tcinputs.get('subscription_id'))

        self.log.info("New client has been configured successfully")
        self.admin_console.refresh_page()

    @test_step
    def change_content(self):
        """ Changes the default content of a new instance from all files to specified content """

        self.navigator.navigate_to_object_storage()
        self.object_storage.access_account(self.client_name)
        self.object_storage.edit_content_group(self.content_group_name, self.tcinputs['full_bkp_content'])
        self.log.info("Default group content updated successfully")
        self.page_container.click_breadcrumb(self.account_name)
        self.admin_console.access_tab(self.admin_console.props['pageHeader.contentGroups'])

    @test_step
    def backup(self, backup_type):
        """ Performs backup for object storage client
                Args:
                    backup_type: Type of backup FULL/INCR/SYNTH
                """

        if backup_type is RBackup.BackupType.FULL:
            jobid = self.object_details.submit_backup(
                self.content_group_name, backup_type
            )
        elif backup_type is RBackup.BackupType.SYNTH:
            _jobid = self.content_group.submit_backup(backup_type)
            jobid = _jobid[0]
        else:
            jobid = self.content_group.submit_backup(backup_type)

        if backup_type is not RBackup.BackupType.SYNTH:
            self.backup_job_list.add(jobid)
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Backup ran Successfully")

    @test_step
    def validate_data(self):
        """ Validates data after restore operation """

        self.log.info("original path : %s", self.original_data_path)
        self.log.info("restored path : %s", self.restored_data_path)

        restore_status = self.controller_object.compare_folders(self.controller_object,
                                                                self.original_data_path,
                                                                self.restored_data_path)
        if len(restore_status) > 0:
            raise CVTestStepFailure("Restore to Given destination Failed During Validation")

        self.log.info("Restore Validation Succeeded")
        self.db_helper.compare_dictionaries(self.b_metadata, self.a_metadata)
        self.log.info("Objects Metadata validation completed no mismatching before and after restore")

    @test_step
    def in_place_restore(self):
        """ Runs in-place restore """

        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.client_name)
        self.object_details.access_restore(self.content_group_name)

        # Create folder and download data from cloud bucket before restore
        self.log.info("Starting content download from cloud bucket before restore")
        self.original_data_path = self.controller_object.join_path(self.common_dir_path, 'original_contents')
        self.azure_dl_helper.download_container_dl(self.bucket_name, dir_name="original_contents")
        self.log.info("Content downloaded from cloud bucket before restore successfully")

        # Get metadata before restore is done
        self.b_metadata = self.azure_helper.get_metadata(container_name=self.bucket_name)
        self.log.info("Metadata collected before restore successfully")

        # Delete bucket from cloud (for primary copy restore)
        self.log.info(f"Deleting from azure cloud - {self.bucket_name} bucket.......")
        self.azure_dl_helper.delete_container_azure_dl(container_name=self.bucket_name)
        time.sleep(60)
        self.log.info("Deletion successful")

        # Submit the restore job
        rstr_obj = self.object_details.submit_restore([self.bucket_name])
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")

        # Create folder and download data from cloud bucket after restore
        self.log.info("Starting content download from cloud bucket after restore")
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents")
        self.azure_dl_helper.download_container_dl(self.bucket_name, dir_name="restored_contents")
        self.log.info("Content downloaded from cloud bucket after restore successfully")

        # Get metadata after restore is done
        self.a_metadata = self.azure_helper.get_metadata(container_name=self.bucket_name)
        self.log.info("Metadata collected after restore successfully")

        # Validate data
        self.validate_data()

        # Delete bucket from cloud (for secondary copy restore)
        self.log.info(f"Deleting from azure cloud - {self.bucket_name} bucket.......")
        self.azure_dl_helper.delete_container_azure_dl(container_name=self.bucket_name)
        self.log.info("Deletion successful")

        # Delete byos bucket
        self.log.info(f"Deleting BYOS {self.byos_bucket_name} bucket.......")
        self.byos_azure_helper.delete_container_azure(container_name=self.byos_bucket_name)
        self.is_byos_bucket_deleted = True
        self.log.info("Deletion of BYOS bucket successful")
        time.sleep(60)

        # Submit the restore job
        rstr_obj = self.object_details.submit_restore([self.bucket_name], copy='Secondary')
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job from secondary ran Successfully")

        # Create folder and download data from cloud bucket after restore
        self.log.info("Starting content download from cloud bucket before restore from secondary")
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents_secondary")
        self.azure_dl_helper.download_container_dl(self.bucket_name,
                                                   dir_name="restored_contents_secondary")
        self.log.info("Content downloaded from cloud bucket after restore from secondary successfully")

        # Get metadata after restore is done
        self.a_metadata = self.azure_helper.get_metadata(container_name=self.bucket_name)
        self.log.info("Metadata collected after restore successfully")

        # Validate data
        self.validate_data()

    def cleanup(self):
        """ Deactivates the company and then deletes it """

        if not self.is_byos_bucket_deleted:
            self.byos_azure_helper.delete_container_azure(self.byos_bucket_name)
        self.azure_helper.azure_helper_cleanup()
        self.hub_management.deactivate_tenant(self.company_name)
        self.hub_management.delete_tenant(self.company_name)

    def run(self):
        try:
            self.configure_new_client()

            self.change_content()

            self.backup(backup_type=RBackup.BackupType.FULL)

            self.object_storage.edit_content_group(self.content_group_name, self.tcinputs['incr_bkp_content'])

            self.backup(backup_type=RBackup.BackupType.INCR)

            time.sleep(60)

            self.backup(backup_type=RBackup.BackupType.SYNTH)

            self.db_helper.run_aux_copy_for_cloud_storage(self.plan)

            self.object_storage.validate_backup_jobs(self.backup_job_list, react=True)

            self.in_place_restore()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
