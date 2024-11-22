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

    _get_mountpath_info(library_id)   --  Gets top first mountpath name from library id

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Design steps:
1. Create a cloud dedupe storage pool using Azure Archive as the storage class using MediaAgent (MA).
2. Configure a policy-copy associated with the pool created in step 1.
3. Configure a backupset and a sub-client on the FS client and associate it with the policy configured in step 2.
4. Run a backup job.
5. Initiate a restore job.
6. The restore job should start a cloud archive recall workflow job.
7. Once recall workflow job finishes after recalling all files, the restore job should resume and complete.
8. After recall, verify if data got restored using cvshadowcopy container in azure.

Sample Input:
        "58774":{
            "ClientName": "Client_1",
            "MediaAgentName": "MediaAgent_1",
            "CloudMountPath": "Azure Archive",
            "CloudUserName": "Azure UserName",
            "SavedCredential": "Azure Saved Credential",
            "CloudServerType": "Microsoft Azure Storage"
        }
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import (DedupeHelper, MMHelper)


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "Cloud Archive Recall using Microsoft Azure Storage - FS Workload"
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

    def _get_mountpath_info(self, library_id):
        """
        Gets top first mountpath name from library id
        Args:
            library_id (int)  --  Library ID

        Returns:
            str - First mountpath name  for the given library id
        """

        self.log.info("Getting first mountpath info from library id")
        query = f"""
                    SELECT	MM.MountPathName
                    FROM	MMMountPath MM WITH(NOLOCK)
                    WHERE	MM.LibraryId = {library_id}
                    ORDER BY MM.MountPathId DESC
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        if cur[0] != '':
            return cur[0]
        else:
            self.log.error("No mountpath entries present")
            raise Exception("Invalid LibraryId")

    def _cleanup(self):
        """Cleanup the entities created"""
        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
            # Delete backup-set
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backup set: %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted backup set: %s", self.backupset_name)
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

        self.client_machine = options_selector.get_machine_object(self.client)
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

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=25 * 1024)
        if client_drive is None:
            raise Exception("No free space for content on client machine.")
        self.log.info('selected drive: %s', client_drive)
        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'TestData')
        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'RestoreData')

        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)

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
            if not (storage_vendor_type == 3 and storage_class in (3, 4, 5, 19)):
                self.log.error("Specify Azure storage with the Archive tier details for the test case.")
                raise Exception("Specify Azure storage with the Archive tier details for the test case.")
            else:
                self.log.info("Cloud storage pool created with Azure Archive storage class")

            # Creating dependent storage policy associated to the pool
            self.mmhelper.configure_storage_policy(self.policy_name, storage_pool_name=self.pool_name)

            # Creating backupset
            self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            # Creating subclient
            subclient_name = "%s_SC1" % str(self.id)
            sc1_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient_name,
                                                        self.policy_name, self.content_path, self.agent)

            self.log.info("Generating Data at %s", self.content_path)
            if not self.client_machine.generate_test_data(self.content_path, dirs=1, file_size=(2 * 1024), files=10):
                self.log.error("unable to Generate Data at %s", self.content_path)
                raise Exception("unable to Generate Data at {0}".format(self.content_path))
            self.log.info("Generated Data at %s", self.content_path)

            # Run a Full Backup
            self.common_util.subclient_backup(sc1_obj, 'full')

            # Restore from cloud
            self.log.info("Restoring data from cloud archive storage")
            expected_jpr = ("The object might be archived and the Cloud Recall workflow might have been initiated. "
                            "After the recall operation is complete, the job will resume and the recalled data will "
                            "be restored.")
            restore_job = sc1_obj.restore_out_of_place(self.client, self.restore_dest_path, [self.content_path])
            self.log.info("Restore job [%s] from cloud archive storage has started.", restore_job.job_id)
            self.mmhelper.wait_for_job_state(restore_job, expected_state=['waiting', 'pending'], hardcheck=False)
            if restore_job.pending_reason and expected_jpr in restore_job.pending_reason:
                self.log.info("Restore job is waiting for recall to complete with JPR.")
            else:
                # MR-445199 - Restore job does not go into pending state with JPR. Therefore, treating as soft failure.
                self.log.warning("Restore job did not go into pending state with JPR.")
                self.result_string = ("Restore job [%s] did not go into pending state with JPR. "
                                      "Treating as soft failure.") % restore_job.job_id
            wf_jobid = self.mmhelper.get_recall_wf_job(restore_job.job_id)
            self.client.add_additional_setting('EventManager', 'CloudActivity_DEBUGLEVEL', 'INTEGER', '2')
            self.mmhelper.wait_for_job_completion(wf_jobid, retry_interval=3600, timeout=1440)
            if not self.mmhelper.wait_for_job_state(restore_job, time_limit=60, hardcheck=False):
                self.log.info("Restore job didn't complete in 60 minutes after recall completion, assuming workflow "
                              "completed prematurely but still recall is still pending. Hence testcase will wait for "
                              "24 hours with 60 minutes status check interval for restore job to complete.")
                self.mmhelper.wait_for_job_completion(restore_job, retry_interval=3600, timeout=1440)
            self.log.info("restore job from cloud archive storage has completed successfully.")
            self.client.delete_additional_setting('EventManager', 'CloudActivity_DEBUGLEVEL')

            # Verify if data got restored using cvshadowcopy container in azure after recall
            self.log.info("Verifying if data got restored using cvshadowcopy container in azure after recall")
            mountpath_name = self._get_mountpath_info(lib_obj.library_id)
            cvshadowcopy_log_regex = 'GET (200|206).*cvshadowcopy-do-not-use-or-delete.*%s.*' % mountpath_name
            cvshadowcopy_log_result = self.dedupehelper.parse_log(self.client.name, 'CloudActivity.log',
                                                                  cvshadowcopy_log_regex, escape_regex=False,
                                                                  only_first_match=True)
            if cvshadowcopy_log_result[0]:
                self.log.info("Matched log entry: [%s]", cvshadowcopy_log_result[1])
                self.log.info("Data got restored using cvshadowcopy container in azure after recall")
            else:
                self.log.error("Data not restored using cvshadowcopy container in azure after recall")
                raise Exception("Data not restored using cvshadowcopy container in azure after recall")

            # Verify the restored data
            self.log.info("Verifying the restored data")
            if not self.client_machine.compare_folders(self.client_machine, self.content_path, self.restore_dest_path):
                self.log.error("Data restored is not same as backed up data")
                raise Exception("Data restored is not same as backed up data, checksum comparison failed")
            self.log.info("Data restored is same as backed up data")

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
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment."
                "Please check for failure reason and manually clean up the environment..."
            )
