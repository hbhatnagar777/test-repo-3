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

    set_encryption()--  sets the encryption properties for the copy

    run_validations_and_restore() -- runs validations for enc.key type and runs restore jobs from each of the copies

    tear_down()     --  tear down function of this test case

Sample JSON:
    "50246": {
        "ClientName": "Name of Client",
        "PrimaryCopyMediaAgent": "Name of Source MA",
        "SecondaryCopyMediaAgent": "Name of Destination MA",
        "AgentName": "File System"
    }
    Note: Both the MediaAgents can be the same machine

Steps:

1: Configure the environment: create a library,Storage Policy-with a Primary, 4 Secondary Copies,
                              a BackupSet,a SubClient

2: Set different Encryption properties for the Copies.

3: Run 2 Full Backup Jobs and then AuxCopy Job

4: Run Validations

5: Seal the Stores for the copies and pick the jobs for recopy

6: Change the Encryption Properties for the copies and run AuxCopy

7: Run DB-Validations and run Restore Job from all the copies(Wait to complete Successfully)

8: Seal the Stores for the copies again and pick the jobs for recopy

9: Change the Encryption Properties for the copies again and run AuxCopy

10: Run DB-Validations and run Restore Jobs from all the copies(Wait to complete Successfully)

11: CleanUp the Environment

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
        self.name = 'AuxCopy: All Enc-Options On Storage Policy Copies'
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
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
        self.restore_path = None
        self.copy_ddb_path = None
        self.subclient = None
        self.storage_policy = None
        self.copy_name = None
        self.library_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_policy_name = None

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs['PrimaryCopyMediaAgent'], self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        utility = OptionsSelector(self.commcell)
        client_drive = utility.get_drive(self.client_machine, 25*1024)
        primary_ma_drive = utility.get_drive(self.ma_machine_1, 25*1024)
        secondary_ma_drive = utility.get_drive(self.ma_machine_2, 25*1024)
        self.client_path = self.client_machine.join_path(client_drive, f'test_{str(self.id)}')
        self.ma_1_path = self.ma_machine_1.join_path(primary_ma_drive, f'test_{str(self.id)}')
        self.ma_2_path = self.ma_machine_2.join_path(secondary_ma_drive, f'test_{str(self.id)}')
        self.ddb_path = self.ma_machine_1.join_path(self.ma_1_path, 'DDB')
        self.mount_path = self.ma_machine_1.join_path(self.ma_1_path, 'MP')
        self.mount_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'MP2')
        self.copy_ddb_path = self.ma_machine_2.join_path(self.ma_2_path, 'copy_DDB')
        self.content_path = self.client_machine.join_path(self.client_path, 'Content')
        self.restore_path = self.client_machine.join_path(self.client_path, 'Restores')
        self.copy_name = f'{str(self.id)}_Copy'
        self.library_name = f'{str(self.id)}_Lib'
        self.backupset_name = f'{str(self.id)}_BS'
        self.subclient_name = f'{str(self.id)}_SC'
        self.storage_policy_name = f'{str(self.id)}_SP'
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def cleanup(self):
        """Cleanup the entities created in this/Previous Run"""
        try:
            self.log.info("****************************** Cleanup Started ******************************")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            self.mm_helper.remove_content(self.restore_path, self.client_machine, suppress_exception=True)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Deleting storage policy  %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
            if self.commcell.disk_libraries.has_library(self.library_name + '_2'):
                self.commcell.disk_libraries.delete(self.library_name + '_2')
            self.log.info('****************************** Cleanup Completed ******************************')
        except Exception as exe:
            self.log.error('ERROR in Cleanup. Might need to Cleanup Manually: %s', str(exe))

    def run(self):
        """Run Function of this case"""
        try:
            self.log.info("Cleaning up the entities from older runs")
            self.cleanup()
            # 1: Configure the environment
            self.log.info('Setting Client Properties for Encryption on Client (BlowFish, 256)')
            self.client.set_encryption_property('ON_CLIENT', 'BlowFish', '256')
            self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                      self.content_path, 0.5)
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

            storage_policy_copies = [self.storage_policy.get_copy('Primary')]
            for index in range(1, 5):
                storage_policy_copies.append(self.dedupe_helper.configure_dedupe_secondary_copy(
                    self.storage_policy,
                    self.copy_name + str(index),
                    self.library_name + '_2',
                    self.tcinputs['SecondaryCopyMediaAgent'],
                    self.copy_ddb_path + str(index),
                    self.tcinputs['SecondaryCopyMediaAgent']))

            self.mm_helper.configure_backupset(self.backupset_name)
            self.subclient = self.mm_helper.configure_subclient(content_path=self.content_path)

            # Remove Association with System Created AutoCopy Schedule
            for index in range(1, 5):
                self.mm_helper.remove_autocopy_schedule(self.storage_policy_name,
                                                        self.copy_name + str(index))

            # 2: Set different Encryption properties for the Copies.
            self.log.info('***** Setting Encryption Properties for Each Of the Copies *****')
            self.log.info('Primary Copy: Re-Encrypt, BlowFish 256')
            self.set_encryption(storage_policy_copies[0], 0, 1, 0, 'BlowFish', 256)
            self.log.info('Copy 1: Re-Encrypt, GOST 256')
            self.set_encryption(storage_policy_copies[1], 0, 1, 0, 'GOST', 256)
            self.log.info('Copy 2: Store Plaintext')
            self.set_encryption(storage_policy_copies[2], 0, 0, 1, None, None)
            self.log.info('Copy 3: Store Plaintext, Network-Encrypt, Serpent 128')
            self.set_encryption(storage_policy_copies[3], 0, 0, 1, 'Serpent', 128)
            self.log.info('Copy 4: Preserve Encryption Mode')
            self.set_encryption(storage_policy_copies[4], 1, 0, 0, None, None)
            self.log.info('Completed Setting the Encryption Settings')

            # 3: Run 2 Full Backup Jobs and then AuxCopy Job
            self.log.info('Submitting 2 FULL Backups and AuxCopy')
            backup_job_1 = self.subclient.backup(backup_level='Full')
            if backup_job_1.wait_for_completion():
                self.log.info('Backup Job 1:(Id: %s) Completed', backup_job_1.job_id)
            else:
                raise Exception(f'Backup Job 1: {backup_job_1.job_id} Failed with JPR: {backup_job_1.delay_reason}')
            backup_job_2 = self.subclient.backup(backup_level='Full')
            if backup_job_2.wait_for_completion():
                self.log.info('Backup Job 2:(Id: %s) Completed', backup_job_2.job_id)
            else:
                raise Exception(f'Backup Job 2:{backup_job_2.job_id} Failed with JPR: {backup_job_2.delay_reason}')

            query = "select value from MMConfigs where name = 'MMS2_CONFIG_ENABLE_INFINI_STORE'"
            self.log.info("Executing Query: %s", query)
            self.csdb.execute(query)
            row = self.csdb.fetch_one_row()
            self.log.info("Result: %s", str(row))
            if int(row[0]) == 0:
                self.log.info('InfiniDDB disabled: Running Old AuxCopy')
                aux_copy_job = self.storage_policy.run_aux_copy(use_scale=False)
            else:
                self.log.info('InfiDDB enabled: Running New AuxCopy')
                aux_copy_job = self.storage_policy.run_aux_copy(use_scale=True)

            if aux_copy_job.wait_for_completion():
                self.log.info('AuxCopy Job Completed (Id: %s)', aux_copy_job.job_id)
            else:
                raise Exception(f'AuxCopy Job {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')

            # 4: Run Validations
            self.log.info('****************** VALIDATIONS FOR 1st AUX COPY JOB ******************')
            log_file = 'CVD.log'
            self.log.info('VALIDATION 1: enc. key used network only encryption to decrypt on CVD')
            (matched_line, matched_string) = self.dedupe_helper.parse_log(
                self.tcinputs['SecondaryCopyMediaAgent'], log_file,
                'Serpent enc. key', aux_copy_job.job_id,
                escape_regex=True)
            if matched_line:
                self.log.info('Success Result : Passed')
            else:
                self.log.error('Error  Result : Failed')
                # self.status = constants.FAILED

            self.log.info('VALIDATION 2: enc. key Fetch call used to decrypt on CVD')
            (matched_line, matched_string) = self.dedupe_helper.parse_log(
                self.tcinputs['SecondaryCopyMediaAgent'], log_file,
                'Retrieving encryption keys', aux_copy_job.job_id,
                escape_regex=True)
            if matched_line:
                self.log.info('Success Result : Passed')
            else:
                self.log.error('Error  Result : Failed')
                # self.status = constants.FAILED

            # 5: Seal the Stores for the copies and pick the jobs for recopy
            for index in range(1, 5):
                self.storage_policy.seal_ddb(self.copy_name + str(index))
                storage_policy_copies[index].recopy_jobs(backup_job_1.job_id)
                storage_policy_copies[index].recopy_jobs(backup_job_2.job_id)

            # 6: Change the Encryption Properties for the copies and run AuxCopy
            self.log.info('Changing the Encryption properties for the Copies and running AuxCopy')
            self.log.info('Set Copy 1: Store Plaintext')
            self.set_encryption(storage_policy_copies[1], 0, 0, 1, None, None)
            self.log.info('Set Copy 2: Preserve Encryption Mode')
            self.set_encryption(storage_policy_copies[2], 1, 0, 0, None, None)
            self.log.info('Set Copy 3: Re-Encrypt, DES3, 192')
            self.set_encryption(storage_policy_copies[3], 0, 1, 0, 'DES3', 192)
            self.log.info('Set Copy 4: Store Plaintext, Network-Encrypt, TwoFish 256')
            self.set_encryption(storage_policy_copies[4], 0, 0, 1, 'TwoFish', 256)
            self.log.info('Completed Setting the Encryption Settings')

            aux_copy_job = self.storage_policy.run_aux_copy(use_scale=True)
            if aux_copy_job.wait_for_completion():
                self.log.info('2nd AuxCopy Job: %s Completed', aux_copy_job.job_id)
            else:
                raise Exception(f'2nd AuxCopy Job {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')

            # 7: Run DB-Validations and run Restore Job from all the copies
            self.run_validations_and_restore(storage_policy_copies[1:])

            # 8: Seal the Stores for the copies again and pick the jobs for recopy
            for index in range(1, 5):
                self.storage_policy.seal_ddb(self.copy_name + str(index))
                storage_policy_copies[index].recopy_jobs(backup_job_1.job_id)
                storage_policy_copies[index].recopy_jobs(backup_job_2.job_id)

            # 9: Change the Encryption Properties for the copies again and run AuxCopy
            self.log.info('Changing the Encryption properties for the Copies and running AuxCopy')
            self.log.info('Set Copy 1: Preserve Encryption Mode')
            self.set_encryption(storage_policy_copies[1], 1, 0, 0, None, None)
            self.log.info('Set Copy 2: Store Plaintext, Network-Encrypt, AES 128')
            self.set_encryption(storage_policy_copies[2], 0, 0, 1, 'AES', 128)
            self.log.info('Set Copy 3: Re-Encrypt, Serpent, 128')
            self.set_encryption(storage_policy_copies[3], 0, 1, 0, 'Serpent', 128)
            self.log.info('Set Copy 4: Store Plaintext')
            self.set_encryption(storage_policy_copies[4], 0, 0, 1, None, None)
            self.log.info('Completed Setting the Encryption Settings')

            aux_copy_job = self.storage_policy.run_aux_copy(use_scale=True)
            if aux_copy_job.wait_for_completion():
                self.log.info('3rd AuxCopy Job: %s Completed', aux_copy_job.job_id)
            else:
                raise Exception(f'3rd AuxCopy Job {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')

            self.run_validations_and_restore(storage_policy_copies[1:])
            self.log.info('All Validations Completed')
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error("Exception Occurred: %s", str(exe))

    def set_encryption(self, copy, preserve, re_encrypt, plain_text, encryption, key_length):
        """Sets the Encryption properties for the copy
                Args:
                        copy              (object)  --   Object of StoragePolicyCopy class

                        preserve          (int)   --  Preserve Enc.Mode as in Source(0/1)

                        re_encrypt        (int)   --  Re-Encrypt Data using cipher(0/1)

                        plain_text        (int)   --  Store in Plain-Text(0/1)

                        encryption        (str)   --  Encryption technique
                                                      (applies when re_encrypt/plain_text - 1)
                                                      (None/DES3/BlowFish/TwoFish/AES/GOST/Serpent)

                        key_length        (int)   --  Length of Key to be used for Encryption
                                                      (128, 192, 256)
        """
        copy._copy_flags['preserveEncryptionModeAsInSource'] = preserve
        copy._copy_flags['auxCopyReencryptData'] = re_encrypt
        copy._copy_flags['storePlainText'] = plain_text

        if encryption and key_length:
            if plain_text:
                copy._copy_flags['encryptOnNetworkUsingSelectedCipher'] = 1
            copy._copy_properties['dataEncryption'] = {'encryptData': 1,
                                                       'encryptionType': encryption,
                                                       'encryptionKeyLength': key_length}
        else:
            copy._copy_flags['encryptOnNetworkUsingSelectedCipher'] = 0
            copy._copy_properties['dataEncryption'] = {}

        copy._set_copy_properties()
        self.log.info('Property Set Successful')

    def run_validations_and_restore(self, storage_policy_copies):
        """Runs Validations for Enc.Key Type and runs Restore jobs from each of the copies
                Args:
                        storage_policy_copies  (list)  --   List of StoragePolicyCopy Objects

        """
        self.log.info('********************* VALIDATIONS FOR AUX COPY JOB ***********************')
        self.log.info('****** VALIDATIONS FOR Enc.Key Types ******')
        expected_types = [11, 3, 10, 3]
        fetched_types = []
        for copy in storage_policy_copies:
            query = '''select distinct encKeyType from archFileCopy
                    where archfileid  in (select id from archFile where filetype = 1)
                    and  archCopyId = %s''' % copy.copy_id
            self.log.info('Query: %s', query)
            self.csdb.execute(query)
            row = self.csdb.fetch_one_row()
            fetched_types.append(int(row[0]))
        self.log.info('Expected Enc.Key Types for Copies: %s', str(expected_types))
        self.log.info('Fetched Enc.Key Types for Copies: %s', str(fetched_types))
        if fetched_types != expected_types:
            raise Exception('Encryption KeyType Validation failed')
        self.log.info('SUCCESS Result: Validation Passed')

        self.log.info('Running Restore Jobs on all the Copies')
        restore_jobs = []
        for index in range(2, 6):
            job = self.subclient.restore_out_of_place(self.client.client_name,
                                                      self.client_machine.join_path(self.restore_path, str(index - 1)),
                                                      [self.content_path],
                                                      copy_precedence=index)
            self.log.info('Restore Job(Id: %s) Initiated', job.job_id)
            restore_jobs.append(job)

        for job in restore_jobs:
            if job.wait_for_completion():
                self.log.info('Restore Job:%s Completed', job.job_id)
            else:
                raise Exception(f'Restore Job {job.job_id} Failed with JPR: {job.delay_reason}')

        self.log.info('Validating Restored Data from 4 Copies')
        for index in range(1, 5):
            restored_path = self.client_machine.join_path(self.restore_path, str(index), 'Content')
            difference = self.client_machine.compare_folders(self.client_machine,
                                                             self.content_path,
                                                             restored_path)
            if difference:
                raise Exception('Validating Data restored from Copy %s Failed' % index)
        self.log.info('Validation SUCCESS')

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 11: CleanUp the Environment
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
