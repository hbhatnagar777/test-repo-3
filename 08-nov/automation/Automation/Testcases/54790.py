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

    in_place_restore()              --  Runs in-place restore

    out_of_place_restore()          --  Runs out-of-place restore

    restore_to_disk()               --  Runs restore to disk

    validate_data()                 --  Validates data after restore

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case



"""
import os
import time

from Application.CloudStorage.google_storage_helper import GoogleObjectStorage
from Application.CloudStorage.s3_helper import S3Helper
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
from Web.AdminConsole.Components.panel import Backup
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Application.CloudStorage.azure_helper import AzureDataLakeHelper


class TestCase(CVTestCase):
    """ Basic acceptance Test for Azure datalake gen2 Object Storage from command center
        Example inputs:
        "54790": {
                "proxy_client":"proxy_client_name",
                "plan":"plan_name",
                "credential":"",
                "account_name":"storage account name",
                "access_key":"b..",
                "content":["/datalake gen2 content/fullbkp"],
                "edit_content":["/datalake gen2 content/incbkp"],
                "dest_fs_client":"fs_client_name",
                "bucket_name":"container_name",
                "dest_cloud":"dest_cloud_name",
                "dest_cloud_path":"/out of place-restore-path",
                "access_key_s3":"A....H",
                "secret_key_s3":"4....J",
                "oss_client_name":"object_storage_client_name"
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
        self.name = "ACCT1 for Azure Datalake gen2 Key-based Auth from Command center"
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
        self.gcp_bucket_name = None
        self.out_of_place_restore_path = None
        self.endpoint = None
        self.is_gcp_bucket_created = False
        self.default_subclient_content = []
        self.tcinputs = {
            "oss_client_name": None,
            "proxy_client": None,
            "plan": None,
            "account_name": None,
            "access_key": None,
            "dest_cloud": None,
            "dest_cloud_path": None,
            "dest_fs_client": None,
            "access_key_s3": None,
            "secret_key_s3": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                 self.inputJSONnode["commcell"]["commcellPassword"])
        self.navigator = self.admin_console.navigator
        self.utils = CommonUtils(self)
        self.servers = Servers(self.admin_console)
        self.object_storage_name = self.tcinputs["oss_client_name"]
        self.object_storage = ObjectStorage(self.admin_console, self.commcell)
        self.object_details = ObjectDetails(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.s3_helper = S3Helper(self)
        self.session = self.s3_helper.create_session_s3(
            self.tcinputs["access_key_s3"],
            self.tcinputs["secret_key_s3"],
            'us-east-1'
        )
        self.default_subclient_content = [self.tcinputs.get('content')[1:-1]]
        self.azure_helper = AzureDataLakeHelper(account_name=self.tcinputs.get('account_name'),
                                                access_key=self.tcinputs.get("access_key"))
        self.google_helper = GoogleObjectStorage(testcase_object=self, ignore_tc_props=True)
        self.controller_object = machine.Machine()
        self.bucket_name = self.tcinputs["bucket_name"]
        self.common_dir_path = self.azure_helper.common_dir_path
        self.gcp_bucket_name = self.tcinputs["dest_cloud_path"][1:]

        self.db_helper = DbHelper(self.commcell)

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
            auth_type='Access key and Account name',
            plan=self.tcinputs["plan"],
            credential=self.tcinputs.get("credential", ''),
            access_key=self.tcinputs["account_name"],
            secret_key=self.tcinputs["access_key"],
            backup_content=self.default_subclient_content,
            url="dfs.core.windows.net",
            vendor_name='Azure Data Lake Storage Gen2'
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
        self.azure_helper.download_container_dl(file_system_name=self.bucket_name, dir_name="original_contents")
        self.azure_helper.delete_container_azure_dl(self.bucket_name)
        time.sleep(60)
        rstr_obj = self.object_details.submit_restore([self.tcinputs["bucket_name"]])
        jobid = rstr_obj.in_place()
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")
        self.restored_data_path = self.controller_object.join_path(self.common_dir_path, "restored_contents")
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
        self.is_gcp_bucket_created = True
        self.restored_data_path = self.controller_object.join_path(self.google_helper.common_dir_path, "outofplace")
        self.log.info("Downloading bucket started........")
        self.google_helper.download_google_bucket(self.gcp_bucket_name, "outofplace")
        self.log.info("Downloading bucket done!")
        self.restored_data_path = self.controller_object.join_path(self.restored_data_path,
                                                                   self.bucket_name)
        self.validate_data()

    @test_step
    def cleanup(self):
        """ cleaning up object storage client/credential if created by automation """
        if self.azure_helper is not None:
            self.azure_helper.azure_data_lake_cleanup()
        if self.is_gcp_bucket_created:
            self.google_helper.delete_bucket(self.gcp_bucket_name)
            self.google_helper.google_helper_cleanup()
        if self.is_automation_account:
            self.navigator.navigate_to_object_storage()
            self.admin_console.wait_for_completion()
            if self.object_storage.is_account_exists(ObjectStorage.Types.Azure_DL_Gen2, self.object_storage_name):
                self.object_storage.delete_object_storage_client_and_credentials(client_name=self.object_storage_name,
                                                                                 credential_name=self.credential_name)

    def run(self):
        """Run function of this test case"""
        try:
            self.add_azure_dlg2_oss_client()

            self.object_storage.validate_default_subclient_content(self.default_subclient_content)

            self.navigator.navigate_to_object_storage()

            self.object_storage.create_content_group(object_storage_name=self.object_storage_name,
                                                     content=self.tcinputs["content"],
                                                     plan=self.tcinputs["plan"],
                                                     content_group_name=self.content_group_name)

            full_jobid = self.object_storage.backup(Backup.BackupType.FULL, self.content_group_name)

            self.object_storage.edit_content_group(self.content_group_name, self.bucket_name)

            incr_jobid = self.object_storage.backup(Backup.BackupType.INCR, self.content_group_name)

            synth_jobid = self.object_storage.backup(Backup.BackupType.SYNTH, self.content_group_name)

            self.object_storage.validate_backup_jobs([full_jobid, incr_jobid, synth_jobid], react=True)

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
