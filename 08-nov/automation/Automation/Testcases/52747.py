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

    cleanup()       --  cleanup the entities created in this/previous runs

    run()           --  run function of this test case

    run_validations --  runs the required validations for the case

    tear_down()     --  tear down function of this test case

Sample JSON:
    "52747": {
        "ClientName": "Name of Client",
        "PrimaryCopyMediaAgent": "Name of Source MA",
        "SecondaryCopyMediaAgent": "Name of Destination MA",
        "AgentName": "File System"
    }
    Note: Both the MediaAgents can be the same machine

Steps:

1: Configure the environment: create a pool, Plan-with Primary, Secondary Copy,
                              a BackupSet,a SubClient

2: Run Multiple Backups: More than 10 (as min. value for Batching jobs is 10)

3: Run AuxCopy with total_jobs_to_process as 10

4: While AuxCopy is running, Verify whether Batching worked as expected
   (should not copy more than 10 jobs simultaneously)

5: CleanUp the environment
"""

import time
from AutomationUtils import constants
from cvpysdk.exception import SDKException
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
        self.name = 'Batching with number of jobs picked to process for dash copy'
        self.tcinputs = {
            "AgentName": None,
            "ClientName": None,
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
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
        self.copy_name = None
        self.pool_name = None
        self.pool_name_2 = None
        self.subclient_name = None
        self.backupset_name = None
        self.plan_name = None

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.tcinputs['ClientName'], self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs['PrimaryCopyMediaAgent'], self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        utility = OptionsSelector(self.commcell)
        client_drive = utility.get_drive(self.client_machine, 25*2014)
        primary_ma_drive = utility.get_drive(self.ma_machine_1, 25*1024)
        secondary_ma_drive = utility.get_drive(self.ma_machine_2, 25*1024)
        self.client_path = self.client_machine.join_path(client_drive, f'test_{str(self.id)}')
        self.ma_1_path = self.ma_machine_1.join_path(primary_ma_drive, f'test_{str(self.id)}')
        self.ma_2_path = self.ma_machine_2.join_path(secondary_ma_drive + f'test_{str(self.id)}')
        self.ddb_path = self.ma_machine_1.join_path(self.ma_1_path, 'DDB')
        self.ddb_path_2 = self.ma_machine_1.join_path(self.ma_1_path, 'DDB2')
        self.mount_path = self.ma_machine_1.join_path(self.ma_1_path, 'MP')
        self.mount_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'MP2')
        self.copy_ddb_path = self.ma_machine_2.join_path(self.ma_2_path, 'copy_DDB')
        self.copy_ddb_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'copy_DDB2')
        self.content_path = self.client_machine.join_path(self.client_path, 'Content')
        self.copy_name = str(self.id) + '_Copy'
        self.pool_name = str(self.id) + '_Pool'
        self.pool_name_2 = self.pool_name + '_2'
        self.backupset_name = str(self.id) + '_BS'
        self.subclient_name = str(self.id) + '_SC'
        self.plan_name = str(self.id) + '_Plan'
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def cleanup(self):
        """Cleanup the entities created in this/Previous Run"""
        try:
            self.log.info("****************************** Cleanup Started ******************************")
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                self.subclient = self.backupset.subclients.get(self.subclient_name)
                if self.backupset.subclients.has_subclient(self.subclient_name):
                    self.subclient.plan = None
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Deleting plan  %s", self.plan_name)
                self.commcell.plans.delete(self.plan_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info("Deleting pool  %s", self.pool_name)
                self.commcell.storage_pools.delete(self.pool_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name_2):
                self.log.info("Deleting pool  %s", self.pool_name_2)
                self.commcell.storage_pools.delete(self.pool_name_2)

            self.log.info('****************************** Cleanup Completed ******************************')
        except Exception as exe:
            self.log.warning('ERROR in Cleanup. Might need to Clean Manually: %s', str(exe))

    def run(self):
        """Run Function of this case"""
        try:
            self.log.info("Cleaning up the entities from older runs")
            self.cleanup()
            # 1: Configure the environment
            self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'],
                                                      self.content_path, 0.4)
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

            self.log.info(f"Adding the secondary copy [{self.copy_name}]")
            self.plan.add_storage_copy(self.copy_name, self.pool_name_2)
            self.log.info(f"secondary copy [{self.copy_name}] added.")

            # remove association for storage_policy with system created auto copy schedule
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.copy_name)

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

            # 2: Run Multiple Backups
            self.log.info('Running Full Backup')
            self.run_backup('Full')

            self.log.info('Running 15 Incremental Backups')
            for _ in range(1, 16):
                self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'],
                                                          self.content_path, 0.1)
                self.run_backup("Incremental")
                time.sleep(60)

            # 3: Run AuxCopy with total_jobs_to_process as 10
            self.log.info('Running AuxCopy Job(jobs to process = 10)')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(total_jobs_to_process=10)

            self.log.info('AuxCopy Job Initiated(Id: %s)', aux_copy_job.job_id)

            # 4: While AuxCopy is running, Verify whether Batching worked as expected
            secondary_copy = self.plan.storage_policy.get_copy(self.copy_name)
            self.run_validations(aux_copy_job, secondary_copy)

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
        if job.wait_for_completion():
            self.log.info('%s Backup job Completed(Id: %s)', backup_type, job.job_id)
        else:
            raise Exception('%s Backup Job Failed(Id: %s) with JPR: %s' % (backup_type, job.job_id, job.delay_reason))

    def run_validations(self, aux_copy_job, storage_policy_copy):
        """Runs the Validations for the Case
                Args:
                        aux_copy_job          (object)  --   Object of Job Class for AuxCopy Job

                        storage_policy_copy   (object)  --   Object of StoragePolicyCopy Class

        """
        self.log.info('**************************** VALIDATIONS *********************************')
        self.log.info('*** CASE 1: Verify No. of Jobs Picked simultaneously always <= 10***')
        query = '''select count(distinct BackupJobID)
                from ArchChunkToReplicate where AdminJobID = {0}
                '''.format(aux_copy_job.job_id)
        self.log.info('Query: %s', query)
        job_status = ['pending', 'running', 'waiting']
        elapsed_time = 1800
        while aux_copy_job.status.lower() in job_status and elapsed_time > 0:
            self.csdb.execute(query)
            row = self.csdb.fetch_one_row()
            if int(row[0]) <= 10:
                self.log.info('Result: Jobs Picked for AuxCopy are %s', str(row[0]))
            else:
                self.status = constants.FAILED
                self.log.error('ERROR Result: Jobs Picked for AuxCopy > 10:  %s', str(row[0]))
            time.sleep(20)
            elapsed_time -= 20
        if aux_copy_job.status != 'Completed':
            aux_copy_job.kill()
            raise Exception('AuxCopy Job Killed - Run > 30 minutes:Id:  %s' % aux_copy_job.job_id)

        # AuxCopy Completes by now: Run other Validations
        self.log.info('*** CASE 2: Verify All Jobs are copied ***')

        query = '''select count(jobId) from JMJobDataStats
                where status in(101,102,103) and archGrpCopyId = {0}
                '''.format(storage_policy_copy.copy_id)
        self.log.info('Query: %s', query)
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info('Result: %s', str(row))
        if int(row[0]) == 0:
            self.log.info('SUCCESS Result: Remaining Jobs are Copied')
        else:
            self.status = constants.FAILED
            self.log.error('ERROR Result: Still some Jobs are not copied')

        # commenting this validation, as batching doesnt honor this option. This option is honored during initial
        # design of batching where *JM launches a new AuxCopy job for next batch of Jobs to be copied*. Now it simply
        # does a re-population of next set of jobs for the same auxcopy job
        # 4007  #define JM_RESUBMIT_JOB_ON_COMPLETION           69
        # 4008  #define JM_RESUBMIT_JOB_ON_COMPLETION_NAME      "Resubmit job on completion"
        #
        # validation3 = 'Verify from JMJobOptions that options are set to '
        # validation3 += 'populate job list & resubmit aux copy on completion'
        # self.log.info('*** CASE 3: %s ***', validation3)
        # query = '''select distinct jobId from JMJobOptions
        #         where attributeId in (69,70) and JobId = {0}
        #         '''.format(aux_copy_job.job_id)
        # self.log.info('Query: %s', query)
        # self.csdb.execute(query)
        # row = self.csdb.fetch_one_row()
        # if int(row[0]) == int(aux_copy_job.job_id):
        #     self.log.info('SUCCESS Result: Validation Succeeded')
        # else:
        #     self.status = constants.FAILED
        #     self.log.error('ERROR Result: Validation Failed')

        self.log.info('*** CASE 3: Verify from TM_JobOptions - Count of Jobs to process ***')
        query = '''select value from TM_JobOptions
                where optionId = 1654993746 and JobId = {0}
                '''.format(aux_copy_job.job_id)
        self.log.info('Query: %s', query)
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info('Result: %s', str(row))
        if int(row[0]) == 10:
            self.log.info('SUCCESS Result: Validation passed')
        else:
            self.status = constants.FAILED
            self.log.error('ERROR Result: %s: Validation Failed', row[0])
        self.log.info('************************ VALIDATIONS  Completed *****************************')

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 5: CleanUp the environment
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
