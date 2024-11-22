# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  initialize TestCase class

    setup()                             --  setup function of this test case

    wait_for_job_completion()           --stops execution until current job completes

    login()                             -- logins to the commcell with given credentials

    add_azure_blob_oss_client()         -- creates a azure blob client

    in_place_restore()                  --  Runs in-place restore

    validate_data()                     --  Validates data after restore

    change_content()                    --  change the default content from all contents to specified default

    run()                               --  run function of this test case

"""
import time
from Application.CloudStorage.google_storage_helper import GoogleObjectStorage
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.ObjectStorage.content_group import ContentGroup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.ObjectStorage.object_storage import ObjectStorage
from Web.AdminConsole.ObjectStorage.object_details import ObjectDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Application.CloudStorage.azure_helper import AzureHelper


class TestCase(CVTestCase):
    """ Basic acceptance Test for Azure Blob Object Storage IAM AD Authentication from command center
        Example inputs:
        "60732": {
                  "proxy_client": "AUTOMATION_PROXY",
                  "plan": "PLAN",
                  "s_content": "CONTENT FOR THE CONTENT GROUP",
                  "bucket_name": "BUCKET NAME ON THE CLOUD",
                  "content": "DEFAULT CONTENT FOR OBJECT STORAGE INSTANCE",
                  "edit_content": "/automation-container",
                  "account_name": "STORAGE ACCOUNT_NAME" ,
                  "access_key": "ACCESS KEY FOR CLOUD HELPER",
                  "tenant_id": "TENANT ID",
                  "app_id": "APPLICATION ID",
                  "app_pwd": "APPLICATION SECRET",
                  "subscription_id": "SUBSCRIPTION ID",
                  "dest_cloud": "CROSS CLOUD DESTINATION CLIENT ON CS",
                  "dest_cloud_path": "PATH ON THE CLOUD DESTINATION CLIENT",
                  "dest_fs_client": "DESTINATION MACHINE FOR DISK RESTORE",
            }
    """

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "ACCT1 for Azure Blob IAM AD Auth from Command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.driver = None
        self.object_storage = None
        self.object_details = None
        self.object_storage_name = None
        self.utils = None
        self.gcp_bucket_name = None
        self.credential_manager = None
        self.servers = None
        self.content_group_name = 'automation_cg'
        self.backup_job_list = set()
        self.db_helper = None
        self.content_group = None
        self.is_automation_account = False
        self.is_automation_credential = False
        self.controller_object = None
        self.bucket_name = None
        self.azure_helper = None
        self.common_dir_path = None
        self.object_storage_name = None
        self.credential_name = None
        self.session = None
        self.b_metadata = None
        self.b_tags = None
        self.a_tags = None
        self.a_metadata = None
        self.original_data_path = None
        self.restored_data_path = None
        self.s3_helper = None
        self.google_helper = None
        self.s3_bucket_name = None
        self.out_of_place_restore_path = None
        self.endpoint = None
        self.is_gcp_bucket_created = False
        self.default_subclient_content = []
        self.tcinputs = {
            "proxy_client": None,
            "plan": None,
            "account_name": None,
            "content": None,
            "dest_cloud": None,
            "dest_cloud_path": None,
            "dest_fs_client": None,
            "tenant_id": None,
            "app_id": None,
            "app_pwd": None,
            "subscription_id": None,
            "s_content": None,
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                 self.inputJSONnode["commcell"]["commcellPassword"])
        self.navigator = self.admin_console.navigator
        # Helper objects
        self.servers = Servers(self.admin_console)
        t = time.localtime()
        self.object_storage_name = f"automation-blob-{t.tm_mday}-{t.tm_mon}-{t.tm_hour}{t.tm_min}{t.tm_sec}"
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.db_helper = DbHelper(self.commcell)

        # For Cloud connections
        self.azure_helper = AzureHelper(account_name=self.tcinputs.get('account_name')[1:],
                                        access_key=self.tcinputs.get("access_key"))
        self.google_helper = GoogleObjectStorage(testcase_object=self, ignore_tc_props=True)

        # Helper variables initialization
        self.controller_object = machine.Machine()
        self.bucket_name = self.tcinputs["bucket_name"]
        self.common_dir_path = self.azure_helper.common_dir_path
        self.gcp_bucket_name = self.tcinputs["dest_cloud_path"][1:]
        self.default_subclient_content = [self.tcinputs.get('content')]

        # Cleanup automation credentials
        self.object_storage.cleanup_credentials(hours=5)

    @test_step
    def add_azure_blob_oss_client(self):
        """
        creates the azure blob client
        """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()

        if self.object_storage.is_account_exists(ObjectStorage.Types.Azure_Blob, self.object_storage_name):
            self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                             credential_name=self.credential_name)
            self.navigator.navigate_to_object_storage()

        self.credential_name = self.object_storage.add_object_storage_client(
            name=self.object_storage_name,
            proxy_client=self.tcinputs["proxy_client"],
            auth_type='IAM AD application',
            plan=self.tcinputs["plan"],
            credential=self.tcinputs.get("credential", ''),
            tenant_id=self.tcinputs["tenant_id"],
            app_id=self.tcinputs["app_id"],
            app_secret_key=self.tcinputs["app_pwd"],
            backup_content=self.tcinputs["account_name"],
            url='blob.core.windows.net',
            vendor_name='Azure Blob',
            cloud_name=self.object_storage_name,
            subscription_id=self.tcinputs["subscription_id"]
        )

        self.log.info("Object storage Account created")
        self.is_automation_account = True
        if not self.tcinputs.get("credential"):
            self.is_automation_credential = True
        self.commcell.refresh()

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
        self.db_helper.compare_dictionaries(self.b_metadata, self.a_metadata)
        self.log.info("Objects Metadata validation completed no mismatching before and after restore")
        self.db_helper.compare_dictionaries(self.b_tags, self.a_tags)
        self.log.info("Objects tags validation completed")
        self.log.info("Restore Validation Succeeded")

    @test_step
    def in_place_restore(self):
        """ Runs in-place restore """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.object_storage_name)
        self.object_details.access_restore(self.content_group_name)
        self.original_data_path = self.controller_object.join_path(self.common_dir_path, 'original_contents')
        self.log.info("Downloading container from cloud")
        self.azure_helper.download_container_azure(container_name=self.bucket_name, dir_name="original_contents")
        self.log.info("Downloading bucket done!")
        self.log.info("Fetching metdata and tags")
        self.b_metadata = self.azure_helper.get_metadata(container_name=self.bucket_name)
        self.b_tags = self.azure_helper.get_tags(container_name=self.bucket_name)
        self.log.info("Deleting container from cloud before restore")
        self.azure_helper.delete_container_azure(self.bucket_name)
        time.sleep(60)
        rstr_obj = self.object_details.submit_restore([self.tcinputs["bucket_name"]])
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")
        self.log.info("Fetching metdata and tags")
        self.a_metadata = self.azure_helper.get_metadata(container_name=self.bucket_name)
        self.a_tags = self.azure_helper.get_tags(container_name=self.bucket_name)
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents")
        self.log.info("Downloading container from cloud")
        self.azure_helper.download_container_azure(self.bucket_name, "restored_contents")
        self.log.info("Downloading bucket done!")
        self.validate_data()

    @test_step
    def out_of_place_restore(self):
        """ Runs out-of-place restore """
        rstr_obj = self.object_details.submit_restore([self.tcinputs["bucket_name"]])
        jobid = rstr_obj.out_of_place(
            self.tcinputs["dest_cloud"], self.tcinputs["dest_cloud_path"]
        )
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, 'out_of_place')
        self.log.info("Downloading bucket started........")
        self.google_helper.download_google_bucket(self.gcp_bucket_name, "out_of_place")
        self.log.info("Downloading bucket done!")
        self.restored_data_path = self.controller_object.join_path(self.google_helper.common_dir_path,
                                                                   'out_of_place',
                                                                   self.tcinputs.get("bucket_name"))
        self.validate_data()
        self.is_gcp_bucket_created = True

    @test_step
    def cleanup(self):
        """ cleaning up object storage client/credential if created by automation """
        if self.azure_helper is not None:
            self.azure_helper.azure_helper_cleanup()

        if self.is_gcp_bucket_created:
            self.google_helper.delete_bucket(self.gcp_bucket_name)
            self.google_helper.google_helper_cleanup()

        if self.is_automation_account:
            self.navigator.navigate_to_object_storage()
            self.admin_console.wait_for_completion()
            if self.object_storage.is_account_exists(ObjectStorage.Types.Azure_Blob, self.object_storage_name):
                self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                                 credential_name=self.credential_name)

    def run(self):
        """Run function of this test case"""
        try:
            # Create the object storage
            self.add_azure_blob_oss_client()

            # Access the created instance
            self.navigator.navigate_to_object_storage()
            self.object_storage.access_account(self.object_storage_name)

            # Compare and validate the data present in the default content group vs the input given
            self.object_storage.validate_default_subclient_content(self.default_subclient_content)

            self.object_storage.create_content_group(object_storage_name=self.object_storage_name,
                                                     content=self.tcinputs["s_content"],
                                                     plan=self.tcinputs["plan"],
                                                     content_group_name=self.content_group_name)

            # Run a full backup on the content group
            full_jobid = self.object_storage.backup(RBackup.BackupType.FULL, self.content_group_name)

            # Add files for the content group
            self.object_storage.edit_content_group(self.content_group_name, self.bucket_name)

            # Run an incremental backup
            incr_jobid = self.object_storage.backup(RBackup.BackupType.INCR, self.content_group_name)

            # Add delay between incremental and synth-full
            time.sleep(60)

            # Run a synthetic full backup
            synth_jobid = self.object_storage.backup(RBackup.BackupType.SYNTH, self.content_group_name)

            time.sleep(10)

            # Validate the backup jobs
            self.object_storage.validate_backup_jobs([full_jobid, incr_jobid, synth_jobid], react=True)

            # Restore
            self.in_place_restore()

            self.out_of_place_restore()

            self.object_storage.restore_to_disk(source_path=self.original_data_path, bucket_name=self.bucket_name,
                                                dest_fs_client=self.tcinputs.get('dest_fs_client'))

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
