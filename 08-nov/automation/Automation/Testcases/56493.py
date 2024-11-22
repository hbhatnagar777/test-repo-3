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

    cleanup()                       --  Deletes instance if it is created by automation

    create_s3_objstorage_client()   --  Creation of Amazon S3 Cloud Object Storage Account

    in_place_restore()              --  Runs in-place restore

    out_of_place_restore()          --  Runs out-of-place restore

    run()                               --  run function of this test case

"""
import os
import time

from Application.CloudStorage.s3_helper import S3Helper
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.AdminConsolePages.credential_manager import CredentialManager
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.ObjectStorage.content_group import ContentGroup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.ObjectStorage.object_storage import ObjectStorage
from Web.AdminConsole.ObjectStorage.object_details import ObjectDetails
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Application.CloudStorage.azure_helper import AzureHelper


class TestCase(CVTestCase):
    """ Basic acceptance Test for Amazon S3 Cloud Object Storage from command center
            Example inputs:
                "56493": {
                "oss_client_name": "AUTOMATION_CLIENT",
                "proxy_client":"AUTOMATION_PROXY",
                "plan": "PLAN",
                "credential": "AUTOMATION_CREDENTIAL",
                "access_key_s3": "ACCESS_KEY_S3",
                "secret_key_s3": "SECRET_KEY_S3",
                "account_name" : "ACCOUNT_NAME" ,
                "access_key" : "ACCESS KEY FOR CLOUD HELPER",
                "bucket_name": "BUCKET NAME PRESENT ON THE CLOUD VENDOR",
                "url": "URL OF THE CLOUD VENDOR",
                "content": "DEFAULT CONTENT FOR OBJECT STORAGE INSTANCE",
                "edit_content": "CONTENT TO ADD BEFORE INCREMENTAL BACKUP",
                "dest_cloud": "CROSS CLOUD DESTINATION CLIENT ON CS",
                "dest_cloud_path": "PATH ON THE CLOUD DESTINATION CLIENT",
                "dest_fs_client": "DESTINATION MACHINE FOR DISK RESTORE",
                "s_content" : "CONTENT FOR THE CONTENT GROUP"
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
        self.a_acls = None
        self.b_acls = None
        self.a_user_metadata = None
        self.b_user_metadata = None
        self.a_sys_metadata = None
        self.name = "ACC1 for Amazon S3 Object Storage Access and Secret Keys from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.driver = None
        self.object_storage = None
        self.object_details = None
        self.object_storage_name = None
        self.s3_session = None
        self.utils = None
        self.credential_manager = None
        self.servers = None
        self.content_group_name = 'automation_cg'
        self.backup_job_list = set()
        self.db_helper = None
        self.content_group = None
        self.is_automation_account = False
        self.is_automation_credential = False
        self.controller_object = None
        self.destination_bucket = None
        self.bucket_name = None
        self.azure_helper = None
        self.common_dir_path = None
        self.b_sys_metadata = None
        self.object_storage_name = None
        self.credential_name = None
        self.session = None
        self.b_metadata = None
        self.b_tags = None
        self.a_tags = None
        self.a_metadata = None
        self.original_data_path = None
        self.restored_data_path = None
        self.s3_storage_helper = None
        self.google_helper = None
        self.s3_bucket_name = None
        self.out_of_place_restore_path = None
        self.endpoint = None
        self.is_azure_bucket_created = False
        self.default_subclient_content = []
        self.tcinputs = {
            "oss_client_name": None,
            "proxy_client": None,
            "plan": None,
            "access_key_s3": None,
            "secret_key_s3": None,
            "bucket_name": None,
            "url": None,
            "content": None,
            "edit_content": None,
            "dest_cloud": None,
            "dest_cloud_path": None,
            "dest_fs_client": None,
            "s_content": None,
        }

    def setup(self):
        """Setup function of this test case"""

        # Open up browser and initialize navigator
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                 self.inputJSONnode["commcell"]["commcellPassword"])
        self.navigator = self.admin_console.navigator

        # Helper objects
        self.utils = CommonUtils(self)
        self.servers = Servers(self.admin_console)
        self.object_storage_name = self.tcinputs["oss_client_name"]
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.credential_manager = CredentialManager(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.db_helper = DbHelper(self.commcell)

        # For cloud applications
        self.azure_helper = AzureHelper(account_name=self.tcinputs.get('account_name'),
                                        access_key=self.tcinputs.get("access_key"))
        self.s3_storage_helper = S3Helper(self)
        self.s3_session = self.s3_storage_helper.create_session_s3(
            self.tcinputs["access_key_s3"],
            self.tcinputs["secret_key_s3"],
            'us-east-1'
        )

        # Helper variables initialization
        self.controller_object = machine.Machine()
        self.bucket_name = self.tcinputs["bucket_name"]
        self.common_dir_path = self.azure_helper.common_dir_path
        self.destination_bucket = self.tcinputs.get('dest_cloud_path')[1:]
        self.default_subclient_content = [self.tcinputs.get('content')]

        # Cleanup automation credentials
        self.object_storage.cleanup_credentials(hours=5)

    @test_step
    def create_s3_objstorage_client(self):
        """ Creation of Amazon S3 Cloud Object Storage Account """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()

        if self.object_storage.is_account_exists(
                ObjectStorage.Types.Amazon_S3,
                self.object_storage_name):
            self.log.info("Object Storage Account found!- Deleting it")
            self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                             credential_name=self.credential_name)
            self.navigator.navigate_to_object_storage()
            self.admin_console.wait_for_completion()

        self.credential_name = self.object_storage.add_object_storage_client(
            name=self.object_storage_name,
            proxy_client=self.tcinputs["proxy_client"],
            auth_type="Access and secret keys",
            plan=self.tcinputs["plan"],
            credential=self.tcinputs.get("credential", ''),
            access_key=self.tcinputs["access_key_s3"],
            secret_key=self.tcinputs["secret_key_s3"],
            backup_content=self.default_subclient_content,
            url=self.tcinputs["url"],
            vendor_name='Amazon S3'
        )
        self.log.info("Object storage Account created")
        self.is_automation_account = True
        if self.tcinputs.get("credential", '') == "":
            self.is_automation_credential = True
        self.commcell.refresh()
        self._client = self.commcell.clients.get(self.object_storage_name)
        self._agent = self._client.agents.get('Cloud Apps')
        self._instance = self._agent.instances.get(self.object_storage_name)

    @test_step
    def validate_data(self, in_place_restore=False):
        """ Validates data after restore"""

        self.log.info("original path : %s", self.original_data_path)
        self.log.info("restored path : %s", self.restored_data_path)

        restore_status = self.controller_object.compare_folders(self.controller_object,
                                                                self.original_data_path,
                                                                self.restored_data_path)
        if len(restore_status) > 0:
            raise CVTestStepFailure("Restore to Given destination Failed During Validation")
        if in_place_restore:
            self.db_helper.compare_dictionaries(self.b_sys_metadata, self.a_sys_metadata)
            self.log.info("System Defined Metadata validation completed no mismatching before and after restore")
            self.db_helper.compare_dictionaries(self.b_user_metadata, self.a_user_metadata)
            self.log.info("User Defined Metadata validation completed no mismatching before and after restore")
            self.db_helper.compare_dictionaries(self.b_acls, self.a_acls)
            self.log.info("ACLs validation completed no mismatching before and after restore")
            self.db_helper.compare_dictionaries(self.b_tags, self.a_tags)
            self.log.info("Tags validation completed no mismatching before and after restore")
        self.log.info("Restore Validation Succeeded")

    @test_step
    def initialize_data_before_restore(self):
        """Initializes data and metadata for validation before restore job starts"""
        self.original_data_path = self.controller_object.join_path(self.common_dir_path, 'original_contents')
        self.b_acls = self.s3_storage_helper.get_bucket_and_objects_acls(self.s3_session, self.tcinputs["bucket_name"])
        self.b_user_metadata = self.s3_storage_helper.get_objects_user_defined_metadata(self.s3_session,
                                                                                        self.tcinputs["bucket_name"])
        self.b_sys_metadata = self.s3_storage_helper.get_objects_metadata(self.s3_session,
                                                                          self.tcinputs["bucket_name"])
        self.b_tags = self.s3_storage_helper.get_bucket_and_objects_tags(self.s3_session, self.tcinputs["bucket_name"])
        self.s3_storage_helper.download_s3_bucket(s3_session=self.s3_session, bucket_name=self.bucket_name,
                                                  path=self.original_data_path)

    @test_step
    def initialize_data_after_restore(self, destination_folder):
        """Initializes data and metadata for validation after restore job completes
            Args:
                destination_folder(str):    destination folder to which data gets downloaded for validation.
        """
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, destination_folder)
        self.a_acls = self.s3_storage_helper.get_bucket_and_objects_acls(self.s3_session, self.tcinputs["bucket_name"])
        self.a_user_metadata = self.s3_storage_helper.get_objects_user_defined_metadata(self.s3_session,
                                                                                        self.tcinputs["bucket_name"])
        self.a_sys_metadata = self.s3_storage_helper.get_objects_metadata(self.s3_session,
                                                                          self.tcinputs["bucket_name"])
        self.a_tags = self.s3_storage_helper.get_bucket_and_objects_tags(self.s3_session, self.tcinputs["bucket_name"])
        self.s3_storage_helper.download_s3_bucket(s3_session=self.s3_session, bucket_name=self.bucket_name,
                                                  path=self.restored_data_path)

    @test_step
    def in_place_restore(self):
        """ Runs in-place restore """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.object_storage_name)
        self.object_details.access_restore(self.content_group_name)
        self.initialize_data_before_restore()
        self.s3_storage_helper.empty_container_s3(self.s3_session, self.bucket_name)
        time.sleep(60)
        rstr_obj = self.object_details.submit_restore([self.bucket_name])
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")
        self.initialize_data_after_restore("restored_contents")
        self.validate_data(in_place_restore=True)

    @test_step
    def out_of_place_restore(self):
        """ Runs out-of-place restore """
        rstr_obj = self.object_details.submit_restore([self.bucket_name])
        jobid = rstr_obj.out_of_place(
            self.tcinputs["dest_cloud"], self.tcinputs["dest_cloud_path"]
        )
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")
        self.restored_data_path = self.controller_object.join_path(self.azure_helper.common_dir_path, 'out_of_place')
        self.log.info("Downloading bucket started........")
        self.azure_helper.download_container_azure(self.destination_bucket, 'out_of_place')
        self.log.info("Downloading bucket done!")
        self.validate_data()
        self.is_azure_bucket_created = True

    @test_step
    def cleanup(self):
        """ cleaning up object storage client/credential if created by automation """
        if self.azure_helper is not None:
            self.azure_helper.azure_helper_cleanup()

        if self.is_azure_bucket_created:
            self.azure_helper.delete_container_azure(self.destination_bucket)

        if self.is_automation_account:
            self.navigator.navigate_to_object_storage()
            self.admin_console.wait_for_completion()
            if self.object_storage.is_account_exists(
                    ObjectStorage.Types.Amazon_S3,
                    self.object_storage_name):
                self.log.info("Object Storage Account found!- Deleting it")
                self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                                 credential_name=self.credential_name)

    def run(self):
        """Run function of this test case"""
        try:
            # Create the object storage
            self.create_s3_objstorage_client()

            # Compare and validate the data present in the default content group vs the input given
            self.object_storage.validate_default_subclient_content(self.default_subclient_content)

            # Create another content group for the object store instance with the name 'content_group_name'
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

            # Validate the backup jobs
            self.object_storage.validate_backup_jobs([full_jobid, incr_jobid, synth_jobid], react=True)

            # Restore
            self.in_place_restore()

            self.out_of_place_restore()

            self.original_data_path = self.controller_object.join_path(self.original_data_path,
                                                                       self.tcinputs.get('bucket_name'))

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
