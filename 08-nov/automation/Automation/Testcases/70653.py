# -*- coding: utf-8 -*-

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

    get_sidb_store()  -- get sdbstore id

    create_resources()  - create resources

    delete_resources()  - delete resources

    run_backups()   -- run backup

    wait_for_jobs()  -- wait for jobs to complete

    add_mountpath() -- adds mount path

    validate_status() -- validates status of dv2 job

    gen_content()  -- generate content

    get_cvods_pid() -- get cvoids pid

    run_dv2()       -- runs dv2 job

    do_validations() -- do final validations of pid used and dv status

    run()           --  run function of this test case

    cleanup()     --  tear down function of this test case

    TcInputs to be passed in JSON File:
    "70653": {
        "ClientName": "client name ",
        "AgentName": "File System",
        "PrimaryCopyMediaAgent":  "Ma name",
        "SecondaryCopyMediaAgent":"Ma name",
        Optional values:
        "mount_path": "c:\MP1",   --- path where primary copy library is to be created
        "mount_path2": "c:\MP1",   -- path where secondary copy library is to be created
        "dedup_path": "c:\DDB1",   ---path where dedup store to be created [for linux MediaAgents,LVM support required for DDB]
        "dedup_path2": ""c:\DDB2" --- path where dedup store to be created for auxcopy [for linux MediaAgents,LVM support required for DDB]
        }
Steps:

1: Configure the environment: create a pool, plan-with Primary, pool for Secondary Copy,
                              a BackupSet,15 SubClients

2: Run 8 backup jobs each for each of the subclients

3: Start Auxcopy Job with 1 stream

4. Start quick full Dv2 job. Get the cvods pid for dv2 job

5. Add a new MP

6. Disable the older MP for writes

7. Start more backups (we have to make sure auxcopy keeps running).

8. Start quick+incr dv2 job once the earlier dv2 job completes.

9. Start more backups and wait for them to complete

10. Start quick+incr dv2 job once the earlier dv2 job completes and get cvods pid for dv2 job

11. Verify that DV2 uses the same CVODS PID as the first DV2 cvods PID and it completely verifies all backup jobs on the primary

12: Cleanup
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
        self.name = "Add MP during DV2 and next DV2 uses the same CVODS PID"
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None,
            "ClientName": None
        }
        self.ma_name = None
        self.ma2_name = None
        self.client_name = None
        self.sp_name = None
        self.pool_name = None
        self.pool2_name = None
        self.plan_name = None
        self.copy_name = None
        self.library_name = None
        self.mountpath = None
        self.backupset_name = None
        self.subclient_name = None
        self.ma_machine_obj = None
        self.ma2_machine_obj = None
        self.client_machine_obj = None
        self.mmhelper_obj = None
        self.deduphelper_obj = None
        self.library_obj = None
        self.option_obj = None
        self.content_path = None
        self.client_drive = None
        self.ma_drive = None
        self.ma2_drive = None
        self.is_user_defined_dedup = False
        self.is_user_defined_mp = False
        self.is_user_defined_dedup2 = False
        self.is_user_defined_mp2 = False
        self.dedup_path = None
        self.dedup_path2 = None
        self.pool_obj = None
        self.pool2_obj = None
        self.subclient_obj = None
        self.subclient = {}
        self.store_obj = None
        self.ddbma_object = None
        self.backup_jobs = []
        self.dv2_job = []
        self.aux_copy_job = None
        self.mount_path_id = None
        self.utility = None
        self.log_file = "ScalableDDBVerf.log"

    def setup(self):
        """Setup function of this test case"""
        self.option_obj = OptionsSelector(self.commcell)
        suffix = round(time.time())
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        if self.tcinputs.get("mount_path2"):
            self.is_user_defined_mp2 = True
        if self.tcinputs.get("dedup_path2"):
            self.is_user_defined_dedup2 = True

        self.ma_name = self.tcinputs.get('PrimaryCopyMediaAgent')
        self.ma2_name = self.tcinputs.get('SecondaryCopyMediaAgent')
        self.client_name = self.tcinputs.get('ClientName')

        self.client_machine_obj = Machine(self.client)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma2_machine_obj = Machine(self.ma2_name, self.commcell)

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.is_user_defined_dedup2 and "unix" in self.ma2_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        self.client_drive = self.option_obj.get_drive(self.client_machine_obj, 30*1024)
        if not self.is_user_defined_mp:
            self.ma_drive = self.option_obj.get_drive(self.ma_machine_obj, 30*1024)
        if not self.is_user_defined_mp2:
            self.ma2_drive = self.option_obj.get_drive(self.ma2_machine_obj, 30 * 1024)

        self.pool_name = f"STORAGEPOOLPRI_{self.id}_{self.ma_name}_{self.ma2_name}"
        self.pool2_name = f"STORAGEPOOLSEC_{self.id}_{self.ma2_name}_{self.ma_name}"
        self.plan_name = f"PLAN_{self.id}_{self.ma_name}_{self.ma2_name}"

        # For primary
        if self.is_user_defined_mp:
            self.mountpath = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"), f"TC_{self.id}", f"LIB1_{suffix}")
            self.mountpath_1 = f"{self.mountpath}_MP2"
            self.log.info(f"Using user provided mount path {self.mountpath}")
        else:
            self.mountpath = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"LIB1_{suffix}")
            self.mountpath_1 = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"MP2_{suffix}")

        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"DDBPRI_{suffix}")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get("dedup_path"), f"TC_{self.id}", f"DDBPRI_{suffix}")
            self.log.info(f"Using user provided dedup path {self.dedup_path}")

        # For secondary
        if self.is_user_defined_mp2:
            self.mountpath2 = self.ma2_machine_obj.join_path(self.tcinputs.get("mount_path2"), f"TC_{self.id}", f"LIB2_{suffix}")
            self.log.info(f"Using user provided mount path {self.mountpath2}")
        else:
            self.mountpath2 = self.ma2_machine_obj.join_path(self.ma2_drive, f"TC_{self.id}", f"LIB2_{suffix}")

        if not self.is_user_defined_dedup2:
            self.dedup_path2 = self.ma2_machine_obj.join_path(self.ma2_drive, f"TC_{self.id}", f"DDBSEC_{suffix}")
        else:
            self.dedup_path2 = self.ma2_machine_obj.join_path(self.tcinputs.get("dedup_path2"), f"TC_{self.id}", f"DDBSEC_{suffix}")
            self.log.info(f"Using user provided dedup path {self.dedup_path2}")

        self.backupset_name = f"BKPSET_{self.id}_{self.client_name}"
        self.subclient_name = f"SUBC_{self.id}_{self.client_name}"
        self.content_path = self.client_machine_obj.join_path(self.client_drive, f"TC_{self.id}_CONTENT")
        self.copy_name = f"{self.id}_Copy"
        self.mmhelper_obj = MMHelper(self)
        self.deduphelper_obj = DedupeHelper(self)
        self.ddbma_object = self.commcell.clients.get(self.ma_name)
        self.utility = OptionsSelector(self.commcell)

    def create_resources(self):
        """Create all the resources required to run backups"""
        # Create primary storage pool
        if not self.commcell.storage_pools.has_storage_pool(self.pool_name):
            self.log.info(f"Creating Storage Pool - {self.pool_name}")
            self.pool_obj = self.commcell.storage_pools.add(self.pool_name, self.mountpath,
                                                           self.ma_name, [self.ma_name]*2,
                                                            [self.dedup_path, self.dedup_path])
        else:
            self.pool_obj = self.commcell.storage_pools.get(self.pool_name)

        # Get library and mountpath id details to be used later
        library_details = self.pool_obj.storage_pool_properties["storagePoolDetails"]["libraryList"][0]['library']
        self.library_name = library_details["libraryName"]
        self.library_obj = self.commcell.disk_libraries.get(self.library_name)
        self.log.info(f"library id {self.library_obj.library_id}")
        query = f"select mountpathid from mmmountpath where libraryid = {self.library_obj.library_id}"
        self.log.info(f"Query is: {query}")
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.mount_path_id = result[0]
        self.log.info(f"Mountpath ID is {self.mount_path_id}")

        # Create plan
        if not self.commcell.plans.has_plan(self.plan_name):
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")
        else:
            self.plan = self.commcell.plans.get(self.plan_name)

        # Disabling the schedule policy for backups on the plan
        self.plan.schedule_policies['data'].disable()

        # Create secondary Storage pool
        if not self.commcell.storage_pools.has_storage_pool(self.pool2_name):
            self.log.info(f"Creating Secondary Storage Pool - {self.pool2_name}")
            self.pool2_obj = self.commcell.storage_pools.add(self.pool2_name, self.mountpath2,
                                                            self.ma2_name, [self.ma2_name]*2,
                                                            [self.dedup_path2, self.dedup_path2])
        else:
            self.pool2_obj = self.commcell.storage_pools.get(self.pool2_name)
        # Add secondary copy to plan
        self.log.info("Adding secondary copy to plan")
        self.plan.add_storage_copy(self.copy_name, self.pool2_name)

        # Remove Association with System Created AutoCopy Schedule
        self.mmhelper_obj.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.copy_name)
        # Create a backupset
        self.log.info(f"Configuring Backupset - {self.backupset_name}")
        bkpset_obj = self.mmhelper_obj.configure_backupset(self.backupset_name)

        # Create 15 subclients
        for index in range(0, 15):
            self.subclient[index] = bkpset_obj.subclients.add(self.subclient_name + str(index))
            self.subclient[index].plan = [self.plan, [self.client_machine_obj.join_path(self.content_path, str(index))]]
            self.subclient[index].data_readers = 4
            self.subclient[index].allow_multiple_readers = True
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
            subclient (obj: subclient on which backup will run
            backup_type (str): type of backup to run
                                 Default - FULL
        Returns:
        (object) -- returns job object to backup job
        """
        self.log.info(f"Running {backup_type} backup...")
        job = subclient.backup(backup_type)
        self.log.info(f"Backup job: {job.job_id}")
        return job

    def validate_status(self, status, job):
        """ Validate job status
        Args:
            status(list):   DV2 job status to verify
            job(obj) : DV2 job object
        """
        self.log.info(f"DV2 Job Current Status : {job.status}")
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
        # Wait for max 45 minutes
        for job in job_list:
            self.log.info(f"Waiting for Job {job.job_id} to be completed")
            if not job.wait_for_completion(timeout=45):
                self.log.error(f"Error: Job(Id: {job.job_id}) Failed({job.delay_reason})")
        self.log.info('Jobs Completed')

    def get_cvods_pid(self, jobid, log_string, only_first_match):
        """
            This function returns the cvods pid for the given job
            Args:
                jobid (str): subclient on which backup will run
                log_string (str): type of backup to run
                                         Default - FULL
                only_first_match(bool) : first or last match in the given log file
            Returns:
            str -- returns cvods pid
        """
        matchedline, matchedstring = self.deduphelper_obj.parse_log(self.ma_name, self.log_file, log_string,
                                                                    jobid=jobid,
                                                                    escape_regex=False,
                                                                    single_file=False,
                                                                    only_first_match=only_first_match)
        if matchedline:
            # get PID from last matched line
            split_line = re.split(r"\s+", matchedline[-1], 1)
            return split_line[0]
        else:
            self.log.error(f"Could not find CVODS PID for the given job")

    def do_validations(self, copy_id):
        """Validate DV status and PID between jobs
        Args:
            copy_id(str):     copy id of primary copy
        """
        # Case 1: Check that dv2 uses the same cvods pid as auxcopy
        if self.dv2_pid == self.dv2_pid2:
            self.log.info(f"CASE 1 PASSED: Both DV2 jobs used the same CVODS PID : {self.dv2_pid}")
        else:
            self.log.info(f"CASE 1 FAILED: CVODS PID for DV2 1{self.dv2_pid}, DV2 2 {self.dv2_pid2} "
                          f"are not same or could not be found in the logs")
            self.status = constants.FAILED
        # Case 2: Check DV status
        query = f"select count(jobid) from jmjobdatastats where archcheckstatus!=5 and archGrpCopyId = {copy_id}"
        self.log.info(f"Query is : {query}")
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info(f"Query result:{result[0][0]}")
        if result[0][0] == '0':
            self.log.info(f"CASE 2 PASSED: All jobs have been verified by DV2")
        else:
            self.log.info(f"CASE 2 FAILED: DV2 did not verify all jobs")
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
                self.log.info(f"Deleting Primary Storage Pool {self.pool_name}")
                self.commcell.storage_pools.delete(self.pool_name)
            if self.commcell.storage_pools.has_storage_pool(self.pool2_name):
                self.log.info(f"Deleting Secondary Storage Pool {self.pool2_name}")
                self.commcell.storage_pools.delete(self.pool2_name)
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
            copy_id = self.plan.storage_policy.get_copy('Primary').copy_id
            log_string = "Initializing Coordinator"

            # Run backups for subclient 0-8
            self.log.info("Running Backups for subclients 0-8")
            for index in range(0, 8):
                self.backup_jobs.insert(index, self.run_backups(subclient=self.subclient[index], backup_type="FULL"))
            # Wait for first 8 backups to complete
            self.wait_for_jobs(self.backup_jobs)

            # Start Auxcopy job with 1 stream so that it keeps running to keep CVODS PID alive
            self.log.info("Submitting AuxCopy job with scalable resource allocation")
            self.aux_copy_job = self.plan.storage_policy.run_aux_copy(use_scale=True, streams=1)
            self.log.info(f"Auxcopy job: {self.aux_copy_job.job_id}")

            # Start quick DV2 job
            self.get_sidb_store()
            self.log.info(f"Running First Quick Full DV2 job on store {self.store_obj.store_id}")
            self.dv2_job.append(self.store_obj.run_ddb_verification(incremental_verification=False, quick_verification=True, max_streams=5))
            self.log.info(f"First Quick FULL DV2 job: {self.dv2_job[0].job_id}")

            # Wait till DV2 goes to running state
            self.validate_status(["running"], self.dv2_job[0])

            # Add MP2 while Auxcopy and DV2 are running
            self.mmhelper_obj.configure_disk_mount_path(self.library_obj, self.mountpath_1, self.ma_name)

            # Disable MP1 for writes so that MP2 is used for next set of backups, but references old MP
            self.log.info(f"Disabling MP1 for writes")
            self.mmhelper_obj.edit_mountpath_properties(self.mountpath, self.library_name, self.ma_name, num_writers_for_mp=0)
            self.log.info(f"MP1 is disabled for writes")

            # Start backup for subclient 0-15
            self.log.info("Running Backups for subclients 0-15")
            for index in range(0, 15):
                self.backup_jobs.insert(index, self.run_backups(subclient=self.subclient[index], backup_type="FULL"))

            # Get CVODS PID for first DV2 Job and wait for dv2 to complete
            self.dv2_pid = self.get_cvods_pid(self.dv2_job[0].job_id, log_string, True)
            self.log.info(f"CVODS PID for first DV2 job: {self.dv2_pid}")
            self.log.info("Wait for backups to complete")
            self.wait_for_jobs(self.backup_jobs)
            time.sleep(60)
            # Start INCR DV2 job
            self.log.info(f"Wait for dv2 job {self.dv2_job[0].job_id} to complete")
            self.wait_for_jobs(self.dv2_job)
            self.log.info(f"Running First INCR Quick DV2 job on store {self.store_obj.store_id}")
            self.dv2_job[0] = self.store_obj.run_ddb_verification(incremental_verification=True, quick_verification=True)
            self.log.info(f"First INCR Quick DV2 jobid: {self.dv2_job[0].job_id}")
            # Get CVODS PID for 2nd incremental DV2 Job
            self.dv2_pid2 = self.get_cvods_pid(self.dv2_job[0].job_id, log_string, True)
            self.log.info(f"CVODS PID for First INCR Quick DV2 job: {self.dv2_pid2}")

            # Kill the auxcopy job as it is not needed. Check if Auxcopy job is running or not first
            if self.aux_copy_job.status.lower() in 'completed' or self.aux_copy_job.status.lower() in 'killed' or self.aux_copy_job.status.lower() in 'failed':
                self.log.info(f"Auxcopy job already completed")
            else:
                self.log.info(f"Killing Auxcopy Job {self.aux_copy_job.job_id}")
                self.aux_copy_job.kill(wait_for_job_to_kill=True)
            # Wait for DV2 job to complete
            self.wait_for_jobs(self.dv2_job)
            # Do validations
            self.do_validations(copy_id)
        except Exception as exp:
            self.log.error(f"Failing test case : Error Encountered {str(exp)}")
            self.status = constants.FAILED
            self.result_string = str(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Performing Unconditional Cleanup")
        self.cleanup()



