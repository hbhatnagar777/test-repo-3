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

    run()           --  run function of this test case

    tear_down()     --  teardown function of this test case

    _cleanup()      --  cleanup the entities created

    _get_cloud_server_host()    --  to get cloud server host name

    _reset_sa_disable_settings()    --  reset additional settings to enable storage accelerator functionality

    _validate_chunk_creation()  --  validate if expected writer created new chunk for writing during backup

    _validate_chunk_open()  --  validate if expected reader opened chunk for read during restore

    _validate_sa_permanent_disable()    -- validate if storage accelerator feature is permanently disabled on client

    _validate_sa_auto_disable() --  validate if storage accelerator get auto disable if SA connectivity fails

    _validate_default_sa_behavior() --  validate default storage accelerator functionality

    _validate_backup_fail_over()    --  validate backup fail over to MA and disable SA temporarily

    _validate_restore_fail_over()   --  Validate restore fail over to MA and disable SA temporarily

    _validate_ma_override() --  validate if destination media agent was overriden by storage accelerator


Sample Input:
            {
                "ClientName": "client_name",
                "MediaAgentName": "MA name",
                "AgentName": "File System"
            }
    Additional Inputs -
        "CloudLibraryName": "library name"
        OR
        "CloudMountPath": "mount path"
        "CloudUserName": "user name",
        "CloudPassword": "password",
        "CloudServerType": "Microsoft Azure Storage"
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Storage Accelerator -- SA connectivity to cloud failure case"
        self.mmhelper = None
        self.dedupehelper = None
        self.common_util = None
        self.ma_machine = None
        self.client_machine = None
        self.cloud_library_name = None
        self.storage_policy_name = None
        self.partition_path = None
        self.backupset_name = None
        self.sc_obj = None
        self.cloud_lib_obj = None
        self.mount_path = None
        self.content_path = None
        self.restore_path = None
        self.job_manager = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }

    def _validate_ma_override(self, job_id, sa_permanently_disable=False):
        """
            Validate if destination media agent was overriden by storage accelerator

            Args:
             job_id (int) -- Backup job id or Restore job id

             sa_permanently_disable (bool) -- if sa is permanently disabled then override to MA should not happen
        """
        self.log.info("Validating destination MA overriding with storage accelerator")
        over_ride_log_string = f'Overriding dest MA as this is detected as CORE MA[{self.client.client_id}]'
        over_ride_parse_result = self.dedupehelper.parse_log(self.commcell.commserv_name, 'ArchMgr.log',
                                                             over_ride_log_string, jobid=job_id, only_first_match=True)
        if not sa_permanently_disable:
            if over_ride_parse_result[0]:
                self.log.info("Validated destination MA overriding with storage accelerator.")
            else:
                self.log.error("Destination MA was not overridden with storage accelerator.")
                raise Exception("Destination MA was not overridden with storage accelerator.")
        else:
            if over_ride_parse_result[0]:
                self.log.error("Destination MA overriding with storage accelerator is not expected")
                raise Exception("Destination MA overriding with storage accelerator is not expected")
            else:
                self.log.info("Validated destination MA was not overridden with storage accelerator.")

    def _get_cloud_server_host(self, job_id):
        """
        Get cloud server host name.
            Args:
                 job_id (int) -- Backup job id or Restore job id

        """
        self.log.info("Get cloud server host name")
        host_name_regex = r'http(s)*://(([\-\w]+\.)+[a-zA-Z]{2,4}.*)'
        host_parse_result = self.dedupehelper.parse_log(self.client.name, 'CloudActivity.log', host_name_regex,
                                                        jobid=job_id, escape_regex=False, only_first_match=True)
        if host_parse_result[0]:
            self.log.info(f"Got cloud server url:[{host_parse_result[1][0].split('/')[2]}]")
            return host_parse_result[1][0].split('/')[2]
        else:
            self.log.error("Unable to find cloud server host name.")
            raise Exception("Unable to find cloud server host name.")

    def _reset_sa_disable_settings(self, remove_host_file_entry=False):
        """
        Reset additional settings to enable storage accelerator functionality
            Args:
                 remove_host_file_entry (bool) -- to remove host file entry of cloud server so that SA can reach it
        """

        self.log.info("Resetting additional settings to enable storage accelerator")
        if self.client_machine.get_registry_value('MediaAgent', 'StorageAcceleratorAutoDisabledUntil') != '':
            sa_current_time = int(self.client_machine.current_time().timestamp())
            # Simulate one day interval for enabling storage accelerator
            sa_new_disable_time = sa_current_time - 86400
            self.client_machine.update_registry('MediaAgent', 'StorageAcceleratorAutoDisabledUntil',
                                                sa_new_disable_time, reg_type='String')
            # CVD restart is required to reinitialize StorageAcceleratorAutoDisabledUntil value
            self.log.info("CVD restart to reinitialize StorageAcceleratorAutoDisabledUntil value")
            self.client.restart_services()
        if remove_host_file_entry:
            self.client.delete_additional_setting('CommServDB.Client', 'DisableStorageAccelerator')
            self.log.info("Removing host file entry for cloud server so that client can reach the cloud server")
            self.client_machine.remove_host_file_entry('127.0.0.1')

    def _validate_chunk_creation(self, expected_writer_name, job_id):
        """
            Validate if expected writer created new chunk for writing during backup

            Args:
             expected_writer_name (str) -- Name of the pipeline's destination machine

             job_id (int) -- Backup job id
        """
        self.log.info(f"Validating new chunk creation by {expected_writer_name}")
        chunk_create_log_string = f'Creating new chunk id'
        chunk_create_parse_result = self.dedupehelper.parse_log(expected_writer_name, 'cvd.log',
                                                                chunk_create_log_string, jobid=job_id,
                                                                only_first_match=True)
        if chunk_create_parse_result[0]:
            self.log.info(f"Validated new chunk creation by {expected_writer_name}.")
        else:
            self.log.error(f"New chunk was not created by {expected_writer_name}.")
            raise Exception(f"New chunk was not created by {expected_writer_name}.")

    def _validate_chunk_open(self, expected_reader_name, job_id):
        """
            Validate if expected reader opened chunk for read during restore

            Args:
             job_id (int) -- Restore job id
        """
        self.log.info(f"Validating chunk open by {expected_reader_name}")
        chunk_open_log_string = f'Opening the Chunk'
        chunk_open_parse_result = self.dedupehelper.parse_log(expected_reader_name, 'cvd.log',
                                                              chunk_open_log_string, jobid=job_id,
                                                              only_first_match=True)
        if chunk_open_parse_result[0]:
            self.log.info(f"Validated chunk open by {expected_reader_name}.")
        else:
            self.log.error(f"Chunk was not opened by {expected_reader_name}.")
            raise Exception(f"Chunk was not opened by {expected_reader_name}.")

    def _validate_sa_permanent_disable(self):
        """
        Validate if storage accelerator feature is permanently disabled on client
        """
        self.log.info("Validate if storage accelerator feature is permanently disabled on client")
        query = f""" SELECT value FROM APP_AdvanceSettings 
                     WHERE keyName = 'DisableStorageAccelerator' 
                            AND entityId = {self.client.client_id}
                            AND     entityType =  3 -- CLIENT_ENTITY
                            AND     relativePath = 'CommServDB.Client'"""
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] != 'true':
            self.log.error("Storage Accelerator is still enabled on client.")
            raise Exception("Storage Accelerator is still enabled on client")
        self.log.info("Storage Accelerator is permanently disabled on client")

    def _validate_sa_auto_disable(self, expected_sa_fail_count):
        """
        Validate if storage accelerator get auto disable if SA connectivity fails
            Args:
             expected_sa_fail_count (int) -- Expected consecutive failure count
        """
        if expected_sa_fail_count > 8:
            self._validate_sa_permanent_disable()
        else:
            sa_auto_disable_until = int(self.client_machine.get_registry_value('MediaAgent',
                                                                               'StorageAcceleratorAutoDisabledUntil'))
            sa_current_time = int(self.client_machine.current_time().timestamp())

            if sa_auto_disable_until > sa_current_time:
                self.log.info(f"storage accelerator got auto disabled until {sa_auto_disable_until}")
            else:
                self.log.error("storage accelerator is not auto disabled")
                raise Exception("storage accelerator is not auto disabled")

            sa_failure_count = int(self.client_machine.get_registry_value('MediaAgent',
                                                                          'StorageAcceleratorConsecutiveFailureCount'))
            if sa_failure_count == expected_sa_fail_count:
                self.log.info(f"storage accelerator got failed for {sa_failure_count} times as expected")
            else:
                self.log.error(f"storage accelerator failed for {sa_failure_count} times "
                               f"but failure count expected is {expected_sa_fail_count}")
                raise Exception("storage accelerator failure count is not correct")

            if sa_failure_count == 8:
                self._validate_sa_permanent_disable()
            else:
                self._reset_sa_disable_settings()

    def _validate_default_sa_behavior(self):
        """
        Validate default storage accelerator functionality
        """

        if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 1):
            self.log.error("unable to Generate Data at %s", self.content_path)
            raise Exception("unable to Generate Data at {0}".format(self.content_path))
        self.log.info("Generated Data at %s", self.content_path)
        # Run a Backup
        self.log.info("Run a backup to validate default storage accelerator behaviour")
        job_id = self.common_util.subclient_backup(self.sc_obj, 'full').job_id
        # Validate storage accelerator functionality
        if self.client_machine.get_registry_value(
                'MediaAgent', 'StorageAcceleratorConsecutiveFailureCount') not in ('', '0'):
            self.log.error("Additional settings related to SA disable is still present")
            raise Exception("Additional settings related to SA disable is still present")
        self._validate_ma_override(job_id)
        self._validate_chunk_creation(self.client.name, job_id)
        return job_id

    def _validate_backup_fail_over(self, failure_attempt):
        """
        Validate fail over to MA and disable SA temporarily if SA connectivity fails for 7 consecutive times
            Args:
                failure_attempt (int) -- Current SA connectivity failure attempt
        """

        self.log.info(f"Running SA connectivity failure attempt - {failure_attempt} ")

        if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 1):
            self.log.error("unable to Generate Data at %s", self.content_path)
            raise Exception("unable to Generate Data at {0}".format(self.content_path))
        self.log.info("Generated Data at %s", self.content_path)
        # Run a Backup and validate fail over to media agent functionality with log parsing
        job_id = self.common_util.subclient_backup(self.sc_obj, 'full').job_id
        self._validate_ma_override(job_id, True if failure_attempt > 8 else False)
        self._validate_chunk_creation(self.tcinputs['MediaAgentName'], job_id)
        self._validate_sa_auto_disable(failure_attempt)

    def _validate_restore_fail_over(self, failure_attempt):
        """
            Validate fail over to MA and disable SA temporarily if SA connectivity fails for 7 consecutive times
            Args:
                failure_attempt (int) -- Current SA connectivity failure attempt
        """

        self.log.info(f"Running SA connectivity failure attempt - {failure_attempt} ")

        # Run a Restore and validate fail over to media agent functionality with log parsing
        restore_job = self.sc_obj.restore_out_of_place(self.client, self.restore_path, [self.content_path])
        self.log.info(f"Restore job {restore_job.job_id} has started.")
        self.job_manager.job = restore_job
        if failure_attempt <= 8:
            if not self.job_manager.wait_for_state('pending', hardcheck=False):
                self.log.warning(f"Restore job {restore_job.job_id} didn't reach pending state.")
            else:
                self.job_manager.modify_job(set_status="resume", hardcheck=False)
        self.job_manager.wait_for_state('completed')

        self._validate_ma_override(restore_job.job_id, True if failure_attempt > 8 else False)
        self._validate_chunk_open(self.tcinputs['MediaAgentName'], restore_job.job_id)
        self._validate_sa_auto_disable(failure_attempt)

    def setup(self):
        """Setup function of this test case"""

        options_selector = OptionsSelector(self.commcell)
        self.cloud_library_name = '%s_cloud_library-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                          self.tcinputs['ClientName'])
        self.storage_policy_name = '%s_policy-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                    self.tcinputs['ClientName'])
        self.backupset_name = '%s_bs-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                           self.tcinputs['ClientName'])
        self.client_machine = options_selector.get_machine_object(self.client)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])

        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        self.job_manager = JobManager(commcell=self.commcell)

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=25 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating content")
        self.log.info('selected drive: %s', client_drive)

        # Content path
        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'TestData')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)

        # Restore path
        self.restore_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'RestoreData')
        if self.client_machine.check_directory_exists(self.restore_path):
            self.client_machine.remove_directory(self.restore_path)

        # DDB partition path
        if self.tcinputs.get("PartitionPath") is not None:
            self.partition_path = self.tcinputs['PartitionPath']
        else:
            if self.ma_machine.os_info.lower() == 'unix':
                self.log.error("LVM enabled DDB partition path must be an input for the unix MA.")
                raise Exception("LVM enabled partition path not supplied for Unix MA!..")
            # To select drive with space available in Media agent machine
            self.log.info('Selecting drive in the Media agent machine based on space available')
            ma_drive = options_selector.get_drive(self.ma_machine, size=25 * 1024)
            if ma_drive is None:
                raise Exception("No free space for hosting ddb")
            self.log.info('selected drive: %s', ma_drive)
            self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')

    def _cleanup(self):
        """cleanup the entities created"""

        self.log.info(
            "********************** CLEANUP STARTING *************************")
        try:
            # Deleting Content Path
            self.log.info("Deleting content path: %s if exists", self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted content path: %s", self.content_path)

            # Deleting Restore Path
            self.log.info("Deleting restore path: %s if exists", self.restore_path)
            if self.client_machine.check_directory_exists(self.restore_path):
                self.client_machine.remove_directory(self.restore_path)
                self.log.info("Deleted content path: %s", self.restore_path)

            # Deleting Backupsets
            self.log.info("Deleting BackupSet if exists")
            if self._agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("BackupSet[%s] exists, deleting that", self.backupset_name)
                self._agent.backupsets.delete(self.backupset_name)

            # Deleting Storage Policies
            self.log.info("Deleting Storage Policy if exists")
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Storage Policy[%s] exists, deleting that", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            # Deleting Libraries
            if not self.tcinputs.get("CloudLibraryName"):
                self.log.info(f"Deleting library {self.cloud_library_name}")
                if self.commcell.disk_libraries.has_library(self.cloud_library_name):
                    self.log.info("Library[%s] exists, deleting that", self.cloud_library_name)
                    self.commcell.disk_libraries.delete(self.cloud_library_name)
                    self.log.info(f"{self.cloud_library_name} deleted successfully!")

            # Enable storage accelerator
            self._reset_sa_disable_settings(remove_host_file_entry=True)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception(
                "Error encountered during cleanup: {0}".format(str(exp)))
        self.log.info(
            "********************** CLEANUP COMPLETED *************************")

    def tear_down(self):
        """Tear Down Function of this Case"""
        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment."
                "Please check for failure reason and manually clean up the environment..."
            )
            self._reset_sa_disable_settings(remove_host_file_entry=True)
            # Deleting Content Path
            self.log.info("Deleting content path: %s if exists", self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted content path: %s", self.content_path)

            # Deleting Restore Path
            self.log.info("Deleting restore path: %s if exists", self.restore_path)
            if self.client_machine.check_directory_exists(self.restore_path):
                self.client_machine.remove_directory(self.restore_path)
                self.log.info("Deleted content path: %s", self.restore_path)

    def run(self):
        """Main test case logic"""
        try:
            self._cleanup()

            # Creating cloud storage.
            if self.tcinputs.get("CloudLibraryName"):
                self.cloud_library_name = self.tcinputs.get("CloudLibraryName")
                if not self.commcell.disk_libraries.has_library(self.cloud_library_name):
                    raise Exception("Cloud library name provided is invalid!")
                self.cloud_lib_obj = self.commcell.disk_libraries.get(self.cloud_library_name)

            elif (("CloudMountPath" and "CloudUserName" and "CloudPassword" and "CloudServerType" in self.tcinputs) and
                  (self.tcinputs["CloudMountPath"] and self.tcinputs["CloudUserName"]
                   and self.tcinputs["CloudPassword"] and self.tcinputs["CloudServerType"])):
                self.cloud_lib_obj = self.mmhelper.configure_cloud_library(self.cloud_library_name,
                                                                           self.tcinputs['MediaAgentName'],
                                                                           self.tcinputs["CloudMountPath"],
                                                                           self.tcinputs["CloudUserName"],
                                                                           self.tcinputs["CloudPassword"],
                                                                           self.tcinputs["CloudServerType"])
            else:
                raise Exception("No cloud library details provided.")

            # create deduplication enabled storage policy
            sp_dedup_obj = self.dedupehelper.configure_dedupe_storage_policy(self.storage_policy_name,
                                                                             self.cloud_lib_obj,
                                                                             self.tcinputs['MediaAgentName'],
                                                                             self.partition_path)

            # Set retention of 0day 1cycle on deduplication enabled secondary copy
            self.log.info("Setting Retention: 0-days and 1-cycle on Secondary Copy")
            dedupe_copy_obj = sp_dedup_obj.get_copy('Primary')
            retention = (0, 1, -1)
            dedupe_copy_obj.copy_retention = retention

            # create backupset
            self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            # create subclient
            self.sc_obj = self.mmhelper.configure_subclient(self.backupset_name, "%s_SC" % str(self.id),
                                                            self.storage_policy_name, self.content_path, self.agent)

            # Run a Backup and validate storage accelerator functionality with log parsing
            self.client.add_additional_setting('EventManager', 'CloudActivity_DEBUGLEVEL', 'INTEGER', '2')
            job_id = self._validate_default_sa_behavior()
            self.client.delete_additional_setting('EventManager', 'CloudActivity_DEBUGLEVEL')

            # Get cloud server host name
            cloud_server_host_name = self._get_cloud_server_host(job_id)

            # Add host file entry
            self.log.info("Adding host file entry for cloud server to loop back address so that client fails to reach "
                          "the cloud server")
            self.client_machine.add_host_file_entry(cloud_server_host_name, '127.0.0.1')

            # Validate fail over to MA and disable SA temporarily if SA connectivity fails for 7 consecutive times
            self._validate_backup_fail_over(failure_attempt=1)
            self._validate_restore_fail_over(failure_attempt=2)

            # Simulating 7 SA failure attempts
            self.log.info("Simulating 7 consecutive SA failure attempts")
            self.client_machine.update_registry('MediaAgent', 'StorageAcceleratorConsecutiveFailureCount',
                                                7, reg_type='String')
            # CVD restart is required to reinitialize StorageAcceleratorConsecutiveFailureCount value
            self.log.info("CVD restart to reinitialize StorageAcceleratorConsecutiveFailureCount value")
            self.client.restart_services()

            # Validate fail over to MA and disable SA permanently if SA connectivity fails for 8th consecutive time
            self._validate_backup_fail_over(failure_attempt=8)

            # Validate SA permanent disable if SA connectivity fails for more than 7 times
            self._validate_restore_fail_over(failure_attempt=9)
            self._validate_backup_fail_over(failure_attempt=10)

            # Enable SA and validate normal storage accelerator functionality with log parsing
            self._reset_sa_disable_settings(remove_host_file_entry=True)

            # Run a Backup and validate storage accelerator functionality with log parsing
            self._validate_default_sa_behavior()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
