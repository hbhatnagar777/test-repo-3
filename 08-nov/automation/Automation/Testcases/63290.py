# coding=utf-8
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    setup_environment() -- configures entities based on inputs

    get_active_files_store() -- gets active files DDB store id

    stop_cvd()  - stops cvd on MA

    start_cvd() - starts cvd on MA

    cleanup()   --  cleanups all created entities

    run_backup()    -- runs backup need for the case

    run_dv2_job()   -- runs DV2 job

    validate_dv2_phase() -- validates the dv2 after auto resume

    validate_status() -- validates job status

    wait_for_jobs() -- wait for jobs to complete

    check_bad_chunks() -- check if there are bad chunks

    validate_data_verification_status() -- check backup job DV status


Note: if no predefined entities provided in input, we will create them.
if need to use predefined entities like Library or SP. add them to input json

Sample JSON: values under [] are optional
"63290": {
            "ClientName": "client name",
            "AgentName": "File System",
            "MediaAgentName": "ma name",
            [ Optional parameters :
            "DDBPath": "E:\\DDBs\\dv2tests\\0", - path to be used for creating ddb during pool creation.For linux specify LVM path
            "MountPath": "E:\\Libraries\\dv2tests_defragmp", - mount path to use to create storage pool
            or
            "PlanName": "Existing Plan Name"           - existing plan to use
            "PoolName": "Existing Pool"
            ]
        }
design:

    Cleanup previous run environment
    Create test environment
    reduce the DV2 job restart time to 2 min
    Run backup B1 with 5GB data"
    Wait for backup job to complete
    Run 5 incremental jobs : 1GB
    Wait for backup job to complete
    Run Incr DV2 job
    After phase 1 started restart the MA services
    Check the job status and wait for it get auto resume
    Wait for job to get complete
    After phase 2 started restart the MA services
    Wait for job to get complete
    Check if any chunks marked bad
    Validate data verification jobs
    Revert the DV2 job restart time to default one
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.machine import Machine
from Server.JobManager.jobmanagement_helper import JobManagementHelper
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Restart MA services During Phase 1 and Phase 2 DV2 job"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }
        self.pool_name = None
        self.plan_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.mount_path = None
        self.agent_name = None
        self.ddb_path = None
        self.bkpset_obj = None
        self.subclient = None
        self.client = None
        self.primary_copy = None
        self.existing_entities = False
        self.ma_name = None
        self.client_name = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_plan = False
        self.client_machine_obj = False
        self.ma_machine_obj = False
        self.client_drive = False
        self.ma_drive = False
        self.media_agent_obj = None
        self.mmhelper_obj = None
        self.plan = None
        self.option_obj = None
        self.jm_helper = None
        self.status = constants.PASSED
        self.default_settings = None

    def setup(self):
        """
        Setup function of this test case. initialises entity names if provided in tcinputs otherwise assigns new names
        """
        self.option_obj = OptionsSelector(self.commcell)
        self.mmhelper_obj = MMHelper(self)
        self.jm_helper = JobManagementHelper(self.commcell)
        suffix = round(time.time())
        self.mount_path = self.tcinputs.get("MountPath")
        self.ma_name = self.tcinputs.get("MediaAgentName")
        self.ddb_path = self.tcinputs.get("DDBPath")
        self.client_name = self.tcinputs.get("ClientName")
        self.plan_name = self.tcinputs.get("PlanName")
        self.pool_name = self.tcinputs.get("PoolName")
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)
        self.client_machine_obj = Machine(self.client)

        if self.tcinputs.get("PlanName") and self.tcinputs.get("PoolName"):
            self.is_user_defined_plan = True
            self.existing_entities = True
        else:
            self.plan_name = f"PLAN_{self.id}_{self.ma_name}"
            self.pool_name = f"STORAGEPOOL_{self.id}_{self.ma_name}"
            self.existing_entities = False

        if not self.existing_entities:
            if self.tcinputs.get("MountPath"):
                self.is_user_defined_mp = True
            if self.tcinputs.get("DDBPath"):
                self.is_user_defined_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        self.client_drive = self.option_obj.get_drive(self.client_machine_obj, 25 * 1024)
        if not self.is_user_defined_mp and not self.existing_entities:
            self.ma_drive = self.option_obj.get_drive(self.ma_machine_obj, 25 * 1024)

        if not self.existing_entities:
            if self.is_user_defined_mp:
                self.mount_path = self.ma_machine_obj.join_path(self.tcinputs.get("MountPath"), f"TC_{self.id}",
                                                                f"LIB_{suffix}")
                self.log.info(f"Using user provided mount path {self.mount_path}")
            else:
                self.mount_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"LIB_{suffix}")
            if self.is_user_defined_dedup:
                self.ddb_path = self.ma_machine_obj.join_path(self.tcinputs.get("DDBPath"), f"TC_{self.id}",
                                                              f"DDB_{suffix}")
                self.log.info(f"Using user provided dedup path {self.ddb_path}")
            else:
                self.ddb_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"DDB_{suffix}")

        self.backupset_name = f"BKPSET_{self.id}_{self.client_name}"
        self.subclient_name = f"SUBC_{self.id}_{self.client_name}"
        self.content_path = self.client_machine_obj.join_path(self.client_drive, f"TC_{self.id}_CONTENT")

    def setup_environment(self):
        """ configures all entities based tcinputs. If Plan, Pool is provided TC will use those,
        TC will use these entities and run the case """
        self.log.info("setting up environment...")
        # Create pool if pool name is not specified
        if not self.is_user_defined_plan:
            if not self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info(f"Creating Storage Pool - {self.pool_name}")
                self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                                self.ma_name, [self.ma_name] * 2,
                                                [self.ddb_path, self.ddb_path])
            else:
                self.log.info(f"Storage Pool already exists - {self.pool_name}")
            # Create Plan if plan name is not specified using the pool name specified in json or pool created
            if not self.commcell.plans.has_plan(self.plan_name):
                self.log.info(f"Creating the Plan [{self.plan_name}]")
                self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
                self.log.info(f"Plan [{self.plan_name}] created")
            else:
                self.log.info(f"Plan already exists - {self.plan_name}")
                self.plan = self.commcell.plans.get(self.plan_name)
        else:
            self.log.info(f"Using user specified Plan {self.plan_name}")
            self.plan = self.commcell.plans.get(self.plan_name)

        self.primary_copy = self.plan.storage_policy.get_copy('Primary')
        self.plan.schedule_policies['data'].disable()
        # Create a backupset
        self.log.info(f"Configuring Backupset - {self.backupset_name}")
        self.bkpset_obj = self.mmhelper_obj.configure_backupset(self.backupset_name)
        # Create subclient
        self.subclient = self.bkpset_obj.subclients.add(self.subclient_name)
        self.subclient.plan = [self.plan, [self.content_path]]

        # reduce the DV2 job restart time to 2 min
        current_setting = self.jm_helper.get_restart_setting("Data Verification")
        self.default_settings = current_setting.copy()
        current_setting['restartIntervalInMinutes'] = 2
        self.log.info("Settings DV2 jobs Restart time to 2 mins")
        self.jm_helper.modify_restart_settings([current_setting])

    def cleanup(self):
        """
        performs cleanup of all entities only if created by case.
        if case is using existing entities, cleanup is skipped.
        """
        try:
            if self.client_machine_obj.check_directory_exists(self.content_path):
                self.log.info(f"Deleting already existing content directory {self.content_path}")
                self.client_machine_obj.remove_directory(self.content_path)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)
            if not self.existing_entities:
                if self.commcell.plans.has_plan(self.plan_name):
                    self.log.info("Reassociating all subclients to None")
                    self.plan.storage_policy.reassociate_all_subclients()
                    self.log.info(f"Deleting plan {self.plan_name}")
                    self.commcell.plans.delete(self.plan_name)
                if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                    self.log.info(f"Deleting Storage Pool {self.pool_name}")
                    self.commcell.storage_pools.delete(self.pool_name)
                self.log.info("Refresh libraries")
                self.commcell.disk_libraries.refresh()
                self.log.info("Refresh Storage Pools")
                self.commcell.storage_pools.refresh()
                self.log.info("Refresh Plans")
                self.commcell.plans.refresh()
            else:
                if self.plan:
                    self.plan.schedule_policies['data'].enable()
                self.log.info("Not running cleanup of pools and plans as case is using existing entities.")
        except Exception as e:
            self.log.warning(f"Something went wrong while cleanup! Exception occurred - [{e}]")

    def run_backup(self, backup_type="FULL", size=1.0):
        """
        this function runs backup by generating new content to get unique blocks for dedupe backups.
        if scalefactor is set in tcinput, creates factor times of backup data

        Args:
            backup_type (str): type of backup to run
                Default - FULL

            size (int): size of backup content to generate
                Default - 1 GB

        Returns:
        (object) -- returns job object to backup job
        """
        # add content
        additional_content = self.client_machine_obj.join_path(self.content_path, 'generated_content')
        if self.client_machine_obj.check_directory_exists(additional_content):
            self.client_machine_obj.remove_directory(additional_content)
        self.mmhelper_obj.create_uncompressable_data(self.client_name, additional_content, size)

        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        self.wait_for_jobs([job])
        self.log.info("Backup job completed.")
        return job

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.pool_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def run_dv2_job(self, store):
        """
        Runs DV2 job with type and option selected and waits for job to complete
        Args:
            store (object) - object of the store to run DV2 job on
        Returns:
             (object) - completed DV2 job object
        """
        self.log.info(f"Running Complete FULL DV2 job on store {store.store_id}")
        job = store.run_ddb_verification(incremental_verification=False, quick_verification=False,
                                         max_streams=3)
        self.log.info(f"DV2 job: {job.job_id}")
        return job

    def validate_dv2_phase(self, job, phase):
        """ Verify auto-resume after service restart in mid-Phase
        Args:
            job(object) : dv2 job object
            phase(str)  : dv2 phase
        """
        self.log.info(f"Verify auto-resume after service restart in Phase {phase}")
        exit_condition = 900
        # Waiting for max 30 minutes
        while job.phase.lower() != phase.lower() and exit_condition > 0:
            self.log.info(f"Job is in {job.phase} phase. Expected Phase = {phase}")
            time.sleep(2)
            exit_condition -= 1

        if job.phase.lower() == phase.lower():
            self.log.info(f"Reached Job Phase : {phase}")
            self.stop_cvd()
            self.validate_status(["pending", "waiting"], job)
            self.start_cvd()
            self.validate_status(["running", "completed"], job)
        else:
            self.log.error("Even after waiting for 30 minutes, Job is not in [%s] phase. Current Phase = [%s]",
                           phase, job.phase)
            raise CVTestStepFailure("Even after waiting for 30 minutes, Job is not in [%s] phase. Current Phase = [%s]",
                                    phase, job.phase)

    def stop_cvd(self):
        """ Killing cvd on Media agent"""
        try:
            self.log.info("Killing CVD process on Mediaagent..")
            self.ma_machine_obj.kill_process('cvd')
        except Exception:
            self.log.info("Entered exception block as Expected. CVD service Killed.")
        self.log.info("Killing CVD process on mediaagent is successfull..")

    def start_cvd(self):
        """ Restart services on MA"""
        self.log.info("Restarting media agent..")
        try:
            self.ma_machine_obj.start_all_cv_services()
        except Exception:
            self.log.info("Entered exception block as Expected. CVD service Started.")
        self.log.info("Sleeping for 1 minute after restarting cvd on media agent..")
        time.sleep(60)

    def validate_status(self, status, job):
        """ Validate job status
        Args:
            status(list) : job status to verify
            job(object) : dv2 job object
        """
        self.log.info(f"DV2 Job Current Phase : {job.phase}, Status : {job.status}")
        exit_condition = 1200  # wait for max 30 minutes
        while job.status.lower() not in status and exit_condition > 0:
            self.log.info(f"Expected job status: [{status}], Current status - [{job.status}]")
            time.sleep(1)
            exit_condition -= 1
        if job.status.lower() in status:
            self.log.info(f"Validated job status : {status}")
            self.log.info(f"Job went to {status} state successfully..")
        else:
            self.log.info(f"Job not moved to [{status}] status, Current status : [{job.status}] even after waiting for 30 minutes")
            raise CVTestStepFailure(f"Job not moved to [{status}] status, Current status : [{job.status}] even after waiting for 30 minutes")

    def wait_for_jobs(self, job_list):
        """Waits Till all Jobs in list are Completed
        Args:
            job_list(list):     List of jobs
        """
        self.log.info("Waiting for the Jobs to be completed")
        for job in job_list:
            self.log.info(f"Waiting for Job {job.job_id}")
            if not job.wait_for_completion():
                self.log.error(f"Error: Job ID {job.job_id} Failed {job.delay_reason}")
        self.log.info("Jobs Completed")

    def check_bad_chunks(self, store):
        """ Check for bad chunks for DV2 job
        Args:
            store(obj) : store object
        """
        bad_chunks = self.mmhelper_obj.get_bad_chunks(store_id=store.store_id, log_chunks=True)
        if bad_chunks:
            self.log.error(f"Bad Chunks found for Backup jobs of store - [{store.store_id}]")
            self.log.error(f"Bad Chunks - {bad_chunks}")
            raise CVTestStepFailure(
                f"Bad chunks found for Backup jobs of store - [{store.store_id}]. Bad Chunks - [{bad_chunks}]")
        self.log.info(f"Bad chunks NOT found for Backup jobs of store - [{store.store_id}]")

    def validate_data_verification_status(self, store):
        """Checks the DataVerification Status of the Jobs
        Args:
            store(obj) : store object
        """
        verification_statuses = []
        query = f"select archCheckStatus from JMJobDataStats where jobId in " \
                f"(select JobId from archJobsOnStoreInfo where StoreId={store.store_id})"
        self.log.info(f"QUERY : {query}")
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {rows}")
        result = [row[0] for row in rows]
        verification_statuses.extend(result)
        self.log.info(f"Job DV STATUS:{str(verification_statuses)}")
        # JMJobDataStatsEntries: 6: DV Failed, 5: Success, 0: Not Picked, Other- Partial or Unknown
        other_status = [x for x in verification_statuses if x != '5']
        if other_status:
            self.log.error(f"Other status found for backup jobs - {other_status}")
            raise CVTestStepFailure(f"Other status found for backup jobs - {other_status}")

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()
            self.run_backup(size=5)
            for _ in range(5):
                self.run_backup(backup_type="incremental", size=1)
            store = self.get_active_files_store()
            quick_incr_dv2 = self.run_dv2_job(store)
            self.validate_dv2_phase(quick_incr_dv2, "Validate Dedupe Data")
            self.validate_dv2_phase(quick_incr_dv2, "Verify Data")
            self.wait_for_jobs([quick_incr_dv2])
            self.check_bad_chunks(store)
            self.validate_data_verification_status(store)
        except Exception as exp:
            self.log.error(f"Failed to execute test case with error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        self.log.info("Performing unconditional cleanup")
        self.jm_helper.modify_restart_settings([self.default_settings])
        if self.status != constants.FAILED:
            self.log.info("Test Case PASSED")
        else:
            self.log.warning("Test Case FAILED")
        self.cleanup()

