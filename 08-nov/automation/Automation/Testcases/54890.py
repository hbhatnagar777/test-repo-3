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

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase

from Application.CloudStorage.azure_helper import AzureHelper

from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import (
    TestStep,
    handle_testcase_exception
)

from AutomationUtils.machine import Machine

from Application.CloudStorage.s3_helper import S3Helper
from Application.CloudStorage.cloud_storage_helper import CloudStorageHelper


class TestCase(CVTestCase):
    """Admin Console: Validate 'Save as View' on Report"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Acceptance - Data Protection - Azure Data Lake Gen2 via SDK"
        self.gen2_client_name = 'TC54790'
        self.content_grp_name = 'group1'
        self.session = None
        self.machine = None
        self.s3_helper = None
        self.tcinputs = {
            "access_node": None,
            "account_name": None,
            "account_pwd": None,
            "dest_cloud": None,
            "dest_cloud_path": None,
            "dest_fs_client": None,
            "access_key_s3": None,
            "secret_key_s3": None
        }
        self.out_place_files = 0
        self.dest_fs_path = None
        self.gen2instance = 'TestAzureDL'
        self.cloud_storage_helper = None
        self.azure_helper = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.machine = Machine(self.tcinputs['dest_fs_client'], self.commcell)
        self.s3_helper = S3Helper(self)
        self.session = self.s3_helper.create_session_s3(
            self.tcinputs["access_key_s3"],
            self.tcinputs["secret_key_s3"],
            'us-east-1'
        )
        self.cloud_storage_helper = CloudStorageHelper(self)
        self.azure_helper = AzureHelper(self)
        if self.machine.os_info == 'WINDOWS':
            self.dest_fs_path = r'c:\\cloudappRestore'
        elif self.machine.os_info == 'UNIX':
            self.dest_fs_path = '/opt/cloudappRestore'

    def cleanup(self):
        """cleanup the testcase pre requisites"""
        self.s3_helper.delete_contents_s3(self.session, [self.tcinputs['dest_cloud_path']])
        self.machine.remove_directory(self.dest_fs_path)

    @test_step
    def create_gen2_instance(self):
        """Creates azure gen2 instance"""
        cloud_options = {
            'instance_name': self.gen2instance,
            'access_node': self.tcinputs['access_node'],
            'description': None,
            'storage_policy': self.subclient.storage_policy,
            'accountname': self.tcinputs['account_name'],
            'accesskey': self.tcinputs['account_pwd'],
            'number_of_streams': 1,
            'cloudapps_type': 'azureDL'
        }
        agent = self.client.agents.get('cloud apps')
        agent.instances.add_cloud_storage_instance(cloud_options)
        agent.instances.refresh()
        if not agent.instances.has_instance('TestAzureDL'):
            raise CVTestStepFailure(
                f"created instance [TestAzureDL] doesn't exist in client [{self.client.name}]"
            )

    @test_step
    def delete_instance(self):
        """verifies Azure DL instance deletion"""
        agent = self.client.agents.get('cloud apps')
        agent.instances.delete(self.gen2instance)
        agent.instances.refresh()
        if agent.instances.has_instance(self.gen2instance):
            raise CVTestStepFailure(
                f"Deleted instance [TestAzureDL] exist in client [{self.client.name}]"
            )

    @test_step
    def backup(self):
        """submits backup job"""
        self.cloud_storage_helper.cloud_apps_backup(self.subclient, "Full")

    @test_step
    def in_place_restore(self):
        """Submits inplace restore"""
        job_obj = self.cloud_storage_helper.cloud_apps_restore(self.subclient, "in_place")
        if not job_obj.num_of_files_transferred > 0:
            raise CVTestStepFailure(f"inplace restore job {job_obj.jobid} success files is 0")

    @test_step
    def out_of_place_restore(self):
        """verify out of place restore"""
        job_obj = self.cloud_storage_helper.cloud_apps_restore(
            self.subclient,
            "out_of_place",
            destination_client_name=self.tcinputs['outofplace_client_name'],
            destination_path=self.tcinputs['dest_cloud_path'],
            destination_instance_name=self.tcinputs['outofplace_client_name']
        )
        if not job_obj.num_of_files_transferred > 0:
            raise CVTestStepFailure(f"out of place restore job {job_obj.jobid} success files is 0")
        self.out_place_files = job_obj.num_of_files_transferred

    @test_step
    def disk_restore(self):
        """Verify disk restore"""
        job_obj = self.cloud_storage_helper.cloud_apps_restore(
            self.subclient,
            "fs_restore",
            destination_client_name=self.tcinputs['dest_fs_client'],
            destination_path=self.dest_fs_path
        )
        path = self.dest_fs_path + self.subclient.content[0]
        if not self.machine.check_directory_exists(path):
            raise CVTestStepFailure(
                f"Disk Restore path [{path}] is empty after restore job [{job_obj.jobid}"
            )
        if not job_obj.num_of_files_transferred > 0:
            raise CVTestStepFailure(f"Disk restore job {job_obj.jobid} success files is 0")
        if self.out_place_files != job_obj.num_of_files_transferred:
            raise CVTestStepFailure(
                f"Disk restore file count {self.out_place_files} not matching with "
                f"disk restore files count {job_obj.num_of_files_transferred}"
            )

    def run(self):
        try:
            self.cleanup()
            self.create_gen2_instance()
            self.delete_instance()
            self.backup()
            self.in_place_restore()
            self.out_of_place_restore()
            self.disk_restore()

        except Exception as err:
            handle_testcase_exception(self, err)
