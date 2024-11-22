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

    cleanup()       --  cleanup the entities created in this/previous run

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample JSON:
    "47528": {
        "ClientName": "Name of Client",
        "PrimaryCopyMediaAgent": "Name of Source MA",
        "SecondaryCopyMediaAgent": "Name of Destination MA",
        "AgentName": "File System"
    }
    Note: Both the MediaAgents can be the same machine

Steps:

1: Configure the environment: create a pool, plan-with a Primary, 2 Secondary Copies,
                              (Source for Secondary Copy2 should be Secondary Copy1)
                              a BackupSet,a SubClient

2: Submit 2 Full Backups and run AuxCopy to Secondary Copy1

3: Seal the store, pick the jobs for recopy and run AuxCopy to Secondary Copy1 again

4: Prune and run DataAging for Backup Job1 on Copy1

5: Validate that same Enc.Key is used for recopy

6: Run AuxCopy to Secondary Copy2 and then Restore jobs from both the copies(Complete Successfully)

7: CleanUp the Environment
"""
import time

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
        self.name = 'Scenario where there is arch.File with two Enc.keys in archfilesidbkeys table'
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None,
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
        self.restore_path = None
        self.copy_ddb_path = None
        self.copy_ddb_path_2 = None
        self.subclient = None
        self.backupset = None
        self.copy_name = None
        self.pool_name = None
        self.pool_name_2 = None
        self.plan = None
        self.subclient_name = None
        self.backupset_name = None
        self.plan_name = None

    def setup(self):
        """Setup function of this test case"""
        utility = OptionsSelector(self.commcell)
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        self.ma_machine_1, self.ma_1_path = self.mm_helper.generate_automation_path(self.tcinputs['PrimaryCopyMediaAgent'], 25*1024)
        self.ma_machine_2, self.ma_2_path = self.mm_helper.generate_automation_path(self.tcinputs['SecondaryCopyMediaAgent'], 25*1024)
        self.client_machine, self.client_path = self.mm_helper.generate_automation_path(self.client.client_name, 25*1024)
        self.ddb_path = self.ma_machine_1.join_path(self.ma_1_path, 'DDB')
        self.ddb_path_2 = self.ma_machine_1.join_path(self.ma_1_path, 'DDB2')
        self.mount_path = self.ma_machine_1.join_path(self.ma_1_path, 'MP')
        self.mount_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'MP2')
        self.copy_ddb_path = self.ma_machine_2.join_path(self.ma_2_path, 'copy_DDB')
        self.copy_ddb_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'copy_DDB2')
        self.content_path = self.client_machine.join_path(self.client_path, 'Content')
        self.restore_path = self.client_machine.join_path(self.client_path, 'Restores')
        self.copy_name = str(self.id) + '_Copy'
        self.pool_name = str(self.id) + '_Pool'
        self.pool_name_2 = self.pool_name + '_2'
        self.backupset_name = str(self.id) + '_BS'
        self.subclient_name = str(self.id) + '_SC'
        self.plan_name = str(self.id) + '_Plan'

    def cleanup(self):
        """Cleanup the entities created in this/Previous Run"""
        try:
            self.log.info("********************** CLEANUP STARTING *************************")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            self.mm_helper.remove_content(self.restore_path, self.client_machine, suppress_exception=True)

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                self.subclient = self.backupset.subclients.get(self.subclient_name)
                if self.backupset.subclients.has_subclient(self.subclient_name):
                    self.subclient.plan = None
                self.log.info(f"Deleting backupset {self.backupset_name}")
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

            self.log.info("********************** CLEANUP COMPLETED *************************")
        except Exception as exe:
            self.log.warning(f'ERROR in Cleanup. Might need to Cleanup Manually: {exe}')

    def run(self):
        """Run Function of this case"""
        self.log.info("Initiating Previous Run Cleanup")
        self.cleanup()
        try:
            # 1: Configure the environment
            self.log.info('Setting Client Properties for Encryption on Client (BlowFish, 256)')
            self.client.set_encryption_property('ON_CLIENT', 'BlowFish', '256')
            self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                      self.content_path, 0.5)

            # adding storage pools
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

            storage_policy_copies = [self.plan.storage_policy.get_copy('Primary')]
            for index in range(1, 3):
                storage_policy_copies.append(self.dedupe_helper.configure_dedupe_secondary_copy(
                    self.plan.storage_policy,
                    self.copy_name + str(index),
                    self.pool_name_2,
                    self.tcinputs['SecondaryCopyMediaAgent'],
                    self.copy_ddb_path + str(index),
                    self.tcinputs['SecondaryCopyMediaAgent']))

            # set copy1 as source for copy2
            source = {'copyId': int(storage_policy_copies[1].copy_id),
                      'copyName': self.copy_name + str(1)}
            storage_policy_copies[2]._copy_properties['sourceCopy'] = source
            storage_policy_copies[2]._set_copy_properties()

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

            # Remove Association with System Created AutoCopy Schedule
            for index in range(1, 3):
                self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name,
                                                        self.copy_name + str(index))

            # 2: Submit 2 Full Backups and run AuxCopy to Secondary Copy1
            self.log.info('Submitting 2 FULL Backups and AuxCopy to copy1')
            backup_job_1 = self.subclient.backup(backup_level='Full')
            if not backup_job_1.wait_for_completion():
                raise Exception(f'Backup Job {backup_job_1.job_id} Failed with JPR: {backup_job_1.delay_reason}')
            self.log.info(f'Backup Job 1 Completed Id : {backup_job_1.job_id}')
            time.sleep(60)
            backup_job_2 = self.subclient.backup(backup_level='Full')
            if not backup_job_2.wait_for_completion():
                raise Exception(f'Backup Job {backup_job_2.job_id} Failed with JPR: {backup_job_2.delay_reason}')
            self.log.info(f'Backup Job 2 Completed Id : {backup_job_2.job_id}')
            time.sleep(60)


            aux_copy_job = self.plan.storage_policy.run_aux_copy(self.copy_name + str(1),
                                                            use_scale=True, all_copies=False)
            if aux_copy_job.wait_for_completion():
                self.log.info(f'AuxCopy Job Completed (Id: {aux_copy_job.job_id})')
            else:
                raise Exception(f'AuxCopy Job {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')

            # 3: Seal the store, pick the jobs for recopy and run AuxCopy to Secondary Copy1 again
            self.log.info('Sealing the store, pick for Re-Copy and run AuxCopy again')
            self.plan.storage_policy.seal_ddb(self.copy_name + str(1))
            storage_policy_copies[1].recopy_jobs(backup_job_1.job_id)
            storage_policy_copies[1].recopy_jobs(backup_job_2.job_id)

            aux_copy_job = self.plan.storage_policy.run_aux_copy(self.copy_name + str(1),
                                                            use_scale=True, all_copies=False)
            if aux_copy_job.wait_for_completion():
                self.log.info(f'2nd AuxCopy Job(Re-Copy): {aux_copy_job.job_id} Completed')
            else:
                raise Exception(f'2nd Aux Copy Job(Re-Copy) {aux_copy_job.job_id}'
                                f' Failed with JPR: {aux_copy_job.delay_reason}')

            # 4: Prune and run DataAging for Backup Job1 on Copy1
            self.log.info('Prune and run DataAging for Backup Job1 on Copy1')
            command = 'qoperation agedata -delbyjobid -j {0} -sp {1} -spc {2} -ft {3}'
            command = command.format(backup_job_1.job_id, self.plan.storage_policy.storage_policy_name,
                                     self.copy_name + str(1), 'Q_DATA')
            self.log.info(f'QCommand: {command}')
            response = self.commcell.execute_qcommand(command)
            self.log.info(f'Response: {response}')
            self.log.info('Prune completed')

            aging_job = self.commcell.run_data_aging(self.copy_name + str(1),
                                                     self.plan.storage_policy.storage_policy_name,
                                                     is_granular=True,
                                                     include_all_clients=True,
                                                     select_copies=True,
                                                     prune_selected_copies=True)
            if aging_job.wait_for_completion():
                self.log.info(f'Data Aging Job Completed: {aging_job.job_id}')
            else:
                raise Exception(f'Data Aging Job {aging_job.job_id} Failed with JPR: {aging_job.delay_reason}')

            # 5: Validate that same Enc.Key is used for recopy
            self.log.info('Validate: All archFiles in archfileSIDBKeys table refer same Enc.KeyID')
            query = '''select distinct encKeyID from archFileSIDBKeys
                    where archCopyId = %s''' % storage_policy_copies[1].copy_id
            self.log.info(f'Query: {query}')
            self.csdb.execute(query)
            result = self.csdb.fetch_all_rows()
            self.log.info(f"Result: {result}")
            if len(result) == 1:
                self.log.info('Validation Succeeded')
            else:
                self.log.error('Validation Failed')

            # 6: Run AuxCopy to Secondary Copy2 and then Restore jobs from both the copies
            self.log.info('Running AuxCopy to Copy2')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(self.copy_name + str(2),
                                                            use_scale=True, all_copies=False)
            if aux_copy_job.wait_for_completion():
                self.log.info(f'AuxCopy Job to Copy2: {aux_copy_job.job_id} Completed')
            else:
                raise Exception(f'Aux Copy Job to Copy2: {aux_copy_job.job_id}'
                                f' Failed with JPR: {aux_copy_job.delay_reason}')

            restores_jobs = []
            for index in range(1, 3):
                job = self.subclient.restore_out_of_place(self.client.client_name,
                                                          self.client_machine.join_path(
                                                              self.restore_path, str(index - 1)),
                                                          [self.content_path],
                                                          copy_precedence=index)
                restores_jobs.append(job)

            for job in restores_jobs:
                if job.wait_for_completion():
                    self.log.info(f'Restore Job: {job.job_id} Completed')
                else:
                    raise Exception(f'Restore job {job.job_id} Failed with JPR: {job.delay_reason}')
                time.sleep(60)

            self.log.info('Validating Restored Data from 2 Copies')
            for index in range(1, 3):
                restored_path = self.client_machine.join_path(self.restore_path, str(index-1), 'Content')
                difference = self.client_machine.compare_folders(self.client_machine,
                                                                 self.content_path,
                                                                 restored_path)
                if difference:
                    raise Exception(f'Validating Data restored from Copy %s Failed' % index)
            self.log.info('Validation SUCCESS')
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error(f'Exception Occurred: {exe}')

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 7: CleanUp the Environment
        self.log.info('reverting Client Enc.properties to default use sp_settings')
        self.client.set_encryption_property()
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
