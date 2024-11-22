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

    configure_tc_environment()	--	Configure testcase environment - library (if required), storage policy,
                                    backupset, subclient

    modify_subclient_properties()	--	Modify subclient properties like number of streams and allow multiple
                                        data readers

    run_parallel_backups()		--	Run backups on all subclients in parallel

    get_reservation_ids()		--	Get reservation ID for give list of running jobs

    clean_test_environment()	--	Clean up test environment

Steps :
    Aim : Check Resource Manager functionality - Spill N Fill
    1. Create a Disk Library with 1 Mountpath from MA1
    2. Add another Mountpath to this library from MA2
    3. Configure Backupset/3 Subclients/Storage Policy
    4. Share Mountpath in RW mode
    5. Set Library Property to Spill n Fill
    6. Submit Backup jobs for all 3 subclients in parallel
    7. Get Reservation ID for jobs while they are running
    8. Get Mountpath ID for reservation IDs
    9. Verify that both the mountpaths are being used by backup jobs
    10. Verify that alternate reservation IDs are using same mountpaths
        Reservation id X has Mountpath Id A then Reservation id X+2 should have same MountPath ID


    Sample Input:
    	"54835": {
					"ClientName": "client name",
					"AgentName": "File System",
					"MediaAgentName": "ma name",
					"MediaAgent2Name" : "ma_name",
					"ma1_dedup_path" : "Path"
			}
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
        self.name = "Resource Manager Case : Spill N Fill feature"
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
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        optionobj = OptionsSelector(self.commcell)
        self.mahelper_obj = MMHelper(self)
        self.dedup_helper_obj = DedupeHelper(self)
        self.ma1_name = self.tcinputs.get('MediaAgentName')
        self.ma2_name = self.tcinputs.get('MediaAgent2Name')
        self.dedup_path = self.tcinputs.get('dedup_path')
        self.client_machine_obj = Machine(self.client)

        self.ma1_machine_obj = Machine(self.ma1_name, self.commcell)
        self.ma2_machine_obj = Machine(self.ma2_name, self.commcell)

        self.ma1_library_drive = optionobj.get_drive(self.ma1_machine_obj, 15)
        self.ma2_library_drive = optionobj.get_drive(self.ma2_machine_obj, 15)
        self.client_system_drive = optionobj.get_drive(self.client_machine_obj, 15)

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

        #Add Mountpath
        self.log.info("Adding Mountpath [%s] to Library [%s]", self.mountpath2, self.library_name)
        self.mahelper_obj.configure_disk_mount_path(self.disklib_obj, self.mountpath2, self.ma2_name)

        #Share Mountpath
        self.disklib_obj.share_mount_path(media_agent=self.ma1_name, library_name=self.library_name,
                                          mount_path=self.mountpath1, new_media_agent=self.ma2_name,
                                          new_mount_path=self.mountpath1)
        self.disklib_obj.share_mount_path(media_agent=self.ma2_name, library_name=self.library_name,
                                          mount_path=self.mountpath2, new_media_agent=self.ma1_name,
                                          new_mount_path=self.mountpath2)
        #Set Library Property : Spill_N_Fill
        self.log.info("Setting Library Property to Spill N Fill")
        self.disklib_obj.mountpath_usage = 'SPILL_AND_FILL'

        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.sp_obj = self.dedup_helper_obj.configure_dedupe_storage_policy(
            self.storage_policy_name, self.library_name, self.ma1_name, self.dedup_path)
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        for id in range(1, 4):
            content_path = self.client_machine_obj.join_path(self.content_path, str(id))
            if self.client_machine_obj.check_directory_exists(content_path):
                self.log.info("Deleting already existing content directory [%s]", content_path)
                self.client_machine_obj.remove_directory(content_path)
            self.client_machine_obj.create_directory(content_path)
            subclient_name = f"{self.subclient_name}_{id}"
            self.log.info("Configuring Subclient [%s_%s]", self.subclient_name, id)
            self.mahelper_obj.create_uncompressable_data(self.client.client_name, content_path, 1, 1)
            self.subclient_obj_list.append(self.mahelper_obj.configure_subclient(
                self.backupset_name, subclient_name, self.storage_policy_name, content_path))
            self.log.info("Successfully configured Subclient [%s]", self.subclient_name)

            self.log.info("Setting Number of Streams to 1 and Allow Multiple Data Readers to False")
            self.modify_subclient_properties(self.subclient_obj_list[-1], 1, False)

    def modify_subclient_properties(self, subclient_obj, num_streams=None, multiple_readers=None):
        """
        Modify subclient properties like number of streams and allow multiple data readers

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


    def run_parallel_backups(self):
        """
        Run backups on all subclients in parallel
        Return:
            Return list of job objects
        """
        job_list = []
        for num in range(1,4):
            job_list.append(self.subclient_obj_list[num-1].backup("Full"))

            self.log.info("Successfully initiated a FULL backup job on subclient [%s] with job id [%s]",
                          self.subclient_obj_list[num-1].subclient_name,
                          job_list[-1].job_id)
        return job_list

    def get_reservation_ids(self, job_list):
        """
        Get reservation ID for give list of running jobs
        """
        job_id_list = []

        for job_obj in job_list:
            job_id_list.append(str(job_obj.job_id))
        #wait for jobs to be in Backup Phase
        backup_in_progress = 0
        for _ in range(0, 40):
            for job_obj in job_list:
                if job_obj.phase.lower() == 'backup' and job_obj.status.lower() == 'running':
                    backup_in_progress+=1
            if backup_in_progress != 3:
                self.log.info("Jobs in Backup Phase = %s, checking again after 15 seconds if all jobs are "
                                  "in Backup Phase", backup_in_progress)
                backup_in_progress = 0
                time.sleep(15)
            else:
                self.log.info("All jobs are in Backup Phase. Moving on to CSDB validations")
                break

        query = "select JobId, ReservationId, MountpathId from RMReservations where JobId in " \
                f"({','.join(job_id_list)})"
        self.log.info("QUERY => %s", query)
        self.csdb.execute(query)
        reservation_id_mapping = self.csdb.fetch_all_rows()
        self.log.info("[JobId, ReservationId, MountPathID] ==> %s", str(reservation_id_mapping))
        reservation_id_list = []
        mountpath_id_list = []
        reservation_mountpath_dict = {}
        for item in reservation_id_mapping:
            reservation_mountpath_dict[item[1]] = item[2]
        for mp in reservation_id_mapping:
            mountpath_id_list.append(mp[2])
            reservation_id_list.append(mp[1])

        query = "select App_Client.name, MMDeviceController.folder from " \
                "MMDeviceController,MMMountPathToStorageDevice," \
                f"APP_Client where MMMountPathToStorageDevice.MountPathId in ({','.join(mountpath_id_list)})" \
                "and MMDeviceController.DeviceId = MMMountPathToStorageDevice.DeviceId and " \
                "MMDeviceController.folder != '' and App_Client.id in (MMDeviceController.ClientId)"
        self.log.info("QUERY => %s", query)
        self.csdb.execute(query)
        list_of_mountpaths = self.csdb.fetch_all_rows()
        self.log.info("List of Mount Paths used : %s", str(list_of_mountpaths))


        self.log.info("Let us wait for all jobs to complete")
        for job in job_list:
            if not job.wait_for_completion():
                raise Exception(f"Backup job [{job.job_id}] has not completed. Reason - {job.delay_reason}")
            self.log.info("Backup job [%s] completed successfully", job.job_id)

        #Find out how many times each mountpath was used
        mountpath_id_counts_list = [[x, mountpath_id_list.count(x)] for x in set(mountpath_id_list)]
        self.log.info("Here is the list of how many times a mount path was used : %s", mountpath_id_counts_list)
        if len(mountpath_id_counts_list) < 2:
            self.log.error("***FAILURE : Resource Manager allocated same mountpath even after setting "
                           "spill_n_fill policy on library .. Marking failure ...***")
            self.error_string += "\nTotal number of Mountpaths used by backup jobs = 1"
        if abs(mountpath_id_counts_list[0][1] - mountpath_id_counts_list[1][1]) != 1:
            self.log.error("***FAILURE : Resource manager did not allocate different mountpaths even after setting "
                           "spill_n_fill policy on library .. Marking failure ...***")
            self.error_string += "\nResource Manager did not allocate different mountpaths."

        self.log.info("***SUCCESS : Resource manager correctly allocated each data path at least once during backups "
                      "after setting spill_n_fill policy .. Marking success ..***")

        reservation_id_list.sort()

        even_job_mpid = reservation_mountpath_dict[reservation_id_list[0]]
        odd_job_mpid = reservation_mountpath_dict[reservation_id_list[1]]
        next_even_job_mpid = reservation_mountpath_dict[reservation_id_list[2]]
        self.log.info("even_job_mpid = [%s], odd_job_mpid = [%s], next_even_job_mpid = [%s]", even_job_mpid,
                      odd_job_mpid, next_even_job_mpid)
        if even_job_mpid != next_even_job_mpid:
            self.error_string += "\nConsecutive Even Numbers Reservation IDs have not used same Mount Path"
            self.log.error("***FAILURE : Resource Manager did not allocate same mpid to two even numbered jobs")
        else:
            self.log.info("\nConsecutive Even Numbers Reservation IDs have used same Mount Path [%s]", even_job_mpid)

        if even_job_mpid == odd_job_mpid:
            self.error_string += "***FAILURE : The mountpath id for odd numbered reservation id in the list matches " \
                                 "with the even numbered job which is not expected. "
            self.log.error("***FAILURE : Resource Manager allocated same Mount Path [%s] to odd & even Jobs",
                           even_job_mpid)

        else:
            self.log.info("***SUCCESS : As expected, the mountpath id for this odd numbered reservation id in the list"
                          " is not same as even numbered job in the list")

    def clean_test_environment(self):
        """
        Clean up test environment
        """
        for id in range(1, 4):
            content_path = self.client_machine_obj.join_path(self.content_path, str(id))
            if self.client_machine_obj.check_directory_exists(content_path):
                self.log.info("Deleting already existing content directory [%s]", content_path)
                self.client_machine_obj.remove_directory(content_path)
        try:
            self.log.info("Deleting BackupSet")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
        except Exception as excp:
            self.log.info("***Failure in deleting backupset during cleanup. "
                          "Treating as soft failure as backupset will be reused***")
        try:
            self.log.info("Deleting Storage Policy")
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                sp_obj = self.commcell.storage_policies.get(self.storage_policy_name)
                sp_obj.reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)

        except Exception as excp:
            self.log.info("***Failure in deleting storage policy during cleanup. "
                          "Treating as soft failure as stroage policy will be reused***")
        try:
            self.log.info("Deleting Library")
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
        except Exception as excp:
            self.log.info("***Failure in deleting library during cleanup. "
                          "Treating as soft failure as library will be reused***")

    def run(self):
        """Run function of this test case"""
        try:
            self.clean_test_environment()
            self.configure_tc_environment()
            job_list = self.run_parallel_backups()
            self.get_reservation_ids(job_list)

            if not self.error_string:
                self.log.info("SUCCESS : Test case completed successfully")
            else:
                self.log.error("FAILURE : %s", self.error_string)
                raise Exception(self.error_string)
        except Exception as exp:
            self.status = constants.FAILED
            self.error_string = str(exp)
            self.log.error('Failed to execute test case with error: %s', (str(exp)))

    def tear_down(self):
        """Tear down function of this test case"""
        # Unconditional cleanup
        try:
            self.log.info("Cleaning up Tescase Environment")
            self.clean_test_environment()
        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)
