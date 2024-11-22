# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    cleanup()       --  cleans up the entities

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    create_resources()  -- Create all the resources required to run backups

    gen_content()   -- Generates content

    run_backups()   --  Run backups on subclient

    get_sidb_store() --  Initialize the SIDB Store object

    wait_for_jobs()  -- wait for jobs to complete

    validate_dv2_pase() -- validates dv2 job phase

    validate_status()  -- validates dv2 status

    rename_dv2_tables() -- renames the dv2 tables

    do_validations() -- validates dv status

    disable_ransomware_protection () -- disables ransomware


    TcInputs to be passed in JSON File:
    "64491": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "MediaAgentName": Name of a MediaAgent - we create Libraries here
        ***** Optional: If provided, the below locations will be used to create ddb and MP*****
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
    }

"""
import time
import re
from cvpysdk import deduplication_engines
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Quick and Complete DV2 should use correct DV2 tables"
        self.tcinputs = {
            "MediaAgentName": None,
            "ClientName": None
        }
        self.ma_name = None
        self.client_name = None
        self.sp_name = None
        self.pool_name = None
        self.plan_name = None
        self.mountpath = None
        self.backupset_name = None
        self.subclient_name = None
        self.ma_machine_obj = None
        self.client_machine_obj = None
        self.mmhelper_obj = None
        self.deduphelper_obj = None
        self.option_obj = None
        self.content_path = None
        self.client_drive = None
        self.ma_drive = None
        self.is_user_defined_dedup = False
        self.is_user_defined_mp = False
        self.dedup_path = None
        self.pool_obj = None
        self.bkpset_obj = None
        self.subclient_obj = None
        self.subclient = {}
        self.store_obj = None
        self.media_agent_obj = None
        self.ddbma_object = None
        self.backup_jobs = []
        self.dv2_jobs = []
        self.copy_id = None
        self.reset_ransomware = False

    def setup(self):
        """Setup function of this test case"""
        self.option_obj = OptionsSelector(self.commcell)
        suffix = round(time.time())
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.client_name = self.tcinputs.get('ClientName')

        self.client_machine_obj = Machine(self.client)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)

        self.client_drive = self.option_obj.get_drive(self.client_machine_obj, 30*1024)
        if not self.is_user_defined_mp:
            self.ma_drive = self.option_obj.get_drive(self.ma_machine_obj, 30*1024)

        self.pool_name = f"STORAGEPOOL_{self.id}_{self.ma_name}"
        self.plan_name = f"PLAN_{self.id}_{self.ma_name}"

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_mp:
            self.mountpath = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"), f"TC_{self.id}", f"LIB_{suffix}")
            self.log.info(f"Using user provided mount path {self.mountpath}")
        else:
            self.mountpath = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"LIB_{suffix}")

        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"DDB_{suffix}")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get("dedup_path"), f"TC_{self.id}", f"DDB_{suffix}")
            self.log.info(f"Using user provided dedup path {self.dedup_path}")

        self.backupset_name = f"BKPSET_{self.id}_{self.client_name}"
        self.subclient_name = f"SUBC_{self.id}_{self.client_name}"
        self.content_path = self.client_machine_obj.join_path(self.client_drive, f"TC_{self.id}_CONTENT")

        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)
        self.mmhelper_obj = MMHelper(self)
        self.deduphelper_obj = DedupeHelper(self)
        self.ddbma_object = self.commcell.clients.get(self.ma_name)

        # Disable ransomware if windows MA
        if self.ma_machine_obj.os_info.lower() == 'windows':
            self.mmhelper_obj.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)
            self.log.info(f"Disabling ransomware protection on MA {self.ma_name}")
            self.media_agent_obj.set_ransomware_protection(False)

    def create_resources(self):
        """Create all the resources required to run backups"""
        # Create a storage pool
        if not self.commcell.storage_pools.has_storage_pool(self.pool_name):
            self.log.info(f"Creating Storage Pool - {self.pool_name}")
            self.pool_obj = self.commcell.storage_pools.add(self.pool_name, self.mountpath,
                                                            self.ma_name, [self.ma_name]*2,
                                                            [self.dedup_path, self.dedup_path])
        else:
            self.pool_obj = self.commcell.storage_pools.get(self.pool_name)
        # create plan
        if not self.commcell.plans.has_plan(self.plan_name):
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")
        else:
            self.plan = self.commcell.plans.get(self.plan_name)
        # disabling the schedule policy
        self.plan.schedule_policies['data'].disable()
        # Create a backupset
        self.log.info(f"Configuring Backupset - {self.backupset_name}")
        self.bkpset_obj = self.mmhelper_obj.configure_backupset(self.backupset_name)

        # Create 15 subclients
        for index in range(0, 15):
            self.subclient[index] = self.bkpset_obj.subclients.add(self.subclient_name + str(index))
            self.subclient[index].plan = [self.plan, [self.client_machine_obj.join_path(self.content_path, str(index))]]
            # To slow down backups
            self.subclient[index].data_readers = 1
            self.gen_content(self.client.client_name, self.client_machine_obj.join_path(self.content_path, str(index)), 1.0)

    def gen_content(self, clname, path, size):
        """
        Generate content
        Args:
            clname (str): client machine name
            path (str): path to gen data
            size (float): size of data
        """
        self.log.info(f"Generating content at {path}")
        self.mmhelper_obj.create_uncompressable_data(clname, path, size)

    def run_backups(self, subclient, backup_type="FULL"):
        """
        this function runs backup by generating new content to get unique blocks for dedupe backups.

        Args:
            subclient (str): subclient on which backup will run
            backup_type (str): type of backup to run
                                 Default - FULL
        Returns:
        (object) -- returns job object to backup job
        """
        self.log.info("Running %s backup...", backup_type)
        job = subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        return job

    def get_sidb_store(self):
        """
        Get SIDB store for the storage pool
        """
        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        if dedup_engines_obj.has_engine(self.pool_name, self.pool_obj.copy_name):
            dedup_engine_obj = dedup_engines_obj.get(self.pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])

    def wait_for_jobs(self, job_list):
        """Waits Till all Jobs in list are Completed
        Args:
            job_list(list):     List of jobs
        """
        #Wait for max 45 minutes
        for job in job_list:
            self.log.info(f"Waiting for Job {job.job_id} to be completed")
            if not job.wait_for_completion(timeout=45):
                self.log.error(f"Error: Job(Id: {job.job_id}) Failed({job.delay_reason})")
        self.log.info('Jobs Completed')

    def validate_dv2_phase(self, job, phase):
        """ Verify auto-resume after service restart in mid-Phase
        Args:
            job(list):   DV2 job object
            phase(str) : DV2 phase to be checked
        """
        # Waiting for max 20 minutes
        exit_condition = 1200
        while job.phase.lower() != phase.lower() and exit_condition > 0:
            self.log.info(f"Job is in {job.phase} phase. Expected Phase = {phase}")
            time.sleep(1)
            exit_condition -= 1
        if job.phase.lower() == phase.lower():
            self.log.info(f"Reached Job Phase : {phase}")
            self.validate_status(["running"], job)
        else:
            self.log.error(f"Even after waiting for 20 minutes, Job is not in {phase} phase. Current Phase = {job.phase}")
            raise Exception(f"Even after waiting for 20 minutes, Job is not in {phase} phase. Current Phase = {job.phase}")

    def validate_status(self, status, job):
        """ Validate job status
        Args:
            status(list):   DV2 job status
            job(obj) : DV2 job object
        """
        self.log.info(f"DV2 Job Current Phase : {job.phase}, Status : {job.status}")
        exit_condition = 1200  # wait for max 20 minutes
        while job.status.lower() not in status and exit_condition > 0:
            self.log.info(f"Expected job status: [{status}], Current status - [{job.status}]")
            time.sleep(1)
            exit_condition -= 1
        if job.status.lower() in status:
            self.log.info(f"Job went to {status} state successfully")
        else:
            self.log.error(f"Job not moved to [{status}] status, Current status : [{job.status}] even after waiting for 20 minutes")
            raise Exception(f"Job not moved to [{status}] status, Current status : [{job.status}] even after waiting for 20 minutes")

    def rename_dv2_tables(self, table_type):
        """
        Rename the dv2 table files for DedupChunks and ChunkIntegrity tables
        Args:
            table_type  (str)       --      Quick or Full tables
        """
        self.log.info("Waiting for SIDB to go down before starting with sidb table file manipulations")
        self.deduphelper_obj.wait_till_sidb_down(str(self.store_obj.store_id), self.commcell.clients.get(self.ma_name))
        table1 = ""
        table2 = ""
        if table_type == "Q":
            table1 = self.ma_machine_obj.join_path(self.dedup_path, "CV_SIDB", "2",
                                                    f"{self.store_obj.store_id}", "Split00", "DedupChunkQ.dat")
            table2 = self.ma_machine_obj.join_path(self.dedup_path, "CV_SIDB", "2",
                                                   f"{self.store_obj.store_id}", "Split00", "DedupChunkQ.idx")

        if table_type == "F":
            table1 = self.ma_machine_obj.join_path(self.dedup_path, "CV_SIDB", "2",
                                                            f"{self.store_obj.store_id}", "Split00", "ChunkIntegrityF.dat")
            table2 = self.ma_machine_obj.join_path(self.dedup_path, "CV_SIDB", "2",
                                                   f"{self.store_obj.store_id}", "Split00", "ChunkIntegrityF.idx")

        modified_table1 = f"{table1}_renamed"
        modified_table2 = f"{table2}_renamed"

        self.log.info(f"Renaming {table1} and {table2} to {modified_table1} and {modified_table2}")
        self.ma_machine_obj.rename_file_or_folder(table1, modified_table1)
        self.ma_machine_obj.rename_file_or_folder(table2, modified_table2)

    def do_validations(self):
        """
        Vaidates DV status
        """
        # Case 5: Check that dvstatus
        query = f"select count(jobid) from jmjobdatastats where archcheckstatus!=5 and archGrpCopyId = {self.copy_id}"
        self.log.info(f"Query is : {query}")
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info(f"Query result:{result[0][0]}")
        if result[0][0] == '0':
            self.log.info(f"CASE 5 PASSED: All jobs have been verified by DV2")
        else:
            self.log.info(f"CASE 5 FAILED: DV2 did not verify all jobs")
            self.status = constants.FAILED

    def cleanup(self):
        """
        Clean up the entities created by this test case
        """
        try:
            if self.client_machine_obj.check_directory_exists(self.content_path):
                self.log.info(f"Deleting already existing content directory {self.content_path}")
                self.client_machine_obj.remove_directory(self.content_path)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info(F"Deleting plan {self.plan_name}")
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
        except Exception as exe:
            self.log.warning("ERROR in Cleanup. Might need to Cleanup Manually: %s", str(exe))

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.create_resources()
            self.copy_id = self.plan.storage_policy.get_copy('Primary').copy_id
            quick_dv2_pid = 0
            complete_dv2_pid = 0
            log_file = "DDBDataVerf.log"

            # Run backups for subclient 0-4
            self.log.info("Running Backups for subclients 0-4")
            for index in range(0, 4):
                self.backup_jobs.insert(index, self.run_backups(subclient=self.subclient[index], backup_type="FULL"))
            # Wait for first 5 backups to complete
            self.wait_for_jobs(self.backup_jobs)

            # Start Quick DV2 job
            self.get_sidb_store()
            self.log.info(f"Running Quick Full DV2 job on store {self.store_obj.store_id}")
            self.dv2_jobs.append(self.store_obj.run_ddb_verification(incremental_verification=False,
                                                                     quick_verification=True, max_streams=1))
            self.log.info(f"Quick DV2 job: {self.dv2_jobs[0].job_id}")

            # Start backup for subclient 0-8 now
            self.log.info("Running Backups for subclients 0-8")
            for index in range(0, 8):
                self.backup_jobs.insert(index, self.run_backups(subclient=self.subclient[index], backup_type="FULL"))

            # Check when DV2 reaches phase-2
            self.validate_dv2_phase(self.dv2_jobs[0], "verify data")

            # While quick DV2 is in verify phase, start backups for 8-15
            self.log.info("Running Backups for subclient 8-15")
            for index in range(8, 15):
                self.backup_jobs.insert(index, self.run_backups(subclient=self.subclient[index], backup_type="FULL"))

            # Get split 0 PID for quick DV2 and make sure it opens Q tables
            log_string = f"{self.store_obj.store_id}-0.*OpenDataVerf.*Type.*\[Q\]"
            matchedline, matchedstring = self.deduphelper_obj.parse_log(self.ma_name, log_file, log_string,
                                                                        jobid=self.dv2_jobs[0].job_id, escape_regex=False,
                                                                        single_file=False, only_first_match=False)
            if matchedline:
                # get PID from last matched line
                split_line = re.split(r"\s+", matchedline[-1], 1)
                quick_dv2_pid = split_line[0]

            # Wait till quick DV2 job completes
            self.log.info(f"Wait for quick full DV2 job on store {self.store_obj.store_id} to complete")
            self.wait_for_jobs(self.dv2_jobs)

            # Start Complete DV2 job once quick DV2 completes.
            self.log.info(f"Running Complete full DV2 job on store {self.store_obj.store_id}")
            self.dv2_jobs[0] = self.store_obj.run_ddb_verification(incremental_verification=False, quick_verification=False)
            self.log.info(f"Complete DV2 job: {self.dv2_jobs[0].job_id}")
            # Check when DV2 reaches phase-1 and in running state, get the sidb pid
            self.validate_dv2_phase(self.dv2_jobs[0], "validate dedupe data")
            # Text to match : Opening DV tables....Type [F]
            log_string = f"{quick_dv2_pid}.*{self.store_obj.store_id}-0.*OpenDataVerf.*Type.*\[F\]"
            matchedline, matchedstring = self.deduphelper_obj.parse_log(self.ma_name, log_file, log_string,
                                                                        jobid=self.dv2_jobs[0].job_id,
                                                                        escape_regex=False,
                                                                        single_file=False, only_first_match=True)
            if matchedline:
                # get complete dv2 PID from first matched line
                split_line = re.split(r"\s+", matchedline[0])
                complete_dv2_pid = split_line[0]
                table_used = split_line[-1]

            if(complete_dv2_pid == quick_dv2_pid and complete_dv2_pid != 0 and quick_dv2_pid !=0 and matchedline):
                self.log.info(f"CASE 1 PASSED: Quick DV2 SIDB pid {quick_dv2_pid} and complete dv2 SIDB  pid {complete_dv2_pid} are same")
                self.log.info(f"CASE 2 PASSED: Correct tables used for complete DV2 : {table_used}")
            else:
                self.log.info(f"CASE 1,2 FAILED: Quick DV2 pid {quick_dv2_pid},complete dv2 pid {complete_dv2_pid} are not same, incorrect table used")
                self.status = constants.FAILED
            # Wait for DV2 and Backup Jobs to complete
            self.wait_for_jobs(self.dv2_jobs)
            self.wait_for_jobs(self.backup_jobs)

            # Launch incremental quick DV2. While it is in phase-1, suspend the job, delete Q tables, resume the job
            # Expectation is that the job should complete without errors.
            # Check DV status from DDB of all backup jobs - it should have 5
            self.log.info(f"Running Quick INCR DV2 job on store {self.store_obj.store_id}")
            self.dv2_jobs[0] = self.store_obj.run_ddb_verification(incremental_verification=True, quick_verification=True)
            self.log.info(f"Quick DV2 job: {self.dv2_jobs[0].job_id}")
            self.validate_dv2_phase(self.dv2_jobs[0], "validate dedupe data")
            # suspend dv2 job
            self.log.info(f"Suspend DV2 Job in phase-1")
            self.dv2_jobs[0].pause(wait_for_job_to_pause=True)
            # delete Q tables
            self.log.info(f"Rename Q Tables")
            self.rename_dv2_tables('Q')
            # resume job
            self.log.info(f"Resume DV2 Job")
            self.dv2_jobs[0].resume(wait_for_job_to_resume=False)
            # wait for job to complete
            self.wait_for_jobs(self.dv2_jobs)
            self.log.info(f"CASE 3 PASSED: DV2 job has completed as expected")

            # Delete the F tables in phase-2. Check that DV2 fails
            self.log.info(f"Running Complete INCR DV2 job on store {self.store_obj.store_id}")
            self.dv2_jobs[0] = self.store_obj.run_ddb_verification(incremental_verification=True, quick_verification=False)
            self.log.info(f"Complete DV2 job: {self.dv2_jobs[0].job_id}")
            self.validate_dv2_phase(self.dv2_jobs[0], "verify data")
            # suspend dv2 job
            self.log.info(f"Suspend DV2 Job in phase-2")
            self.dv2_jobs[0].pause(wait_for_job_to_pause=True)
            self.log.info(f"Rename F Tables")
            self.rename_dv2_tables('F')
            # resume job
            self.log.info(f"Resume DV2 Job")
            self.dv2_jobs[0].resume(wait_for_job_to_resume=True)
            # check the job goes pending again.
            self.validate_status(["pending"], self.dv2_jobs[0])
            # check DDBDataverf.log that the pending reason is not being to open tables
            log_string = f"{self.store_obj.store_id}-0.*OpenDataVerf.*Cannot open DV2 tables.*\[53018\]"
            matchedline, matchedstring = self.deduphelper_obj.parse_log(self.ma_name, log_file, log_string,
                                                                        jobid=self.dv2_jobs[0].job_id,
                                                                        escape_regex=False,
                                                                        single_file=False, only_first_match=True)
            if matchedline:
                self.log.info("CASE 4 PASSED: DV2 job has gone pending as expected. Kill this job")
            else:
                self.log.error("CASE 4 FAILED: DV2 job has not gone pending with expected logging")
            # kill the job
            self.dv2_jobs[0].kill(wait_for_job_to_kill=True)

            # start a new complete incr dv2 job and make sure it passes
            self.log.info(f"Running Complete INCR DV2 job on store {self.store_obj.store_id}")
            self.dv2_jobs[0] = self.store_obj.run_ddb_verification(incremental_verification=True,
                                                                      quick_verification=False)
            self.log.info(f"Complete DV2 job: {self.dv2_jobs[0].job_id}")
            self.wait_for_jobs(self.dv2_jobs)
            # Check DV status=5 for all the jobs
            self.do_validations()

        except Exception as exp:
            self.log.error("Failing test case : Error Encountered - %s", str(exp))
            self.status = constants.FAILED
            self.result_string = str(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Performing Unconditional Cleanup")
        # Enable Ransomware back
        if self.ma_machine_obj.os_info.lower() == 'windows':
            self.log.info(f"Enabling ransomware protection on client {self.ma_name}")
            self.media_agent_obj.set_ransomware_protection(True)
        self.cleanup()


