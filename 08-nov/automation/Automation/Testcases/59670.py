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

    cleanup()       --  cleans up the entities

    tear_down()     --  tear down function of this test case

tcInputs to be passed in JSON File:
59670: {
    "ClientName"          : Client which has the subclient. Restore job will restore to this machine
    "AgentName"           : File System
    "BackupsetName"       : BackupSet to be used (pre-existing)
    "SubclientName"       : Subclient to be used (pre-existing, with backups run already)
    "StoragePolicyName"   : StoragePolicy to be used (pre-existing,associated to above subclient)
    "PrimaryCopy_v11MA"   : Latest v11 MA to which the MountPath Used by the old MA is shared
    "SecondaryCopy_v11MA" : Latest v11 MA on which new library(for Secondary Copy) will be created
}
Steps:

1: Configure the entities:
    - create a new library, new secondary copy on Storage Policy with new library as DataPath

2: Initiate AuxCopy. Wait for completion and validate the MA used for AuxCopy

3: Pick Jobs for DataVerification on the Primary Copy

4: Initiate DataVerification. Wait for completion and validate the MA used for DataVerification

5: Initiate Restore. Wait for completion and validate the MA used for Restore.

6: Validate the Restored Data by comparing it with subclient content.

7: Upon Successful Validations, cleanup the entities created in Step 1.

"""
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
        self.name = 'Read Operations from latest v11 MA on chunks written by older Version MAs'
        self.tcinputs = {
            "StoragePolicyName": None,
            "PrimaryCopy_v11MA": None,
            "SecondaryCopy_v11MA":  None
        }
        self.result_string = ''
        self.utility = None
        self.mm_helper = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.client_path = None
        self.mount_path_2 = None
        self.restore_path = None
        self.copy_ddb_path = None
        self.secondary_ma_path = None
        self.copy_name = None
        self.library_name_2 = None
        self.storage_policy = None
        self.storage_policy_name = None

    def setup(self):
        """Setup function of this test case"""
        self.utility = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs.get('SecondaryCopy_v11MA'), self.commcell)

        client_drive = self.utility.get_drive(self.client_machine, 40*1024)
        self.client_path = self.client_machine.join_path(client_drive, 'test_' + str(self.id))
        self.restore_path = self.client_machine.join_path(self.client_path, 'Restore')
        ma_2_drive = self.utility.get_drive(self.ma_machine_2, 40*1024)
        self.secondary_ma_path = self.ma_machine_2.join_path(ma_2_drive, 'test_' + str(self.id))
        self.mount_path_2 = self.ma_machine_2.join_path(
            self.secondary_ma_path, 'MP2', self.tcinputs.get('PrimaryCopy_v11MA')[1:])
        self.copy_ddb_path = self.ma_machine_2.join_path(
            self.secondary_ma_path, "CopyDDB", self.tcinputs.get('PrimaryCopy_v11MA')[1:])

        self.copy_name = '%s%s%s' % (self.id, '_Copy', self.tcinputs.get('PrimaryCopy_v11MA')[1:])
        self.storage_policy_name = self.tcinputs.get('StoragePolicyName')
        self.library_name_2 = '%s%s%s' % (self.id, '_Lib2_',
                                          self.tcinputs.get('PrimaryCopy_v11MA')[1:])
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def cleanup(self):
        """CleansUp the Entities"""
        self.log.info('************************ Clean Up Started *********************************')
        try:
            self.mm_helper.remove_content(self.restore_path, self.client_machine, suppress_exception=True)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)
                if storage_policy.has_copy(self.copy_name):
                    self.log.info('Deleting Copy: %s', self.copy_name)
                    storage_policy.delete_secondary_copy(self.copy_name)
                    self.mm_helper.remove_content(self.copy_ddb_path, self.ma_machine_2)

            if self.commcell.disk_libraries.has_library(self.library_name_2):
                self.log.info('Deleting Library: %s', self.library_name_2)
                self.commcell.disk_libraries.delete(self.library_name_2)
            self.mm_helper.remove_content(self.mount_path_2, self.ma_machine_2)
        except Exception as exe:
            self.log.warning('CleanUp Failed: ERROR: %s', str(exe))
        finally:
            self.log.info('********************** Clean Up Completed *****************************')

    def run(self):
        """Run Function of this case"""
        self.cleanup()
        try:
            # Configure a Secondary Library with SecondaryCopy_v11MA
            self.mm_helper.configure_disk_library(self.library_name_2,
                                                  self.tcinputs.get('SecondaryCopy_v11MA'),
                                                  self.mount_path_2)

            self.storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)
            # configure a Secondary Copy which writes to Secondary Library
            self.dedupe_helper.configure_dedupe_secondary_copy(
                self.storage_policy, self.copy_name, self.library_name_2,
                self.tcinputs.get('SecondaryCopy_v11MA'),
                self.ma_machine_2.join_path(self.copy_ddb_path,
                                            'Dir' + self.utility.get_custom_str()),
                self.tcinputs.get('SecondaryCopy_v11MA'))

            # Remove Association with System Created AutoCopy Schedule
            self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.copy_name)

            # Here we are assuming that there are few valid jobs on the Primary Copy already
            self.log.info('********** Auxcopy - Chunk read validation with v11 Source MA *********')

            self.log.info('Submitting AuxCopy job with PrimaryCopy_v11MA as Source MA')
            aux_copy_job = self.storage_policy.run_aux_copy(
                media_agent=self.tcinputs.get('PrimaryCopy_v11MA'),
                storage_policy_copy_name=self.copy_name, all_copies=False)
            self.log.info('AuxCopyJob: %s', aux_copy_job.job_id)

            if aux_copy_job.wait_for_completion():
                self.log.info('AuxCopy (Id: %s): Completed', aux_copy_job.job_id)

                self.log.info('Validating Source MA for AuxCopy')
                query = '''select distinct AC.Name
                        from ArchJobStreamStatusHistory AJSH, App_Client AC
                        where AJSH.SrcMAId = AC.id and AJSH.jobId = {0}
                        '''.format(aux_copy_job.job_id)
                self.log.info('Executing Query to fetch SrcMA for AuxCopy: %s', query)
                self.csdb.execute(query)
                rows = self.csdb.fetch_all_rows()
                self.log.info('Result(Src MAs): %s', rows)

                if len(rows) > 1 or rows[0][0] != self.tcinputs.get('PrimaryCopy_v11MA'):
                    self.result_string += '[ERROR: Source MA Validation for AuxCopy FAILED]'
                    self.log.error('ERROR: Source MA Validation for AuxCopy FAILED')
                else:
                    self.log.info('SUCCESS: Source MA Validation for AuxCopy PASSED')
            else:
                self.result_string += '[AuxCopy (Id: %s): %s]' % (aux_copy_job.job_id,
                                                                  aux_copy_job.status)
                self.log.error('AuxCopy (Id: %s): %s', aux_copy_job.job_id, aux_copy_job.status)

            self.log.info('************ DV1 - Chunk read validation with v11 Source MA ***********')

            query = '''select distinct jobId
                    from  JMJobDataStats
                    where archGrpCopyId = {0} and status<>1000
                    '''.format(self.storage_policy.get_copy('Primary').copy_id)
            self.log.info('Executing Query to fetch Jobs on Primary Copy: %s', query)
            self.csdb.execute(query)
            rows = self.csdb.fetch_all_rows()
            job_strings = []
            string = ''
            for row in rows:
                string += ',%s' % row[0]
                if len(string) > 100:
                    job_strings.append(string.strip(','))
                    string = ''
            if string:
                job_strings.append(string.strip(','))
            self.log.info('Result(Jobs): %s', job_strings)
            cmd = "-sn MarkJobsOnCopy -si '{0}' -si 'Primary' -si 'pickForVerification' -si '{1}'"
            for string in job_strings:
                args = cmd.format(self.storage_policy_name, string)
                self.log.info('Running QOperation to pick jobs for DataVerification: %s', args)
                self.commcell._qoperation_execscript(args)

            self.log.info('Running Data verification with PrimaryCopy_v11MA as SrcMA')
            dv1_job = self.storage_policy.run_data_verification(
                self.tcinputs.get('PrimaryCopy_v11MA'))
            self.log.info('DV1: %s', dv1_job.job_id)

            if dv1_job.wait_for_completion():
                self.log.info('DV1 Job(Id: %s): Completed', dv1_job.job_id)

                self.log.info('Validating Source MA for DV1')
                query = '''select distinct AC.Name
                        from archJobStreamStatusHistory AJSSH, App_Client AC
                        where AJSSH.SrcMAId = AC.id and AJSSH.jobId = {0}'''.format(dv1_job.job_id)
                self.log.info('Executing Query to fetch SrcMA for DV1: %s', query)
                self.csdb.execute(query)
                rows = self.csdb.fetch_all_rows()
                self.log.info('Result(Src MAs): %s', rows)

                if len(rows) > 1 or rows[0][0] != self.tcinputs.get('PrimaryCopy_v11MA'):
                    self.result_string += '[ERROR: Source MA Validation for DV1 FAILED]'
                    self.log.error('ERROR: Source MA Validation for DV1 FAILED')
                else:
                    self.log.info('SUCCESS: Source MA Validation for DV1 PASSED')
            else:
                self.result_string += '[DV1 Job(Id: %s): %s]' % (dv1_job.job_id, dv1_job.status)
                self.log.error('DV1 Job(Id: %s): %s', dv1_job.job_id, dv1_job.status)

            self.log.info('********** Restore - Chunk read validation with v11 Source MA *********')

            self.log.info('Initiating Restore Job with PrimaryCopy_v11MA')
            restore_job = self.subclient.restore_out_of_place(
                self.client.client_name, self.restore_path, self.subclient.content,
                fs_options={'media_agent': self.tcinputs.get('PrimaryCopy_v11MA')})
            self.log.info('Restore Job: %s', restore_job.job_id)

            if restore_job.wait_for_completion():
                self.log.info('Restore Job(Id: %s): Completed', restore_job.job_id)

                query = '''select AC.Name
                        from JMJobOptions JO, App_Client AC
                        where JO.attributeValue = AC.id
                        and jobId = {0} and attributeId = 46'''.format(restore_job.job_id)
                self.log.info('Executing Query to fetch SrcMA for Restore: %s', query)
                self.csdb.execute(query)
                result = self.csdb.fetch_one_row()
                self.log.info('Result(Src MAs): %s', result)

                if result[0] != self.tcinputs.get('PrimaryCopy_v11MA'):
                    self.result_string += '[ERROR: Source MA Validation for Restore FAILED]'
                    self.log.error('ERROR: Source MA Validation for Restore FAILED')
                else:
                    self.log.info('SUCCESS: Source MA Validation for Restore PASSED')

                # say subclient content is ['E:\Content'] and restore path is 'F:\Restore'
                # we have to compare 'E:\Content' & 'F:\Restore\Content' (<restore_path>+'Content')
                # since here we are not defining content/content path in tc,
                # here we are temporarily assuming that subclient content is single element list
                # it shouldn't be ['E:\f1.x', 'E:\f2.x']

                self.log.info('Validating Restored Data from Primary Copy')
                content_tail = self.subclient.content[0].split(self.client_machine.os_sep)[-1]
                difference = self.client_machine.compare_folders(
                    self.client_machine, self.subclient.content[0],
                    self.client_machine.join_path(self.restore_path, content_tail))
                if difference:
                    self.result_string += '[Validating Data restored from Primary Copy Failed]'
                    self.log.error('Validating Data restored from Primary Copy Failed')
            else:
                self.result_string += '[Restore job(Id: %s): %s]' % (restore_job.job_id,
                                                                     restore_job.status)
                self.log.error('Restore job(Id: %s): %s', restore_job.job_id, restore_job.status)

            if len(self.result_string) != 0:
                raise Exception(self.result_string)

        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('EXCEPTION Occurred : %s', str(exe))
        finally:
            self.log.info('Completed executing %s Run function', self.id)

    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED. Cleaning Up the Entities')
            self.cleanup()
        else:
            self.mm_helper.remove_content(self.restore_path, self.client_machine, suppress_exception=True)
            self.log.warning('Test Case FAILED. Hence Not CleaningUp for debugging purposes')
