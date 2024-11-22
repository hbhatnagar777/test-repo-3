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

    _validate_sa_package()  --  validate if client had storage accelerator package installed

    _validate_ma_package()  --  validate if client has media agent package installed or not

    _get_sa_credential()    --  get mount path related storage accelerator credential

    _get_cloud_mount_path() --  get cloud mount path container name

    _validate_ma_override() --  validate if destination media agent was overriden by storage accelerator

    _validate_sa_chunk_creation() --  validate if storage accelerator created new chunk for write during backup

    _validate_sa_chunk_open() --    validate if storage accelerator opened chunk for read during restore

    _validate_sa_enabled()  --  validate if storage accelerator feature is enabled on CommCell

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


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Secondary credentials for storage accelerator"
        self.mmhelper = None
        self.dedupehelper = None
        self.common_util = None
        self.ma_machine = None
        self.client_machine = None
        self.cloud_library_name = None
        self.storage_policy_name = None
        self.partition_path = None
        self.backupset_name = None
        self.cloud_lib_obj = None
        self.mount_path = None
        self.content_path = None
        self.restore_path = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }

    def _validate_sa_package(self):
        """
        Validate if client had storage accelerator package installed
        """

        self.log.info("Validating if the client has storage accelerator package installed")
        query = f""" select count(1) from simInstalledPackages where simPackageID IN  (54, 1305)
                    and ClientId = {self.client.client_id} """
        self.log.info(f"Query: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"Result: {cur}")
        if cur[0] == '0':
            self.log.error("Client doesn't have storage accelerator package installed.")
            raise Exception("Client doesn't have storage accelerator package installed.")

        self.log.info(f"Client {self.client.name} has storage accelerator package installed.")

    def _validate_ma_package(self):
        """
        Validate if client has media agent package installed or not.
        """
        self.log.info("Validating if client has MediaAgent package installed")
        query = f""" select count(1) from simInstalledPackages where simPackageID IN (51, 1301)
                        and ClientId = {self.client.client_id}"""
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] != '0':
            self.log.error("Client also has MediaAgent package on it, client with no MA package is recommended.")
            raise Exception("Storage Accelerator client also has MediaAgent package installed.")
        self.log.info(f"Client {self.client.name} doesn't have MediaAgent package installed on it.")

    def _get_sa_credential(self):
        """
        Get mount path related storage accelerator credential
        """
        self.log.info("Get storage accelerator credential")
        query = f""" 
                select	Creds.credentialName
                from	MMMountPathToStorageDevice MPSD, MMMountPath MP,APP_CredentialAssoc CA, APP_Credentials Creds
                where	MPSD.MountPathId=MP.MountPathId
                        and CA.entityId=MPSD.DeviceId and CA.entityType=185 -- DEVICE_ENTITY
                        and CA.credentialId=Creds.credentialId
                        and MP.LibraryId='{self.cloud_lib_obj.library_id}'"""
        self.log.info(f"Query: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"Result: {cur}")
        return cur[0]

    def _get_cloud_mount_path(self):
        """
        Get cloud mount path container name.
        """
        self.log.info("Get cloud mount path container name")
        query = f"""
                select folder from MMDeviceController  MDC
                Join MMMountPathToStorageDevice MPSD on 
                MDC.DeviceId = MPSD.DeviceId
                JOIN MMMountPath MP on 
                MPSD.MountPathId = MP.MountPathId 
                Where MP.LibraryId={self.cloud_lib_obj.library_id}"""
        self.log.info(f"Query: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        return cur[0]

    def _validate_ma_override(self, job_id):
        """
            Validate if destination media agent was overriden by storage accelerator

            Args:
             job_id (int) -- Backup job id or Restore job id
        """
        self.log.info("Validating destination MA overriding with storage accelerator")
        over_ride_log_string = f'Overriding dest MA as this is detected as CORE MA[{self.client.client_id}]'
        over_ride_parse_result = self.dedupehelper.parse_log(self.commcell.commserv_name, 'ArchMgr.log',
                                                             over_ride_log_string, jobid=job_id, 
                                                             only_first_match=True)
        if over_ride_parse_result[0]:
            self.log.info("Validated destination MA overriding with storage accelerator.")
        else:
            self.log.error("Destination MA was not overridden with storage accelerator.")
            raise Exception("Destination MA was not overridden with storage accelerator.")

    def _validate_sa_chunk_creation(self, job_id):
        """
            Validate if storage accelerator created new chunk for write during backup

            Args:
             job_id (int) -- Backup job id
        """
        self.log.info("Validating new chunk creation by storage accelerator")
        chunk_create_log_string = f'Creating new chunk id'
        chunk_create_parse_result = self.dedupehelper.parse_log(self.client.name, 'cvd.log',
                                                                chunk_create_log_string, jobid=job_id,
                                                                only_first_match=True)
        if chunk_create_parse_result[0]:
            self.log.info("Validated new chunk creation by storage accelerator.")
        else:
            self.log.error("New chunk was not created by storage accelerator.")
            raise Exception("New chunk was not created by storage accelerator.")

    def _validate_sa_chunk_open(self, job_id):
        """
            Validate if storage accelerator opened chunk for read during restore

            Args:
             job_id (int) -- Restore job id
        """
        self.log.info("Validating chunk open by storage accelerator")
        chunk_open_log_string = f'Opening the Chunk'
        chunk_open_parse_result = self.dedupehelper.parse_log(self.client.name, 'cvd.log',
                                                              chunk_open_log_string, jobid=job_id,
                                                              only_first_match=True)
        if chunk_open_parse_result[0]:
            self.log.info("Validated chunk open by storage accelerator.")
        else:
            self.log.error("Chunk was not opened by storage accelerator.")
            raise Exception("Chunk was not opened by storage accelerator.")

    def _validate_sa_enabled(self):
        """
        Validate if storage accelerator feature is enabled on CommCell.
        """
        self.log.info("Validate if storage accelerator feature is enabled on CommCell")
        query = f""" select value from MMConfigs where name = 'MMCONFIG_CONFIG_STORAGE_ACCELERATOR_ENABLED'"""
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] != '1':
            self.log.error("Storage Accelerator is disabled on the CommCell, enable it and re-run the case.")
            raise Exception("Storage Accelerator is disabled on the CommCell")
        self.log.info("Storage Accelerator is enabled on CommCell")

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

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=25 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating content")
        self.log.info('selected drive: %s', client_drive)

        # Content path
        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'TestData')

        # Restore path
        self.restore_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'RestoreData')

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

    def run(self):
        """Main test case logic"""
        try:
            self._cleanup()

            # Validate if storage accelerator package is installed on client machine
            self._validate_sa_package()

            # Validate if MA package on client machine is installed
            self._validate_ma_package()

            # Validate if storage accelerator is enabled
            self._validate_sa_enabled()

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

            # Set MediaAgent
            self.cloud_lib_obj.media_agent = self.tcinputs['MediaAgentName']

            # Get Mount Path
            if not self.tcinputs.get("CloudLibraryName"):
                self.mount_path = self.tcinputs["CloudMountPath"]
            else:
                self.mount_path = self._get_cloud_mount_path()
                self.log.info(f"Got mount path {self.mount_path} for library {self.cloud_library_name}")

            # Reset SA credentials
            self.cloud_lib_obj.add_storage_accelerator_credential(self.mount_path, reset=True)
            sa_creds = self._get_sa_credential()
            if sa_creds != '':
                self.log.error(f"Resetting secondary credential on mount path {self.mount_path} failed")
            self.log.info(f"Resetting secondary credential on mount path {self.mount_path} was done successfully")

            # Set SA credentials
            self.cloud_lib_obj.add_storage_accelerator_credential(self.mount_path, self.tcinputs["CloudSACredential"])

            # validate SA credentials are set on mount path
            sa_creds = self._get_sa_credential()
            if sa_creds != self.tcinputs["CloudSACredential"]:
                self.log.error(f"Setting secondary credential on mount path {self.mount_path} failed")
            self.log.info(f"Setting secondary credential on mount path {self.mount_path} was done successfully")

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
            sc_obj = self.mmhelper.configure_subclient(self.backupset_name, "%s_SC1" % str(self.id),
                                                       self.storage_policy_name, self.content_path, self.agent)

            job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full']

            for sequence_index in range(0, 4):
                # Create unique content
                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 10):
                        self.log.error("unable to Generate Data at %s", self.content_path)
                        raise Exception("unable to Generate Data at {0}".format(self.content_path))
                    self.log.info("Generated Data at %s", self.content_path)

                # Run a Backup and validate storage accelerator functionality with log parsing
                job_id = self.common_util.subclient_backup(sc_obj, job_types_sequence_list[sequence_index]).job_id

                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    self._validate_ma_override(job_id)
                    self._validate_sa_chunk_creation(job_id)

            # Run a Restore and validate storage accelerator functionality with log parsing
            restore_job = self.common_util.subclient_restore_out_of_place(self.restore_path, [self.content_path], 
                                                                          subclient=sc_obj)
            self._validate_ma_override(restore_job.job_id)
            self._validate_sa_chunk_open(restore_job.job_id)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
