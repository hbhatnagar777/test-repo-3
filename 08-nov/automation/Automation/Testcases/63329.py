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

    setup_environment() -- configures all entities based tcinputs

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    setup_environment() -- configures entities based on inputs

    get_active_files_store() -- gets active files DDB store id

    cleanup()   --  cleanups all created entities

    run_backup()    -- runs backup need for the case

    run_dv2_job()   -- runs DV2 job with options provided

    verify_job_type() -- Verify Job type is converted to Full

    validate_log() -- Searches for passed string in log file

    kill_dv2_job() --Method to kill the dv2 jobs running for the client
    get_total_chunks() -- Returns total chunks for the job
    validation_in_phase2() -- Chunk count and Pruning flag validations after phase1
    validate_all_jobs() -- Validate all jobs are successfully validated
    check_bad_chunks() -- Check for bad chunks for DV2 job

Note: if no predefined entities provided in input, we will create them.
if need to use predefined entities like Library or SP. add them to input json

Sample JSON: values under [] are optional
"63329": {
            "ClientName": "client name",
            "AgentName": "File System",
            "MediaAgentName": "ma name",
            [ Optional :
            "ScaleFactor": "ScaleFactor",
            "DDBPath": "E:\\DDBs\\dv2tests\\0", - path to be used for creating ddb during pool creation. For linux specify LVM path
            "MountPath": "E:\\Libraries\\dv2tests_defragmp", - mount path to use to create storage pool
        }

design:

    Cleanup previous run environment
    Create test environment
    Run backup B1 with 10GB data
    Wait for backup job to complete
    Run 20 incremental jobs : 100MB
    Wait for backup job to complete
    Run Incr DV2 job
    After validation of some chunks KILL the DV2 job
    Once enumeration is done, note down the chunk count
    Run Incr DV2 job again
    As soon as DV2 phase 2 starts wait for 40 seconds and kill the DV2 job
    Once phase 1 completed  (During Phase 2) ,  check total count of "validated in this run and already validated chunk count" should be equal to count in step 12
    "ArchCheckstatus of some jobs should be 4 and 5

    0 - do not verify data
    3 - pick for verification
    4 - partial
    5 - successful
    6 - failed"
    Run Incr DV2 job and it should verify all jobs without any issue
    Verify no Bad Chunks found
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from Server.JobManager.jobmanagement_helper import JobManagementHelper
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Kill DV2 job and Verify the backup job verification Status."
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
        self.deduphelper_obj = None
        self.scale_factor = None
        self.status = constants.PASSED

    def setup(self):
        """
        Setup function of this test case. initialises entity names if provided in tcinputs otherwise assigns new names
        """
        self.option_obj = OptionsSelector(self.commcell)
        self.mmhelper_obj = MMHelper(self)
        self.jm_helper = JobManagementHelper(self.commcell)
        self.deduphelper_obj = DedupeHelper(self)
        suffix = round(time.time())
        self.mount_path = self.tcinputs.get("MountPath")
        self.ma_name = self.tcinputs.get("MediaAgentName")
        self.ddb_path = self.tcinputs.get("DDBPath")
        self.client_name = self.tcinputs.get("ClientName")
        self.scale_factor = self.tcinputs.get("ScaleFactor")
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)
        self.client_machine_obj = Machine(self.client)

        self.plan_name = f"PLAN_{self.id}_{self.ma_name}"
        self.pool_name = f"STORAGEPOOL_{self.id}_{self.ma_name}"
        if self.tcinputs.get("MountPath"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("DDBPath"):
            self.is_user_defined_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        self.client_drive = self.option_obj.get_drive(self.client_machine_obj, 25 * 1024)
        if not self.is_user_defined_mp:
            self.ma_drive = self.option_obj.get_drive(self.ma_machine_obj, 25 * 1024)

        if self.is_user_defined_mp:
            self.mount_path = self.ma_machine_obj.join_path(self.tcinputs.get("MountPath"), f"TC_{self.id}", f"LIB_{suffix}")
            self.log.info(f"Using user provided mount path {self.mount_path}")
        else:
            self.mount_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"LIB_{suffix}")

        if self.is_user_defined_dedup:
            self.ddb_path = self.ma_machine_obj.join_path(self.tcinputs.get("DDBPath"), f"TC_{self.id}", f"DDB_{suffix}")
            self.log.info(f"Using user provided dedup path {self.ddb_path}")
        else:
            self.ddb_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"DDB_{suffix}")

        self.backupset_name = f"BKPSET_{self.id}_{self.client_name}"
        self.subclient_name = f"SUBC_{self.id}_{self.client_name}"
        self.content_path = self.client_machine_obj.join_path(self.client_drive, f"TC_{self.id}_CONTENT")

    def setup_environment(self):
        """ configures all entities based tcinputs. if subclient or storage policy or library is provided,
        TC will use these entities and run the case """
        self.log.info("Setting up environment...")
        # Create pool if pool name is not specified
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

        self.primary_copy = self.plan.storage_policy.get_copy('Primary')
        self.plan.schedule_policies['data'].disable()
        # Create a backupset
        self.log.info(f"Configuring Backupset - {self.backupset_name}")
        self.bkpset_obj = self.mmhelper_obj.configure_backupset(self.backupset_name)
        # Create subclient
        self.subclient = self.bkpset_obj.subclients.add(self.subclient_name)
        self.subclient.plan = [self.plan, [self.content_path]]

    def cleanup(self):
        """
        performs cleanup of all entities only if created by case.
        """
        try:
            if self.client_machine_obj.check_directory_exists(self.content_path):
                self.log.info(f"Deleting already existing content directory {self.content_path}")
                self.client_machine_obj.remove_directory(self.content_path)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)
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
        except Exception as e:
            self.log.warning(f"Something went wrong while cleanup! Exception occurred - [{e}]")

    def run_backup(self, backup_type="FULL", size=1.0):
        """
        this function runs backup by generating new content to get unique blocks for dedupe backups.
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
        # if scale test param is passed in input json, multiply size by scale factor times and generate content
        if self.scale_factor:
            size = size * int(self.scale_factor)
        self.mmhelper_obj.create_uncompressable_data(self.client_name, additional_content, size)

        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(backup_type, job.delay_reason)
            )
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
        Runs DV2 job with type and option selected
        Args:
            store (object) - object of the store to run DV2 job on
        Returns:
             (object) -  DV2 job object
        """
        self.log.info(f"running incremental DV2 job on store {store.store_id}")
        job = store.run_ddb_verification(quick_verification=False, max_streams=5)
        self.log.info(f"DV2 job: {job.job_id}")
        return job

    @test_step
    def validate_log(self, job, log_string):
        """ Searches for passed string in log file """
        log_file = 'ScalableDDBVerf.log'
        logline = self.check_logs(job, log_string, log_file)
        if not logline:
            raise CVTestStepFailure(
                f"Log file [{log_file}] not contain [{log_string}], even after waiting for 5 minutes")

    def check_logs(self, job, log_string, log_file='DDBDataVerf.log'):
        """ Searches for passed string in log file
        Returns:
             list of matched lines"""
        wait_limit = 0
        while wait_limit < 300:
            self.log.info(f"Keep Checking logging for [{log_string}] in log file [{log_file}]")
            (matched_line, matched_string) = self.deduphelper_obj.parse_log(
                self.tcinputs['MediaAgentName'], log_file, log_string, jobid=job.job_id)

            if matched_line:
                self.log.info(f"Found search string [{log_string}] in logs")
                return matched_line
            wait_limit += 1
            time.sleep(1)
            self.log.info(f"Wait for job to get {log_string} :  Retrying")
        self.log.error(f"Log file [{log_file}] not contain [{log_string}]")
        return []

    @test_step
    def validation_in_phase2(self, job, phase, total_chunks):
        """Chunk count and Pruning flag validations after phase1
            args:
            job(obj) : job object
            phase(str) : dv2 phase
            total_chunks(int) : chunk total
        """
        self.log.info(f"Chunk count and Pruning flag validations after phase1 -{phase}")
        exit_condition = 900
        # Waiting for max 30 minutes..
        while job.phase.lower() != phase.lower() and exit_condition > 0:
            self.log.info(f"Job is in [{job.phase}] phase. Expected Phase = [{phase}]")
            time.sleep(2)
            exit_condition -= 1

        if job.phase.lower() == phase.lower():
            self.log.info(f"Reached Job Phase : [{phase}]")
            time.sleep(40)  # intentional sleep for 40 seconds for some jobs to get verified
            self.kill_dv2_job(job)

            enabled_count = self.check_logs(job, "Pruning is [Enabled] now", log_file='SIDBEngine.log')
            disabled_count = self.check_logs(job, "Disabling pruning control flag", log_file='SIDBEngine.log')
            if len(enabled_count) != 2 and len(disabled_count) != 2:
                self.log.error("Pruning Enabled/Disabled is not found for both substores")
                self.log.error(f"Pruning Enabled Count - [{len(enabled_count)}]")
                self.log.error(f"Pruning Disabled Count - [{len(disabled_count)}]")
                raise CVTestStepFailure(f"Pruning Enabled/Disabled is not found for both substores")

            current_chunk, already_chunk = self.get_validated_chunk_count(job)
            validated_chunks = current_chunk + already_chunk
            if not (validated_chunks >= total_chunks):
                self.log.error("Chunks count doesnt match."
                               f"Total Chunks {total_chunks}; Validated Chunks {validated_chunks}")
                raise CVTestStepFailure(f"Chunks count doesnt match."
                                        f"Total Chunks{total_chunks}; Validated Chunks {validated_chunks}")
        else:
            self.log.error(f"Even after waiting for 30 minutes, Job is not in {phase} phase. Current Phase = {job.phase}")
            raise CVTestStepFailure(
                f"Even after waiting for 30 minutes, Job is not in [{phase}] phase. Current Phase = [{job.phase}]")

    def wait_for_jobs(self, job_list):
        """Waits Till all Jobs in list are Completed
        Args:
            job_list(list):     List of jobs
        """
        self.log.info("Waiting for the Jobs to be completed")
        time.sleep(30)
        for job in job_list:
            self.log.info(f'Waiting for Job {job.job_id}')
            if not job.wait_for_completion():
                self.log.error(f"Error: Job(Id: {job.job_id}) Failed :{job.delay_reason})")
        self.log.info("Jobs Completed")

    @test_step
    def check_bad_chunks(self, store):
        """ Check for bad chunks for DV2 job"""
        bad_chunks = self.mmhelper_obj.get_bad_chunks(store_id=store.store_id, log_chunks=True)
        if bad_chunks:
            self.log.error(f"Bad Chunks found for Backup jobs of store - [{store.store_id}]")
            self.log.error(f"Bad Chunks - {bad_chunks}")
            raise CVTestStepFailure(
                f"Bad chunks found for Backup jobs of store - [{store.store_id}]. Bad Chunks - [{bad_chunks}]")
        self.log.info(f"Bad chunks NOT found for Backup jobs of store - [{store.store_id}]")

    def get_data_verification_status(self, store):
        """Returns the DataVerification Status of the Jobs"""
        verification_statuses = []
        query = f"""select
        archCheckStatus
        from JMJobDataStats where
        jobId in (select JobId from archJobsOnStoreInfo where StoreId={store.store_id})"""

        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        result = [row[0] for row in rows]
        verification_statuses.extend(result)
        self.log.info(f"Job DV STATUS: {str(verification_statuses)}")
        # JMJobDataStatsEntries: 6: DV Failed, 5: Success, 0: Not Picked, Other- Partial or Unknown
        return verification_statuses

    @test_step
    def validate_all_jobs(self, store):
        """Validate all jobs are successfully validated"""
        verification_statuses = self.get_data_verification_status(store)
        other_status = [x for x in verification_statuses if x != '5']
        if other_status:
            self.log.error(f"Other status found for backup jobs - {other_status}")
            raise CVTestStepFailure(f"Other status found for backup jobs - {other_status}")
        self.log.info("All Jobs are Successful!")

    @test_step
    def kill_dv2_job(self, job):
        """ Method to kill the dv2 jobs running for the client """
        if job.status.lower() != 'completed' or job.status.lower() != 'failed':
            self.log.info("Killing Job:%s", job)
            job.kill(True)
            if job.status.lower() != 'killed':
                self.log.error(f"Job is in [{job.status}] State. Expected Status = Killed")
                raise CVTestStepFailure(f"Job is not killed. Job is in [{job.status}] status")
            self.log.info("Job Killed successfully")

    def get_total_chunks(self, job):
        """ Returns total chunks for the job"""
        logline = self.check_logs(job, "Finished traversing")
        if logline:
            total_chunks = int(logline[-1].split('recs. Added')[1].split('[')[1].split(']')[0])
            self.log.info(f"Total Chunks are {total_chunks}")
            return total_chunks
        self.log.error("Logs do not contain total count of chunks added, even after waiting for 5 minutes")
        raise CVTestStepFailure(
            "Logs do not contain total count of chunks added, even after waiting for 5 minutes")

    def get_validated_chunk_count(self, job):
        """ Returns the count of Chunks validated in this run and last run"""
        logline = self.check_logs(job, "Chnks validated in this run")
        if logline:
            current_validated_chunks = int(
                logline[0].split('Chnks validated in this run')[-1].split('[')[1].split(']')[0])
            already_validated_chunks = int(logline[0].split(' already validated')[-1].split('[')[1].split(']')[0])
            return current_validated_chunks, already_validated_chunks
        self.log.error("Logs do not contain total count of chunks validated in this run or already validated")
        raise CVTestStepFailure(
            "Logs do not contain total count of chunks validated in this run or already validated")

    @test_step
    def verify_job_type(self, job):
        """ Verify Job type is converted to Full"""
        # logline = self.check_logs(job, "Dedup Chunks Collector - Created data verf tables.")
        logline = self.check_logs(job, "Created data verf tables.")
        if logline:
            self.log.info("Incr Job Converted to Full")
        else:
            self.log.error("Incr Job NOT Converted to Full.")
            self.log.error("Logline not found - [Dedup Chunks Collector - Created data verf tables.]")
            raise CVTestStepFailure("Incr Job NOT Converted to Full. "
                                    "Logline not found - [Dedup Chunks Collector - Created data verf tables.]")

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()
            self.run_backup(size=10)
            for _ in range(15):
                self.run_backup(backup_type="incremental", size=0.1)
            store = self.get_active_files_store()
            dv2_job1 = self.run_dv2_job(store)
            self.verify_job_type(dv2_job1)
            self.validate_log(dv2_job1, "Validated")
            self.kill_dv2_job(dv2_job1)
            total_chunks = self.get_total_chunks(dv2_job1)

            dv2_job2 = self.run_dv2_job(store)
            self.validation_in_phase2(dv2_job2, "Verify Data", total_chunks)

            dv2_job3 = self.run_dv2_job(store)
            self.wait_for_jobs([dv2_job3])
            self.validate_all_jobs(store)
            self.check_bad_chunks(store)
        except Exception as exp:
            self.log.error(f"Failed to execute test case with error: {exp}")
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED.')
        else:
            self.log.warning('Test Case FAILED.')
        self.cleanup()
