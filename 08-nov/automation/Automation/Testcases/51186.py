# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    run_backups()   --  run backups on first set of subclients

    configure_tc_environment()	--	Configure testcase environment - library (if required), storage policy,
                                    backupset, subclient

    modify_subclient_properties()	--	Modify subclient properties like number of streams and allow multiple
                                        data readers

    run_backup_add_mountpath()	--	Runs a backup and adds a mountpath in parallel

    run_backups()			--	Run backups on first 2 subclients

    get_reservation_ids()		--	Get reservation ID for give list of running jobs

    run_restore_validations()	--	run restore job for the subclient and validate correct volumes were mounted on MAs

    validate_backup_pending()	--	Validate that backup is in Pending

    _get_drivepoolid_for_job()  --  Get drive pool id for given job

    _set_device_access_type_to_rw()  --  Set device access type to read/write for provided library

    validate_round_robin_feature()  -- run backups and validate Preferred Datapath and Round-Robin features



Steps :
    Aim : Check Resource Manager functionality - Fill N Spill
    1. Create a Disk Library with 1 Mountpath from MA1
    2. Configure Backupset/3 Subclients/Storage Policy, set compression = Off on subclients
    3. Check total size of Mountpath and set Reserve Space to current size - 4 GB
    4. Set Library Property to Fill n Spill
    5. Generate 600 MB, 1200 MB and 3900 MB data for 3 subclients
    6. Submit Backup jobs for first 2 subclients one after the other
    7. Submit Backup job for third subclient and when the backup job is in Backup Phase, add+share new mountpath and
        also add new datapath to copy.
    8. Wait for job to go to PENDING state
    9. Resume the pending job and wait till its complete.
    7. Get Reservation ID + Volume ID + Mountpath ID for job and confirm that it has used 2 different mountpaths
    8. Start Restore
    9. Verify that restore completes and data validation succeeds
    10. Set reserve space back to default of 2 GB
    11. Set device access type to read/write
    12. Run 2 backups sequentially and check drive pool ids to verify Preferred datapath selection
    13. Drive pool ids must be the same
    14. Run 3 backups simultaneously to verify round-robin feature
    15. Drive pool ids for one of the jobs must be different


    Sample Input:
    	"51186": {
				  "ClientName": "client name",
                  "AgentName": "File System",
                  "MediaAgentName": "ma name",
                  "MediaAgent2Name": "ma name",
                  "SQLUser": "sql username",
                  "SQLPassword": "sql password"
                  "dedup_path" : "Path"
			}
		dedup_path is optional parameter - to be provided if MediaAgentName is Linux Media Agent.
		Note: Client should be different from both MAs for verifying RR feature
"""
import time
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Resource Manager Case : Fill N Spill, Preferred Datapath and Round-Robin Features"
        self.tcinputs = {
            "MediaAgentName": None,
            "MediaAgent2Name": None
        }
        self.error_string = ""
        self.library_name = None
        self.library_name = None
        self.mountpath = None
        self.ma1_name = None
        self.ma2_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mahelper_obj = None
        self.disklib_obj = None
        self.client_machine_obj = None
        self.ma1_machine_obj = None
        self.ma2_machine_obj = None
        self.ma_library_drive = None
        self.dedup_path = None
        self.content_path = None
        self.subclient_obj_list = []
        self.bkpset_obj = None
        self.sp_obj = None
        self.client_system_drive = None
        self.dedup_helper_obj = None
        self.backup_job_list = []
        self.mountpath1 = None
        self.mountpath2 = None
        self.ma1_library_drive = None
        self.ma2_library_drive = None
        self.restore_path = None
        self.drive_poolid_list = []
        self.sql_user = None
        self.sql_pwd = None
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        optionobj = OptionsSelector(self.commcell)
        self.mahelper_obj = MMHelper(self)
        self.dedup_helper_obj = DedupeHelper(self)
        self.ma1_name = self.tcinputs.get('MediaAgentName')
        self.ma2_name = self.tcinputs.get('MediaAgent2Name')
        self.dedup_path = self.tcinputs.get('dedup_path')
        self.sql_user = self.tcinputs.get('SQLUser')
        self.sql_pwd = self.tcinputs.get('SQLPassword')
        self.client_machine_obj = Machine(self.client)

        self.ma1_machine_obj = Machine(self.ma1_name, self.commcell)
        self.ma2_machine_obj = Machine(self.ma2_name, self.commcell)

        self.ma1_library_drive = optionobj.get_drive(self.ma1_machine_obj, 25)
        self.ma2_library_drive = optionobj.get_drive(self.ma2_machine_obj, 25)
        self.client_system_drive = optionobj.get_drive(self.client_machine_obj, 40)

        if not self.dedup_path and "unix" in self.ma1_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")

        if not self.dedup_path:
            self.dedup_path = self.ma1_machine_obj.join_path(self.ma1_library_drive, self.id, "DDB")

        self.library_name = f"Lib_TC_{self.id}"
        self.mountpath1 = self.ma1_machine_obj.join_path(self.ma1_library_drive, self.id, "LIB_MP1")
        self.mountpath2 = self.ma2_machine_obj.join_path(self.ma2_library_drive, self.id, "LIB_MP2")

        self.storage_policy_name = f"SP_TC_{self.id}"
        self.backupset_name = f"BkpSet_TC_{self.id}"
        self.subclient_name = f"Subc_TC__{self.id}"
        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, str(self.id))
        self.restore_path = self.client_machine_obj.join_path(self.content_path, "restore_path")

    def configure_tc_environment(self):
        """
        Configure testcase environment - library (if required), storage policy, backupset, subclient
        """
        self.log.info("===STEP: Configuring TC Environment===")


        if not self.ma1_machine_obj.check_directory_exists(self.mountpath1):
            self.log.info("Creating mountpath directory [%s]", self.mountpath1)
            self.ma1_machine_obj.create_directory(self.mountpath1)

        self.log.info("Creating Library [%s] with Mountpath [%s]", self.library_name, self.mountpath1)
        self.disklib_obj = self.mahelper_obj.configure_disk_library(self.library_name, self.ma1_name, self.mountpath1)
        self.log.info("Library [%s] created successfully.", self.library_name)

        #Set Library Property : Spill_N_Fill
        self.log.info("Setting Library Property to Spill N Fill")
        self.disklib_obj.mountpath_usage = 'FILL_AND_SPILL'

        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.sp_obj = self.dedup_helper_obj.configure_dedupe_storage_policy(
            self.storage_policy_name, self.library_name, self.ma1_name, self.dedup_path)
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        space_constant = 6
        data_size = 0
        for id in range(1, 4):
            content_path = self.client_machine_obj.join_path(self.content_path, str(id))
            if self.client_machine_obj.check_directory_exists(content_path):
                self.log.info("Deleting already existing content directory [%s]", content_path)
                self.client_machine_obj.remove_directory(content_path)
            self.client_machine_obj.create_directory(content_path)
            subclient_name = f"{self.subclient_name}_{id}"
            self.log.info("Configuring Subclient [%s_%s]", self.subclient_name, id)
            if id == 1:
                data_size = float(space_constant * 0.2)
            elif id == 2:
                data_size = float(space_constant * 0.1)
            else:
                data_size = float(space_constant * 3.0)
            self.log.info("Creating %s GB data as content", data_size)
            self.mahelper_obj.create_uncompressable_data(self.client.client_name, content_path, data_size, 1)
            self.subclient_obj_list.append(self.mahelper_obj.configure_subclient(
                self.backupset_name, subclient_name, self.storage_policy_name, content_path))
            self.log.info("Successfully configured Subclient [%s]", self.subclient_name)

            self.log.info("Setting Number of Streams to 1, compression=OFF and Allow Multiple Data Readers to False")
            self.modify_subclient_properties(self.subclient_obj_list[-1], 1, False)
            if self.client_machine_obj.check_directory_exists(self.restore_path):
                self.log.info("Deleting already existing restore directory [%s]", self.restore_path)
                self.client_machine_obj.remove_directory(self.restore_path)
            self.client_machine_obj.create_directory(self.restore_path)

        # Sleep for 5 mins
        time.sleep(300)
        self.log.info("Getting reserve space on Mountpath [%s]", self.mountpath1)
        # Set free space limit on MP
        self.log.info("Firing query to determine the total size of mount path %s", self.mountpath1)
        query = "select MMMediaSide.FreeBytesMB from MMMediaSide, MMMountPath where " \
                f"MMMountPath.LibraryId={self.disklib_obj.library_id} and " \
                "MMMountPath.MediaSideId = MMMediaSide.MediaSideId"
        self.log.info("QUERY ==> %s", query)
        self.csdb.execute(query)
        mp_size = int(self.csdb.fetch_one_row()[0])
        self.log.info("Current size of Mountpath [%s] is [%s] MB", self.mountpath1, mp_size)
        self.log.info("Setting Reserved Space on Mountpath [%s] to [%s - 10240 ] MB", self.mountpath1, mp_size)
        self.disklib_obj.set_mountpath_reserve_space(self.mountpath1, mp_size - 10240)
        self.log.info("Successfully set Reserved space on [%s] to [%s]", self.mountpath1, mp_size - 10240)

    def modify_subclient_properties(self, subclient_obj, num_streams=None, multiple_readers=None):
        """
        Modify subclient properties like number of streams and allow multiple data readers"

        Args:
            subclient_obj (object) - Subclient Object
            num_streams (int) - Number of streams
            multiple_readers(boolean) - Boolean value for setting multiple data readers value

        """
        if num_streams is not None:
            self.log.info("Setting number of streams to [%s]", num_streams)
            subclient_obj.data_readers = num_streams
        if multiple_readers is not None:
            self.log.info("Setting multiple data readers to [%s]", multiple_readers)
            subclient_obj.allow_multiple_readers = multiple_readers

    def run_backups(self, num_jobs):
        """
        Run backups on subclients based on number of jobs required
        param:
            num_jobs (int)  : number of backup jobs to run
        """
        for num in range(1, num_jobs + 1):
            self.backup_job_list.append(self.subclient_obj_list[num - 1].backup("Full"))

            self.log.info("Successfully initiated a FULL backup job on subclient [%s] with job id [%s]",
                          self.subclient_obj_list[num - 1].subclient_name,
                          self.backup_job_list[-1].job_id)
            if not self.backup_job_list[-1].wait_for_completion():
                raise Exception("Failed to run backup job with error: {0}".format(
                    self.backup_job_list[-1].delay_reason))
            self.log.info("Backup job: %s completed successfully", self.backup_job_list[-1].job_id)

    def run_backup_add_mountpath(self):
        """
        Runs a backup and adds a mountpath in parallel
        """
        self.backup_job_list.append(self.subclient_obj_list[-1].backup("FULL"))
        # When backup is in "Backup" phase, add new mountpath
        current_job = self.backup_job_list[-1]
        wait_time = 0
        while current_job.phase != "Backup":
            self.log.info("Waiting for backup job to get into Backup phase. Waiting Since : %s seconds", wait_time)
            time.sleep(15)
            wait_time += 15
            if wait_time > 600:
                self.log.error("Backup job has still not entered Backup Phase after %s seconds.", wait_time)
                raise Exception("Job could not enter Backup phase within 10 minutes timeout period")
        self.log.info("Backup job [%s] is in Backup Phase now", current_job.job_id)
        self.log.info("Waiting for job to enter Running state in Backup Phase")
        wait_time = 0
        while current_job.status != "Running":
            self.log.info("Waiting for backup job to get into Running Status. Waiting Since : %s seconds", wait_time)
            time.sleep(15)
            wait_time += 15
            if wait_time > 600:
                self.log.error("Backup job has still not entered Running status after %s seconds.", wait_time)
                raise Exception("Job could not enter Running Status within 10 minutes timeout period")

        self.log.info("Backup job [%s] is now [Running] in [Backup] Phase", current_job.job_id)
        self.log.info("Adding new Mountpath to library as job is in Backup Phase")

        # Add Mountpath
        self.log.info("Adding Mountpath [%s] to Library [%s]", self.mountpath2, self.library_name)
        self.mahelper_obj.configure_disk_mount_path(self.disklib_obj, self.mountpath2, self.ma2_name)

        # Share Mountpath
        self.disklib_obj.share_mount_path(media_agent=self.ma1_name, library_name=self.library_name,
                                          mount_path=self.mountpath1, new_media_agent=self.ma2_name,
                                          new_mount_path=self.mountpath1, access_type=20)
        self.disklib_obj.share_mount_path(media_agent=self.ma2_name, library_name=self.library_name,
                                          mount_path=self.mountpath2, new_media_agent=self.ma1_name,
                                          new_mount_path=self.mountpath2, access_type=20)

    def get_reservation_ids(self):
        """
        Get reservation ID for give list of running jobs
        """
        current_job = self.backup_job_list[-1]

        query = f"select ReservationId, MountpathId, VolumeId, ClientId from RMReservations where JobId = " \
                f"{current_job.job_id}"
        self.log.info("QUERY => %s", query)
        self.csdb.execute(query)
        reservation_id_mapping = self.csdb.fetch_all_rows()
        self.log.info("[ReservationId, MountpathId, VolumeId] ==> %s", str(reservation_id_mapping))

        if len(reservation_id_mapping) != 2:
            self.log.error("***FAILURE : The job did not consume 2 different resources (mountpaths) as expected. "
                           "Returning error...")
            raise Exception("The job did not consume 2 different resources (mountpaths) as expected")
        self.log.info("The job did use 2 different resources(mountpaths) as expected. "
                      "Now will make sure that those are 2 unique resources...")

        if reservation_id_mapping[0][1] == reservation_id_mapping[1][1]:
            self.log.info("***FAILURE : Both the mount paths look the same, erroring out ...")
            raise Exception("The job did not use 2 different mountpath as expected.")
        self.log.info("Both mount paths are different as expected. Declaring success...")

        return reservation_id_mapping

    def clean_test_environment(self):
        """
        Clean up test environment
        """
        for id in range(1, 4):
            content_path = self.client_machine_obj.join_path(self.content_path, str(id))
            if self.client_machine_obj.check_directory_exists(content_path):
                self.log.info("Deleting already existing content directory [%s]", content_path)
                self.client_machine_obj.remove_directory(content_path)
        if self.client_machine_obj.check_directory_exists(self.restore_path):
            self.log.info("Deleting already existing content directory [%s]", self.restore_path)
            self.client_machine_obj.remove_directory(self.restore_path)
        try:
            self.log.info("Deleting BackupSet")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)

            self.log.info("Deleting Storage Policy")
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                sp_obj = self.commcell.storage_policies.get(self.storage_policy_name)
                sp_obj.reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)

            self.log.info("Deleting Library")
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
        except Exception as excp:
            self.log.info(f"***Failure in Cleanup with error {excp}***")

    def run_restore_validations(self, reservation_id_mapping):
        """
        run restore job for the subclient and validate correct volumes were mounted on MAs

        Args:
        reservation_id_mapping(list) - List returned by get_reservation_ids

        """
        self.log.info("starting restore job...")
        job = self.subclient_obj_list[-1].restore_out_of_place(self.client.client_name, self.restore_path,
                                                               [self.client_machine_obj.join_path(self.content_path,
                                                                                                  str(3))])
        if not job.wait_for_completion():
            raise Exception("Failed to run restore job with error: {0}".format(job.delay_reason))
        self.log.info("restore job: %s completed successfully", job.job_id)

        #Compare data
        self.log.info("Performing data comparison between source & destination MAs")
        diff_files = self.client_machine_obj.compare_folders(self.client_machine_obj,
                                                             self.client_machine_obj.join_path(self.content_path,
                                                                                               str(3)),
                                                             self.client_machine_obj.join_path(self.restore_path,
                                                                                               str(3)))

        if not diff_files:
            self.log.info("Restore validation successful")
        else:
            self.log.error("Restore Validation Failed : Diff = %s", str(diff_files))
            raise Exception("Checksum Validation after restore failed for Backup which used 2 resources (mountpaths)")
        # Due to Dataserver IP, one won't know which MA will do the reads.

    def validate_backup_waiting(self):
        """
        Validate that backup is in Pending
        """
        current_job = self.backup_job_list[-1]

        self.log.info("Wait till job completes.")
        wait_time = 0
        while current_job.status != "Waiting":
            self.log.info("Waiting for backup job to get into Waiting state. Waiting Since : %s seconds", wait_time)
            time.sleep(1)
            wait_time += 1
            if wait_time > 300:
                self.log.error("Backup job has still not entered Waitng state after %s seconds.", wait_time)
                raise Exception("Job could not enter Waiting state within 5 minutes timeout period")
        self.log.info("Backup job has entered Waitng state as expected")
        if not current_job.wait_for_completion(return_timeout=15):
            raise Exception(f"Failed to run Backup job with error: {current_job.delay_reason}")
        self.log.info("Backup job completed successfully.")
        self.log.info("SPILL N FILL FEATURE VALIDATED SUCCESSFULLY")

    def _get_drivepoolid_for_job(self, jobid):
        """
        Query CSDB to get drivepool id corresponding to job
        :param
            jobid (int) : jobid to get associated drivepool id
        :return:
            drivepool id (string)
        """
        query = f"""SELECT drivePoolId
                    FROM archfilecopy
                    WHERE archfileid in
                    (SELECT archfileid
                    FROM archchunkmapping
                    WHERE jobid = {jobid})"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)

        return self.csdb.fetch_one_row()

    def _set_device_access_type_to_rw(self, lib):
        """
        Method to set device access type of data server ip mount paths of a lib to r/w
        :param
            lib (string): library alias name
        """
        query = f"""Update mmdevicecontroller set DeviceAccessType = 22
                    WHERE deviceid in
                     (SELECT DISTINCT MMDC.DeviceId from MMDeviceController MMDC
                     JOIN MMMountPathToStorageDevice MMSD
                     ON MMDC.DeviceId = MMSD.DeviceId
                     JOIN MMMountPath MMP
                     ON MMSD.MountPathId = MMP.MountPathId
                     JOIN MMLibrary ML
                     ON ML.LibraryId = MMP.LibraryId
                     WHERE ML.Aliasname = '{lib}')
                     AND DeviceAccessType = 20"""

        self.log.info("QUERY: %s", query)
        self.mahelper_obj.execute_update_query(query, self.sql_pwd, self.sql_user)

    def _verify_drivepool_selection_sequence(self):
        """
        Methode to verify drive pool selection for round robin
        """
        if self.drive_poolid_list[0] == self.drive_poolid_list[1] == self.drive_poolid_list[2]:
            return False

        return True

    def _wait_for_jobs_completion(self, job_list):
        """
        Wait for jobs in jobs kist to be completed
        """
        self.log.info("Waiting for jobs to complete")
        for job in job_list:
            if not job.wait_for_completion():
                self.log.error('Error: Job(Id: %s) Failed', job.job_id)
        self.log.info('Jobs Completed')

    def validate_round_robin_feature(self):
        """
        Validate round robin selection of mountpaths
        """
        self.log.info("Validating Preferred Datapath and Round Robin Features")
        self.log.info("Setting reserve space for MP1 back to min value")
        self.disklib_obj.set_mountpath_reserve_space(self.mountpath1, 2048)
        self.log.info("Setting device access type to mountpaths to Read/Write")
        self._set_device_access_type_to_rw(self.library_name)
        # sleep for 5 mins
        time.sleep(300)
        self.log.info("Running 2 more backups to check MP selection for Preferred Data Path")
        self.run_backups(2)
        for i in range(1, 3):
            self.drive_poolid_list.append(self._get_drivepoolid_for_job(self.backup_job_list[-i].job_id))
            self.log.info(
                f"Drive pool id for Pref Data Path job {i} [id: {self.backup_job_list[-i].job_id}] is"
                f" {self.drive_poolid_list[-1]}")

        if self.drive_poolid_list[0] == self.drive_poolid_list[1]:
            self.log.info("Sucessfully Validated Preferred datapath selection")
        else:
            self.log.error("Error: data paths not same as expected with preferred datapath selection")
            raise Exception("Preferred datapath Validation Failed")

        self.log.info("Running 3 more backups from backupset level to validate Round-Robin MP selection")
        self.bkpset_obj.subclients.refresh()
        job_list = self.bkpset_obj.backup(backup_level="Full")
        self._wait_for_jobs_completion(job_list)
        # clear drive pool list
        self.drive_poolid_list = []
        for index in range(0, 3):
            self.drive_poolid_list.append(self._get_drivepoolid_for_job(job_list[index].job_id))
            self.log.info(f"Drive pool id for RR job {index} [id: {job_list[index].job_id}] is"
                          f" {self.drive_poolid_list[-1]}")

        if self._verify_drivepool_selection_sequence():
            self.log.info("Sucessfully Validated Round Robin selection")
        else:
            self.log.error("Error: data paths not alternating as expected with round-robin")
            raise Exception("Round Robin Validation Failed")

    def run(self):
        """Run function of this test case"""
        try:
            self.clean_test_environment()
            self.configure_tc_environment()
            self.run_backups(2)
            self.run_backup_add_mountpath()
            self.validate_backup_waiting()
            reservation_id_mapping = self.get_reservation_ids()
            self.run_restore_validations(reservation_id_mapping)
            self.validate_round_robin_feature()

        except Exception as exp:
            self.error_string = str(exp)
            self.log.error('Failed to execute test case with error: %s', (str(exp)))
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        # Unconditional cleanup
        try:
            self.log.info("Cleaning up Tescase Environment")
            self.clean_test_environment()
        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)
