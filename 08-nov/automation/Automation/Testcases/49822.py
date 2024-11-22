# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

VMW VM Filtering TC - Streaming.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

Sample Input:

"49822": {
      "ClientName": "sk-vmw-client",
      "AgentName": "Virtual Server",
      "InstanceName": "VMWare",
      "BackupsetName": "defaultbackupset",
      "SubclientName": "sk-vmw-sub"
      }
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from Web.Common.page_object import TestStep
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing VSA VM Filtering TC - Streaming"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "v2: Vmware VM Filtering"
        self.auto_subclient = None
        self.backup_options = None
        self.vm_restore_options = None
        self.test_individual_status = True
        self.test_individual_failure_message = ""

    def setup(self):
        """Setup function for test case"""
        self.auto_subclient = VirtualServerUtils.subclient_initialize(self)
        if not self.auto_subclient.auto_vsaclient.isIndexingV2:
            self.test_individual_status = False
            self.test_individual_failure_message = 'This testcase is for indexing v2. The client passed is indexing v1'
            raise Exception

    @test_step
    def backup(self):
        """Run FULL backup"""
        self.backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
        self.backup_options.backup_type = "FULL"
        self.auto_subclient.backup(self.backup_options)

    @test_step
    def validate_vm_filtering(self):
        """Validate VM Filtering"""
        backup_job_id = self.auto_subclient.backup_job.job_id
        backedup_vms = self.auto_subclient.get_vms_from_backup_job(backup_job_id)
        self.log.info(f"Backedup VMs: {backedup_vms}")
        self.log.info(f"VM List: {self.auto_subclient.vm_list}")
        assert set(backedup_vms) == set(self.auto_subclient.vm_list)
        self.log.info("Successfully validated VM Filtering")

    @test_step
    def full_vm_restore(self):
        """Full VM out of place restore"""
        self.vm_restore_options = OptionsHelper.FullVMRestoreOptions(
            self.auto_subclient, self)
        self.vm_restore_options.power_on_after_restore = True
        self.vm_restore_options.unconditional_overwrite = True
        VirtualServerUtils.set_inputs(self.tcinputs, self.vm_restore_options)
        self.auto_subclient.virtual_machine_restore(self.vm_restore_options)

    @test_step
    def clean_up(self):
        """Cleanup after TC execution"""
        try:
            self.auto_subclient.cleanup_testdata(self.backup_options)
            self.auto_subclient.post_restore_clean_up(self.vm_restore_options, status=self.test_individual_status)
        except Exception as exp:
            self.log.warning(
                f"Following exception was encountered during cleanup: {exp}")
            self.log.warning("Testcase and/or Restored vm cleanup was not completed")

    def run(self):
        """Main function for test case execution"""
        try:
            self.backup()

            try:
                self.validate_vm_filtering()
                self.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)

        finally:
            try:
                self.clean_up()
            except Exception as exp:
                self.log.error(f"Cleanup Failed, Exception: {exp}")
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
