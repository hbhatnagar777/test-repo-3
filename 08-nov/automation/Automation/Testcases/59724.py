# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case
Testcase: Storage Validation Testcase

TestCase: Class for executing this test case
Sample JSON: {
        "tenant_username": <username>,
        "tenant_password": <password>,
        "ClientName": "hypervisor",
        "source_vm": "VM_Name",
        "recovery_target": "Target_name",
        "primary_storage_name" : "Storage1",
        "secondary_storage_name": "Storage2"

}
"""
from time import sleep
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper, DRHelper
from VirtualServer.VSAUtils import OptionsHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, ReplicationType
from DROrchestration.replication import Replication


class TestCase(CVTestCase):
    """This class is used to automate the replication"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        super(TestCase, self).__init__()
        self.name = " Storage Validation testcase"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "ClientName": None,
            "source_vm": None,
            "recovery_target": None,
            "primary_storage_name": None,
            "secondary_storage_name": None
        }
        self.source_hypervisor = None
        self.source_vm = None
        self.recovery_target = None
        self.primary_storage_name = None
        self.secondary_storage_name = None

        self.utils = None

        self.browser = None
        self.admin_console = None
        self.replication_helper = None
        self.replication_group = None
        self.group_details = None
        self.secondary_storage = None
        self.group_obj = None
        self.replication_group_obj = None
        self.dr_helper = None

    @property
    def group_name(self):
        """Returns the name for the replication group"""
        return self.replication_helper.group_name(self.id)

    def login(self):
        """Logs in to admin console"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(self.tcinputs['tenant_username'],
                                     self.tcinputs['tenant_password'])

            self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
            self.replication_group = ReplicationGroup(self.admin_console)
            self.replication_group_obj = self.commcell.replication_groups
            self.group_details = ReplicationDetails(self.admin_console)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def setup(self):
        """Sets up the Testcase"""
        self.utils = TestCaseUtils(self)
        self.source_hypervisor = self.tcinputs["ClientName"]
        self.source_vm = self.tcinputs["source_vm"]
        self.source_vms_input = [vmname.split('/')[-1] for vmname in self.source_vm]
        self.recovery_target = self.tcinputs["recovery_target"]
        self.primary_storage_name = self.tcinputs["primary_storage_name"]
        self.secondary_storage_name = self.tcinputs["secondary_storage_name"]

        self.dr_helper = DRHelper(self.commcell, self.csdb, self.client)
        self._source_vendor = Vendors_Complete.VMWARE.value
        self._destination_vendor = Vendors_Complete.VMWARE.value
        self._replication_type = ReplicationType.Periodic

    @test_step
    def delete_replication_group(self):
        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name, self.source_vms_input)

    @test_step
    def configure_replication_group(self):
        """Configures the replication group with primary storage"""
        self.admin_console.navigator.navigate_to_replication_groups()
        configure = self.replication_group.configure_virtualization(source_vendor=self._source_vendor,
                                                                    destination_vendor=self._destination_vendor,
                                                                    replication_type=self._replication_type.value)
        configure.add_default_group(self.group_name, self.source_hypervisor, self.source_vm,
                                    self.recovery_target, self.primary_storage_name)

    @test_step
    def verify_copy_precedence(self, aux_set=False):
        """Verify copy precedence
        aux_set(bool) : if false, copy precedence will be 0 or 1(if copyPrecedenceApplicable)
                        if True,  copy precedence will be 2
        """
        self.replication_group_obj.refresh()
        self.group_obj = self.replication_group_obj.get(self.group_name)

        if self.group_obj.copy_precedence_applicable:
            if aux_set:
                self.replication_helper.assert_comparison(self.group_obj.copy_for_replication, 2)
            else:
                self.replication_helper.assert_comparison(self.group_obj.copy_for_replication, 1)
        else:
            self.replication_helper.assert_comparison(self.group_obj.copy_for_replication, 0)

        self.log.info("Verified successfully the copy precedence applicable")

    @test_step
    def verify_sync_completion(self, aux_set=False):
        """Waits for backup job to complete and wait for aux(if true) then wait for sync to complete"""
        self.replication = Replication(self.commcell, self.group_name)
        self.replication.wait_for_first_backup()
        self.replication.get_running_replication_jobs()
        self.dr_helper.source_subclient = self.group_name
        if aux_set:
            sleep(300)
        rep_job_id = self.replication.get_last_replication_job_id()

        '''Verify copy used for replication'''
        if self.group_obj.copy_precedence_applicable:
            if aux_set:
                self.log.info("Verifying replication job is using secondary copy")
                self.dr_helper.verify_replication_job_copy(replication_job_id=rep_job_id,
                                                           expected_copy_precedence=2)
                self.log.info("Verified successfully replication job is using secondary copy")
            else:
                self.log.info("Verifying replication job is using primary copy")
                self.dr_helper.verify_replication_job_copy(replication_job_id=rep_job_id,
                                                           expected_copy_precedence=1)
                self.log.info("Verified successfully replication job is using primary copy")
        else:
            self.log.info("Verifying replication job is using primary copy")
            self.dr_helper.verify_replication_job_copy(replication_job_id=rep_job_id,
                                                       expected_copy_precedence=0)
            self.log.info("Verified successfully replication job is using primary copy")

    @test_step
    def perform_backup_sync(self, aux_set=False):
        """Perform incremental backup,
        aux(bool)= True, if aux is used for replication
        """
        backup_options = OptionsHelper.BackupOptions(self.dr_helper.source_auto_subclient)
        backup_options.backup_type = "INCREMENTAL"
        self.dr_helper.source_auto_subclient.backup(backup_options, skip_discovery=True)
        self.verify_sync_completion(aux_set)

    @test_step
    def add_secondary_validate(self):
        """Configure secondary in replication group and validate it group is updated"""
        self.secondary_storage = 'Secondary'
        self.replication_helper.add_storage(self.group_name, storage_name=self.secondary_storage,
                                            storage_pool=self.secondary_storage_name)
        self.replication_helper.verify_storage(group_name=self.group_name,
                                               storage_list=[self.primary_storage_name, self.secondary_storage_name])

    @test_step
    def set_copy_default(self, secondary=False):
        """Set copy(Primary / Secondary(if true)) in copy for replication in group"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)

        if secondary:
            self.group_details.overview.storageOperations.change_copy_for_replication(copy_name=self.secondary_storage)
        else:
            primary_storage = 'Primary'
            self.group_details.overview.storageOperations.change_copy_for_replication(copy_name=primary_storage)

    @test_step
    def delete_aux(self):
        """Remove the aux from replication in group"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        self.group_details.overview.storageOperations.delete_storage(copy_name=self.secondary_storage)
        self.replication_helper.verify_storage(group_name=self.group_name,
                                            storage_list=[self.primary_storage_name])

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.delete_replication_group()
            self.configure_replication_group()

            self.logout()
            self.verify_copy_precedence()
            self.verify_sync_completion()

            self.login()
            self.add_secondary_validate()
            self.logout()
            self.verify_copy_precedence()
            self.perform_backup_sync()

            self.login()
            self.set_copy_default(secondary=True)
            self.logout()
            self.verify_copy_precedence(aux_set=True)
            self.perform_backup_sync(aux_set=True)

            self.login()
            self.set_copy_default()
            self.logout()
            self.verify_copy_precedence()
            self.perform_backup_sync()

            self.login()
            self.delete_aux()
            self.logout()
            self.verify_copy_precedence()
            self.perform_backup_sync()

            self.login()
            self.delete_replication_group()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
