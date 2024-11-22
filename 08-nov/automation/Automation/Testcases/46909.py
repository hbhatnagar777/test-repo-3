# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase to perform Basic Mountpath, Storage Policy and DDB configuration for MA Acceptance.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _validate_jmdatastats(job_id, copy_id)
                                --  validates if a job_id on copy_id exists in table jmdatastats

    _validate_archchunkmapping(job_id, copy_id)
                                --  validates if archchunkmapping entry for job id exists on copy_id

    _validate_jobs_prune(job_copy_list)
                                --  validates if a job on copy is aged by checking table entries

    _validate_license(client_id)
                                -- validates DDO and Cloud Storage licenses.

    _restore_verify             --  validates restored data with original data

    _push_install               --  Install a new media agent.

    _cleanup()                  --  Cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Design Steps:
    1. Push Install a MA.
	2. Validate licenses (DDO, Cloud) are not consumed. 
	3. Create a disk library DL1
	4. Create a dedupe enabled Storage Policy.
	5.  Create a disk Library DL2
	6. Create a non dedupe secondary copy. 
	7. Create a Cloud Library CL1
	8. Create a dedupe enabled secondary copy. 
	9. Set retention of 0day 1cycle all copies. 
	10. Remove association of secondary copy with system created autocopy schedule.
	11. Validate licenses (DDO, Cloud) should be consumed. 
	12. Allow multiple data readers to subclient, set readers to 4. 
	13. Create BackupSet and SubClient. 
	14. Run backups - (full, incremental, incremental, synthetic full, incremental, synthetic full)
	15. Run AuxCopy Job.
	16. Perform Restore from each copy and verify restore content. 
	17. Run Data Aging Job. 
	18. Validate Jobs got pruned. 
Delete all libraries and validate licenses (DDO, Cloud) are released/uninstalled. 

Sample Inputs:
        "46909": {
            "ClientName": "ClientName",
            "AgentName": "File System",
            "MachineHostName": "hostname/IP",
            "MachineUsername": "usename",
            "MachinePassword": "password",
            "CloudMountPath":"cloud mount paath",
            "CloudUserName": "cloud username",
            "CloudPassword": "cloud password",
            "CloudServerType":"microsoft azure storage"
            }
"""

from AutomationUtils import (constants, commonutils)
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import (DedupeHelper, MMHelper)
from Install.install_helper import InstallHelper
from cvpysdk.policies.storage_policies import StoragePolicy

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "MA Basic Acceptance"
        self.primary_lib_name = None
        self.secondary_nondedupe_lib_name = None
        self.secondary_dedupe_lib_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.client_machine = None
        self.ma_machine = None
        self.mountpath = None
        self.partition_path = None
        self.copy_partition_path = None
        self.content_path = None
        self.restore_dest_path = None
        self.common_util = None
        self.dedupehelper = None
        self.mmhelper = None
        self.MediaAgent = None
        self.machine_name = None
        self.install_helper = None
        self.ma_name = None

        self.tcinputs = {
            "ClientName": None,
            "MachineHostName": None,
            "MachineUsername": None,
            "MachinePassword": None
        }

    def _push_install(self):
        # Check if MA is already installed.
        if self.commcell.clients.has_client(self.machine_name):
            client_obj = self.commcell.clients.get(self.machine_name)
            self.log.info("%s already installed", self.machine_name)
            if client_obj.is_ready:
                self.log.info("Check Readiness of CS successful")
                return client_obj
            self.install_helper.uninstall_client(delete_client=False, instance=client_obj.instance)

        # Pushing Packages from CS to the client
        self.log.info(f"Starting a Push Install Job: {self.machine_name}")
        push_job = self.install_helper.install_software(
                            client_computers=[self.machine_name],
                            features=['FILE_SYSTEM', 'MEDIA_AGENT'],
                            username=self.tcinputs['MachineUsername'],
                            password=self.tcinputs['MachinePassword']
        )
        self.log.info(f"Job Launched Successfully for Windows, Will wait until Job: {push_job.job_id} Completes")
        if push_job.wait_for_completion():
            self.log.info("Push Upgrade Job Completed successfully")
        else:
            job_status = push_job.delay_reason
            self.log.error(f"Job failed with an error: {job_status}")
            raise Exception(job_status)

        # Check Readiness Test --
        # Refreshing the Client list to me the New Client Visible on GUI
        self.log.info("Refreshing Client List on the CS")
        self.commcell.refresh()

        # Check if the services are up on Client and is Reachable from CS
        self.log.info("Initiating Check Readiness from the CS")
        if self.commcell.clients.has_client(self.machine_name):
            client_obj = self.commcell.clients.get(self.machine_name)
            if client_obj.is_ready:
                self.log.info("Check Readiness of CS successful")
                return client_obj
        else:
            self.log.error("Client failed Registration to the CS")
            raise Exception(f"Client: {self.machine_name} failed registering to the CS, "
                            f"Please check client logs")

    def _get_optype(self, res, idx):
        """
        Gets the Optype Value from results.
        Args:
            res (list) : list of db output
            idx (int)   : index value to be returned.
        """
        try:
            optype = res[idx]
            self.log.info(f"Get Optype: {optype}")
            return optype
        except Exception as e:
            self.log.info(f"Exception Occured {e}")
            return 'UnInstall'

    def _validate_license(self, flag=True):
        """
        Validate if media agent still has DDO and Cloud Storage license.

        Args:
            flag (bool)    :    Validate for install or uninstall
        Response:
            raises Exception if fails.
        """
        query = f"""select OpType from LicUsage 
                    where LicType in (84, 190) -- 84: Disk Library Connector (DDO), 190 : Cloud Storage
                    AND CId = {self.MediaAgent.client_id}
                """
        self.log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        result = [x[0].strip() for x in cur]
        self.log.info(f"Result {result}")
        ddoOptype = self._get_optype(result, 0)
        csOptype = self._get_optype(result, 1)
        self.log.info(f"DDO: {ddoOptype}, CloudStorage: {csOptype}")
        if ddoOptype == 'Install' and csOptype == 'Install':
            install = True
        elif (ddoOptype == "" or ddoOptype == 'UnInstall') and (csOptype == "" or csOptype == 'UnInstall'):
            install = False
        else:
            raise Exception("Failure Validating License!")

        self.log.info(f"Flag: {flag}, Install: {install}")
        if install != flag:
            raise Exception("Failure Validating License!")

    def _validate_jmdatastats(self, job_id, copy_id):
        """
        Validate if a job_id on copy_id exists in table jmdatastats
        Args:
            job_id (int) -- backup job id to check in table
            copy_id (int) -- copy id of the job to validate on
        Return:
            (Bool) True if job id exists
            (Bool) False if not exists
        """

        query = """select agedTime, agedBy, disabled&256 from JMJobDataStats where jobId = {0} and archGrpCopyId = {1}
                """.format(job_id, copy_id)
        self.log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: {0}".format(cur))
        if cur != ['']:
            values = [int(x) for x in cur]
            if values[0] > 0 and values[1] > 0 and values[2] == 256:
                return False
        return True

    def _validate_archchunkmapping(self, job_id, copy_id):
        """
        Validate if archchunkmapping entry for job id exists on copy_id
        Args:
            job_id (int) -- job id to check in table
            copy_id (int) -- copy id of the job to validate on

        Return:
            (Bool) True if entries exist
            (Bool) False if entries doesnt exist
        """

        query = """select archFileId, archChunkId from archchunkmapping where jobId = {0} and archCopyId = {1}
                        """.format(job_id, copy_id)
        self.log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self.log.info("RESULT: {0}".format(cur))
        if cur != [['']]:
            return True
        self.log.info("No entries present")
        return False

    def _validate_jobs_prune(self, job_copy_list):
        """
        Validates if a job on copy is aged by checking table entries
        Args:
            job_copy_list (list) -- list of tuples, each tuple has job instance and list of copy instance
        Return:
            (Bool) True/False
        """

        for job_copy in job_copy_list:
            for copy in job_copy[1]:
                if (self._validate_jmdatastats(job_copy[0], int(copy.copy_id)) and
                        self._validate_archchunkmapping(job_copy[0], int(copy.copy_id))):
                    self.log.error("Job %s is not aged on [%s/%s]",
                                   str(job_copy[0]), copy._storage_policy_name, copy._copy_name)
                    raise Exception("Job {0} is not aged on [{1}/{2}]".format(
                        str(job_copy[0]), copy._storage_policy_name, copy._copy_name))

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

    def _cleanup(self):
        """Cleanup the entities created"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete backupset
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            # Delete Storage Policy
            self.log.info("Deleting Storage Policy: %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info(f"Re-Associating Storage Policy {self.storage_policy_name}")
                StoragePolicy(self.commcell, self.storage_policy_name).reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted Storage Policy: %s", self.storage_policy_name)

            # Delete Library
            self.log.info("Deleting primary copy library: %s if exists", self.primary_lib_name)
            if self.commcell.disk_libraries.has_library(self.primary_lib_name):
                self.commcell.disk_libraries.delete(self.primary_lib_name)
                self.log.info("Deleted library: %s", self.primary_lib_name)

            # Delete Library
            self.log.info("Deleting non-deduplication secondary copy library: %s if exists",
                          self.secondary_nondedupe_lib_name)
            if self.commcell.disk_libraries.has_library(self.secondary_nondedupe_lib_name):
                self.commcell.disk_libraries.delete(self.secondary_nondedupe_lib_name)
                self.log.info("Deleted library: %s", self.secondary_nondedupe_lib_name)

            # Delete Library
            self.log.info("Deleting deduplication enabled secondary copy library: %s if exists",
                          self.secondary_dedupe_lib_name)
            if self.commcell.disk_libraries.has_library(self.secondary_dedupe_lib_name):
                self.commcell.disk_libraries.delete(self.secondary_dedupe_lib_name)
                self.log.info("Deleted library: %s", self.secondary_dedupe_lib_name)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        options_selector = OptionsSelector(self.commcell)
        timestamp_suffix = options_selector.get_custom_str()
        self.primary_lib_name = '%s_primary_lib' % str(self.id)
        self.secondary_nondedupe_lib_name = '%s_nondedupe_lib' % str(self.id)
        self.secondary_dedupe_lib_name = '%s_dedupe_lib' % str(self.id)
        self.storage_policy_name = '%s_storage_policy' % str(self.id)
        self.backupset_name = '%s_bs' % str(self.id)
        # Client Machine
        self.client_machine = options_selector.get_machine_object(self.tcinputs['ClientName'])
        # MediaAgent Machine
        self.ma_machine = options_selector.get_machine_object(
            self.tcinputs['MachineHostName'], self.tcinputs['MachineUsername'],
            self.tcinputs['MachinePassword']
        )
        self.log.info("Ma Machine instance created")
        self.machine_name = self.ma_machine.machine_name
        self.install_helper = InstallHelper(self.commcell, self.ma_machine)

        # Push Install
        self.MediaAgent = self._push_install()
        self.ma_name = self.MediaAgent.display_name

        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        self._cleanup()

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=20 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        # To select drive with space available in Media agent machine
        self.log.info('Selecting drive in the Media agent machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=20 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.mountpath = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP')
        self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                        'DDB_%s' % timestamp_suffix)

        self.copy_partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                             'Copy_DDB_%s' % timestamp_suffix)

        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)
        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Restoredata')
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)
        self.client_machine.create_directory(self.restore_dest_path)

    def run(self):
        """Run function of this test case"""

        try:
            # Validating License.
            self.log.info("Validating license False")
            self._validate_license(False)

            # Create library for primary copy
            primary_lib_obj = self.mmhelper.configure_disk_library(self.primary_lib_name,
                                                                   self.ma_name, self.mountpath)

            # Create deduplication enabled storage policy
            sp_obj = self.dedupehelper.configure_dedupe_storage_policy(self.storage_policy_name, primary_lib_obj,
                                                                       self.ma_name,
                                                                       self.partition_path)

            # Set retention of 0-day & 1-cycle on primary copy
            self.log.info("Setting Retention: 0-days and 1-cycle on Primary Copy")
            sp_dedup_primary_obj = sp_obj.get_copy("Primary")
            retention = (0, 1, -1)
            sp_dedup_primary_obj.copy_retention = retention

            # Create library for non-deduplication secondary copy
            self.mmhelper.configure_disk_library(self.secondary_nondedupe_lib_name, self.ma_name,
                                                 self.mountpath)

            # Create non-deduplication secondary copy
            nondedupe_copy_name = '%s_copy_nondedupe' % str(self.id)
            nondedupe_copy_obj = self.mmhelper.configure_secondary_copy(nondedupe_copy_name, self.storage_policy_name,
                                                                        self.secondary_nondedupe_lib_name,
                                                                        self.ma_name)

            # Set retention of 0day 1cycle on non-deduplication secondary copy
            self.log.info("Setting Retention: 0-days and 1-cycle on Secondary Copy")
            retention = (0, 1, -1)
            nondedupe_copy_obj.copy_retention = retention

            # remove association of secondary copy with system created autocopy schedule.
            self.log.info("remove association of secondary copy with system created autocopy schedule")
            self.mmhelper.remove_autocopy_schedule(
                storage_policy_name=self.storage_policy_name,
                copy_name=nondedupe_copy_name)

            # Create library for deduplication enabled secondary copy

            # Create cloud library cloud.
            if (("CloudMountPath" and "CloudUserName" and "CloudPassword" and "CloudServerType" in self.tcinputs) and
                    (self.tcinputs["CloudMountPath"] and self.tcinputs["CloudUserName"]
                     and self.tcinputs["CloudPassword"] and self.tcinputs["CloudServerType"])):

                cloud_lib_obj = self.mmhelper.configure_cloud_library(self.secondary_dedupe_lib_name,
                                                                      self.ma_name,
                                                                      self.tcinputs["CloudMountPath"],
                                                                      self.tcinputs["CloudUserName"],
                                                                      self.tcinputs["CloudPassword"],
                                                                      self.tcinputs["CloudServerType"])
            else:
                raise Exception("Cloud Library Inputs are not Provided!")

            # create deduplication enabled secondary copy
            dedupe_copy_name = '%s_copy_dedupe' % str(self.id)
            self.dedupehelper.configure_dedupe_secondary_copy(sp_obj, dedupe_copy_name, self.secondary_dedupe_lib_name,
                                                              self.ma_name, self.copy_partition_path,
                                                              self.ma_name)

            # Set retention of 0day 1cycle on deduplication enabled secondary copy
            self.log.info("Setting Retention: 0-days and 1-cycle on Secondary Copy")
            dedupe_copy_obj = sp_obj.get_copy(dedupe_copy_name)
            retention = (0, 1, -1)
            dedupe_copy_obj.copy_retention = retention

            # remove association of secondary copy with system created autocopy schedule.
            self.log.info("remove association of secondary copy with system created autocopy schedule")
            self.mmhelper.remove_autocopy_schedule(
                storage_policy_name=self.storage_policy_name,
                copy_name=dedupe_copy_name)

            # Validate License Installed,
            self.log.info("Validating license Install")
            self._validate_license()

            # create backupset
            self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            # create subclient
            subclient1_name = "%s_SC1" % str(self.id)
            sc1_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient1_name,
                                                        self.storage_policy_name, self.content_path, self.agent)

            # Allow multiple data readers to subclient
            self.log.info("Setting Data Readers=4 on Subclient")
            sc1_obj.data_readers = 4
            sc1_obj.allow_multiple_readers = True

            job_copy_list = []
            job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full', 'incremental',
                                       'synthetic_full']

            for sequence_index in range(len(job_types_sequence_list)):
                # Create unique content
                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 2):
                        self.log.error("unable to Generate Data at %s", self.content_path)
                        raise Exception("unable to Generate Data at {0}".format(self.content_path))
                    self.log.info("Generated Data at %s", self.content_path)
                # Perform Backup
                if sequence_index < 3:
                    job_copy_list.append(
                        (self.common_util.subclient_backup(sc1_obj, job_types_sequence_list[sequence_index]).job_id,
                         [sp_dedup_primary_obj, dedupe_copy_obj, nondedupe_copy_obj]))
                else:
                    self.common_util.subclient_backup(sc1_obj, job_types_sequence_list[sequence_index])

            # Restore from primary copy
            restore_job = sc1_obj.restore_out_of_place(self.client, self.restore_dest_path,
                                                       [self.content_path])
            self.log.info("restore job [%s] has started from primary copy.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info("restore job [%s] has completed.", restore_job.job_id)

            # Verify restored data
            if self.client_machine.os_info == 'UNIX':
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '/')
            else:
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '\\')

            dest_path = self.client_machine.join_path(dest_path, 'Testdata')

            self._restore_verify(self.client_machine, self.content_path, dest_path)

            # Run Aux copy Job
            auxcopy_job = sp_obj.run_aux_copy()
            self.log.info("Auxcopy job [%s] has started.", auxcopy_job.job_id)
            if not auxcopy_job.wait_for_completion():
                self.log.error(
                    "Auxcopy job [%s] has failed with %s.", auxcopy_job.job_id, auxcopy_job.delay_reason)
                raise Exception(
                    "Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id, auxcopy_job.delay_reason))
            self.log.info("Auxcopy job [%s] has completed.", auxcopy_job.job_id)

            # Restore from non dedupe secondary copy
            self.client_machine.remove_directory(self.restore_dest_path)
            restore_job = sc1_obj.restore_out_of_place(self.client, self.restore_dest_path, [self.content_path],
                                                       copy_precedence=2)
            self.log.info("restore job [%s] has started from non dedupe secondary copy.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info("restore job [%s] has completed.", restore_job.job_id)
            self._restore_verify(self.client_machine, self.content_path, dest_path)

            # Restore dedupe secondary copy
            self.client_machine.remove_directory(self.restore_dest_path)
            restore_job = sc1_obj.restore_out_of_place(self.client, self.restore_dest_path, [self.content_path],
                                                       copy_precedence=3)
            self.log.info("restore job [%s] has started from dedupe secondary copy.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info("restore job [%s] has completed.", restore_job.job_id)
            self._restore_verify(self.client_machine, self.content_path, dest_path)

            # Run DataAging
            data_aging_job = self.commcell.run_data_aging(storage_policy_name=self.storage_policy_name,
                                                          is_granular=True, include_all_clients=True)
            self.log.info("Data Aging job [%s] has started.", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)

            # Prune Validation
            self.log.info("Pruning Validation Started.")
            self._validate_jobs_prune(job_copy_list)
            self.log.info("Pruning Validation completed successfully.")

        except Exception as exp:
            self.log.error('Failed to execute test case with error:%s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""
        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)

            self._cleanup()
            # Verify License released
            self._validate_license(False)
            # Uninstall MA Client.
            if self.commcell.clients.has_client(self.machine_name):
                client_obj = self.commcell.clients.get(self.machine_name)
                self.log.info("%s already installed", self.machine_name)
                self.install_helper.uninstall_client(delete_client=True, instance=client_obj.instance)
        else:
            self.log.error("Testcase shows failure in execution, not cleaning up the test environment ...")
