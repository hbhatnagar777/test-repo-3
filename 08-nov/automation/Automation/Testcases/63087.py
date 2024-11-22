# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: OCI object storage Acceptance case for Metallic command center.

TestCase:
    __init__()                   --  initialize TestCase class

    setup()                     --  Setup function of this test case

    run()                       --  run function of this test case

    create_tenant()             --  creates a new tenant for automation.

    configure_new_client()      --  Configures New OCI Object Storage Client

    backup()                    --  Runs Backup and waits for backup job to finish

    in_place_restore()               --  Runs a Restore from Admin Console

    wait_for_backup_job_completion()    --  Gets the Backup Job submitted from Metallic and waits for completion

    validate_data()   -- Validates restored files by checking if the files exists and comparing sizes

    cleanup()                       -- deletes the stack created during backup.

Input Example:

    "testCases":
            {
                "63087": {
                "full_bkp_content":"content for full backup",
			    "incr_bkp_content":"content for incremental backup",
			    "bkp_gateway_os_type":"backup gateway os type",
			    "region":"region for resource creation and backup",
			    "compartment_path":"path to the source compartment"
                }
            }

"""
import datetime
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Metallic.hubutils import HubManagement
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Hub.CCObjectStorage.object_storage import ROCIObjectStorageInstance
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
from Application.CloudStorage.oci_helper import OCIOSSHelper
from Web.AdminConsole.Components.dialog import RBackup


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "OCI Acceptance case for Metallic"
        self.browser = None
        self.oci_metallic_helper = None
        self.oci_storage_helper = None
        self.tenant_password = None
        self.admin_console = None
        self.navigator = None
        self.driver = None
        self.commcell = None
        self.object_storage = None
        self.client_name = None
        self.object_storage_name = None
        self.db_helper = None
        self.object_details = None
        self.plan = None
        self.browse = None
        self.company_name = None
        self.tenant_user_name = None
        self.hub_management = None
        self.utils = TestCaseUtils(self)
        self.common_dir_path = None
        self.controller_object = None
        self.original_data_path = None
        self.restored_data_path = None
        self.config = None
        self.b_bucket_metadata = None
        self.b_objects_metadata = None
        self.a_bucket_metadata = None
        self.a_objects_metadata = None
        self.oss_metallic = None
        self.content_group_name = 'default'
        self.backup_job_list = set()
        self.oci_oss_helper = None
        self.bucket_name = None
        self.content_group = None
        self.byos_bucket_name = None
        self.tcinputs = {
            "full_bkp_content": None,
            "incr_bkp_content": None,
            "bkp_gateway_os_type": None,
            "region": None,
            "compartment_path": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.hub_management = HubManagement(
            testcase_instance=self,
            commcell=self.commcell.webconsole_hostname
        )
        self.hub_management.delete_companies_with_prefix('OCIobjectstorage')
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
        self.client_name = f'OCIclient{str(int(time.time()))}'
        self.plan = f'OCIplan{str(int(time.time()))}'
        self.object_storage_name = datetime.datetime.now().strftime("OCIclient-%d-%B-%H-%M")
        self.admin_console.login(username=self.tenant_user_name,
                                 password=self.tenant_password,
                                 stay_logged_in=True)
        self.admin_console.wait_for_completion()
        username = {
            'oci_user_id': self.config.ObjectStorage.oci.oci_user_id,
            'oci_private_file_name': self.config.ObjectStorage.oci.private_key_path,
            'oci_finger_print': self.config.ObjectStorage.oci.oci_finger_print,
            'oci_tenancy_id': self.config.ObjectStorage.oci.tenancy,
            'oci_region_name': 'us-ashburn-1',
            'oci_private_key_password': self.config.ObjectStorage.oci.private_key_password
        }
        self.oss_metallic = ROCIObjectStorageInstance(self.admin_console, 'OCI Object Storage', username)
        self.oci_oss_helper = OCIOSSHelper(user_name=username)
        self.controller_object = self.oci_oss_helper.machine
        self.common_dir_path = self.oci_oss_helper.common_dir_path
        self.bucket_name = self.tcinputs["full_bkp_content"].split('/')[0]
        self.db_helper = DbHelper(self.commcell)

    @test_step
    def create_tenant(self):
        """
        Create a new tenant for the automation
        """
        self.company_name = datetime.datetime.now().strftime("OCIobjectstorage-%d-%B-%H-%M")
        user_firstname = "OCIobjectstorage" + str(int(time.time()))
        user_lastname = "user"
        user_email = user_firstname + user_lastname + '@domain.com'
        user_phonenumber = '00000000'
        user_country = self.tcinputs.get("UserCountry", "United States")

        self.log.info(f"Creating Tenant with Company name {self.company_name}")

        self.hub_management = HubManagement(
            testcase_instance=self,
            commcell=self.commcell.webconsole_hostname
        )

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
        """ Configures New OCI Object Storage Client"""
        region = self.tcinputs['region']
        backup_gateway_os_type = self.tcinputs['bkp_gateway_os_type']
        compartment_path = self.tcinputs['compartment_path']
        compartment_name = compartment_path.split('/')[-1]
        content = [self.tcinputs['full_bkp_content']]
        self.byos_bucket_name = f'oci_byos_{int(time.time())}'
        backup_gateway_name = self.oss_metallic.configure(region, backup_gateway_os_type,
                                                          self.byos_bucket_name, compartment_name, self.plan,
                                                          self.object_storage_name,
                                                          compartment_path, content,
                                                          vendor_name='OCI Object Storage')
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
    def in_place_restore(self):
        """ Runs in-place restore """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.object_storage_name)
        self.object_details.access_restore(self.content_group_name)
        self.original_data_path = self.controller_object.join_path(self.common_dir_path, 'original_contents')
        self.oci_oss_helper.download_bucket(bucket_name=self.bucket_name, dir_name="original_contents")
        self.b_objects_metadata = self.oci_oss_helper.get_objects_metadata(self.bucket_name)
        self.b_bucket_metadata = self.oci_oss_helper.get_bucket_metadata(self.bucket_name)
        self.oci_oss_helper.delete_bucket(self.bucket_name)
        time.sleep(60)
        rstr_obj = self.object_details.submit_restore([self.bucket_name])
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents")
        self.oci_oss_helper.download_bucket(self.bucket_name, "restored_contents")
        self.a_objects_metadata = self.oci_oss_helper.get_objects_metadata(self.bucket_name)
        self.a_bucket_metadata = self.oci_oss_helper.get_bucket_metadata(self.bucket_name)
        self.validate_data()
        self.oci_oss_helper.delete_bucket(self.bucket_name)
        self.log.info(f"Deleting BYOS {self.byos_bucket_name} bucket.......")
        self.oci_oss_helper.delete_bucket(self.byos_bucket_name)
        self.log.info("Deletion of BYOS bucket successfull")
        time.sleep(60)
        rstr_obj = self.object_details.submit_restore([self.bucket_name], copy='Secondary')
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job from secondary ran Successfully")
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents_secondary")
        self.oci_oss_helper.download_bucket(self.bucket_name, "restored_contents_secondary")
        self.a_objects_metadata = self.oci_oss_helper.get_objects_metadata(self.bucket_name)
        self.a_bucket_metadata = self.oci_oss_helper.get_bucket_metadata(self.bucket_name)
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
        self.db_helper.compare_dictionaries(self.b_bucket_metadata, self.a_bucket_metadata)
        self.log.info("Bucket Metadata validation completed no mismatching before and after restore")
        self.db_helper.compare_dictionaries(self.b_objects_metadata, self.a_objects_metadata)
        self.log.info("Objects Metadata validation completed no mismatching before and after restore")

    def cleanup(self):
        """Cleanups the backup gateway, credentials and byos storage in cloud
        followed by deactivating and deleting the created company"""
        self.oss_metallic.oci_cleanup()
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
