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

    run()                 --  run function of this test case

    v2_indexing_check()   --  checks whether v2_indexing is enabled or not

    run_backup()          -- runs the backup of specified type

    run_auxcopy_validation() --  checks that auxcopy has copied the data successfully

    fetch_copied_times()     --  fetches the copied time of the job to Secondary Copy

    fetch_primary_count()    -- fetches the count of primary objects for job in Both DDBs

    tear_down()              --  tear down function of this test case

tcInputs to be passed in JSON File:
    BackupVM                : Pattern that matches to set of vm's to be backed up
    PrimaryCopyMediaAgent   : Name of a MediaAgent machine - we create primary copy here
    SecondaryCopyMediaAgent : Name of a MediaAgent machine - we create secondary copy here

    Note: Both the MediaAgents can be the same machine

        : Sample Input Format for BackupVM:
            -suppose there are 3 vm's with names as (vmtestclient1, vmtestclient2, vmtestclient3),
            pass input as: "vmtestclient" this would match all the above vm's

Steps:

1: Check V2 Indexing is enabled or not

2: Configure the environment:
    - create a Library, Storage Policy(secondary copy space-optimized), a BackupSet,a SubClient

3: Run Backups on the subclient in order: F_I_F_I_SF

4: Run AuxCopy

5: Run AuxCopy Validation:
    - auxCopyStatus is 100 for all entries in JMJobDataStats for this Policy
    - Count of archFiles for both the copies are same in archFileCopy table

6: Run the Validations whether SpaceOptimized Copy feature worked as expected:
    - Full Backups should be copied first
    - PrimaryObjects count for 1st Full should be equal in both copies
    - PrimaryObjects count for 2nd Incremental in Secondary Copy is 0
    - PrimaryObjects count for Synthetic full in Primary Copy is 0
    - Total Primary objects count in both copies should be equal

7: CleanUp the environment
"""
from cvpysdk.constants import VSAObjects

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
        self.name = 'ArchiveManager - Space Optimized Auxcopy with VSA V2 subclients'
        self.tcinputs = {
            "BackupVM": None,
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
        self.backup_vm_name = None
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ddb_path = None
        self.ma_1_path = None
        self.ma_2_path = None
        self.mount_path = None
        self.client_path = None
        self.mount_path_2 = None
        self.content_path = None
        self.copy_ddb_path = None
        self.subclient = None
        self.copy_name = None
        self.library_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_policy = None
        self.storage_policy_name = None

    def setup(self):
        """Setup function of this test case"""
        self.ma_machine_1 = Machine(self.tcinputs['PrimaryCopyMediaAgent'], self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        utility = OptionsSelector(self.commcell)

        self.backup_vm_name = self.tcinputs['BackupVM']

        self.backupset_name = str(self.id) + '_BS'
        self.subclient_name = str(self.id) + '_SC'
        primary_ma_drive = utility.get_drive(self.ma_machine_1, 150*1024)
        secondary_ma_drive = utility.get_drive(self.ma_machine_2, 150*1024)
        self.ma_1_path = primary_ma_drive + 'test_' + str(self.id) + self.ma_machine_1.os_sep
        self.ma_2_path = secondary_ma_drive + 'test_' + str(self.id) + self.ma_machine_2.os_sep
        self.ddb_path = self.ma_1_path + 'DDB'
        self.mount_path = self.ma_1_path + 'MP'
        self.mount_path_2 = self.ma_2_path + 'MP2'
        self.copy_ddb_path = self.ma_2_path + 'copy_DDB'
        self.copy_name = str(self.id) + '_Copy'
        self.library_name = str(self.id) + '_Lib'
        self.storage_policy_name = str(self.id) + '_SP'
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def run(self):
        """Run Function of this case"""
        try:
            # 1: Check V2 Indexing is enabled or not
            self.v2_indexing_check()
            # 2: Configure the environment
            self.mm_helper.configure_disk_library(self.library_name,
                                                  self.tcinputs['PrimaryCopyMediaAgent'],
                                                  self.mount_path)
            self.mm_helper.configure_disk_library(self.library_name + '_2',
                                                  self.tcinputs['SecondaryCopyMediaAgent'],
                                                  self.mount_path_2)
            self.storage_policy = self.dedupe_helper.configure_dedupe_storage_policy(
                self.storage_policy_name,
                self.library_name,
                self.tcinputs['PrimaryCopyMediaAgent'],
                self.ddb_path)
            primary_copy = self.storage_policy.get_copy('Primary')
            # By default we create space optimized copy in Automation
            storage_policy_copy = self.dedupe_helper.configure_dedupe_secondary_copy(
                self.storage_policy,
                self.copy_name,
                self.library_name + '_2',
                self.tcinputs['SecondaryCopyMediaAgent'],
                self.copy_ddb_path,
                self.tcinputs['SecondaryCopyMediaAgent'])

            self.backupset = self.mm_helper.configure_backupset(self.backupset_name)
            content = {
                'type': VSAObjects.VMName,
                'name': '*' + self.tcinputs['BackupVM'] + '*',
                'display_name': '*' + self.tcinputs['BackupVM'] + '*'
            }
            self.subclient = self.mm_helper.configure_subclient(content_path=content)

            # Remove association for StoragePolicy with System created AutoCopy Schedule
            self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.copy_name)

            # 3: Run Backups on the subclient in order: F_I_F_I_SF
            self.log.info('Running backupJobs in order F_I_F_I_SF')
            full_1 = self.run_backup("Full")
            incremental_1 = self.run_backup("Incremental")
            full_2 = self.run_backup("Full")
            incremental_2 = self.run_backup("Incremental")
            synth_job = self.run_backup("Synthetic_full")

            # 4: Run AuxCopy
            self.log.info('Running AuxCopy Job with Scalable Resource Allocation')
            aux_copy_job = self.storage_policy.run_aux_copy()
            if aux_copy_job.wait_for_completion():
                self.log.info('AuxCopy Completed(Id: %s)', aux_copy_job.job_id)
            else:
                raise Exception('AuxCopy Failed(Id: %s)' % aux_copy_job.job_id)

            self.log.info('**************************** VALIDATIONS *****************************')

            # 5: Run AuxCopy Validation
            self.run_auxcopy_validation(self.storage_policy.storage_policy_id,
                                        primary_copy.copy_id, storage_policy_copy.copy_id)

            # 6: Run the Validations whether SpaceOptimized Copy feature worked as expected:
            self.log.info('***** CASE 1: Order of Jobs -> Fulls copied 1st, Remaining Later *****')
            self.log.info('Fetching Copied Times')
            time_1 = self.fetch_copied_times(storage_policy_copy.copy_id, full_1)
            time_2 = self.fetch_copied_times(storage_policy_copy.copy_id, incremental_1)
            time_4 = self.fetch_copied_times(storage_policy_copy.copy_id, full_2)
            time_3 = self.fetch_copied_times(storage_policy_copy.copy_id, incremental_2)
            time_5 = self.fetch_copied_times(storage_policy_copy.copy_id, synth_job)

            max_copy_time = max(time_1 + time_4 + time_5)
            min_copy_time = min(time_2 + time_3)
            if max_copy_time < min_copy_time:
                self.log.info('SUCCESS Result: Passed')
            else:
                self.status = constants.FAILED
                self.log.error('ERROR Result: Failed')

            count_0, count_1 = self.fetch_primary_count(full_1)
            count_2, count_3 = self.fetch_primary_count(incremental_1)
            count_4, count_5 = self.fetch_primary_count(full_2)
            count_6, count_7 = self.fetch_primary_count(incremental_2)
            count_8, count_9 = self.fetch_primary_count(synth_job)

            self.log.info('**** CASE 2: PrimaryObjectsCount for 1st Full: Sec_Copy = Primary ****')
            # Tolerance of 25 is given
            if abs(count_0 - count_1) <= 25:
                self.log.info('SUCCESS Result: Passed : %d, %d', count_0, count_1)
            else:
                self.log.error('ERROR Result: Failed : %d, %d', count_0, count_1)
                self.status = constants.FAILED

            self.log.info('**** CASE 3: PrimaryObjectsCount for 2nd Incremental: Sec_Copy = 0 ***')
            if count_7 == 0:
                self.log.info('SUCCESS Result: PASSED')
            else:
                self.log.error('ERROR Result: FAILED: %d', count_7)
                self.status = constants.FAILED

            self.log.info('********* CASE 4: PrimaryObjectsCount for SFull: Primary = 0 *********')
            if count_8 == 0:
                self.log.info('SUCCESS Result: PASSED')
            else:
                self.log.error('ERROR Result: FAILED: %s', count_8)
                self.status = constants.FAILED

            self.log.info('******* CASE 5: Sum of PrimaryObjectsCount : Sec_Copy = Primary ******')
            total_in_primary = count_0 + count_2 + count_4 + count_6 + count_8
            total_in_secondary = count_1 + count_3 + count_5 + count_7 + count_9
            if abs(total_in_primary - total_in_secondary) <= 25:
                self.log.info('SUCCESS Result: PASSED %d %d', total_in_primary, total_in_secondary)
            else:
                self.status = constants.FAILED
                self.log.error('ERROR Result: FAILED %d %d', total_in_primary, total_in_secondary)

        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('Exception Occurred : %s', str(exe))

    def v2_indexing_check(self):
        """
        Check if V2 indexing is enabled
            Enabled     : Pass
        Raises:
            Exception   : If v2 indexing is not enabled
        """
        query = f"""select attrval from app_clientprop 
                where componentNameId = {self.client.client_id} 
                and attrname like 'IndexingV2_VSA'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", result[0])
        if result[0] != '' and int(result[0]) == 1:
            self.log.info('V2 Indexing is enabled')
        else:
            raise Exception('V2 Indexing is not enabled')

    def run_backup(self, backup_type):
        """Runs Backup of specified type and waits for job till it completes

        Args:
            backup_type    (str)  :   Type of backup to Run
        Return:
            (list)                :   List of Job Id's
        """
        job = self.subclient.backup(backup_level=backup_type)
        # for synthetic fulls, if the content has multiple vm's, sc.backup() return list of SF jobs
        if backup_type == 'Synthetic_full' and isinstance(job, list):
            for each_job in job:
                if each_job.wait_for_completion():
                    self.log.info('%s Backup job Completed(Id: %s)', backup_type, each_job.job_id)
                else:
                    raise Exception('%s Backup Job Failed(Id:%s)' % (backup_type, each_job.job_id))
            return [each_job.job_id for each_job in job]
        if backup_type == 'Synthetic_full':
            if job.wait_for_completion():
                self.log.info('%s Backup job Completed(Id: %s)', backup_type, job.job_id)
            else:
                raise Exception('%s Backup Job Failed(Id: %s)' % (backup_type, job.job_id))
            return [job.job_id]

        if job.wait_for_completion():
            self.log.info('%s Backup job Completed(Id: %s)', backup_type, job.job_id)
        else:
            raise Exception('%s Backup Job Failed(Id: %s)' % (backup_type, job.job_id))

        query = '''select distinct childJobId
                from JMJobdatalink where parentJobId = {0}'''.format(job.job_id)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        return [str(row[0]) for row in rows]

    def run_auxcopy_validation(self, policy_id, primary_id, secondary_id):
        """
        Checks whether aux-copy has succeeded or not

        Args:
            policy_id      (str) : Id of StoragePolicy
            primary_id     (str) : Copy Id of Primary Copy
            secondary_id   (str) : Copy Id of Secondary Copy
        """
        self.log.info('**** VALIDATION: auxCopyStatus=100 for all entries in JMJobDataStats *****')

        query = '''select count(1) from JMJobDataStats
                where archGrpId = {0} and auxCopyStatus<>100'''.format(policy_id)
        self.log.info('Query: %s', query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info('Result: %s', str(rows))
        if int(rows[0][0]) != 0:
            self.log.error('FAILED: auxCopyStatus(JMJobDataStats) not 100 for few entries')
            self.status = constants.FAILED
        else:
            self.log.info('SUCCESS: auxCopyStatus(JMJobDataStats) is 100')

        self.log.info('******** VALIDATION: archFile Count Same in Both the Copies *********')

        query = '''select count(1) from archFileCopy
                where archCopyId in ({0},{1})
                group by archCopyId'''.format(primary_id, secondary_id)
        self.log.info('Query: %s', query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info('Result: %s', str(rows))

        if int(rows[0][0]) != int(rows[1][0]):
            self.log.error('FAILED: Count of archFiles mismatch for the Copies')
            self.status = constants.FAILED
        else:
            self.log.info('VALIDATION: SUCCESS')

    def fetch_copied_times(self, copy_id, job_ids):
        """Returns copiedTime from JMJobDataStats

        Args:
            copy_id   (str)  :   Id of Storage Policy Copy
            job_ids   (list) :   List of Backup Job Ids
        Return:
            (list)           :   List of Copied times of Job to the Secondary Copy
        """
        job_ids_string = ','.join(job_ids)
        query = '''select distinct copiedTime from JMJobDataStats
                where archGrpCopyId = {0} and jobId in ({1})
                '''.format(copy_id, job_ids_string)
        self.log.info('Executing Query: %s', query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        result = [int(row[0]) for row in rows]
        self.log.info('Copied Time(s) : %s', str(result))
        return result

    def fetch_primary_count(self, job_ids):
        """Returns Count of primary Objects for the job in Primary and Secondary Copies

        Args:
            job_ids    (list)  : List of Backup Job Id's
        Return:
            (tuple)            : 2 lists having count of PrimaryObjects for each job
                                 in DDBs of both copies
        """
        result_1 = []
        result_2 = []
        for job_id in job_ids:
            result_1.append(self.dedupe_helper.get_primary_objects_sec(job_id, 'Primary'))
            result_2.append(self.dedupe_helper.get_primary_objects_sec(job_id, self.copy_name))
        result_1 = list(map(int, result_1))
        result_2 = list(map(int, result_2))
        return sum(result_1), sum(result_2)

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 5: CleanUp the environment
        try:
            # if self.is_vsa:
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                # re-associate subclients to Not Assigned state
                request_xml = '''<App_ReassociateStoragePolicyReq>
                                    <forceNextBkpToFull>1</forceNextBkpToFull>
                                    <runSyntheticFullForTurbo/>
                                    <currentStoragePolicy>
                                        <storagePolicyName>{0}</storagePolicyName>
                                    </currentStoragePolicy>
                                    <newStoragePolicy>
                                        <storagePolicyName>CV_DEFAULT</storagePolicyName>
                                    </newStoragePolicy>
                                </App_ReassociateStoragePolicyReq>
                                '''.format(self.storage_policy_name)
                self.commcell.qoperation_execute(request_xml)
                self.log.info("Deleting storage policy  %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            self.commcell.disk_libraries.delete(self.library_name)
            self.commcell.disk_libraries.delete(self.library_name + '_2')

            self.mm_helper.remove_content(self.ma_1_path, self.ma_machine_1)
            if self.tcinputs['PrimaryCopyMediaAgent'] != self.tcinputs['SecondaryCopyMediaAgent']:
                self.mm_helper.remove_content(self.ma_2_path, self.ma_machine_2)
        except Exception as exe:
            self.log.error('ERROR in TearDown. Might need to Cleanup Manually: %s', str(exe))
