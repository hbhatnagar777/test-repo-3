# -*- coding: utf-8 -*-
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
    __init__()                          --  initialize TestCase class

    setup()                             --  setup function of this test case

    run()                               --  run function of this test case

    tear_down()                         --  tear down function of this test case

    configure_tc_environment()          --	Configure testcase environment - library (if required),
                                            storage policy, backupset, subclient

    modify_subclient_properties()       --  Modify subclient properties like number of streams and allow
                                            multiple data readers

    generate_data_run_backup()          --  Generate subclient content and run given type of backup on subclient

    get_volumes_for_jobs()              --	Populates volumes to which list of jobs have written their chunks

    get_volume_update_time()	        --  Returns value in RMSpareStatusUpdateTime column against each
                                            volume provided in list

    set_volume_update_time()	        --  Sets value of RMSpareStatusUpdateTime to given time for each volume
                                            in the list

    get_volume_physical_size()	        --  Get physical size of each volume from mountpath

    get_volume_csdb_size()	            --	Fetches volume size from PhysicalBytesMB column of MMVolume Table

    set_mmconfigs_param_value()	        --  Set value for param in MMCOnfigs table

    get_mm_admin_thread_frequency()	    --  Get MM Admin Thread frequency and set the class variable

    wait_for_mm_thread_invocation()	    --  Sleep for MM Thread invocation for given amount of time

    validate_volume_update()	        --  Validate that physical volume size and csdb volume size equality for a
                                            volume based on equality_check value. Also validate that
                                            RMSpareStatusUpdateTime is set to -1 for all the volumes based on
                                            equality check.

    rename_cv_magnetic()	            --	Renames cv_magnetic folder name to some temporary folder name for all
                                            mountpaths on which volumes reside

    rename_cv_magentic_to_original()    --  Renames cv_magnetic folder name to original value for all the mountpaths
                                            in arguments

    clean_test_environment()            --  Clean up test environment

Steps :
    Aim : TC should be able to run on disk library
    1. Configure test environment - Library (if not given), Dedup Storage Policy, Backupset and Subclient
    2. Set subclient properties to use 4 streams, start new media & mark Media Full on Success.
    3. Generate different sized content from 1 GB to 5 GB for each of the 3 iterations of backups and run backups.
    4. Reset start new media & mark Media Full on Success and run 2 more jobs with content size from 2 GB to 5 GB
    5. Get a list of all volumes and verify RMSpareStatusUpdateTime is 24 hours ahead
    6. Fetch physical size of each volume
    7. Modify RMSpareStatusUpdateTime to current time
    8. Rename CV_MAGNETIC folder on MountPath
    9. Modify Volume Update frequency to 15 mins
    10. Verify that RMSpareStatusUpdateTime has changed to current time + 1 hour
    11. Verify volume size is not updated in MMVolume table
    12. Rename CV_MAGNETIC folder back to normal name
    13. Again wait for next Volume Size Update to trigger
    14. Verify that volume size is updated in MMVolume table
    15. Validate physical volume size fetched in earlier step matches with size in MMVolume table
    16. Verify that RMSpareStatusUpdateTime for all the volumes gets updated to -1

    Sample JSON Input: TC creates a new library as LibraryName is None
    "58873": {
				"ClientName": "client name",
				"AgentName": "File System",
				"MediaAgentName": "ma name",
				"LibraryName": "None"
			}
	Sample JSON Input: TC reuses library TestLibrary
	"58873": {
				"ClientName": "client name",
				"AgentName": "File System",
				"MediaAgentName": "ma name",
				"LibraryName": "Test Library"
			}
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
        self.name = "volume size update: failure in volume size update & successful retry scenario"
        self.tcinputs = {
            "MediaAgentName": None,
            "LibraryName": None
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
        self.optionobj = None
        self.volume_physical_size_dict = {}
        self.mm_admin_thread = None
        self.volume_update_interval = None
        self.physical_location_list = []
        self.is_user_defined_dedup = False
        self.engine_id = None


    def setup(self):
        """Setup function of this test case"""
        self.optionobj = OptionsSelector(self.commcell)
        self.library_name = self.tcinputs['LibraryName']
        self.ma_name = self.tcinputs['MediaAgentName']
        timestamp_suffix = OptionsSelector.get_custom_str()

        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 15)
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.library_name.lower() == "none":
            self.library_name = f"Lib_TC_{self.id}_{self.ma_name}"
            self.log.info("No library name provided, new library [%s] will be created", self.library_name)
            if self.ma_machine_obj.os_info.lower() == 'windows':
                self.log.info('Disabling Ransomware protection on MA')
                self.commcell.media_agents.get(
                    self.tcinputs.get('MediaAgentName')).set_ransomware_protection(False)

            self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 15)
            self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, self.id)
            if not self.is_user_defined_dedup:
                self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, "DDBs", f"TC_{self.id}")
            else:
                self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get('dedup_path'), "DDBs",
                                                                f"TC_{self.id}")
        self.storage_policy_name = f"SP_TC_{self.id}_{self.ma_name}"
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

        if self.tcinputs['LibraryName'].lower() == "none":
            self.log.info("Creating Library [%s]", self.library_name)
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.log.info("Library [%s] already exists. Reusing the Library.", self.library_name)
            else:
                self.mahelper_obj.configure_disk_library(self.library_name, self.ma_name, self.mountpath)
                self.log.info("Library [%s] created successfully.", self.library_name)
        else:
            self.log.info("Skipping Library creation as user has provided Library [%s]", self.library_name)
            self.log.info("Checking if user provided Library exists")
            if not self.commcell.disk_libraries.has_library(self.library_name):
                self.log.error("User Provided Library does not exist. Erroring out.")
                raise Exception("User Provided Library [%s] does not exist. Please provide correct library name"%
                                self.library_name)

        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.sp_obj = self.dedup_helper_obj.configure_dedupe_storage_policy(self.storage_policy_name,
                                                                            self.library_name, self.ma_name,
                                                                            self.dedup_path)
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)

        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        if dedup_engines_obj.has_engine(self.storage_policy_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_policy_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                store_obj = dedup_engine_obj.get(dedup_store[0])
                self.log.info("Disabling Garbage Collection on DDB Store == %s", dedup_store[0])
                store_obj.enable_garbage_collection = False

        self.engine_id = self.dedup_helper_obj.get_sidb_ids(self.sp_obj.storage_policy_id, "Primary")[0]

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        self.log.info("Configuring Subclient [%s]", self.subclient_name)
        self.subclient_obj = self.mahelper_obj.configure_subclient(self.backupset_name, self.subclient_name,
                                                                   self.storage_policy_name, self.content_path)
        self.log.info("Successfully configured Subclient [%s]", self.subclient_name)

        self.log.info("Setting Number of Streams to 10 and Allow Multiple Data Readers to True")
        self.modify_subclient_properties(10, True)

    def modify_subclient_properties(self, num_streams=None, multiple_readers=None):
        """
        Modify subclient properties like number of streams and allow multiple data readers

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
        self.mahelper_obj.create_uncompressable_data(self.client.client_name, self.content_path, size_in_gb)
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
        query = "update mmvolume set RMSpareStatusUpdateTime = RMSPareStatusUpdateTime %s %s where volumeid in (%s) and RMSPareStatusUpdateTime > 0"%\
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
        self.physical_location_list = self.csdb.fetch_all_rows()
        self.log.info(self.physical_location_list)
        #volumeid	folder	    MountPathName	        client
        #111799	    C:\\54835	R3BGE3_07.01.2020_04.55	winma1pdcauto
        for (volumeid, folder, mountpath, clientname) in self.physical_location_list:
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

    def wait_for_mm_thread_invocation(self, mins, check_pruning=False):
        """
        Sleep for MM Thread invocation for given amount of time
        """
        pruning_complete = False
        self.log.info("Sleeping for %s minutes for MM Admin Thread invocation", mins)
        if check_pruning:
            pruning_complete = False
            for iteration in range(1, 5):
                self.log.info("Sleeping for %s mins before running Data Aging job", int((mins/4)))
                time.sleep(int((mins/4))*60)
                da_job = self.mahelper_obj.submit_data_aging_job()
                if not da_job.wait_for_completion():
                    raise Exception(f"Data Aging job [{da_job.job_id}] did not complete in given timeout")
                self.log.info("Validating logs to confirm Phase 3 pruning has occurred")
                matched_lines = self.dedup_helper_obj.validate_pruning_phase(self.engine_id,
                                                                         self.tcinputs['MediaAgentName'])
                if matched_lines != None:
                    self.log.info("Found at least 1 log line with phase 3 pruning")
                    self.log.info(matched_lines)
                    pruning_complete = True
                    break
            if not pruning_complete:
                self.log.error("Pruning is not complete even after timeout")
                raise Exception("Pruning is not complete even after timeout")
        else:
            self.log.info("Sleeping for %s minutes", mins)
            time.sleep(mins*60)

    def validate_volume_update(self, physical_size_dict, csdb_size_dict, equality_check=True):
        """
        Validate that physical volume size and csdb volume size equality for a volume based on equality_check value.
        Also validate that RMSpareStatusUpdateTime is set to -1 for all the volumes based on equality check.

        Args:
            physical_size_dict (dictionary obj) --  dictionary containing volume & its physical size
            csdb_size_dict (dictionary obj)     --  dictionary containing volume & its csdb size
            equality_check (boolean)            --  If set to True, checks that Physical size and CSDB size are equal
                                                    and RMSpareStatusUpdateTime is set to -1.
                                                    If set to False, checks that Physical size and CSDB size are not
                                                    equal and RMSpareStatusUpdateTime is set to a future value
        """
        fail_flag = False
        self.log.info("===Equality flag set to [%s]===", equality_check)
        for volumeid in self.volumes_list:
            self.log.info("VolumeID [%s] - Physical Size [%s] - CSDB Size [%s]", volumeid,
                          physical_size_dict[volumeid], csdb_size_dict[volumeid])
            if abs(physical_size_dict[volumeid] - csdb_size_dict[volumeid]) > 1:
                self.log.error("VolumeID [%s] => Physical Size & CSDB Size does not match", volumeid)
                if equality_check:
                    self.log.info("Marking failure as equality flag is set to [%s]", equality_check)
                    fail_flag = True
            else:
                if not equality_check:
                    self.log.info("Marking failure as equality flag is set to [%s]", equality_check)
                    fail_flag = True
                self.log.info("VolumeID [%s] => PHysical Size & CSDB Size matches", volumeid)

        #Check RMSpareStatusUpdateTime for volumes
        if equality_check:
            query = "select volumeid, RMSpareStatusUpdateTime from mmvolume where " \
                    "RMSpareStatusUpdateTime <> -1 and volumeid in (%s)"%','.join(self.volumes_list)
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
        else:
            query = "select volumeid, RMSpareStatusUpdateTime from mmvolume where " \
                    " volumeid in (%s)"%','.join(self.volumes_list)
            self.log.info("Query => %s", query)
            self.csdb.execute(query)
            vol_list = self.csdb.fetch_all_rows()
            #Fetch CS Time
            self.log.info("Fetching current time as per CSDB")
            query = "SELECT DATEDIFF(SECOND,'1970-01-01', GETUTCDATE()) AS 'CSTIME';"
            self.log.info("Query => %s", query)
            self.csdb.execute(query)
            cs_time = int(self.csdb.fetch_one_row()[0])
            self.log.info("Current CS time as per CSDB is [%s]", cs_time)
            for (vol, update_time) in vol_list:
                update_time = int(update_time)
                if update_time >= cs_time:
                    self.log.info("SUCCESS: CS correctly updated RMSpareStatusUpdateTime for volume [%s] "
                                  "to a value [%s] which is in future", vol, update_time)
                else:
                    self.log.error("FAILURE: CS did not update RMSpareStatusUpdateTime for volume [%s] "
                                   "to a value in future. Current value shown is [%s]", vol, update_time)
                    fail_flag = True


        if fail_flag:
            self.log.error("Some volumes failed volume size update validation. Please see logs for more details.")
            raise Exception("Volume size update validation failure")



    def rename_cv_magnetic(self):
        """
        Renames cv_magnetic folder name to some temporary folder name for all mountpaths on which volumes reside

        Return:
            Returns dictionary containing MA Name and Renamed Path name
        """
        client_cv_magnetic_path_dict = {}
        for (volumeid, folder, mountpath, clientname) in self.physical_location_list:
            machine_obj = Machine(clientname, self.commcell)
            cv_magnetic_path = "%s%s%s%s%s" % (folder, self.ma_machine_obj.os_sep, mountpath,
                                               self.ma_machine_obj.os_sep, "CV_MAGNETIC")
            #To ensure that we rename each folder only once
            if clientname not in client_cv_magnetic_path_dict:
                self.log.info("Renaming mountpath [%s] on client [%s]", cv_magnetic_path, clientname)
                if machine_obj.check_directory_exists(cv_magnetic_path):
                    machine_obj.rename_file_or_folder(cv_magnetic_path, "%s_RenamedBy_%s"%(cv_magnetic_path, self.id))
                    self.log.info("Renamed mountpath [%s] on client [%s] to [%s]", cv_magnetic_path, clientname,
                                  "%s_RenamedBy_%s" % (cv_magnetic_path, self.id))
                    client_cv_magnetic_path_dict[clientname] = "%s_RenamedBy_%s" % (cv_magnetic_path, self.id)

            return client_cv_magnetic_path_dict

    def rename_cv_magentic_to_original(self, rename_cv_magnetic):
        """
        Renames cv_magnetic folder name to original value for all the mountpaths in arguments

        Args:
             client_cv_magnetic_path_dict (dictionary)  - Dictionary returned by function rename_cv_magnetic
        """

        for (clientname, mp) in rename_cv_magnetic.items():
            self.log.info("Renaming mountpath [%s] on client [%s]", mp, clientname)
            machine_obj = Machine(clientname, self.commcell)
            if machine_obj.check_directory_exists(mp):
                machine_obj.rename_file_or_folder(mp, mp.rstrip("_RenamedBy_%s"% (self.id)))
                self.log.info("Renamed mountpath [%s] on client [%s] to [%s]", mp, clientname,
                              mp.rstrip("RenamedBy_%s"% (self.id)))

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
            self.log.info("Deleting Storage Policy")
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
        except Exception as excp:
            self.log.info("***Failure in deleting storage policy during cleanup. [%s]"
                          "Treating as soft failure as stroage policy will be reused***",
                          str(excp))
        try:
            self.log.info("Deleting Library")
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
        except Exception as excp:
            self.log.info("***Failure in deleting library during cleanup. [%s]"
                          "Treating as soft failure as library will be reused***",
                          str(excp))

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
        da_job = self.mahelper_obj.submit_data_aging_job()
        if not da_job.wait_for_completion():
            raise Exception(f"Data Aging job [{da_job.job_id}] did not complete in given timeout")

    def validate_volume_size_update_failure(self):
        """
        Validate volume size update failure for volumes by parsing CVMA logs
        """
        statement = 'Unable to get size of volume'
        failed_volumes = 0
        (matched_lines, matched_string) = self.dedup_helper_obj.parse_log(self.tcinputs["MediaAgentName"],
                                                                          "CVMA.log", regex=statement,
                                                                          escape_regex=False)
        for line in matched_lines:
            if 'Unable to get size of volume' in line and str(self.id) in line:
                split_line = line.split(r'].')[0]
                volume_id  = split_line.split(self.ma_machine_obj.os_sep)[-1].split('_')[-1]
                if volume_id in self.volumes_list:
                    self.log.info("Verified volume size update failure for volume %s", volume_id)
                    self.log.info(line)
                    failed_volumes+=1
        if failed_volumes == len(self.volumes_list):
            self.log.info("Successfully verified that volume size update has failed for volumes")
        else:
            raise Exception("Failed to verify the volume size update failure for volumes")



    def run(self):
        """Run function of this test case"""
        try:
            self.clean_test_environment()
            #STEP : Configure TC environment
            self.configure_tc_environment()
            #STEP : Run 1 Full Backup
            self.generate_data_run_backup(1, "Full")
            self.generate_data_run_backup(1, "Incremental")
            self.generate_data_run_backup(1, "Incremental")
            self.generate_data_run_backup(1, "Incremental")

            #Rearranging the flow of this test case as from SP30 onwards,
            #volume sizes are being updated after backups without volume size update mechanism
            self.get_volumes_for_jobs()

            volumes_physical_size_dict = self.get_volume_physical_size(self.volumes_list)
            self.set_mmconfigs_param_value('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5)
            self.mahelper_obj.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)

            #STEP : Prune the incremental jobs.
            self.log.info("==Prune half the backup jobs==")
            self.prune_jobs(self.backup_job_list[1:3])
            self.log.info("==Wait for Pruning to complete==")
            self.wait_for_mm_thread_invocation(40, True)
            volumes_physical_size_dict_pruned = self.get_volume_physical_size(self.volumes_list)
            
            #Rename the MP folder to a different name
            cv_magnetic_dict = self.rename_cv_magnetic()
            #Set RMSpareStatusUpdateTime back by 1 day
            self.set_volume_update_time(self.volumes_list, -86400)
            self.set_mmconfigs_param_value('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15)
            self.wait_for_mm_thread_invocation(20)
            volumes_csdb_size_dict = self.get_volume_csdb_size(self.volumes_list)
            self.validate_volume_update(volumes_physical_size_dict_pruned, volumes_csdb_size_dict, False)
            #Unable to get size of volume [C:\58873\DDTF8S_08.22.2022_08.40\CV_MAGNETIC\V_97690]. Cannot access volume
            self.validate_volume_size_update_failure()
            #Rename the MP folder to a original name
            self.rename_cv_magentic_to_original(cv_magnetic_dict)
            self.set_volume_update_time(self.volumes_list, -86400)
            self.wait_for_mm_thread_invocation(20)

            volumes_csdb_size_dict = self.get_volume_csdb_size(self.volumes_list)

            self.validate_volume_update(volumes_physical_size_dict_pruned, volumes_csdb_size_dict, True)

            self.set_mmconfigs_param_value('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', self.mm_admin_thread)
            self.set_mmconfigs_param_value('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES',
                                           self.volume_update_interval)
            self.log.info("SUCCESS : Test case completed successfully")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.error('Failed to execute test case with error: %s', (str(exp)))

    def tear_down(self):
        """Tear down function of this test case"""
        self.set_mmconfigs_param_value('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', self.mm_admin_thread)
        self.set_mmconfigs_param_value('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES',
                                       self.volume_update_interval)
        if self.ma_machine_obj.os_info.lower() == 'windows':
            self.log.info('Enabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)
        self.log.info("Starting cleanup...")
        self.clean_test_environment()
