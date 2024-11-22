# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Live sync Resiliency testcase to Introduce network errors by changing host file entry of vcenter
in proxy machine.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"49354": {
      "group_name": "rep_group_1"
}
"""

from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.replication import Replication
from AutomationUtils.machine import Machine

from Web.Common.page_object import handle_testcase_exception
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """Class for executing VSA Fake connectivity issue to VCenter"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMW Live sync Resiliency - Introduce network errors"
        self.tcinputs = {
            "group_name": None,
        }
        self.proxy_machine = None
        self.vcenter_hostname = None
        self.backup_options = None
        self.replication = None
        self.group_name = None
        self.last_replication_job = None
        self.current_replication_job = None

    def _initialize_proxy_machine_obj(self):
        """Creates restore proxy machine object"""
        target = self.commcell.recovery_targets.get(self.replication.group.recovery_target)
        if target.access_node:
            proxy_client = target.access_node
        else:
            proxy_client = self.replication.destination_auto_instance.get_proxy_list()[0]
        self.log.info(f"Initializing proxy Machine Object of [{proxy_client}]")
        self.proxy_machine = Machine(proxy_client, self.commcell)
        self.vcenter_hostname = self.replication.destination_auto_instance.hvobj.prop_dict["server_name"]

    def _add_fake_host_entry(self):
        """Add fake host entry, wait for 15 secs and remove fake host entry"""
        fake_ip = "172.16.1.1"
        self.log.info(
            f"Adding fake host file entry in {self.proxy_machine.machine_name}"
            f"for vcenter {self.vcenter_hostname}"
        )
        # Add fake host entry
        self.proxy_machine.add_host_file_entry(self.vcenter_hostname, fake_ip)

    def _remove_fake_host_entry(self):
        self.log.info(f"Removing fake host file entry in {self.proxy_machine.machine_name}")
        # Remove fake host entry
        self.proxy_machine.remove_host_file_entry(self.vcenter_hostname)

    def setup(self):
        """Setup function for test case"""
        self.group_name = self.tcinputs['group_name']
        self.replication = Replication(self.commcell, replication_group=self.group_name)

    @test_step
    def backup(self):
        """Run Incremental backup"""
        self.last_replication_job = (list(self.replication.vm_pairs.values())[0]['Replication']
                                     .vm_pair.latest_replication_job)
        self.replication.pre_validation()
        backup_job = self.replication.group.subclient.backup("Full")
        self.log.info("Waiting for backup job: [%s] to complete" % str(backup_job.job_id))
        if not backup_job.wait_for_completion():
            raise Exception(f"Backup job: [{backup_job.job_id}] failed to complete")

    @test_step
    def replication_to_pending(self):
        """Replication job should go to pending state"""
        self.log.info('Sleeping for 1 minutes')
        sleep(60)
        self.log.info(
            f'Sleeping for 1 hour 15 minutes for the Replication job '
            f'to go to pending state'
        )
        vm_pair = list(self.replication.vm_pairs.values())[0]['Replication'].vm_pair
        # Run for 75 times for 1 minute sleep each. i.e 75 minutes or 1:15 hour wait
        for _ in range(75):
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
            raise CVTestStepFailure(f"[{vm_pair}] still not in Sync paused state, "
                                    f"even though proxy is not able to access vCenter")

        if vm_pair.status == 'SYNC_PAUSED' and self.last_replication_job != vm_pair.last_replication_job:
            # Get the replication job status from last replication job if the sync status is sync in progress
            job_obj = self.commcell.job_controller.get(str(vm_pair.last_replication_job))
        else:
            # Find all replication jobs for source hypervisor and then
            # select the one where subclientId is set in job's task details
            job_ids = self.commcell.job_controller.active_jobs(
                vm_pair._agent_object._client_object.client_name,
                filters={"jobFilter": "REPLICATION"}
            )
            for job_id, job_dict in job_ids.items():
                job_obj = self.commcell.job_controller.get(job_id)
                job_subclient_id = str(job_obj.task_details.get('associations', [{}])[0].get('subclientId'))
                if job_subclient_id == str(vm_pair._subclient_id):
                    if job_dict.get('status').lower() in ["pending", "running"]:
                        break
                    else:
                        raise CVTestStepFailure(f"Replication job: [{job_id}] is not in pending state")
            else:
                raise CVTestStepFailure(f"Cannot find replication job linked to Group: [{self.group_name}]")

        connection_broken_event_found = False
        for _ in range(10):
            for event in job_obj.get_events():
                if event.get('eventCode') in ["91:465", "91:73", "91:238"]:
                    connection_broken_event_found = True
                    break
            if connection_broken_event_found or job_obj.status.lower() == 'pending':
                break
            self.log.info("Waiting for 30 seconds to let replication job reach pending state")
            sleep(30)
        else:
            # In 10 minutes, replication job didn't go to pending or connection broken event not found
            raise CVTestStepFailure(
                f"Replication job [{job_obj.job_id}] should be in pending state "
                f"but it's in status [{job_obj.status.lower()}]"
            )
        self.current_replication_job = job_obj

    @test_step
    def replication_to_complete(self):
        """Replication job to complete after failure"""
        vm_pair = list(self.replication.vm_pairs.values())[0]['Replication'].vm_pair
        job_obj = self.current_replication_job

        self.log.info('Resuming job to go to running state')
        job_obj.resume()
        if job_obj.status.lower() == 'pending':
            self.log.info(
                f'Sleeping for 120 seconds for the replication status of VM'
                f' [{vm_pair}] to go to running state'
            )
            sleep(120)
            job_obj.refresh()
        if job_obj.status.lower() == 'pending':
            raise CVTestStepFailure(
                f"Replication job [{job_obj.job_id}] should not be in pending state "
                f"but it's in status [{job_obj.status.lower()}]"
            )
        self.log.info(f"Waiting for Replication job [{job_obj.job_id}] to complete")
        if not job_obj.wait_for_completion():
            self.log.info(f"Replication job with job id: {job_obj.job_id} failed")
            raise CVTestStepFailure(f"Replication job [{job_obj.job_id}] failed")
        self.log.info(f"Replication job [{job_obj.job_id}] completed")

    def run(self):
        """Main function for test case execution"""
        try:
            self.replication.power_off_vms(source=False)
            self._initialize_proxy_machine_obj()
            self.backup()
            self._add_fake_host_entry()
            self.replication_to_pending()
            self._remove_fake_host_entry()
            self.replication_to_complete()
            self.replication.post_validation()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Cleanup testdata"""
        try:
            self._remove_fake_host_entry()
            vm_pair = list(self.replication.vm_pairs.values())[0]['Replication']
            vm_pair.cleanup_test_data(source=True)
        except Exception:
            self.log.warning("Testcase cleanup was not completed")
