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

    cleanup()       --  cleanup the entities

    run_backup()    --  run backup of specified type and wait till it completes

    initial_setup()     --  configures the environment

    run_validations()   --  runs the required validations for the case

    aux_populator_validation()      -- launches auxcopy and initiates the populator validations for aux

    dv2_populator_validation()      -- launches dv2 and initiates the populator validations for dv2

    defrag_populator_validation()   -- launches defrag and initiates the populator validations for defrag

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Inputs to be passed in JSON File:
    "64135": {
        "ClientName": "Name of client",
        "AgentName": "File System",
        "PrimaryCopyMediaAgent":"MA to host Primary Copy",
        "SecondaryCopyMediaAgent":"MA to host Secondary Copy"
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "mount_path": "path where the data is to be stored",
        "dedup_path": "path where dedup store to be created",
        "copy_mount_path": "path where the data is to be stored for auxcopy",
        "copy_dedup_path": "path where dedup store to be created for auxcopy"
    }
    Note: Both the MediaAgents can be the same machine

Steps:

1. Configure Environment: Storage Policy 2 Dedupe Copies, Backupset, Subclient.
2. Run Backup(s) to the Primary Copy
3. Set GxGlobalParam bEnableAuxCopyPopulatorODS to true and Launch auxcopy to secondary copy
4. Validate Populator for auxcopy:
    a. JMJobOptions: Using CVJobReplicatorPopulator - 1
    b. CVJobReplicatorPopulator.log - Logging for the job
    c. JMJobDataStats: status <> (101,102,103) for backups in secondary copy
    d. archFileCopy: sum(physicalSize) matches for both copies
5.  Set GxGlobalParam bEnablePopulatorODSForScalableDV to true and Launch DV2 for Primary pool
6. Validate Populator for DV2:
    a. JMJobOptions: Using CVJobReplicatorPopulator - 1
    b. CVJobReplicatorPopulator.log - Logging for the job
    c. JMJobDataStats: archCheckStatus = 5 for all backups in primary copy
7. Launch Defrag for Primary pool
9. Validate Populator for Defrag:
    a. JMJobOptions: Using CVJobReplicatorPopulator - 1
    b. CVJobReplicatorPopulator.log - Logging for the job
10. Remove GlobalParams and CleanUp the Environment
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
        self.name = 'Aux,DV2,Defrag with Populator - Basic Test Scenario'
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
        self.ma_1_name = None
        self.ma_2_name = None
        self.client_name = None
        self.utility = None
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ma_1_path = None
        self.ma_2_path = None
        self.client_path = None
        self.ddb_1_path = None
        self.ddb_2_path = None
        self.content_path = None
        self.mount_path_1 = None
        self.mount_path_2 = None
        self.copy_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_pool_1_name = None
        self.storage_pool_2_name = None
        self.storage_policy_name = None
        self.storage_pool_1 = None
        self.storage_pool_2 = None
        self.store = None
        self.subclient = None
        self.primary_copy = None
        self.secondary_copy = None
        self.storage_policy = None

        self.backup_jobs = []
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_copy_mp = False
        self.is_user_defined_copy_dedup = False
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        self.client_name = self.tcinputs.get('ClientName')
        self.ma_1_name = self.tcinputs.get('PrimaryCopyMediaAgent')
        self.ma_2_name = self.tcinputs.get('SecondaryCopyMediaAgent')

        self.utility = OptionsSelector(self.commcell)
        self.ma_machine_1 = Machine(self.ma_1_name, self.commcell)
        self.ma_machine_2 = Machine(self.ma_2_name, self.commcell)
        self.client_machine = Machine(self.client_name, self.commcell)

        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('copy_mount_path'):
            self.is_user_defined_copy_mp = True
        if self.tcinputs.get('copy_dedup_path'):
            self.is_user_defined_copy_dedup = True

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.ma_machine_1, 25*1024)
            self.ma_1_path = self.ma_machine_1.join_path(ma_1_drive, f'test_{self.id}')
        if not self.is_user_defined_copy_mp or not self.is_user_defined_copy_dedup:
            ma_2_drive = self.utility.get_drive(self.ma_machine_2, 25*1024)
            self.ma_2_path = self.ma_machine_2.join_path(ma_2_drive, f'test_{self.id}')

        client_drive = self.utility.get_drive(self.client_machine, 25*1024)
        self.client_path = self.client_machine.join_path(client_drive, f'test_{self.id}')
        self.content_path = self.client_machine.join_path(self.client_path, 'Content')

        self.subclient_name = f'{self.id}_SC'
        self.backupset_name = f'{self.id}_BS_{self.ma_1_name}'
        self.storage_pool_1_name = f'{self.id}_Src_Pool_{self.ma_1_name}'
        self.storage_pool_2_name = f'{self.id}_Dest_Pool_{self.ma_1_name}'
        self.storage_policy_name = f'{self.id}_SP_{self.ma_1_name}'
        self.copy_name = f'{self.id}_Copy'

        if not self.is_user_defined_mp:
            self.mount_path_1 = self.ma_machine_1.join_path(self.ma_1_path, 'MP1')
        else:
            self.log.info("custom mount_path supplied: %s", self.tcinputs.get('mount_path'))
            self.mount_path_1 = self.ma_machine_1.join_path(
                self.tcinputs.get('mount_path'), f'test_{self.id}', 'MP1')

        if not self.is_user_defined_mp:
            self.mount_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'MP2')
        else:
            self.log.info("custom copy mount_path supplied: %s", self.tcinputs.get('mount_path'))
            self.mount_path_2 = self.ma_machine_2.join_path(
                self.tcinputs.get('mount_path'), f'test_{self.id}', 'MP2')

        if self.is_user_defined_dedup:
            self.ddb_1_path = self.tcinputs.get("dedup_path")
            self.log.info("custom dedup path supplied: %s", self.ddb_1_path)
        else:
            if "unix" in self.ma_machine_1.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_1_path = self.ma_machine_1.join_path(self.ma_1_path, "DDBs")

        if self.is_user_defined_copy_dedup:
            self.ddb_2_path = self.tcinputs.get("copy_dedup_path")
            self.log.info("custom copy dedup path supplied: %s", self.ddb_2_path)
        else:
            if "unix" in self.ma_machine_2.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_2_path = self.ma_machine_2.join_path(self.ma_2_path, "CopyDDBs")

        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def cleanup(self):
        """"CleanUp the Entities"""
        self.log.info('************************ Clean Up Started *********************************')
        try:
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            self.log.info('Deleting BackupSet if exists')
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            self.log.info('Deleting Storage Policies if exists')
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.get(self.storage_policy_name).reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)

            self.log.info('Deleting Storage Pools if exists')
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_1_name):
                self.commcell.storage_pools.delete(self.storage_pool_1_name)
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_2_name):
                self.commcell.storage_pools.delete(self.storage_pool_2_name)
        except Exception as exe:
            self.log.warning('CleanUp Failed: ERROR: %s', str(exe))

    def run_backup(self, backup_type, iteration):
        """Runs Backup of specified type and waits for job till it completes
        Args:
            backup_type    (str)  --   Type of backup To Run

            iteration       (int) --   Index of Current Backup Job
        """
        self.utility.create_uncompressable_data(self.client_machine, self.content_path, 1, delete_existing=True)
        job = self.subclient.backup(backup_level=backup_type)
        self.log.info('Backup Job %d Initiated. Job Id: %s', iteration, job.job_id)
        if not job.wait_for_completion():
            raise Exception('Backup Job(Id: %s) Failed with JPR: %s' % (job.job_id, job.delay_reason))
        self.log.info('Backup job(Id: %s) Completed', job.job_id)

    def initial_setup(self):
        """Configures the environment"""
        self.log.info("Configuring source and destination storage pools")
        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_1_name):
            self.storage_pool_1 = self.commcell.storage_pools.add(self.storage_pool_1_name, self.mount_path_1,
                                                                  self.ma_1_name, self.ma_1_name, self.ddb_1_path)
        else:
            self.storage_pool_1 = self.commcell.storage_pools.get(self.storage_pool_1_name)

        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_2_name):
            self.storage_pool_2 = self.commcell.storage_pools.add(self.storage_pool_2_name, self.mount_path_2,
                                                                  self.ma_2_name, self.ma_2_name, self.ddb_2_path)
        else:
            self.storage_pool_2 = self.commcell.storage_pools.get(self.storage_pool_2_name)

        self.storage_policy = self.dedupe_helper.configure_dedupe_storage_policy(
            self.storage_policy_name, storage_pool_name=self.storage_pool_1_name, is_dedup_storage_pool=True)
        self.primary_copy = self.storage_policy.get_copy('Primary')

        self.storage_policy.create_secondary_copy(self.copy_name, global_policy=self.storage_pool_2_name)
        self.secondary_copy = self.storage_policy.get_copy(self.copy_name)
        # Remove association for StoragePolicy with System created AutoCopy Schedule
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.copy_name)

        self.mm_helper.configure_backupset(self.backupset_name)
        self.subclient = self.mm_helper.configure_subclient(self.backupset_name, self.subclient_name,
                                                            self.storage_policy_name, self.content_path)

        self.log.info('Running 2 Full Backups')
        for iteration in range(1, 3):
            self.utility.create_uncompressable_data(self.client_machine, self.content_path, 1, delete_existing=True)
            job = self.subclient.backup(backup_level="Full")
            self.log.info('Backup Job %d Initiated. Job Id: %s', iteration, job.job_id)
            if not job.wait_for_completion():
                raise Exception(f'Backup Job(Id: {job.job_id}) Failed with JPR: {job.delay_reason}')
            self.log.info('Backup job(Id: %s) Completed', job.job_id)
            self.log.info("Sleeping for 30 secs for backup to be properly committed")
            time.sleep(30)

    def run_validations(self, job_obj, job_type):
        """Runs the Validations for the Case
        Args:
            job_obj          (object)  --   Job object for which the validations are to be done

            job_type         (object)  --   Type of the job for which validations are to be done('aux'/'dv2'/'defrag')
        """
        result_list = []
        self.log.info('**************************** VALIDATIONS *********************************')

        self.log.info('*** CASE 1: Verify from JMJobOptions - Job is using Populator ***')
        query = f'''select attributeValueInt from JMJobOptions
                where attributeName = 'Using CVJobReplicatorPopulator' and JobId = {job_obj.job_id}'''
        self.log.info(f'Executing Query: {query}')
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(f'Result: {row}')
        if int(row[0]) == 1:
            self.log.info(f'SUCCESS Validation PASSED for {job_type} job {job_obj.job_id}: JMJobOptions set correctly')
        else:
            self.log.error(
                f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}: JMJobOptions not set correctly]')
            result_list.append(
                f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}: JMJobOptions not set correctly]')

        self.log.info('*** CASE 2: Verify from logs, job handling is done by Populator Service ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.commcell.commserv_client.client_name, 'CVJobReplicatorPopulator.log',
            ' ', job_obj.job_id, escape_regex=False)
        if matched_line:
            self.log.info(f'SUCCESS Validation PASSED for {job_type} job {job_obj.job_id}:'
                          f' Populator Service handled the job. Found {len(matched_line)} log lines for job')
        else:
            self.log.error(f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}:'
                           f' Populator Service did not handle the job. No logging found]')
            result_list.append(f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}:'
                               f' Populator Service did not handle the job. No logging found]')

        if job_type == 'aux':
            self.log.info('*** CASE 3: Verify All Jobs are copied ***')
            query = f'''select count(jobId) from JMJobDataStats
                    where status in(101,102,103) and archGrpCopyId = {self.secondary_copy.copy_id}'''
            self.log.info(f'Executing Query: {query}')
            self.csdb.execute(query)
            row = self.csdb.fetch_one_row()
            self.log.info(f'Result: {row}')
            if int(row[0]) == 0:
                self.log.info(f'SUCCESS Validation PASSED for {job_type} job {job_obj.job_id}: All Jobs are Copied')
            else:
                self.log.error(
                    f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}: Some Jobs are not copied]')
                result_list.append(
                    f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}: Some Jobs are not copied]')

            self.log.info('*** CASE 4: Verify total size of archive files match on both copies ***')
            query = f'''select archCopyId, sum(physicalSize)
                    from archFileCopy
                    where archCopyId in
                        ({self.primary_copy.copy_id},{self.secondary_copy.copy_id})
                    group by archCopyId'''
            self.log.info(f'Executing Query: {query}')
            self.csdb.execute(query)
            rows = self.csdb.fetch_all_rows()
            self.log.info(f'Result: {rows}')
            if int(rows[0][1]) != int(rows[1][1]):
                self.log.error(f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}:'
                               f' Total Size of archFiles mismatch for the Copies')
                result_list.append(f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}:'
                                   f' Total Size of archFiles mismatch for the Copies')
            else:
                self.log.info(f'SUCCESS Validation PASSED for {job_type} job {job_obj.job_id}:'
                              f' Size of archFiles matched on both Copies')
        elif job_type == 'dv2':
            self.log.info('*** CASE 3: Verify All Jobs are Verified ***')
            query = f'''select count(jobId) from JMJobDataStats
                    where archCheckStatus<>5 and archGrpCopyId = {self.primary_copy.copy_id}'''
            self.log.info(f'Executing Query: {query}')
            self.csdb.execute(query)
            row = self.csdb.fetch_one_row()
            self.log.info(f'Result: {row}')
            if int(row[0]) == 0:
                self.log.info(f'SUCCESS Validation PASSED for {job_type} job {job_obj.job_id}: All Jobs are verified')
            else:
                self.log.error(
                    f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}: Some Jobs are not verified]')
                result_list.append(
                    f'[ERROR: Validation FAILED for {job_type} job {job_obj.job_id}: Some Jobs are not verified]')

        if len(result_list) > 0:
            raise Exception(str(result_list))
        self.log.info(f'SUCCESS All Validations PASSED for {job_type} job {job_obj.job_id}')

    def aux_populator_validation(self):
        """Launches auxcopy and initiates the populator validations for aux"""
        try:
            self.log.info(
                'Setting GxGlobal Param bEnableAuxCopyPopulatorODS as true'
                ' to use Populator Framework for AuxCopy Jobs')
            self.commcell.add_additional_setting('CommServDB.GxGlobalParam', 'bEnableAuxCopyPopulatorODS',
                                                 'BOOLEAN', 'true')
            self.log.info('Launching AuxCopy Job')
            aux_copy_job = self.storage_policy.run_aux_copy()
            self.log.info('AuxCopy Job Initiated(Id: %s). Waiting for it to complete', aux_copy_job.job_id)
            if not aux_copy_job.wait_for_completion():
                raise Exception(
                    f'[AuxCopy Job(Id: {aux_copy_job.job_id}) Failed] with JPR: {aux_copy_job.delay_reason}')
            self.log.info('AuxCopy Job(Id: %s) Completed', aux_copy_job.job_id)
            self.run_validations(aux_copy_job, 'aux')
            return '', True
        except Exception as exe:
            result_string = f'Auxcopy Validations Failed with error: {str(exe)}'
            self.log.error(result_string)
            return result_string, False

    def dv2_populator_validation(self):
        """Launches dv2 and initiates the populator validations for dv2"""
        try:
            self.log.info(
                'Setting GxGlobal Param bEnablePopulatorODSForScalableDV as true'
                ' to use Populator Framework for DV2, Defrag jobs')
            self.commcell.add_additional_setting('CommServDB.GxGlobalParam', 'bEnablePopulatorODSForScalableDV',
                                                 'BOOLEAN', 'true')
            self.log.info('Fetching store object and Launching DV2 Job for Source Pool(Primary Copy)')
            engine = self.commcell.deduplication_engines.get(
                self.storage_pool_1.global_policy_name, self.storage_pool_1.copy_name)
            self.store = engine.get(engine.all_stores[0][0])
            dv2_job = self.store.run_ddb_verification(incremental_verification=False, quick_verification=False)
            self.log.info('DV2 Job Initiated(Id: %s). Waiting for it to complete', dv2_job.job_id)
            if not dv2_job.wait_for_completion():
                raise Exception(f'[DV2 Job(Id: {dv2_job.job_id}) Failed] with JPR: {dv2_job.delay_reason}')
            self.log.info('DV2 Job(Id: %s) Completed', dv2_job.job_id)
            self.run_validations(dv2_job, 'dv2')
            return '', True
        except Exception as exe:
            result_string = f'DV2 Validations Failed with error: {str(exe)}'
            self.log.error(result_string)
            return result_string, False

    def defrag_populator_validation(self):
        """Launches defrag and initiates the populator validations for defrag"""
        try:
            self.log.info("Global Param is bEnablePopulatorODSForScalableDV is already set earlier. Proceeding further")
            self.log.info('Launching Defrag Job')
            defrag_job = self.store.run_space_reclaimation()
            self.log.info('Defrag Job Initiated(Id: %s). Waiting for it to complete', defrag_job.job_id)
            if not defrag_job.wait_for_completion():
                raise Exception(f'[Defrag Job(Id: {defrag_job.job_id}) Failed] with JPR: {defrag_job.delay_reason}')
            self.log.info('Defrag Job(Id: %s) Completed', defrag_job.job_id)
            self.run_validations(defrag_job, 'defrag')
            return '', True
        except Exception as exe:
            result_string = f'Defrag Validations Failed with error: {str(exe)}'
            self.log.error(result_string)
            return result_string, False

    def run(self):
        """Run Function of this case"""
        self.log.info("Initiating Previous Run Cleanup")
        self.cleanup()
        try:
            self.initial_setup()
            result1, status1 = self.aux_populator_validation()
            result2, status2 = self.dv2_populator_validation()
            result3, status3 = self.defrag_populator_validation()
            if not (status1 and status2 and status3):
                raise Exception(f'{result1}\n{result2}\n{result3}')
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('Test Case Failed with Exception : %s', str(exe))

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info('Removing GxGlobal Params bEnableAuxCopyPopulatorODS, bEnablePopulatorODSForScalableDV')
        self.commcell.delete_additional_setting('CommServDB.GxGlobalParam', 'bEnableAuxCopyPopulatorODS')
        self.commcell.delete_additional_setting('CommServDB.GxGlobalParam', 'bEnablePopulatorODSForScalableDV')
        if self.status != constants.PASSED:
            self.log.error('Test Case FAILED. Please check logs for failure analysis')
        self.cleanup()
