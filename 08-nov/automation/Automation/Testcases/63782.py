# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case
TestCase to perform Data Server IP Backup and Restore with client as FQDN.
TestCase is the only class defined in this file.
TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class
    setup()                     --  setup function of this test case
    run()                       --  run function of this test case
    tear_down()                 --  teardown function of this test case
    _cleanup()                  --  function to remove resources created by automation TC.
    _restore_verify()           --  verify restored data.
    run_backup()                --  util to run backups.
    parse_ma_logs()             --  parse MA logs(3dnfs and NFSTransport logs)

Design:
    Configure a client whose nethostname is a FQDN. 
    Use this MA as 3dnfs server and run backup and restore via DSIP controller.

Sample Input:
    {
        "MediaAgentRegular": "MediaAgent1", ***(Please provide a MA whose NetHostName is FQDN(Fully Qualified Domain Name))
        "MediaAgentNetHostNameIP": "MediaAgent2",
        "ClientName": "ClientName"
    }
    
    Optional Input: 
        "ddb_path": "/ddb_path"
"""
from cvpysdk import storage
from AutomationUtils import (constants, commonutils)
from MediaAgents import mediaagentconstants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """
        Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "DSIP -- NetHostName is FQDN"
        self.media_agent_regular = None
        self.media_agent_ip = None
        self.disk_library_name = None
        self.storage_pool_name = None
        self.media_agent_regular_machine = None
        self.client_machine = None
        self.disk_mount_path_name = None
        self.disk_mount_path = None
        self.content_path = None
        self.restore_dest_path = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.ddb_path = None
        self.is_user_defined_dedup = None

        self.dedup_helper = None
        self.mm_helper = None
        self.dedup_helper = None
        self.options_selector = None
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
        self.media_agent_regular = self.tcinputs["MediaAgentRegular"]
        self.media_agent_ip = self.tcinputs["MediaAgentIP"]
        constant = mediaagentconstants.DEVICE_ACCESS_TYPES
        self.access_type = constant['DATASERVER_IP'] + constant['READWRITE']

        self.storage_policy_name = f'storage_policy_{self.id}_{self.media_agent_ip}'
        self.backupset_name = f'{self.id}_backupset'
        self.disk_library_name = f'disk_storage_{self.id}_{self.media_agent_regular}'
        self.storage_pool_name = self.disk_library_name
        # Client Machine
        self.client_machine = self.options_selector.get_machine_object(self.tcinputs['ClientName'])
        self.media_agent_regular_machine = Machine(
            machine_name=self.media_agent_regular,
            commcell_object=self.commcell
        )

        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = self.options_selector.get_drive(self.client_machine, size=20 * 1024)
        if client_drive is None:
            raise Exception(f"No free space on client machine: {self.tcinputs['ClientName']}!")
        self.log.info('Selecting drive in the regular MA machine based on space available')
        ma_regular_drive = self.options_selector.get_drive(self.media_agent_regular_machine, 1024 * 20)
        if ma_regular_drive is None:
            raise Exception(f"No free space on regular MA: {self.media_agent_regular}")

        # Cleanup
        self._cleanup()
        if self.tcinputs.get("ddb_path"):
            self.is_user_defined_dedup = True
        else:
            self.is_user_defined_dedup = False

        # Disk Mount Path
        self.disk_mount_path_name = f'DSIP_{self.id}'
        self.disk_mount_path = self.media_agent_regular_machine.join_path(
            ma_regular_drive, 'Automation', self.disk_mount_path_name)
        self.log.info("Created Mount")
        # Content Path
        self.content_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata'
        )
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)
        # Restore Path
        self.restore_dest_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Restoredata'
        )
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)
        self.client_machine.create_directory(self.restore_dest_path)
        # DDB Path
        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.tcinputs["ddb_path"]
        else:
            if "unix" in self.media_agent_regular_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_path = self.media_agent_regular_machine.join_path(
                ma_regular_drive, 'Automation',
                str(self.id), 'DDBPath'
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
            self.log.error("Checksum comparison failed")
            self.log.info("Diff output: \n%s", diff_output)
            raise Exception("Checksum comparison failed")

    def run_backup(self, subclient_obj, backup_type):
        """
        Run backup
        Args:
            backup_type (str) -- type of the backup operation
            subclient_obj (object) -- object of the subclient to take backup of
        Return:
            (object) -- object of the Job class
        """
        self.log.info(f"Starting {backup_type} backup")
        job = subclient_obj.backup(backup_type)
        self.log.info(f"Started {backup_type} backup with Job ID: {job.job_id}")
        if not job.wait_for_completion():
            raise Exception(
                f"Failed to run {backup_type} backup job with error: {job.delay_reason}"
            )
        self.log.info(f"Successfully finished {backup_type} backup job")
        return job

    def parse_ma_logs(self, mount_path):
        """
        Parse media agent logs
        Args:
            (str) -- shared mount path of the disk library
        Return:
            (bool) -- True, if the parsing and comparison is successful. False, otherwise
        """
        self.log.info(f"seaching for {mount_path}")
        nfst_final_list, matched_strings = self.dedup_helper.parse_log(
            client=self.media_agent_ip,
            log_file='NFSTransport.log',
            regex=f'exported successfully as .*{mount_path}',
            escape_regex=False
        )

        all_3dnfs_request, matched_strings = self.dedup_helper.parse_log(
            client=self.media_agent_regular,
            log_file='3dnfs.log',
            regex=f"Request to mount .*{mount_path}",
            escape_regex=False
        )

        # Get all successfull mount from 3dnfs
        all_3dnfs_success, matched_strings = self.dedup_helper.parse_log(
            client=self.media_agent_regular,
            log_file='3dnfs.log',
            regex=f'Successfully added mount point .*{mount_path}',
            escape_regex=False
        )

        # Compare successful mount to export requests.
        nfst_count = len(nfst_final_list)
        _3dnfs_request_count = len(all_3dnfs_request)
        _3dnfs_success_count = len(all_3dnfs_success)
        if nfst_count == 0 or _3dnfs_success_count == 0 or _3dnfs_request_count == 0:
            self.log.error("Parsing failed as there are no matching log lines...")
            return False
        if _3dnfs_request_count + _3dnfs_success_count == nfst_count * 2:
            self.log.info("Parsing and comparison is successful...")
            return True
        self.log.error("Parsing and comparison is not successful...")
        return False

    def run(self):
        """Run function of this test case"""
        try:
            # Configure storage pool and storage
            self.log.info(f"Creating Storage Pool {self.storage_pool_name}")
            self.commcell.storage_pools.add(
                self.storage_pool_name, self.disk_mount_path,
                self.media_agent_regular, self.media_agent_regular,
                self.ddb_path
            )

            # Sharing MP using Data Server IP Access Type (22).
            library_details = {
                "mountPath": self.disk_mount_path,
                "mediaAgentName": self.media_agent_regular
            }
            self.log.info(f"Sharing {self.disk_mount_path} MountPath with "
                          f"MediaAgentIP {self.media_agent_ip} through DSIP")

            storage.DiskLibrary(
                self.commcell,
                self.disk_library_name,
                library_details=library_details).share_mount_path(
                media_agent=self.media_agent_regular,
                library_name=self.disk_library_name,
                mount_path=self.disk_mount_path,
                new_media_agent=self.media_agent_ip,
                access_type=self.access_type,
                new_mount_path=self.disk_mount_path
            )
            self.log.info("Mount Path was Shared successfully!")

            # Configure storage policy
            self.log.info("Configuring Dependent Storage Policy ==> %s", self.storage_policy_name)
            if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
                sp_copy_obj = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                 library=self.disk_library_name,
                                                                 media_agent=self.media_agent_ip,
                                                                 global_policy_name=self.storage_pool_name,
                                                                 dedup_media_agent="",
                                                                 dedup_path="")
            else:
                sp_copy_obj = self.commcell.storage_policies.get(self.storage_policy_name)
            self.log.info("Dependent Storage Policy Created Successfully!!")

            # Update Default Data path on storage policy Copy
            copy_obj = sp_copy_obj.get_copy("Primary")

            # set default data path on storage policy copy
            self.log.info(f" set default datapath on MA: {self.media_agent_ip} to force backups via DSIP")
            copy_obj.set_default_datapath(self.disk_library_name, self.media_agent_ip)

            # Delete
            self.log.info(f"Deleting datapath on MA: {self.media_agent_regular} to force backups via DSIP")
            copy_obj.delete_datapath(self.disk_library_name, self.media_agent_regular)

            # Create BackupSet
            self.mm_helper.configure_backupset(self.backupset_name, self.agent)

            # Create SubClient
            subclient_name = "%s_SubClient" % str(self.id)
            subclient_obj = self.mm_helper.configure_subclient(self.backupset_name, subclient_name,
                                                               self.storage_policy_name, self.content_path, self.agent)

            # Run Backups
            job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full', 'incremental',
                                       'synthetic_full']

            for job_type in job_types_sequence_list:
                # Create unique content
                if job_type != 'synthetic_full':
                    if not self.mm_helper.create_uncompressable_data(self.client_machine, self.content_path, 0.5, 3):
                        self.log.error("unable to Generate Data at %s", self.content_path)
                        raise Exception("unable to Generate Data at {0}".format(self.content_path))
                    self.log.info("Generated Data at %s", self.content_path)

                # Perform Backup
                self.run_backup(subclient_obj, job_type)

            # Restore from primary copy via DSIP.
            restore_job = subclient_obj.restore_out_of_place(
                client=self.client,
                destination_path=self.restore_dest_path,
                paths=[self.content_path],
                fs_options={
                    "media_agent": self.media_agent_ip
                })
            self.log.info("restore job [%s] has started from primary copy.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info("restore job [%s] has completed.", restore_job.job_id)

            # Verify restored data
            if self.client_machine.os_info.lower()== 'unix':
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '/')
            else:
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '\\')

            dest_path = self.client_machine.join_path(dest_path, 'Testdata')

            self._restore_verify(self.client_machine, self.content_path, dest_path)

            # Get Mount Path
            self.commcell.disk_libraries.refresh()
            if self.commcell.disk_libraries.has_library(self.disk_library_name):
                library_obj = self.commcell.disk_libraries.get(self.disk_library_name)
            else:
                raise Exception(f"Could not found the disk library: {self.disk_library_name}")
            library_id = library_obj.library_id
            mount_path_name = self.mm_helper.get_mount_path_name(library_id)[0]

            if not self.parse_ma_logs(mount_path_name):
                raise Exception("Error while validating 3dnfs and NFSTransport logs")
            else:
                self.log.info("Successfully Validated 3dnfs and NFSTransport log on MAs")
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

        # Delete Storage pool
        self.log.info("Deleting Storage Pool: %s if exists", self.storage_pool_name)
        if self.commcell.storage_policies.has_policy(self.storage_pool_name):
            self.commcell.storage_policies.delete(self.storage_pool_name)
            self.log.info("Deleted Storage Policy: %s", self.storage_pool_name)

        # Deleting Library
        self.log.info("Deleting library: %s if exists", self.disk_library_name)
        if self.commcell.disk_libraries.has_library(self.disk_library_name):
            self.commcell.disk_libraries.delete(self.disk_library_name)
            self.log.info("Deleted library: %s", self.disk_library_name)
