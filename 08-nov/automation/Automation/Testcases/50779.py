# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase to perform Basic AmazonS3 Cloud verification via Access and Secret Access key.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _cleanup()                  --  Cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "AmazonS3 Cloud verification via Access and Secret Access key"
        self.tcinputs = {
            "ClientName": None,
            "MediaAgentName": None,
            "CloudMountPath": None,
            "CloudUserName": None,
            "CloudPassword": None,
            "CloudServerType": None
        }
        self.disk_pool_name = None
        self.cloud_dedupe_pool_name = None
        self.cloud_nondedupe_pool_name = None
        self.cloud_sec_pool_name = None
        self.storage_policy_dedupe_name = None
        self.storage_policy_nondedupe_name = None
        self.backupset_name = None
        self.client_machine = None
        self.ma_machine = None
        self.mountpath1 = None
        self.mountpath2 = None
        self.partition_path = None
        self.copy_partition_path = None
        self.partition2_path = None
        self.copy_partition2_path = None
        self.content_path1 = None
        self.content_path2 = None
        self.restore_dest_path = None
        self.common_util = None
        self.mmhelper = None

    def _cleanup(self):
        """Cleanup the entities created"""
        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            if self.client_machine.check_directory_exists(self.content_path1):
                self.log.info("Deleting content path: %s", self.content_path1)
                self.client_machine.remove_directory(self.content_path1)
            if self.client_machine.check_directory_exists(self.content_path2):
                self.log.info("Deleting content path: %s", self.content_path2)
                self.client_machine.remove_directory(self.content_path2)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.log.info("Deleting restore path: %s", self.restore_dest_path)
                self.client_machine.remove_directory(self.restore_dest_path)

            # Delete backupset
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)
            # Delete Storage Policies
            self.log.info("Deleting Dedupe storage policy: %s if exists", self.storage_policy_dedupe_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_dedupe_name):
                self.commcell.storage_policies.delete(self.storage_policy_dedupe_name)
                self.log.info("Deleted Dedupe storage policy: %s", self.storage_policy_dedupe_name)

            self.log.info("Deleting second Dedupe storage policy: %s if exists", self.storage_policy_nondedupe_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_nondedupe_name):
                self.commcell.storage_policies.delete(self.storage_policy_nondedupe_name)
                self.log.info("Deleted second Dedupe storage policy: %s", self.storage_policy_nondedupe_name)

            # Delete Storage Pools
            self.log.info("Deleting Disk Storage Pool: %s if exists", self.disk_pool_name)
            if self.commcell.storage_pools.has_storage_pool(self.disk_pool_name):
                self.commcell.storage_pools.delete(self.disk_pool_name)
                self.log.info("Deleted Disk Storage Pool: %s", self.disk_pool_name)

            self.log.info("Deleting Cloud Dedupe Storage Pool: %s if exists", self.cloud_dedupe_pool_name)
            if self.commcell.storage_pools.has_storage_pool(self.cloud_dedupe_pool_name):
                self.commcell.storage_pools.delete(self.cloud_dedupe_pool_name)
                self.log.info("Deleted Cloud Dedupe Storage Pool: %s", self.cloud_dedupe_pool_name)

            self.log.info("Deleting Cloud Non-Dedupe Storage Pool: %s if exists", self.cloud_nondedupe_pool_name)
            if self.commcell.storage_pools.has_storage_pool(self.cloud_nondedupe_pool_name):
                self.commcell.storage_pools.delete(self.cloud_nondedupe_pool_name)
                self.log.info("Deleted Cloud Non-Dedupe Storage Pool: %s", self.cloud_nondedupe_pool_name)

            self.log.info("Deleting Cloud Non-Dedupe Secondary Storage Pool: %s if exists", self.cloud_sec_pool_name)
            if self.commcell.storage_pools.has_storage_pool(self.cloud_sec_pool_name):
                self.commcell.storage_pools.delete(self.cloud_sec_pool_name)
                self.log.info("Deleted Cloud Non-Dedupe Secondary Storage Pool: %s", self.cloud_sec_pool_name)
        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        self.disk_pool_name = '%s_disk-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                             self.tcinputs['ClientName'])
        self.cloud_dedupe_pool_name = '%s_s3_dedupe-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                          self.tcinputs['ClientName'])
        self.cloud_nondedupe_pool_name = '%s_s3_nondedupe-ma(%s)-client(%s)' % (str(self.id),
                                                                                self.tcinputs['MediaAgentName'],
                                                                                self.tcinputs['ClientName'])
        self.cloud_sec_pool_name = '%s_s3_sec-ma(%s)-client(%s)' % (str(self.id),
                                                                    self.tcinputs['MediaAgentName'],
                                                                    self.tcinputs['ClientName'])
        self.storage_policy_dedupe_name = '%s_dedupe-ma(%s)-client(%s)' % (str(self.id),
                                                                           self.tcinputs['MediaAgentName'],
                                                                           self.tcinputs['ClientName'])
        self.storage_policy_nondedupe_name = '%s_nondedupe-ma(%s)-client(%s)' % (str(self.id),
                                                                                 self.tcinputs['MediaAgentName'],
                                                                                 self.tcinputs['ClientName'])
        self.backupset_name = '%s_bs-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                           self.tcinputs['ClientName'])

        options_selector = OptionsSelector(self.commcell)
        self.client_machine = options_selector.get_machine_object(self.client)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])

        # To select drive with space available in Media agent machine
        self.log.info('Selecting drive in the Media agent machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=25 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb on media agent machine.")
        self.log.info('selected drive: %s', ma_drive)

        # mount path
        self.mountpath1 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP1')
        self.mountpath2 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP2')

        # DDB partition path
        if self.tcinputs.get("PartitionPath"):
            self.partition_path = self.ma_machine.join_path(self.tcinputs['PartitionPath'], 'DDB')
            self.copy_partition_path = self.ma_machine.join_path(self.tcinputs['PartitionPath'], 'Copy_DDB')
        else:
            if self.ma_machine.os_info.lower() == 'unix':
                self.log.error("LVM enabled DDB partition path must be an input for the unix MA.")
                raise Exception("LVM enabled partition path not supplied for Unix MA!..")
            self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')
            self.copy_partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'Copy_DDB')

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=5 * 1024)
        if client_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', client_drive)

        # content path
        self.content_path1 = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata1')
        self.content_path2 = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata2')
        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'RestoreData')

        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)

        self._cleanup()

    def run(self):
        """Run function of this test case"""
        try:

            # Creating cloud dedupe storage pool
            cloud_dedupe_pool_obj, cloud_dedupe_lib_obj = self.mmhelper.configure_storage_pool(
                self.cloud_dedupe_pool_name,
                self.tcinputs["CloudMountPath"],
                self.tcinputs["MediaAgentName"],
                self.tcinputs["MediaAgentName"],
                self.partition_path,
                username=self.tcinputs["CloudUserName"],
                password=self.tcinputs["CloudPassword"],
                cloud_vendor_name=self.tcinputs["CloudServerType"])

            self.mmhelper.configure_cloud_mount_path(cloud_dedupe_lib_obj, self.tcinputs["CloudMountPath"],
                                                     self.tcinputs['MediaAgentName'], self.tcinputs["CloudUserName"],
                                                     self.tcinputs["CloudPassword"], self.tcinputs["CloudServerType"])

            # disk storage pool creation
            disk_pool_obj, disk_lib_obj = self.mmhelper.configure_storage_pool(self.disk_pool_name, self.mountpath1,
                                                                               self.tcinputs['MediaAgentName'],
                                                                               self.tcinputs['MediaAgentName'],
                                                                               self.copy_partition_path)
            self.mmhelper.configure_disk_mount_path(disk_lib_obj, self.mountpath2, self.tcinputs['MediaAgentName'])

            # Creating cloud non-dedupe storage pool
            cloud_nondedupe_pool_obj, cloud_nondedupe_lib_obj = self.mmhelper.configure_storage_pool(
                self.cloud_nondedupe_pool_name,
                self.tcinputs["CloudMountPath"],
                self.tcinputs["MediaAgentName"],
                username=self.tcinputs["CloudUserName"],
                password=self.tcinputs["CloudPassword"],
                cloud_vendor_name=self.tcinputs["CloudServerType"])

            self.mmhelper.configure_cloud_mount_path(cloud_nondedupe_lib_obj, self.tcinputs["CloudMountPath"],
                                                     self.tcinputs['MediaAgentName'], self.tcinputs["CloudUserName"],
                                                     self.tcinputs["CloudPassword"], self.tcinputs["CloudServerType"])

            # Creating cloud non-dedupe secondary storage pool
            cloud_sec_pool_obj, cloud_sec_lib_obj = self.mmhelper.configure_storage_pool(
                self.cloud_sec_pool_name,
                self.tcinputs["CloudMountPath"],
                self.tcinputs["MediaAgentName"],
                username=self.tcinputs["CloudUserName"],
                password=self.tcinputs["CloudPassword"],
                cloud_vendor_name=self.tcinputs["CloudServerType"])

            self.mmhelper.configure_cloud_mount_path(cloud_sec_lib_obj, self.tcinputs["CloudMountPath"],
                                                     self.tcinputs['MediaAgentName'], self.tcinputs["CloudUserName"],
                                                     self.tcinputs["CloudPassword"], self.tcinputs["CloudServerType"])

            # Creating dependent dedupe storage policy associated to the pool
            sp_dedup_obj = self.mmhelper.configure_storage_policy(self.storage_policy_dedupe_name,
                                                                  storage_pool_name=self.cloud_dedupe_pool_name)

            # create secondary copy to copy from cloud to disk.
            copy1_name = '%s_copy1' % str(self.id)
            self.mmhelper.configure_secondary_copy(copy1_name, self.storage_policy_dedupe_name,
                                                   global_policy_name=self.disk_pool_name)
            # Removing association with System Created Automatic Auxcopy schedule
            self.log.info("Removing association with System Created Autocopy schedule on above created copy")
            self.mmhelper.remove_autocopy_schedule(self.storage_policy_dedupe_name, copy1_name)

            # create backupset
            self.mmhelper.configure_backupset(self.backupset_name, self.agent)
            # create subclient
            subclient1_name = "%s_SC1" % str(self.id)
            sc1_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient1_name,
                                                        self.storage_policy_dedupe_name, self.content_path1, self.agent)

            job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full', 'incremental',
                                       'synthetic_full']
            for sequence_index in range(0, 6):
                # Create unique content
                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    self.log.info("Generating Data at %s", self.content_path1)
                    if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path1, 0.1, 10):
                        self.log.error("unable to Generate Data at %s", self.content_path1)
                        raise Exception("unable to Generate Data at {0}".format(self.content_path1))
                    self.log.info("Generated Data at %s", self.content_path1)

                # Perform Backup
                self.common_util.subclient_backup(sc1_obj, job_types_sequence_list[sequence_index])

            # Restore from cloud
            self.log.info("Restoring data from dedupe cloud primary copy")
            self.common_util.subclient_restore_out_of_place(self.restore_dest_path, [self.content_path1],
                                                            subclient=sc1_obj, copy_precedence=1)
            self.log.info("Restore data from dedupe cloud primary copy has completed")

            # Run Aux copy Job
            auxcopy_job = sp_dedup_obj.run_aux_copy()
            self.log.info("Auxcopy job to disk [%s] has started.", auxcopy_job.job_id)
            self.mmhelper.wait_for_job_completion(auxcopy_job)
            self.log.info("Auxcopy job to disk [%s] has completed.", auxcopy_job.job_id)

            # Restore from disk
            self.log.info("Restoring data from disk copy auxcopied from cloud copy")
            self.common_util.subclient_restore_out_of_place(self.restore_dest_path, [self.content_path1],
                                                            subclient=sc1_obj, copy_precedence=2)
            self.log.info("Restore data from disk copy auxcopied from cloud copy has completed")

            # create Non-Dedupe storage policy
            sp_nondedup_obj = self.mmhelper.configure_storage_policy(self.storage_policy_nondedupe_name,
                                                                     storage_pool_name=self.cloud_nondedupe_pool_name)

            # Creating Secondary Copy
            copy2_name = '%s_copy2' % str(self.id)
            self.mmhelper.configure_secondary_copy(copy2_name, self.storage_policy_nondedupe_name,
                                                   global_policy_name=self.cloud_sec_pool_name)

            # Removing association with System Created Autocopy schedule
            self.mmhelper.remove_autocopy_schedule(self.storage_policy_nondedupe_name, copy2_name)

            # create subclient
            subclient2_name = "%s_SC2" % str(self.id)
            sc2_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient2_name,
                                                        self.storage_policy_nondedupe_name, self.content_path2,
                                                        self.agent)

            for sequence_index in range(0, 6):
                # Create unique content
                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    # Create unique content
                    self.log.info("Generated Data at %s", self.content_path2)
                    if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path2, 0.1, 10):
                        self.log.error("unable to Generate Data at %s", self.content_path2)
                        raise Exception("unable to Generate Data at {0}".format(self.content_path2))
                    self.log.info("Generated Data at %s", self.content_path2)

                # Perform Backup
                self.common_util.subclient_backup(sc2_obj, job_types_sequence_list[sequence_index])

            # Run Aux copy Job
            auxcopy_job = sp_nondedup_obj.run_aux_copy()
            self.log.info("Auxcopy job [%s] has started.", auxcopy_job.job_id)
            self.mmhelper.wait_for_job_completion(auxcopy_job)
            self.log.info("Auxcopy job [%s] has completed.", auxcopy_job.job_id)

            # Restore J6 from non-dedupe cloud copy
            self.log.info("Restoring data from non-dedupe cloud copy")
            self.common_util.subclient_restore_out_of_place(self.restore_dest_path, [self.content_path2],
                                                            subclient=sc2_obj, copy_precedence=2)
            self.log.info("Restore data from non-dedupe cloud copy has completed")
        except Exception as exp:
            self.log.error('Failed to execute test case with error:%s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""
        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment."
                "Please check for failure reason and manually clean up the environment..."
            )
            if self.client_machine.check_directory_exists(self.content_path1):
                self.log.info("Deleting content path: %s", self.content_path1)
                self.client_machine.remove_directory(self.content_path1)
            if self.client_machine.check_directory_exists(self.content_path2):
                self.log.info("Deleting content path: %s", self.content_path2)
                self.client_machine.remove_directory(self.content_path2)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.log.info("Deleting restore path: %s", self.restore_dest_path)
                self.client_machine.remove_directory(self.restore_dest_path)
