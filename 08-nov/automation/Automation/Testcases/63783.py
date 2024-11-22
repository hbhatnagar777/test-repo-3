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
    _restore_verify             --  perform verification after restore.
    get_source_media_agent_id_of_aux_copy_job   -- returns the media agent of source aux copy MA.

Design Steps:
1. Create a primary storage pool on disk and write backups to this primary copy using regular MA.
2. Configure a secondary storage pool where the library is configured with two mountpaths which should
    be carved out of the same disk but each mount path should be a new simple volume.
3. Add a data server IP MA with r/w access
4. Set 3dnfs.log and NFSTrasnport.log on debug 3 and file versions to 50
5. Run multiple streams dedupe aux copy job writing using DSIP MA. Idea is to have more open and close at the same time across volumes.
6. Collect the FileID using fsutil command and check for duplicate fileID's
7. For the chunks returning duplicate fileID's
8. Run DV and see if we can validate via data server IP MA or not.
9. If DV fails, run validate chunk and verify the chunk is valid or not
10. If validate chunk returns valid, that means it is the read corruption issue.
11. Else write corruption via DS-IP
12. Else it is all good.
13. Restore the data using IP MA, from a secondary copy.

Sample Input:
    {
        "MediaAgentRegular": "MediaAgent1",
        "MediaAgentIP": "MediaAgent2",
        "ClientName": "ClientName",
        "mount_path1": "MountPath1",
        "mount_path2": "MountPath2",
        "ddb_path" : "DDB Path" ** on Media Agent IP.
    }
    ****Note - Please make sure that both mounts should be carved out of the same disk but each mount path should be a New Simple Volume
"""
from cvpysdk import deduplication_engines
from AutomationUtils import (constants, commonutils)
from MediaAgents import mediaagentconstants
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """
        Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "DSIP -- Test 3dfs fd cache via DSIP writes and read"
        self.media_agent_regular = None
        self.media_agent_ip = None
        self.disk_library_name = None
        self.media_agent_ip_machine_obj = None
        self.client_machine = None
        self.disk_mount_path = None
        self.base_path = None
        self.content_path = None
        self.restore_dest_path = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.ddb_path = None
        self.is_user_defined_dedup = None
        self.ma_regular_machine_obj = None
        self.job_id_list = None

        self.custom_mount_path1 = None
        self.custom_mount_path2 = None
        self.ma_ip_id = None

        self.dedup_helper = None
        self.mm_helper = None
        self.dedup_helper = None
        self.options_selector = None
        self.common_utils = None
        self.access_type = None

        self.tcinputs = {
            "MediaAgentRegular": None,
            "MediaAgentIP": None,
            "ClientName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.options_selector = OptionsSelector(self.commcell)
        self.common_utils = CommonUtils(self.commcell)
        self.media_agent_regular = self.tcinputs["MediaAgentRegular"]
        self.media_agent_ip = self.tcinputs["MediaAgentIP"]
        self.custom_mount_path1 = self.tcinputs["mount_path1"]
        self.custom_mount_path2 = self.tcinputs["mount_path2"]
        constant = mediaagentconstants.DEVICE_ACCESS_TYPES
        self.access_type = constant['DATASERVER_IP'] + constant['READWRITE']

        self.storage_policy_name = 'storage_policy_%s' % str(self.id)
        self.backupset_name = '%s_backupset' % str(self.id)
        self.primary_library_name = 'primary_disk_storage_%s' % str(self.id)
        self.secondary_library_name = 'secondary_disk_storage_%s' % str(self.id)
        self.job_id_list = []

        ma_ip_obj = self.commcell.media_agents.get(self.media_agent_ip)
        self.ma_ip_id = ma_ip_obj.media_agent_id
        self.log.info(f"IP of MediaAgentIP : {self.ma_ip_id}")

        # Regular MA Machine object
        self.ma_regular_machine_obj = self.options_selector.get_machine_object(self.media_agent_regular)

        # Client Machine
        self.client_machine = self.options_selector.get_machine_object(self.tcinputs['ClientName'])

        self.media_agent_ip_machine_obj = self.options_selector.get_machine_object(self.media_agent_ip)

        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = self.options_selector.get_drive(self.client_machine, size=10 * 1024)
        if client_drive is None:
            raise Exception("No free space on client machine...")
        self.log.info('Selecting drive in the IP MediaAgent machine based on space available')
        ma_ip_drive = self.options_selector.get_drive(self.media_agent_ip_machine_obj, 1024 * 10)
        if ma_ip_drive is None:
            raise Exception("No free space on IP MediaAgent...")
        self.log.info('Selecting drive in the regular MA machine based on space available')
        ma_regular_drive = self.options_selector.get_drive(self.ma_regular_machine_obj, 1024 * 10)
        if ma_regular_drive is None:
            raise Exception("No free space on IP MediaAgent...")

        # Content path -
        self.base_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id)
        )
        self.content_path = self.client_machine.join_path(
            self.base_path, 'Testdata'
        )
        # Restore Path -
        self.restore_dest_path = self.client_machine.join_path(
            self.base_path, 'Restoredata'
        )

        # Cleanup
        self._cleanup()
        if self.tcinputs.get("primary_ddb_path"):
            self.is_user_defined_primary_dedup = True
        else:
            self.is_user_defined_primary_dedup = False

        if self.tcinputs.get("secondary_ddb_path"):
            self.is_user_defined_secondary_dedup = True
        else:
            self.is_user_defined_secondary_dedup = False

        # Disk Mount Path
        self.disk_mount_path_name = 'DSIP_%s' % str(self.id)
        self.disk_mount_path = self.media_agent_ip_machine_obj.join_path(
            ma_ip_drive, 'Automation', self.disk_mount_path_name)
        self.log.info("Created Mount")

        # Primary DDB Path
        if self.is_user_defined_primary_dedup:
            self.log.info("custom dedup path supplied for primary copy")
            self.primary_ddb_path = self.tcinputs["primary_ddb_path"]
        else:
            if "unix" in self.media_agent_ip_machine_obj.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.primary_ddb_path = self.media_agent_ip_machine_obj.join_path(
                ma_ip_drive, 'Automation',
                str(self.id), 'DDBPathPrimary'
            )

        # Secondary DDB Path.
        if self.is_user_defined_secondary_dedup:
            self.log.info("custom dedup path supplied for secondary copy")
            self.secondary_ddb_path = self.tcinputs["secondary_ddb_path"]
        else:
            if "unix" in self.ma_regular_machine_obj.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.secondary_ddb_path = self.ma_regular_machine_obj.join_path(
                ma_regular_drive, 'Automation',
                str(self.id), 'DDBPathSecondary'
            )

    def _restore_verify(self, machine, src_path, dest_path):
        """
            Performs the verification after restore

            Args:
                machine          (object)    --  Machine class object.

                src_path         (str)       --  path on source machine that is to be compared.

                dest_path        (str)       --  path on destination machine that is to be compared.

            Raises:
                Exception - Any difference from source data to destination data

        """
        self.log.info("Comparing source:%s destination:%s", src_path, dest_path)
        diff_output = machine.compare_folders(machine, src_path, dest_path)

        if not diff_output:
            self.log.info("Checksum comparison successful")
        else:
            raise Exception("Checksum comparison failed")

    def run(self):
        """Run function of this test case"""
        try:
            # Create a disk Library DL1
            primary_library_obj = self.mm_helper.configure_disk_library(
                library_name=self.primary_library_name,
                ma_name=self.media_agent_ip,
                mount_path=self.disk_mount_path
            )
            # Create a secondary disk library DL2 with 2 mount paths
            secondary_library_obj = self.mm_helper.configure_disk_library(
                library_name=self.secondary_library_name,
                ma_name=self.media_agent_regular,
                mount_path=self.custom_mount_path1
            )

            # Add another mount path on secondary library
            self.mm_helper.configure_disk_mount_path(
                secondary_library_obj, self.custom_mount_path2, self.media_agent_regular)

            # Configure storage policy using Disk Library DL1
            self.storage_policy_obj = self.dedup_helper.configure_dedupe_storage_policy(
                self.storage_policy_name, primary_library_obj,
                self.media_agent_ip,
                self.primary_ddb_path
            )
            # Add secondary Copy
            secondary_copy_name = 'secondary_copy'
            self.dedup_helper.configure_dedupe_secondary_copy(
                self.storage_policy_obj,
                secondary_copy_name,
                self.secondary_library_name,
                self.media_agent_regular,
                self.secondary_ddb_path,
                self.media_agent_regular
            )
            # Removing auto copy schedule association
            self.mm_helper.remove_autocopy_schedule(
                storage_policy_name=self.storage_policy_name,
                copy_name=secondary_copy_name)

            # Create BackupSet
            self.mm_helper.configure_backupset(self.backupset_name, self.agent)

            # Create SubClient
            subclient_name = "%s_SubClient" % str(self.id)
            subclient_obj = self.mm_helper.configure_subclient(self.backupset_name, subclient_name,
                                                               self.storage_policy_name, self.content_path, self.agent)

            # Run Backups using regular media agent on primary copy
            job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full', 'incremental',
                                       'synthetic_full']
            for job_type in job_types_sequence_list:
                # Create unique content
                if job_type != 'synthetic_full':
                    if not self.mm_helper.create_uncompressable_data(self.client_machine, self.content_path, 1, 2):
                        self.log.error("unable to Generate Data at %s", self.content_path)
                        raise Exception("unable to Generate Data at {0}".format(self.content_path))
                    self.log.info("Generated Data at %s", self.content_path)

                # Perform Backup
                job = self.common_utils.subclient_backup(subclient_obj, job_type)
                self.job_id_list.append(job.job_id)

            # Sharing Custom Mount Path 1 with MediaAgentIP
            self.log.info(f"Sharing {self.custom_mount_path1} MountPath on library {self.secondary_library_name} with"
                          f"MediaAgentIP {self.media_agent_ip} through DSIP")

            secondary_library_obj.share_mount_path(
                media_agent=self.media_agent_regular,
                library_name=self.secondary_library_name,
                mount_path=self.custom_mount_path1,
                new_media_agent=self.media_agent_ip,
                access_type=self.access_type,
                new_mount_path=self.custom_mount_path1
            )
            self.log.info(f"Mount Path {self.custom_mount_path1} on library: {self.secondary_library_name}"
                          f"was Shared successfully with {self.media_agent_ip}")

            # Sharing Custom Mount Path 2 with MediaAgentIP
            self.log.info(f"Sharing {self.custom_mount_path2} MountPath with"
                          f"MediaAgentIP {self.media_agent_ip} through DSIP")

            secondary_library_obj.share_mount_path(
                media_agent=self.media_agent_regular,
                library_name=self.secondary_library_name,
                mount_path=self.custom_mount_path2,
                new_media_agent=self.media_agent_ip,
                access_type=self.access_type,
                new_mount_path=self.custom_mount_path2
            )
            self.log.info(f"Mount Path {self.custom_mount_path2} was Shared successfully!")

            # Perform AuxCopy using MA IP.
            aux_copy_obj = self.storage_policy_obj.run_aux_copy(secondary_copy_name)
            if not aux_copy_obj.wait_for_completion():
                raise Exception("Failed to run aux copy job with error: {0}".format(
                    aux_copy_obj.delay_reason))
            self.log.info("Successfully finished aux copy job.")
            source_ma_id_list = self.mm_helper.get_source_ma_id_for_auxcopy(int(aux_copy_obj.job_id))
            if len(source_ma_id_list) > 1:
                raise Exception(f"More than 1 source media agent used in aux copy job: {aux_copy_obj.job_id}, Media Agents: {source_ma_id_list}")
            source_ma_id = source_ma_id_list[0]

            self.log.info(f"Source media agent id used for aux copy job: {source_ma_id}")
            self.log.info(f"Destination media agent id used for aux copy job: {self.ma_ip_id}")
            if str(source_ma_id) == str(self.ma_ip_id):
                self.log.info(
                    "Source media agent and the destination media agent is the IP Media Agent.")
            else:
                raise Exception("Source media agent or the destination media agent is not the IP Media Agent.")

            # Get Chunks written by the job:
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)
                self.log.info("Got the updated Storage policy object")
            else:
                raise Exception(f"{self.storage_policy_name} does not exsists")
            secondary_copy_id = storage_policy.get_copy(secondary_copy_name).copy_id
            self.log.info(f"Secondary Copy ID: {secondary_copy_id}")
            chunks_on_sec_cpy = {}
            for job_id in self.job_id_list:
                self.log.info(f"Getting Chunks for job: {job_id}")
                chunk_list = self.mm_helper.get_chunks_for_job(
                    job_id=job_id,
                    copy_id=secondary_copy_id
                )
                self.log.info(f"CHUNKS WRITTEN BY JOB: {chunk_list}")
                for obj in chunk_list:
                    if obj[-1] not in chunks_on_sec_cpy:
                        chunks_on_sec_cpy[obj[-1]] = obj

            self.log.info(f"CHUNK LISTS: {chunks_on_sec_cpy}")

            # Process the chunks paths recieved.
            chunk_paths = []
            for chunk in chunks_on_sec_cpy.values():
                chunk[-1] = f"CHUNK_{chunk[-1]}"
                path = "\\".join(chunk[:2]) + '\\CV_MAGNETIC' + "\\" + "\\".join(chunk[2:])
                self.log.info(f"CHUNK PATH: {path}")
                chunk_paths.append(path)

            # Get file id using fsutil from machine.
            found_duplicate_fids = False
            fsutil_fid_store = {}
            for path in chunk_paths:
                command = 'fsutil file queryfileid "%s"' % path
                self.log.info(f"Executing Command: {command}")
                output = self.ma_regular_machine_obj.execute_command(command).formatted_output
                self.log.info(f"fs File ID: {output} for {path}")
                if output not in fsutil_fid_store:
                    fsutil_fid_store[output] = path
                else:
                    self.log.error(f"Found duplicate file Id: {output} for {fsutil_fid_store[output]} and {path}")
                    found_duplicate_fids = True

            if found_duplicate_fids:
                # Get DDB Store
                store_obj = None
                dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
                if dedup_engines_obj.has_engine(self.storage_policy_name, secondary_copy_name):
                    dedup_engine_obj = dedup_engines_obj.get(self.storage_policy_name, secondary_copy_name)
                    dedup_stores_list = dedup_engine_obj.all_stores
                    for dedup_store in dedup_stores_list:
                        store_obj = dedup_engine_obj.get(dedup_store[0])
                if not store_obj:
                    raise Exception(f"Failed to get store object for {self.storage_policy_name} {secondary_copy_name}")

                # Run Data Verification
                self.log.info(f"Running DDB Verification on {store_obj.store_id}")
                store_obj.refresh()
                job = store_obj.run_ddb_verification(incremental_verification=False, quick_verification=False,
                                                          use_scalable_resource=True)
                self.log.info("DV2 job: %s", job.job_id)

                if not job.wait_for_completion():
                    self.log.error("***DDB Verification Job failed, please check for read/write corruption***")
                    raise Exception(
                        "DDB Job {0} Failed with {1}".format(
                            job.job_id, job.delay_reason))
                self.log.info("DDB job %s complete", job.job_id)

            else:
                # Restore from primary copy via DSIP.
                restore_job = self.common_utils.subclient_restore_out_of_place(
                    subclient=subclient_obj,
                    destination_path=self.restore_dest_path,
                    paths=[self.content_path],
                    client=self.client,
                    copy_precedence=2,
                    fs_options={
                        "media_agent": self.media_agent_ip
                    }
                )
                self.log.info("restore job [%s] has completed.", restore_job.job_id)

                # Verify restored data
                if self.client_machine.os_info == 'UNIX':
                    dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '/')
                else:
                    dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '\\')

                dest_path = self.client_machine.join_path(dest_path, 'Testdata')

                self._restore_verify(self.client_machine, self.content_path, dest_path)
                self.result_string = "NO Duplicate File ID Found"

        except Exception as excp:
            self.log.error('Exception raised while executing testcase: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        try:
            if self.status != constants.FAILED:
                self.log.info("Testcase shows successful execution, cleaning up the test environment ...")

            else:
                self.log.warning("Testcase shows failure in execution, not cleaning up the test environment ...")
            self._cleanup()
        except Exception as exp:
            self.log.info("Cleanup failed even after successful execution - %s", str(exp))

    def _cleanup(self):
        """Cleanup function"""
        self.log.info("****************************** CLEAN UP STARTED *********************************")

        # Delete Content Path
        self.log.info(f"Deleting content path: {self.content_path} if exists!")
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)

        # Delete Restore Path
        self.log.info(f"Deleting restore path: {self.restore_dest_path} if exists!")
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)

        # Delete Base Folder
        self.log.info(f"Deleting restore path: {self.base_path} if exists!")
        if self.client_machine.check_directory_exists(self.base_path):
            self.client_machine.remove_directory(self.base_path)

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

        # Deleting Library
        self.log.info("Deleting library: %s if exists", self.primary_library_name)
        if self.commcell.disk_libraries.has_library(self.primary_library_name):
            self.commcell.disk_libraries.delete(self.primary_library_name)
            self.log.info("Deleted library: %s", self.primary_library_name)

        # Deleting Secondary Library
        self.log.info("Deleting library: %s if exists", self.secondary_library_name)
        if self.commcell.disk_libraries.has_library(self.secondary_library_name):
            self.commcell.disk_libraries.delete(self.secondary_library_name)
            self.log.info("Deleted library: %s", self.secondary_library_name)
        self.log.info("****************************** CLEAN UP COMPLETE *********************************")
