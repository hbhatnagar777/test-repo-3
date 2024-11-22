# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase to perform Basic storage accelerator test.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _run_backup(subclient_obj, backup_type)
                                --  initiates backup job and waits for completion

    _cleanup()                  --  Cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Sample Input:
        "59089": {
          "AgentName": "File System",
          "MediaAgentName": "MA_name",
          "PartitionPath": "/ddb/partition_path",
          "CloudLibrary": "Lib_existing_in_CS",
          "ClientName": "Client_name"
        }
        PartitionPath is an optional parameter for Windows and mandatory for Unix MA.
        Run this case on CS with min FR22.
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "StorageAccelerator(SA)_Cloud_TestCase (Windows Client)"
        self.tcinputs = {
            "MediaAgentName": None,
            "CloudLibrary": None,
            "ClientName": None
        }
        self.cloud_library_name = None
        self.storage_policy_dedupe_name = None
        self.backupset_name = None
        self.client_machine = None
        self.ma_machine = None
        self.partition_path = None
        self.content_path1 = None
        self.restore_dest_path = None
        self.dedupehelper = None
        self.mmhelper = None
        self.bkupsets = None
        self.subclients = None

    def _validate_sapackage(self, clientid):
        """
        Validate if a windows client had storage accelerator package installed

        Args:
            Clientid -- This is the client id for which we are verifying packages installed.
        Return:
            (Bool) True if it exists
            (Bool) False if doesn't exists
        """
        query = f""" select count(1) from simInstalledPackages where simPackageID =  54
                    and ClientId = {clientid} """
        self.log.info(f"Query: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"Result: {cur}")
        if cur[0] == '0':
            return False
        return True

    def _validate_mapackage(self, clientid):
        """
        Validate if windows client also has mediaagent package installed or not.
        Args:
            Clientid -- This is the client id for which we are verifying packages installed.
        Return:
            (Bool) True if it exists
            (Bool) False if doesn't exists
        """
        query = f""" select count(1) from simInstalledPackages where simPackageID = 51
                        and ClientId = {clientid}"""
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] == '0':
            return False
        return True

    def _sa_global_param(self):
        """
        Validate if media managament service configuration parameter "MMCONFIG_CONFIG_STORAGE_ACCELERATOR_ENABLED" is
        enabled or disabled.
        Args:

        Return:
            (Bool) True if enabled
            (Bool) False if disabled
        """
        query = f""" select value from MMConfigs where name = 'MMCONFIG_CONFIG_STORAGE_ACCELERATOR_ENABLED'"""
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] == '1':
            return True
        return False

    def _run_backup(self, subclient_obj, backup_type):
        """
        Initiates backup job and waits for completion
        Args:
            subclient_obj (object) -- subclient object on which backup is initiated
            backup_type (str)      -- backup type to initiate
                                      Eg: full, incremental
        Return:
            (int) backup job_id
        """
        self.log.info("*" * 10 + " Starting Subclient %s Backup ", backup_type + "*" * 10)
        job = subclient_obj.backup(backup_type)
        self.log.info(f"Started {backup_type} backup with Job ID: {job.job_id}")
        if not job.wait_for_completion():
            self.log.error(f"Backup job {job.job_id} has failed with {job.delay_reason}.")
            raise Exception(f"Backup job {job.job_id} has failed with {job.delay_reason}.")
        self.log.info(f"Successfully finished {backup_type} backup job: {job.job_id}")
        return job.job_id

    def _cleanup(self):
        """Cleanup the entities created"""
        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete backup set
            self.log.info(f"Deleting BackupSet: {self.backupset_name} if exists")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info(f"Deleted BackupSet: {self.backupset_name}")

            # Delete Storage Policy
            self.log.info(f"Deleting Dedupe storage policy: {self.storage_policy_dedupe_name} if exists")
            if self.commcell.storage_policies.has_policy(self.storage_policy_dedupe_name):
                self.commcell.storage_policies.delete(self.storage_policy_dedupe_name)
                self.log.info(f"Deleted Dedupe storage policy: {self.storage_policy_dedupe_name}")
            # Removed Cloud library clean up, as we are not creating it in the case.
            # clean up content and restore content paths
            if self.client_machine.check_directory_exists(self.content_path1):
                self.client_machine.remove_directory(self.content_path1)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
            # Run DataAging
            data_aging_job = self.mmhelper.submit_data_aging_job()
            self.log.info(f"Data Aging job {data_aging_job.job_id} has started.")
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    f"Data Aging job {data_aging_job.job_id} has failed with {data_aging_job.delay_reason}.")
                raise Exception(
                    f"Data Aging job {data_aging_job.job_id} has failed with {data_aging_job.delay_reason}.")
            self.log.info(f"Data Aging job [{data_aging_job.job_id}] has completed.")
            # clean up ddb paths
            if self.ma_machine.check_directory_exists(self.partition_path):
                self.ma_machine.remove_directory(self.partition_path)
        except Exception as exp:
            self.log.warning(f"Error encountered during cleanup : {exp}")
        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        timestamp_suffix = options_selector.get_custom_str()
        self.cloud_library_name = self.tcinputs['CloudLibrary']
        self.storage_policy_dedupe_name = str(self.id) + "_Dedupe_1" + timestamp_suffix
        self.backupset_name = str(self.id) + "_BS_" + timestamp_suffix
        self.client_machine = Machine(self.tcinputs['ClientName'], self.commcell)
        self.ma_machine = Machine(self.tcinputs['MediaAgentName'], self.commcell)
        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=20 * 1024)
        if client_drive is None:
            raise Exception("No free space for creating client content.")
        self.log.info(f'selected drive: {client_drive}')
        self.content_path1 = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata1')
        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Restoredata')

        # To decide on the DDB partition path
        if self.tcinputs.get("PartitionPath") is not None:
            self.partition_path = self.tcinputs['PartitionPath']
        else:
            self.log.info("No DDB [PartitionPath] provided as input.")
            if self.ma_machine.os_info.lower() == 'unix':
                self.log.error("LVM enabled path must be an input for the unix MA.")
                raise Exception("LVM enabled partition path not supplied for Unix MA!..")
            self.log.info('Selecting drive in the Win Media agent machine based on space available')
            ma_drive = options_selector.get_drive(self.ma_machine, size=20 * 1024)
            if ma_drive is None:
                raise Exception("No free space for hosting ddb and mount paths")
            self.log.info(f'selected drive: {ma_drive}')
            self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                            'DDB_' + timestamp_suffix)

    def run(self):
        """Run function of this test case"""
        try:

            self._cleanup()
            self.log.info(f"Started executing {self.id} testcase")
            # Check for the SA package on client machine, if not fail case.
            self.log.info("Check if the client has SA package installed or not.")
            if self._validate_sapackage(self.client.client_id) is True:
                self.log.info(f"Client {self.client.name} has storage accelerator package installed.")
            else:
                self.log.error("Client doesn't have storage accelerator package.")
                raise Exception("Client doesn't have storage accelerator package, enter client with SA package")
            # Check for the MA package on client machine, if there error out.
            self.log.info("Check if client also has MA package installed or not.")
            if self._validate_mapackage(self.client.client_id) is False:
                self.log.info("Client doesn't have MA package installed on it.")
            else:
                self.log.error("selected client also has MA package on it, client with no MA package is recommended.")
                raise Exception("selected client also has MA package on it, specify client with no MA package.")
            # Check global configuration parameter value
            self.log.info("Check what is the value of SA global config parameter value.")
            if self._sa_global_param is False:
                self.log.error("SA is disabled on the commcell, enable it and re-run the case.")
                raise Exception("SA is disabled on the commcell, enable the service configuration "
                                "'Config parameter to enable the storage accelerator feature'")
            else:
                self.log.info("SA is enabled on CS. Proceeding with the case run.")
            # create deduplication enabled storage policy
            self.log.info(f"Creating a new dedupe StoragePolicy: {self.storage_policy_dedupe_name}")
            self.ma_machine.create_directory(self.partition_path)
            self.commcell.storage_policies.add(self.storage_policy_dedupe_name,
                                               self.cloud_library_name,
                                               self.tcinputs['MediaAgentName'],
                                               self.partition_path)
            sp_dedup_obj = self.commcell.storage_policies.get(self.storage_policy_dedupe_name)
            self.log.info("StoragePolicy Configuration is successful.")

            # Modify retention to 0day 1cycle
            self.log.info("Updating retention to 0 days and 1 cycle on primary copy")
            sp_dedup_primary_obj = sp_dedup_obj.get_copy("Primary")
            retention = (0, 1, -1)
            sp_dedup_primary_obj.copy_retention = retention

            # creating backup-set
            self.log.info(f"Creating a new backup set: {self.backupset_name}")
            self.backupset = self.agent.backupsets.add(self.backupset_name)
            self.log.info("Backup set created successfully.")

            # creating sub-client
            subclient1_name = str(self.id) + "_SC1"
            self.log.info(f"Adding a new sub-client: {subclient1_name}")
            sc1_obj = self.backupset.subclients.add(subclient1_name, self.storage_policy_dedupe_name)
            self.log.info("Sub-client added successfully.")

            # Set content path and allow multiple data readers to sub-client
            sc1_obj.content = [self.content_path1]
            self.log.info("Set content path to sub-client successful")

            self.log.info("Enabling multiple data readers i.e. 4 on sub-client")
            sc1_obj.data_readers = 4
            sc1_obj.allow_multiple_readers = True
            # Run a cycle of backups
            job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full']

            for sequence_index in range(0, 4):
                # Create unique content
                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    self.log.info(f"Generating data at {self.content_path1}")
                    if not self.client_machine.generate_test_data(self.content_path1, dirs=1, file_size=(20 * 1024),
                                                                  files=2):
                        self.log.error(f"Unable to generate data at {self.content_path1}")
                        raise Exception(f"unable to Generate Data at {self.content_path1}")
                    self.log.info(f"Generated data at {self.content_path1}")

                # Perform Backup parse logs only for non-SF jobs
                job_id = self._run_backup(sc1_obj, job_types_sequence_list[sequence_index])
                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    archmgr_log_string = f'Overriding dest MA as this is detected as CORE MA' \
                                         f'[{self.client.client_id}]'
                    self.log.info(f"Parse string [{archmgr_log_string}]")
                    parse_result1 = self.dedupehelper.parse_log(self.commcell.commserv_name, 'ArchMgr.log',
                                                                archmgr_log_string, jobid=job_id)
                    if parse_result1[0]:
                        self.log.info("Validated, over-ride was done to use Client as SA by ArchMgr.")
                        self.log.info("Checking in Client cvd log for chunk creation")
                        client_cvd_log_string = 'Creating new chunk id'
                        parse_result2 = self.dedupehelper.parse_log(self.client.name, 'cvd.log',
                                                                    client_cvd_log_string, jobid=job_id)
                        if parse_result2[0]:
                            self.log.info("Validated, chunks are created by client. SA package is used.")
                        else:
                            self.log.error("Chunk not created by client.")
                            raise Exception("No Chunk created by client, SA package not used failing the case.")
                    else:
                        self.log.error("ArchMgr didn't override to use client as SA.")
                        raise Exception("ArchMgr didn't override to use client as SA, failing case.")
            # Run a Restore and validate by log parsing
            restore_job = sc1_obj.restore_out_of_place(self.client, self.restore_dest_path, [self.content_path1])
            self.log.info(f"restore job {restore_job.job_id} has started.")
            if not restore_job.wait_for_completion():
                self.log.error(f"restore job {restore_job.job_id} has failed with {restore_job.delay_reason}.")
                raise Exception(f"restore job {restore_job.job_id} has failed with {restore_job.delay_reason}.")
            self.log.info("restore job [%s] has completed.", restore_job.job_id)
            archmgr_restorelog_string = f'Overriding dest MA as this is detected as CORE MA' \
                                        f'[{self.client.client_id}]'
            parse_result3 = self.dedupehelper.parse_log(self.commcell.commserv_name, 'ArchMgr.log',
                                                        archmgr_restorelog_string, jobid=restore_job.job_id)
            if parse_result3[0]:
                self.log.info("Validated, over-ride was done to use Client as SA for restore by ArchMgr.")
            else:
                self.log.error("Restore ran via MA of library.")
                raise Exception("Restore ran via MA of library, We expect SA to be used failing case.")

        except Exception as exp:
            self.log.error('Failed to execute test case with error:%s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        self._cleanup()
