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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    cleanup()                       --  Deletes instance if it is created by automation

    create_gcp_objstorage_client()  --  Creation of Google Cloud Object Storage Account

    in_place_restore()              --  Runs in-place restore

    out_of_place_restore()          --  Runs out-of-place restore

    restore_to_disk()               --  Runs restore to disk

    validate_data()                 --  Validates data after restore

    run()           --  run function of this test case


"""
import time
from Application.CloudStorage.google_storage_helper import GoogleObjectStorage
from Application.CloudStorage.ibm_helper import IbmHelper
from AutomationUtils.idautils import CommonUtils
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
from Application.CloudStorage.azure_helper import AzureDataLakeHelper


class TestCase(CVTestCase):
    """ Basic acceptance Test for Azure datalake gen2 Object Storage from command center
        Example inputs:
        "62412": {
                  "proxy_client": "AUTOMATION_PROXY",
                  "plan": "PLAN",
                  "s_content": "CONTENT FOR THE CONTENT GROUP",
                  "bucket_name": "BUCKET NAME ON THE CLOUD",
                  "content": "DEFAULT CONTENT FOR OBJECT STORAGE INSTANCE",
                  "tenant_id": "TENANT ID",
                  "app_id": "APPLICATION ID",
                  "app_pwd": "APPLICATION SECRET",
                  "subscription_id": "SUBSCRIPTION ID",
                  "dest_cloud": "CROSS CLOUD DESTINATION CLIENT ON CS",
                  "dest_cloud_path": "PATH ON THE CLOUD DESTINATION CLIENT",
                  "dest_fs_client": "DESTINATION MACHINE FOR DISK RESTORE",
                  "access_key" : "ACCESS KEY FOR AZURE CLOUD"
                  "ibm_access_key":"ACCESS KEY IBM",
                  "ibm_secret_key":"SECRET KEY IBM",
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
        self.name = "ACCT1 for Azure Datalake gen2 IAM AD Auth from Command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.driver = None
        self.object_storage = None
        self.object_details = None
        self.object_storage_name = None
        self.utils = None
        self.credential_manager = None
        self.servers = None
        self.content_group_name = 'automation_cg'
        self.backup_job_list = set()
        self.ibm_helper = None
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
        self.alibaba_obj = None
        self.common_download_path = None
        self.original_data_path = None
        self.restored_data_path = None
        self.s3_helper = None
        self.google_helper = None
        self.ibm_bucket_name = None
        self.out_of_place_restore_path = None
        self.endpoint = None
        self.is_ibm_bucket_created = False
        self.default_subclient_content = []
        self.tcinputs = {
            "proxy_client": None,
            "plan": None,
            "account_name": None,
            "access_key": None,
            "dest_cloud": None,
            "dest_cloud_path": None,
            "dest_fs_client": None,
            "ibm_access_key": None,
            "ibm_secret_key": None
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
        self.utils = CommonUtils(self)
        self.servers = Servers(self.admin_console)
        t = time.localtime()
        self.object_storage_name = f"automation-adls-{t.tm_mday}-{t.tm_mon}-{t.tm_hour}{t.tm_min}{t.tm_sec}"
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.db_helper = DbHelper(self.commcell)

        # For cloud connections
        self.ibm_helper = IbmHelper(self.tcinputs["ibm_access_key"], self.tcinputs.get("ibm_secret_key"),
                                    self.tcinputs.get("endpoint"))

        self.azure_helper = AzureDataLakeHelper(account_name=self.tcinputs.get('account_name')[1:],
                                                access_key=self.tcinputs.get("access_key"))
        self.google_helper = GoogleObjectStorage(testcase_object=self, ignore_tc_props=True)

        # Helper variables initialization
        self.controller_object = machine.Machine()
        self.bucket_name = self.tcinputs["bucket_name"]
        self.common_dir_path = self.azure_helper.common_dir_path
        self.ibm_bucket_name = self.tcinputs["dest_cloud_path"][1:]
        self.default_subclient_content = [self.tcinputs.get('content')]

        # Cleanup automation credentials
        self.object_storage.cleanup_credentials(hours=5)

    @test_step
    def add_azure_dlg2_oss_client(self):
        """
        creates the azure dlg2 client
        """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()

        if self.object_storage.is_account_exists(ObjectStorage.Types.Azure_DL_Gen2, self.object_storage_name):
            self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                             credential_name=self.credential_name)
            self.navigator.navigate_to_object_storage()

        self.credential_name = self.object_storage.add_object_storage_client(
            name=self.object_storage_name,
            proxy_client=self.tcinputs["proxy_client"],
            auth_type='IAM AD application',
            plan=self.tcinputs["plan"],
            credential=self.tcinputs.get("credential", ''),
            access_key=self.tcinputs.get('account_name'),
            tenant_id=self.tcinputs["tenant_id"],
            app_id=self.tcinputs["app_id"],
            app_secret_key=self.tcinputs["app_pwd"],
            backup_content=self.tcinputs.get('account_name'),
            url="dfs.core.windows.net",
            vendor_name='Azure Data Lake Storage Gen2',
            subscription_id=self.tcinputs["subscription_id"],
            cloud_name=self.object_storage_name
        )
        
        self.log.info("Object storage Account created")
        self.is_automation_account = True
        if self.tcinputs.get("credential", '') == "":
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
        self.log.info("Restore Validation Succeeded")

    @test_step
    def in_place_restore(self):
        """ Runs in-place restore """
        self.navigator.navigate_to_object_storage()
        self.admin_console.wait_for_completion()
        self.object_storage.access_account(self.object_storage_name)
        self.object_details.access_restore(self.content_group_name)
        self.original_data_path = self.controller_object.join_path(self.common_dir_path, 'original_contents')
        self.log.info("Downloading container from cloud before restore...")
        self.azure_helper.download_container_dl(file_system_name=self.bucket_name, dir_name="original_contents")
        self.log.info("Deleting container from cloud before restore")
        self.azure_helper.delete_container_azure_dl(self.bucket_name)
        time.sleep(60)
        rstr_obj = self.object_details.submit_restore([self.tcinputs["bucket_name"]])
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents")
        self.log.info("Downloading container from cloud after restore...")
        self.azure_helper.download_container_dl(self.bucket_name, "restored_contents")
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
        self.is_ibm_bucket_created = True
        self.restored_data_path = self.controller_object.join_path(self.ibm_helper.common_dir_path, "outofplace")
        self.log.info("Downloading bucket started........")
        self.ibm_helper.download_bucket(self.ibm_bucket_name, "outofplace")
        self.log.info("Downloading bucket done!")
        self.restored_data_path = self.controller_object.join_path(self.restored_data_path,
                                                                   self.bucket_name)
        self.validate_data()

    @test_step
    def cleanup(self):
        """ cleaning up object storage client/credential if created by automation """
        if self.azure_helper is not None:
            self.azure_helper.azure_data_lake_cleanup()
        if self.is_ibm_bucket_created:
            self.ibm_helper.delete_bucket(self.ibm_bucket_name)
        if self.is_automation_account:
            self.navigator.navigate_to_object_storage()
            self.admin_console.wait_for_completion()
            if self.object_storage.is_account_exists(ObjectStorage.Types.Azure_DL_Gen2, self.object_storage_name):
                self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                                 credential_name=self.credential_name)

    def run(self):
        """Run function of this test case"""
        try:
            # Create the object storage
            self.add_azure_dlg2_oss_client()

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