# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2020 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Base class for all tests about the replication monitor. This is inherited from class
CVTestDROrchestration.

CVTestCaseReplicationMonitor is the only class defined in this file.

CVTestCaseReplicationMonitor: Class for executing this test case

CVTestCaseReplicationMonitor:
    __init__()                      --  Initializes only variables related to `ReplicationMonitor`

    setup()                         --  Sets up `self._replication_monitor` object,
                                        `self._src_vm_names`, and `self._dst_vm_names`

    run()                           --  Run function for the test case. This should be overridden.

    ##### internal methods #####
    _init_replication_monitor()     --  Initializes the `ReplicationMonitor` object

    _get_dst_vm_names()             --  Collects all corresponding destination VM names

    _fetch_replication_info()       --  Fetches the replication entries in this test

    _get_snapshot_names()           --  Gets the list of snapshot names with the guid

    _check_status_after_failover()  --  Checks sync status and failover status after failover

    _check_snapshots_after_planned_failover()   --  Checks snapshot names after planned failover

    _check_snapshots_after_unplanned_failover() --  Checks snapshot names after unplanned failover

    _check_snapshots_after_point_in_time_failvoer() --  Checks snapshot names fater point-in-time
                                                        failover

    _check_status_after_failback()              --  Checks the sync status and failover status
                                                    after failback

    _check_snapshots_after_failback()           --  Checks snapshot names after failback

    _check_status_after_reverse_replication()   --  Checks sync status and failover status after
                                                    reverse replication

    _check_snapshots_after_reverse_replication()--  Checks snapshot names after reverse replication

    _do_planned_failover()                      --  Runs planned failover from replication monitor

    _do_unplanned_failover()                    --  Runs unplanned failover from replication
                                                    monitor

    _do_point_in_time_failover()                --  Runs point-in-time failover from replication
                                                    monitor

    _do_failback()                              --  Runs failback from replication monitor

    _do_undo_failover()                         --  Runs undo failover from replication monitor

    _force_one_reverse_replication()            --  Forces one reverse replication from replication
                                                    monitor

    ##### property methods #####
    _operation_validate_dr_orchestration_job    --  operation to validate DR orchestration jobs
                                                    from replication group

    _operation_testboot                         --  operation to run testboot from replication
                                                    group

    _operation_planned_failover                 --  operation to run planned failover from
                                                    replication group

    _operation_unplanned_failover               --  operation to run unplanned failover from
                                                    replication group

    _operation_point_in_time_failover           --  operation to run point-in-time failover from
                                                    replication group

    _operation_failback                         --  operation to run failback from replication
                                                    group

    _operation_undo_failover                    --  operation to run undo failover from replication
                                                    group

    _operation_schedule_reverse_replication     --  operation to schedule reverse replication from
                                                    replication group

    _operation_force_one_reverse_replication    --  operation to force one reverse replication from
                                                    replication group

    _replication_ids                            --  list of replication IDs in this test

"""

from enum import Enum
import json

from cvpysdk.drorchestration.replicationmonitor import ReplicationMonitor

from VirtualServer.DROrchestration.cvtestcase_drorchestration import CVTestDROrchestration


class CVTestCaseReplicationMonitor(CVTestDROrchestration):
    """Class for test cases about the replication monitor."""

    def __init__(self):
        super(CVTestCaseReplicationMonitor, self).__init__()

        # collection of source vm names to be tested
        self._src_vm_names = []
        # collection of destination vm names to be tested
        self._dst_vm_names = []

        # will be initialized in the `setup()`
        self._replication_monitor = None

        self.tcinputs.update({
            "vmName": [],
            "failoverGroupId": ""
        })

        # default value indicating whether to check snapshots after operations
        # Some hypervisors which might not support snapshots should turn this
        # off.
        self._check_snapshots = True

    def setup(self):
        """Initializes all member variables for later use."""
        super(CVTestCaseReplicationMonitor, self).setup()

        try:
            if not isinstance(self.tcinputs["vmName"], list):
                # if the input is not what we expect, try to assume it as
                # json and convert it
                self.tcinputs["vmName"] = json.loads(self.tcinputs["vmName"])

            self._src_vm_names = self.tcinputs["vmName"]

            self.tcinputs["vmName"] = ""
            self._replication_monitor = self._init_replication_monitor()

            self._dst_vm_names = self._get_dst_vm_names()
            self.log.info(
                "Found src VM \"%s\" and dst VM \"%s\"",
                str(self._src_vm_names),
                str(self._dst_vm_names))
        except Exception as exp:
            self.log.error(str(exp))
            raise Exception("Failed during `setup()`.")

    def run(self):
        """This should be overridden by child classes."""
        raise NotImplementedError(
            "`run` is not implemented by its child class.")

    @property
    def _operation_validate_dr_orchestration_job(self):
        """Returns the operation to validate DR orchestration jobs"""
        return self._replication_monitor.validate_dr_orchestration_job

    @property
    def _operation_testboot(self):
        """Returns the operation to run testboot"""
        return self._replication_monitor.testboot

    @property
    def _operation_planned_failover(self):
        """Returns the operation to run planned failover"""
        return self._replication_monitor.planned_failover

    @property
    def _operation_unplanned_failover(self):
        """Returns the operation to run unplanned failover"""
        return self._replication_monitor.unplanned_failover

    @property
    def _operation_point_in_time_failover(self):
        """Returns the operation to run point-in-time failover"""
        return self._replication_monitor.point_in_time_failover

    @property
    def _operation_failback(self):
        """Returns the operation to run failback"""
        return self._replication_monitor.failback

    @property
    def _operation_undo_failover(self):
        """Returns the operation to run undo failover"""
        return self._replication_monitor.undo_failover

    @property
    def _operation_schedule_reverse_replication(self):
        """Returns the operation to schedule reverse replication"""
        return self._replication_monitor.schedule_reverse_replication

    @property
    def _operation_force_one_reverse_replication(self):
        """Returns the operation to force one reverse replication"""
        return self._replication_monitor.force_reverse_replication

    @property
    def _replication_ids(self) -> [int]:
        """Returns the list of replications IDs"""
        return self._replication_monitor._replication_Ids

    def _init_replication_monitor(self) -> ReplicationMonitor:
        """Initializes the `ReplicationMonitor` object."""
        self.log.info("Started to initialize the `ReplicationMonitor` object.")
        try:
            replication_monitor = ReplicationMonitor(
                self.commcell, self.tcinputs)
        except Exception as exp:
            raise Exception(
                "Failed to initialize the `ReplicationMonitor` object: {}.".format(exp))
        self.log.info(
            "Initialization of `ReplicationMonitor` object finished.")
        return replication_monitor

    def _get_dst_vm_names(self) -> [str]:
        """Collects all corresponding destination VM names"""
        dst_vm_names = []
        for src_vm_name in self._src_vm_names:
            for replication_entry in self._replication_monitor.replication_monitor:
                if replication_entry["sourceName"].lower(
                ) == src_vm_name.lower():
                    dst_vm_names.append(replication_entry["destinationName"])
                    break
        return dst_vm_names

    def _fetch_replication_info(self) -> [dict]:
        """Fetches the replication entries related to this test"""
        replication_info = []
        for src_vm_name in self._src_vm_names:
            for replication_entry in self._replication_monitor.replication_monitor:
                if replication_entry["sourceName"].lower(
                ) == src_vm_name.lower():
                    replication_info.append(replication_entry)
                    break
        return replication_info

    # Ref:
    # ....Common/XmlMessage/App.x
    class VSAReplicationStatus(Enum):
        """Enum of sync status"""
        VSAREP_NONE = 0  # Never synced
        VSAREP_COMPLETE = 1  # In Sync
        VSAREP_PENDING = 2  # Sync Pending
        VSAREP_RUNNING = 3  # Sync In Progress
        VSAREP_PAUSED = 4  # Sync Paused
        VSAREP_FAILED = 5  # Sync Failed
        VSAREP_DISABLED = 6  # Sync Disabled
        VSAREP_ENABLED = 7  # Sync Enabled
        VSAREP_VALIDATION_FAILED = 8  # Validation Failed
        VSAREP_JOB_QUEUED = 9  # Sync Queue
        VSAREP_REVERT_FAILED = 10  # Revert Failed
        VSAREP_STARTING = 11  # Sync Starting

    # Ref:
    # ...Common/XmlMessage/App.x#VSAFailoverStatus
    class VSAFailoverStatus(Enum):
        """Enum of failover status"""
        VSAREP_NONE = 0  # Never has been Failed Over
        VSAREP_FAILOVER_COMPLETE = 1  # Failover Complete
        VSAREP_FAILOVER_RUNNING = 2  # Failover In Progress
        VSAREP_FAILOVER_PAUSED = 3  # Failover Paused
        VSAREP_FAILOVER_FAILED = 4  # Failover Failed
        VSAREP_FAILBACK_COMPLETE = 5  # Failback Complete
        VSAREP_FAILBACK_RUNNING = 6  # Failback In Progress
        VSAREP_FAILBACK_PAUSED = 7  # Failback Paused
        VSAREP_FAILBACK_FAILED = 8  # Failback Failed
        VSAREP_FAILBACK_PARTIAL = 9  # Partial Failback
        VSAREP_FAILOVER_PARTIAL = 10  # Partial Failover
        VSAREP_FAILOVER_SKIPPED = 11  # Failover Skipped
        VSAREP_FAILBACK_SKIPPED = 12  # Failback Skipped
        VSAREP_REVERT_FAILOVER_COMPLETE = 13  # Revert Failover Complete
        VSAREP_REVERT_FAILOVER_RUNNING = 14  # Revert Failover In Progress
        VSAREP_REVERT_FAILOVER_FAILED = 15  # Revert Failover Failed
        VSAREP_REVERT_FAILOVER_PAUSED = 16  # Revert Failover Paused
        VSAREP_FAILOVER_UNCHANGED = 1000  # FailOver unchanged

    def _get_snapshot_names(self, guid: str) -> [str]:
        """Returns a list of snapshot names from the specified guid"""
        snapshot_list = self._replication_monitor._dr_operation.get_snapshot_list(
            guid=guid, instance_id=int(self.instance.instance_id), timestamp_filter=False)
        return list(map(lambda x: x["name"], snapshot_list))

    def _check_status_after_failover(self):
        """Checks the sync status and failover status after failover"""

        # initializes the replication monitor again to fetch the latest status
        self._replication_monitor = self._init_replication_monitor()
        replication_info = self._fetch_replication_info()

        self.log.info("Checking sync status and failover status.")
        for replication_entry in replication_info:
            if self.VSAReplicationStatus(
                    int(replication_entry["status"])) != self.VSAReplicationStatus.VSAREP_DISABLED:
                self.log.error("Sync status should be \"Sync Disabled\".")
                raise Exception("Sync status validation failed.")

            failover_status = self.VSAFailoverStatus(
                int(replication_entry["FailoverStatus"]))
            if failover_status != self.VSAFailoverStatus.VSAREP_FAILOVER_COMPLETE:
                self.log.error(
                    "Failover status should be \"Failover Complete\".")
                raise Exception("Failover status validation failed.")

        self.log.info("Sync status and failover status validation succeed.")

    def _check_snapshots_after_planned_failover(self):
        """Checks snapshot names after planned failover"""
        self.log.info("Checking snapshots")
        replication_info = self._fetch_replication_info()

        for replication_entry in replication_info:
            src_guid = replication_entry["sourceGuid"]
            if "__GX_BACKUP__" not in self._get_snapshot_names(src_guid):
                self.log.error(
                    "A snapshot named \"__GX_BACKUP__\" should exist in the src machine %s.",
                    replication_entry["sourceName"])
                raise Exception("Snapshot validation on src machine failed.")

            dst_guid = replication_entry["destinationGuid"]
            if "__GX_FAILOVER__" not in self._get_snapshot_names(dst_guid):
                self.log.error(
                    "A snapshot named \"__GX_FAILOVER__\" should exist in the dst machine %s.",
                    replication_entry["destinationName"])
                raise Exception("Snapshot validation on dst machine failed.")

        self.log.info("Snapshot validation succeed.")

    def _check_snapshots_after_unplanned_failover(self):
        """Checks snapshot names after unplanned failover"""
        self.log.info("Checking snapshots")
        replication_info = self._fetch_replication_info()

        for replication_entry in replication_info:
            dst_guid = replication_entry["destinationGuid"]
            if "__GX_FAILOVER__" not in self._get_snapshot_names(dst_guid):
                self.log.error(
                    "A snapshot named \"__GX_FAILOVER__\" should exist in the dst machine %s.",
                    replication_entry["destinationName"])
                raise Exception("Snapshot validation on dst machine failed.")

        self.log.info("Snapshot validation succeed.")

    def _check_snapshots_after_point_in_time_failvoer(self):
        """Checks snapshot names after point-in-time failover"""
        # THe result should be as same as the one for unplanned failover
        self._check_snapshots_after_unplanned_failover()

    def _check_status_after_failback(self):
        """Checks the sync status and failover status after failback"""
        # initializes the replication monitor again to fetch the latest status
        self._replication_monitor = self._init_replication_monitor()
        replication_info = self._fetch_replication_info()

        self.log.info("Checking sync status and failover status.")
        for replication_entry in replication_info:
            if self.VSAReplicationStatus(
                    int(replication_entry["status"])) != self.VSAReplicationStatus.VSAREP_COMPLETE:
                self.log.error("Sync status should be \"In Sync\".")
                raise Exception("Sync status validation failed.")

            if self.VSAFailoverStatus(
                    int(replication_entry["FailoverStatus"])) != self.VSAFailoverStatus.VSAREP_NONE:
                self.log.error("Failover status should be \"None\".")
                raise Exception("Failover status validation failed.")

        self.log.info("Sync status and failover status validation succeed.")

    def _check_snapshots_after_failback(self):
        """Checks snapshot names after failback"""
        self.log.info("Checking snapshots")
        replication_info = self._fetch_replication_info()

        for replication_entry in replication_info:
            dst_guid = replication_entry["destinationGuid"]
            if "__GX_BACKUP__" not in self._get_snapshot_names(dst_guid):
                self.log.error(
                    "A snapshot named \"__GX_BACKUP__\" should exist in the dst machine %s.",
                    replication_entry["destinationName"])
                raise Exception("Snapshot validation on dst machine failed.")

        self.log.info("Snapshot validation succeed.")

    def _check_status_after_reverse_replication(self):
        """Checks the sync status and failover status after reversse replication"""
        # The result should be as same as the one for failover
        return self._check_status_after_failover()

    def _check_snapshots_after_reverse_replication(self):
        """Checks snapshot names after reverse replication"""
        self.log.info("Checking snapshots")
        replication_info = self._fetch_replication_info()

        for replication_entry in replication_info:
            src_guid = replication_entry["sourceGuid"]
            if "__GX_BACKUP__" not in self._get_snapshot_names(src_guid):
                self.log.error(
                    "A snapshot named \"__GX_BACKUP__\" should exist in the src machine %s.",
                    replication_entry["sourceName"])
                raise Exception("Snapshot validation on src machine failed.")

        self.log.info("Snapshot validation succeed.")

    def _run_operation(self, job_name: str, operation_func,
                       check_backup_job_id: bool):
        """Though replication monitor supports multiple replication ids in one
        job, sometimes it does not work well. For safety, run jobs one by one.
        """
        src_vm_full_list = self._src_vm_names

        for vm_name in src_vm_full_list:
            self._src_vm_names = [vm_name]
            self.tcinputs["vmName"] = vm_name
            self._replication_monitor = self._init_replication_monitor()

            super(
                CVTestCaseReplicationMonitor,
                self)._run_operation(
                    job_name=job_name,
                    operation_func=operation_func,
                    check_backup_job_id=check_backup_job_id)

        self._src_vm_names = src_vm_full_list

    def _do_planned_failover(self):
        """Does other validation in addition to the ones in the parent class."""
        super(CVTestCaseReplicationMonitor, self)._do_planned_failover()
        self._check_status_after_failover()

        if self._check_snapshots:
            self._check_snapshots_after_planned_failover()

    def _do_unplanned_failover(self):
        """Does other validation in addition to the ones in the parent class."""
        super(CVTestCaseReplicationMonitor, self)._do_unplanned_failover()
        self._check_status_after_failover()

        if self._check_snapshots:
            self._check_snapshots_after_unplanned_failover()

    def _do_point_in_time_failover(self):
        """Does other validation in addition to the ones in the parent class."""
        super(CVTestCaseReplicationMonitor, self)._do_point_in_time_failover()
        self._check_status_after_failover()

        if self._check_snapshots:
            self._check_snapshots_after_point_in_time_failvoer()

    def _do_failback(self):
        """Does other validation in addition to the ones in the parent class."""
        super(CVTestCaseReplicationMonitor, self)._do_failback()
        self._check_status_after_failback()

        if self._check_snapshots:
            self._check_snapshots_after_failback()

    def _do_undo_failover(self):
        """Does other validation in addition to the ones in the parent class."""
        super(CVTestCaseReplicationMonitor, self)._do_undo_failover()
        self._check_status_after_failback()

        if self._check_snapshots:
            self._check_snapshots_after_failback()

    def _schedule_reverse_replication(self):
        """Though replication monitor supports multiple replication ids in one
        job, sometimes it does not work well. For safety, run jobs one by one.
        """
        src_vm_full_list = self._src_vm_names

        for vm_name in src_vm_full_list:
            self._src_vm_names = [vm_name]
            self.tcinputs["vmName"] = vm_name
            self._replication_monitor = self._init_replication_monitor()

            super(
                CVTestCaseReplicationMonitor,
                self)._schedule_reverse_replication()

        self._src_vm_names = src_vm_full_list

    def _force_one_reverse_replication(self):
        """Does other validation in addition to the ones in the parent class."""
        super(CVTestCaseReplicationMonitor,
              self)._force_one_reverse_replication()
        self._check_status_after_reverse_replication()

        if self._check_snapshots:
            self._check_snapshots_after_reverse_replication()
