# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    _cleanup()      --  deletes the automation created resources.

    get_mount_path  --  return the mounth path for the given library.

    run_data_aging  --  run data aging job.

Design Steps:
	1. Create Cloud Storage Library.
	2. From MountPath Properties > Do not consume more than, set it to 5 GBs
	3. Create a backupset and a subclient.
	4. run a backup with 3 GB content --> backup should succeed.
    5. Run a backup with 3 GB content --> backup should fail.

Sample Input:
            {
                "ClientName": "client_name",
                "MediaAgentName": "MA name",
                "AgentName": "File System"
            }
    Additional Inputs -
        LibraryName: "library name"
        OR
        "CloudMountPath": "mount path"
        "CloudUserName": "user name",
        "CloudPassword": "password",
        "CloudServerType": "microsoft azure storage"
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils


class TestCase(CVTestCase):
    """Class for executing max data to consume on cloud library"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Max Data to Consume on cloud library"
        self.MMHelper = None
        self.DedupeHelper = None
        self.client_machine_obj = None

        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None

        self.media_agent = None
        self.cloud_lib = None
        self.mount_path = None

        self.content_path = None
        self.restore_dest_path = None
        self.is_user_provided_lib = None

        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Starting test case setup")
        self.MMHelper = MMHelper(self)
        self.DedupeHelper = DedupeHelper(self)
        self.common_util = CommonUtils(self)
        options_selector = OptionsSelector(self.commcell)

        self.media_agent = self.tcinputs.get("MediaAgentName")
        # Client machine object
        self.client_machine_obj = options_selector.get_machine_object(self.tcinputs['ClientName'])

        # Selecting Drive in Machines
        client_drive = options_selector.get_drive(self.client_machine_obj, size=10 * 1024)

        # Storage_policy
        self.storage_policy_name = f"{self.id}_storage_policy"

        # Backupset
        self.backupset_name = f"{self.id}_backupset"

        # Subclient
        self.subclient_name = f"{self.id}_subclient"

        # Library
        self.library_name = '%s_library' % str(self.id)

        # Content path
        self.content_path = self.client_machine_obj.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata')

        # Restore path
        self.restore_dest_path = self.client_machine_obj.join_path(
            client_drive, 'Automation', str(self.id), 'Restoredata')

        # clean up
        self._cleanup()
        self.log.info("Successfully completed test case setup")

    def _cleanup(self):
        """Cleanup the existing entities"""
        self.log.info(
            "********************** CLEANUP STARTING *************************")
        try:
            # Deleting Content Path
            self.log.info("Deleting content path: %s if exists", self.content_path)
            if self.client_machine_obj.check_directory_exists(self.content_path):
                self.client_machine_obj.remove_directory(self.content_path)
                self.log.info("Deleted content path: %s", self.content_path)

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
            if not self.tcinputs.get("LibraryName"):
                self.log.info(f"Deleting library {self.library_name}")
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.log.info("Library[%s] exists, deleting that", self.library_name)
                    self.commcell.disk_libraries.delete(self.library_name)
                    self.log.info(f"{self.library_name} deleted sucessfully!")

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception(
                "Error encountered during cleanup: {0}".format(str(exp)))
        self.log.info(
            "********************** CLEANUP COMPLETED *************************")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")
        if self.status != constants.FAILED:
            self.log.info(
                "Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
            # Run Data Aging.
            self.run_data_aging()
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment."
                "Please check for failure reason and manually clean up the environment..."
            )
        if self.is_user_provided_lib:
            self.log.info("Updating max data to write on cloud library to default!")
            self.cloud_lib.set_max_data_to_write_on_mount_path(
                self.mount_path, -1
            )
            self.log.info("Successfully Updated max data to write to default!")

    def get_mount_path(self, library_id):
        """
        Get folder path name from MMMountPath.
        """
        query = """
        select folder from MMDeviceController  MDC
        Join MMMountPathToStorageDevice MPSD on 
        MDC.DeviceId = MPSD.DeviceId
        JOIN MMMountPath MP on 
        MPSD.MountPathId = MP.MountPathId 
        Where MP.LibraryId={0}""".format(library_id)

        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT: {res}")
        return res

    def run_data_aging(self):
        """
        Function to run data aging job.
        """
        data_aging_job = self.commcell.run_data_aging()
        self.log.info("Data Aging job [%s] has started.", data_aging_job.job_id)
        if not data_aging_job.wait_for_completion():
            self.log.error(
                "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
            raise Exception(
                "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                   data_aging_job.delay_reason))
        self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)

    def run(self):
        """Main test case logic"""
        try:
            # Creating cloud storage.
            if self.tcinputs.get("LibraryName"):
                self.is_user_provided_lib = True
                self.library_name = self.tcinputs.get("LibraryName")
                if not self.commcell.disk_libraries.has_library(self.library_name):
                    raise Exception("Library Name provided is invalid!")
                self.cloud_lib = self.commcell.disk_libraries.get(self.library_name)
                self.cloud_lib.mediaagent = self.tcinputs.get("MediaAgentName")

            elif (("CloudMountPath" and "CloudUserName" and "CloudPassword" and "CloudServerType" in self.tcinputs) and
                  (self.tcinputs["CloudMountPath"] and self.tcinputs["CloudUserName"]
                   and self.tcinputs["CloudPassword"] and self.tcinputs["CloudServerType"])):
                self.is_user_provided_lib = False
                self.cloud_lib = self.MMHelper.configure_cloud_library(self.library_name,
                                                                       self.media_agent,
                                                                       self.tcinputs["CloudMountPath"],
                                                                       self.tcinputs["CloudUserName"],
                                                                       self.tcinputs["CloudPassword"],
                                                                       self.tcinputs["CloudServerType"])
            else:
                raise Exception("No Library details provided.")

            # Get Mount Path
            if self.is_user_provided_lib:
                library_id = self.cloud_lib.library_id
                self.log.info(f"Got library id {library_id}")
                self.mount_path = self.get_mount_path(library_id)
                self.log.info(f"Got mount path {self.mount_path} for library {library_id}")

                # Set max data to be written on Mount Path to 5GB
                self.log.info("Setting max data to consume to 5GB")
                self.cloud_lib.set_max_data_to_write_on_mount_path(
                    self.mount_path, 5120
                )
                self.log.info("Set max data to write to 5GB")
            else:
                # Set max data to be written on Mount Path to 5GB
                self.log.info("Setting max data to consume to 5GB")
                self.cloud_lib.set_max_data_to_write_on_mount_path(
                    self.tcinputs["CloudMountPath"], 5120
                )
                self.log.info("Set max data to write to 5GB")

            # Storage Policy
            self.MMHelper.configure_storage_policy(
                self.storage_policy_name, self.library_name,
                self.media_agent
            )

            # Creating Backupset
            self.MMHelper.configure_backupset(self.backupset_name)

            # Creating Subclient - Disk Storage Policy
            subclient = self.MMHelper.configure_subclient(
                self.backupset_name, self.subclient_name,
                self.storage_policy_name, self.content_path
            )

            # Run Full Backup job
            # Create unique content of 3 GB
            if not self.MMHelper.create_uncompressable_data(self.client_machine_obj, self.content_path, 3):
                self.log.error(
                    "unable to Generate Data at %s", self.content_path)
                raise Exception(
                    "unable to Generate Data at {0}".format(self.content_path))
            self.log.info("Generated Data at %s", self.content_path)

            # Perform Backup.
            self.log.info("Starting backup jobs for subclient %s", self.subclient_name)
            job_id = self.common_util.subclient_backup(
                subclient, 'full').job_id

            self.log.info('Backup completed successfully on %s with job_id %s', self.subclient_name, job_id)

            # Create uncompressable data of 3GB
            if not self.MMHelper.create_uncompressable_data(self.client_machine_obj, self.content_path, 3):
                self.log.error(
                    "unable to Generate Data at %s", self.content_path)
                raise Exception(
                    "unable to Generate Data at {0}".format(self.content_path))
            self.log.info("Generated Data at %s", self.content_path)

            # Run Backup and verify - backup goes in waiting state.
            job = subclient.backup(r'full')
            job_id = job.job_id
            self.log.info("Backup job id %s started!", job_id)
            while True:
                phase = job.phase
                self.log.info(f"Job Phase Reached  ->  {phase}")
                status = job.status.lower()
                self.log.info("Job status %s", status)
                if phase == "Backup" and status == 'waiting':
                    self.log.info(f"Job waiting :- {job.delay_reason}")

                    # Verify Job Manager Logs for Job Failure Reasons.
                    matched_line, matched_string = self.DedupeHelper.parse_log(
                        self.commcell.commserv_name,
                        'JobManager.log',
                        'Amount of data on Mount Path has reached the maximum threshold set',
                        job_id
                    )
                    if matched_line or matched_string:
                        self.log.info('matched line: %s', matched_line)
                        self.log.info('matched string: %s', matched_string)
                    else:
                        raise Exception(f"Job Manager logs not found for- {job_id}")

                    job.kill()
                    self.log.info("Job Killed Successfully!!")
                    break
                if status == 'completed':
                    self.log.info("Failure: Job got completed!")
                    raise Exception("Job Got Completed!")
                time.sleep(10)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
