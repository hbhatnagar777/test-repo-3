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
    __init__()            --  initialize TestCase class

    setup()               --  setup function of this test case

    cleanup()       --  cleanup the entities created in this/previous run

    run()                 --  run function of this test case

    run_backup()          -- runs the backup of specified type

    fetch_copied_times()  --  fetches the copied time of the job to Secondary Copy

    fetch_primary_count() -- fetches the count of primary objects for job in Both DDBs

    tear_down()           --  tear down function of this test case

    verify_cvperfmgr_log  --  Verify that given job ID is present in CVPerfMgr log on MA
Inputs to be passed in JSON File:
    "52811": {
        "ClientName": "Name of client",
        "AgentName": "File System",
        "PrimaryCopyMediaAgent":"MA to host Primary Copy",
        "SecondaryCopyMediaAgent":"MA to host Secondary Copy",
        "dedup_path":"User provided path for hosting Primary copy DDB on Linux MA",
        "copy_dedup_path":"User provided dedup path for hosting Secondary copy DDB on Linux MA"
    }
    ************************          IMPORTANT NOTE:         ***************************
    *************************************************************************************
    ** 1. BOTH THE MEDIA AGENTS SHOULD NOT BE SAME,                                    **
    ** 2. DURING RESTORE VALIDATION WE STOP MEDIA MOUNT MANAGER SERVICE ON PRIMARY MA. **
    *************************************************************************************

Steps:

1: Configure the environment: create a library,Storage Policy-with secondary copy space-optimized),
                              a BackupSet,a SubClient
2: Run Backups on the subclient in order: F_I_I_F_SF

3: Run AuxCopy

4: Run the Validations whether SpaceOptimized Copy feature worked as expected
    -Full Backups should be copied first
    -PrimaryObjects count for 1st Full should be equal in both copies
    -PrimaryObjects count for 2nd Full should be more in Secondary Copy
    -PrimaryObjects count for Synthetic fulls should always be 0
    -Total Primary objects count in both copies should be equal
    -Restore Validation from the Secondary Copy

5: CleanUp the environment
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
        self.name = 'Space Optimized AuxCopy'
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
        self.restore_path = None
        self.copy_ddb_path = None
        self.subclient = None
        self.plan = None
        self.copy_name = None
        self.pool_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.plan_name = None
        self.is_user_defined_dedup = False
        self.is_user_defined_copy_dedup = False
        self.result_string = ""

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.tcinputs['ClientName'], self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs['PrimaryCopyMediaAgent'], self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        utility = OptionsSelector(self.commcell)
        client_drive = utility.get_drive(self.client_machine, 25 * 1024)
        primary_ma_drive = utility.get_drive(self.ma_machine_1, 25 * 1024)
        secondary_ma_drive = utility.get_drive(self.ma_machine_2, 25 * 1024)
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('copy_dedup_path'):
            self.is_user_defined_copy_dedup = True

        self.client_path = self.client_machine.join_path(client_drive, 'test_' + str(self.id))
        self.ma_1_path = self.ma_machine_1.join_path(primary_ma_drive, 'test_' + str(self.id))
        self.ma_2_path = self.ma_machine_2.join_path(secondary_ma_drive, 'test_' + str(self.id))


        if self.is_user_defined_dedup:
            self.log.info("User defined Dedup path supplied for primary MA")
            self.ddb_path = self.ma_machine_1.join_path(self.tcinputs['dedup_path'], self.id, "DDB")
        else:
            if "unix" in self.ma_machine_1.os_info.lower():
                self.log.error("LVM enabled dedup path must be provided for Primary MA if it is Unix MA!..")
                raise Exception("LVM enabled dedup path must be provided for Primary MA if it is Unix MA!..")
            self.ddb_path = self.ma_machine_1.join_path(self.ma_1_path, 'DDB')

        if self.is_user_defined_copy_dedup:
            self.log.info("User defined dedup path supplied for secondary MA")
            self.copy_ddb_path  = self.ma_machine_2.join_path(self.tcinputs['copy_dedup_path'], self.id, "DDB")
        else:
            if "unix" in self.ma_machine_2.os_info.lower():
                self.log.error("LVM enabled dedup path must be provided for Secondary MA if it is Unix MA!..")
                raise Exception("LVM enabled dedup path must be provided for Secondary MA if it is Unix MA!..")
            self.copy_ddb_path  = self.ma_machine_2.join_path(self.ma_2_path, 'DDB_2')

        self.mount_path = self.ma_machine_1.join_path(self.ma_1_path, 'MP')
        self.mount_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'MP2')

        self.content_path = self.client_machine.join_path(self.client_path, 'Content')
        self.restore_path = self.client_machine.join_path(self.client_path, 'Restores')
        self.copy_name = str(self.id) + '_Copy'
        self.pool_name = str(self.id) + '_Pool'
        self.backupset_name = str(self.id) + '_BS'
        self.subclient_name = str(self.id) + '_SC'
        self.plan_name = str(self.id) + '_Plan'
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def cleanup(self):
        """Cleans Up the Entities created in the TC"""
        try:
            self.log.info('********* STARTING Media Mount Manager SERVICE ON PRIMARY MA *********')
            self.ma_machine_1.client_object.start_service(
                'GXMMM(%s)' % self.ma_machine_1.client_object.instance)
            self.log.info('********* STARTED Media Mount Manager SERVICE ON PRIMARY MA **********')

            self.log.info("****************************** Cleanup Started ******************************")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            self.mm_helper.remove_content(self.restore_path, self.client_machine, suppress_exception=True)

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Deleting plan  %s", self.plan_name)
                self.commcell.plans.delete(self.plan_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info("Deleting pool  %s", self.pool_name)
                self.commcell.storage_pools.delete(self.pool_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name + '_2'):
                self.log.info("Deleting pool  %s", self.pool_name + '_2')
                self.commcell.storage_pools.delete(self.pool_name + '_2')
            self.log.info('****************************** Cleanup Completed ******************************')
        except Exception as exe:
            self.log.error('ERROR in Cleanup. Might need to Cleanup Manually: %s', str(exe))


    def verify_cvperfmgr_log(self, job_id, ma_name):
        """
        Verify that given job ID is present in CVPerfMgr log on MA

        Args:
            job_id  (object)        --  Job ID to be looked up in CVPerfMgr.log
            ma_name (str)           --  Name of the MA where to check CVPerfMgr.log

        """
        self.log.info(f"Verifying presence of {job_id} in CVPerfMgr.log on MA {ma_name}")
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            ma_name, "CVPerfMgr.log", f"*Perf*|{job_id}| Job-ID: {job_id}")
        if matched_line:
            self.log.info(matched_line)
            self.log.info('Success Result : Passed')
        else:
            self.log.info(f"Failed to look up {job_id} in CVPerfMgr.log on MA {ma_name}")
            self.log.error('Error  Result : Failed')
            self.result_string += "f[Failed to look up {job_id} in CVPerfMgr.log on MA {ma_name}]"
            self.status = constants.FAILED

    def run(self):
        """Run Function of this case"""
        self.log.info('**************** Cleaning up Entities from older runs ****************')
        self.cleanup()
        try:
            # 1: Configure the environment
            self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'], self.content_path, 0.5)
            self.log.info(f"Creating the pool [{self.pool_name}]")
            self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                            self.tcinputs['PrimaryCopyMediaAgent'],
                                            [self.tcinputs['PrimaryCopyMediaAgent'], self.tcinputs['PrimaryCopyMediaAgent']],
                                            [self.ddb_path, self.ddb_path])
            self.log.info(f"Pool [{self.pool_name}] Created.")

            self.log.info(f"Creating the pool [{self.pool_name + '_2'}]")
            self.commcell.storage_pools.add(self.pool_name + '_2', self.mount_path_2,
                                            self.tcinputs['SecondaryCopyMediaAgent'],
                                            [self.tcinputs['SecondaryCopyMediaAgent'], self.tcinputs['SecondaryCopyMediaAgent']],
                                            [self.copy_ddb_path, self.copy_ddb_path])
            self.log.info(f"Pool [{self.pool_name + '_2'}] Created.")

            self.commcell.storage_pools.refresh()
            self.commcell.plans.refresh()

            # creation of plan
            self.log.info(f"Plan Present: {self.commcell.plans.has_plan(self.plan_name)}")
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.commcell.plans.refresh()
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")

            if self.plan.storage_policy.has_copy(self.copy_name):
                self.plan.storage_policy.delete_secondary_copy(self.copy_name)

            # By default we create space optimized copy in Automation
            # disabling the schedule policy
            self.log.info('Disabling the schedule policy')
            self.plan.schedule_policies['data'].disable()

            self.log.info(f"Adding the secondary copy [{self.copy_name}]")
            self.plan.add_storage_copy(self.copy_name, self.pool_name + "_2")
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

            # 2: Run Backups on the subclient in order: F_I_F_I_SF
            self.log.info('Running backupJobs in order F_I_F_I_SF')
            full_1 = self.run_backup("Full")
            time.sleep(60)

            self.log.info(f"Verify CVPerfMgr log file after running Full Backup Job {full_1.job_id}")
            self.verify_cvperfmgr_log(full_1.job_id, self.tcinputs['PrimaryCopyMediaAgent'])

            self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'],
                                                      self.content_path, 0.5)
            incremental_1 = self.run_backup("Incremental")
            time.sleep(60)

            full_2 = self.run_backup("Full")
            time.sleep(60)

            self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'],
                                                      self.content_path, 0.5)
            incremental_2 = self.run_backup("Incremental")
            time.sleep(60)

            synth_job = self.run_backup("Synthetic_full")

            time.sleep(60)

            self.log.info(f"Verify CVPerfMgr log file after running Synthetic Full Backup Job {synth_job.job_id}")
            self.verify_cvperfmgr_log(synth_job.job_id, self.tcinputs['PrimaryCopyMediaAgent'])

            # 3: Run AuxCopy
            self.log.info('Running AuxCopy Job with Scalable Resource Allocation')
            aux_copy_job = self.plan.storage_policy.run_aux_copy()
            if aux_copy_job.wait_for_completion():
                self.log.info('AuxCopy Completed(Id: %s)', aux_copy_job.job_id)
            else:
                raise Exception(f'AuxCopy {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')
            self.log.info(f"Verify CVPerfMgr log file after running Auxcopy Job {aux_copy_job.job_id}")
            self.verify_cvperfmgr_log(aux_copy_job.job_id, self.tcinputs['SecondaryCopyMediaAgent'])
            # 4: Run the Validations
            time.sleep(120)
            self.log.info('********************** VALIDATIONS **********************')
            self.log.info('*** CASE 1: Order of Jobs -> Fulls copied 1st, Remaining Later ***')
            self.log.info('Fetching Copied Times')
            secondary_copy = self.plan.storage_policy.get_copy(self.copy_name)
            time_1 = self.fetch_copied_times(secondary_copy.copy_id, full_1.job_id)
            time_2 = self.fetch_copied_times(secondary_copy.copy_id, incremental_1.job_id)
            time_3 = self.fetch_copied_times(secondary_copy.copy_id, incremental_2.job_id)
            time_4 = self.fetch_copied_times(secondary_copy.copy_id, full_2.job_id)
            time_5 = self.fetch_copied_times(secondary_copy.copy_id, synth_job.job_id)

            max_copy_time = max(time_1, time_4, time_5)
            min_copy_time = min(time_2, time_3)
            if max_copy_time < min_copy_time:
                self.log.info('SUCCESS Result: Passed')
            else:
                self.status = constants.FAILED
                self.log.error('ERROR Result: Failed')

            count_0, count_1 = self.fetch_primary_count(full_1.job_id)
            count_2, count_3 = self.fetch_primary_count(incremental_1.job_id)
            count_6, count_7 = self.fetch_primary_count(full_2.job_id)
            count_4, count_5 = self.fetch_primary_count(incremental_2.job_id)
            count_8, count_9 = self.fetch_primary_count(synth_job.job_id)

            self.log.info('*** CASE 2: PrimaryObjectsCount for 1st Full: Sec_Copy = Primary ***')
            if count_0 == count_1:
                self.log.info('SUCCESS Result: Passed')
            else:
                self.log.error('ERROR Result: Failed')

            self.log.info('*** CASE 3: PrimaryObjectsCount for 2nd Full: Sec_Copy >= Primary(=0) ***')
            if (count_6 <= count_7) and (count_6 == 0):
                self.log.info('SUCCESS Result: Passed')
            else:
                self.log.error('ERROR Result: Failed')

            self.log.info('*** CASE 4: PrimaryObjectsCount for SFull: Sec_Copy >= Primary(=0) ***')
            if (count_8 <= count_9) and (count_8 == 0):
                self.log.info('SUCCESS Result: Passed')
            else:
                self.log.error('ERROR Result: Failed')

            self.log.info('*** CASE 4: PrimaryObjectsCount for Both Incrementals: Sec_Copy = 0 ***')
            if count_3 == count_5 == 0:
                self.log.info('SUCCESS Result: Passed')
            else:
                self.log.error('ERROR Result: Failed')

            self.log.info('*** CASE 5: Sum of PrimaryObjectsCount : Sec_Copy = Primary ***')
            total_in_primary = count_0 + count_2 + count_4 + count_6 + count_8
            total_in_secondary = count_1 + count_3 + count_5 + count_7 + count_9
            if total_in_primary == total_in_secondary:
                self.log.info('SUCCESS Result: Passed %d', total_in_primary)
            else:
                self.status = constants.FAILED
                self.log.error('ERROR Result: Failed %d %d', total_in_primary, total_in_secondary)

            self.log.info('*** Running Restore from Secondary copy when Primary MA is offline ***')

            self.log.info('********* STOPPING Media Mount Manager SERVICE ON PRIMARY MA *********')
            self.ma_machine_1.client_object.stop_service(
                'GXMMM(%s)' % self.ma_machine_1.client_object.instance)
            self.log.info('********* STOPPED Media Mount Manager SERVICE ON PRIMARY MA **********')

            self.log.info('Initiating Restore Job')
            restore_job = self.subclient.restore_out_of_place(self.client.client_name,
                                                              self.restore_path,
                                                              [self.content_path],
                                                              copy_precedence=2)
            if restore_job.wait_for_completion():
                self.log.info('Restore Job: %s Completed', restore_job.job_id)
            else:
                raise Exception(f'Restore job {restore_job.job_id} Failed with JPR: {restore_job.delay_reason}')

            self.log.info('Validating Restored Data from Secondary Copy')
            restored_path = self.client_machine.join_path(self.restore_path, 'Content')
            difference = self.client_machine.compare_folders(self.client_machine,
                                                             self.content_path, restored_path)
            if difference:
                self.result_string += f"[Validating Data restored from Secondary Copy Failed]"

            if self.result_string:
                self.log.error("Raising Exception as result string is not empty")
                raise Exception(self.result_string)
            else:
                self.log.info('Validation SUCCESS')

        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('Exception Occurred : %s', str(exe))

    def run_backup(self, backup_type):
        """Runs Backup of specified type and waits for job till it completes
                Args:
                        backup_type    (str)  --   Type of backup To Run
                Return:
                        (object)              --   Object of Job Class

        """
        job = self.subclient.backup(backup_level=backup_type)
        if job.wait_for_completion():
            self.log.info('%s Backup job Completed(Id: %s)', backup_type, job.job_id)
        else:
            raise Exception(f'{backup_type} Backup Job {job.job_id} Failed with JPR: {job.delay_reason}')
        return job

    def fetch_copied_times(self, copy_id, job_id):
        """Returns copiedTime from JMJobDataStats
                Args:
                        job_id    (str)  --   Id of Backup Job

                        copy_id   (str)  --   Id of Storage Policy Copy
                Return:
                        (int)            --   Copied Time of Job to the Secondary Copy

        """
        query = '''select distinct copiedTime from JMJobDataStats
                where archGrpCopyId = {0} and jobId = {1}
                '''.format(copy_id, job_id)
        self.log.info('Query: %s', query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info('Copied Time : %s', result[0])
        return int(result[0])

    def fetch_primary_count(self, job_id):
        """Returns Count of primary Objects for the job in Primary and Secondary Copies
                Args:
                        job_id    (str)  --   Id of Backup Job
                Return:
                        (tuple)          --   Count of Primary objects in DDBs of both copies

        """
        result_1 = self.dedupe_helper.get_primary_objects_sec(job_id, 'Primary')
        result_2 = self.dedupe_helper.get_primary_objects_sec(job_id, self.copy_name)
        return int(result_1), int(result_2)

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 5: CleanUp the environment
        self.log.info('********* STARTING Media Mount Manager SERVICE ON PRIMARY MA *********')
        self.ma_machine_1.client_object.start_service(
            'GXMMM(%s)' % self.ma_machine_1.client_object.instance)
        self.log.info('********* STARTED Media Mount Manager SERVICE ON PRIMARY MA **********')
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
