# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: SaaS: S3 Acceptance after upgrade to latest CU pack

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  Setup function of this test case

    run()                           --  run function of this test case

    backup()                        --  Runs Backup and waits for backup job to finish

    upgrade_client_software()       --  Upgrades the client software

    in_place_restore()              --  Runs a Restore from Admin Console

    revert_incremental_content()    --  Reverts the incremental content to original content

    validate_data()                 -- Validates restored files by checking if the files exists and comparing sizes

    cleanup()                       -- deletes the stack created during backup.

Input Example:

    "testCases":
            {
                "71229": {
                "exisitng_gateway_name":"NAME OF THE GATEWAY",
                "exisiting_client_name":"NAME OF THE S3 CLIENT",
                "s3_access_key":"ACCESS KEY S3",
                "s3_secret_key":"SECRET KEY S3",
                "incremental_data":"CONTENT TO BE ADDED FOR INCREMENTAL BACKUP",
                "bucket_name":"BUCKET NAME",
                "region":"REGION OF THE EXISTING S3 CLIENT",
                }
            }

"""

import os
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.ObjectStorage.content_group import ContentGroup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Reports.utils import TestCaseUtils
from Web.AdminConsole.ObjectStorage.object_storage import ObjectStorage
from Web.AdminConsole.ObjectStorage.object_details import ObjectDetails
import time
from Application.CloudStorage.s3_helper import S3Helper
from AutomationUtils import constants, machine


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "SaaS: S3 Acceptance after upgrade to latest CU pack"
        self.browser = None
        self.s3_storage_helper = None
        self.admin_console = None
        self.navigator = None
        self.servers = None
        self.db_helper = None
        self.utils = TestCaseUtils(self)
        self.common_dir_path = None
        self.controller_object = None
        self.original_data_path = None
        self.restored_data_path = None
        self.s3_session = None
        self.b_tags = None
        self.b_sys_metadata = None
        self.b_user_metadata = None
        self.b_acls = None
        self.a_sys_metadata = None
        self.a_user_metadata = None
        self.a_tags = None
        self.a_acls = None
        self.bucket_name = None
        self.content_group = None
        self.content_group_name = 'default'
        self.backup_job_list = set()
        self.object_storage_name = None
        self.backup_gateway = None
        self.content_to_remove = None
        self.object_storage = None
        self.object_details = None
        self.content_group = None
        self.tcinputs = {
            "exisitng_gateway_name": None,
            "exisiting_client_name": None,
            "s3_access_key": None,
            "s3_secret_key": None,
            "incremental_data": None,
            "bucket_name": None,
            "region": None,
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

        self.s3_storage_helper = S3Helper(self)
        self.s3_session = self.s3_storage_helper.create_session_s3(
            self.tcinputs["s3_access_key"],
            self.tcinputs["s3_secret_key"],
            self.tcinputs["region"]
        )
        self.bucket_name = self.tcinputs["bucket_name"]

        self.servers = Servers(self.admin_console)
        self.object_storage_name = self.tcinputs["exisiting_client_name"]
        self.backup_gateway = self.tcinputs["exisitng_gateway_name"]
        self.content_to_remove = ["/"+self.tcinputs["incremental_data"]]
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.db_helper = DbHelper(self.commcell)

        temp_folder_name = f"MetallicS3_{str(int(time.time()))}"
        self.controller_object = machine.Machine()
        self.common_dir_path = self.controller_object.join_path(
            constants.TEMP_DIR, temp_folder_name)
        self.controller_object.create_directory(self.common_dir_path,
                                                force_create=True)

    @test_step
    def upgrade_client_software(self, client):
        """
        Method to submit software upgrade for a client from UI
        Args:
            client      (object)    :   client object
        """
        self.navigator.navigate_to_servers()
        self.admin_console.refresh_page()
        job = self.servers.action_update_software(client_name=client)
        self.db_helper.wait_for_job_completion(job)
        self.log.info("Client software Upgrade successful.")

    @test_step
    def revert_incremental_content(self):
        """Reverts the incremental content to original content"""

        self.access_existing_object_storage()
        self.object_storage.delete_selected_content_from_content_group(self.content_group_name, self.content_to_remove)

    @test_step
    def access_existing_object_storage(self, reach_subclient=False):
        """Accesses the object storage"""
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.object_storage_name)
        if reach_subclient:
            self.object_details.access_content_group(self.content_group_name)

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
    def download_s3_bucket(self, path):
        """ Downloads S3 bucket
            Args:
                path(str) -- location to which s3 buckets need to be downloaded
        """
        current_path = os.getcwd()
        head, tail = os.path.split(path)
        os.chdir(head)
        os.mkdir(tail)
        os.chdir(path)
        self.s3_storage_helper.download_container_s3(self.s3_session, self.tcinputs["bucket_name"])
        os.chdir(current_path)
        self.log.info("Downloaded S3 bucket")

    @test_step
    def initialize_data_before_restore(self):
        """Initializes data and metadata for validation before restore job starts"""
        self.original_data_path = self.controller_object.join_path(self.common_dir_path, 'original_contents')
        self.b_acls = self.s3_storage_helper.get_bucket_and_objects_acls(self.s3_session, self.bucket_name)
        self.b_user_metadata = self.s3_storage_helper.get_objects_user_defined_metadata(self.s3_session, self.bucket_name)
        self.b_sys_metadata = self.s3_storage_helper.get_objects_metadata(self.s3_session, self.bucket_name)
        self.b_tags = self.s3_storage_helper.get_bucket_and_objects_tags(self.s3_session, self.bucket_name)
        self.download_s3_bucket(self.original_data_path)

    @test_step
    def initialize_data_after_restore(self, destination_folder):
        """Initializes data and metadata for validation after restore job completes
            Args:
                destination_folder(str):    destination folder to which data gets downloaded for validation.
        """
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, destination_folder)
        self.a_acls = self.s3_storage_helper.get_bucket_and_objects_acls(self.s3_session, self.bucket_name)
        self.a_user_metadata = self.s3_storage_helper.get_objects_user_defined_metadata(self.s3_session,self.bucket_name)
        self.a_sys_metadata = self.s3_storage_helper.get_objects_metadata(self.s3_session, self.bucket_name)
        self.a_tags = self.s3_storage_helper.get_bucket_and_objects_tags(self.s3_session, self.bucket_name)
        self.download_s3_bucket(self.restored_data_path)

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
        self.db_helper.compare_dictionaries(self.b_sys_metadata, self.a_sys_metadata)
        self.log.info("System Defined Metadata validation completed no mismatching before and after restore")
        self.db_helper.compare_dictionaries(self.b_user_metadata, self.a_user_metadata)
        self.log.info("User Defined Metadata validation completed no mismatching before and after restore")
        self.db_helper.compare_dictionaries(self.b_acls, self.a_acls)
        self.log.info("ACLs validation completed no mismatching before and after restore")
        self.db_helper.compare_dictionaries(self.b_tags, self.a_tags)
        self.log.info("Tags validation completed no mismatching before and after restore")

    def run(self):
        try:
            # Incremental backup before upgrade
            self.access_existing_object_storage(reach_subclient=True)

            self.backup(RBackup.BackupType.INCR)

            # Upgrade the backup gateway
            self.upgrade_client_software(self.backup_gateway)

            self.access_existing_object_storage()

            # Run incremental and synthetic backup
            self.object_storage.edit_content_group(self.content_group_name, self.tcinputs['incremental_data'])

            self.backup(RBackup.BackupType.INCR)

            time.sleep(60)

            self.backup(RBackup.BackupType.SYNTH)

            # Validate the backup jobs
            self.object_storage.validate_backup_jobs(self.backup_job_list, react=True)

            self.in_place_restore()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            self.revert_incremental_content()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
