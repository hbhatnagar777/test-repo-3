# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Azure Blob Acceptance case for Metallic Hub

TestCase:
    __init__()                   --  initialize TestCase class

    setup()                     --  Setup function of this test case

    run()                       --  run function of this test case

    login()                     -- Performs login to Metallic Hub and Admin Console

    create_tenant()             --  Create a new tenant for the automation

    configure_new_client()      --  Configures New Azure Blob Object Storage Client

    change_content()            -- Change the default content from All contents to specified content

    run_backup()                --  Runs Backup and waits for backup job to finish

    run_restore()               --  Runs a Restore from Admin Console

    delete_account()            --  Deletes the Azure Blob ObjectStorage Account

    wait_for_backup_job_completion()    --  Gets the Backup Job submitted from Metallic and waits for completion

    validate_data()   -- Validates restored files by checking if the files exists and comparing sizes

    init_admin_console_objects()    --  Initializes Objects required by Admin Console

Input Example:

    "testCases":
            {
                "63649": {
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
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.ObjectStorage.content_group import ContentGroup
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.constants import FileObjectTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Hub.CCObjectStorage.object_storage import RAzureObjectStorageInstance
from Metallic.hubutils import HubManagement
from Web.AdminConsole.ObjectStorage.object_storage import ObjectStorage
from Web.AdminConsole.ObjectStorage.object_details import ObjectDetails
from AutomationUtils import machine
from AutomationUtils.config import get_config
import time
import datetime
from cvpysdk.commcell import Commcell
from Application.CloudStorage.azure_helper import AzureHelper
from Web.AdminConsole.AdminConsolePages.Servers import Servers


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Azure Blob Acceptance with IAM AD authentication for Metallic using Infrastructure Nodes"
        self.browser = None
        self.object_storage_obj = None
        self.tenant_password = None
        self.a_metadata = None
        self.b_metadata = None
        self.db_helper = None
        self.a_tags = None
        self.b_tags = None
        self.admin_console = None
        self.navigator = None
        self.driver = None
        self.commcell = None
        self.object_storage = None
        self.page_container = None
        self.client_name = None
        self.object_details = None
        self.account_name = None
        self.account_key = None
        self.cloud_storage_loc = None
        self.plan = None
        self.file_service = None
        self.browse = None
        self.service = None
        self.app_type = None
        self.hub_dashboard = None
        self.oss_metallic_helper = None
        self.company_name = None
        self.tenant_user_name = None
        self.hub_management = None
        self.utils = TestCaseUtils(self)
        self.azure_helper = None
        self.common_dir_path = None
        self.controller_object = None
        self.original_data_path = None
        self.restored_data_path = None
        self.backup_job_list = set()
        self.bucket_name = None
        self.content_group_name = 'default'
        self.content_group = None
        self.config = None
        self.byos_azure_helper = None
        self.byos_bucket_name = None
        self.resource_group_name = None
        self.backup_gateway_name = None
        self.is_byos_bucket_deleted = False
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
        """Setup function of this test case"""
        self.hub_management = HubManagement(
            testcase_instance=self,
            commcell=self.commcell.webconsole_hostname,
        )
        self.hub_management.delete_companies_with_prefix(prefix='AzureBlob-iam-ad')
        self.create_tenant()
        self.config = get_config()
        self.tenant_password = self.config.Metallic.tenant_password
        self.commcell = Commcell(webconsole_hostname=self.commcell.webconsole_hostname,
                                 commcell_username=self.tenant_user_name,
                                 commcell_password=self.tenant_password)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.client_name = f'azureblobclient{str(int(time.time()))}'
        self.account_name = self.tcinputs.get("accountName")
        self.account_key = self.tcinputs.get("accountKey")
        self.plan = f'azureblobplan{str(int(time.time()))}'
        self.admin_console.login(username=self.tenant_user_name,
                                 password=self.tenant_password,
                                 stay_logged_in=True)
        self.admin_console.wait_for_completion()
        self.service = HubServices.file_system
        self.app_type = FileObjectTypes.object_storage
        self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
        self.azure_helper = AzureHelper(account_name=self.tcinputs["accountName"],
                                        access_key=self.tcinputs["accountKey"])
        self.byos_azure_helper = AzureHelper(account_name=self.tcinputs.get('byos_account_name'),
                                             access_key=self.tcinputs.get('byos_access_key'))
        self.common_dir_path = self.azure_helper.common_dir_path
        self.controller_object = machine.Machine()
        self.bucket_name = self.tcinputs["full_bkp_content"].split('/')[0]
        self.db_helper = DbHelper(self.commcell)

    def create_tenant(self):
        """
        Create a new tenant for the automation
        """
        self.company_name = datetime.datetime.now().strftime("AzureBlob-iam-ad-%d-%B-%H-%M")
        user_firstname = "AzureBlob" + str(int(time.time()))
        user_lastname = "user"
        user_email = user_firstname + user_lastname + '@domain.com'
        user_phonenumber = '00000000'
        user_country = self.tcinputs.get("UserCountry", "United States")

        self.log.info(f"Creating Tenant with Company name {self.company_name}")

        # Create a tenant and get password that is returned
        self.tenant_user_name = self.hub_management.create_tenant(
            company_name=self.company_name,
            email=user_email,
            first_name=user_firstname,
            last_name=user_lastname,
            phone_number=user_phonenumber,
            country=user_country
        )

        time.sleep(30)

    @test_step
    def upgrade_client_software(self, client):
        """
        Method to submit software upgrade for a client from UI
        Args:
            client      (object)    :   client object
        """
        self.navigator.navigate_to_servers()
        self.admin_console.refresh_page()
        servers = Servers(self.admin_console)
        job = servers.action_update_software(client_name=client)
        self.db_helper.wait_for_job_completion(job)
        self.log.info("Client software Upgrade successful.")

    @test_step
    def configure_new_client(self):
        """ Configures New Azure Files Object Storage Client"""
        self.byos_bucket_name = f'blob-byos-{int(time.time())}'
        self.oss_metallic_helper = RAzureObjectStorageInstance(self.admin_console, 'Azure Blob', self.commcell)
        self.resource_group_name, self.backup_gateway_name = self.oss_metallic_helper.configure(
            self.byos_bucket_name,
            self.plan,
            self.client_name,
            account_name=self.tcinputs.get('accountName'),
            tenant_id=self.tcinputs.get('tenant_id'),
            application_id=self.tcinputs.get('application_id'),
            app_password=self.tcinputs.get('app_password'),
            byos_account_name=self.tcinputs.get('byos_account_name'),
            byos_access_key=self.tcinputs.get('byos_access_key'),
            auth_type='IAM AD application',
            vendor_name='Azure Blob',
            gateway_os_type='Windows',
            rg_location='East US 2',
            backup_method='Gateway',
            subscription_id=self.tcinputs.get('subscription_id'))
        self.admin_console.refresh_page()
        self.navigator = self.admin_console.navigator
        self.upgrade_client_software(self.backup_gateway_name)
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.page_container = PageContainer(self.admin_console)

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
    def change_content(self):
        """ Changes the default content of a new instance from all files to specified content """
        self.navigator.navigate_to_object_storage()
        self.object_storage.access_account(self.client_name)
        self.object_storage.edit_content_group(self.content_group_name, self.tcinputs['full_bkp_content'])
        self.log.info("Default group content updated successfully")
        self.page_container.click_breadcrumb(self.tcinputs['accountName'])
        self.admin_console.access_tab(self.admin_console.props['pageHeader.contentGroups'])

    @test_step
    def in_place_restore(self):
        """ Runs in-place restore """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.client_name)
        self.object_details.access_restore(self.content_group_name)
        self.original_data_path = self.controller_object.join_path(self.common_dir_path, 'original_contents')
        self.azure_helper.download_container_azure(container_name=self.bucket_name, dir_name="original_contents")
        self.b_metadata = self.azure_helper.get_metadata(container_name=self.bucket_name)
        self.b_tags = self.azure_helper.get_tags(container_name=self.bucket_name)
        self.azure_helper.delete_container_azure(container_name=self.bucket_name)
        time.sleep(60)
        rstr_obj = self.object_details.submit_restore([self.bucket_name])
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents")
        self.azure_helper.download_container_azure(container_name=self.bucket_name, dir_name="restored_contents")
        self.a_metadata = self.azure_helper.get_metadata(container_name=self.bucket_name)
        self.a_tags = self.azure_helper.get_tags(container_name=self.bucket_name)
        self.validate_data()
        self.azure_helper.delete_container_azure(container_name=self.bucket_name)
        self.log.info(f"Deleting BYOS {self.byos_bucket_name} bucket.......")
        self.byos_azure_helper.delete_container_azure(container_name=self.byos_bucket_name)
        self.is_byos_bucket_deleted = True
        self.log.info("Deletion of BYOS bucket successfull")
        time.sleep(60)
        rstr_obj = self.object_details.submit_restore([self.bucket_name], copy='Secondary')
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job from secondary ran Successfully")
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents_secondary")
        self.azure_helper.download_container_azure(container_name=self.bucket_name,
                                                   dir_name="restored_contents_secondary")
        self.a_metadata = self.azure_helper.get_metadata(container_name=self.bucket_name)
        self.a_tags = self.azure_helper.get_tags(container_name=self.bucket_name)
        self.validate_data()

    @test_step
    def validate_data(self):
        """ Validates data after restore"""

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
        self.db_helper.compare_dictionaries(self.b_tags, self.a_tags)
        self.log.info("Objects tags validation completed")

    def cleanup(self):
        """deactivates the company and then deletes it"""
        if not self.is_byos_bucket_deleted:
            self.byos_azure_helper.delete_container_azure(self.byos_bucket_name)
        self.azure_helper.azure_helper_cleanup()
        self.hub_management.deactivate_tenant(self.company_name)
        self.hub_management.delete_tenant(self.company_name)

        if self.resource_group_name:
            self.oss_metallic_helper.azure_cleanup(self.resource_group_name)

    def run(self):
        try:
            self.configure_new_client()

            self.change_content()

            self.backup(RBackup.BackupType.FULL)

            self.object_storage.edit_content_group(self.content_group_name, self.tcinputs['incr_bkp_content'])

            self.backup(RBackup.BackupType.INCR)

            time.sleep(60)

            self.backup(RBackup.BackupType.SYNTH)

            self.db_helper.run_aux_copy_for_cloud_storage(self.plan)

            self.object_storage.validate_backup_jobs(self.backup_job_list, react=True)

            self.in_place_restore()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)