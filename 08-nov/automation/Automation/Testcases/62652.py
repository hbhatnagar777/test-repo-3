# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Amazon S3 Acceptance case for Metallic Hub

TestCase:
    __init__()                   --  initialize TestCase class

    setup()                     --  Setup function of this test case

    run()                       --  run function of this test case

    create_tenant()             --  creates a new tenant for automation.

    configure_new_client()      --  Configures New S3 Object Storage Client

    backup()                    --  Runs Backup and waits for backup job to finish

    in_place_restore()               --  Runs a Restore from Admin Console

    wait_for_backup_job_completion()    --  Gets the Backup Job submitted from Metallic and waits for completion

    validate_data()   -- Validates restored files by checking if the files exists and comparing sizes

    cleanup()                       -- deletes the stack created during backup.

Input Example:

    "testCases":
            {
                "62652": {
                "bucket_name":"name of s3 bucket",
                "hostname": "metallic host name",
                "s3_access_key":"access key of s3 account",
                "s3_secret_key":"secret key of s3 account",
                "stack_name":"cloud formation stack name",
                "key-pair":"keypair-name",
			    "vpc":"vpc-id",
			    "subnet":"subnet-id",
                "platform":"os type",
                "storage_bucket":"bucket to where backup data will be written",
                "region":"region name in which resources reside in AWS"
                    }
            }

"""
import datetime
import os
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Metallic.hubutils import HubManagement
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Hub.CCObjectStorage.object_storage import S3ObjectStorageInstance
from Web.AdminConsole.ObjectStorage.content_group import ContentGroup
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Reports.utils import TestCaseUtils
from Web.AdminConsole.ObjectStorage.object_storage import ObjectStorage
from Web.AdminConsole.ObjectStorage.object_details import ObjectDetails
import time
from cvpysdk.commcell import Commcell
from Application.CloudStorage.s3_helper import S3Helper
from AutomationUtils import constants, machine


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Amazon S3 Acceptance case for Metallic Hub with STS assume IAM role Authentication"
        self.browser = None
        self.s3_metallic_helper = None
        self.s3_storage_helper = None
        self.tenant_password = None
        self.admin_console = None
        self.navigator = None
        self.driver = None
        self.commcell = None
        self.object_storage = None
        self.client_name = None
        self.object_storage_name = None
        self.object_details = None
        self.s3_metallic = None
        self.plan = None
        self.browse = None
        self.company_name = None
        self.tenant_user_name = None
        self.hub_management = None
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
        self.access_key = None
        self.secret_key = None
        self.is_automation_account = False
        self.plan_page = None
        self.config = None
        self.b_bucket_metadata = None
        self.oss_metallic_helper = None
        self.b_objects_metadata = None
        self.a_bucket_metadata = None
        self.a_objects_metadata = None
        self.oss_metallic = None
        self.content_group_name = 'default'
        self.backup_job_list = set()
        self.bucket_name = None
        self.content_group = None
        self.byos_bucket_name = None
        self.tcinputs = {
            "bucket_name": None,
            "hostname": None,
            "s3_access_key": None,
            "s3_secret_key": None,
            "stack_name": None,
            "key-pair": None,
            "vpc": None,
            "subnet": None,
            "platform": None,
            "storage_bucket": None,
            "region": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.hub_management = HubManagement(
            testcase_instance=self,
            commcell=self.commcell.webconsole_hostname
        )
        self.hub_management.delete_companies_with_prefix('S3objectstorage')
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
        self.access_key = self.tcinputs.get("s3_access_key")
        self.secret_key = self.tcinputs.get("s3_secret_key")
        self.plan = f's3plan{str(int(time.time()))}'
        self.object_storage_name = datetime.datetime.now().strftime("S3client-%d-%B-%H-%M")
        self.admin_console.login(username=self.tenant_user_name,
                                 password=self.tenant_password,
                                 stay_logged_in=True)
        self.admin_console.wait_for_completion()
        self.s3_metallic = S3ObjectStorageInstance(self.admin_console, 'Amazon S3')
        self.s3_storage_helper = S3Helper(self)
        self.s3_session = self.s3_storage_helper.create_session_s3(self.config.aws_access_creds.tenant_access_key,
                                                                   self.config.aws_access_creds.tenant_secret_key,
                                                                   self.tcinputs.get('region'))
        temp_folder_name = f"MetallicS3_{str(int(time.time()))}"
        self.controller_object = machine.Machine()
        self.common_dir_path = self.controller_object.join_path(
            constants.TEMP_DIR, temp_folder_name)
        self.controller_object.create_directory(self.common_dir_path,
                                                force_create=True)
        self.bucket_name = self.tcinputs["full_bkp_content"].split('/')[0]
        self.db_helper = DbHelper(self.commcell)

    @test_step
    def create_tenant(self):
        """
        Create a new tenant for the automation
        """
        self.company_name = datetime.datetime.now().strftime("S3objectstorage-%d-%B-%H-%M")
        user_firstname = "S3objectstorage" + str(int(time.time()))
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
        """ Configures New S3 Object Storage Client"""
        content = [self.tcinputs['full_bkp_content']]
        self.byos_bucket_name = self.tcinputs['storage_bucket']
        self.oss_metallic_helper = S3ObjectStorageInstance(self.admin_console, 'Amazon S3')
        params = [
            {
                "ParameterKey": "KeyName",
                "ParameterValue": self.tcinputs.get("key-pair")
            },
            {
                "ParameterKey": "VpcId",
                "ParameterValue": self.tcinputs.get("vpc")
            },
            {
                "ParameterKey": "SubnetId",
                "ParameterValue": self.tcinputs.get("subnet")
            }
        ]
        backup_gateway_name = self.oss_metallic_helper.configure(byos_storage_name=f's3_byos_storage{int(time.time())}',
                                                                 byos_bucket_name=self.byos_bucket_name,
                                                                 plan_name=self.plan,
                                                                 client_name=self.object_storage_name,
                                                                 content=content,
                                                                 auth_type='STS assume role with IAM policy',
                                                                 stack_params=params, region='us-east-1',
                                                                 stack_name=self.tcinputs.get('stack_name'),
                                                                 gateway_os_type=self.tcinputs.get('platform'),
                                                                 region_human_readable=self.tcinputs.get(
                                                                     'region-human-readable'),
                                                                 vendor_name='Amazon S3',
                                                                 backup_method='Gateway')
        self.admin_console.refresh_page()
        self.navigator = self.admin_console.navigator
        self.upgrade_client_software(backup_gateway_name)
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.navigator.navigate_to_object_storage()
        self.object_storage.access_account(self.object_storage_name)

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
        self.b_acls = self.s3_storage_helper.get_bucket_and_objects_acls(self.s3_session, self.tcinputs["bucket_name"])
        self.b_user_metadata = self.s3_storage_helper.get_objects_user_defined_metadata(self.s3_session,
                                                                                        self.tcinputs["bucket_name"])
        self.b_sys_metadata = self.s3_storage_helper.get_objects_metadata(self.s3_session,
                                                                          self.tcinputs["bucket_name"])
        self.b_tags = self.s3_storage_helper.get_bucket_and_objects_tags(self.s3_session, self.tcinputs["bucket_name"])
        self.download_s3_bucket(self.original_data_path)

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
        self.download_s3_bucket(self.restored_data_path)

    @test_step
    def in_place_restore(self):
        """ Runs in-place restore """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.object_storage_name)
        self.object_details.access_restore(self.content_group_name)
        self.initialize_data_before_restore()
        self.s3_storage_helper.delete_container_s3(self.s3_session, self.bucket_name)
        rstr_obj = self.object_details.submit_restore([self.bucket_name])
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")
        self.initialize_data_after_restore('restored_contents')
        self.validate_data()
        self.s3_storage_helper.delete_container_s3(self.s3_session, self.bucket_name)
        self.log.info(f"Deleting BYOS {self.byos_bucket_name} bucket.......")
        self.s3_storage_helper.empty_container_s3(self.s3_session, self.byos_bucket_name)
        self.log.info("Deletion of BYOS bucket success full")
        time.sleep(30)
        rstr_obj = self.object_details.submit_restore([self.bucket_name], copy='Secondary')
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job from secondary ran Successfully")
        self.initialize_data_after_restore("restored_contents_secondary")
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

    def cleanup(self):
        """Cleanups the backup gateway, credentials and byos storage in cloud
        followed by deactivating and deleting the created company"""
        self.oss_metallic_helper.s3_cleanup(self.tcinputs['stack_name'])
        self.controller_object.remove_directory(self.common_dir_path)
        self.hub_management.deactivate_tenant(self.company_name)
        self.hub_management.delete_tenant(self.company_name)

    def run(self):
        try:
            self.configure_new_client()

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
