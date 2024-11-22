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

    run()           --  run function of this test case

    get_copied_status() --  checks if backup job's are copied to secondary copy

    run_validations()   --  runs the validations

    tear_down()     --  tear down function of this test case

TcInputs to be passed in JSON File:
    "56489": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "PrimaryCopyMediaAgent":   Name of a MediaAgent machine - we create primary copy here
        "SecondaryCopyMediaAgent": Name of a MediaAgent machine - we create secondary copies here
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "pool_name"  : Name of Existing Library to be Used
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
        "copy_library_name" : Name of Existing Library to be Used for Secondary Copies
        "copy_mount_path"   : Path to be used as MP for Library for Secondary Copies
        "copy_dedup_path"   :  Path to be used for creating Dedupe-Partitions for Secondary Copies
    }
    ***** Note *****
    # 1: For linux MediaAgents(Primary/Secondary),
        User must explicitly provide a dedup path that is inside a Logical Volume with min 10% of free extents in VG.
        (LVM support required for DDB)]

   # 2   ***********************************
        if pool_name_given then reuse_pool
        else:
            if mountpath_location_given -> create_pool_with_this_mountpath
            else:
                auto_generate_mountpath_location
                create_pool_with_this_mountpath

        if dedup_path_given -> use_given_dedup_path
        else it will auto_generate_dedup_path
        ***********************************

    # 3: Both the MediaAgents can be the same machine

Steps:

1: Configure the environment: create a pool, plan-with Primary, Secondary Copy,
                              a BackupSet,a SubClient

2: Run 2 Full Backups

3: Validate System Created AutoCopy Schedule.
   Mark jobs on Copy2 to DoNotCopy. Schedule then copies to Copy1 and skips Copy2.

4: Validate User Created AuxCopy Schedule.
   Mark jobs on Copy1 to ReCopy. Schedule then copies to Copy1 and skips Copy2.

5: Validate User Created AuxCopy Schedule.
   Mark jobs on Copy1, Copy2 to ReCopy. Mark Copy2 as inactive.Schedule then copies to Copy1 and skips Copy2.

6: CleanUp the environment
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
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify System Created and User Created AuxCopy Schedules"
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
        self.mount_path = None
        self.client_path = None
        self.mount_path_2 = None
        self.content_path = None
        self.copy_ddb_path = None
        self.primary_ma_path = None
        self.secondary_ma_path = None
        self.subclient = None
        self.backupset = None
        self.copy_name = None
        self.pool_name = None
        self.pool_name_2 = None
        self.plan = None
        self.subclient_name = None
        self.backupset_name = None
        self.plan_name = None
        self.list_primary = []
        self.list_secondary = []
        self.config_strings = None
        self.is_user_defined_pool = False
        self.is_user_defined_copy_pool = False
        self.is_user_defined_mp = False
        self.is_user_defined_copy_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_copy_dedup = False

    def setup(self):
        """Setup function of this test case"""
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        self.utility = OptionsSelector(self.commcell)
        self.client_machine, self.client_path = self.mm_helper.generate_automation_path(self.client.client_name, 25*1024)
        self.ma_machine_1, self.primary_ma_path = self.mm_helper.generate_automation_path(self.tcinputs['PrimaryCopyMediaAgent'], 25*1024)
        self.ma_machine_2, self.secondary_ma_path = self.mm_helper.generate_automation_path(self.tcinputs['SecondaryCopyMediaAgent'], 25*1024)
        self.content_path = self.client_machine.join_path(self.client_path, 'content')
        self.copy_name = f'{str(self.id)}_Copy'
        self.subclient_name = f'{str(self.id)}_SC'
        self.backupset_name = f"{str(self.id)}_BS_{self.tcinputs.get('SecondaryCopyMediaAgent')[2:]}"
        self.plan_name = f"{str(self.id)}_Plan_{self.tcinputs.get('SecondaryCopyMediaAgent')[2:]}"

        if self.tcinputs.get('pool_name'):
            self.is_user_defined_pool = True
        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('copy_library_name'):
            self.is_user_defined_copy_pool = True
        if self.tcinputs.get('copy_mount_path'):
            self.is_user_defined_copy_mp = True
        if self.tcinputs.get('copy_dedup_path'):
            self.is_user_defined_copy_dedup = True

        if self.is_user_defined_pool:
            self.log.info("Existing pool name supplied")
            self.pool_name = self.tcinputs.get("pool_name")
        else:
            self.pool_name = f"{str(self.id)}_Pool1_{str(self.tcinputs.get('SecondaryCopyMediaAgent'))[2:]}"
            if not self.is_user_defined_mp:
                self.mount_path = self.ma_machine_1.join_path(self.primary_ma_path, 'MP1')
            else:
                self.log.info("custom mount_path supplied")
                self.mount_path = self.ma_machine_1.join_path(
                    self.tcinputs.get('mount_path'), f'test_{str(self.id)}', 'MP1')

        if self.is_user_defined_copy_pool:
            self.log.info("Existing pool name supplied for secondary copy")
            self.pool_name_2 = self.tcinputs.get("copy_pool_name")
        else:
            self.pool_name_2 = f"{str(self.id)}_Pool2_{str(self.tcinputs.get('SecondaryCopyMediaAgent'))[2:]}"
            if not self.is_user_defined_copy_mp:
                self.mount_path_2 = self.ma_machine_2.join_path(self.secondary_ma_path, 'MP2')
            else:
                self.log.info("custom copy_mount_path supplied")
                self.mount_path = self.ma_machine_2.join_path(
                    self.tcinputs.get('copy_mount_path'), f'test_{str(self.id)}', 'MP2')

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.ma_machine_1.join_path(self.tcinputs.get("dedup_path"),
                                                        f'test_{str(self.id)}', "DDB")
        else:
            if "unix" in self.ma_machine_1.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_path = self.ma_machine_1.join_path(self.primary_ma_path, "DDB")

        if self.is_user_defined_copy_dedup:
            self.log.info("custom copydedup path supplied")
            self.copy_ddb_path = self.ma_machine_2.join_path(self.tcinputs.get("copy_dedup_path"),
                                                             f'test_{str(self.id)}', "CopyDDB")
        else:
            if "unix" in self.ma_machine_2.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.copy_ddb_path = self.ma_machine_2.join_path(self.secondary_ma_path, "CopyDDB")

    def cleanup(self):
        try:
            self.log.info("****************************** Cleanup Started ******************************")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info(f"Deleting plan  {self.plan_name}")
                self.commcell.plans.delete(self.plan_name)

            if not self.is_user_defined_pool:
                if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                    self.log.info(f"Deleting pool  {self.pool_name}")
                    self.commcell.storage_pools.delete(self.pool_name)

            if not self.is_user_defined_copy_pool:
                if self.commcell.storage_pools.has_storage_pool(self.pool_name_2):
                    self.log.info(f"Deleting pool  {self.pool_name_2}")
                    self.commcell.storage_pools.delete(self.pool_name_2)
            self.log.info('****************************** Cleanup Completed ******************************')
        except Exception as exe:
            self.log.error(f'ERROR in Cleanup. Might need to Cleanup Manually: {exe}')

    def run(self):
        """Run Function of This Case"""
        self.log.info('**************** Cleaning up Entities from older runs ****************')
        self.cleanup()
        try:
            # 1: Setup the Environment
            self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                      self.content_path, 0.7)
            if not self.is_user_defined_pool:
                self.log.info(f"Creating the pool [{self.pool_name}]")
                self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                                self.tcinputs['PrimaryCopyMediaAgent'],
                                                [self.tcinputs['PrimaryCopyMediaAgent'], self.tcinputs['PrimaryCopyMediaAgent']],
                                                [self.ma_machine_1.join_path(self.ddb_path, 'Dir'), self.ma_machine_1.join_path(self.ddb_path, 'Dir2')])
                self.log.info(f"Pool [{self.pool_name}] Created.")

            if not self.is_user_defined_copy_pool:
                self.commcell.storage_pools.refresh()
                self.log.info(f"Creating the pool [{self.pool_name_2}]")
                self.commcell.storage_pools.add(self.pool_name_2, self.mount_path_2,
                                      self.tcinputs['SecondaryCopyMediaAgent'],
                                      [self.tcinputs['SecondaryCopyMediaAgent'], self.tcinputs['SecondaryCopyMediaAgent']],
                                      [self.ma_machine_2.join_path(self.copy_ddb_path, 'Dir'), self.ma_machine_2.join_path(self.copy_ddb_path, 'Dir2')])
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
            self.plan.schedule_policies['data'].disable()

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
            self.log.info("Added plan to subclient")

            # 2: Run 2 Full Backups
            self.log.info('Submitting 1st Full Backup')
            backup_1 = self.subclient.backup(backup_level='Full')
            if not backup_1.wait_for_completion():
                raise Exception(f'1st Backup Job {backup_1.job_id} Failed with JPR: {backup_1.delay_reason}')
            self.log.info(f'1st Backup Completed :Id - {backup_1.job_id}')
            time.sleep(60)

            self.log.info('Submitting 2nd Full Backup')
            backup_2 = self.subclient.backup(backup_level='Full')
            if not backup_2.wait_for_completion():
                raise Exception(f'2nd Backup Job {backup_2.job_id} Failed with JPR: {backup_2.delay_reason}')
            self.log.info(f'2nd Backup Completed :Id - {backup_2.job_id}')

            self.log.info("Creating the secondary copy 1")
            self.plan.storage_policy.create_dedupe_secondary_copy(f'{self.copy_name}_1', self.pool_name_2,
                                                                  self.tcinputs.get('SecondaryCopyMediaAgent'),
                                                                  self.ma_machine_2.join_path(self.copy_ddb_path,
                                                                                f'Dir{self.utility.get_custom_str()}'),
                                                                  self.tcinputs.get('SecondaryCopyMediaAgent'))
            copy_1 = self.plan.storage_policy.get_copy(f'{self.copy_name}_1')
            self.log.info("Created the secondary copy 1")

            self.log.info("Creating the secondary copy 2")
            self.plan.storage_policy.create_dedupe_secondary_copy(f'{self.copy_name}_2', self.pool_name_2,
                                                                  self.tcinputs.get('SecondaryCopyMediaAgent'),
                                                                  self.ma_machine_2.join_path(self.copy_ddb_path,
                                                                                              f'Dir{self.utility.get_custom_str()}'),
                                                                  self.tcinputs.get('SecondaryCopyMediaAgent'))
            copy_2 = self.plan.storage_policy.get_copy(f'{self.copy_name}_2')
            self.log.info("Created the secondary copy 2")

            # 3: Validate System Created AutoCopy Schedule.
            # Mark jobs on Copy2 to DoNotCopy. Schedule then copies to Copy1 and skips Copy2.
            self.log.info('Marking both jobs to DoNotCopy on the secondary copy 2')
            copy_2.do_not_copy_jobs([backup_1.job_id, backup_2.job_id])

            self.log.info('Waiting 40 mins for AutoCopy Schedule to kickoff and copy the jobs')
            time.sleep(40*60)

            self.log.info('Wait Completed. Remove Association with System Created AutoCopy Schedule')
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, f'{self.copy_name}_1')
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, f'{self.copy_name}_2')

            self.run_validations(backup_1.job_id, backup_2.job_id,
                                 copy_1.copy_id, copy_2.copy_id)

            self.log.info('Marking both jobs for ReCopy on the secondary copy 1')
            copy_1.recopy_jobs([backup_1.job_id, backup_2.job_id])

            # 4: Validate User Created AuxCopy Schedule.
            # Mark jobs on Copy1 to ReCopy. Schedule then copies to Copy1 and skips Copy2.
            self.log.info('Configure User Created Schedule Policy for AuxCopy')
            if self.commcell.schedule_policies.has_policy(f'{self.id}_schedule_policy'):
                self.commcell.schedule_policies.delete(f'{self.id}_schedule_policy')
            self.commcell.schedule_policies.add(
                name=f'{self.id}_schedule_policy', policy_type='Auxiliary Copy',
                associations=[{'storagePolicyName': f'{self.plan.storage_policy.storage_policy_name}'}],
                schedules=[{'pattern': {"freq_type": 'continuous', 'job_interval': 10}}])

            self.log.info('Waiting 20 mins for AutoCopy Schedule to kickoff and copy the jobs')
            time.sleep(20*60)
            self.run_validations(backup_1.job_id, backup_2.job_id,
                                 copy_1.copy_id, copy_2.copy_id)

            self.log.info('Validation Completed. Deleting user Create Schedule Policy for AuxCopy')
            self.commcell.schedule_policies.delete(f'{self.id}_schedule_policy')

            # 5: Validate User Created AuxCopy Schedule.
            # Mark jobs on Copy1, Copy2 to ReCopy. Mark Copy2 as inactive.Schedule then copies to Copy1 and skips Copy2.
            self.log.info('Marking both jobs for ReCopy on both secondary copies')
            copy_1.recopy_jobs([backup_1.job_id, backup_2.job_id])
            copy_2.recopy_jobs([backup_1.job_id, backup_2.job_id])

            self.log.info('Marking Secondary Copy 2 as inactive')
            copy_2.is_active = False
            self.log.info('Configure User Created Schedule Policy for AuxCopy')
            self.commcell.schedule_policies.add(
                name=f'{self.id}_schedule_policy', policy_type='Auxiliary Copy',
                associations=[{'storagePolicyName': f'{self.plan.storage_policy.storage_policy_name}'}],
                schedules=[{'pattern': {"freq_type": 'continuous', 'job_interval': 10}}])

            self.log.info('Waiting 20 mins for AutoCopy Schedule to kickoff and copy the jobs')
            time.sleep(20*60)
            self.run_validations(backup_1.job_id, backup_2.job_id,
                                 copy_1.copy_id, copy_2.copy_id)

            self.log.info('Validation Completed. Deleting user Create Schedule Policy for AuxCopy')
            self.commcell.schedule_policies.delete(f'{self.id}_schedule_policy')
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error(f'Exception Occurred: {exe}')

    def get_copied_status(self, job_id, copy_id):
        """
        Checks if backup job's are copied to secondary copy

        Args:
            job_id      (list): List of Id's of Backup Jobs

            copy_id     (str):  Id of the Secondary Copy
        Returns:
            (bool): True if job is copied, False if job isn't copied
        """
        job_id = ','.join(job_id)
        query = f'''
                select  jobId, status
                from    JMJobDataStats WITH (NOLOCK)
                where   jobId in ({job_id})
                    and archGrpCopyId = {copy_id}
                group by    jobId, status
                '''
        self.log.info(f'Executing Query: {query}')
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info(f'Result: {result}')
        if len(result) < 2:
            return False
        for row in result:
            if int(row[1]) != 100:
                return False
        return True

    def run_validations(self, backup_1, backup_2, copy_1, copy_2):
        """Validates Whether The Schedule Policy has Copied the Data to Intended Copy

        Args:
              backup_1 (str) :  Job Id of the 1st Backup
              backup_2 (str) :  Job Id of the 2nd Backup
              copy_1   (str) :  Copy Id of the Secondary Copy 1
              copy_2   (str) :  Copy Id of the Secondary Copy 2
        Raises:
            Exception : If Validation Fails
        """
        self.log.info('*** Validating job status on both secondary copies to make sure aux ran to right copy ***')
        if not self.get_copied_status([backup_1, backup_2], copy_1):
            raise Exception("FAILED: AuxCopy didn't copy the jobs to Secondary Copy 1")
        self.log.info("SUCCESS: AuxCopy copied the jobs to Secondary Copy 1")

        if self.get_copied_status([backup_1, backup_2], copy_2):
            raise Exception("FAILED: AuxCopy copied the jobs to Secondary Copy 2")
        self.log.info("SUCCESS: AuxCopy didn't copy the jobs to Secondary Copy 2")

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 6: CleanUp the environment
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
