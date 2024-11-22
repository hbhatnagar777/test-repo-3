# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: This test case verifies that the vmware replication group can perform backups on disabled live sync and then
sync after the live sync schedule is re-enabled

TestCase: Class for executing this test case
Sample JSON: {
        "tenant_username": <username>,
        "tenant_password": <password>,
        "ClientName": "vmwhyp",
        "source_vm": "vm"
        "recovery_target": "vmwtarget",
        "storage_name" : "storage",
        "resource_pool": None,
        "vm_folder": None,
        "network_1": None,
        "network_2": None,
        ""
}
"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import OptionsHelper
from Web.AdminConsole.DR.monitor import ReplicationMonitor
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, ReplicationType
from DROrchestration.replication import Replication
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """This TC is used to verify disabling and enabling of replication groups along with pending live sync"""
    test_step = TestStep()
    _AGENT_NAME = 'virtual server'
    _INSTANCE_NAME = 'vmware'
    _BACKUPSET_NAME = 'defaultBackupSet'

    def __init__(self):
        """Initialises the objects and TC inputs"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - VMW - Live sync -Replicate Backups pending to sync before full cycle ."

        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "ClientName": None,
            "source_vm": None,
            "recovery_target": None,
            "storage_name": None,
            "secondary_storage_name": None,
        }
        self.utils = None
        self.source_hypervisor = None
        self.source_vm = None
        self.source_vms_input = None
        self.recovery_target = None
        self.storage_name = None
        self.secondary_storage_name = None

        self.admin_console = None
        self.replication_helper = None
        self.replication_group = None
        self.replication_monitor = None

        
        self.replication = None

    @property
    def group_name(self):
        """Returns the virtualization group name"""
        return self.replication_helper.group_name(self.id)

    def login(self):
        """Logs in to admin console"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          machine=self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])

        self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
        self.replication_group = ReplicationGroup(self.admin_console)
        self.replication_monitor = ReplicationMonitor(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.source_hypervisor = self.tcinputs['ClientName']
            self.source_vm = self.tcinputs['source_vm']
            self.source_vms_input = [vmname.split('/')[-1] for vmname in self.source_vm]
            self.recovery_target = self.tcinputs['recovery_target']
            self.storage_name = self.tcinputs['storage_name']
            self.secondary_storage_name = self.tcinputs['secondary_storage_name']

            self._source_vendor = Vendors_Complete.VMWARE.value
            self._destination_vendor = Vendors_Complete.VMWARE.value
            self._replication_type = ReplicationType.Periodic

        except Exception as exp:
            raise CVTestCaseInitFailure(f'Failed to initialise testcase {str(exp)}')

    @test_step
    def delete_replication_group(self):
        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name, self.source_vms_input)

    @test_step
    def configure_replication_group(self):
        """Configures the replication group with default options"""
        self.admin_console.navigator.navigate_to_replication_groups()
        configure = self.replication_group.configure_virtualization(source_vendor=self._source_vendor,
                                                                    destination_vendor=self._destination_vendor,
                                                                    replication_type=self._replication_type.value)
        configure.add_default_group(self.group_name, self.source_hypervisor, self.source_vm,
                                    self.recovery_target, self.storage_name, self.secondary_storage_name)

    @test_step
    def verify_backup_job_completion(self):
        """Waits for backup job to complete and then verify its details"""
        self.replication = Replication(self.commcell, self.group_name)
        self.replication.wait_for_first_backup()

    @test_step
    def verify_replication_job_completion(self):
        """Waits for replication job to complete and then verify its details"""
        self.replication.get_running_replication_jobs()

    @test_step
    def disable_group(self):
        """Wait for backup and replication to finish and then disable the replication group sync"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.disable(self.group_name)

    @test_step
    def verify_pre_validation(self):
        """Adds data to VM and performs pre validation"""
        self.replication.pre_validation()

    @test_step
    def perform_backups(self):
        """Adds data to the VM and then performs different backups
            1. Incremental
            2. Full
            3. Incremental
        """
        backup_options = OptionsHelper.BackupOptions(self.replication.auto_subclient)
        backup_options.backup_type = "INCREMENTAL"
        self.replication.auto_subclient.backup(backup_options, skip_discovery=True)

        backup_options.backup_type = "FULL"
        self.replication.auto_subclient.backup(backup_options, skip_discovery=True)

        backup_options.backup_type = "INCREMENTAL"
        self.replication.auto_subclient.backup(backup_options, skip_discovery=True)

    @test_step
    def enable_group(self):
        """Enable group and then wait for replication to complete"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.enable(self.group_name)

    @test_step
    def validate_live_sync(self):
        """Validates the live sync is performed"""
        self.replication.post_validation()

    @test_step
    def perform_test_boot(self):
        """Perform test boot on the destination VM"""
        test_boot_job_id = self.replication_monitor.test_boot_vm(self.source_vms_input, self.group_name)
        job_obj = self.commcell.job_controller.get(test_boot_job_id)

        self.logout()
        self.log.info('Waiting for Job [%s] to complete', test_boot_job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.delete_replication_group()
            self.configure_replication_group()

            self.logout()
            self.verify_backup_job_completion()
            self.verify_replication_job_completion()

            self.login()
            self.disable_group()
            self.logout()

            self.verify_pre_validation()

            self.perform_backups()

            self.login()
            self.enable_group()
            self.logout()
            self.verify_replication_job_completion()

            self.validate_live_sync()

            self.login()
            self.admin_console.navigator.navigate_to_replication_monitor()
            self.perform_test_boot()

            self.login()
            self.delete_replication_group()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.logout()
