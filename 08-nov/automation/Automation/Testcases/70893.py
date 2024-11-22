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
    __init__()                  --  initialize TestCase class

    _cleanup()                  --  Cleanup the entities created

    _vsa_helper_init()          --  Initialize the VSA Helper objects

    _vsa_vm_delete()            --  Delete the VM from the VSA Hypervisor

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Design steps:
1. Create a cloud dedupe storage pool using Amazon S3 glacier as the storage class using MediaAgent (MA).
2. Configure a policy-copy associated with the pool created in step 1.
3. Configure a backupset and a sub-client on the VSA client and associate it with the policy configured in step 2.
4. Run a backup job.
5. Initiate a restore job.
6. The restore job should start a cloud archive recall workflow job.
7. Once recall workflow job finishes after recalling all files, the restore job should resume and complete.

Sample Input:
        "70893":{
            "AgentName": "Virtual Server",
            "ClientName": "Client_1",
            "MediaAgentName": "MediaAgent_1",
            "CloudMountPath": "Amazon Archive",
            "CloudUserName": "Amazon UserName",
            "SavedCredential": "Amazon Saved Credential",
            "CloudServerType": "Amazon S3"
        }
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import (DedupeHelper, MMHelper)
from VirtualServer.VSAUtils import VirtualServerHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "Cloud Archive Recall using Amazon S3 Storage - VSA Workload"
        self.tcinputs = {
            "ClientName": None,
            "MediaAgentName": None,
            "CloudMountPath": None,
            "CloudUserName": None,
            "SavedCredential": None,
            "CloudServerType": None
        }
        self.pool_name = None
        self.policy_name = None
        self.backupset_name = None
        self.client_machine = None
        self.ma_machine = None
        self.partition_path = None
        self.content_path = None
        self.restore_dest_path = None
        self.common_util = None
        self.dedupehelper = None
        self.mmhelper = None
        self.vsa_restore_vm_name = None
        self.vsa_content_vm_name = None

    def _vsa_helper_init(self):
        """Initialize the VSA Helper objects"""

        vsa_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
        vsa_client = VirtualServerHelper.AutoVSAVSClient(vsa_commcell, self.client)
        vsa_instance = VirtualServerHelper.AutoVSAVSInstance(vsa_client, self.agent, self.instance)
        self.vsa_hv_obj = vsa_instance.hvobj

    def _vsa_vm_delete(self, vm_name):
        """Delete the VM from the VSA client"""
        try:
            self.vsa_hv_obj.VMs = vm_name
            self.log.info("Deleting VM [%s] from the hypervisor", vm_name)
            self.vsa_hv_obj.VMs[vm_name].delete_vm()
            self.log.info("VM [%s] deleted from the hypervisor", vm_name)
        except Exception as exp:
            self.log.error("Unable to find/delete VM [%s] from the hypervisor with error: %s", vm_name, str(exp))

    def _cleanup(self):
        """Cleanup the entities created"""
        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete the restore VM
            self._vsa_vm_delete(self.vsa_restore_vm_name)
            # Delete backup-set
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backup set: %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted backup set: %s", self.backupset_name)
                self.log.info("If exists delete backup set [%s_Deleted] on content VM [%s] backed up",
                              self.backupset_name, self.vsa_content_vm_name)
                if self.commcell.clients.has_client(self.vsa_content_vm_name):
                    content_vm_client = self.commcell.clients.get(self.vsa_content_vm_name)
                    if content_vm_client.agents.has_agent(self.tcinputs['AgentName']):
                        content_vm_agent = content_vm_client.agents.get(self.tcinputs['AgentName'])
                        if content_vm_agent.backupsets.has_backupset('%s_Deleted' % self.backupset_name):
                            self.log.info("Deleting Backup Set: %s_Deleted ", self.backupset_name)
                            content_vm_agent.backupsets.delete('%s_Deleted' % self.backupset_name)
                            self.log.info("Deleted Backup Set: %s_Deleted", self.backupset_name)
            # Delete Storage Policies
            if self.commcell.storage_policies.has_policy(self.policy_name):
                self.log.info("Deleting storage policy: %s", self.policy_name)
                self.commcell.storage_policies.delete(self.policy_name)
                self.log.info("Deleted storage policy: %s", self.policy_name)
            # Delete Cloud Storage Pool
            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info("Deleting storage pool: %s", self.pool_name)
                self.commcell.storage_pools.delete(self.pool_name)
                self.log.info("Deleted storage pool: %s", self.pool_name)
        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        self.pool_name = '%s_pool-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                        self.tcinputs['ClientName'])
        self.policy_name = '%s_policy-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                            self.tcinputs['ClientName'])
        self.backupset_name = '%s_bs-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                           self.tcinputs['ClientName'])
        self.vsa_restore_vm_name = '%s_Restore_VM' % str(self.id)

        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])

        # DDB partition path
        if self.tcinputs.get("PartitionPath"):
            self.partition_path = self.tcinputs['PartitionPath']
        else:
            if self.ma_machine.os_info.lower() == 'unix':
                self.log.error("LVM enabled DDB partition path must be an input for the unix MA.")
                raise Exception("LVM enabled partition path not supplied for Unix MA!..")
            # To select drive with space available in Media agent machine
            self.log.info('Selecting drive in the Media agent machine based on space available')
            ma_drive = options_selector.get_drive(self.ma_machine, size=25 * 1024)
            if ma_drive is None:
                raise Exception("No free space for hosting ddb on media agent machine.")
            self.log.info('selected drive: %s', ma_drive)
            self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')

        self.vsa_content_vm_name = self.tcinputs['ContentVMName']
        self.content_path = [{'type': 9, 'display_name': self.vsa_content_vm_name}]

        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        self._vsa_helper_init()

        self._cleanup()

    def run(self):
        """Run function of this test case"""
        try:
            # Creating cloud storage pool
            pool_obj, lib_obj = self.mmhelper.configure_storage_pool(self.pool_name, self.tcinputs["CloudMountPath"],
                                                                     self.tcinputs["MediaAgentName"],
                                                                     self.tcinputs["MediaAgentName"],
                                                                     self.partition_path,
                                                                     username=self.tcinputs["CloudUserName"],
                                                                     credential_name=self.tcinputs["SavedCredential"],
                                                                     cloud_vendor_name=self.tcinputs["CloudServerType"])

            storage_vendor_type = pool_obj.storage_vendor
            storage_class = pool_obj.storage_pool_properties['storagePoolDetails']['cloudStorageClassNumber']
            if not (storage_vendor_type == 2 and storage_class in (8, 9, 10, 11, 12, 16, 17, 18, 19, 20, 40, 48)):
                self.log.error("Specify Amazon S3 storage with the Archive storage class details for the test case.")
                raise Exception("Specify Amazon S3 storage with the Archive storage class details for the test case.")
            else:
                self.log.info("Cloud storage pool created with Amazon S3 storage with the Archive storage class")

            # Creating dependent storage policy associated to the pool
            self.mmhelper.configure_storage_policy(self.policy_name, storage_pool_name=self.pool_name)

            # Creating backupset
            self.backupset = self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            # Creating subclient
            subclient_name = "%s_SC1" % str(self.id)
            self.subclient = self.mmhelper.configure_subclient(self.backupset_name, subclient_name,
                                                               self.policy_name, self.content_path, self.agent)

            # Run a Full Backup
            self.common_util.subclient_backup(self.subclient, 'full')

            # Restore from cloud
            self.log.info("Restoring data from cloud archive storage")
            expected_jpr = ("The object might be archived and the Cloud Recall workflow might have been initiated. "
                            "After the recall operation is complete, the job will resume and the recalled data will "
                            "be restored.")
            self.log.info("Restoring VM [%s] from cloud archive storage", self.vsa_content_vm_name)
            self.subclient.refresh()
            restore_job = self.subclient.full_vm_restore_out_of_place(vm_to_restore=self.vsa_content_vm_name,
                                                                      restored_vm_name=self.vsa_restore_vm_name,
                                                                      destination_path="", overwrite=True)
            self.log.info("Restore job [%s] from cloud archive storage has started.", restore_job.job_id)
            self.mmhelper.wait_for_job_state(restore_job, expected_state=['waiting', 'pending'], hardcheck=False)
            if restore_job.pending_reason and expected_jpr in restore_job.pending_reason:
                self.log.info("Restore job is waiting for recall to complete.")
            else:
                # MR-445199 - Restore job does not go into pending state with JPR. Therefore, treating as soft failure.
                self.log.warning("Restore job did not go into pending state with JPR.")
                self.result_string = ("Restore job [%s] did not go into pending state with JPR. "
                                      "Treating as soft failure.") % restore_job.job_id
            wf_jobid = self.mmhelper.get_recall_wf_job(restore_job.job_id)
            self.mmhelper.wait_for_job_completion(wf_jobid, retry_interval=3600, timeout=1440)
            if not self.mmhelper.wait_for_job_state(restore_job, time_limit=90, hardcheck=False):
                self.log.info("Restore job didn't complete in 90 minutes after recall completion, assuming workflow "
                              "completed prematurely but still recall is pending. Hence testcase will wait for "
                              "24 hours with 60 minutes status check interval for restore job to complete.")
                self.mmhelper.wait_for_job_completion(restore_job, retry_interval=3600, timeout=1440)
            self.log.info("restore job from cloud archive storage has completed successfully.")

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
            self._vsa_vm_delete(self.vsa_restore_vm_name)
