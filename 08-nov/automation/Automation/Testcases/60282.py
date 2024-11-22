# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    run_validations --  runs the required validations for the case

    tear_down()     --  tear down function of this test case

Inputs to be passed in JSON File:
    "60282": {
        "ClientName": "Name of client",
        "AgentName": "File System",
        "PrimaryCopyMediaAgent":"MA to host Primary Copy",
        "SecondaryCopyMediaAgent":"MA to host Secondary Copy"
    }
    Note: Both the MediaAgents can be the same machine

Steps:

1: Configure the environment: create a pool, plan-with Primary, Secondary Copy,
                              a BackupSet,a SubClient
    - Disable Space-Optimized Auxillary Copy and Copy First Full for SubClient

2: Run Multiple Backups: More than 10 (as min. value for Batching jobs is 10)

3: Run AuxCopy with Batching disabled

4: While AuxCopy is running, using archChunkToReplicate
   verify whether all jobs on source are picked for copy since batching is disabled

5: Other Validations:
    - value of option(1654993746) in TM_JobOptions should be 0
    - no jobs remain in to be copied state in JMJobDataStats after the auxillary copy completes
    - size of archive files in archFileCopy match on source and destination copies
6: CleanUp the environment
"""
import time

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = 'Auxcopy without batching'
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
        self.utility = None
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ddb_path = None
        self.ddb_path_2 = None
        self.ma_1_path = None
        self.ma_2_path = None
        self.mount_path = None
        self.client_path = None
        self.mount_path_2 = None
        self.content_path = None
        self.copy_ddb_path = None
        self.copy_ddb_path_2 = None
        self.subclient = None
        self.backupset = None
        self.plan = None
        self.secondary_copy = None
        self.copy_name = None
        self.pool_name = None
        self.pool_name_2 = None
        self.subclient = None
        self.backupset = None
        self.subclient_name = None
        self.backupset_name = None
        self.plan_name = None

    def setup(self):
        """Setup function of this test case"""
        self.copy_name = f'{self.id}_Copy'
        self.pool_name = f'{self.id}_Pool'
        self.pool_name_2 = self.pool_name + '_2'
        self.backupset_name = f'{self.id}_BS'
        self.subclient_name = f'{self.id}_SC'
        self.plan_name = f'{self.id}_Plan'

        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

        self.client_machine, self.client_path = self.mm_helper.generate_automation_path(self.tcinputs['ClientName'], 25*1024)
        self.ma_machine_1, self.ma_1_path = self.mm_helper.generate_automation_path(self.tcinputs['PrimaryCopyMediaAgent'], 25*1024)
        self.ma_machine_2, self.ma_2_path = self.mm_helper.generate_automation_path(self.tcinputs['SecondaryCopyMediaAgent'], 25*1024)
        self.ddb_path = self.ma_machine_1.join_path(self.ma_1_path, 'DDB')
        self.ddb_path_2 = self.ma_machine_1.join_path(self.ma_1_path, 'DDB2')
        self.mount_path = self.ma_machine_1.join_path(self.ma_1_path, 'MP1')
        self.mount_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'MP2')
        self.copy_ddb_path = self.ma_machine_2.join_path(self.ma_2_path, 'copy_DDB')
        self.copy_ddb_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'copy_DDB2')
        self.content_path = self.client_machine.join_path(self.client_path, 'Content')

    def run(self):
        """Run Function of this case"""
        self.log.info("Initiating Previous Run Cleanup")
        self.cleanup()
        try:
            # 1: Configure the environment
            self.log.info('Disabling AuxCopy Config: Copy first full for new SubClient')
            self.mm_helper.update_mmconfig_param('MMCONFIG_AUXCOPY_COPY_FIRST_FULL_FOR_NEW_SUBCLIENT', 0, 0)

            # creating storage pools
            self.log.info(f"Creating the pool [{self.pool_name}]")
            self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                            self.tcinputs['PrimaryCopyMediaAgent'],
                                            [self.tcinputs['PrimaryCopyMediaAgent'], self.tcinputs['PrimaryCopyMediaAgent']],
                                            [self.ddb_path, self.ddb_path_2])
            self.log.info(f"Pool [{self.pool_name}] Created.")

            self.log.info(f"Creating the pool [{self.pool_name_2}]")
            self.commcell.storage_pools.add(self.pool_name_2, self.mount_path_2,
                                            self.tcinputs['SecondaryCopyMediaAgent'],
                                            [self.tcinputs['SecondaryCopyMediaAgent'], self.tcinputs['SecondaryCopyMediaAgent']],
                                            [self.copy_ddb_path, self.copy_ddb_path_2])
            self.log.info(f"Pool [{self.pool_name_2}] Created.")

            self.commcell.storage_pools.refresh()
            self.commcell.plans.refresh()

            # creation of plan
            self.log.info(f"Plan Present: {self.commcell.plans.has_plan(self.plan_name)}")
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.commcell.plans.refresh()
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")

            # disabling the schedule policy
            self.log.info('Disabling the schedule policy')
            self.plan.schedule_policies['data'].disable()

            # adding a opy to the plan
            self.log.info("Adding the secondary copy")
            self.plan.add_storage_copy(self.copy_name, self.pool_name_2)
            self.log.info("Added the secondary copy")

            # add backupset
            self.log.info(f"Adding the backup set [{self.backupset_name}]")
            self.backupset = self.mm_helper.configure_backupset(self.backupset_name)
            self.log.info(f"Backup set Added [{self.backupset_name}]")

            # add subclient
            self.log.info(f"Adding the subclient set [{self.subclient_name}]")
            self.subclient = self.backupset.subclients.add(self.subclient_name)
            self.log.info(f"Subclient set Added [{self.subclient_name}]")

            # Add plan and content to the subclient
            self.log.info("Adding plan to subclient")
            self.subclient.plan = [self.plan, [self.content_path]]

            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.copy_name)

            self.secondary_copy = self.plan.storage_policy.get_copy(self.copy_name)

            # Disable Space Optimized Auxillary Copy
            self.secondary_copy.space_optimized_auxillary_copy = False

            self.log.info('Running 15 Full Backups')
            for iteration in range(1, 16):
                self.run_backup("Full", iteration)
                time.sleep(60)

            # 3: Run AuxCopy with batching disabled
            self.log.info('Running AuxCopy Job with batching disabled(jobs to process = 0)')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(streams=1, total_jobs_to_process=0)
            self.log.info(f'AuxCopy Job Initiated(Id: {aux_copy_job.job_id}). Waiting for it to get to running state')
            timeout = 600
            while aux_copy_job.status.lower() != 'running' and timeout > 0:
                timeout -= 1
                time.sleep(1)
            if timeout <= 0:
                raise Exception(f"AuxCopy Job(Id: {aux_copy_job.job_id}) didn't get to running state in 10 mins")

            # 4: While AuxCopy is running, Verify whether Batching worked as expected
            time.sleep(5)
            self.run_validations(aux_copy_job)

        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error(f'Test Case Failed with Exception : {exe}')

    def run_backup(self, backup_type, iteration):
        """Runs Backup of specified type and waits for job till it completes
        Args:
            backup_type    (str)  --   Type of backup To Run

            iteration       (int) --   Iteration of Current Backup Job among 15 jobs
        """
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)
        self.mm_helper.create_uncompressable_data(self.client_machine,
                                                  self.content_path, 0.5)
        job = self.subclient.backup(backup_level=backup_type)
        self.log.info(f'Backup Job(%d) Initiated. Job Id: {job.job_id}')
        if not job.wait_for_completion():
            raise Exception(f'Backup Job {job.job_id} Failed with JPR: {job.delay_reason}')
        self.log.info(f'Backup job(Id: {job.job_id}) Completed')

    def run_validations(self, aux_copy_job):
        """Runs the Validations for the Case
        Args:
            aux_copy_job          (object)  --   Object of Job Class for AuxCopy Job
        """
        result_string = ''
        self.log.info('**************************** VALIDATIONS *********************************')
        self.log.info('*** CASE 1: Verify No. of Jobs Picked simultaneously is 15(total jobs)***')
        query = '''select count(distinct BackupJobID)
                from ArchChunkToReplicate where AdminJobID = {0}
                '''.format(aux_copy_job.job_id)
        self.log.info(f'Query: {query}')
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(f'Result: {row}')
        if int(row[0]) == 15:
            self.log.info('SUCCESS Batching Validation PASSED')
        else:
            result_string = f'{result_string}[ERROR: Batching Validation FAILED]'
            self.log.error('ERROR: Batching Validation FAILED')

        self.log.info('*** CASE 2: Verify from TM_JobOptions - Count of Jobs to process = 0 ***')
        query = '''select value from TM_JobOptions
                where optionId = 1654993746 and JobId = {0}
                '''.format(aux_copy_job.job_id)
        self.log.info(f'Query: {query}')
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(f'Result: {row}')
        if int(row[0]) == 0:
            self.log.info('SUCCESS TM_JobOptions Validation PASSED')
        else:
            result_string = f'{result_string}[ERROR: TM_JobOptions Validation FAILED]'
            self.log.error('ERROR: TM_JobOptions Validation FAILED')

        self.log.info('Waiting for AuxCopy job to complete for further validations')
        if not aux_copy_job.wait_for_completion():
            raise Exception(f'{result_string}[AuxCopy Job(Id: {aux_copy_job.job_id}) Failed with JPR: {aux_copy_job.delay_reason}]')
        self.log.info(f'AuxCopy Job(Id: {aux_copy_job.job_id}) Completed')

        # AuxCopy Validations
        self.log.info('*** CASE 3: Verify All Jobs are copied ***')
        query = '''select count(jobId) from JMJobDataStats
                where status in(101,102,103) and archGrpCopyId = {0}
                '''.format(self.secondary_copy.copy_id)
        self.log.info(f'Query: {query}')
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(f'Result: {row}')
        if int(row[0]) == 0:
            self.log.info('SUCCESS Validation PASSED: All Jobs are Copied')
        else:
            result_string = f'{result_string}[ERROR: Validation FAILED: Some Jobs are not copied]'
            self.log.error('ERROR: Validation FAILED: Still some Jobs are not copied')

        self.log.info('*** CASE 4: Verify total size of archive files match on both copies ***')
        query = '''select archCopyId, sum(physicalSize)
                from archFileCopy
                where archCopyId in ({0},{1})
                group by archCopyId'''.format(self.secondary_copy.copy_id,
                                              self.plan.storage_policy.get_copy('Primary').copy_id)
        self.log.info(f'Query: {query}')
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info(f'Result: {rows}')
        if int(rows[0][1]) != int(rows[1][1]):
            result_string = f'{result_string}[ERROR: VALIDATION FAILED: Total Size of archFiles mismatch for the Copies]'
            self.log.error('ERROR: VALIDATION FAILED: Total Size of archFiles mismatch for the Copies')
        else:
            self.log.info('SUCCESS Validation PASSED: Size of archFiles matched on both Copies')

        if result_string:
            raise Exception(result_string)
        self.log.info('SUCCESS: ALL VALIDATIONS PASSED')

    def cleanup(self):
        """"CleanUp the Entities"""
        try:
            self.log.info("****************************** Cleanup Started ******************************")

            if self.client_machine.check_directory_exists(self.content_path):
                self.mm_helper.remove_content(self.content_path, self.client_machine)

            self.log.info(f"Deleting backupset: {self.backupset_name} if exists")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                self.subclient = self.backupset.subclients.get(self.subclient_name)
                if self.backupset.subclients.has_subclient(self.subclient_name):
                    self.subclient.plan = None
                self.log.info(f"Deleting backup set  {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info(f"Deleting plan  {self.plan_name}")
                self.commcell.plans.delete(self.plan_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info(f"Deleting pool  {self.pool_name}")
                self.commcell.storage_pools.delete(self.pool_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name_2):
                self.log.info(f"Deleting pool  {self.pool_name_2}")
                self.commcell.storage_pools.delete(self.pool_name_2)

            self.log.info('****************************** Cleanup Completed ******************************')
        except Exception as exe:
            self.log.warning(f'ERROR in Cleanup. Might need to Cleanup Manually: {exe}')

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 5: CleanUp the environment
        self.log.info('Enabling AuxCopy Config: Copy first full for new SubClient')
        self.mm_helper.update_mmconfig_param('MMCONFIG_AUXCOPY_COPY_FIRST_FULL_FOR_NEW_SUBCLIENT', 0, 1)
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
