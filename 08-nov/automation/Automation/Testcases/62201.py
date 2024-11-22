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
    __init__()                      --  initialize TestCase class

    setup()                         --  Method to setup test variables

    cleanup()                       --  Method to clean up automation created entities

    wait_for_job_completion()       --  Waits for completion of job and gets the object once job completes

    navigate_over_guided_setup_page()  --  Navigates through guided setup page to add object storage client

    create_azure_blob_client_key_based() -- to create Azure blob client with key based Authentication

    create_azure_blob_client_iam_vm_auth() -- to create Azure blob client with IAM VM Role Authentication

    create_azure_blob_client_iam_ad_auth() -- to create Azure blob client with IAM AD Authentication

    create_content_group()          --  Creates content group

    backup()                        --  Performs backup for object storage account

    restore()                       --  Runs in-place restore

    validate_data()                 --  Validates data after restore

    delete_azure_blob_account()     --  Method to delete Azure blob clients

    run()                           --  Main method to run the testcase

"""

import time
from Application.CloudStorage.azure_helper import AzureHelper
from AutomationUtils import machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.ObjectStorage.object_details import ObjectDetails
from Web.AdminConsole.ObjectStorage.object_storage import ObjectStorage
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ Testcase to verify Getting started Page operations for Cloud Object Storage in command center
            Example inputs:
        "62201": {
                  "proxy_client": "AUTOMATION_PROXY",
                  "plan": "PLAN",
                  "bucket_name": "BUCKET NAME ON THE CLOUD",
                  "content": "DEFAULT CONTENT FOR OBJECT STORAGE INSTANCE",
                  "s_content": "CONTENT FOR THE CONTENT GROUP",
                  "account_name": "STORAGE ACCOUNT_NAME" ,
                  "access_key": "ACCESS KEY FOR CLOUD HELPER",
                  "tenant_id": "TENANT ID",
                  "app_id": "APPLICATION ID",
                  "app_pwd": "APPLICATION SECRET",
                  "cloud_name": "INSTANCE NAME FOR THE STORAGE ACCOUNT",
                  "subscription_id": "SUBSCRIPTION ID",
        }

    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Getting started Page verification for Cloud Object Storage in command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.object_storage = None
        self.object_details = None
        self.content_group = None
        self.credential_name = None
        self.servers = None
        self.utils = None
        self.azure_helper = None
        self.getting_started = None
        timestamp = str(int(time.time()))
        self.object_storage_name = 'automation-blob-cloud-account-' + timestamp
        self.content_group_name = 'automation_cg'
        self.controller_object = None
        self.original_data_path = None
        self.bucket_name = None
        self.common_dir_path = None
        self.is_automation_account = False

    def setup(self):
        """ Method to set up test variables """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                 self.inputJSONnode["commcell"]["commcellPassword"])
        self.navigator = self.admin_console.navigator

        # Helper objects
        self.getting_started = GettingStarted(self.admin_console)
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.utils = CommonUtils(self)

        # Cloud Connections
        self.azure_helper = AzureHelper(
            access_key=self.tcinputs["access_key"],
            account_name=self.tcinputs["account_name"][1:]
        )

        # Helper variables initialization
        self.controller_object = machine.Machine()
        self.bucket_name = self.tcinputs["bucket_name"]
        self.common_dir_path = self.azure_helper.common_dir_path

        # Cleanup automation credentials
        self.object_storage.cleanup_credentials(hours=5)

    @test_step
    def cleanup(self):
        """Method to clean up automation created entities"""
        if self.azure_helper is not None:
            self.azure_helper.azure_helper_cleanup()

        if self.is_automation_account:
            self.navigator.navigate_to_object_storage()
            self.admin_console.wait_for_completion()
            if self.object_storage.is_account_exists(ObjectStorage.Types.Azure_Blob, self.object_storage_name):
                self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                                 credential_name=self.credential_name)

    @test_step
    def wait_for_job_completion(self, jobid):
        """
        Waits for completion of job and gets the object once job completes
        Args:
            jobid   (str): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(f"Failed to run job:{jobid} with error: {job_obj.delay_reason}")
        self.log.info(f"Successfully finished {jobid} job")

    @test_step
    def navigate_over_guided_setup_page(self):
        """ Navigates through guided setup page to add object storage client """
        self.navigator.navigate_to_getting_started()
        self.admin_console.wait_for_completion()
        self.getting_started.select_card(card_title='Object storage')
        self.admin_console.wait_for_completion()

    @test_step
    def create_azure_blob_client_key_based(self):
        """ to create Azure blob client with key based Authentication """
        self.navigate_over_guided_setup_page()
        self.credential_name = self.object_storage.add_azure_blob_client(
            cloud_name=self.object_storage_name,
            proxy_client=self.tcinputs["proxy_client"],
            plan=self.tcinputs["plan"],
            credential=self.tcinputs.get("credential", ''),
            tenant_id=self.tcinputs["tenant_id"],
            app_id=self.tcinputs["app_id"],
            app_secret_key=self.tcinputs["app_pwd"],
            backup_content=self.tcinputs["account_name"],
            subscription_id=self.tcinputs["subscription_id"]
        )
        self.log.info("Object storage Account created")
        self.is_automation_account = True
        self.commcell.refresh()

        self.navigator.navigate_to_object_storage()
        self.object_storage.access_account(self.object_storage_name)

        self.object_storage.change_auth_type(auth_type="Access key and Account name",
                                             account_name=self.tcinputs['account_name'],
                                             access_key=self.tcinputs['access_key'])

    @test_step
    def create_azure_blob_client_iam_vm_auth(self):
        """ to create Azure blob client"""
        self.navigate_over_guided_setup_page()
        self.credential_name = self.object_storage.add_azure_blob_client(
            cloud_name=self.object_storage_name,
            proxy_client=self.tcinputs["proxy_client"],
            plan=self.tcinputs["plan"],
            credential=self.tcinputs.get("credential", ''),
            tenant_id=self.tcinputs["tenant_id"],
            app_id=self.tcinputs["app_id"],
            app_secret_key=self.tcinputs["app_pwd"],
            backup_content=self.tcinputs["account_name"],
            subscription_id=self.tcinputs["subscription_id"]
        )
        self.log.info("Object storage Account created")
        self.is_automation_account = True
        self.commcell.refresh()

        self.navigator.navigate_to_object_storage()
        self.object_storage.access_account(self.object_storage_name)

        self.object_storage.change_auth_type(auth_type="IAM VM role")

    @test_step
    def create_azure_blob_client_iam_ad_auth(self):
        """ to create Azure blob client"""
        self.navigate_over_guided_setup_page()
        self.credential_name = self.object_storage.add_azure_blob_client(
            cloud_name=self.object_storage_name,
            proxy_client=self.tcinputs["proxy_client"],
            plan=self.tcinputs["plan"],
            credential=self.tcinputs.get("credential", ''),
            tenant_id=self.tcinputs["tenant_id"],
            app_id=self.tcinputs["app_id"],
            app_secret_key=self.tcinputs["app_pwd"],
            backup_content=self.tcinputs["account_name"],
            subscription_id=self.tcinputs["subscription_id"]
        )
        self.log.info("Object storage Account created")
        self.is_automation_account = True
        self.commcell.refresh()

        self.navigator.navigate_to_object_storage()
        self.object_storage.access_account(self.object_storage_name)

    @test_step
    def create_content_group(self):
        """ Creates content group """
        self.admin_console.access_tab(self.admin_console.props['pageHeader.contentGroups'])
        self.object_details.create_content_group(
            self.content_group_name,
            self.tcinputs["plan"],
            [self.tcinputs["s_content"]]
        )
        self.log.info(f"content group {self.content_group_name} created.")

    @test_step
    def backup(self):
        """ Performs backup for object storage account """
        jobid = self.object_details.submit_backup(
                self.content_group_name, RBackup.BackupType.FULL)
        self.wait_for_job_completion(jobid)
        self.log.info("Backup ran Successfully")

    @test_step
    def restore(self):
        """ Runs in-place restore """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.object_storage_name)
        self.object_details.access_restore(self.content_group_name)
        rstr_obj = self.object_details.submit_restore([self.tcinputs["bucket_name"]])
        jobid = rstr_obj.in_place()
        self.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")

    @test_step
    def validate_data(self, restored_data_path):
        """ Validates data after restore
            Args:
                 restored_data_path: the path to which restore has happened.
        """
        self.log.info("original path : %s", self.original_data_path)
        self.log.info("restored path : %s", restored_data_path)
        restore_status = self.controller_object.compare_folders(
            self.controller_object, self.original_data_path, restored_data_path)
        if restore_status is False:
            raise CVTestStepFailure("Restore to Given destination Failed During Validation")
        self.log.info("Restore Validation Succeeded")

    @test_step
    def delete_azure_blob_account(self):
        """ Method to delete Azure blob clients """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                         credential_name=self.credential_name)
        self.log.info("Deleted object Storage account")
        self.is_automation_account = False

    def run(self):
        """ Main method to run the testcase """
        try:
            self.log.info("Access key and Account Name based Authentication")
            self.create_azure_blob_client_key_based()
            self.create_content_group()
            self.backup()
            self.original_data_path = self.controller_object.join_path(self.common_dir_path, 'original')
            self.azure_helper.download_container_azure(
                container_name=self.bucket_name,
                dir_name="original"
            )
            self.azure_helper.delete_container_azure(self.bucket_name)
            self.restore()
            restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored")
            self.azure_helper.download_container_azure(self.bucket_name, "restored")
            self.validate_data(restored_data_path)
            self.delete_azure_blob_account()

            timestamp = str(int(time.time()))
            self.object_storage_name = 'automation-blob-cloud-account-' + timestamp

            self.log.info("IAM AD based Authentication")
            self.create_azure_blob_client_iam_ad_auth()
            self.create_content_group()
            self.backup()
            self.azure_helper.delete_container_azure(self.bucket_name)
            self.restore()
            restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_iam_ad")
            self.azure_helper.download_container_azure(self.bucket_name, "restored_iam_ad")
            self.validate_data(restored_data_path)
            self.delete_azure_blob_account()

            timestamp = str(int(time.time()))
            self.object_storage_name = 'automation-blob-cloud-account-' + timestamp

            self.log.info("IAM VM Role Authentication")
            self.create_azure_blob_client_iam_vm_auth()
            self.create_content_group()
            self.backup()
            self.azure_helper.delete_container_azure(self.bucket_name)
            self.restore()
            restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_iam_vm")
            self.azure_helper.download_container_azure(self.bucket_name, "restored_iam_vm")
            self.validate_data(restored_data_path)
            self.delete_azure_blob_account()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
