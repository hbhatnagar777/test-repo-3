# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Helper file for validating Operation window

OpValidate:
        __init__()                              -- Initialises OpValidate object

        validate()                              -- Validates an operation rule

        validate_full_data_management()         -- Validates Full data Management feature

        validate_non_full_data_management()     -- Validates Non full data Management feature

        validate_data_recovery()                -- Validates Data Recovery feature

        validate_synthetic_full()               -- Validates Synthetic full feature

        validate_aux_copy()                     -- Validates Aux copy feature

        validate_dr_backup()                    -- Validates Disaster Recovery feature

"""
from datetime import datetime
import time
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from Server.Scheduler import schedulerhelper, schedulerconstants
from Server.JobManager.jobmanager_helper import JobManager


class OpValidate:
    """Helper class to validate operation window"""

    def __init__(self, testcase, op_rule):
        """
        Initialize instance of the opvalidate class.
        Args:
            testcase     (obj)     --Testcase object

            op_rule (obj)          --Instance of operationWindowDetails class
        """
        self.op_rule = op_rule
        self.testcase = testcase
        self.log = logger.get_log()
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(testcase)
        self.job_run_types = ["immediate", "scheduled"]
        self.job_manager = JobManager(commcell=self.testcase.commcell)

    def _init_job_object_verify(self):
        """
        Verifies whether the job object honors the operation window or not
        Requires a testcase initialised subclient on which operations should be performed.
        Returns:
            Flag      (int)     --- 1 if job object honors operation window else 0
            subclient (object)  --- testcase initialised subclient
        Raises:
            Exception :
                if subclient is not initialised
                                or
                if operation rule entity level is client group and clientgroup object is not initialised in testcase
        """
        self.log.info("Initialising subclient object")
        flag = 0
        if self.testcase.subclient is None:
            self.log.info("No subclient object is present in the test case %s", self.testcase.id)
            raise Exception("No subclient object is present in the test case {0}".format(self.testcase.id))
        testcase_dict = {"commserv": self.testcase.commcell.commcell_id,
                         "client": self.testcase.client.client_id,
                         "agent": self.testcase.agent.agent_id,
                         "instance": self.testcase.instance.instance_id,
                         "backupset": self.testcase.backupset.backupset_id,
                         "subclient": self.testcase.subclient.subclient_id}

        op_rule_dict = {"commserv": self.op_rule.commcell_id,
                        "client": self.op_rule.client_id,
                        "agent": self.op_rule.agent_id,
                        "instance": self.op_rule.instance_id,
                        "backupset": self.op_rule.backupset_id,
                        "subclient": self.op_rule.subclient_id}
        self.log.info("Checking whether the subclient honors the operation window")
        op_rule_entity_level = self.op_rule.entity_level.lower()
        if op_rule_entity_level == "clientgroup":
            self.log.info("Checking whether the subclient belongs to the client group")
            if self.testcase.clientgroup is None:
                self.log.info("No clientgroup object is present in the test case %s", self.testcase.id)
                raise Exception("No clientgroup object is present in the test case {0}".format(self.testcase.id))
            if self.testcase.client.name in self.testcase.clientgroup.associated_clients \
                    and self.testcase.clientgroup.clientgroup_id == self.op_rule.clientgroup_id:
                self.log.info("Subclient does honor the operation window and belongs to clientgroup")
                flag = 1
            else:
                self.log.info("Subclient does not honor the operation window")
        elif op_rule_dict[op_rule_entity_level] == testcase_dict[op_rule_entity_level]:
            self.log.info("Subclient does honor the operation window")
            flag = 1
        else:
            self.log.info("Subclient does not honor the operation window")
        self.log.info("Initialised subclient object")
        return self.testcase.subclient, flag

    def validate(self, features=None):
        """if the features are None..It'll validate
            the initialised op_rule at it's entity level for all the features
        if features are provided then it'll validate for that
            set of features for the initialised op_rule at it's entity_level
        Args:
            features (List)  --- List of features that need to be verified
        """
        if features is None:
            features = self.op_rule.operations

        for feature in features:
            if feature in self.op_rule.operations:
                getattr(self, "validate_"+feature.lower())()
            self.log.info("waiting for 60 seconds before starting next time to handle intermittent issue")
            time.sleep(60)

    def _verify_schedule_job(self, subclient_obj, backup_type, flag, operations):
        """
        Verify scheduled backup job for full ,incremental and synthfull
        Args:
            subclient_obj (Object) -- Subclient instance where backup job to be run

            backup_type (str) -- backup type to run (full/incremental/synth_full)

            flag (int)          --flag is used to know whether the Entity created in
                                testcase is same as our entity object

            job  (object)       --job object to check status and waiting for the job to complete

            operations (List)   --List of operations after removing the feature that needs to be validated
        """
        self.log.info("scheduling {0} backup for subclient".format(backup_type))
        client_machine_obj = Machine(subclient_obj.properties['subClientEntity']['clientName'], self.testcase.commcell)
        current_local_time = client_machine_obj.current_time()
        new_start_date, new_start_time = self._schedule_creator.add_minutes_to_datetime(current_local_time)
        self.log.info(f"new start time:{new_start_date} {new_start_time}")
        _schedule_obj = self._schedule_creator.create_schedule('subclient_backup',
                                                               schedule_pattern={
                                                                   'freq_type': 'One_time',
                                                                   'active_start_date': new_start_date,
                                                                   'active_start_time': new_start_time,
                                                                   'time_zone': 'UTC'},
                                                               wait=False,
                                                               subclient=subclient_obj,
                                                               backup_type=backup_type)
        scheduler_helper_obj = schedulerhelper.SchedulerHelper(_schedule_obj, self.testcase.commcell)
        jobs = scheduler_helper_obj.check_job_for_taskid(retry_count=10)
        if not jobs and self.op_rule.do_not_submit_job:
            self.log.info('Job is not submitted when do not submit option is selected, expected behavior')
        elif not jobs and not self.op_rule.do_not_submit_job:
            raise Exception("Job did not get triggered for the Schedule {0}".format(
                _schedule_obj.schedule_id))
        else:
            self._job_verify(flag, jobs[0], operations)

    def validate_full_data_management(self):
        """Validates Full Data Management feature"""
        _backup_type = "full"
        operations = list(self.op_rule.operations)
        if "FULL_DATA_MANAGEMENT" in operations:
            operations.remove("FULL_DATA_MANAGEMENT")
            self.log.info("Full Data Management feature do honor operation window")
        else:
            self.log.info("Full Data Management feature does not honor operation window")

        _subclient_obj, flag = self._init_job_object_verify()

        for job_run_type in self.job_run_types:
            if job_run_type == "scheduled":
                self.log.info("Validating Full Data Management feature for scheduled backup".center(50, "*"))
                self._verify_schedule_job(_subclient_obj, _backup_type, flag, operations)
            else:
                self.log.info("Validating Full Data Management feature for immediate backup".center(50, "*"))
                self.log.info("Starting immediate full backup job")
                try:
                    job_obj = _subclient_obj.backup(_backup_type)
                except Exception as exp:
                    raise Exception("Job is not submitted for immediate backup job. exception:{0}, "
                                    "active jobs:{1}".format(exp, self.testcase.commcell.job_controller.active_jobs()))
                self._job_verify(flag, job_obj, operations)

        self.log.info("Validated Full Data Management feature".center(50, "*"))

    def validate_non_full_data_management(self):
        """Validates Non Full Data Management feature"""
        _backup_type = "incremental"
        operations = list(self.op_rule.operations)
        if "NON_FULL_DATA_MANAGEMENT" in operations:
            operations.remove("NON_FULL_DATA_MANAGEMENT")
            self.log.info("Non Full Data Management feature do honor operation window")
        else:
            self.log.info("Non Full Data Management feature does not honor operation window")

        _subclient_obj, flag = self._init_job_object_verify()

        for job_run_type in self.job_run_types:
            if job_run_type == "scheduled":
                self.log.info("Validating Non Full Data Management feature for scheduled backup".center(50, "*"))
                self._verify_schedule_job(_subclient_obj, _backup_type, flag, operations)
            else:
                self.log.info("Validating Non Full Data Management feature for immediate backup".center(50, "*"))
                self.log.info("Starting immediate {0} backup job".format(_backup_type))
                try:
                    job_obj = _subclient_obj.backup(_backup_type)
                except Exception as exp:
                    raise Exception("Job is not submitted for immediate backup job. exception:{0}, "
                                    "active jobs:{1}".format(exp, self.testcase.commcell.job_controller.active_jobs()))
                self.log.info("Successfully started {0} backup job with job id {1}".format(_backup_type,
                                                                                              job_obj.job_id))
                self._job_verify(flag, job_obj, operations)

        self.log.info("Validated Non Full Data Management feature".center(50, "*"))

    def validate_data_recovery(self):
        """Validates Data Recovery feature"""
        operations = list(self.op_rule.operations)
        if "DATA_RECOVERY" in operations:
            operations.remove("DATA_RECOVERY")
            self.log.info("Data Recovery feature do honor operation window")
        else:
            self.log.info("Data Recovery feature does not honor operation window")

        _subclient_obj, flag = self._init_job_object_verify()

        if self.op_rule.entity_level == "backupset":
            flag = 0
        if self.op_rule.entity_level == "subclient":
            flag = 0

        for job_run_type in self.job_run_types:
            if job_run_type == "scheduled":
                self.log.info("Validating Data Recovery feature for scheduled backup".center(50, "*"))
                self.log.info("scheduling in place restore job for subclient")
                _schedule_obj = self._schedule_creator.create_schedule('subclient_restore_in_place',
                                                       schedule_pattern={
                                                           'freq_type': 'One_time',
                                                           'active_start_date': self._schedule_creator.
                                                       add_minutes_to_datetime()[0],
                                                           'active_start_time': self._schedule_creator.
                                                       add_minutes_to_datetime()[1],
                                                           'time_zone': 'UTC'},
                                                       wait=False,
                                                       subclient=_subclient_obj,
                                                       paths=_subclient_obj.content)
                scheduler_helper_obj = schedulerhelper.SchedulerHelper(_schedule_obj, self.testcase.commcell)
                jobs = scheduler_helper_obj.check_job_for_taskid(retry_count=10)
                if not jobs and self.op_rule.do_not_submit_job:
                    self.log.info('Job is not submitted when do not submit option is selected, expected behavior')
                elif not jobs and not self.op_rule.do_not_submit_job:
                    raise Exception("Job did not get triggered for the Schedule {0}".format(
                        _schedule_obj.schedule_id))
                else:
                    self._job_verify(flag, jobs[0], operations)
            else:
                self.log.info("Validating Data Recovery feature for immediate backup".center(50, "*"))
                self.log.info("Starting immediate in place restore job")
                try:
                    job_obj = _subclient_obj.restore_in_place(_subclient_obj.content)
                except Exception as exp:
                    raise Exception("Job is not submitted for immediate backup job. exception:{0}, "
                                    "active jobs:{1}".format(exp, self.testcase.commcell.job_controller.active_jobs()))
                self.log.info("Successfully started in place restore job with job id %s", job_obj.job_id)
                self._job_verify(flag, job_obj, operations)

        self.log.info("Validated Data Recovery feature".center(50, "*"))

    def validate_synthetic_full(self):
        """Validates Synthetic full feature feature"""
        _backup_type = "Synthetic_full"
        self.log.info("Validating Synthetic Full feature".center(50, "*"))
        operations = list(self.op_rule.operations)
        if "SYNTHETIC_FULL" in operations:
            operations.remove("SYNTHETIC_FULL")
            self.log.info("Synthetic Full  feature do honor operation window")
        else:
            self.log.info("Synthetic Full feature does not honor operation window")

        _subclient_obj, flag = self._init_job_object_verify()
        if self.op_rule.entity_level.lower() == "commserv":
            flag = 1
        else:
            flag = 0

        for job_run_type in self.job_run_types:
            if job_run_type == "scheduled":
                self.log.info("Validating Synthetic Full feature feature for scheduled backup".center(50, "*"))
                old_operations = list(self.op_rule.operations)
                allow_non_full = list(self.op_rule.operations)
                allow_non_full.remove("NON_FULL_DATA_MANAGEMENT")
                self.log.info("Modifying the operation window to allow incremental backup")
                self.op_rule.operations = allow_non_full
                self.log.info("successfully modified the operation window")
                time.sleep(30)
                self.log.info("running incremental backup before synth_full")
                job_obj = _subclient_obj.backup(backup_level="incremental")
                self.log.info("waiting for incremental backup job {0} to complete".format(job_obj.job_id))
                job_obj.wait_for_completion(timeout=300)
                self.log.info("Backup job {0} Completed".format(job_obj.job_id))
                self.log.info("Modifying the operation window to it's initial state")
                self.op_rule.operations = old_operations
                time.sleep(30)

                self._verify_schedule_job(_subclient_obj, _backup_type, flag, operations)
            else:
                self.log.info("Validating Synthetic Full feature feature for immediate backup".center(50, "*"))
                self.log.info("Starting immediate Synthetic_full job")
                try:
                    job_obj = _subclient_obj.backup(backup_level=_backup_type)
                except Exception as exp:
                    raise Exception("Job is not submitted for immediate backup job. exception:{0}, "
                                    "active jobs:{1}".format(exp, self.testcase.commcell.job_controller.active_jobs()))
                self.log.info("Successfully started Synthetic_full job with job id %s", job_obj.job_id)
                self._job_verify(flag, job_obj, operations)

        self.log.info("Validated Synthetic Full feature".center(50, "*"))

    def validate_aux_copy(self):
        """Validates Aux copy feature feature"""
        from cvpysdk.policies.storage_policies import StoragePolicies
        self.log.info("Validating Aux Copy feature".center(50, "*"))
        operations = list(self.op_rule.operations)
        if "AUX_COPY" in operations:
            operations.remove("AUX_COPY")
            self.log.info("Aux Copy feature do honor operation window")
        else:
            self.log.info("Aux Copy feature does not honor operation window")
        job_object, flag = self._init_job_object_verify()
        self.log.info("running incremental backup to run the aux copy job on that data.")
        job_obj = job_object.backup(backup_level="incremental")
        self.log.info("waiting for incremental backup job {0} to complete".format(job_obj.job_id))
        job_obj.wait_for_completion(timeout=300)
        self.log.info("Backup job {0} Completed".format(job_obj.job_id))
        sec_copy_name = "selective_copy_" + job_object.storage_policy
        job_object = StoragePolicies(self.testcase.commcell).get(job_object.storage_policy)
        lib_name = job_object.storage_policy_advanced_properties['policies'][0]['copies'][0]['library']['libraryName']
        ma_name = job_object.storage_policy_advanced_properties['policies'][0]['copies'][0]['mediaAgent'][
            'mediaAgentName']
        # aux copy job on a sec copy runs with a schedule and on demand aux copy job shows the error that
        # there is nothing to copy.
        # to avoid this we are creating a selective copy and an auxiliary copy job can be run on demand.
        job_object.create_selective_copy(
            copy_name=sec_copy_name,
            library_name=lib_name,
            media_agent_name=ma_name,
            sel_freq="monthly",
            first_or_last_full="FirstFull",
            backups_from=datetime.now().strftime("%Y-%m-%d")
        )
        self.log.info("Starting a aux copy job")
        if self.op_rule.do_not_submit_job:
            _schedule_obj = None
            _schedule_obj = job_object.run_aux_copy(
                sec_copy_name,
                schedule_pattern={
                    "freq_type": "One_time",
                    "active_start_date": self._schedule_creator.add_minutes_to_datetime()[0],
                    "active_start_time": self._schedule_creator.add_minutes_to_datetime()[1],
                    "time_zone": "UTC",
                }
            )
            scheduler_helper_obj = schedulerhelper.SchedulerHelper(_schedule_obj, self.testcase.commcell)
            jobs = scheduler_helper_obj.check_job_for_taskid(retry_count=10)
            if not jobs:
                self.log.info('Job is not submitted when do not submit option is selected, expected behavior')
            else:
                jobs[0].kill(wait_for_job_to_kill=True)
                raise Exception("Job is submitted with job id={0}"
                                " when do not submit job is enabled".format(job_obj.job_id))
        else:
            job = job_object.run_aux_copy(sec_copy_name)
            self.log.info("Successfully started an aux copy job with job id %s", job.job_id)
            self._job_verify(flag, job, operations)
        self.log.info("Validated Aux Copy feature".center(50, "*"))

    def validate_dr_backup(self):
        """Validates Disaster Recovery feature feature"""
        self.log.info("Validating Disaster Recovery feature".center(50, "*"))
        operations = list(self.op_rule.operations)
        if "DR_BACKUP" in operations:
            operations.remove("DR_BACKUP")
            self.log.info("Disaster Recovery feature do honor operation window")
        else:
            self.log.info("Disaster Recovery feature does not honor operation window")
        job_object = self.testcase.commcell.disasterrecovery
        if self.op_rule.entity_level.lower() == "commserv":
            flag = 1
        else:
            flag = 0
        self.log.info("Starting a Disaster Recovery Backup job")

        # do not submit option is not honoured for immediate backups
        job = job_object.disaster_recovery_backup()
        self.log.info("Successfully started Disaster Recovery "
                      "Backup job with job id %s", job.job_id)
        self._job_verify(flag, job, operations)
        self.log.info("Validated Disaster Recovery feature".center(50, "*"))

    def validate_clients_in_different_timezones(self, flag1, flag2):
        """Validates Operation Window features for clients in different timezones"""
        self.log.info("Validating multiple timezones feature".center(50, "*"))
        operations, tmp_operations = list(self.op_rule.operations), list(self.op_rule.operations)
        if "FULL_DATA_MANAGEMENT" in operations:
            operations.remove("FULL_DATA_MANAGEMENT")
            self.log.info("Full Data Management feature do honor operation window")
        else:
            self.log.info("Full Data Management feature does not honor operation window")

        try:
            job_obj1 = self.testcase.subclient1.backup("full")
            self.log.info(
                f"Started immediate full backup job {job_obj1.job_id} on {self.testcase.subclient1.subclient_name}")
        except Exception as exp:
            raise Exception("Job is not submitted for immediate backup job. exception:{0}, "
                            "active jobs:{1}".format(exp, self.testcase.commcell.job_controller.active_jobs()))
        self.log.info(f"flag1 : {flag1}")
        self._job_verify(flag1, job_obj1, operations)
        self.op_rule.operations, operations = tmp_operations, tmp_operations
        if "FULL_DATA_MANAGEMENT" in operations:
            operations.remove("FULL_DATA_MANAGEMENT")
            self.log.info("Full Data Management feature do honor operation window")
        else:
            self.log.info("Full Data Management feature does not honor operation window")
        try:
            job_obj2 = self.testcase.subclient2.backup("full")
            self.log.info(
                f"Started immediate full backup job {job_obj2.job_id} on {self.testcase.subclient2.subclient_name}")
        except Exception as exp:
            raise Exception("Job is not submitted for immediate backup job. exception:{0}, "
                            "active jobs:{1}".format(exp, self.testcase.commcell.job_controller.active_jobs()))
        self.log.info(f"flag2 : {flag2}")
        self._job_verify(flag2, job_obj2, operations)


    def _job_verify(self, flag, job, operations):
        """
        Verifying whether job is going according to the rules of operation window
        Args:
            flag (int)          --flag is used to know whether the Enitiy created in
                                testcase is same as our entity object

            job  (object)       --job object to check status and waiting for the job to complete

            operations (List)   --List of operations after removing the feature that needs to be validated
        """
        self.job_manager.job = job
        # operations == self.op_rule.operations for individual validations
        if flag == 0 or operations == self.op_rule.operations:
            self.log.info("%s should be Running", job.job_type)
            self.job_manager.wait_for_state(expected_state=['running', 'completed'],
                                            time_limit=1,
                                            hardcheck=False,
                                            fetch_job_state_in_validate=False)
            if job.status.lower() == "queued":
                self.log.error("Failed to run %s with error: %s", job.job_type, job.delay_reason)
                raise Exception(
                    "Failed to run {0} with error: {1}".format(job.job_type, job.delay_reason)
                )
            self.log.info("Success:%s is running", job.job_type)
            self.log.info("Waiting for the %s job to complete", job.job_type)
            job.wait_for_completion(timeout=300)
            self.log.info("Completed the %s job", job.job_type)
        else:
            self.log.info("%s should be queued", job.job_type)
            self.job_manager.wait_for_state(expected_state='queued',
                                            time_limit=1,
                                            hardcheck=False,
                                            fetch_job_state_in_validate=False)
            if not job.status.lower() == "queued":
                self.log.error("Failed to Queue %s with error: %s", job.job_type, job.delay_reason)
                job.kill(wait_for_job_to_kill=True)
                raise Exception(
                    "Failed to Queue {0} with error: {1}".format(job.job_type, job.delay_reason)
                )
            self.log.info("Success:%s is queued", job.job_type)
            old_operations = list(self.op_rule.operations)
            self.log.info("Modifying the operation window to check if the job will be resumed")
            self.op_rule.operations = operations
            self.log.info("successfully modified the operation window")
            self.log.info("%s should be resumed", job.job_type)
            self.job_manager.wait_for_state(expected_state=['running', 'completed'],
                                            time_limit=5,
                                            hardcheck=False,
                                            fetch_job_state_in_validate=False)
            if job.status == "Queued":
                self.log.error("Failed to run %s with error: %s", job.job_type, job.delay_reason)
                raise Exception(
                    "Failed to run {0} with error: {1}".format(job.job_type, job.delay_reason)
                )
            self.log.info("Success : %s is resumed", job.job_type)
            self.log.info("Waiting for the %s job to complete", job.job_type)
            job.wait_for_completion(timeout=300)
            self.log.info("Completed the %s job", job.job_type)
            self.log.info("Modifying the operation window to it's initial state")
            self.op_rule.operations = old_operations
            self.log.info("Successfully modified the operation window")
