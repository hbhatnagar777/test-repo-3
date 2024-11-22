# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Copy Promotion from Command Center

Steps:
    0.  Previous run cleanup
    1.  Create entities.
        A.  Primary and secondary disk storage.
        B.  Server plan with 2 copies.
        C.  Disassociate secondary copy from autocopy schedule.
        D.  Backupset and subclient.
    C1. Immediate Copy Promotion
        2.  Initial Backups
            A.  four backup jobs (full, incremental, incremental, synthetic full).
            B.  Aux copy job
            C.  four backup jobs (full, incremental, incremental, synthetic full).
            D.  Validate aux copy status
        3.  Run backup job B1 and aux copy job A1
        4.  Submit immediate copy promotion request
        5.  Wait for copy promotion to complete
        6.  Once copy promotion is complete, verify the following,
            A.  secondary copy has been promoted,
            C.  jobs B1 and A1 should have been killed with proper JPR (OR) committed,
        7.  Run a restore job from promoted copy
    C2. Force conversion after x hours
        8.  Initial Backpus
            A.  four backup jobs (full, incremental, incremental, synthetic full).
            B.  Aux copy job
            C.  four backup jobs (full, incremental, incremental, synthetic full).
            D.  Validate aux copy status
        9.  Submit aux copy job A2
        10. Submit copy promotion request for conversion after x hours
        11. Submit backup job B2
        12. Wait for A2, Kill B2 and Wait for copy promotion to complete
        13. Once copy promotion is complete, verify the following,
            A.  secondary copy has been promoted,
        14. Run a restore job from promoted copy
    15.  Cleanup

TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class object.

    _init_tc()      --  Initial configuration for the test case.
    _init_props()   --  Initializes parameters and names required for testcase.
    setup()         --  setup function of this test case.

    _cleanup()      --  Delete entities before/after running testcase.

    _create_plan()  --  Configures a new plan and associates each copy to given storage.
    _create_entities--  Create entities for the test case.

    _run_backups()                      --  Run 4 backups to primary copy.
    _validate_aux_copy_status_for_job() --  Validates if the specified job auxCopyStatus is set to expected_status.
    _run_initial_backups()              --  Runs initial set of backup jobs and auxcopy job.

    _submit_copy_promotion()            --  Submit secondary copy for immediate copy promotion.
    _wait_for_copy_promotion()          --  Waits for copy promotion to complete.

    _post_copy_promotion_validations()  --  Validations to be performed after copy promotion finishes
    _case_1_validations()               --  Extra validations applicable for case 1: Immediate Copy Promotion
    _case_2_validations()               --  Extra validations applicable for case 2: Force conversion after x hours

    _case_1()                           --  Runs case 1: Immediate Copy Promotion
    _case_2()                           --  Runs case 2: Force conversion after x hours

    run()           --  run function of this test case.
    tear_down()     --  tear down function of this test case.


User should have the following permissions:
        [Execute Workflow] permission on [Execute Query] workflow


Sample Input:
"70611": {
    "ClientName": "Name of the client",
    "AgentName": "File System",
    "MediaAgentName": "Name of the media agent",
    *** OPTIONAL ***
    "dedupe_path": "LVM enabled path for Unix MediaAgent",
}


NOTE:
    1. LVM enabled path must be supplied for Unix MA. Dedupe paths will be created inside this folder.
"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector

from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, handle_testcase_exception

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """This is to validate Copy Promotion from Command Center."""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object.

            Properties to be initialized:
                name        (str)       --  name of this test case

                tcinputs    (dict)      --  test case inputs with input name as dict key
                                            and value as input type
        """
        super(TestCase, self).__init__()

        self.name = 'Copy Promotion from Command Center'
        self.tcinputs = {
            'ClientName': None,
            'AgentName': None,
            'MediaAgentName': None
        }

        self.browser = None
        self.admin_console: AdminConsole = None
        self.setup_phase_completed_successfully = None  # Just in case setup fails

        self.storage_helper: StorageMain = None
        self.plan_helper: PlanMain = None
        self.mm_helper: MMHelper = None

        self.media_agent_name = None
        self.client_machine = None

        self.content_path = None
        self.restore_path = None
        self.mount_path_template = None
        self.dedupe_path_template = None

        self.primary_storage_name = None
        self.secondary_Storage_name = None
        self.plan_name = None

        self.storage_policy = None
        self.primary_copy = None
        self.secondary_copy = None

        self.backupset_name = None
        self.subclient_name = None
        self.subclient = None

    def _init_tc(self):
        """Initial configuration for the test case."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )

            self.storage_helper = StorageMain(self.admin_console)
            self.plan_helper = PlanMain(self.admin_console)
            self.mm_helper = MMHelper(self)
        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    def _init_props(self):
        """Initializes parameters and names required for testcase."""
        self.media_agent_name = self.tcinputs['MediaAgentName']

        options_selector = OptionsSelector(self.commcell)
        str_id = str(self.id)

        media_agent_machine = options_selector.get_machine_object(self.media_agent_name)
        ma_drive = options_selector.get_drive(media_agent_machine, size=15*1024)

        self.client_machine = options_selector.get_machine_object(self.client.client_name)
        cl_drive = options_selector.get_drive(self.client_machine, size=15*1024)

        self.content_path = self.client_machine.join_path(cl_drive, 'Automation', str_id, 'CONTENT')
        self.restore_path = self.client_machine.join_path(cl_drive, 'Automation', str_id, 'RESTORE')
        self.mount_path_template = media_agent_machine.join_path(ma_drive, 'Automation', str_id, 'MP(%s)')

        if 'unix' in media_agent_machine.os_info.lower():
            if 'dedupe_path' not in self.tcinputs:
                self.log.error('LVM enabled dedup path must be supplied for Unix MA')
                raise ValueError('LVM enabled dedup path must be supplied for Unix MA')
            self.dedupe_path_template = media_agent_machine.join_path(self.tcinputs["dedupe_path"],
                                                                      'Automation', str_id, f"DDB(%s)")
        else:
            self.dedupe_path_template = media_agent_machine.join_path(ma_drive, 'Automation', str_id, f"DDB(%s)")

        self.primary_storage_name = '%s_disk-storage_ma-%s_primary' % (str_id, self.media_agent_name)
        self.secondary_Storage_name = '%s_disk-storage_ma-%s_secondary' % (str_id, self.media_agent_name)
        self.plan_name = '%s_plan_ma-%s' % (str_id, self.media_agent_name)

        self.backupset_name = '%s_backupset_cl-%s_ma-%s' % (str_id, self.client.client_name, self.media_agent_name)
        self.subclient_name = '%s_subclient_plan-%s' % (str_id, self.plan_name)

    def setup(self):
        """Setup function of this test case."""
        try:
            self._init_tc()
            self._init_props()
        except Exception as exp:
            self.setup_phase_completed_successfully = False
            self.log.error(str(exp))
        else:
            self.setup_phase_completed_successfully = True

    @test_step
    def _cleanup(self):
        """Delete entities before/after running testcase."""
        try:
            self.log.info(f"Deleting backupset {self.backupset_name}, if exits")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info(f"Deleted backupset {self.backupset_name}")

            plans_list = self.plan_helper.list_plans(company_name=None)

            self.log.info(f"Deleting plan {self.plan_name}, if exits")
            if self.plan_name in plans_list:
                self.log.info(f"Deleting plan {self.plan_name}")
                self.plan_helper.plan_name = {'server_plan': self.plan_name}
                self.plan_helper.delete_plans()
                self.log.info(f"Deleted plan {self.plan_name}")

            disk_storage_list = self.storage_helper.list_disk_storage()

            self.log.info(f"Deleting storage {self.primary_storage_name}, if exists")
            if self.primary_storage_name in disk_storage_list:
                self.log.info(f"Deleting storage {self.primary_storage_name}")
                self.storage_helper.delete_disk_storage(self.primary_storage_name)
                self.log.info(f"Deleted storage {self.primary_storage_name}")

            self.log.info(f"Deleting storage {self.secondary_Storage_name}, if exists")
            if self.secondary_Storage_name in disk_storage_list:
                self.log.info(f"Deleting storage {self.secondary_Storage_name}")
                self.storage_helper.delete_disk_storage(self.secondary_Storage_name)
                self.log.info(f"Deleted storage {self.secondary_Storage_name}")
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}') from exp

    def _create_plan(self, plan, pri_storage, sec_storage=None):
        """Configures a new plan and associates each copy to given storage.

            Args:
                plan        (str)   - Plan name
                pri_storage (str)   - Storage to be used for primary copy
                sec_storage (str)   - Storage to be used for secondary copy
        """
        self.plan_helper.plan_name = {'server_plan': plan}
        self.plan_helper.storage = {'pri_storage': pri_storage, 'pri_ret_period': '1', 'ret_unit': 'Day(s)'}
        if sec_storage is not None:
            self.plan_helper.storage.update({'sec_storage': sec_storage, 'sec_ret_period': '1'})
            self.plan_helper.sec_copy_name = 'Secondary'

        self.plan_helper.retention = None
        self.plan_helper.rpo_hours = None
        self.plan_helper.backup_data = None
        self.plan_helper.allow_override = None
        self.plan_helper.allowed_features = None
        self.plan_helper.backup_data = None
        self.plan_helper.backup_day = None
        self.plan_helper.backup_duration = None
        self.plan_helper.snapshot_options = None
        self.plan_helper.database_options = None

        self.plan_helper.add_plan()

    @test_step
    def _create_entities(self):
        """Create entities for the test case."""

        self.log.info(f"Creating disk storage")
        self.log.info(f"... Using storage name: {self.primary_storage_name}")
        self.log.info(f"... Using media agent: {self.media_agent_name}")
        self.log.info(f"... Using backup location: {self.mount_path_template % 'primary'}")
        self.storage_helper.add_disk_storage(
            disk_storage_name=self.primary_storage_name,
            media_agent=self.media_agent_name,
            backup_location=self.mount_path_template % 'primary',
            deduplication_db_location=[
                self.dedupe_path_template % '10',
                self.dedupe_path_template % '11',
                self.dedupe_path_template % '12',
                self.dedupe_path_template % '13',
            ]
        )

        self.log.info(f"Creating disk storage")
        self.log.info(f"... Using storage name: {self.secondary_Storage_name}")
        self.log.info(f"... Using media agent: {self.media_agent_name}")
        self.log.info(f"... Using backup location: {self.mount_path_template % 'secondary'}")
        self.storage_helper.add_disk_storage(
            disk_storage_name=self.secondary_Storage_name,
            media_agent=self.media_agent_name,
            backup_location=self.mount_path_template % 'secondary',
            deduplication_db_location=[
                self.dedupe_path_template % '20',
                self.dedupe_path_template % '21',
                self.dedupe_path_template % '22',
                self.dedupe_path_template % '23',
            ]
        )

        self.log.info(f"Creating server plan")
        self.log.info(f"... Using plan name: {self.plan_name}")
        self.log.info(f"... Using storage for primary copy: {self.primary_storage_name}")
        self.log.info(f"... Using storage for secondary copy: {self.secondary_Storage_name}")
        self._create_plan(self.plan_name, self.primary_storage_name, self.secondary_Storage_name)

        # disassociate secondary copy from autocopy schedule.
        self.storage_policy = self.commcell.plans.get(self.plan_name).storage_policy
        self.primary_copy = self.storage_policy.get_primary_copy()
        self.secondary_copy = self.storage_policy.get_secondary_copies()[0]
        self.mm_helper.remove_autocopy_schedule(self.storage_policy.storage_policy_name, self.secondary_copy.copy_name)

        self.log.info(f"Configuring Backupset {self.backupset_name}")
        self.mm_helper.configure_backupset(backupset_name=self.backupset_name, agent=self.agent)
        self.log.info(f"Configured Backupset {self.backupset_name}")

        self.log.info(f"Configuring Subclient {self.subclient_name}")
        self.subclient = self.mm_helper.configure_subclient(
            backupset_name=self.backupset_name,
            subclient_name=self.subclient_name,
            storage_policy_name=self.storage_policy.storage_policy_name,
            content_path=self.content_path,
            agent=self.agent,
        )
        self.log.info(f"Configured Subclient {self.subclient_name}")

    def _run_backups(self, size=1.0):
        """Run 4 backups to primary copy.

            Args:
                size        (int)   -   size of backup content to generate (default 0.1 GiB)

            Returns:
                list of Backup Job Instance
        """
        backup_jobs = []
        for backup_level in ['full', 'incremental', 'incremental', 'synthetic_full']:
            suffix = time.strftime("%H%M")
            self.log.info(f"Initiating {backup_level} backup job")
            self.log.info(f"Additional data, if required, will be generated with size: {size}, at location:"
                          f"{self.client_machine.join_path(self.content_path, suffix)}")
            backup_job = self.mm_helper.run_backup(self.client_machine,
                                                   self.subclient,
                                                   self.client_machine.join_path(self.content_path, suffix),
                                                   backup_type=backup_level,
                                                   size=size)
            backup_jobs.append(backup_job)
        self.log.info(f"{backup_level} backup job {backup_job.job_id} completed")
        return backup_jobs

    def _validate_aux_copy_status_for_job(self, job_id, expected_status=101):
        """Validates if the specified job auxCopyStatus is set to expected_status.

            Args:
                job_id          (int)   -- Job ID to check status for
                expected_status (int)   -- Aux copy status. 101 = To be copied, 100 = Available

            Raises:
                Exception       --  if auxCopyStatus does not match expected_status
        """
        query = f"""
SELECT  jobId, auxCopyStatus
FROM    JMJobDataStats WITH (NOLOCK)
WHERE   jobId = {job_id}
        AND archGrpCopyId = {self.storage_policy.get_secondary_copies()[0].copy_id} 
        AND auxCopyStatus = {expected_status}"""

        self.log.info(f"Query: {query}")
        result = self.mm_helper.execute_select_query(query)
        self.log.info(f"Result: {result}")
        if result[0][0] == '':
            if expected_status == 101:
                self.log.error("Expected job to show up as TO BE COPIED on secondary copy.")
                raise Exception("Expected job to show up as TO BE COPIED on secondary copy.")
            else:
                self.log.error("Expected job to show up as ALREADY COPIED on secondary copy.")
                raise Exception("Expected job to show up as ALREADY COPIED on secondary copy.")

    @test_step
    def _run_initial_backups(self):
        """Runs initial set of backup jobs and auxcopy job.
        """
        self.log.info("Running backup sequence")
        copied_jobs = self._run_backups()
        self.log.info("Finished running backup sequence")

        self.log.info('Running AuxCopy Job')
        aux_copy_job = self.storage_policy.run_aux_copy()
        self.log.info(f"Started AuxCopy job {aux_copy_job.job_id}")
        if not aux_copy_job.wait_for_completion():
            raise Exception(f'AuxCopy Job {aux_copy_job.job_id} Failed with JPR: {str(aux_copy_job.delay_reason)}')
        self.log.info('AuxCopy Job Completed: %s', aux_copy_job.job_id)

        self.log.info("Running backup sequence")
        to_be_copied_jobs = self._run_backups(size=1.0)
        self.log.info("Finished running backup sequence")

        self.log.info("Validating aux copy status")
        for job in copied_jobs:
            self._validate_aux_copy_status_for_job(job.job_id, expected_status=100)
        for job in to_be_copied_jobs:
            self._validate_aux_copy_status_for_job(job.job_id)

    @test_step
    def _submit_copy_promotion_request(self, sec_copy_name, synchronize_and_convert_time=-1):
        """Submit secondary copy for immediate copy promotion.

            Args:
                sec_copy_name               (str)   -   Name of copy
                synchronize_and_convert_time(int)   -   Time, -1 for immediate copy promotion (Convert immediately)
                                                        Uses UI default for unit. UI default would be 'Hour(s)'
        """
        self.log.info(f"Initiating copy promotion request: {sec_copy_name}, {synchronize_and_convert_time}")
        self.plan_helper.submit_copy_promotion_request(self.plan_name, sec_copy_name,
                                                       synchronize_and_convert_time=synchronize_and_convert_time)
        self.log.info("Helper method finished for submitting copy promotion request")

        self.log.info("Checking for toast message to confirm whether copy promotion request has been submitted")
        received_alert = self.admin_console.get_notification()
        expected_alert = self.admin_console.props.get("label.copyConversionRequest",
                                                      "The copy conversion request to primary submitted successfully.")
        if received_alert == expected_alert:
            self.log.info("Copy promotion request submitted successfully!")
        else:
            self.log.error("[SOFT ERROR] Failed to read notification for copy promotion request...")

    @test_step
    def _wait_for_copy_promotion(self, max_wait_secs=600):
        """Waits for copy promotion to complete.

            Args:
                max_wait_secs       (int)   --  Maximum wait time before failing copy promotion
        """
        start_time = time.time()
        elapsed_time = 0

        query = f"""
SELECT  extendedFlags & 1073741824
FROM    archGroupCopy WITH (NOLOCK)
WHERE   archGroupId = {self.storage_policy.storage_policy_id}"""

        while elapsed_time < max_wait_secs:
            self.log.info(f"Time elapsed: {elapsed_time}")
            self.log.info(f"Query: {query}")
            result = self.mm_helper.execute_select_query(query)
            self.log.info(f"Result: {result}")
            result = result[0]

            if result[0] == '0':
                self.log.info("Copy promotion finished.")
                break
            else:
                self.log.info("Copy promotion not finished yet.. Will recheck in 5 seconds.")
            time.sleep(5)
            elapsed_time = time.time() - start_time
        else:
            self.log.error(f"Copy promotion did not finish in {max_wait_secs} seconds. Raising error...")
            raise Exception(f"Copy promotion did not finish in {max_wait_secs} seconds.")

        self.log.info(f"Copy promotion finished after {elapsed_time} seconds")

    @test_step
    def _post_copy_promotion_validations(self, copy):
        """Once copy promotion is complete, verify the following,
            - secondary copy has been promoted,

            Args:
                copy            (StoragePolicyCopy) --  Object for Promoted copy
        """
        promoted_copy_validation = f"""
SELECT  defaultCopy
FROM    ArchGroup WITH (NOLOCK)
WHERE   id = {self.storage_policy.storage_policy_id}
        AND defaultCopy = {copy.copy_id}"""

        errors = ""

        self.log.info("************************ VALIDATION ************************")

        self.log.info("Validation: secondary copy has been promoted")
        self.log.info(f"Query: {promoted_copy_validation}")
        result = self.mm_helper.execute_select_query(promoted_copy_validation)
        self.log.info(f"Result: {result}")
        if result[0] == '':
            errors += f"[Copy {copy.copy_name} has not been promoted]  "
            self.log.error(f"Validation failed: Copy {copy.copy_name} has not been promoted")
        else:
            self.log.info(f"Validation Passed: Copy {copy.copy_name} has been promoted")

        self.log.info(f"Errors: {errors}")
        if errors:
            raise Exception(errors)
        else:
            self.log.info("All validations passed!")

    def _case_1_validations(self, b1_job, a1_job):
        """Once copy promotion is complete, verify the following,
            - jobs B1 and A1 should have been killed with proper JPR, or committed

            Args:
                b1_job      (Job)   --  Job instance for Backup job started just before immediate copy promotion
                a1_job      (Job)   --  Job instance for AuxCopy job started just before immediate copy promotion
        """
        errors = ""

        self.log.info("************************ VALIDATION ************************")

        self.log.info("Validation: jobs B1 and A1 should have been killed with proper JPR")
        b1_job.refresh()
        a1_job.refresh()
        reason = "Killing job for copy promotion."

        self.log.info(f"B1 job status [{b1_job.status}], A1 job status [{a1_job.status}]")
        self.log.info(f"B1 job JPR [{str(b1_job.delay_reason)}], A1 job JPR [{str(a1_job.delay_reason)}]")

        # --------------------------
        if b1_job.status == 'Committed' or b1_job.status == "Completed":
            self.log.error(f"[SOFT ERROR]: Backup job B1 {b1_job.status} before copy promotion...")
        else:
            if b1_job.status != "Killed":
                errors += f"[Backup job B1 not killed]  "
                self.log.error(f"Validation failed: Backup job B1 not killed!")
            else:
                self.log.info(f"Validation passed: Backup job B1 killed")
            if b1_job.status == "Killed" and reason not in str(b1_job.delay_reason):
                errors += f"[Backup job B1 JPR did not match]  "
                self.log.error(f"Validation failed: Backup job B1 JPR did not match!")
            else:
                self.log.info(f"Validation passed: Backup job B1 has proper JPR.")

        # --------------------------
        if a1_job.status == 'Committed' or a1_job.status == "Completed":
            self.log.error(f"[SOFT ERROR]: AuxCopy job A1 {a1_job.status} before copy promotion...")
        else:
            if a1_job.status != "Killed":
                errors += f"[AuxCopy job A1 not killed]  "
                self.log.error(f"Validation failed: AuxCopy job A1 not killed!")
            else:
                self.log.info(f"Validation passed: AuxCopy job A1 killed")
            if a1_job.status == "Killed" and reason not in str(a1_job.delay_reason):
                errors += f"[AuxCopy job A1 JPR did not match]  "
                self.log.error(f"Validation failed: AuxCopy job A1 JPR did not match!")
            else:
                self.log.info(f"Validation passed: AuxCopy job A1 has proper JPR.")

        self.log.info(f"Errors: {errors}")
        if errors:
            raise Exception(errors)
        else:
            self.log.info("All validations passed!")

    def _case_2_validations(self, b2_job):
        """Once backup job is submitted, verify the following,
            - job B2 has delay_reason 'copy under maintenance due to copy promotion'

            Args:
                b2_job      (Job)   --  Job instance for Backup job started just after copy promotion
        """
        errors = ""

        self.log.info("************************ VALIDATION ************************")

        self.log.info("Validation: job B2 should got to waiting with proper JPR")

        b2_job.refresh()
        wait_time_begin = time.time()   # in seconds
        while b2_job.status != "Waiting" and (time.time() - wait_time_begin) < 600:  # Wait for some time
            self.log.info("Job B2 is still running. Will wait for some time until it goes waiting...")
            time.sleep(30)
            b2_job.refresh()
            self.log.info(f"Elapsed time: {time.time() - wait_time_begin}")

        time.sleep(30)  # Some more delay because job may be in waiting state, but delay reason is still being updated
        b2_job.refresh()

        self.log.info(f"B2 job status [{b2_job.status}]")
        if b2_job.status != "Waiting":
            errors += f"[Job B2 not in waiting state]  "
            self.log.error(f"Validation failed: Job B2 not Waiting!")
        else:
            self.log.info(f"Validation passed: Job B2 waiting")

            reason = "The copy is currently under maintenance as the copy promotion request is in progress."
            self.log.info(f"B2 job JPR [{str(b2_job.delay_reason)}]")
            if b2_job.delay_reason is None or reason not in str(b2_job.delay_reason):
                errors += f"[JPR did not match for job B2]  "
                self.log.error(f"Validation failed: JPR did not match for Job B2!")
            else:
                self.log.info(f"Validation passed: Job B2 waiting with proper JPR.")

        self.log.info(f"Errors: {errors}")
        if errors:
            raise Exception(errors)
        else:
            self.log.info("All validations passed!")

    @test_step
    def _case_1(self):
        """ Runs case 1: Immediate Copy Promotion """
        try:
            self._run_initial_backups()

            # Submit Backup job B1 and Aux copy job A1
            self.log.info("Running Backup job B1...")
            b1_job = self.subclient.backup("full")
            self.log.info(f"Started backup job {b1_job.job_id}")
            self.log.info("Running AuxCopy job A1...")
            a1_job = self.storage_policy.run_aux_copy()
            self.log.info(f"Started auxcopy job {a1_job.job_id}")

            self._submit_copy_promotion_request(self.plan_helper.sec_copy_name)
            self._wait_for_copy_promotion()

            self.storage_policy.refresh()
            self.primary_copy.refresh()     # Now demoted
            self.secondary_copy.refresh()   # Now promoted

            self._post_copy_promotion_validations(self.secondary_copy)
            self._case_1_validations(b1_job, a1_job)

            restore_job = self.subclient.restore_out_of_place(self.client, self.restore_path, [self.content_path],
                                                              copy_precedence=1)
            self.log.info("restore job [%s] has started.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, str(restore_job.delay_reason))
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                str(restore_job.delay_reason)))
            self.log.info("restore job [%s] has completed.", restore_job.job_id)
        except Exception as exp:
            raise Exception(f"Case 1 failed with error: {exp}") from exp

    @test_step
    def _case_2(self):
        """ Runs case 2: Force conversion after x hours """
        try:
            self._run_initial_backups()

            self.log.info("Running AuxCopy job A2...")
            a2_job = self.storage_policy.run_aux_copy()
            self.log.info(f"Started auxcopy job {a2_job.job_id}")

            self._submit_copy_promotion_request('Primary', synchronize_and_convert_time=2)

            self.log.info("Running Backup job B2...")
            b2_job = self.subclient.backup("full")
            self.log.info(f"Started backup job {b2_job.job_id}")

            self._case_2_validations(b2_job)

            self.log.info("Waiting for aux copy job A2 to complete")
            if not a2_job.wait_for_completion():
                raise Exception(f'AuxCopy Job {a2_job.job_id} Failed with JPR: {str(a2_job.delay_reason)}')
            self.log.info('AuxCopy Job Completed: %s', a2_job.job_id)

            b2_job.kill(wait_for_job_to_kill=True)
            self._wait_for_copy_promotion()

            self.storage_policy.refresh()
            self.primary_copy.refresh()     # Now promoted
            self.secondary_copy.refresh()   # Now demoted

            self._post_copy_promotion_validations(self.primary_copy)

            restore_job = self.subclient.restore_out_of_place(self.client, self.restore_path, [self.content_path],
                                                              copy_precedence=1)
            self.log.info("restore job [%s] has started.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, str(restore_job.delay_reason))
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                str(restore_job.delay_reason)))
            self.log.info("restore job [%s] has completed.", restore_job.job_id)
        except Exception as exp:
            raise Exception(f"Case 2 failed with error: {exp}") from exp

    def run(self):
        """Run function of this test case."""

        try:
            if not self.setup_phase_completed_successfully:
                raise Exception("Setup phase not completed. Skipping run phase. Please check logs for error")

            self._cleanup()
            self._create_entities()

            self._case_1()
            self._case_2()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case."""
        try:
            self.log.info(f"Deleting content path created by test case: {self.content_path}, if exists")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info(f"Deleting content path created by test case: {self.content_path}")
                self.client_machine.remove_directory(self.content_path)
                self.log.info(f"Deleted content path created by test case: {self.content_path}")

            self.log.info(f"Deleting restore path created by test case: {self.restore_path}, if exists")
            if self.client_machine.check_directory_exists(self.restore_path):
                self.log.info(f"Deleting restore path created by test case: {self.restore_path}")
                self.client_machine.remove_directory(self.restore_path)
                self.log.info(f"Deleted restore path created by test case: {self.restore_path}")

            self._cleanup()
        except Exception as exp:
            self.log.error('Failed to tear down test case with error: %s', exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            self.browser.close()

