# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2020 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Base class for all tests about DR Orchestration. This is inherited from class CVTestCase. This
should be overriden by other classes which share different operations provided here.

CVTestDROrchestration is the only class defined in this file.

CVTestDROrchestration: This class defines almost all necessary setups and validations. To implement
child classes, you should inherit this class and feed corresponding operations to the methods this
class.

CVTestDROrchestration:
   __init__()                       --  Initialize shared attributes

    setup()                         --  Set up `self.tcinputs`, `self._auto_client` object,
                                        `self._hypervisor`, and `self._controller_machine`object.

    run()                           --  Run function for the test case. This should be overridden.

    tear_down()                     --  Clean up test data generated on the controller machine.

    ##### internal methods #####
    _get_hypervisor_vm()                --  Return a HypervisorVM object with the given name

    _init_auto_client()                 --  Initialize the `AutoVSAVSClient` object

    _init_hypervisor()                  --  Initialize the `Hypervisor` object

    _init_controller_machine()          --  Initialize the controller machine object

    _fetch_last_synced_backup_job_ids() --  Fetches last synced backup job ids from database

    _fetch_backup_jobs_to_sync_job_ids()--  Fetches backup jobs to sync job ids from database

    _run_operation()                    --  Generic function to run all operations

    _wait_for_job_and_validate()        --  Wait for a job and validate it

    _do_testboot()                      --  Run testboot from a provided operation function

    _do_planned_failover()              --  Run planned failover from a provided operation function

    _do_unplanned_failover()            --  Run unplanned failover from a provided operation
                                            function

    _do_point_in_time_failover()        --  Run point-in-time failover from a provided operation
                                            function

    _do_failback()                      --  Run failback from a provided operation function

    _do_undo_failover()                 --  Run undo failover from a provided operation function

    _schedule_reverse_replication()     --  Schedule reverse replication from a provided operation
                                            function

    _force_one_reverse_replication()    --  Force one reverse replication from a provided operation
                                            function

    _init_vm_machine()                  --  Initialize a `Machine` object from a `HypervisorVM`

    _put_testdata_on()                  --  Generate testdata on the specified machine

    _check_testdata_on()                --  Check whether the testdata is on the specified machine

    ##### property methods #####
    _src_hypervisor_vm                          --  The src `HypervisorVM` object

    _dst_hypervisor_vm                          --  The dst `HypervisorVM` object

    _operation_validate_dr_orchestration_job    --  Operation to validate DR orchestration jobs

    _operation_testboot                         --  Operation to run testboot

    _operation_planned_failover                 --  Operation to run planned failover

    _operation_unplanned_failover               --  Operation to run unplanned failover

    _operation_point_in_time_failover           --  Operation to run point-in-time failover

    _operation_failback                         --  Operation to run failback

    _operation_undo_failover                    --  Operation to run undo failover

    _operation_schedule_reverse_replication     --  Operation to schedule reverse replication

    _operation_force_one_reverse_replication    --  Operation to force one reverse replication

    _replication_ids                            --  Replication IDs in this test

"""

import os
from datetime import datetime
import socket
from time import sleep

from cvpysdk.job import Job
from cvpysdk.drorchestration.failovergroups import FailoverGroups

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils import VirtualServerHelper, VirtualServerConstants
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils.VMHelper import HypervisorVM


class CVTestDROrchestration(CVTestCase):
    """Class for test cases about DR Orchestration"""

    def __init__(self):
        super(CVTestDROrchestration, self).__init__()
        self.product = self.products_list.DRORCHESTRATION
        self.feature = self.features_list.DRORCHESTRATION
        self.show_to_user = True

        # collection of source vm names to be tested
        self._src_vm_names = []
        # collection of destination vm names to be tested
        self._dst_vm_names = []

        # will be initialized in the `setup()`
        self._hypervisor = None
        self._auto_client = None
        self._controller_machine = None
        self._dest_hypervisor = None
        self._dest_region = None

        # collection of testdata folder names
        # used for cleanup in `tear_down()`
        self._testdata_list = []

        self.tcinputs = {
            "ClientName": "",
            "AgentName": "",
            "InstanceName": ""
        }


    def setup(self):
        """Initializes all member variables for later use."""

        # fills in default values for these two fields
        self.tcinputs["approvalRequired"] = self.tcinputs.get(
            "approvalRequired", False)
        self.tcinputs["initiatedfromMonitor"] = self.tcinputs.get(
            "initiatedfromMonitor", True)

        # initializes other member variables
        try:
            self._auto_client = self._init_auto_client()
            self._hypervisor = self._init_hypervisor()
            self._dest_region = self.tcinputs.get("DstRegion", None)
            if self._dest_region is not None:
                self._dest_hypervisor = self._init_dest_hypervisor()
            self._controller_machine = self._init_controller_machine()
        except Exception as exp:
            self.log.error(str(exp))
            raise Exception("Failed during `setup()`.")

    def run(self):
        """This should be overridden by child classes."""
        raise NotImplementedError(
            "`run` is not implemented by its child class.")

    def tear_down(self):
        """Cleans up test data generated during this test on this machine"""
        base_dir = os.getcwd()
        for dir_name in self._testdata_list:
            target_dir = os.path.join(base_dir, dir_name)
            if self._controller_machine.check_directory_exists(target_dir):
                self._controller_machine.remove_directory(target_dir)

    def _get_hypervisor_vm(
            self,
            vm_name: str,
            hypervisor: Hypervisor = None) -> HypervisorVM:
        """Returns the `HypervisorVM` object with the given VM name

        Here I used look up on demand because it is possible that the VM is
        initially powered off. Initializing this in the `setup()` will
        forcely power on the machine (might cause unexpected outcome during
        testing), and it will also take a lot of time to complete.
        """

        # fills in default object
        if not hypervisor:
            hypervisor = self._hypervisor

        #sleep(120)
        hypervisor_vm = hypervisor.VMs.get(vm_name)
        if hypervisor_vm:
            # If the target vm already exists, just update it.
            hypervisor_vm.update_vm_info(force_update=True)
        else:
            self.log.info(
                "Initializing a `HypervisorVM` object for %s.", vm_name)
            # explicitly fetches the vm information with the name `vm_name`
            hypervisor.VMs = vm_name
            hypervisor_vm = hypervisor.VMs.get(vm_name)

            # explicitly trigger `_set_credentials()` in `HypervisorVM` class
            hypervisor_vm.vm_guest_os = hypervisor_vm.guest_os

        return hypervisor_vm

    @property
    def _src_hypervisor_vms(self) -> [HypervisorVM]:
        """Returns the src `HypervisorVM` objects"""
        src_hypervisor_vms = []
        for src_vm_name in self._src_vm_names:
            src_hypervisor_vms.append(self._get_hypervisor_vm(src_vm_name))
        return src_hypervisor_vms

    @property
    def _dst_hypervisor_vms(self) -> [HypervisorVM]:
        """Returns the dst `HypervisorVM` objects"""
        dst_hypervisor_vms = []
        for dst_vm_name in self._dst_vm_names:
            dst_hypervisor_vms.append(self._get_hypervisor_vm(dst_vm_name, hypervisor=self._dest_hypervisor))
        return dst_hypervisor_vms

    @property
    def _operation_validate_dr_orchestration_job(self):
        """Returns the operation to validate DR orchestration jobs

        This should be overridden.
        """
        raise NotImplementedError(
            "`_operation_validate_dr_orchestration_job` is not implemented "
            "by its child class.")

    @property
    def _operation_testboot(self):
        """Returns the operation to run testboot

        This should be overridden.
        """
        raise NotImplementedError(
            "`_operation_testboot` is not implemented by its child class.")

    @property
    def _operation_planned_failover(self):
        """Returns the operation to run planned failover

        This should be overridden.
        """
        raise NotImplementedError(
            "`_operation_planned_failover` is not implemented by its child "
            "class.")

    @property
    def _operation_unplanned_failover(self):
        """Returns the operation to run unplanned failover

        This should be overridden.
        """
        raise NotImplementedError(
            "`_operation_unplanned_failover` is not implemented by its "
            "child class.")

    @property
    def _operation_point_in_time_failover(self):
        """Returns the operation to run point-in-time failover

        This should be overridden.
        """
        raise NotImplementedError(
            "`_operation_point_in_time_failover` is not implemented by its "
            "child class.")

    @property
    def _operation_failback(self):
        """Returns the operation to run failback

        This should be overridden.
        """
        raise NotImplementedError(
            "`_operation_failback` is not implemented by its child class.")

    @property
    def _operation_undo_failover(self):
        """Returns the operation to run undo failover

        This should be overridden.
        """
        raise NotImplementedError(
            "`_operation_undo_failover` is not implemented by its child "
            "class.")

    @property
    def _operation_schedule_reverse_replication(self):
        """Returns the operation to schedule reverse replication

        This should be overridden.
        """
        raise NotImplementedError(
            "`_operation_schedule_reverse_replication` is not implemented "
            "by its child class.")

    @property
    def _operation_force_one_reverse_replication(self):
        """Returns the operation to force one reverse replication

        This should be overridden.
        """
        raise NotImplementedError(
            "`_operation_force_one_reverse_replication` is not implemented "
            "by its child class.")

    @property
    def _replication_ids(self) -> [int]:
        """Returns the list of replications IDs

        This is used to fetch backup job IDs in
        `_fetch_last_synced_backup_job_ids()` and
        `_fetch_backup_jobs_to_sync_job_ids()`.

        This should be overridden.
        """
        raise NotImplementedError(
            "`_replication_ids` is not implemented by its child class.")

    def _init_auto_client(self) -> VirtualServerHelper.AutoVSAVSClient:
        """Initializes the `AutoVSAVSClient` object.

        This should only be used in `setup()`. Making this a function helps
        shorten the length of `setup()`.
        """
        self.log.info("Started to initialize the `AutoVSAVSClient` object.")
        try:
            auto_commcell = VirtualServerHelper.AutoVSACommcell(
                self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(
                auto_commcell, self.client)
        except Exception as exp:
            raise Exception(
                "Failed to initialize the `AutoVSAVSClient` object: "
                "{}.".format(exp))
        self.log.info("Initialization of `AutoVSAVSClient` object finished.")
        return auto_client

    def _init_hypervisor(self) -> Hypervisor:
        """Initializes the `Hypervisor` object.

        This should only be used in `setup()`. Making this a function helps
        shorten the length of `setup()`.
        """
        self.log.info("Started to initialize the `Hypervisor` object.")
        try:
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                self._auto_client, self.agent, self.instance)
            hypervisor = auto_instance.hvobj
        except Exception as exp:
            raise Exception(
                "Failed to initialize the `Hypervisor` object: "
                "{}.".format(exp))
        self.log.info("Initialization of `Hypervisor` object finished.")
        return hypervisor

    def _init_dest_hypervisor(self) -> Hypervisor:
        """Initializes the `Hypervisor` object.

        This should only be used in `setup()`. Making this a function helps
        shorten the length of `setup()`.
        """
        self.log.info("Started to initialize the destination `Hypervisor` object.")
        try:
            if self._dest_region is not None:
                auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                    self._auto_client, self.agent, self.instance, region=self.tcinputs["DstRegion"])
            else:
                auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                    self._auto_client, self.agent, self.instance)
            hypervisor = auto_instance.hvobj
        except Exception as exp:
            raise Exception(
                "Failed to initialize the `Hypervisor` object: "
                "{}.".format(exp))
        self.log.info("Initialization of destination `Hypervisor` object finished.")
        return hypervisor

    def _init_controller_machine(self) -> Machine:
        """Initializes the controller machine object.

        This should only be used in `setup()`. Making this a function helps
        shorten the length of `setup()`.
        """
        self.log.info("Started to initialize the controller machine object.")
        try:
            controller_machine = Machine(
                socket.gethostbyname_ex(
                    socket.gethostname())[2][0],
                self.commcell)
        except Exception as exp:
            raise Exception(
                "Failed to initialize the controller machine object: "
                "{}.".format(exp))
        self.log.info("Initialization of `Hypervisor` object finished.")
        return controller_machine

    def _fetch_last_synced_backup_job_ids(self) -> [int]:
        """Fetches last synced backup job IDs from database
        This uses SQL query to fetch these IDs.

            Args:

            Returns:
                A list of last synced backup job ids associated with this
                replication ([int])
        """
        ret = []
        sql_template = "SELECT lastSyncedBkpJob FROM app_vsareplication " \
                       "WHERE replicationId = {}"
        for replication_id in self._replication_ids:
            sql_query = sql_template.format(replication_id)
            res = self._auto_client.auto_commcell.execute(sql_query)
            if res:
                ret.append(int(res))
        assert len(ret) == len(self._replication_ids)
        return ret

    def _fetch_backup_jobs_to_sync_job_ids(self, job_id: int) -> [int]:
        """Fetches backup jobs to sync IDs from database
        This uses SQL query to fetch these IDs. This should be executed during
        a DR orchestration operation.
        The field in "BkpJobsToSync" will be filled at some point during the
        operation. So a while loop here checks the field until it gets filled
        in.

            Args:
                job_id (int)        --  serves as a filter that returned job
                                        ids should be after this job id

            Returns:
                a list of job ids associated with this replication ([int])
        """
        record = {}
        sql_template = "SELECT BkpJobsToSync FROM app_vsareplication WHERE " \
                       "replicationId = {}"
        job = Job(self.commcell, job_id)
        while (not job.is_finished) and len(record) != len(self._replication_ids):
            for replication_id in self._replication_ids:
                sql_query = sql_template.format(replication_id)
                res = self._auto_client.auto_commcell.execute(sql_query)
                if res:
                    # It is possible that this field contains multiple job ids.
                    # We only need the latest one.
                    res = max([int(x) for x in res.split(",")])
                    if res > int(job_id):
                        record[replication_id] = int(res)

            # waits for 10 seconds for the next check
            sleep(10)

        ret = []
        for replication_id in self._replication_ids:
            ret.append(record.get(replication_id, None))

        return ret

    def _run_operation(self, job_name: str, operation_func,
                       check_backup_job_id: bool):
        """Runs an operation from the Replication Monitor

            Args:
                job_name (string)           --  string of the job name

                operation_func (function)   --  function object of the
                                                operation which should
                                                return a tuple
                                                (job_id, task_id)

                check_backup_job_id (bool)  --  indicates whether to verify
                                                backup job IDs during the
                                                operation
                                                This should be true only when
                                                backups are involved in the
                                                specified operation.

            Returns:

        """
        try:
            # runs the specified operation
            (self.jobID, task_id) = operation_func()
            self.log.info(
                "Started executing %s with Job ID: [%d], Task ID: [%d].",
                job_name,
                int(self.jobID),
                int(task_id))

            if check_backup_job_id:
                # fetches backup job ids for later use
                backup_job_to_sync_job_ids = \
                    self._fetch_backup_jobs_to_sync_job_ids(int(self.jobID))
                self.log.info("Backup job to sync job IDs are %s.",
                              str(backup_job_to_sync_job_ids))

            self._wait_for_job_and_validate(self.jobID)
            self.log.info("%s execution finished.", job_name)

            if check_backup_job_id:
                # needs to ensure the job ids fetched above finally get
                # replicated
                last_synced_backup_job_ids = \
                    self._fetch_last_synced_backup_job_ids()
                self.log.info("Last synced backup job IDs are %s.",
                              str(last_synced_backup_job_ids))
                if backup_job_to_sync_job_ids != last_synced_backup_job_ids:
                    raise Exception("Backups pending to sync are not "
                                    "replicated in the current replication.")

                # ensures all backup jobs are incremental
                for backup_job_id in backup_job_to_sync_job_ids:
                    backup_job = self.commcell.job_controller.get(
                        backup_job_id)
                    if backup_job.backup_level != 'Incremental':
                        raise Exception("Backups pending to sync are not "
                                        "incremental.")
                self.log.info("Validation on backups pending to sync "
                              "succeeded.")
        except Exception as exp:
            raise Exception(
                "Failed to execute {}: {}".format(job_name, str(exp)))

    def _wait_for_job_and_validate(self, job_id: int):
        """Waits for a job and validates its job phases

            Args:
                job_id (int) -- job ID

            Returns:
        """
        job_state = Job(self.commcell, job_id).wait_for_completion()

        if job_state is not True:
            raise Exception("Job state is {}".format(str(job_state)))

        validation_result = self._operation_validate_dr_orchestration_job(
            job_id)
        if validation_result is not True:
            raise Exception(
                "Validate DR Orchestration Job: {}".format(
                    str(validation_result)))

    def _do_testboot(self):
        self._run_operation(
            "Testboot",
            operation_func=self._operation_testboot,
            check_backup_job_id=False)

    def _do_planned_failover(self):
        # writes test data in the src VM for later check
        (local_path, remote_paths) = self._put_testdata_on(
            self._src_hypervisor_vms)

        self._run_operation("Planned Failover",
                            operation_func=self._operation_planned_failover,
                            check_backup_job_id=True)

        # waits for the dst VM to settle down
        sleep(60)

        # checks if the test data exist in the dst VM
        self.log.info(
            "Checking if the test data directory \"%s\" exist in the dst VM %s.",
            str(remote_paths),
            str(self._dst_vm_names))
        if self._check_testdata_on(
                self._dst_hypervisor_vms,
                local_path,
                remote_paths) is False:
            self.log.error(
                "%s should have existed in the dst VM %s.",
                str(remote_paths), str(self._dst_vm_names))
            raise Exception("Data validation failed.")
        self.log.info("Data validation succeeded.")

    def _do_unplanned_failover(self):
        # writes test data in the src VM for later check
        (local_path, remote_paths) = self._put_testdata_on(
            self._src_hypervisor_vms)

        self._run_operation("Unplanned Failover",
                            operation_func=self._operation_unplanned_failover,
                            check_backup_job_id=False)

        # waits for the dst VM to settle down
        sleep(60)

        # checks if the test data exist in the dst VM
        self.log.info(
            "Checking if the test data directory \"%s\" exist in the dst VM %s.",
            str(remote_paths),
            str(self._dst_vm_names))
        if self._check_testdata_on(
                self._dst_hypervisor_vms,
                local_path,
                remote_paths) is True:
            self.log.error(
                "%s should not have existed in the dst VM %s.",
                str(remote_paths), str(self._dst_vm_names))
            raise Exception("Data validation failed.")
        self.log.info("Data validation succeeded.")

    def _do_point_in_time_failover(self):
        # writes test data in the src VM for later check
        (local_path, remote_paths) = self._put_testdata_on(
            self._src_hypervisor_vms)

        self._run_operation(
            "Point-in-time Failover",
            operation_func=self._operation_point_in_time_failover,
            check_backup_job_id=False)

        # waits for the dst VM to settle down
        sleep(60)

        # checks if the test data exist in the dst VM
        self.log.info(
            "Checking if the test data directory \"%s\" exist in the dst VM %s.",
            str(remote_paths), str(self._dst_vm_names))
        if self._check_testdata_on(
                self._dst_hypervisor_vms,
                local_path,
                remote_paths) is True:
            self.log.error(
                "%s should not have existed in the dst VM %s.",
                str(remote_paths), str(self._dst_vm_names))
            raise Exception("Data validation failed.")
        self.log.info("Data validation succeeded.")

    def _do_failback(self):
        # writes test data in the dst VM for later check
        (local_path, remote_paths) = self._put_testdata_on(
            self._dst_hypervisor_vms)

        self._run_operation(
            "Failback",
            operation_func=self._operation_failback,
            check_backup_job_id=True)

        # waits for the src VM to settle down
        sleep(60)

        # checks if the test data exist in the src VM
        self.log.info(
            "Checking if the test data directory \"%s\" exist in the src VM %s.",
            str(remote_paths),
            str(self._src_vm_names))
        if self._check_testdata_on(
                self._src_hypervisor_vms,
                local_path,
                remote_paths) is False:
            self.log.error(
                "%s should have existed in the src VM %s.",
                str(remote_paths), str(self._src_vm_names))
            raise Exception("Data validation failed.")
        self.log.info("Data validation succeeded.")

    def _do_undo_failover(self):
        # writes test data in the dst VM for later check
        (local_path, remote_paths) = self._put_testdata_on(
            self._dst_hypervisor_vms)

        self._run_operation(
            "Undo Failover", operation_func=self._operation_undo_failover,
            check_backup_job_id=False)

        # waits for the src VM to settle down
        sleep(60)

        # checks if the previously written file is in the src VM
        self.log.info(
            "Checking if the test data directory \"%s\" exist in the src VM %s.",
            str(remote_paths),
            str(self._src_vm_names))
        if self._check_testdata_on(
                self._src_hypervisor_vms,
                local_path,
                remote_paths) is True:
            self.log.error(
                "%s should not have existed in the src VM %s.",
                str(remote_paths),
                str(self._src_vm_names))
            raise Exception("Data validation failed.")
        self.log.info("Data validation succeeded.")

    def _do_reverse_replication(self):
        self._schedule_reverse_replication()
        self._force_one_reverse_replication()

    def _schedule_reverse_replication(self):
        try:
            task_id = self._operation_schedule_reverse_replication()
            self.log.info(
                "Scheduled Reverse Replication with Task ID: [%d].",
                int(task_id))
        except Exception as exp:
            raise Exception(
                "Failed to schedule Reverse Replication: " + str(exp))

    def _force_one_reverse_replication(self):
        # writes test data in the dst VM for later check
        (local_path, remote_paths) = self._put_testdata_on(
            self._dst_hypervisor_vms)

        self._run_operation(
            "Reverse Replication",
            operation_func=self._operation_force_one_reverse_replication,
            check_backup_job_id=True)

        # checks if the previously written file is in the src VM
        self.log.info(
            "Checking if file %s exists in the src VM %s.",
            str(remote_paths),
            str(self._src_vm_names))

        # gives some time for the src VM to settle down
        sleep(60)

        if self._check_testdata_on(
                self._src_hypervisor_vms,
                local_path,
                remote_paths) is False:
            self.log.error(
                "%s should not have existed in the src VM %s.",
                str(remote_paths),
                str(self._src_vm_names))
            raise Exception("Data validation failed.")
        self.log.info("Data validation succeeded.")
        self.log.info("Powering off the VM %s.", str(self._src_vm_names))

        for src_hypervisor_vm in self._src_hypervisor_vms:
            if src_hypervisor_vm.power_state.lower() != "PowerOff".lower():
                src_hypervisor_vm.power_off()
                # gives some time for the src VM to power off
                sleep(60)

    def _init_vm_machine(self, hypervisor_vm: HypervisorVM) -> Machine:
        """Returns a `Machine` object from a `HypervisorVM` object."""

        max_try = 5
        cur_try = 1
        # I am facing the problem sometimes the `Machine` object cannot be
        # created for unknown reasons. Multiple tries help this issue.
        while cur_try <= max_try:
            try:
                # updates the info in the VM since the IP might change
                hypervisor_vm.update_vm_info(force_update=True)

                # explicitly triggers the `_set_credentials()` in class
                # `HypervisorVM`
                hypervisor_vm.vm_guest_os = hypervisor_vm.guest_os

                # successfully gets the object
                break
            except Exception as exp:
                if cur_try == max_try:
                    raise exp

            # sleeps 30 seconds to get another try
            sleep(30)
            cur_try += 1

        # `_set_credentials()` will update the `Machine` object
        return hypervisor_vm.machine

    def _put_testdata_on(self, hypervisor_vms: [HypervisorVM]) -> (str, [str]):
        """Generates testdata locally and copy them to the spcified VM.

            Args:
                hypervisor_vms ([HypervisorVM]) --  HypervisorVMs to put testdata on

            Returns:
                (str, [str])                    --  The file path on src and dst machine
                                                    respectively

        """

        # generates a distinct directory name
        timestamp = datetime.timestamp(datetime.now())
        dir_name = "test_{}_{}".format(self.id, timestamp)
        local_path = os.path.join(os.getcwd(), dir_name)

        # generates testdata locally
        generate_res = self._controller_machine.generate_test_data(
            local_path, 3, 5, 10)
        if generate_res is False:
            raise Exception(
                "Failed to generate test data at {}".format(local_path))
        self._testdata_list.append(dir_name)

        remote_paths = []
        for hypervisor_vm in hypervisor_vms:
            # generates destination path and copy testdata to it
            target_machine = self._init_vm_machine(hypervisor_vm)
            if VirtualServerConstants.is_windows(
                    target_machine.os_info.lower()):
                remote_path = "C:\\Users\\{}".format(hypervisor_vm.user_name)
                target_machine.copy_from_local(local_path, remote_path)
                remote_path += "\\{}".format(dir_name)
            else:
                remote_path = "/home/{}/{}".format(
                    hypervisor_vm.user_name, dir_name)
                target_machine.copy_from_local(local_path, remote_path)
            remote_paths.append(remote_path)

        return (local_path, remote_paths)

    def _check_testdata_on(
            self,
            hypervisor_vms: [HypervisorVM],
            local_path: str,
            remote_paths: [str]) -> bool:
        """Checks if the testdata in the local are identical to the ones in the remote end.

            Args:
                hypervisor_vms ([HypervisorVM]) --  VMs to check
                local_path (str)                --  File path on local machine
                remote_path ([str])             --  File path on target machines

            Returns:
                bool                            --  Result of checking
        """
        assert len(hypervisor_vms) == len(remote_paths)

        for i in range(len(hypervisor_vms)):
            hypervisor_vm = hypervisor_vms[i]
            remote_path = remote_paths[i]
            dst_machine = self._init_vm_machine(hypervisor_vm)
            try:
                self._auto_client.fs_testdata_validation(
                    dst_machine, local_path, remote_path)
            except BaseException as exp:
                return exp