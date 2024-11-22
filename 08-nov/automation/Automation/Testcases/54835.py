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

Steps :
    Aim : TC should be able to run on all types of libraries and for target number of volumes [ eg. 1000 ]
    1. Configure test environment - Library (if not given), Dedup Storage Policy, Backupset and Subclient
    2. Set subclient properties to use 4 streams, start new media & mark Media Full on Success.
    3. Generate different sized content from 1 GB to 5 GB for each of the 3 iterations of backups and run backups.
    4. Reset start new media & mark Media Full on Success and run 2 more jobs with content size from 2 GB to 5 GB
    5. Get a list of all volumes and verify RMSpareStatusUpdateTime is 24 hours ahead
    6. Fetch physical size of each volume
    7. Modify RMSpareStatusUpdateTime to current time - 86400
    8. Modify MM Admin Thread time to 5 mins and wait for MM thread invocation to happen
    9. Verify MM logs have volume update logs for each of the volumes
    10. Verify volume size is updated in MMVolume table
    11. Validate physical volume size fetched in earlier step matches with size in MMVolume table
    12. Verify that RMSpareStatusUpdateTime for all the volumes gets updated to -1

    Sample Input:
    	"54835": {
					"ClientName": "client name",
					"AgentName": "File System",
					"MediaAgentName": "ma name",
					"ExistingLibraryName": "library name",
					"ExistingStoragePolicyName": "None"
			}
	Please make sure that MediaAgentName is a datamover MA for ExistingLibraryName.
	Possible Combinations for (ExistingLibraryName, ExistingStoragePolicyName) tuple are
	i.  (None, None) => Both will be created & deleted at the end of successful execution
	ii. (LibraryName, None) => New SP will be created using LibraryName, only new SP will be deleted at the
	    end of successfull execution
	iii. (None, StoragePolicyName) => StoragePolicy will be used, no entities will be delted at the end of
	    successful execution
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
        self.name = "volume size update: backup scenario"
        self.tcinputs = {
            "MediaAgentName": None,
            "ExistingLibraryName": None,
            "ExistingStoragePolicyName": None
        }
        self.library_name = None
        self.mountpath = None
        self.ma_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mahelper_obj = None
        self.client_machine_obj = None
        self.ma_machine_obj = None
        self.ma_library_drive = None
        self.dedup_path = None
        self.content_path = None
        self.subclient_obj = None
        self.bkpset_obj = None
        self.sp_obj = None
        self.client_system_drive = None
        self.dedup_helper_obj = None
        self.backup_job_list = []
        self.volumes_list = []
        self.volume_physical_size_dict = {}
        self.mm_admin_thread = None
        self.volume_update_interval = None
        self.user_lib = False
        self.user_sp = False
        self.is_user_defined_dedup = False
        self.optionobj = None

    def setup(self):
        """Setup function of this test case"""
        self.optionobj = OptionsSelector(self.commcell)
        self.library_name = self.tcinputs['ExistingLibraryName']
        self.ma_name = self.tcinputs['MediaAgentName']
        self.storage_policy_name = self.tcinputs['ExistingStoragePolicyName']

        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 15)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 15)

        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.library_name.lower() != "none":
            self.user_lib = True

        if self.storage_policy_name.lower() != "none":
            self.user_sp = True

        timestamp_suffix = OptionsSelector.get_custom_str()


        if not self.user_lib  and not self.user_sp:
            self.library_name = f"Lib_TC_{self.id}_{self.ma_name}"
            self.log.info("No library name provided, new library [%s] will be created", self.library_name)
            self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, self.id)


        if not self.user_sp:
            self.storage_policy_name = f"SP_TC_{self.id}_{self.ma_name}"
            if not self.is_user_defined_dedup:
                self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, "DDBs",
                                                            "TC%s_%s" % (self.id, timestamp_suffix))
            else:
                self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs["dedup_path"], self.id)

        else:
            self.log.info("Storage Policy Name %s given. If it exists, it will be reused.", self.storage_policy_name)
            if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.error("Existing Storage Policy Name provided by user does not exist. Treating as "
                               "configuration error and exiting...")
                raise Exception("User provided storage policy [%s] does not exist, please correct the "
                                "inputs/configuration and re-run the testcase.")

        self.backupset_name = f"BkpSet_TC_{self.id}_{self.ma_name}"
        self.subclient_name = f"Subc_TC_{self.id}_{self.ma_name}"
        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, self.id)


    def configure_tc_environment(self):
        """
        Configure testcase environment - library (if required), storage policy, backupset, subclient
        """
        self.log.info("===STEP: Configuring TC Environment===")
        self.get_mm_admin_thread_frequency()
        self.mahelper_obj = MMHelper(self)
        self.dedup_helper_obj = DedupeHelper(self)
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", self.content_path)
            self.client_machine_obj.remove_directory(self.content_path)
        self.client_machine_obj.create_directory(self.content_path)

        if not self.user_lib and not self.user_sp:
            if not self.ma_machine_obj.check_directory_exists(self.mountpath):
                self.log.info("Creating mountpath directory [%s]", self.mountpath)
                self.ma_machine_obj.create_directory(self.mountpath)
            self.log.info("Creating Library [%s]", self.library_name)
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.log.info("Library [%s] already exists. Reusing the Library.", self.library_name)
            else:
                self.mahelper_obj.configure_disk_library(self.library_name, self.ma_name, self.mountpath)
                self.log.info("Library [%s] created successfully.", self.library_name)
        else:
            if self.user_lib:
                self.log.info("Skipping Library creation as user has provided Library [%s]", self.library_name)
                self.log.info("Checking if user provided Library exists")
                if not self.commcell.disk_libraries.has_library(self.library_name):
                    self.log.error("User Provided Library does not exist. Erroring out.")
                    raise Exception("User Provided Library [%s] does not exist. Please provide correct library name"%
                                    self.library_name)

        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.sp_obj = self.dedup_helper_obj.configure_dedupe_storage_policy(
            self.storage_policy_name, self.library_name, self.ma_name, self.dedup_path)
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        self.log.info("Configuring Subclient [%s]", self.subclient_name)
        self.subclient_obj = self.mahelper_obj.configure_subclient(self.backupset_name, self.subclient_name,
                                                                   self.storage_policy_name, self.content_path)
        self.log.info("Successfully configured Subclient [%s]", self.subclient_name)

        self.log.info("Setting Number of Streams to 4 and Allow Multiple Data Readers to True")
        self.modify_subclient_properties(10, True)

    def modify_subclient_properties(self, num_streams=None, multiple_readers=None):
        """
        Modify subclient properties like number of streams and allow multiple data readers"

        Args:
            num_streams (int) - Number of streams
            multiple_readers(boolean) - Boolean value for setting multiple data readers value

        """
        if num_streams is not None:
            self.log.info("Setting number of streams to [%s]", num_streams)
            self.subclient_obj.data_readers = num_streams
        if multiple_readers is not None:
            self.log.info("Setting multiple data readers to [%s]", multiple_readers)
            self.subclient_obj.allow_multiple_readers = multiple_readers

    def generate_data_run_backup(self, size_in_gb, backup_type="Incremental", mark_media_full=False):
        """
        Generate subclient content and run given type of backup on subclient
        Args:
            size_in_gb (int)      -- Content Size in GB
            backup_type (str)     -- Backup Type [ Full or Incremental etc. ]
            mark_media_full(bool) -- Boolean Flag to decide if volumes are to be marked full after backup completion
        Return:
            Returns job object
        """
        self.log.info("Generating content of size [%s] at location [%s]", size_in_gb, self.content_path)
        self.mahelper_obj.create_uncompressable_data(self.client.client_name, self.content_path, size_in_gb, 1)
        if mark_media_full:
            job_obj = self.subclient_obj.backup(backup_type, advanced_options={'mediaOpt': {'startNewMedia': True}})
        else:
            job_obj = self.subclient_obj.backup(backup_type)

        self.log.info("Successfully initiated a [%s] backup job on subclient with jobid [%s]", backup_type,
                      job_obj.job_id)
        if not job_obj.wait_for_completion():
            raise Exception("Backup job [%s] did not complete in given timeout" % job_obj.job_id)

        self.log.info("Successfully completed the backup job with jobid [%s]", job_obj.job_id)
        self.backup_job_list.append(job_obj)

    def get_volumes_for_jobs(self):
        """
        Populates volumes to which list of jobs have written their chunks
        """
        jobs_list = [job.job_id for job in self.backup_job_list]
        job_ids = ','.join(jobs_list)
        self.log.info("Fetching volumes to which following jobs have written chunks - [%s]", job_ids)
        query = "select volumeid from mmvolume where volumeid in (" \
                "select volumeid from archchunk where id in (" \
                "select archchunkid from archchunkmapping where jobid in (" \
                "%s)))"%job_ids
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        volumes_list = self.csdb.fetch_all_rows()
        self.log.info(volumes_list)
        self.volumes_list = [v[0] for v in volumes_list]
        self.log.info("List of volumes fetched from CSDB - [%s]", str(self.volumes_list))

    def get_volume_update_time(self, volume_list):
        """
        Returns value in RMSpareStatusUpdateTime column against each volume provided in list
        Args:
            volume_list (List Obj) - List of volume IDs
        Return:
            A dictionary having RMSpareStatusUpdateTime for each volume
        """
        self.log.info("Fetching RMSpareStatusUpdateTime for following volumes - [%s]", str(volume_list))
        query = "select volumeid, RMSpareStatusUpdateTime from mmvolume where volumeid in (%s)"%','.join(volume_list)
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        update_time_list = self.csdb.fetch_all_rows()
        self.log.info("RMSpareStatusUpdateTime for volumes - [%s]", update_time_list)
        return dict(update_time_list)


    def set_volume_update_time(self, volume_list, time_to_set):
        """
        Sets value of RMSpareStatusUpdateTime to given time for each volume in the list

        Args:
            volume_list (List)  :   List of volume IDs
            time_to_set (int)   :   Time value to set in the RMSpareStatusUpdateTime column
        """
        operation = '+'
        if time_to_set < 0:
            operation = '-'
        self.log.info("Setting RMSpareStatusUpdateTime to [%s] for following volumes - [%s]",
                      time_to_set, str(volume_list))
        query = "update mmvolume set RMSpareStatusUpdateTime = RMSPareStatusUpdateTime %s %s where volumeid in (%s) and RMSpareStatusUpdateTime <> -1"%\
                (operation, abs(time_to_set), ','.join(volume_list))
        self.log.info("Query => %s", query)
        self.optionobj.update_commserve_db(query)
        self.log.info("RMSpareStatusUpdateTime updated to [%s]", time_to_set)

    def get_volume_physical_size(self, volume_list):
        """
        Get physical size of each volume from mountpath
        Args:
            volume_list (List) : List of volume IDs

        Return:
            Dictionary containing volume and its physical size on disk
        """
        #Get physical location of the volume
        volume_path_dict = {}
        volume_physical_size_dict = {}
        ma_name_obj_dict = {}
        self.log.info("Fetching physical location of volumes in volume list : [%s]", volume_list)
        query = "select MMV.volumeid, MMDC.folder, MNTPATH.MountPathName, CL.name " \
                "from MMMountpath MNTPATH, MMDeviceController MMDC, MMMountPathToStorageDevice MMPS, MMVOLUME MMV " \
                ", App_Client CL where MMPS.MountPathId = MMV.CurrMountPathId and " \
                "MNTPATH.MountPathId = MMV.CurrMountPathId and CL.id = MMDC.clientid " \
                " and MMDC.deviceid = MMPS.DeviceId and MMV.volumeid in (%s)"%','.join(volume_list)
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        #Now work out the path for each of the volume and fetch its size
        physical_location_list = self.csdb.fetch_all_rows()
        self.log.info(physical_location_list)
        #volumeid	folder	    MountPathName	        client
        #111799	    C:\\54835	R3BGE3_07.01.2020_04.55	winma1pdcauto

        for (volumeid, folder, mountpath, clientname) in physical_location_list:
            volume_path_dict[volumeid] = "%s%s%s%s%s%sV_%s"%(folder, self.ma_machine_obj.os_sep, mountpath,
                                                             self.ma_machine_obj.os_sep, "CV_MAGNETIC",
                                                             self.ma_machine_obj.os_sep, volumeid)
            self.log.info("Fetching physical size of volume [%s] from location - [%s]", volumeid,
                          volume_path_dict[volumeid])

            #Create machine object of MA and store in dictionary as we may need it many times
            if clientname not in ma_name_obj_dict:
                ma_name_obj_dict[clientname] = Machine(clientname, self.commcell)

            #Get physical size in bytes
            volume_physical_size_dict[volumeid] = round(ma_name_obj_dict[clientname].get_folder_size(
                volume_path_dict[volumeid]))

        return volume_physical_size_dict

    def get_volume_csdb_size(self, volume_list):
        """
        Fetches volume size from PhysicalBytesMB column of MMVolume Table
        Args:
            volume_list (List of strings)  : List of volumes

        Return:
            Dictionary containing volume as key and PhysicalBytesMB as value
        """
        volume_csdb_size_dict = {}
        self.log.info("Fetching PhysicalBytesMB column value for volumes - [%s]", 's'.join(volume_list))

        query = "select volumeid, PhysicalBytesMB from MMVolume where volumeid in (%s)"%','.join(volume_list)
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        volume_size_list = self.csdb.fetch_all_rows()
        self.log.info(volume_size_list)
        for (vol, size) in volume_size_list:
            volume_csdb_size_dict[vol] = int(size)

        return volume_csdb_size_dict

    def set_mmconfigs_param_value(self, param, value):
        """
        Set value for param in MMCOnfigs table
        Args:
            param (str) -- Parameter whose value is to be set
            value (int) -- MM admin thread frequency in minutes
        """
        self.log.info("Setting MMConfigs Param [%s] value to [%s]", param, value)
        query = "update MMConfigs set value=%s, nmin=%s where " \
                "name = '%s'"%(value, value, param)
        self.log.info("Query => %s", query)
        self.optionobj.update_commserve_db(query)

    def get_mm_admin_thread_frequency(self):
        """
        Get MM Admin Thread frequency and set the class variable
        """
        self.log.info("Getting MM Admin Thread frequency")
        query = "select name, value from MMConfigs where name in " \
                "('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', " \
                "'MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES')"

        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        all_rows = self.csdb.fetch_all_rows()
        self.log.info(all_rows)
        for (name, value) in all_rows:
            if name == 'MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES':
                self.log.info("Current MM Admin Thread value - [%s]", value)
                self.mm_admin_thread = int(value)
            else:
                self.log.info("Current Volume Update Interval Value - [%s]", value)
                self.volume_update_interval = int(value)

    def wait_for_mm_thread_invocation(self, mins):
        """
        Sleep for MM Thread invocation for given amount of time
        """
        self.log.info("Sleeping for %s minutes for MM Admin Thread invocation", mins)
        time.sleep(mins*60)

    def validate_volume_update(self, physical_size_dict, csdb_size_dict):
        """
        Validate that physical volume size and csdb volume size are same for a volume.
        Also validate that RMSpareStatusUpdateTime is set to -1 for all the volumes.

        Args:
            physical_size_dict (dictionary obj) - dictionary containing volume & its physical size
            csdb_size_dict (dictionary obj)     - dictionary containing volume & its csdb size

        """
        fail_flag = False
        for volumeid in self.volumes_list:
            self.log.info("VolumeID [%s] - Physical Size [%s] - CSDB Size [%s]", volumeid,
                          physical_size_dict[volumeid], csdb_size_dict[volumeid])
            if abs(physical_size_dict[volumeid] - csdb_size_dict[volumeid]) > 1:
                self.log.error("FAILURE: VolumeID [%s] => Physical Size & CSDB Size does not match", volumeid)
                fail_flag = True
            else:
                self.log.info("SUCCES: VolumeID [%s] => PHysical Size & CSDB Size matches", volumeid)

        #Check RMSpareStatusUpdateTime for volumes
        query = "select volumeid, RMSpareStatusUpdateTime from mmvolume where " \
                "RMSpareStatusUpdateTime > 0 and volumeid in (%s)"%','.join(self.volumes_list)
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        vol_list = self.csdb.fetch_all_rows()
        self.log.info(vol_list)
        if vol_list[0][0] != '':
            fail_flag = True
            self.log.error("FAILURE : RMSpareStatusUpdateTime of following volumes is "
                           "not set to -1 - [%s]", str(vol_list))
        else:
            self.log.info("SUCCESS: Verified that RMSpareStatusUpdateTime for all volumes is set to -1")

        if fail_flag:
            self.log.error("Some volumes failed volume size update validation. Please see logs for more details.")
            raise Exception("Volume size update validation failure")

    def clean_test_environment(self):
        """
        Clean up test environment
        """
        try:
            self.log.info("Deleting BackupSet")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
        except Exception as excp:
            self.log.info("***Failure in deleting backupset during cleanup. "
                          "Treating as soft failure as backupset will be reused***")
        try:
            if not self.user_sp:
                self.log.info("Deleting Storage Policy")
                if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                    self.commcell.storage_policies.delete(self.storage_policy_name)
            else:
                self.log.info("Keeping storage policy intact as it was a user provided storage policy")
        except Exception as excp:
            self.log.info("***Failure in deleting storage policy during cleanup. "
                          "Treating as soft failure as stroage policy will be reused***")
        try:
            if not self.user_lib:
                self.log.info("Deleting Library")
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
            else:
                self.log.info("Keeping library intact as it was a user provided library")
        except Exception as excp:
            self.log.info("***Failure in deleting library during cleanup. "
                          "Treating as soft failure as library will be reused***")

        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.client_machine_obj.remove_directory(self.content_path)
            self.log.info("Deleted the Content Directory.")
        else:
            self.log.info("Content directory does not exist.")

    def run(self):
        """Run function of this test case"""
        try:
            self.clean_test_environment()
            #STEP : Configure TC environment
            self.configure_tc_environment()

            #STEP : Run 3 Backups
            for i in range(1, 4):
                self.generate_data_run_backup(i*2)

            #STEP : Run Full/Incremental/Differential/SynthFull Backups
            self.generate_data_run_backup(1, "Full", True)
            self.generate_data_run_backup(1, "Incremental", True)
            self.generate_data_run_backup(1, "Differential", True)
            self.generate_data_run_backup(1, "Synthetic_Full")


            #STEP : Fetch all the volumes to which the above jobs have written data.
            self.get_volumes_for_jobs()

            #STEP : Get physical size of volumes from mountpath
            volumes_physical_size_dict = self.get_volume_physical_size(self.volumes_list)
            self.set_mmconfigs_param_value('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5)

            #STEP : Set RMSpareStatusUpdateTime to current time - 1 day and Volume Update Interval to 15 mins
            self.set_volume_update_time(self.volumes_list, -86400)
            self.set_mmconfigs_param_value('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15)
            self.wait_for_mm_thread_invocation(15)

            #STEP : Fetch volume size from CSDB
            volumes_csdb_size_dict = self.get_volume_csdb_size(self.volumes_list)
            self.set_mmconfigs_param_value('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', self.mm_admin_thread)
            self.set_mmconfigs_param_value('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES',
                                           self.volume_update_interval)

            #Validate that volume size on Mountpath and in CSDB are same and RMSpareStatusUpdateTime is set to -1
            self.validate_volume_update(volumes_physical_size_dict, volumes_csdb_size_dict)

            self.log.info("SUCCESS : Test case completed successfully")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.error('Failed to execute test case with error: %s', (str(exp)))

    def tear_down(self):
        """Tear down function of this test case"""

        self.log.info("Cleaning up Tescase Environment")
        self.clean_test_environment()



