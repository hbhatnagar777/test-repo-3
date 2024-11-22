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

    run_validations()    --  runs the validations

    set_registry_keys()  -- sets the registry keys on media agent

    tear_down()     --  tear down function of this test case

Sample JSON:
    "45210": {
        "ClientName": "Name of Client",
        "AgentName": "File System",
        "PrimaryCopyMediaAgent": "Name of Source MA",
        "SecondaryCopyMediaAgent": "Name of Destination MA",
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "pool_name": "name of the storage pool to be reused",
        "mount_path": "path where the data is to be stored",
        "dedup_path": "path where dedup store to be created",
        "copy_pool_name": "name of the storage pool to be reused for auxcopy",
        "copy_mount_path": "path where the data is to be stored for auxcopy",
        "copy_dedup_path": "path where dedup store to be created for auxcopy"
    }

    Note: Both the MediaAgents can be the same machine
    For linux MA, User must explicitly provide a ddb path that is inside a Logical Volume.(LVM support required for DDB)

Steps:

1: Configure the environment: create two storage pools for primary copy and secondary copy,
                            plan-with Primary, Secondary Copy, a BackupSet,a SubClient

2: Enable Secondary Copy as Network Optimized Copy and maxCacheDBSizeMB = 4096

3: Run a Backup Job and then AuxCopy and run Validations(properties set)

4: Submit another Backup Job and again a AuxCopy Job

5: Run Validations(Network Optimized, Cache used, Dedupe Occurred, properties set)

6: CleanUp the environment
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
        self.name = "Automation -Dedupe-Network Optimized AuxCopy with cache"
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None,
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
        self.copy_name = None
        self.pool_name = None
        self.plan = None
        self.pool_name_2 = None
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
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs['PrimaryCopyMediaAgent'], self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        self.utility = OptionsSelector(self.commcell)
        client_drive = self.utility.get_drive(self.client_machine, 25*1024)
        self.client_path = self.client_machine.join_path(client_drive, 'test_' + str(self.id))
        self.content_path = self.client_machine.join_path(self.client_path, 'content')
        self.copy_name = '%s%s' % (str(self.id), '_Copy')
        self.subclient_name = '%s%s' % (str(self.id), '_SC')
        self.backupset_name = '%s%s%s' % (str(self.id), '_BS_',
                                          str(self.tcinputs['SecondaryCopyMediaAgent'])[2:])
        self.plan_name = '%s%s%s' % (str(self.id), '_SP_',
                                               str(self.tcinputs['SecondaryCopyMediaAgent'])[2:])

        if self.tcinputs.get('pool_name'):
            self.is_user_defined_pool = True
        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('copy_pool_name'):
            self.is_user_defined_copy_pool = True
        if self.tcinputs.get('copy_mount_path'):
            self.is_user_defined_copy_mp = True
        if self.tcinputs.get('copy_dedup_path'):
            self.is_user_defined_copy_dedup = True

        if (not self.is_user_defined_dedup and "unix" in self.ma_machine_1.os_info.lower()) or \
                (not self.is_user_defined_copy_dedup and "unix" in self.ma_machine_2.os_info.lower()):
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.ma_machine_1, 25*1024)
            self.primary_ma_path = self.ma_machine_1.join_path(ma_1_drive, 'test_' + str(self.id))
        if not self.is_user_defined_copy_mp or not self.is_user_defined_copy_dedup:
            ma_2_drive = self.utility.get_drive(self.ma_machine_2, 25*1024)
            self.secondary_ma_path = self.ma_machine_2.join_path(ma_2_drive,
                                                                 'test_' + str(self.id))

        if self.is_user_defined_pool:
            self.log.info("Existing library name supplied")
            self.pool_name = self.tcinputs["pool_name"]
        else:
            self.pool_name = '%s%s%s' % (str(self.id), '_Pool1_',
                                            str(self.tcinputs['SecondaryCopyMediaAgent'])[2:])
            if not self.is_user_defined_mp:
                self.mount_path = self.ma_machine_1.join_path(self.primary_ma_path, 'MP1')
            else:
                self.log.info("custom mount_path supplied")
                self.mount_path = self.ma_machine_1.join_path(
                    self.tcinputs['mount_path'], 'test_' + self.id, 'MP1')

        if self.is_user_defined_copy_pool:
            self.log.info("Existing pool name supplied for secondary copy")
            self.pool_name_2 = self.tcinputs["copy_pool_name"]
        else:
            self.pool_name_2 = '%s%s%s' % (str(self.id), '_Pool2_',
                                              str(self.tcinputs['SecondaryCopyMediaAgent'])[2:])
            if not self.is_user_defined_copy_mp:
                self.mount_path_2 = self.ma_machine_2.join_path(self.secondary_ma_path, 'MP2')
            else:
                self.log.info("custom copy_mount_path supplied")
                self.mount_path = self.ma_machine_2.join_path(
                    self.tcinputs['copy_mount_path'], 'test_' + self.id, 'MP2')

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.ma_machine_1.join_path(self.tcinputs["dedup_path"],
                                                        'test_' + self.id, "DDB")
        else:
            self.ddb_path = self.ma_machine_1.join_path(self.primary_ma_path, "DDB")

        if self.is_user_defined_copy_dedup:
            self.log.info("custom copydedup path supplied")
            self.copy_ddb_path = self.ma_machine_2.join_path(self.tcinputs["copy_dedup_path"],
                                                             'test_' + self.id, "CopyDDB")
        else:
            self.copy_ddb_path = self.ma_machine_2.join_path(self.secondary_ma_path, "CopyDDB")

        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        self.config_strings = ['Using 10.0 readless mode',
                               '\[Signatures processed .*?\]', '\[Found in cache .*?\]',
                               '\[Size-processed .*?\]', '\[Size-New Data- .*?\]',
                               'Encryption Type [3]', 'encryptionType [CV_DECRYPT_AND_ENCRYPT]',
                               '\[Size-Discarded .*?\]', 'Initializing Coordinator',
                               'Initializing Controller',
                               '[Coordinator] Number of streams allocated for the agent',
                               '[Reader_1] Initializing Worker Thread',
                               '^\d+\s*\w+\s*\d+\/\d+\s*\d+:\d+:\d+\s*\d+\s*\[Coordinator\] Initializing Coordinator:',
                               'SI Block Size [128 KB]']

    def cleanup(self):
        try:
            self.log.info("********************** CLEANUP STARTING *************************")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Deleting plan %s", self.plan_name)
                self.commcell.plans.delete(self.plan_name)
            if not self.is_user_defined_pool:
                if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                    self.commcell.storage_pools.delete(self.pool_name)
            if not self.is_user_defined_copy_pool:
                if self.commcell.storage_pools.has_storage_pool(self.pool_name_2):
                    self.commcell.storage_pools.delete(self.pool_name_2)
            self.log.info("********************** CLEANUP COMPLETED *************************")
        except Exception as exe:
            self.log.warning('ERROR in Cleanup. Might need to Cleanup Manually: %s', str(exe))

    def run(self):
        """Run Function of This Case"""
        self.log.info("Initiating Previous Run Cleanup")
        self.cleanup()
        try:
            # 1: Configure the environment
            self.log.info("Setting cvods debug lvl to 3 for doing important log validations")
            self.ma_machine_1.set_logging_debug_level('CVJobReplicatorODS', 3)
            # if both MA's are same:  Set Registry Keys: UseCacheDB, Delete: UseAuxCopyReadLessPlus
            if self.tcinputs['PrimaryCopyMediaAgent'] == self.tcinputs['SecondaryCopyMediaAgent']:
                self.set_registry_keys()
            self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                      self.content_path, 0.4)
            if not self.is_user_defined_pool:
                self.log.info(f"Creating the pool [{self.pool_name}]")
                self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                                self.tcinputs['PrimaryCopyMediaAgent'],
                                                [self.tcinputs['PrimaryCopyMediaAgent']] * 2,
                                                [self.ma_machine_1.join_path(self.ddb_path, 'Dir1'),
                                                 self.ma_machine_1.join_path(self.ddb_path, 'Dir2')])
                self.log.info(f"Pool [{self.pool_name}] Created.")

            if not self.is_user_defined_copy_pool:
                self.log.info(f"Creating the pool [{self.pool_name_2}]")
                self.commcell.storage_pools.add(self.pool_name_2, self.mount_path_2,
                                                self.tcinputs['SecondaryCopyMediaAgent'],
                                                [self.tcinputs['SecondaryCopyMediaAgent']] * 2,
                                                [self.ma_machine_2.join_path(self.copy_ddb_path, 'Dir1'),
                                                 self.ma_machine_2.join_path(self.copy_ddb_path, 'Dir2')])
                self.log.info(f"Pool [{self.pool_name_2}] Created.")

            self.log.info(f"Plan Present: {self.commcell.plans.has_plan(self.plan_name)}")
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.commcell.plans.refresh()
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")

            # disabling the schedule policy
            self.plan.schedule_policies['data'].disable()

            self.plan.storage_policy.create_dedupe_secondary_copy(
                self.copy_name,
                self.pool_name_2,
                self.tcinputs['SecondaryCopyMediaAgent'],
                self.ma_machine_2.join_path(self.copy_ddb_path,
                                            'Dir' + self.utility.get_custom_str()),
                self.tcinputs['SecondaryCopyMediaAgent'],
                dash_full=False,
                source_side_disk_cache=True
            )

            storage_policy_copy = self.plan.storage_policy.get_copy(self.copy_name)

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

            # Remove Association with System Created AutoCopy Schedule
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.copy_name)

            # 2: Enable Secondary Copy as Network Optimized Copy and maxCacheDBSizeMB = 4096
            storage_policy_copy.copy_client_side_dedup = True
            storage_policy_copy.set_encryption_properties(re_encryption=True, encryption_type="AES", encryption_length=256)

            query = '''update archgroupcopy
                    set maxCacheDBSizeMB = 4096 where id = %s''' % storage_policy_copy.copy_id
            self.log.info("Executing Query to set CacheDBSize: %s", query)
            self.utility.update_commserve_db(query)

            # 3: Run a Backup Job and then AuxCopy and run Validations(properties set)
            # 1st Iteration
            self.log.info('Submitting 1st Full Backup')
            backup_job = self.subclient.backup(backup_level='Full')
            if backup_job.wait_for_completion():
                self.log.info('1st Backup Completed :Id - %s', backup_job.job_id)
            else:
                raise Exception(f'1st Backup {backup_job.job_id} Failed with JPR: {backup_job.delay_reason}')
            self.log.info('Submitting AuxCopy job')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(use_scale=True)
            if aux_copy_job.wait_for_completion():
                self.log.info('1st AuxCopy Completed :Id - %s', aux_copy_job.job_id)
            else:
                raise Exception(f'1st AuxCopy {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')

            self.run_validations(1, backup_job.job_id, aux_copy_job.job_id)

            # 4: Submit another Backup Job and again a AuxCopy Job
            # 2nd Iteration
            self.log.info('Submitting 2nd Full Backup')
            backup_job = self.subclient.backup(backup_level='Full')
            if backup_job.wait_for_completion():
                self.log.info('2nd Backup Completed :Id - %s', backup_job.job_id)
            else:
                raise Exception(f'2nd Backup {backup_job.job_id} Failed with JPR: {backup_job.delay_reason}')
            self.log.info('Submitting AuxCopy job')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(use_scale=True)
            if aux_copy_job.wait_for_completion():
                self.log.info('2nd AuxCopy Completed :Id - %s', aux_copy_job.job_id)
            else:
                raise Exception(f'2nd AuxCopy {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')

            # 5: Run Validations(Network Optimized, Cache used, Dedupe Occurred, properties set)
            self.run_validations(2, backup_job.job_id, aux_copy_job.job_id)
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('Exception Raised: %s', str(exe))

    def run_validations(self, iteration, backup_job_id, aux_copy_job_id):
        """Runs the validations
            Args:

                    iteration             (int)  --   Iteration of the Case Validations

                    backup_job_id         (str)  --   Id of Backup Job

                    aux_copy_job_id       (str)  --   Id of the AuxCopy Job
        """

        log_file = 'CVJobReplicatorODS.log'
        self.log.info('********* ITERATION %s *********', str(iteration))

        self.log.info('*** CASE 1: 10.0 Using readless Mode ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[0], aux_copy_job_id)
        if matched_line:
            self.log.error('Error  Result : Failed')
            self.status = constants.FAILED
        else:
            self.log.info('Success Result : Passed')

        self.log.info('*** CASE 2: Signatures Processed ***')
        signatures_processed = ''
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[1], aux_copy_job_id,
            escape_regex=False)
        if matched_line:
            signatures_processed = int(matched_string[0].split('-')[-1].split(']')[0].strip())
            self.log.info('Signatures Processed = %s', signatures_processed)
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
            self.status = constants.FAILED
        if iteration == 1:
            self.log.info('*** CASE 3: Found in cache - 0 ***')
        else:
            self.log.info('*** CASE 3: Found in cache != 0  but equals Signatures processed***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[2], aux_copy_job_id,
            escape_regex=False)
        if matched_line:
            found_in_cache = int(matched_string[0].split('-')[-1].split(']')[0].strip())
            self.log.info('Found in Cache : %s', found_in_cache)
            if iteration == 1 and found_in_cache == 0:
                self.log.info('Success Result : Passed')
            elif iteration == 2 and abs(found_in_cache - signatures_processed) <= 10:
                self.log.info('Success Result : Passed')
            else:
                self.log.error('Error  Result : Failed')
                self.status = constants.FAILED
        else:
            self.log.error('Error  Result : Failed')
            self.status = constants.FAILED

        check_string = self.config_strings[4]
        if iteration == 1:
            self.log.info("*** CASE 4: Size-processed == Size-Transferred ***")
        else:
            self.log.info("*** CASE 4: Size-processed == Size-Discarded ***")
            check_string = self.config_strings[7]
        compressed_size = ''
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[3], aux_copy_job_id,
            escape_regex=False)
        if matched_line:
            compressed_size = matched_string[0].split('-')[-1]
            self.log.info('Compressed Size = %s', compressed_size.split(']')[0])

        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            check_string, aux_copy_job_id,
            escape_regex=False)
        if matched_line and iteration == 1:
            transferred_size = matched_string[0].split('-')[-1]
            self.log.info('Size-New Data = %s', transferred_size.split(']')[0])
            if compressed_size.split(']')[0] == transferred_size.split(']')[0] + ' ':
                self.log.info('Success Result : Passed')
            else:
                self.status = constants.FAILED
        elif matched_line and iteration == 2:
            discarded_size = matched_string[0].split('-')[-1]
            # Giving tolerance up to 10 signatures for diff b/w compressed size and discarded size
            self.log.info('Size Discarded = %s', discarded_size.split(']')[0])
            if abs(int(compressed_size.split(']')[0].split()[0].strip()) -
                   int(discarded_size.split(']')[0].split()[0].strip())) <= (128*1024*10):
                self.log.info('Success Result : Passed')
            else:
                self.log.error('Error  Result : Failed')
                self.status = constants.FAILED
        else:
            self.log.error('Error  Result : Failed')
            self.status = constants.FAILED

        self.log.info('*** CASE 6: Did Dedupe Occur? ***')

        primary = self.dedupe_helper.get_primary_objects_sec(backup_job_id, self.copy_name)

        secondary = self.dedupe_helper.get_secondary_objects_sec(backup_job_id, self.copy_name)
        self.list_primary.append(int(primary))
        self.list_secondary.append(int(secondary))
        self.log.info('Primary Objects : %s', primary)
        self.log.info('Secondary Objects : %s', secondary)
        if iteration == 1:
            self.log.info('Validation will be done in next Iteration')
        else:
            if self.list_primary[0] == self.list_secondary[1] and self.list_primary[1] == 0:
                self.log.info('Success Result : Passed')
            else:
                self.log.error('Error  Result : Failed')
                self.status = constants.FAILED

        self.log.info("*** CASE 7: Encryption Type [3] ***")
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[5], aux_copy_job_id)
        if matched_line:
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
        #     self.status = constants.FAILED

        self.log.info('*** CASE 8: Pipeline encryptionType [CV_DECRYPT_AND_ENCRYPT] ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[6], aux_copy_job_id)
        if matched_line:
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
        #     self.status = constants.FAILED

        self.log.info('** CASE 9: Initializing Coordinator ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[8], aux_copy_job_id)
        if matched_line:
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
        #     self.status = constants.FAILED

        self.log.info('*** CASE 10: Initializing Controller ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[9], aux_copy_job_id)
        if matched_line:
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
        #     self.status = constants.FAILED

        self.log.info('*** CASE 11: [Coordinator] Number of streams allocated for agent ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[10], aux_copy_job_id)
        if matched_line:
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
        #     self.status = constants.FAILED

        self.log.info('*** CASE 12: [Reader_1] Initializing Worker Thread ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[11], aux_copy_job_id)
        if matched_line:
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
        #     self.status = constants.FAILED

        self.log.info('*** CASE 13: Get pid of the CVJobReplicatorODS process ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[12], aux_copy_job_id,
            escape_regex=False)
        if matched_line:
            self.log.info('PID %s', (matched_string[0].split(' ')[-4]))
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
        #     self.status = constants.FAILED

        self.log.info('*** CASE 14: ArchChunkToReplicate status ***')
        query = '''select distinct status
                from archchunktoreplicatehistory where AdminJobId = {0}
                '''.format(aux_copy_job_id)
        self.log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        row_1 = self.csdb.fetch_one_row()
        self.log.info("Result: %s", str(row_1))
        query = '''select distinct status
                from archchunktoreplicate where AdminJobId = {0}
                '''.format(aux_copy_job_id)
        self.log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        row_2 = self.csdb.fetch_one_row()
        self.log.info("Result: %s", str(row_2))
        if int(row_1[0]) == 2 or int(row_2[0]) == 2:
            self.log.info('ArchChunkToReplicate status for all chunks is 2')
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error Result : Fail')
            self.status = constants.FAILED

    def set_registry_keys(self):
        """Sets the Properties of the MA Machine as required for case"""
        self.ma_machine_1.create_registry('MediaAgent', 'UseCacheDB', '1', 'DWord')
        self.ma_machine_1.remove_registry('MediaAgent', 'UseAuxcopyReadlessPlus')
        self.log.info("Same MA's: Registry Keys: UseCacheDB Set, UseAuxCopyreadlessPlus Deleted")

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 6: CleanUp the environment
        self.log.info("ReSetting cvods debug lvl to 1")
        self.ma_machine_1.set_logging_debug_level('CVJobReplicatorODS', 1)
        if self.tcinputs['PrimaryCopyMediaAgent'] == self.tcinputs['SecondaryCopyMediaAgent']:
            # if both MA's are same, remove registry keys set previously
            self.ma_machine_1.remove_registry('MediaAgent', 'UseCacheDB')
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
