# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase to perform Inline & Parallel copy case for Aux copy

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                -- initialize TestCase class

    _v2_indexing_check()      -- checks whether V2 indexing is enabled or not

    _run_auxcopy_validation() -- checks whether data has been copied successfully

    _validate_inline_copy()   -- validates inline copy functionality by checking for job status
                                 on secondary copy in JMJobDataStats

    _get_stream_reader_id()   -- gets StreamReaderId is used for reading
                                 for both copies in ArchJobStreamStatus

    _validate_parallel_copy() -- validates inline copy by checking that same StreamReaderId is
                                 used for reading for both copies in ArchJobStreamStatus

    _cleanup()                -- cleanup the entities created

    setup()                   -- setup function of this test case

    run()                     -- run function of this test case

    tear_down()               -- teardown function of this test case

tcInputs to be passed in JSON File:
    MediaAgentName  : Name of a MediaAgent machine
    BackupVM        : Pattern that matches to set of vm's to be backed up

    Note: Sample Input Format for BackupVM:
            -suppose there are 3 vm's with names as (vmtestclient1, vmtestclient2, vmtestclient3),
            pass input as: "vmtestclient" this would match all the above vm's

Steps:

1: Check v2 Indexing is enabled or not

2: Configure the test environment:
    -   Create Library, StoragePolicy
    -   Create 2 non-dedupe SecondaryCopies(with inline and parallel copy enabled on both)
    -   Create BackupSet, Subclient

3: Run 2 Full Backups

4: Validate inline copy functionality

5: Picking jobs for recopy on both copies and running AuxCopy

6: Run Auxcopy Validation

7: Validate parallel copy functionality

8: CleanUp the test environment
"""
from cvpysdk.constants import VSAObjects

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "ArchiveManager - Inline & Parallel copy case for VSA V2 subclients"
        self.tcinputs = {
            "MediaAgentName": None,
            "BackupVM": None
        }
        self.disk_library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mountpath = None
        self.partition_path = None
        self.backup_vm_name = None
        self.content_path = None
        self.dedupehelper = None
        self.library_name = None
        self.mmhelper = None
        self.common_util = None
        self.ma_machine = None

    def _v2_indexing_check(self):
        """
        Check if V2 indexing is enabled
            Enabled     : Pass
            Not Enabled : Raise Exception
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

    def _run_auxcopy_validation(self, policy_id, primary_id, secondary_id, tertiary_id):
        """
        Checks whether aux-copy has succeeded or not

        Args:
            policy_id      (str) : Id of StoragePolicy
            primary_id     (str) : Copy Id of Primary Copy
            secondary_id   (str) : Copy Id of Secondary Copy
            tertiary_id    (str) : Copy Id of Tertiary Copy
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

        self.log.info('******** VALIDATION: archFile Count Same in All Copies *********')

        query = '''select count(1) from archFileCopy
                where archCopyId in ({0},{1},{2})
                group by archCopyId'''.format(primary_id, secondary_id, tertiary_id)
        self.log.info('Query: %s', query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info('Result: %s', str(rows))

        if not(int(rows[0][0]) == int(rows[1][0]) == int(rows[2][0])):
            self.log.error('FAILED: Count of archFiles Mismatch')
            self.status = constants.FAILED
        else:
            self.log.info('SUCCESS: Validation PASSED')

    def _validate_inline_copy(self, job_ids, copy_id):
        """
        Validates inline copy by checking for job status on secondary copy in JMJobDataStats
        Args:
            job_ids (list)  : backup job id's to check in table
            copy_id (int)   : copy id to validate on
        Return:
            (Bool) True if status of job is 100/ False if not
        """
        for job_id in job_ids:
            query = """select status from JMJobDataStats 
                    where jobId = {0} and archGrpCopyId = {1}""".format(job_id, copy_id)
            self.log.info("QUERY: {0}".format(query))
            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            self.log.info("RESULT: {0}".format(cur))
            if cur == ['']:
                return False
            if int(cur[0]) != 100:
                return False
        return True

    def get_child_jobs(self, parent_job_id):
        """
        Returns list of child jobs spawned for the given parent jobs

        Args:
            parent_job_id (str):  Job Id of the Parent Job

        Return:
            (list)             :  List of Job Id's of child jobs spawned from the parent job
        """
        query = '''select distinct childJobId
                from JMJobDataLink
                where parentJobId = %s''' % parent_job_id
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        return [row[0] for row in rows]

    def _validate_parallel_copy(self, id_list):
        """
        Validates Parallel copy functionality by checking that no single chunk(that is to be
        copied) is read by multiple stream readers

        Note: This not a definite validation as Parallel Copy is an "attempt" to copy parallel, but
        sometimes cannot be possible due to resources availability/locks. So it can fail Sometimes
        Args:
            id_list (list): list of id's of StoragePolicy Copies to validate on
        Return:
            (Bool) True if StreamReaderIds are matching for all the chunks/ False if not
        """

        query = '''select count(*)
                from archchunktoreplicatehistory
                where archchunkid in 
                    (SELECT archchunkid
                    FROM archchunktoreplicatehistory
                    WHERE DestCopyId in ({0},{1})
                    GROUP BY archchunkid
                    HAVING COUNT(distinct streamReaderID) > 1)
                and DestCopyId in ({0},{1})
                '''.format(id_list[0], id_list[1])
        self.log.info('Executing Query: %s', query)
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info('Result: %s', str(row[0]))
        if int(row[0]) == 0:
            return True
        return False

    def _cleanup(self):
        """Cleanup the entities created"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete backupset
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            # Delete Storage Policy
            self.log.info("Deleting storage policy: %s if exists", self.storage_policy_name)
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
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted storage policy: %s", self.storage_policy_name)

            # Delete Library
            self.log.info("Deleting library: %s if exists", self.disk_library_name)
            if self.commcell.disk_libraries.has_library(self.disk_library_name):
                self.commcell.disk_libraries.delete(self.disk_library_name)
                self.log.info("Deleted library: %s", self.disk_library_name)

            # Run DataAging
            data_aging_job = self.commcell.run_data_aging()
            self.log.info("Data Aging job [%s] has started.", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.", data_aging_job.job_id,
                    data_aging_job.delay_reason)
                raise Exception(
                    "Data Aging job [%s] has failed with %s." % (data_aging_job.job_id,
                                                                 data_aging_job.delay_reason))
            self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            self.result_string += "Error encountered during cleanup : %s" % str(exp)
        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        self.disk_library_name = '%s_library' % str(self.id)
        self.storage_policy_name = '%s_storage_policy' % str(self.id)
        self.backupset_name = '%s_BS' % str(self.id)
        self.subclient_name = '%s_SC' % str(self.id)

        self._cleanup()

        self.ma_machine = Machine(self.tcinputs['MediaAgentName'], self.commcell)

        # To select drive with space available in ma machine
        self.log.info('Selecting drive in the MA machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=(180 * 1024))
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.mountpath = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP')

        self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation',
                                                        str(self.id), 'DDB')

        self.backup_vm_name = self.tcinputs['BackupVM']
        self.content_path = {
            'type': VSAObjects.VMName,
            'name': '*' + self.backup_vm_name + '*',
            'display_name': '*' + self.backup_vm_name + '*',
        }

        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        self.common_util = CommonUtils(self)

    def run(self):
        """Run function of this test case"""

        try:
            self._v2_indexing_check()
            self.mmhelper.configure_disk_library(self.disk_library_name,
                                                 self.tcinputs['MediaAgentName'],
                                                 self.mountpath)
            sp_dedup_obj = self.dedupehelper.configure_dedupe_storage_policy(
                self.storage_policy_name,
                self.disk_library_name,
                self.tcinputs['MediaAgentName'],
                self.partition_path)

            # Enable MA side dedupe  on client
            self.client.set_dedup_property('clientSideDeduplication', 'OFF')

            # Set retention of 0day 1cycle
            self.log.info("Setting Retention on Primary Copy")
            sp_dedup_primary_obj = sp_dedup_obj.get_copy("Primary")
            retention = (1, 1, -1)
            sp_dedup_primary_obj.copy_retention = retention

            # Enable encryption on Primary copy
            encryption = (True, 'BLOWFISH', 128, False)
            sp_dedup_primary_obj.copy_reencryption = encryption

            # create first non-dedupe secondary copy
            copy1_non_dedupe = '%s_copy1_nondedupe' % str(self.id)
            copy1_non_dedupe_obj = self.mmhelper.configure_secondary_copy(
                copy1_non_dedupe,
                self.storage_policy_name,
                self.disk_library_name,
                self.tcinputs['MediaAgentName'])
            # Enable parallel copy
            copy1_non_dedupe_obj.set_parallel_copy(True)

            # Enable inline copy
            copy1_non_dedupe_obj.set_inline_copy(True)

            # create second non-dedupe secondary copy
            copy2_non_dedupe = '%s_copy2_nondedupe' % str(self.id)
            copy2_non_dedupe_obj = self.mmhelper.configure_secondary_copy(
                copy2_non_dedupe,
                self.storage_policy_name,
                self.disk_library_name,
                self.tcinputs['MediaAgentName'])

            # Removing association with System Created Automatic Auxcopy schedule
            self.log.info("Removing association with System Created Autocopy schedule")
            self.mmhelper.remove_autocopy_schedule(self.storage_policy_name, copy1_non_dedupe)
            self.mmhelper.remove_autocopy_schedule(self.storage_policy_name, copy2_non_dedupe)

            # Enable parallel copy
            copy2_non_dedupe_obj.set_parallel_copy(True)

            # Enable inline copy
            copy2_non_dedupe_obj.set_inline_copy(True)

            self.backupset = self.mmhelper.configure_backupset(self.backupset_name, self.agent)
            sc_obj = self.mmhelper.configure_subclient(self.backupset_name, self.subclient_name,
                                                       self.storage_policy_name, self.content_path,
                                                       self.agent)

            # Allow multiple data readers to subclient
            self.log.info("Setting Data Readers=10 on Subclient")
            sc_obj.allow_multiple_readers = True
            sc_obj.data_readers = 10

            # Backup Job J1
            job1_obj = sc_obj.backup(backup_level="Full")
            if job1_obj.wait_for_completion():
                self.log.info('1st Backup Job(Id: %s) Completed', job1_obj.job_id)
            else:
                self.log.error('1st Backup Job(Id: %s) Failed', job1_obj.job_id)
            # Backup Job J2
            job2_obj = sc_obj.backup(backup_level="Full")
            if job2_obj.wait_for_completion():
                self.log.info('1st Backup Job(Id: %s) Completed', job2_obj.job_id)
            else:
                self.log.error('1st Backup Job(Id: %s) Failed', job2_obj.job_id)

            job1_list = self.get_child_jobs(job1_obj.job_id)
            job2_list = self.get_child_jobs(job2_obj.job_id)

            # 4: Validate inline copy functionality

            #   validating inline copy for job1 on copy1
            if self._validate_inline_copy(job1_list, int(copy1_non_dedupe_obj.copy_id)):
                self.log.info("Inline copy for 1st Backup on copy1 was success")
            else:
                self.log.error("Inline copy for 1st Backup on copy1 failed")
                raise Exception("Inline copy for 1st Backup on copy1 failed")

            #   validating inline copy for job1 on copy2
            if self._validate_inline_copy(job1_list, int(copy2_non_dedupe_obj.copy_id)):
                self.log.info("Inline copy for 1st Backup on copy2 was success")
            else:
                self.log.error("Inline copy for 1st Backup on copy2 failed")
                raise Exception("Inline copy for 1st Backup on copy2 failed")

            #   validating inline copy for job2 on copy1
            if self._validate_inline_copy(job2_list, int(copy1_non_dedupe_obj.copy_id)):
                self.log.info("Inline copy for 2nd Backup on copy1 was success")
            else:
                self.log.error("Inline copy for 2nd Backup on copy1 failed")
                raise Exception("Inline copy for 2nd Backup on copy1 failed")

            #   validating inline copy for job2 on copy2
            if self._validate_inline_copy(job2_list, int(copy2_non_dedupe_obj.copy_id)):
                self.log.info("Inline copy for 2nd Backup on copy2 was success")
            else:
                self.log.error("Inline copy for 2nd Backup on copy2 failed")
                raise Exception("Inline copy for 2nd Backup on copy2 failed")

            # 5: Picking jobs for recopy on both copies and running AuxCopy
            # Picking jobs J1 and J2 for recopy on copy1
            copy1_non_dedupe_obj.recopy_jobs(job1_obj.job_id + ", " + job2_obj.job_id)
            #   Picking jobs J1 and J2 for recopy on copy2
            copy2_non_dedupe_obj.recopy_jobs(job1_obj.job_id + ", " + job2_obj.job_id)

            # Run Aux copy Job
            auxcopy_job = sp_dedup_obj.run_aux_copy()

            self.log.info("Auxcopy job [%s] has started.", auxcopy_job.job_id)
            if not auxcopy_job.wait_for_completion():
                self.log.error("Auxcopy job [%s] has failed with %s.", auxcopy_job.job_id,
                               auxcopy_job.delay_reason)
                raise Exception("Auxcopy job [%s] has failed with %s" % (auxcopy_job.job_id,
                                                                         auxcopy_job.delay_reason))
            self.log.info("Auxcopy job [%s] has completed.", auxcopy_job.job_id)

            # 6: Run Auxcopy Validation
            self._run_auxcopy_validation(sp_dedup_obj.storage_policy_id,
                                         sp_dedup_primary_obj.copy_id,
                                         copy1_non_dedupe_obj.copy_id,
                                         copy2_non_dedupe_obj.copy_id)

            # 7: Validate parallel copy functionality
            if self._validate_parallel_copy(
                    [copy1_non_dedupe_obj.copy_id, copy2_non_dedupe_obj.copy_id]):
                self.log.info("SUCCESS for Parallel copy as streamReaderId match for both copies")
            else:
                raise Exception("FAIL for Parallel copy as streamReaderId didn't match for copies")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""
        # 8: CleanUp the test environment
        # revert back dedupe default setting on client
        self.client.set_dedup_property('clientSideDeduplication', 'USE_SPSETTINGS')

        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning the test environment ...")
            self._cleanup()
        else:
            self.log.error("Testcase shows failure in execution, not cleaning test environment ..")
