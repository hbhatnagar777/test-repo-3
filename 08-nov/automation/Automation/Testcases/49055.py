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

Sample input:
"49055": {
      "group_name": "repl_group"
}

"""

from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.replication import Replication
from VirtualServer.VSAUtils import OptionsHelper

from Web.Common.page_object import handle_testcase_exception
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """Class for executing VSA Backup and Replication when Destination VM is powered ON"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - VMW Live sync - Replication with destination VM powered ON"
        self.tcinputs = {
            "group_name": None,
        }

        self.backup_options = None
        self.replication = None
        self.group_name = None
        self.last_replication_job = None

    def get_replication_status(self):
        vm_pair = self.replication.vm_pairs[self.replication.vm_list[0]]['Replication'].vm_pair
        return vm_pair.status

    def setup(self):
        """Setup function for test case"""
        self.group_name = self.tcinputs['group_name']
        self.replication = Replication(self.commcell, replication_group=self.group_name)

    @test_step
    def backup(self):
        """Run Incremental backup and store last successful replication job ID"""
        self.last_replication_job = list(self.replication.vm_pairs.values())[0]['Replication'].vm_pair.latest_replication_job
        self.replication.pre_validation()
        self.backup_options = OptionsHelper.BackupOptions(self.replication.auto_subclient)
        self.backup_options.backup_type = "INCREMENTAL"
        self.replication.auto_subclient.backup(self.backup_options, skip_discovery=True)

    @test_step
    def replication_to_pending(self):
        """Replication job should go to pending state"""
        self.log.info('Sleeping for 1 minutes')
        sleep(60)
        vm_pair = list(self.replication.vm_pairs.values())[0]['Replication'].vm_pair
        for _ in range(15):
            vm_pair.refresh()
            if ((vm_pair.status == 'SYNC_PAUSED' and self.last_replication_job != vm_pair.last_replication_job)
                 or vm_pair.status == 'SYNC_STARTING'):
                break

            if vm_pair.status == 'IN_SYNC':
                raise CVTestStepFailure(f"[{vm_pair}] has reached In sync state"
                                        f" with replication job ID: {vm_pair.last_replication_job}")

            self.log.info('Waiting for 1 minute to let replication job trigger and reach pending state')
            sleep(60)
        else:
            raise CVTestStepFailure(f"[{vm_pair}] still not in Sync paused state, even though DR VM is powered on")

        self.log.info('Sleeping for 60 seconds to let job status update')
        sleep(60)
        job_obj = self.commcell.job_controller.get(str(vm_pair.last_replication_job))
        if job_obj.status.lower() != 'pending':
            raise CVTestStepFailure(
                f"Replication job [{job_obj.job_id}] should be in pending state "
                f"but it's in status [{job_obj.status.lower()}]"
            )

    @test_step
    def replication_to_complete(self):
        """Replication job to complete after failure"""
        vm_pair = list(self.replication.vm_pairs.values())[0]['Replication'].vm_pair
        job_obj = self.commcell.job_controller.get(str(vm_pair.last_replication_job))
        self.log.info('Resuming job to go to running state')
        job_obj.resume()

        job_obj.refresh()
        self.log.info('Waiting for 1 minute for job resume')
        sleep(60)
        job_obj.refresh()
        if job_obj.status.lower() != 'running':
            raise CVTestStepFailure(
                f"Replication job [{job_obj.job_id}] should be in running state "
                f"but it's in status [{job_obj.status.lower()}]"
            )
        self.log.info(
            f"Replication job [{job_obj.job_id}] is in {job_obj.status.lower()} status as expected"
        )
        if job_obj.status.lower() != 'completed':
            self.log.info(f"Waiting for Replication job [{job_obj.job_id}] to complete")
            if job_obj.wait_for_completion():
                self.log.info(f"Replication job with job id: {job_obj.job_id} Completed")
            else:
                raise CVTestStepFailure(f"Replication Job {job_obj.job_id} Failed")

    def run(self):
        """Main function for test case execution"""
        try:
            self.replication.power_on_vms(source=False)
            self.backup()
            self.replication_to_pending()
            self.replication.power_off_vms(source=False)
            self.replication_to_complete()
            self.replication.post_validation()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Cleanup testdata"""
        try:
            vm_pair = list(self.replication.vm_pairs.values())[0]['Replication']
            vm_pair.cleanup_test_data(source=True)
        except Exception:
            self.log.warning("Testcase cleanup was not completed")
