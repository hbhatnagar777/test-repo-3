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
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case

    tear_down()         --  tear down function of this test case

    run_backup()        --  runs the backup of specified type

    v2_indexing_check()         --  checks whether v2_indexing is enabled or not

    run_backups_validation()    --  checks that type of backups performed for vm's are correct

    run_ddb_validation()        --  runs DV2 and waits for successful completion

    run_auxcopy_validation()    --  checks that auxcopy has copied the data successfully

tcInputs to be passed in JSON File:

    VMPattern1              : Pattern that matches to set of vm's - matched vm's will be backed up
    VMPattern2              : Another Pattern that matches to another set of vm's
    PrimaryCopyMediaAgent   : Name of a MediaAgent machine - we create primary copy here
    SecondaryCopyMediaAgent : Name of a MediaAgent machine - we create secondary copy here

    Note: Both the MediaAgents can be the same machine

        : Sample Input Format for BackupVM:
            -suppose there are 3 vm's with names as (vmtestclient1, vmtestclient2, vmtestclient3),
            pass input as: "vmtestclient" this would match all the above vm's
Steps:

1: Check V2 Indexing is enabled or not

2: Configure the environment: create a library,Storage Policy, a BackupSet, a SubClient(VMPattern1)

3: Run a Backup, Reconfigure Subclient(content) to include more VM's(VMPattern2), Run Backup again

4: Run Backup Validation
    - 1st Backup: All of the VM's -> Full backup
    - 2nd Backup: Newly added VM's -> Full, Old Vm's -> Incremental

5: Run AuxCopy

6: Run Validations:
    - AuxCopy:  i) auxCopyStatus is 100 for all entries in JMJobDataStats for this Policy
                ii) Count of archFiles for both the copies are same in archFileCopy table
    - DV2   :   Run DV2 and wait for successful Completion

7: CleanUp the environment
"""
from cvpysdk.job import Job
from cvpysdk.constants import VSAObjects

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
        self.name = 'ArchiveManager - Basic AuxCopy Scenario with VSA V2 subclients'
        self.tcinputs = {
            "VMPattern1": None,
            "VMPattern2": None,
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.ddb_path = None
        self.ma_1_path = None
        self.ma_2_path = None
        self.mount_path = None
        self.mount_path_2 = None
        self.content = None
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
        self.backupset_name = str(self.id) + '_BS'
        self.subclient_name = str(self.id) + '_SC'
        primary_ma_drive = utility.get_drive(self.ma_machine_1, 80*1024)
        secondary_ma_drive = utility.get_drive(self.ma_machine_2, 80*1024)
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

            # By default we create space optimized copy in Automation
            primary_copy = self.storage_policy.get_copy('Primary')
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
                'name': '*' + self.tcinputs['VMPattern1'] + '*',
                'display_name': '*' + self.tcinputs['VMPattern1'] + '*'
            }
            self.subclient = self.mm_helper.configure_subclient(content_path=content)

            # Remove association for StoragePolicy with System created AutoCopy Schedule
            self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.copy_name)

            # 3: Run a Backup, Reconfigure Subclient, Run Backup Again
            self.log.info('Running Full Backup')
            backup_list_1 = self.run_backup("Full")

            self.log.info("Adding more VM's to subclient")
            self.subclient.content = [
                {
                    'type': VSAObjects.VMName,
                    'name': '*' + self.tcinputs['VMPattern1'] + '*',
                    'display_name': '*' + self.tcinputs['VMPattern1'] + '*'
                },
                {
                    'type': VSAObjects.VMName,
                    'name': '*' + self.tcinputs['VMPattern2'] + '*',
                    'display_name': '*' + self.tcinputs['VMPattern2'] + '*'
                }
            ]
            backup_list_2 = self.run_backup("Incremental")

            # 4: Run Backup Validation
            self.run_backups_validation(backup_list_1, backup_list_2)

            # 5: Run AuxCopy
            self.log.info('Running AuxCopy Job with Scalable Resource Allocation')
            aux_copy_job = self.storage_policy.run_aux_copy()
            if aux_copy_job.wait_for_completion():
                self.log.info('AuxCopy Completed(Id: %s)', aux_copy_job.job_id)
            else:
                raise Exception('AuxCopy Failed(Id: %s)' % aux_copy_job.job_id)

            # 6: Run Validations:
            self.log.info('********************** VALIDATIONS **********************')
            self.run_auxcopy_validation(self.storage_policy.storage_policy_id,
                                        primary_copy.copy_id, storage_policy_copy.copy_id)
            self.run_ddb_validation(primary_copy.copy_id, storage_policy_copy.copy_id)
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('Exception Occurred : %s', str(exe))

    def run_backup(self, backup_type):
        """
        Runs Backup of specified type and waits for job till it completes

        Args:
                backup_type    (str)  :   Type of Backup to Initiate
        Return:
                (list)                :   List of Job Id's
        """
        job = self.subclient.backup(backup_level=backup_type)

        if job.wait_for_completion():
            self.log.info('%s Backup job Completed(Id: %s)', backup_type, job.job_id)
        else:
            raise Exception('%s Backup Job Failed(Id: %s)' % (backup_type, job.job_id))

        query = '''select distinct childJobId
                from JMJobdatalink where parentJobId = {0}'''.format(job.job_id)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        return [int(row[0]) for row in rows]

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

    def run_backups_validation(self, backup_1_list, backup_2_list):
        """
        Validate if new vm's in first backup get incremental and others get full backup

        Args:
            backup_1_list   (list): List of Child backup Job Id's for 1st Backup
            backup_2_list   (list): List of Child backup Job Id's for 2nd Backup
        Raises:
            Exception:  If validation fails
        """
        self.log.info('*** VALIDATION: No.of fulls in 1st Job = No.of Incrementals in 2nd Job ***')
        first_backups_list = [Job(self.commcell, job_id) for job_id in backup_1_list]
        second_backups_list = [Job(self.commcell, job_id) for job_id in backup_2_list]
        first_fulls = set()
        second_fulls = set()
        second_incrementals = set()
        for job in first_backups_list:
            if job.backup_level == 'Full':
                first_fulls.add(job.client_name)
        for job in second_backups_list:
            if job.backup_level == 'Incremental':
                second_incrementals.add(job.client_name)
            elif job.backup_level == 'Full':
                second_fulls.add(job.client_name)
        self.log.info('First Full VMs: %s', str(first_fulls))
        self.log.info('Second Full VMs: %s', str(second_fulls))
        self.log.info('Second Incremental VMs: %s', str(second_incrementals))
        if first_fulls == second_incrementals:
            self.log.info('SUCCESS: Validation PASSED')
        else:
            raise Exception("ERROR: Validation FAILED: Fulls(1st Job) != Incrementals(2nd Job)")

    def run_ddb_validation(self, primary_id, secondary_id):
        """
        Runs DDB Verification Jobs and waits for successful completion

        Args:
            primary_id      (str) : Copy Id of Primary Copy
            secondary_id    (str) : Copy Id of Secondary Copy
        """
        self.log.info('***** VALIDATION: Running DDB Verification on DDBs of both the copies ****')
        self.storage_policy.run_ddb_verification('Primary', 'FULL',
                                                 'DDB_AND_DATA_VERIFICATION')
        self.storage_policy.run_ddb_verification(self.copy_name, 'FULL',
                                                 'DDB_AND_DATA_VERIFICATION')

        # Fetching ddb job id's since above method returns DV2 job for FS, we need for VS
        import time
        time.sleep(60)
        query = '''select distinct jobid 
                from JMAdminJobInfoTable
                where archGrpCopyID = {0}'''.format(primary_id)
        self.csdb.execute(query)
        rows_1 = self.csdb.fetch_all_rows()
        query = '''select distinct jobid 
                from JMAdminJobInfoTable
                where archGrpCopyID = {0}'''.format(secondary_id)
        self.csdb.execute(query)
        rows_2 = self.csdb.fetch_all_rows()

        for row in rows_1:
            job = Job(self.commcell, row[0])
            if job.wait_for_completion():
                self.log.info('DDB Job:(Id: %s)(on Primary Copy) Completed', job.job_id)
            else:
                self.log.error('DDB Job:(Id: %s)(on Primary Copy) Failed', job.job_id)
                self.status = constants.FAILED

        for row in rows_2:
            job = Job(self.commcell, row[0])
            if job.wait_for_completion():
                self.log.info('DDB Job:(Id: %s)(on Secondary Copy) Completed', job.job_id)
            else:
                self.log.error('DDB Job:(Id: %s)(on Secondary Copy) Failed', job.job_id)
                self.status = constants.FAILED

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
            self.log.info('SUCCESS: Validation PASSED')

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 7: CleanUp the environment
        try:
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
            self.result_string += "Error encountered during cleanup : %s" % str(exe)
