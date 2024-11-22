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

    cleanup()       --  cleans up the entities

    run()           --  run function of this test case

    create_resources()   --  creates resources for the TC

    gen_content()   -- genarte content for backup

    run_backup()   -- run backups

    run_validations --  runs the required validations for the case

    tear_down()     --  tear down function of this test case

    get_sidb_store() -- Get SIDB store for the storage pool


Inputs to be passed in JSON File:

    "64250": {
        "ClientName"    : "Name of a Client - Content to be BackedUp will be created here",
        "AgentName"     : "File System",
        "MediaAgentName": "Name of a MediaAgent - we create Library, DDBs here"
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
                            - (Mandatory for Linux MA for creating snapshots with LVM)
    }

Steps:

1: Configure the environment: create a library,Storage Policy, a BackupSet,a SubClient

2: Run Multiple Backups: More than 10 (as min. value for Batching jobs is 10)

3: Run DV2 with total_jobs_to_process as 10

4: While DV2 is running, Verify whether Batching worked as expected
   Validations:
   - No. of Jobs Picked simultaneously <= 10 when dv2 is running: distinct BackupJobId in archChunkToVerify2
   - All Jobs are verified when dv2 is completed: archCheckStatus 5(verified) in JMJobDataStats
   - No Chunks are marked as bad for the store: archChunkDDBDrop table entries
   - TM_JobOptions is set correctly: Option 1654993746 set to 10

5: CleanUp the environment

"""

import time
from AutomationUtils import constants
from cvpysdk import deduplication_engines
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
        self.name = 'Batching with number of jobs picked to process for DV2'
        self.tcinputs = {
            "MediaAgentName": None,
            "ClientName": None
        }
        self.client_name = None
        self.dedup_path = None
        self.mount_path = None
        self.content_path = None
        self.subclient = None
        self.subclient_name = None
        self.backupset_name = None
        self.bkpset_obj = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.store_obj = None
        self.pool_name = None
        self.plan_name = None
        self.plan = None
        self.option_obj = None
        self.ma_name = None
        self.client_machine_obj = None
        self.ma_machine_obj = None
        self.client_drive = None
        self.ma_drive = None
        self.media_agent_obj = None
        self.mmhelper_obj = None
        self.deduphelper_obj = None
        self.ddbma_object = None
        self.pool_obj = None
        self.status = constants.PASSED

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

        self.client_drive = self.option_obj.get_drive(self.client_machine_obj, 30 * 1024)
        if not self.is_user_defined_mp:
            self.ma_drive = self.option_obj.get_drive(self.ma_machine_obj, 30 * 1024)

        self.pool_name = f"STORAGEPOOL_{self.id}_{self.ma_name}"
        self.plan_name = f"PLAN_{self.id}_{self.ma_name}"

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_mp:
            self.mount_path = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"), f"TC_{self.id}", f"LIB_{suffix}")
            self.log.info(f"Using user provided mount path {self.mount_path}")
        else:
            self.mount_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"LIB_{suffix}")

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

    def cleanup(self):
        """CleansUp the Entities"""
        self.log.info('************************ Clean Up Started *********************************')
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
        except Exception as exe:
            self.log.warning("ERROR in Cleanup. Might need to Cleanup Manually: %s", str(exe))

    def create_resources(self):
        """Create resources needed by the Test Case"""
        # Configure the environment
        # Create a storage pool
        if not self.commcell.storage_pools.has_storage_pool(self.pool_name):
            self.log.info(f"Creating Storage Pool - {self.pool_name}")
            self.pool_obj = self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                                            self.ma_name, [self.ma_name] * 2,
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
        # Create subclient
        self.subclient = self.bkpset_obj.subclients.add(self.subclient_name)
        self.subclient.plan = [self.plan, [self.content_path]]

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

    def run(self):
        """Run Function of this case"""
        try:
            self.log.info("Initiating previous run cleanup")
            self.cleanup()
            self.create_resources()
            copy_id = self.plan.storage_policy.get_copy('Primary').copy_id

            # 2: Run Multiple Backups
            self.gen_content(self.client.client_name, self.content_path, 0.4)
            self.log.info('Running Full Backup')
            self.run_backup('Full')

            self.log.info('Running 20 Incremental Backups')
            for index in range(1, 21):
                self.gen_content(self.client.client_name, self.content_path, 0.1)
                self.run_backup("Incremental")

            # 3: Run DV2 with total_jobs_to_process as 10
            self.log.info('Running DV2 Job(jobs to process = 10)')
            self.get_sidb_store()
            dv2_job = self.store_obj.run_ddb_verification(incremental_verification=False, quick_verification=False, total_jobs_to_process=10)
            self.log.info('DDB Verification Job Initiated(Id: %s)', dv2_job.job_id)

            # 4: While DV2 is running, Verify whether Batching worked as expected
            self.run_validations(dv2_job, copy_id)
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('Test Case Failed with Exception : %s', str(exe))

    def run_backup(self, backup_type):
        """Runs Backup of specified type and waits for job till it completes
                Args:
                        backup_type    (str)  --   Type of backup To Run
        """
        job = self.subclient.backup(backup_level=backup_type)
        self.log.info("%s Backup Job Initiated(Id: %s)", backup_type, job.job_id)
        if job.wait_for_completion():
            self.log.info('%s Backup job Completed(Id: %s)', backup_type, job.job_id)
        else:
            raise Exception(f'{backup_type} Backup Job Failed(Id:{job.job_id}) with JPR: {job.delay_reason}')

    def run_validations(self, dv2_job, copy_id):
        """Runs the Validations for the Case
            Args:
                    dv2_job (object)  --   Job Object for DDB Verification job

                    copy_id (str)  --   copy id
        """
        self.log.info("Waiting for DV2 job to Get to Phase 2 - Verify Data")
        elapsed_time = 1200
        while dv2_job.phase.lower() != 'verify data' and elapsed_time > 0:
            time.sleep(5)
            elapsed_time -= 5
        if elapsed_time <= 0:
            dv2_job.kill()
            raise Exception(f"DDB Verification Job(Id: {dv2_job.job_id}) Killed - Phase 2 isn't started in 20 minutes")

        self.log.info('**************************** VALIDATIONS *********************************')
        error_string = []

        self.log.info('*** CASE 1: Verify No. of Jobs Picked simultaneously always <= 10***')

        query = '''select count(distinct BackupJobId)
                from ArchChunkToVerify2 where AdminJobId = {0}
                '''.format(dv2_job.job_id)
        self.log.info('Query: %s', query)
        job_status = ['pending', 'running', 'waiting']
        elapsed_time = 1800
        while dv2_job.status.lower() in job_status and elapsed_time > 0:
            self.csdb.execute(query)
            row = self.csdb.fetch_one_row()
            if int(row[0]) <= 10:
                self.log.info('Result: Jobs Picked for DDB Verification are %s', str(row[0]))
            else:
                self.log.error('ERROR Result: Jobs Picked for DDB Verification > 10:  %s', str(row[0]))
                error_string.append('Jobs Picked for DDB Verification > 10:  %s' % str(row[0]))
                break
            time.sleep(5)
            elapsed_time -= 5
        if dv2_job.status.lower() != 'completed':
            dv2_job.kill()
            raise Exception(f'DDB Verification Job Killed - Run > 30 minutes:Id: {dv2_job.job_id}')

        # DV2 Completes by now: Run other Validations
        self.log.info('*** CASE 2: Check All Jobs are verified ***')

        query = f"select count(jobId) from JMJobDataStats where archCheckStatus <> 5 and archGrpCopyId = {copy_id}"
        self.log.info(f"Query: {query}")
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(f"Result: {str(row)}")
        if int(row[0]) == 0:
            self.log.info('SUCCESS Result: All Jobs are Verified')
        else:
            self.log.error('ERROR Result: Some Jobs are left unVerified')
            error_string.append('Some Jobs are left unVerified')

        self.log.info('*** CASE 3: Check All Jobs are picked and verified ***')

        query = f"select count(distinct BackupJobId) from ArchChunkToVerify2History where AdminJobId = {dv2_job.job_id}"
        self.log.info(f"Query: {query}")
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(f"Result: {str(row)}")
        if int(row[0]) == 21:
            self.log.info('SUCCESS Result: All Jobs are picked and verified')
        else:
            self.log.error('ERROR Result: Some Jobs are not picked for Verification')
            error_string.append('Some Jobs are not picked for Verification')

        self.log.info('*** CASE 4: Verify no chunks are marked as bad ***')

        chunks = self.mmhelper_obj.get_bad_chunks(job_id=dv2_job.job_id, log_chunks=True)
        if not chunks:
            self.log.info('SUCCESS Result: No chunks are marked as bad')
        else:
            self.log.error('ERROR Result: Some chunks are marked bad')
            error_string.append('Some chunks are marked bad')

        self.log.info('*** CASE 5: Verify from TM_JobOptions - Count of Jobs to process ***')
        query = f"select value from TM_JobOptions where optionId = 1654993746 and JobId = {dv2_job.job_id}"
        self.log.info('Query: %s', query)
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info("Result: %s", str(row))
        if int(row[0]) == 10:
            self.log.info("SUCCESS Result: TM_JobOptions is set correctly to 10")
        else:
            self.log.error(f"ERROR Result: TM_JobOptions is set incorrectly to {row[0]}")
            error_string.append(f"TM_JobOptions is set incorrectly to % {row[0]}")
        if error_string:
            raise Exception(str(error_string))

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 5: CleanUp the environment
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED')
        else:
            self.log.warning('Test Case FAILED. Please review the TC and Commcell logs')
        self.cleanup()
