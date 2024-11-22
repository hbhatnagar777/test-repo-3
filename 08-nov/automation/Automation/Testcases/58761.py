# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase to Validate Azure Application IAM (Credential Manager) authentication option.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _cleanup()                  --  Cleanup the entities created

    set_multiple_readers()        -- Allow multiple data readers to subclient

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import (DedupeHelper, MMHelper)
from time import sleep


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "Validate Azure Application IAM (Credential Manager) authentication option."
        self.tcinputs = {
            "ClientName": None,
            "MediaAgentName": None,
            "CloudMountPath": None,  # Container Name
            "CloudUserName": None,  # blob.core.windows.net@[storage class]//[account name]|-|__CVCREDID__
            "CredentialName": None
        }
        self.cloud_library_name = None
        self.storage_policy_dedupe_name = None
        self.backupset_name = None
        self.client_machine = None
        self.ma_machine = None
        self.partition_path = None
        self.content_path1 = None
        self.restore_dest_path = None
        self.common_util = None
        self.dedupehelper = None
        self.mmhelper = None

    def _validate_credtype(self, cred_name):
        """
        Validate if credentials passed as input are of azure app type or not.
        Args:
            (str) Cred_name -- Name of credential entered by user in input file.
        Return:
            (Bool) True if type is 4
            (Bool) False if type is not 4
        """
        query = f"""SELECT recordType FROM APP_Credentials WHERE credentialName LIKE ('{cred_name}')"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        if cur != ['4']:
            return False
        return True

    @staticmethod
    def set_multiple_readers(subclient, num_readers):
        """
            Allow multiple data readers to subclient
            Args:
                subclient          (object) --  instance of subclient to set data readers
                num_readers        (int)    --  Number of data readers
        """

        subclient.allow_multiple_readers = True
        subclient.data_readers = num_readers

    def _cleanup(self):
        """Cleanup the entities created"""
        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete content path
            if self.client_machine.check_directory_exists(self.content_path1):
                self.client_machine.remove_directory(self.content_path1)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
            # Delete backup set
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting Backup-set: %s ", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted Backup-set: %s", self.backupset_name)
            # Delete Storage Policies
            if self.commcell.storage_policies.has_policy(self.storage_policy_dedupe_name):
                self.log.info("Deleting storage policy: %s", self.storage_policy_dedupe_name)
                self.commcell.storage_policies.delete(self.storage_policy_dedupe_name)
                self.log.info("Deleted storage policy: %s", self.storage_policy_dedupe_name)
            # Delete Cloud Library
            if self.commcell.disk_libraries.has_library(self.cloud_library_name):
                self.log.info("Deleting library: %s", self.cloud_library_name)
                self.commcell.disk_libraries.delete(self.cloud_library_name)
                self.log.info("Deleted library: %s", self.cloud_library_name)
        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        self.cloud_library_name = '%s_cloud-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                           self.tcinputs['ClientName'])
        self.storage_policy_dedupe_name = '%s_dedupe-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                           self.tcinputs['ClientName'])
        self.backupset_name = '%s_bs-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                           self.tcinputs['ClientName'])

        options_selector = OptionsSelector(self.commcell)
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
        client_drive = options_selector.get_drive(self.client_machine, size=5 * 1024)
        if client_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', client_drive)

        self.content_path1 = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata1')
        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Restoredata')

        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)

        self._cleanup()

    def run(self):
        """Run function of this test case"""
        try:

            cred_name = self.tcinputs["CredentialName"]
            chk_cred_type = self._validate_credtype(cred_name)
            if chk_cred_type:
                self.log.info("Credentials used are of Azure App type, proceeding with the case.")
            else:
                self.log.error("Wrong type of credentials entered by user, Failing case.")
                raise Exception("Wrong type of credentials entered by user, Failing case.")

            # Creating Cloud Library by using saved credentials only for Azure Storage.
            cloud_lib_obj = self.mmhelper.configure_cloud_library(self.cloud_library_name,
                                                                  self.tcinputs['MediaAgentName'],
                                                                  self.tcinputs["CloudMountPath"],
                                                                  self.tcinputs["CloudUserName"],
                                                                  "dummy",
                                                                  "Microsoft Azure Storage",
                                                                  self.tcinputs["CredentialName"])
            # Configuring de-dupe storage policy
            sp_dedup_obj = self.dedupehelper.configure_dedupe_storage_policy(self.storage_policy_dedupe_name,
                                                                             self.cloud_library_name,
                                                                             self.tcinputs['MediaAgentName'],
                                                                             self.partition_path)
            # Set retention of 0-day & 1-cycle on configured storage policy copy
            self.log.info("Setting Retention: 0-days and 1-cycle on Primary Copy")
            sp_dedup_primary_obj = sp_dedup_obj.get_copy("Primary")
            retention = (0, 1, -1)
            sp_dedup_primary_obj.copy_retention = retention
            # create backup set
            self.mmhelper.configure_backupset(self.backupset_name, self.agent)
            # create sub-client
            subclient1_name = "%s_SC1" % str(self.id)
            sc1_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient1_name,
                                                        self.storage_policy_dedupe_name, self.content_path1, self.agent)
            # Allow multiple data readers to subclient
            self.log.info("Setting Data Readers=4 on Subclient")
            self.set_multiple_readers(sc1_obj, 4)
            job_copy_list = []
            job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full', 'incremental',
                                       'synthetic_full']
            for sequence_index in range(0, 6):
                # Create unique content
                if job_types_sequence_list[sequence_index] is not 'synthetic_full':
                    self.log.info("Generating Data at %s", self.content_path1)
                    if not self.client_machine.generate_test_data(self.content_path1, dirs=1, file_size=(2 * 1024),
                                                                  files=5):
                        self.log.error("unable to Generate Data at %s", self.content_path1)
                        raise Exception("unable to Generate Data at {0}".format(self.content_path1))
                    self.log.info("Generated Data at %s", self.content_path1)
                    self.log.info("Sleeping for 10 seconds before running backup job.")
                    sleep(10)
                # Perform Backup
                if sequence_index < 3:
                    job_copy_list.append(
                        (self.common_util.subclient_backup(sc1_obj, job_types_sequence_list[sequence_index]).job_id,
                         [sp_dedup_primary_obj]))
                else:
                    self.common_util.subclient_backup(sc1_obj, job_types_sequence_list[sequence_index])
            # Restore from cloud
            restore_job = sc1_obj.restore_out_of_place(self.client, self.restore_dest_path,
                                                       [self.content_path1])
            self.log.info("restore job [%s] has started.", restore_job.job_id)
            if not restore_job.wait_for_completion(60):
                self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info("Comparing source content and restore destination content sizes.")
            src_folder_size = self.client_machine.get_folder_size(self.content_path1, in_bytes='true')
            self.log.info("Get Source Folder Size: %s", src_folder_size)
            dest_folder_size = self.client_machine.get_folder_size(self.restore_dest_path, in_bytes='true')
            self.log.info("Get Destination Folder Size: %s", dest_folder_size)
            if not src_folder_size == dest_folder_size:
                self.log.error(" Folder Size mismatch between source and destination.")
                raise Exception(" Size of source folder and destination folder is not same.")
            self.log.info("restore job from cloud [%s] has completed.", restore_job.job_id)
            # Run Granular DataAging
            data_aging_job = self.commcell.run_data_aging(storage_policy_name=self.storage_policy_dedupe_name,
                                                          is_granular=True,
                                                          include_all_clients=True)
            self.log.info("Granular Data Aging job [%s] has started.", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)
            # Pruning Validation
            self.log.info("Pruning Validation Started for storage policy.")
            for job_copy in job_copy_list:
                for copy in job_copy[1]:
                    if self.mmhelper.validate_job_prune(job_copy[0], int(copy.copy_id)):
                        self.log.info("Job %s is aged on [%s/%s]", str(job_copy[0]),
                                      copy.storage_policy.storage_policy_name, copy._copy_name)
                    else:
                        self.log.error("Job %s is not aged on [%s/%s]", str(job_copy[0]),
                                       copy.storage_policy.storage_policy_name, copy._copy_name)
                        raise Exception("Job [{0}] is not aged on [{1}/{2}]".format(str(job_copy[0]),
                                                                                    copy.storage_policy. \
                                                                                    storage_policy_name,
                                                                                    copy._copy_name)
                                        )
            self.log.info("Pruning Validation completed successfully.")
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
                self.client_machine.remove_directory(self.content_path1)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
