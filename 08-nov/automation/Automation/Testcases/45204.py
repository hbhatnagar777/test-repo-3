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

    set_registry_keys()  -- sets the registry keys UseCacheDB, UseAuxCopyReadLessPlus

    run_validations()    --  runs the validations

    tear_down()     --  tear down function of this test case

Sample JSON:
    "45204": {
        "ClientName": "Name of Client",
        "AgentName": "File System",
        "PrimaryCopyMediaAgent": "Name of Source MA",
        "SecondaryCopyMediaAgent": "Name of Destination MA",
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "pool_name": "name of the Library to be reused",
        "mount_path": "path where the data is to be stored",
        "dedup_path": "path where dedup store to be created",
        "copy_pool_name": "name of the Library to be reused for auxcopy",
        "copy_mount_path": "path where the data is to be stored for auxcopy",
        "copy_dedup_path": "path where dedup store to be created for auxcopy"
        "use_lookahead": "Boolean to indicate whether to use LookAhead Link Reader"
    }

    Note: Both the MediaAgents can be the same machine
    For linux MA, User must explicitly provide a ddb path that is inside a Logical Volume.(LVM support required for DDB)

Steps:

1: Configure the environment: create a library,Storage Policy-with Primary, Secondary Copy,
                              a BackupSet,a SubClient

2: Set Properties: Use new read-less mode(Enable DiskRead) and maxCacheDBSizeMB: 4096

3: Run a Backup Job and then AuxCopy and run Validations(properties set)

4: Submit another Backup Job and again a AuxCopy Job

5: Run Validations(new read-less, Network Optimized, Cache used, Dedupe Occurred, properties set)

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
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Automation -Dedupe-New Readless AuxCopy with cache"
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
        self.use_lookahead = False
        self.initial_la_config = -1
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
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.client_machine, self.client_path = self.mm_helper.generate_automation_path(self.client.client_name, 25*1024)
        self.content_path = self.client_machine.join_path(self.client_path, 'content')
        self.copy_name = f'{self.id}_Copy'
        self.subclient_name = f'{self.id}_SC'
        self.backupset_name = f"{self.id}_BS_{self.tcinputs['SecondaryCopyMediaAgent'][2:]}"
        self.plan_name = f"{self.id}_Plan{self.tcinputs['SecondaryCopyMediaAgent'][2:]}"


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
        if self.tcinputs.get('use_lookahead', True):
            self.use_lookahead = True

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            self.ma_machine_1, self.primary_ma_path = self.mm_helper.generate_automation_path(self.tcinputs['PrimaryCopyMediaAgent'], 25*1024)
        if not self.is_user_defined_copy_mp or not self.is_user_defined_copy_dedup:
            self.ma_machine_2, self.secondary_ma_path = self.mm_helper.generate_automation_path(self.tcinputs['SecondaryCopyMediaAgent'], 25*1024)

        if self.is_user_defined_pool:
            self.log.info("Existing library name supplied")
            self.pool_name = self.tcinputs["pool_name"]
        else:
            self.pool_name = f"{self.id}_Pool1_{self.tcinputs['SecondaryCopyMediaAgent'][2:]}"
            if not self.is_user_defined_mp:
                self.mount_path = self.ma_machine_1.join_path(self.primary_ma_path, 'MP1')
            else:
                self.log.info("custom mount_path supplied")
                self.mount_path = self.ma_machine_1.join_path(
                    self.tcinputs['mount_path'], 'test_' + self.id, 'MP1')

        if self.is_user_defined_copy_pool:
            self.log.info("Existing library name supplied for secondary copy")
            self.pool_name_2 = self.tcinputs["copy_pool_name"]
        else:
            self.pool_name_2 = f"{self.id}_Pool2_{self.tcinputs['SecondaryCopyMediaAgent'][2:]}"
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
            if "unix" in self.ma_machine_1.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_path = self.ma_machine_1.join_path(self.primary_ma_path, "DDB")

        if self.is_user_defined_copy_dedup:
            self.log.info("custom copydedup path supplied")
            self.copy_ddb_path = self.ma_machine_2.join_path(self.tcinputs["copy_dedup_path"],
                                                             'test_' + self.id, "CopyDDB")
        else:
            if "unix" in self.ma_machine_2.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.copy_ddb_path = self.ma_machine_2.join_path(self.secondary_ma_path, "CopyDDB")

        self.config_strings = ['Using 10.0 readless mode',
                               '\[Signatures processed .*?\]', '\[Found in cache .*?\]',
                               '\[Size-processed .*?\]', '\[Size-New Data- .*?\]',
                               'Encryption Type [3]', 'encryptionType [CV_DECRYPT_AND_ENCRYPT]',
                               '\[Size-Discarded .*?\]', 'Initializing Coordinator',
                               'Initializing Controller',
                               '[Coordinator] Number of streams allocated for the agent',
                               '[Reader_1] Initializing Worker Thread',
                               '^\d+\s*\w+\s*\d+\/\d+\s*\d+:\d+:\d+\s*\d+\s*\[Coordinator\] Initializing Coordinator:',
                               'SI Block Size [128 KB]', ': Look ahead reader ']

    def cleanup(self):
        """Cleanup the entities created in this/Previous Run"""
        try:
            self.log.info("********************** CLEANUP STARTING *************************")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting BackupSet: {self.backupset_name} if exists")
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                self.subclient = self.backupset.subclients.get(self.subclient_name)
                if self.backupset.subclients.has_subclient(self.subclient_name):
                    self.subclient.plan = None
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

            self.log.info("********************** CLEANUP COMPLETED *************************")
        except Exception as exe:
            self.log.warning(f'ERROR in Cleanup. Might need to Cleanup Manually: {exe}')

    def run(self):
        """Run Function of This Case"""
        self.log.info("Initiating Previous Run Cleanup")
        self.cleanup()
        try:
            # 1: Setup the Environment
            self.log.info("Setting cvods debug lvl to 3 for doing important log validations")
            self.ma_machine_1.set_logging_debug_level('CVJobReplicatorODS', 3)
            # if Both MA's are same: Enable Registry Keys : UseCacheDB, UseAuxCopyReadLessPlus
            if self.tcinputs['PrimaryCopyMediaAgent'] == self.tcinputs['SecondaryCopyMediaAgent']:
                self.set_registry_keys()

            # Enable/Disable lookahead based on user input
            if self.ma_machine_1.get_registry_value('MediaAgent', 'DataMoverUseLookAheadLinkReader'):
                # self.initial_la_config: (-1)reg.key absent, (0)reg.key set to disable LA, (1)reg.key set to enable LA
                self.initial_la_config = int(
                    self.ma_machine_1.get_registry_value('MediaAgent', 'DataMoverUseLookAheadLinkReader'))

            if not self.use_lookahead:
                self.log.info('Disabling LookAheadLinkReader for this run by setting reg.key to 0 on Src MA')
                self.ma_machine_1.create_registry('MediaAgent', 'DataMoverUseLookAheadLinkReader', '0', r'DWord')
            else:
                self.log.info('LookAheadLinkReader is enabled for this Run. '
                              'Removing reg.key if exists on Src MA.  [LA is enabled by default]')
                if self.initial_la_config != -1:
                    self.ma_machine_1.remove_registry('MediaAgent', 'DataMoverUseLookAheadLinkReader')

            self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                      self.content_path, 0.4)
            if not self.is_user_defined_pool:
                self.log.info(f"Creating the pool [{self.pool_name}]")
                self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                                self.tcinputs['PrimaryCopyMediaAgent'],
                                                [self.tcinputs['PrimaryCopyMediaAgent']]*2,
                                                [self.ma_machine_1.join_path(self.ddb_path, 'Dir1'), self.ma_machine_1.join_path(self.ddb_path, 'Dir2')])
                self.log.info(f"Pool [{self.pool_name}] Created.")

            if not self.is_user_defined_copy_pool:
                self.commcell.storage_pools.refresh()
                self.log.info(f"Creating the pool [{self.pool_name_2}]")
                self.commcell.storage_pools.add(self.pool_name_2, self.mount_path_2,
                                                self.tcinputs['SecondaryCopyMediaAgent'],
                                                [self.tcinputs['SecondaryCopyMediaAgent']]*2,
                                                [self.ma_machine_2.join_path(self.copy_ddb_path, 'Dir1'), self.ma_machine_2.join_path(self.copy_ddb_path, 'Dir2')])
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

            self.plan.storage_policy.create_dedupe_secondary_copy(
                self.copy_name,
                self.pool_name_2,
                self.tcinputs['SecondaryCopyMediaAgent'],
                self.ma_machine_2.join_path(self.copy_ddb_path,
                                            'Dir' + self.utility.get_custom_str()),
                self.tcinputs['SecondaryCopyMediaAgent'],
                dash_full=True,
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

            # 2: Set Properties: Use new read-less mode(Enable DiskRead) and maxCacheDBSizeMB: 4096
            storage_policy_copy.copy_client_side_dedup = False
            storage_policy_copy.set_encryption_properties(re_encryption=True, encryption_type="AES", encryption_length=256)

            query = '''update archgroupcopy
                    set maxCacheDBSizeMB = 4096 where id = %s''' % storage_policy_copy.copy_id
            self.log.info(f"Executing Query to set CacheDBSize: {query}")
            self.utility.update_commserve_db(query)

            # 3: Run a Backup Job and then AuxCopy and run Validations(properties set)
            # 1st Iteration
            self.log.info('Submitting 1st Full Backup')
            backup_job = self.subclient.backup(backup_level='Full')
            if backup_job.wait_for_completion():
                self.log.info(f'1st Backup Completed :Id - {backup_job.job_id}')
            else:
                raise Exception(f'1st Backup {backup_job.job_id} Failed with JPR: {backup_job.delay_reason}')
            time.sleep(60)

            self.log.info('Submitting AuxCopy job with scalable resource allocation')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(use_scale=True)
            if aux_copy_job.wait_for_completion():
                self.log.info(f'1st AuxCopy Completed :Id - {aux_copy_job.job_id}')
            else:
                raise Exception(f'1st AuxCopy {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')

            self.run_validations(1, backup_job.job_id, aux_copy_job.job_id)

            # 4: Submit another Backup Job and again a AuxCopy Job
            # 2nd Iteration
            self.log.info('Submitting 2nd Full Backup')
            backup_job = self.subclient.backup(backup_level='Full')
            if backup_job.wait_for_completion():
                self.log.info(f'2nd Backup Completed :Id - {backup_job.job_id}')
            else:
                raise Exception(f'2nd Backup {backup_job.job_id} Failed with JPR: {backup_job.delay_reason}')
            time.sleep(60)

            self.log.info('Submitting AuxCopy job with scalable resource allocation')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(use_scale=True)
            if aux_copy_job.wait_for_completion():
                self.log.info(f'2nd AuxCopy Completed :Id - {aux_copy_job.job_id}')
            else:
                raise Exception(f'2nd AuxCopy {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')

            # 5: Run Validations (new read-less, Network Optimized, Cache used, Dedupe Occurred)
            self.run_validations(2, backup_job.job_id, aux_copy_job.job_id)

        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error(f'Exception Occurred: {exe}')

    def run_validations(self, iteration, backup_job_id, aux_copy_job_id):
        """Runs the validations
            Args:

                    iteration             (int)  --   Iteration of the Case Validations

                    backup_job_id         (str)  --   Id of Backup Job

                    aux_copy_job_id       (str)  --   Id of the AuxCopy Job
        """

        log_file = 'CVJobReplicatorODS.log'
        self.log.info(f'********* ITERATION {iteration} *********')

        self.log.info('*** CASE 1: 10.0 Using readless Mode ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[0], aux_copy_job_id)
        if matched_line:
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
            self.status = constants.FAILED

        self.log.info('*** CASE 2: Signatures Processed ***')
        signatures_processed = 0
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[1], aux_copy_job_id,
            escape_regex=False)
        if matched_line:
            for string in matched_string:
                signatures_processed += int(string.split(' ')[-1].split(']')[0])
            self.log.info('Signatures Processed = %d', signatures_processed)
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error Result : Failed')
            self.status = constants.FAILED

        if iteration == 1:
            self.log.info('*** CASE 3: Found in cache - 0 ***')
        else:
            self.log.info('*** CASE 3: Found in cache != 0  but equals Signatures processed***')
        found_in_cache = 0
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[2], aux_copy_job_id,
            escape_regex=False)
        if matched_line:
            for string in matched_string:
                found_in_cache += int(string.split(' ')[-2])
            self.log.info('Found in Cache: %d', found_in_cache)
            if iteration == 1 and found_in_cache == 0:
                self.log.info('Success Result : Passed')
            elif iteration == 2 and abs(signatures_processed - found_in_cache) <= 10:
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
        compressed_size = 0
        transferred_size = 0
        discarded_size = 0
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[3], aux_copy_job_id,
            escape_regex=False)
        if matched_line:
            for string in matched_string:
                compressed_size += int(string.split(' ')[2])
            self.log.info('Compressed Size = %d(%f GB)', compressed_size, compressed_size/(1024*1024*1024))
        else:
            self.log.error('Error  Result : Failed')
            self.status = constants.FAILED

        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            check_string, aux_copy_job_id,
            escape_regex=False)
        if matched_line and iteration == 1:
            for string in matched_string:
                transferred_size += int(string.split(' ')[2])
            self.log.info('Size-New Data = %d(%f GB)', transferred_size, transferred_size/(1024*1024*1024))
            if compressed_size == transferred_size:
                self.log.info('Success Result : Passed')
            else:
                self.log.error('Error  Result : Failed')
                self.status = constants.FAILED
        elif matched_line and iteration == 2:
            for string in matched_string:
                discarded_size += int(string.split(' ')[2])
            self.log.info('Size Discarded = %d(%f GB)', discarded_size, discarded_size/(1024*1024*1024))
            # Giving tolerance up to 10 signatures for diff b/w compressed size and discarded size
            if abs(compressed_size - discarded_size) <= (128*1024*10):
                self.log.info('Success Result : Passed')
            else:
                self.log.error('Error  Result : Failed')
                self.status = constants.FAILED
        else:
            self.log.error('Error  Result : Failed')
            self.status = constants.FAILED

        self.log.info('*** CASE 6: Did Dedupe Occur? ***')

        primary = self.dedupe_helper.get_primary_objects_sec(backup_job_id, self.copy_name)

        secondary = self.dedupe_helper.get_secondary_objects_sec(backup_job_id,
                                                                 self.copy_name)
        self.list_primary.append(int(primary))
        self.list_secondary.append(int(secondary))
        self.log.info(f'Primary Objects : {primary}')
        self.log.info(f'Secondary Objects : {secondary}')
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
            self.log.info(f"PID {(matched_string[0].split(' ')[-4])}")
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
        #     self.status = constants.FAILED

        self.log.info('*** CASE 14: LA enabled or disabled ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            self.tcinputs['PrimaryCopyMediaAgent'], log_file,
            self.config_strings[14], aux_copy_job_id,
            escape_regex=False)
        if matched_line:
            if self.use_lookahead and 'enabled' in matched_line[0]:
                self.log.info('Success Result : Passed, LA is enabled')
            elif not self.use_lookahead and 'disabled' in matched_line[0]:
                self.log.info('Success Result : Passed, LA is disabled')
            else:
                self.log.error(f'Error  Result : Failed. LA Enabled?: {self.use_lookahead}. Log: {matched_line[0]}')
                self.status = constants.FAILED
        else:
            self.log.error('Error  Result : Failed')
            self.status = constants.FAILED

        self.log.info('*** CASE 15: ArchChunkToReplicate status ***')
        query = '''select distinct status
                from archchunktoreplicatehistory where AdminJobId = {0}
                '''.format(aux_copy_job_id)
        self.log.info(f"Executing Query: {query}")
        self.csdb.execute(query)
        row_1 = self.csdb.fetch_one_row()
        self.log.info(f"Result: {row_1}")
        query = '''select distinct status
                from archchunktoreplicate where AdminJobId = {0}
                '''.format(aux_copy_job_id)
        self.log.info(f"Executing Query: {query}", query)
        self.csdb.execute(query)
        row_2 = self.csdb.fetch_one_row()
        self.log.info(f"Result: {row_2}")
        if int(row_1[0]) == 2 or int(row_2[0]) == 2:
            self.log.info('ArchChunkToReplicate status for all chunks is 2')
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error Result : Fail')
            self.status = constants.FAILED

    def set_registry_keys(self):
        """Sets the Registry keys of the Client"""
        self.ma_machine_1.create_registry('MediaAgent', 'UseCacheDB', '1', r'DWord')
        self.ma_machine_1.create_registry('MediaAgent', 'UseAuxcopyReadlessPlus', '1', 'DWord')
        self.log.info("Same MA's: Registry Keys: UseCacheDB, UseAuxCopyreadlessPlus set")

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 6: CleanUp the environment
        self.log.info("ReSetting cvods debug lvl to 1")
        self.ma_machine_1.set_logging_debug_level('CVJobReplicatorODS', 1)
        if self.tcinputs['PrimaryCopyMediaAgent'] == self.tcinputs['SecondaryCopyMediaAgent']:
            # if both MA's are same, remove registry keys set previously
            self.ma_machine_1.remove_registry('MediaAgent', 'UseCacheDB')
            self.ma_machine_1.remove_registry('MediaAgent', 'UseAuxcopyReadlessPlus')
        # revert LA registry to initial configuration
        if self.initial_la_config != -1:  # set registry to whatever it is before
            self.ma_machine_1.create_registry('MediaAgent', 'DataMoverUseLookAheadLinkReader',
                                              f'{self.initial_la_config}', r'DWord')
        elif not self.use_lookahead:  # absent before, so removing it if we have set it in the tc
            self.ma_machine_1.remove_registry('MediaAgent', 'DataMoverUseLookAheadLinkReader')
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
