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

    configure_tc_environment()  --  Configure Test case environment

    modify_subclient_properties()   -- Modify subclient properties

    generate_data_run_backup()  -- Generate data and run backups

    get_volumes_for_jobs()      -- Get a list of volumes created by backup jobs

    get_volume_update_time()    -- Returns RMSpareStatusUpdateTime all the volumes

    set_volume_update_time()    -- Set RMSpareStatusUpdateTime column value for volumes

    get_volume_physical_size()  -- Get physical size of the volume folder from mountpath

    get_volume_csdb_size()      -- Get volume size from MMVolume table

    get_mm_admin_thread_frequency() -- Get frequency of mm admin threads so that it can be reset after completion

    wait_for_mm_thread_invocation() -- Wait for MM volume size update thread invocation

    validate_volumes_update_time()  -- Validates that RMSpareStatusUpdateTime has changed for volumes

    validate_volume_update()        -- Validate that volume size update has happened correctly

    clean_test_environment()        -- Cleanup the test case environment

    prune_jobs()                    -- Prune the given jobs

    initiate_volume_size_update_process()   -- Iinitiate volume size update process

    validate_size_reduction()       -- Validate that volume size have reduced after pruning

    wait_for_pruning()              -- Wait for phase 3 pruning to complete within given timeout

    Aim : TC should be able to run on all types of mountpaths & OS
    Sample Input:
    	"58872": {
					"ClientName": "client name",
					"AgentName": "File System",
					"MediaAgentName": "ma name",
					"dedup_path": "/ws/ddb",
					"mount_path": "/ws/glus"
			}
	    dedup_path and mount_path are optional parameters


    Steps :
    1. Create a new library, storage policy, backupset, subclient
    2. Generate Unique data and run backup
    3. Copy half the data from previous backup and run a new incremental backup
    4. Get a list of volumes for these backups
    5. Change RMSpareStatusUpdateTime to the current value - 86400 seconds
    6. Change Volume Update interval, MM Thread interval and Pruner interval to 15 and 5 and 2 mins respectively
    7. Allow 20 minutes for volume update to happen - keep checking every 5 minutes
    8. Validate that RMSpareStatusUpdateTime is set to -1
    9. Fetch Physical Size for volumes
    10. Fetch Size from PhysicalBytesMB column for all the volumes
    11. Compare the two set of values for each volume and verify that they are same
    12. Delete 1st backup job and run data aging
    13. Wait for pruning to catch up
    14. Verify that RMSpareStatusUPdateTime has changed to future value
    15. Change RMSpareStatusUpdateTime to its current value - 86400 seconds
    16. Repeat steps 7 to 11 again
    17. Make sure that sum of sizes of volumes as fetched from CSDB before pruning>sum of sizes of volumes after
        pruning
"""
import time
from cvpysdk import deduplication_engines
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
        self.name = "volume size update: pruning scenario"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.library_name = None
        self.mountpath = None
        self.ma_name = None
        self.storage_policy_name = None
        self.storage_policy_obj = None
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
        self.drillhole_key_added = False
        self.client_system_drive = None
        self.dedup_helper_obj = None
        self.backup_job_list = []
        self.volumes_list = []
        self.sqlobj = None
        self.volume_physical_size_dict = {}
        self.mm_admin_thread = None
        self.volume_update_interval = None
        self.user_lib = False
        self.user_sp = False
        self.optionobj = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.store_obj = None

    def setup(self):
        """Setup function of this test case"""
        self.optionobj = OptionsSelector(self.commcell)

        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.ma_name =  self.tcinputs.get('MediaAgentName')

        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 15)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 15)
        self.library_name = f"Lib_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))}"

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"), self.id)
        else:
            self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, self.id)

        self.storage_policy_name = f"SP_TC_{self.id}_{self.ma_name}"
        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, "DDBs", f"TC_{self.id}")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get('dedup_path'), "DDBs", f"TC_{self.id}")

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

        if not self.ma_machine_obj.check_directory_exists(self.mountpath):
            self.log.info("Creating mountpath directory [%s]", self.mountpath)
            self.ma_machine_obj.create_directory(self.mountpath)
        self.log.info("Creating Library [%s]", self.library_name)
        if self.commcell.disk_libraries.has_library(self.library_name):
            self.log.info("Library [%s] already exists. Reusing the Library.", self.library_name)
        else:
            self.mahelper_obj.configure_disk_library(self.library_name, self.ma_name, self.mountpath)
            self.log.info("Library [%s] created successfully.", self.library_name)
            #Reset flag 128 on the library & set DedupeDrillHoles to 0 on MA

        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.sp_obj = self.dedup_helper_obj.configure_dedupe_storage_policy(
            self.storage_policy_name, self.library_name, self.ma_name, self.dedup_path)
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)

        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        if dedup_engines_obj.has_engine(self.storage_policy_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_policy_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])
                self.log.info("Disabling Garbage Collection on DDB Store == %s", dedup_store[0])
                self.store_obj.enable_garbage_collection = False

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        self.log.info("Configuring Subclient [%s]", self.subclient_name)
        self.subclient_obj = self.mahelper_obj.configure_subclient(self.backupset_name, self.subclient_name,
                                                                   self.storage_policy_name, self.content_path)
        self.log.info("Successfully configured Subclient [%s]", self.subclient_name)

        self.log.info("Setting Number of Streams to 5 and Allow Multiple Data Readers to True")
        self.modify_subclient_properties(5, True)

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

    def generate_data_run_backup(self, size_in_gb, backup_type="Incremental", mark_media_full=False,
                                 copy_data=False, copy_from_dir=""):
        """
        Generate subclient content and run given type of backup on subclient
        Args:
            size_in_gb (int)      -- Content Size in GB
            backup_type (str)     -- Backup Type [ Full or Incremental etc. ]
            mark_media_full(bool) -- Boolean Flag to decide if volumes are to be marked full after backup completion
            copy_data (bool)      -- Boolean Flag to decide if new data to be generated  or existing data to be copied
            copy_from_dir (str)   -- Source directory if copy_data is set to True
        Return:
            Returns content dir for job
        """
        self.log.info("Generating content of size [%s] at location [%s]", size_in_gb, self.content_path)
        content_dir = ""
        if not copy_data:
            content_dir = f"{self.content_path}{self.client_machine_obj.os_sep}{size_in_gb}"
            self.mahelper_obj.create_uncompressable_data(self.client.client_name, content_dir, size_in_gb, 1)
        else:
            target_content_dir = f"{copy_from_dir}_copied"
            if not self.client_machine_obj.check_directory_exists(target_content_dir):
                self.client_machine_obj.create_directory(target_content_dir)
            self.log.info("Generatig duplicate content by copying from - %s", copy_from_dir)
            self.client_machine_obj.copy_folder(copy_from_dir, target_content_dir)
            copied_dir = self.client_machine_obj.get_folders_in_path(target_content_dir, recurse=True)
            self.log.info(f"Deleting every alternate file from {copied_dir[1]}")
            self.optionobj.delete_nth_files_in_directory(self.client_machine_obj, copied_dir[1], 2, "delete")
            content_dir = target_content_dir
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
        return content_dir

    def get_volumes_for_jobs(self):
        """
        Populates volumes to which list of jobs have written their chunks
        """
        jobs_list = [job.job_id for job in self.backup_job_list]
        job_ids = ','.join(jobs_list)
        self.log.info("Fetching volumes to which following jobs have written chunks - [%s]", job_ids)
        query = f"""select volumeid from mmvolume where volumeid in (select volumeid from archchunk where 
        id in (select archchunkid from archchunkmapping where jobid in ({job_ids})))"""
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        volumes_list = self.csdb.fetch_all_rows()
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
        query = f"select volumeid, RMSpareStatusUpdateTime from mmvolume where volumeid in ({','.join(volume_list)})"
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
        query = f"update mmvolume set RMSpareStatusUpdateTime = RMSPareStatusUpdateTime {operation} " \
                f"{abs(time_to_set)} where volumeid in ({','.join(volume_list)}) and RMSpareStatusUpdateTime > 0"
        self.log.info("Query => %s", query)
        self.optionobj.update_commserve_db(query)
        self.log.info("RMSpareStatusUpdateTime updated to [%s]", time_to_set)

    def get_volume_physical_size(self, volume_list, size_disk=False):
        """
        Get physical size of each volume from mountpath
        Args:
            volume_list (List)  : List of volume IDs
            size_disk (bool)    : Whether size on disk needs to be fetched instead of size
        Return:
            Dictionary containing volume and its physical size on disk
        """
        #Get physical location of the volume
        volume_path_dict = {}
        volume_physical_size_dict = {}
        ma_name_obj_dict = {}
        self.log.info("Fetching physical location of volumes in volume list : [%s]", volume_list)
        query = f"""select MMV.volumeid, MMDC.folder, MNTPATH.MountPathName, CL.name 
                from MMMountpath MNTPATH, MMDeviceController MMDC, MMMountPathToStorageDevice MMPS, MMVOLUME MMV, 
                App_Client CL where MMPS.MountPathId = MMV.CurrMountPathId and
                MNTPATH.MountPathId = MMV.CurrMountPathId and CL.id = MMDC.clientid
                and MMDC.deviceid = MMPS.DeviceId and MMV.volumeid in ({','.join(volume_list)})"""
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        #Now work out the path for each of the volume and fetch its size
        physical_location_list = self.csdb.fetch_all_rows()
        self.log.info(physical_location_list)
        #volumeid	folder	    MountPathName	        client
        #111799	    C:\\54835	R3BGE3_07.01.2020_04.55	winma1pdcauto

        for (volumeid, folder, mountpath, clientname) in physical_location_list:
            #TODO: Use Join Paths method
            volume_path_dict[volumeid] = f"{folder}{self.ma_machine_obj.os_sep}{mountpath}" \
                                         f"{self.ma_machine_obj.os_sep}CV_MAGNETIC{self.ma_machine_obj.os_sep}" \
                                         f"V_{volumeid}"

            self.log.info("Fetching physical size of volume [%s] from location - [%s]", volumeid,
                          volume_path_dict[volumeid])

            #Create machine object of MA and store in dictionary as we may need it many times
            if clientname not in ma_name_obj_dict:
                ma_name_obj_dict[clientname] = Machine(clientname, self.commcell)

            #Get physical size in bytes
            volume_physical_size_dict[volumeid] = round(ma_name_obj_dict[clientname].get_folder_size(
                volume_path_dict[volumeid], size_on_disk=size_disk ))

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
        self.log.info("Fetching PhysicalBytesMB column value for volumes - [%s]", ','.join(volume_list))

        query = f"select volumeid, PhysicalBytesMB from MMVolume where volumeid in ({','.join(volume_list)})"
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        volume_size_list = self.csdb.fetch_all_rows()
        self.log.info(volume_size_list)
        for (vol, size) in volume_size_list:
            volume_csdb_size_dict[vol] = int(size)

        return volume_csdb_size_dict


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

    def wait_for_mm_thread_invocation(self, mins, volumes_list):
        """
        Check if volume size update has happened for given volumes
        """

        self.log.info("Checking if RMSpareStatusUpdateTime has been updated for volumes %s", volumes_list)
        is_volsize_update_done = False
        #TODO : Check if we need volume_list or it can be self.volumes_list
        for i in range(0,5):
            self.log.info("Sleeping for %s minutes", int(mins/5))
            time.sleep(int(mins/5)*60)
            if self.validate_volumes_update_time(future_time=False):
                self.log.info("Volume Size update has been done for volumes %s", volumes_list)
                is_volsize_update_done = True
                break
            else:
                self.log.info("Volume Size update has not been done for volumes %s yet", volumes_list)
                self.log.info("Waiting for another %s minutes before trying again", int(mins/5))

        if is_volsize_update_done:
            return True
        else:
            self.log.error("Volume Size update did not happen even after %s minutes. Raising exception", mins)
            #TODO : Later raise exception
            return False


    def validate_volumes_update_time(self,future_time=False):
        """
        Validate the RMSpareStatusUpdateTime column value for all volumes based on future_time expectations

        Args:
            future_time(boolean) -  When set to False : check -1 in RMSpareStatusUpdateTime
                                    When set to True  : check for a non-zero positive value in RMSpareStatusUpdateTime
        """
        # Check RMSpareStatusUpdateTime for volumes
        equality_string = ""
        fail_flag = False
        if future_time:
            equality_string = ">0"
        else:
            equality_string = "=-1"
        query = f"""select volumeid, RMSpareStatusUpdateTime from mmvolume where 
        RMSpareStatusUpdateTime {equality_string} and volumeid in ({','.join( self.volumes_list)})"""
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        vol_list = self.csdb.fetch_all_rows()
        self.log.info("Fetched Output : ==> %s", vol_list)
        if vol_list[0][0] == '':
            fail_flag = True
            self.log.error("FAILURE : RMSpareStatusUpdateTime of following volumes is "
                           "not set as per expectation - [%s]", str(self.volumes_list))
            #raise Exception("RMSpareStatusUpdateTime of volumes is not set in Future")
        else:
            self.log.info("SUCCESS: Verified that RMSpareStatusUpdateTime for all volumes is set as per expectation")

        return not fail_flag

    def validate_size_reduction(self, csdb_size_dict_before, csdb_size_dict_after):
        """
        Validate whether CSDB shows reduction in volume size after pruning

        Args:
            csdb_size_dict_before (dictionary obj) : CSDB size dictionary before pruning
            csdb_size_dict_after (dictionary obj)  : CSDB size dictionary after pruning

        Return:
            True if sum of volume size after pruning is less than earlier
        """
        before_size = 0
        after_size = 0
        for (volumeid, size) in csdb_size_dict_before.items():
            before_size += int(size)
        for (volumeid, size) in csdb_size_dict_after.items():
            after_size += int(size)

        self.log.info("Total Size of volumes as per CSDB *before* pruning => %s", before_size)
        self.log.info("Total Size of volumes as per CSDB *after* pruning => %s", after_size)

        if before_size > after_size:
            self.log.info("Sum of volume sizes after pruning has reduced as expected")
            return True

        self.log.error("Sum of volume sizes after pruning has not reduced as expected")
        return False




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
            if physical_size_dict[volumeid] != csdb_size_dict[volumeid]:
                if abs(physical_size_dict[volumeid] - csdb_size_dict[volumeid]) > 1:
                    self.log.error("******FAILURE: VolumeID [%s] => Physical Size & CSDB Size does not match******",
                                   volumeid)
                    fail_flag = True
                else:
                    self.log.info("*****PARTIAL SUCCESS : VolumeID [%s] => Physical Size & CSDB Size does not match "
                                  "but is within tolerance limit of 1 MB*****")
            else:
                self.log.info("SUCCES: VolumeID [%s] => Physical Size & CSDB Size matches", volumeid)

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
            self.log.info("***Failure in deleting backupset during cleanup - %s "
                          "Treating as soft failure as backupset will be reused***", str(excp))
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

        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.client_machine_obj.remove_directory(self.content_path)
            self.log.info("Deleted the Content Directory.")
        else:
            self.log.info("Content directory does not exist.")


    def prune_jobs(self, list_of_jobs):
        """
        Prunes jobs from storage policy copy

        Args:
            list_of_jobs(obj) - List of jobs
        """
        sp_copy_obj = self.sp_obj.get_copy("Primary")
        for job in list_of_jobs:
            sp_copy_obj.delete_job(job.job_id)
            self.log.info("Deleted job from %s with job id %s", self.storage_policy_name, job.job_id)
        self.mahelper_obj.submit_data_aging_job()

    def initiate_volume_size_update_process(self, after_which_action, size_on_disk=False):
        """
        Initiate sequence of actions to verify volume size update after actions like backup / pruning

        Args:
            after_which_action  (str)   -- Action that initiated volume size update eg. pruning/backup
            size_on_disk        (bool)  -- if size on disk is required, Set it to True if method is called after
                                            space reclamation

        Return :
            dictionary containing volume ID and its size in CSDB
        """
        self.log.info("==Verify that RMSpareStatusUpdateTime is set to Future==")
        #TODO : Raise exception if it returns False
        if not self.validate_volumes_update_time(future_time=True):
            raise  Exception("RMSpareStatusUpdatetime validation failed while verifying future time")

        self.log.info("==Move RMspareStatusUpdateTime back by 1 day==")
        self.set_volume_update_time(self.volumes_list, -86400)

        self.log.info("==Fetching Volume size ON DISK==")
        volumes_physical_size_dict = self.get_volume_physical_size(self.volumes_list, size_disk=size_on_disk)

        self.log.info("==Wait for volume size update to take place after %s==", after_which_action)
        self.wait_for_mm_thread_invocation(30, self.volumes_list)

        self.log.info("==Get volume size from CSDB==")
        volumes_csdb_size_dict = self.get_volume_csdb_size(self.volumes_list)

        self.log.info("==Verify that RMSpareStatusUpdateTime is set to -1==")
        #TODO : Raise exception if it returns False
        if not self.validate_volumes_update_time(future_time=False):
            raise Exception("RMSpareStatusUpdatetime validation failed while verifying -1")

        self.log.info("==Verify that volume size is same in CSDB and physical location==")
        self.validate_volume_update(volumes_physical_size_dict, volumes_csdb_size_dict)

        return volumes_csdb_size_dict

    def wait_for_pruning(self, timeout=30):
        """
        Wait for phase 3 pruning to complete within given timeout

        Args:
            timeout (int)       --      Timeout in minutes
        """
        pruning_complete = False
        for iteration in range(1, 5):
            self.log.info("Sleeping for %s mins before running Data Aging job", int((timeout / 4)))
            time.sleep(int((timeout / 4)) * 60)
            da_job = self.mahelper_obj.submit_data_aging_job()
            if not da_job.wait_for_completion():
                raise Exception(f"Data Aging job [{da_job.job_id}] did not complete in given timeout due to error "
                                f"{da_job.delay_reason}")
            self.log.info("Validating logs to confirm Phase 3 pruning has occurred")
            output = self.dedup_helper_obj.validate_pruning_phase(self.store_obj.store_id, self.tcinputs['MediaAgentName'])
            if output:
                self.log.info("Found at least 1 log line with phase 3 pruning")
                self.log.info(output)
                pruning_complete = True
                break
        if not pruning_complete:
            self.log.error(f"Pruning is not complete even after timeout of {timeout} minutes")
            raise Exception(f"Pruning is not complete even after timeout of {timeout} minutes")

    def run(self):
        """Run function of this test case"""
        try:
            self.clean_test_environment()
            #STEP : Configure TC environment
            self.configure_tc_environment()
            self.backup_job_list = []
            backup_content_dirs = []
            self.log.info("+++++++++++++++++VOLUME SIZE UPDATE : DEDUP PRUNING+++++++++++++++++")

            self.log.info("============PHASE 1 : Volume Size Updates after Backups ============")

            self.log.info("==Run Backups==")
            for i in range(1, 4):
                backup_content_dirs.append(self.generate_data_run_backup(i*1, mark_media_full=True, copy_data=False))
                self.generate_data_run_backup(i*1, mark_media_full=False, copy_data=True,
                                              copy_from_dir=backup_content_dirs[i-1])

            self.log.info("==Set Required MM Config Params==")
            #TODO: Directly call mmhelper method
            self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 5)
            self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15, 15)
            self.mahelper_obj.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)

            self.log.info("==Get names of volumes created by backup jobs==")
            self.get_volumes_for_jobs()

            csdb_size_before = self.initiate_volume_size_update_process("backups")

            self.log.info("============Volume Size Updates after Pruning============")

            self.log.info("==Prune half the backup jobs==")
            self.prune_jobs([self.backup_job_list[x] for x in range(0,len(self.backup_job_list),2)])

            self.log.info("==Wait for Pruning to complete==")
            self.wait_for_pruning(40)

            csdb_size_after = self.initiate_volume_size_update_process("pruning", size_on_disk=True)

            self.log.info("==Verifying reduction in PhysicalBytesMB in MMVolume table after pruning==")
            self.validate_size_reduction(csdb_size_before, csdb_size_after)
            self.log.info("SUCCESS : Test case completed successfully")
        except Exception as exp:
            self.status = constants.FAILED
            self.result_string = str(exp)
            self.log.error('Failed to execute test case with error: %s', (str(exp)))

    def tear_down(self):
        """Tear down function of this test case"""
        self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, self.mm_admin_thread)
        self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15,
                                                self.volume_update_interval)
        self.log.info("Starting cleanup...")
        self.clean_test_environment()



