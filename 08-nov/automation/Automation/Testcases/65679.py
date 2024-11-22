# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case
TestCase to perform 3dfs fd cache via DSIP writes and read
TestCase is the only class defined in this file.
TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class
                                --  function to carry out data protection operations
    setup()                     --  setup function of this test case
    run()                       --  run function of this test case
    tear_down()                 --  teardown function of this test case
    _cleanup()                 --  clean TC created resources.

Design Steps:
1. Ensure Library creation for HPE StoreOnce Catalyst Library feature is enabled on the setup.
2. Add a HPE Catalyst Library.
3. Try adding a Mount Path to the library.
4. Try configuring dedupe storage pool, as Commvault deduplication is not supported with HP storeonce.
5. Try configuring non-dedupe storage pool and also enable multiplexing. -- This configuration should also error out; Mux is not supported.
6. Try configuring non-dedupe storage pool -- It should be successful.
7. Create dependent primary copy to it and run backups and restores.
8. Create a new Storage pool with a new HPE Library. Create a secondary copy using this storage pool.
9. Run Aux Copy.
"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.hpe_dd_helper import HPEHelper
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import (constants, commonutils)


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "HPStoreOnce Acceptance SDK"
        self.client_machine = None
        self.MediaAgentName = None
        self.primary_lib_name = None
        self.secondary_lib_name = None
        self.saved_creds = None
        self.storeName = None
        self.username = None
        self.password = None
        self.host = None
        self.content_path = None
        self.disk_mount_path = None
        self.dedupe_path = None
        self.dedup_storage_pool_name = None
        self.non_dedup_storage_pool_name = None
        self.secondary_non_dedup_storage_pool_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.storage_policy_obj = None
        self.maintainence_process_interval = None
        self.prune_process_interval = None

        self.options_selector = None
        self.hpe_helper = None
        self.mmhelper = None
        self.CommonUtils = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgentName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.options_selector = OptionsSelector(self.commcell)
        self.hpe_helper = HPEHelper(self)
        self.mmhelper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        self.common_util = CommonUtils(self)

        self.MediaAgentName = self.tcinputs.get("MediaAgentName", "")
        self.primary_lib_name = f'Primary-HPE-Catalyst-{self.MediaAgentName}-Lib-{self.id}'
        self.secondary_lib_name = f'Secondary-HPE-Catalyst-{self.MediaAgentName}-Lib-{self.id}'
        self.non_dedup_storage_pool_name = f'Non-Dedup-HPE-Catalyst-{self.MediaAgentName}-{self.id}-pool'
        self.secondary_non_dedup_storage_pool_name = f'Aux-HPE-Catalyst-{self.MediaAgentName}-{self.id}-pool'
        self.dedup_storage_pool_name = f'Dedup-HPE-Catalyst-{self.MediaAgentName}-{self.id}-pool'
        self.backupset_name = f'HPE-Catalyst-Auto-BackUpSet-{self.id}'
        self.subclient_name = f'HPE-Subclient-{self.id}'
        self.storage_policy_name = f'HPE-Storage-Policy-{self.MediaAgentName}-{self.id}'
        self.prune_process_interval = 2
        self.maintainence_process_interval = 5

        if "SavedCredentails" in self.tcinputs:
            self.saved_creds = self.tcinputs.get("SavedCredentials")
        else:
            self.storeName = self.tcinputs.get("StoreName")
            if not self.storeName:
                raise Exception("HPE Library store name not provided in tc inputs!!")
            self.username = self.tcinputs.get("Username")
            if not self.username:
                raise Exception("HPE Library username to access Mount Path not provided in tc inputs!!")
            self.password = self.tcinputs.get("Password")
            if not self.password:
                raise Exception("HPE Library password to access Mount Path not provided in tc inputs!!")
            self.host = self.tcinputs.get("Host")
            if not self.host:
                raise Exception("HPE Library host IP not provided in tc inputs!!")

        self.log.info("Creating client machine object!!")
        self.client_machine = self.options_selector.get_machine_object(
            self.tcinputs['ClientName'])
        self.media_agent_machine = self.options_selector.get_machine_object(
            self.MediaAgentName
        )

        # Create client drive object
        self.log.info(
            'Selecting drive in the client machine based on space available')
        client_drive = self.options_selector.get_drive(
            self.client_machine, size=10 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)
        self.content_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata')
        self.restore_dest_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'RestoreData')

        # Create MA Drive object
        self.log.info(
            'Selecting drive in the media agent machine based on space available')
        media_agent_drive = self.options_selector.get_drive(
            self.media_agent_machine, size=10 * 1024)
        if media_agent_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', media_agent_drive)
        self.disk_mount_path = self.media_agent_machine.join_path(
            media_agent_drive, 'Automation', str(self.id), 'Disk Mount Path')
        # Partition path
        self.dedupe_path = self.media_agent_machine.join_path(
            media_agent_drive, 'Automation', str(self.id), 'DDB_mount_path'
        )
        self.cleanup()

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(f"Creating HPE Store Once Library:- {self.primary_lib_name}")
            library_object = self.hpe_helper.configure_hpe_library(
                self.primary_lib_name,
                self.MediaAgentName,
                self.storeName,
                self.host,
                self.username,
                self.password
            )
            self.log.info(f"{self.primary_lib_name} successfully created.")

            self.log.info(f"Creating HPE Store Once Library:- {self.secondary_lib_name}")
            self.hpe_helper.configure_hpe_library(
                self.secondary_lib_name,
                self.MediaAgentName,
                self.storeName,
                self.host,
                self.username,
                self.password
            )
            self.log.info(f"{self.secondary_lib_name} successfully created.")

            # NEGATIVE CASE: Try Adding MountPath to Primary Library.
            add_mount_path_flag = True
            try:
                self.mmhelper.configure_disk_mount_path(
                    library_object,
                    self.disk_mount_path,
                    self.MediaAgentName
                )
            except Exception as e:
                add_mount_path_flag = False
                self.log.info(f"NEGATIVE CASE: Adding Mount Path to HPE Library failed as expected with error :- {e}")
            
            if add_mount_path_flag:
                raise Exception(f"NEGATIVE CASE: Failed mount path was successfully added to HPE Storage.")

            # NEGATIVE CASE: Try Configuring Dedupe Storage Pool. --Added MR 440542 update case to fail if operation goes through.
            dedupe_storage_policy_flag = True
            try:
                self.log.info(f"Configure dedpe storage pool using library - {self.primary_lib_name}")
                self.dedupe_helper.configure_global_dedupe_storage_policy(
                    self.dedup_storage_pool_name,
                    self.primary_lib_name,
                    self.MediaAgentName,
                    self.dedupe_path,
                    self.MediaAgentName
                )
            except Exception as e:
                dedupe_storage_policy_flag = False
                self.log.info(
                    f"NEGATIVE CASE: Adding Dedupe StoragePolicy to HPE Library failed as expected with error :- {e}")
            
            # Uncomment this code after MR 440542 is fixed. 
            # if dedupe_storage_policy_flag:
            #     raise Exception(f"NEGATIVE CASE: Failed dedupe storage policy was created for HPE Storage.")

            # Configure non dedupe storage pool
            self.log.info(f"creating non dedupe storage pool using library - {self.primary_lib_name}")
            self.commcell.storage_pools.add(
                storage_pool_name=self.non_dedup_storage_pool_name,
                mountpath='',
                media_agent=self.MediaAgentName,
                library_name=self.primary_lib_name
            )

            # Configure secondary non dedupe storage pool.
            self.log.info(f"creating non dedupe storage pool using library - {self.secondary_lib_name}")
            self.commcell.storage_pools.add(
                storage_pool_name=self.secondary_non_dedup_storage_pool_name,
                mountpath='',
                media_agent=self.MediaAgentName,
                library_name=self.secondary_lib_name
            )

            # Create Storage Policy.
            self.log.info(f"creating storage dependant storage policy for - {self.non_dedup_storage_pool_name}")
            self.storage_policy_obj = self.mmhelper.configure_storage_policy(
                self.storage_policy_name,
                self.primary_lib_name,
                self.tcinputs.get('MediaAgentName')
            )

            # Setting retention to 0 days and 1 cylcle -
            self.log.info("Setting Retention: 0-days and 1-cycle on Primary Copy")
            copy_obj = self.storage_policy_obj.get_copy("Primary")
            retention = (0, 1, -1)
            copy_obj.copy_retention = retention

            # Create Backupset -
            self.log.info(f"creating backupset : {self.backupset_name}")
            self.mmhelper.configure_backupset(self.backupset_name)

            # Create Subclient
            self.log.info("creating subclient")
            subclient_obj = self.mmhelper.configure_subclient(
                self.backupset_name, self.subclient_name,
                self.storage_policy_name, self.content_path, self.agent
            )

            # Run Backups -
            jobs = self.run_backups(subclient_obj)

            self.age_first_cycle_job(jobs[:4])

            # restore from primary copy -
            restore_job = subclient_obj.restore_out_of_place(self.client, self.restore_dest_path,
                                                            [self.content_path])
            self.log.info("restore job [%s] has started from primary copy.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error(
                    "restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info(
                "restore job [%s] has completed.", restore_job.job_id)

            # Verify Restore
            if self.client_machine.os_info == 'UNIX':
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '/')
            else:
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '\\')

            dest_path = self.client_machine.join_path(dest_path, 'Testdata')

            self.restore_verify(self.content_path, dest_path)

            # Adding Secondary Copy to the storage policy
            self.log.info(f"Adding secondary copy to storage policy {self.storage_policy_name}")
            self.hpe_helper.create_secondary_copy('AuxCopy', self.storage_policy_name, self.MediaAgentName,
                                                self.secondary_non_dedup_storage_pool_name)
            self.log.info("Successfully created secondary copy!!")

            # Run Aux Copy
            auxcopy_job = self.storage_policy_obj.run_aux_copy()
            self.log.info("Auxcopy job [%s] has started.", auxcopy_job.job_id)
            if not auxcopy_job.wait_for_completion():
                self.log.error(
                    "Auxcopy job [%s] has failed with %s.", auxcopy_job.job_id, auxcopy_job.delay_reason)
                raise Exception(
                    "Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id, auxcopy_job.delay_reason))
            self.log.info(
                "Auxcopy job [%s] has completed.", auxcopy_job.job_id)
        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED


    def age_first_cycle_job(self, jobs):
        """
            Verifies if jobs that have meet retention are aged.

            Args:
                jobs         (list)       --  list of jobs to be verified.

            Raises:
                Exception - If jobs are not aged.
        """
        # Verify Job aged
        job_aged = False
        for _ in range(3):
            # Running Granular Data Aging Job.
            self.run_data_aging()
            time.sleep(2 * 60)
            if self.verifyJobAged(jobs):
                job_aged = True
                break
        if not job_aged:
            raise Exception(f"Jobs are not pruned!")

    def restore_verify(self, src_path, dest_path):
        """
            Performs the verification after restore

            Args:
                src_path         (str)       --  path on source machine that is to be compared.

                dest_path        (str)       --  path on destination machine that is to be compared.

            Raises:
                Exception - Any difference from source data to destination data

        """
        self.log.info("Comparing source:%s destination:%s", src_path, dest_path)
        diff_output = self.client_machine.compare_folders(self.client_machine, src_path, dest_path)

        if not diff_output:
            self.log.info("Checksum comparison successful")
        else:
            self.log.error("Checksum comparison failed")
            self.log.info("Diff output: \n%s", diff_output)
            raise Exception("Checksum comparison failed")

    def verifyJobAged(self, job_list):
        """
        Verify that Jobs are Aged.
        Args:
            job_list    - (list) list of jobs to be verified.
        """
        self.log.info(f"Validating jmjobdatastats table for {job_list}")
        jobs_str = ','.join(job_list)
        query = f"""select agedBy from jmjobdatastats  where jobid in ({jobs_str})"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        aged_flags = [x[0] for x in res]
        self.log.info(f"RESULT: {aged_flags}")
        for flag in aged_flags:
            if flag != '512':
                self.log.info("All jobs are not aged yet!")
                return False
        self.log.info("All jobs are aged successfully!")
        return True

    def run_data_aging(self):
        """Run data aging job"""
        data_aging_job = self.mmhelper.submit_data_aging_job(
            copy_name='primary',
            storage_policy_name=self.storage_policy_name,
            is_granular=True,
            include_all_clients=True
        )
        self.log.info(
            "Data Aging job [%s] has started.", data_aging_job.job_id)
        if not data_aging_job.wait_for_completion():
            self.log.error(
                "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
            raise Exception(
                "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                   data_aging_job.delay_reason))
        self.log.info(
            "Data Aging job [%s] has completed.", data_aging_job.job_id)

    def generate_backup_data(self, content_path):
        """
        Generates 500MB of uncompressable data
        Args:
            content_path    (str)   -- path where data is to be generated.
        """
        self.log.info(f"Creating 500 MB of data on {content_path}")
        self.options_selector.create_uncompressable_data(
            client=self.tcinputs['ClientName'],
            path=content_path,
            size=0.5
        )

    def run_backups_util(self, subclient, job_type, start_new_media=False):
        """
        run a backup job for the subclient specified in Testcase

        Args:
            subclient       (instance)  instance of subclient object
            job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)
            start_new_media (boolean)   flag to enable/disable start new media option for backup job

        returns job id(int)
        """
        job = subclient.backup(backup_level=job_type,
                               advanced_options={'mediaOpt': {'startNewMedia': start_new_media}})
        self.log.info("starting %s backup job %s...", job_type, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run backup job with error: {0}".format(job.delay_reason)
            )
        self.log.info("backup job: %s completed successfully", job.job_id)

        return job.job_id

    def run_backups(self, subclient):
        """ Run backups on subclient"""
        job_list = ['full', 'incremental', 'incremental', 'differential', 'synthetic_full', 'differential',
                    'synthetic_full']
        job_ids = []
        for job in job_list:
            # Create unique content
            self.log.info(f"Starting Backup Job:- {job}")
            if job not in ('differential', 'synthetic_full'):
                self.generate_backup_data(self.content_path)
            # Perform Backup
            job_id = self.run_backups_util(subclient, job)
            job_ids.append(job_id)

        return job_ids

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status != constants.FAILED:
                self.log.info("Testcase shows successful execution ...")
            else:
                self.log.warning("Testcase shows failure in execution, cleaning up the test environment ...")
            self.cleanup()
            self.log.info("tear down function complete!!")

        except Exception as exp:
            self.log.info("Failure in tear down function - %s", str(exp))

    def cleanup(self):
        self.log.info("****************************** CLEAN UP STARTING *********************************")
        # Delete Content Path
        self.log.info(f"Deleting content path: {self.content_path} if exists!")
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)

        # Delete Restore Path 
        self.log.info(f"Deleting restore path: {self.restore_dest_path} if exists!")
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)

        # Delete backupset
        self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("Deleted BackupSet: %s", self.backupset_name)

        # Delete Storage Policy
        self.log.info("Deleting Storage Policy: %s if exists", self.storage_policy_name)
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("Deleted Storage Policy: %s", self.storage_policy_name)

        # Delete Storage Pools.
        self.log.info("Deleting Storage Pools if exists")
        if self.commcell.storage_policies.has_policy(self.non_dedup_storage_pool_name):
            self.log.info("Storage Policy[%s] exists, deleting that", self.non_dedup_storage_pool_name)
            self.commcell.storage_policies.delete(self.non_dedup_storage_pool_name)

        self.log.info("Deleting Storage Pools if exists")
        if self.commcell.storage_policies.has_policy(self.secondary_non_dedup_storage_pool_name):
            self.log.info("Storage Policy[%s] exists, deleting that", self.secondary_non_dedup_storage_pool_name)
            self.commcell.storage_policies.delete(self.secondary_non_dedup_storage_pool_name)

        self.log.info("Deleting Storage Pools if exists")
        if self.commcell.storage_policies.has_policy(self.dedup_storage_pool_name):
            self.log.info("Storage Policy[%s] exists, deleting that", self.dedup_storage_pool_name)
            self.commcell.storage_policies.delete(self.dedup_storage_pool_name)

        # Deleting Library
        self.log.info("Deleting library: %s if exists", self.primary_lib_name)
        if self.commcell.disk_libraries.has_library(self.primary_lib_name):
            self.commcell.disk_libraries.delete(self.primary_lib_name)
            self.log.info("Deleted library: %s", self.primary_lib_name)

        # Deleting Secondary Library
        self.log.info("Deleting library: %s if exists", self.secondary_lib_name)
        if self.commcell.disk_libraries.has_library(self.secondary_lib_name):
            self.commcell.disk_libraries.delete(self.secondary_lib_name)
            self.log.info("Deleted library: %s", self.secondary_lib_name)

        self.log.info("****************************** CLEAN UP COMPLETE *********************************")