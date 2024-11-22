# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  Method to setup test variables

    wait_for_job_completion()       --  Waits for completion of job and gets the object once job completes

    cleanup()                       --  Deletes instance if it is created by automation

    create_gcp_objstorage_client()  --  Creation of Google Cloud Object Storage Account

    in_place_restore()              --  Runs in-place restore

    out_of_place_restore()          --  Runs out-of-place restore

    run()                               --  run function of this test case

"""

import time
from Application.CloudStorage.google_storage_helper import GoogleObjectStorage
from Application.CloudStorage.alibaba_helper import Alibaba
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import constants, config
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.ObjectStorage.object_storage import ObjectStorage
from Web.AdminConsole.ObjectStorage.object_details import ObjectDetails
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.ObjectStorage.content_group import ContentGroup


class TestCase(CVTestCase):
    """ Basic acceptance Test for Google Cloud Object Storage from command center
        Example inputs:
        "55026": {
              "oss_client": "CLIENT NAME",
              "proxy_client": "ACCESS NODE",
              "plan": "PLAN",
              "s_content": "CONTENT FOR THE CONTENT GROUP",
              "bucket_name": "BUCKET NAME ON THE CLOUD",
              "content": "DEFAULT CONTENT FOR OBJECT STORAGE INSTANCE",
              "access_key" : "ACCESS KEY FOR GCP"
              "secret_key" : "SECRET KEY FOR GCP"
              "ali_endpoint" : "ENDPOINT OF ALIBABA CLOUD"
              "ali_access_key": "ACCESS KEY FOR CLOUD HELPER",
              "ali_secret_key": "SECRET KEY FOR CLOUD HELPER",
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
        self.controller_object = None
        self.name = "ACC1 for Google cloud Object Storage from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.driver = None
        self.config = None
        self.object_storage = None
        self.credential_name = None
        self.object_details = None
        self.default_subclient_content = None
        self.content_group = None
        self.is_ali_bucket_created = False
        self.destination_bucket = None
        self.common_dir_path = None
        self.azure_helper = None
        self.is_automation_credential = False
        self.servers = None
        self.restored_data_path = None
        self.db_helper = None
        self.is_automation_account = None
        self.content = []
        self.object_storage_name = None
        self.content_group_name = 'automation_cg'
        self.backup_job_list = set()
        self.ali_helper = None
        self.google_helper = None
        self.session = None
        self.bucket_name = None
        self.original_data_path = None
        self.utils = None
        self.tcinputs = {
            "proxy_client": None,
            "plan": None,
            "access_key": None,
            "secret_key": None,
            "bucket_name": None,
            "url": None,
            "content": None,
            "s_content": None,
            "dest_cloud": None,
            "dest_cloud_path": None,
            "dest_fs_client": None
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

        # Initialize objects
        self.utils = CommonUtils(self)
        self.config = config.get_config()
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.db_helper = DbHelper(self.commcell)

        # Cloud Helpers
        self.google_helper = GoogleObjectStorage(testcase_object=self, ignore_tc_props=True)

        self.ali_helper = Alibaba(access_key=self.tcinputs['ali_access_key'],
                                  secret_key=self.tcinputs['ali_secret_key'])

        # Initialize variables
        self.controller_object = self.google_helper.controller_object
        self.default_subclient_content = [self.tcinputs.get('content')]
        self.bucket_name = self.tcinputs["bucket_name"]
        self.common_dir_path = self.google_helper.common_dir_path
        self.destination_bucket = self.tcinputs.get('dest_cloud_path')[1:]
        self.object_storage_name = self.tcinputs["oss_client_name"]

        # Cleanup automation credentials
        self.object_storage.cleanup_credentials(hours=5)

    @test_step
    def create_gcp_client(self):
        """ Creation of GCP Cloud Object Storage Account """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        if self.object_storage.is_account_exists(
                ObjectStorage.Types.GOOGLE,
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
            access_key=self.tcinputs["access_key"],
            secret_key=self.tcinputs["secret_key"],
            backup_content=self.default_subclient_content,
            url=self.tcinputs["url"],
            vendor_name='Google Cloud'
        )
        self.log.info("Object storage Account created")
        self.is_automation_account = True
        if self.tcinputs.get("credential", '') == "":
            self.is_automation_credential = True

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

    @test_step
    def in_place_restore(self):
        """ Runs in-place restore """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.object_storage_name)
        self.object_details.access_restore(self.content_group_name)
        self.google_helper.download_google_bucket(self.bucket_name, "original_contents")
        self.original_data_path = self.google_helper.controller_object.join_path(self.google_helper.common_dir_path,
                                                                                 'original_contents')
        self.google_helper.delete_bucket(self.bucket_name)
        time.sleep(30)
        rstr_obj = self.object_details.submit_restore([self.bucket_name])
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.google_helper.download_google_bucket(self.bucket_name, "restored_contents")
        self.restored_data_path = self.google_helper.controller_object.join_path(self.google_helper.common_dir_path,
                                                                                 "restored_contents")
        self.log.info("Restore job ran Successfully")
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
        self.restored_data_path = self.controller_object.join_path(self.ali_helper.common_dir_path, "out_of_place")
        self.log.info("Downloading bucket started........")
        self.ali_helper.download_bucket(bucket_name=self.destination_bucket, endpoint=self.tcinputs['ali_endpoint'],
                                        dir_name='out_of_place')
        self.restored_data_path = self.controller_object.join_path(self.restored_data_path, self.bucket_name)
        self.log.info("Downloading bucket done!")
        self.validate_data()
        self.is_ali_bucket_created = True

    @test_step
    def cleanup(self):
        """ cleaning up object storage client/credential if created by automation """
        if self.google_helper is not None:
            self.google_helper.google_helper_cleanup()

        if self.is_ali_bucket_created:
            self.ali_helper.delete_bucket(bucket_name=self.destination_bucket, endpoint=self.tcinputs['ali_endpoint'])

        if self.is_automation_account:
            self.navigator.navigate_to_object_storage()
            self.admin_console.wait_for_completion()
            if self.object_storage.is_account_exists(ObjectStorage.Types.GOOGLE, self.object_storage_name):
                self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                                 credential_name=self.credential_name)

    def run(self):
        """Run function of this test case"""
        try:
            # Create the object storage
            self.create_gcp_client()

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
