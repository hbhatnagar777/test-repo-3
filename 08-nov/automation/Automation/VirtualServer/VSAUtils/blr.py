# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This File Contains all the helper methods necessary for BLR operation"""
from time import sleep

from cvpysdk.backupsets._virtual_server import vmware as bs_vmware
from cvpysdk.job import Job
from cvpysdk.subclients.virtualserver import vmware as sc_vmware
from cvpysdk.virtualmachinepolicies import VirtualMachinePolicies

from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.HypervisorHelper import VmwareHelper
from VirtualServer.VSAUtils.VMHelper import VmwareVM


class BLRHelper:
    """A wrapping of BLR related APIs with the VMWare VMs"""

    TEST_BOOT_VM_NAME = "Automation_test_boot_vm"
    PERMANENT_BOOT_VM_NAME = "Automation_permanent_boot_vm"

    def __init__(self, hypervisor: VmwareHelper, vm: VmwareVM, backupset: bs_vmware, subclient: sc_vmware):
        self._hypervisor = hypervisor
        self._vm = vm
        self._commcell = vm.commcell
        self._log = vm.log
        self._subclient = subclient
        self._backupset = backupset
        self.pair = None
        self.test_data_path = None
        self.controller = Machine()

    def _check_for_job_completion(self, jobs, job_type):
        """Checks for the completion of job

        Args:
            jobs     (dict): Dict of jobs which are currently running

            job_type (str): type of job

        """
        latest_job = list()
        for _ in range(20):
            self._log.info("Waiting for the job to be scheduled")
            sleep(3)
            jobs_ = self._commcell.job_controller.active_jobs(job_filter=job_type)
            latest_job = jobs_.keys() - jobs.keys()
            if latest_job:
                break
        if not latest_job:
            raise Exception(f"{job_type} Job is not being scheduled to run")
        latest_job = latest_job.pop()
        job = Job(self._commcell, latest_job)
        self._log.info(f"Job Id: {job.job_id}")
        if job.wait_for_completion() is False:
            raise Exception(f"Job: {latest_job}:{self._commcell.job_controller.get(latest_job).pending_reason}")

    def create_blr_pair(self, target, plan_name, rpstore=None, granular_options=None):
        """Creates a BLR Pair. This method can create only one BLR pair for a VM.
        Re invoking this method after a successful creation would cause an exception

        Args:
            target  (str): Name of the Target [Virtual Machine Policy]

            plan_name(str): Name of the plan

            rpstore (str)                 : Name of the RPStore.
                default : None. If name of the RPStore is given, granular mode is chosen else Live mode

            granular_options(dict)        : Dict which contains granular recovery options
                 default : None.

        """

        policies = VirtualMachinePolicies(self._commcell)
        try:
            policy = policies.get(target)
        except Exception as excp:
            raise Exception(f"CVTestStepFailure -create_blr_pair: {excp}")

        backup_jobs = self._commcell.job_controller.active_jobs(job_filter="backup")
        restore_jobs = self._commcell.job_controller.active_jobs(job_filter="restore")

        self._log.info("creating BLR replication Pair")
        self._subclient.create_blr_replication_pair(target=policy, vms=[self._vm.vm_name], plan_name=plan_name,
                                                    rpstore=rpstore, granular_options=granular_options)
        self._check_for_job_completion(backup_jobs, "backup")
        self._check_for_job_completion(restore_jobs, "restore")

        sleep(10)
        self._backupset.refresh()
        self._log.info("Fetching pair details")
        self.pair = self._backupset.get_blr_replication_pair(self._vm.vm_name)
        if self.pair.status != "REPLICATING":
            raise Exception(f"BLR pair is in {self.pair.status} state")

    def write_temp_data(self, dir_count, file_count, file_size):
        """Writes data to the virtual machine

        Args:
            dir_count: No of directories

            file_count: No of files per directory

            file_size: size of file

        """
        local_testdata_path = VirtualServerUtils.get_testdata_path(self.controller)
        self.controller.generate_test_data(local_testdata_path, dir_count, file_count, file_size)
        drive_letter = list(self._vm.machine.get_storage_details()["drive"].keys())[0]
        self._log.info("writing test data")
        self.test_data_path = self._vm.machine.join_path(drive_letter, "Dummy")
        self._hypervisor.copy_test_data_to_each_volume(self._vm.vm_name, drive_letter, "Dummy", local_testdata_path)

    def get_boot_vm(self, test_boot):
        """Boots the VM and validates content and deletes the VM as well

        Args:
            test_boot    (bool):  Whether to boot vm in test mode

        """
        vm_name = f"{BLRHelper.TEST_BOOT_VM_NAME}" if test_boot else f"{BLRHelper.PERMANENT_BOOT_VM_NAME}"
        vm_name = f"{vm_name}{self._vm.vm_name}"
        boot = self.pair.create_test_boot if test_boot else self.pair.create_permanent_boot
        sleep(120)
        boot(vm_name)
        self._log.info("Booting VM")
        sleep(30)

        self._hypervisor.VMs = vm_name
        boot_vm = self._hypervisor.VMs[vm_name]
        if test_boot:
            boot_vm.attach_network_adapter()
            sleep(30)

        boot_vm.update_vm_info(force_update=True)
        boot_vm.update_vm_info(prop="All")
        return boot_vm

    def cleanup_test_data(self):
        """Deletes the BLR Pair and cleans up test data"""
        self.pair.delete()
        sleep(30)
        try:
            assert self.pair.status == "DELETED"
        except AssertionError:
            raise Exception("Failed to Delete the pair")
        self._vm.machine.remove_directory(self.test_data_path)
