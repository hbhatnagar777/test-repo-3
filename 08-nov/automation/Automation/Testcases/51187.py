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

    configure_resources_for_roundrobin()    --  Configure resources for Round Robin between Data Paths

    verify_mp_offline()         --  Check if MP is offline

    wait_till_ma_offline()      --  Wait till MA is offline

    enable_preferred_datapath() --  Enable datapath options

    wait_till_backup_phase()    --  Wait till job is in backup phase

    run_big_backup()            --  Run log running backups

    validate_job_pending()      --  Validate that job is in pending state

    start_stop_ma_services()    --  Take service action on MA

    verify_lanfree_restore()    --  Verify that Restore job has used Lan Free datapath



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
        "51187": {
				"ClientName": "client_name",
				"AgentName": "File System",
				"MediaAgentName": "ma1_name",
				"MediaAgent2Name": "ma2_name",
				"ma1_username" : "user_name",
				"ma1_password" :"password" 
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
        self.name = "Resource Manager Case : Datapath Failover Scenarios (Round-Robin/Preferred/failover-offline)"
        self.tcinputs = {
            "MediaAgentName": None,
            "MediaAgent2Name": None,
            "ma1_username" : None,
            "ma1_password" : None
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
        self.ma1_username = None
        self.ma1_password = None
        self.ma1_instance = None
        self.ma1_client_obj = None
        self.restore_path = None
        self.lanfree_volumeid = None
        self.optionobj = None

    def setup(self):
        """Setup function of this test case"""
        self.optionobj = OptionsSelector(self.commcell)
        self.mahelper_obj = MMHelper(self)
        self.dedup_helper_obj = DedupeHelper(self)
        self.ma1_name = self.tcinputs.get('MediaAgentName')
        self.ma2_name = self.tcinputs.get('MediaAgent2Name')
        self.dedup_path = self.tcinputs.get('dedup_path')
        self.ma1_username = self.tcinputs.get('ma1_username')
        self.ma1_password = self.tcinputs.get('ma1_password')

        #For Preferred Datapath Test - Client has to be MA
        self.client_machine_obj = Machine(self.ma1_name, self.commcell)
        timestamp_suffix = "TC"

        self.ma1_machine_obj = Machine(self.ma1_name,  username=self.ma1_username, password=self.ma1_password)
        self.ma2_machine_obj = Machine(self.ma2_name, self.commcell)
        self.ma1_client_obj = self.commcell.clients.get(self.ma1_name)
        self.ma_client_agent = self.ma1_client_obj.agents.get('File System')

        self.ma1_library_drive = self.optionobj.get_drive(self.ma1_machine_obj, 30)
        self.ma2_library_drive = self.optionobj.get_drive(self.ma2_machine_obj, 30)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 30)
        if not self.dedup_path and "unix" in self.ma2_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path must be input for Unix MA!..")

        if not self.dedup_path:
            self.dedup_path = self.ma2_machine_obj.join_path(self.ma2_library_drive, self.id, "DDB")

        self.library_name = f"Lib_TC_{self.id}_{timestamp_suffix}"
        self.mountpath1 = self.ma1_machine_obj.join_path(self.ma1_library_drive, self.id, "LIB_MP1")
        self.mountpath2 = self.ma2_machine_obj.join_path(self.ma2_library_drive, self.id, "LIB_MP2")


        self.storage_policy_name = f"SP_TC_{self.id}_{timestamp_suffix}"
        self.backupset_name = f"BkpSet_TC_{self.id}_{self.ma1_name}"
        self.subclient_name = f"Subc_TC__{self.id}_{timestamp_suffix}"


    def configure_tc_environment(self):
        """
        Configure testcase environment - library (if required), storage policy, backupset, subclient

        Args:
            suffix  (str)       --      Suffix for entity names
        """
        self.log.info("===STEP: Configuring TC Environment===")
        self.client_machine_obj = Machine(self.ma1_name, self.commcell)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 30)
        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, str(self.id), "Content")
        self.restore_path = self.client_machine_obj.join_path(self.client_system_drive, str(self.id), "Restore")
        if not self.ma1_machine_obj.check_directory_exists(self.mountpath1):
            self.log.info("Creating mountpath directory [%s]", self.mountpath1)
            self.ma1_machine_obj.create_directory(self.mountpath1)

        self.log.info("Creating Library [%s] with Mountpath [%s]", self.library_name, self.mountpath1)
        self.disklib_obj = self.mahelper_obj.configure_disk_library(self.library_name, self.ma1_name, self.mountpath1)
        self.log.info("Library [%s] created successfully.", self.library_name)



        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.sp_obj = self.dedup_helper_obj.configure_dedupe_storage_policy(
            self.storage_policy_name, self.library_name, self.ma1_name, self.dedup_path, self.ma2_name)
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)

        # Add Mountpath
        self.log.info("Adding Mountpath [%s] to Library [%s]", self.mountpath2, self.library_name)
        self.mahelper_obj.configure_disk_mount_path(self.disklib_obj, self.mountpath2, self.ma2_name)

        #Enable Preferred Datapath Setting
        self.enable_preferred_datapath(1)

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.backupset_name = f"BkpSet_TC_{self.id}_{self.ma1_name}"
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name, self.ma_client_agent)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        for id in range(1, 5):
            content_path = self.client_machine_obj.join_path(self.content_path, str(id))
            if self.client_machine_obj.check_directory_exists(content_path):
                self.log.info("Deleting already existing content directory [%s]", content_path)
                self.client_machine_obj.remove_directory(content_path)
            self.client_machine_obj.create_directory(content_path)
            subclient_name = f"{self.subclient_name}_{id}"
            self.log.info("Configuring Subclient [%s_%s]", self.subclient_name, id)
            self.mahelper_obj.create_uncompressable_data(self.ma1_client_obj.client_name, content_path, 1, 1)
            self.subclient_obj_list.append(self.mahelper_obj.configure_subclient(
                self.backupset_name, subclient_name, self.storage_policy_name, content_path, self.ma_client_agent))
            self.log.info("Successfully configured Subclient [%s]", subclient_name)

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

    def configure_resources_for_roundrobin(self):
        """
        Configure resources for Round Robin Testcase
        """

        # Enable Preferred Datapath Setting
        self.enable_preferred_datapath(2)
        self.subclient_obj_list=[]
        self.client_machine_obj = Machine(self.client.client_name, self.commcell)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 30)
        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, str(self.id), "Content")
        self.log.info("Configuring Backupset [%s] on Client [%s]", self.backupset_name, self.client.client_name)
        self.backupset_name = f"BkpSet_TC_{self.id}_{self.client.client_name}"
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name, self.agent)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        for id in range(1, 5):
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


    def run_parallel_backups(self):
        """
        Run backups on all subclients in parallel
        Return:
            Return list of job objects
        """
        job_list = []
        for num in range(1,5):
            job_list.append(self.subclient_obj_list[num-1].backup("Full"))

            self.log.info("Successfully initiated a FULL backup job on subclient [%s] with job id [%s]",
                          self.subclient_obj_list[num-1].subclient_name,
                          job_list[-1].job_id)
        return job_list

    def get_reservation_ids(self, job_list, verify_for):
        """
        Get reservation ID for give list of running jobs
        Args:
            job_list (list of obj)  -- List of job objects
            verify_for (int)        -- 1 = Preferred Datapath Setting, 2 = Round-Robin Setting
        """
        self.log.info("Waiting for all the jobs to complete")
        for job in job_list:
            if not job.wait_for_completion():
                raise Exception(f"Failed to run backup job [{job.job_id}] with error: {job.delay_reason}")
            self.log.info(f"Backup job {job.job_id} completed successfully")

        job_id_list = [str(job_obj.job_id) for job_obj in job_list]

        query = "select JobId, ReservationId, MountpathId, ClientId, volumeid from RMReservations where JobId in " \
                f"({','.join(job_id_list)})"
        self.log.info("QUERY => %s", query)
        self.csdb.execute(query)
        reservation_id_mapping = self.csdb.fetch_all_rows()
        self.log.info("[JobId, ReservationId, MountPathID] ==> %s", str(reservation_id_mapping))
        mountpath_id_list = [mp[2] for mp in reservation_id_mapping]
        reservation_mountpath_dict = {}
        for item in reservation_id_mapping:
            reservation_mountpath_dict[item[1]] = item[2]

        query = "select App_Client.name, MMDeviceController.folder from " \
                "MMDeviceController,MMMountPathToStorageDevice," \
                f"APP_Client where MMMountPathToStorageDevice.MountPathId in ({','.join(mountpath_id_list)})" \
                "and MMDeviceController.DeviceId = MMMountPathToStorageDevice.DeviceId and " \
                "MMDeviceController.folder != '' and App_Client.id in (MMDeviceController.ClientId)"
        self.log.info("QUERY => %s", query)
        self.csdb.execute(query)
        list_of_mountpaths = self.csdb.fetch_all_rows()
        self.log.info("List of Mount Paths used : %s", str(list_of_mountpaths))
        list_of_clients = [item[0] for item in list_of_mountpaths]

        if verify_for == 1:
            self.log.info("Verifying for Test Case - Use Preferred Data Path Option")
            #Find out how many times each mountpath was used
            is_fail = False
            for index in range(len(list_of_clients)):
                if list_of_clients[index].lower() != self.ma1_name.lower():
                    self.log.error("Validation Failure : At least one job [%s] has not used local MA for backups",
                                   job_id_list[index])
                    is_fail = True

            if is_fail:
                self.error_string = self.error_string + \
                                    "[Use Preferred Data Path Option : One more more jobs did not consume local " \
                                    "resources (mountpaths) as expected]"
                self.log.error(self.error_string)
            self.log.info("Successfully verified that Lan-Free backups have been performed using MA - [%s]",
                          list_of_clients[0])
            self.lanfree_volumeid = reservation_id_mapping[0][4]

        elif verify_for == 2:
            self.log.info("Verifying for Test Case - Round Robin Option")
            #Verify that even MA names are same and odd MA names are same
            mountpath_client_id_tuple_list = [(item[2], item[3]) for item in reservation_id_mapping]
            self.log.info("Mountpath ID & Client ID tuples for jobs ==> [%s]", mountpath_client_id_tuple_list)
            if mountpath_client_id_tuple_list[0] == mountpath_client_id_tuple_list[2] and \
                    mountpath_client_id_tuple_list[1] == mountpath_client_id_tuple_list[3]:
                self.log.info("Datapaths were picked in Round Robin Fashion as Mountpaths are "
                              "picked is alternate fashion - [%s]", mountpath_id_list )
            else:
                self.log.error("Datapaths were not picked in Round Robin Fashion as Mountpaths are not picked "
                               "in alternate fashion - [%s]", mountpath_id_list)
                self.error_string = self.error_string + \
                                    "[Round-Robin between Data Paths Option : " \
                                    "Jobs did not use Round Robin mechanism while consuming  resources]"
                self.log.error(self.error_string)
        elif verify_for == 3:
            self.log.info("Verifying for Test Case - Datapath Failover Scenario")
            if mountpath_id_list[0] != mountpath_id_list[1]:
                self.log.info("As expected : Job [%s] used 2 different mountpaths - [%s]", job_list[0].job_id,
                              mountpath_id_list)
            else:
                self.log.error("Job [%s] used same mountpath - [%s] which is not expected", job_list[0].job_id,
                               mountpath_id_list[0])
                self.error_string += f"job {job_list[0].job_id} used same mountpath - [{mountpath_id_list[0]}] " \
                                     "even with Failover Setting"

            if self.verify_mp_offline(mountpath_id_list[0]) == 0:
                self.log.info("Successfully verified that Mountpath [%s] is online", mountpath_id_list[0])
            else:
                self.log.error("Mountpath [%s] is still offline which is not expected", mountpath_id_list[0])
                self.error_string += f"Mountpath [{mountpath_id_list[0]} is still offline after whole " \
                                     "Datapath Failover test"

    def verify_mp_offline(self, mountpath_id, wait_time=0):
        """
        Check if mountpath is offline

        Args:
            mountpath_id    (int)   --  Mountpath ID whose state needs to be checked
            wait_time       (int)   --  Optional time for which state check will be retried with interval of
                                        every 2 minutes

        Returns :
            Value of IsOffline as an integer
        """
        query = f"select Isoffline from MMMountPath where MountPathId = {mountpath_id}"
        self.log.info("QUERY => %s", query)
        offline = 0
        index = 0
        self.csdb.execute(query)
        offline = self.csdb.fetch_one_row()
        while wait_time > 0:
            index += 1
            self.log.info("Verifying if Mountpath is marked as offline : Attempt [%s]", index)
            self.csdb.execute(query)
            offline = self.csdb.fetch_one_row()
            if offline and offline[0] == '1':
                self.log.info("As expected : Mountpath ID [%s] is marked offline", mountpath_id)
                break
            else:
                self.log.info("Mountpath is not offline, checking again after 2 minutes")
                time.sleep(120)
                wait_time -= 120

        return int(offline[0])

    def wait_till_ma_offline(self, job_obj):
        """
        Wait till MA is marked offline in CSDB after service stop is issued.

        Args:
            job_obj (object)    --  Job Object

        Returns:
            Mountpath ID of the offline MP
        """
        query = f"select JobId, ReservationId, MountpathId, ClientId from RMReservations where JobId = {job_obj.job_id}"
        self.log.info("QUERY => %s", query)
        self.csdb.execute(query)
        reservation_id_mapping = self.csdb.fetch_all_rows()
        self.log.info(reservation_id_mapping)
        mountpath_id_list = [mp[2] for mp in reservation_id_mapping]
        if len(mountpath_id_list) != 1:
            self.log.error("Job [%s] has used more than 1 mountpaths during backup - [%s]", job_obj.job_id,
                           mountpath_id_list)
            self.error_string += f"[Job {job_obj.job_id} has used more than 1 mountpaths for backup before " \
                                 f"failover. MPs = [{mountpath_id_list}]"
            raise Exception(self.error_string)
        else:
            self.log.info("As expected, only 1 Mountpath is being used by Backup job before Failover")

        offline = self.verify_mp_offline(mountpath_id_list[0], wait_time=600)

        if offline == 0:
            self.log.error("Mountpath [%s] is not marked offline even after 10 minutes", mountpath_id_list[0])
            self.error_string += f"[Mountpath [{mountpath_id_list[0]}] is not marked offline even after 10 minutes]"
            raise Exception(self.error_string)
        else:
            self.log.info("Resuming the backup job [%s] and waiting till it is in Running state and Backup Phase",
                          job_obj.job_id)
            job_obj.resume()
            self.wait_till_backup_phase(job_obj)

        return mountpath_id_list[0]

    def clean_test_environment(self):
        """
        Clean up test environment
        """
        self.client_machine_obj = Machine(self.ma1_name, self.commcell)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj)
        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, str(self.id), "Content")

        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", self.content_path)
            self.client_machine_obj.remove_directory(self.content_path)

        if self.client_machine_obj.check_directory_exists(self.restore_path):
            self.log.info("Deleting already existing Restore directory [%s]", self.restore_path)
            self.client_machine_obj.remove_directory(self.restore_path)

        try:
            self.log.info("Deleting BackupSet on Client which was MA")
            self.backupset_name = f"BkpSet_TC_{self.id}_{self.ma1_name}"
            if self.ma_client_agent.backupsets.has_backupset(self.backupset_name):
                self.ma_client_agent.backupsets.delete(self.backupset_name)
        except Exception as excp:
            self.log.warning("***Failure in deleting backupset during cleanup. "
                             "Treating as soft failure as backupset will be reused - [%s]***", str(excp))

        self.client_machine_obj = Machine(self.client.client_name, self.commcell)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj)
        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, str(self.id), "Content")

        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", self.content_path)
            self.client_machine_obj.remove_directory(self.content_path)

        try:
            self.log.info("Deleting BackupSet on Client")
            self.backupset_name = f"BkpSet_TC_{self.id}_{self.client.client_name}"
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
        except Exception as excp:
            self.log.warning("***Failure in deleting backupset during cleanup. "
                          "Treating as soft failure as backupset will be reused - [%s]***", str(excp))
        try:
            self.log.info("Deleting Storage Policy")
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
        except Exception as excp:
            self.log.info("***Failure in deleting storage policy during cleanup. "
                          "Treating as soft failure as stroage policy will be reused - [%s]***", str(excp))
        try:
            self.log.info("Deleting Library")
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
        except Exception as excp:
            self.log.info("***Failure in deleting library during cleanup. "
                          "Treating as soft failure as library will be reused - [%s]***", str(excp))


    def enable_preferred_datapath(self, enable=1):
        """
        Enable or Disable Preferred Datapath setting on Storage Policy Copy

        Args:
            enable  (Integer)   :   1 = Preferred Datapath, 2 = Round-Robin, 3 = Failover
        """
        copy_obj = self.commcell.storage_policies.get(self.storage_policy_name).get_copy('Primary')
        self.log.info("Before Changing Copy Properits - [%s]", copy_obj._copy_properties['copyFlags'])
        if enable == 1:
            self.log.info("Enabling Preferred Datapath Setting")
            copy_obj._copy_properties['copyFlags']['roundRobbinDataPath'] = 0
        elif enable == 2:
            self.log.info("Disabling Preferred Datapath Setting")
            copy_obj._copy_properties['copyFlags']['roundRobbinDataPath'] = 1
        else:
            self.log.info("Enabling Failover Setting")
            copy_obj._copy_properties['copyFlags']['roundRobbinDataPath'] = 0
            copy_obj._copy_properties['copyFlags']['switchIfBusy'] = 1
            copy_obj._copy_properties['copyFlags']['switchIfOffline'] = 1

        copy_obj._set_copy_properties()
        copy_obj.refresh()
        self.log.info("After Changing Copy Properits - [%s]", copy_obj._copy_properties['copyFlags'])

    def wait_till_backup_phase(self, job_obj):
        """
        Wait till job is in Running state and in Backup Phase
        """
        wait_count = 600
        while wait_count:
            self.log.info("Waiting for Job [%s] to be in Backup Phase and in Running state", job_obj.job_id)
            if job_obj.phase.lower() == 'backup' and job_obj.status.lower() == 'running':
                self.log.info("Job [%s] is in Backup Phase and Running State.", job_obj.job_id)
                break
            else:
                self.log.info("Checking Phase & State of job [%s] again after 5 seconds", job_obj.job_id)
                time.sleep(5)
                wait_count -= 5
        if wait_count == 0:
            self.log.error("Backup Job [%s] has not entered Running State for Backup Phase in 600 seconds",
                           job_obj.job_id)
            self.error_string += f"[Job {job_obj.job_id} did not enter Running State for Backup Phase in 600 seconds]"
            raise Exception(self.error_string)

    def run_big_backup(self):
        """
        Run a long running backup
        """

        subc = self.subclient_obj_list[0]
        content_path = self.client_machine_obj.join_path(self.content_path, "1")
        self.log.info("Generating 15 GB content for failover test case")
        self.mahelper_obj.create_uncompressable_data(self.client.client_name, content_path, 1, 15)
        job_obj = subc.backup("Full")
        self.log.info("Successfully initiated a FULL backup job on subclient [%s] with job id [%s]",
                      subc.subclient_name,
                      job_obj.job_id)

        self.wait_till_backup_phase(job_obj)
        self.log.info("Job [%s] is now in Running State for Backup Phase", job_obj.job_id)
        time.sleep(15)
        return job_obj

    def validate_job_pending(self, job_obj):
        """
        Validate that job has gone pending
        Args:
            job_obj (object)    -- Job object
        """
        timeout = 600
        while timeout != 0:
            job_status = job_obj.status.lower()
            self.log.info("Expected Status : [pending] & Current Status : [%s]", job_status)
            if job_status.lower() != 'pending':
                self.log.info("Job is still not in Pending State - Sleeping for 30 seconds")
                time.sleep(30)
                timeout -= 30
            else:
                self.log.info("Job is in pending state now.")
                break
        if timeout == 0:
            self.error_string += f"[Job {job_obj.job_id} did not enter Pending state even after 10 minutes]"
            self.log.error(self.error_string)
            raise Exception(self.error_string)

    def start_stop_ma_services(self, action="Stop"):
        """
        Start or Stop MA service

        Args:
            action  (str)       --      Start or Stop the serivces
        """

        self.log.info("Performing [%s] operation on client %s", action, self.ma1_name)

        if action.lower() == 'stop':
            self.ma1_client_obj.stop_service()
        else:
            self.ma1_machine_obj.start_all_cv_services()

    def verify_lanfree_restore(self):
        """
        Verify that restore also uses Lan Free Datapath
        """
        self.log.info("starting restore job...Destination : %s", self.restore_path)
        job_obj = self.subclient_obj_list[0].restore_out_of_place(self.ma1_client_obj.client_name, self.restore_path,
                                                               [self.client_machine_obj.join_path(self.content_path,
                                                                                                  str(1))])
        if not job_obj.wait_for_completion():
            raise Exception("Failed to run restore job with error: {0}".format(job_obj.delay_reason))
        self.log.info("restore job: %s completed successfully", job_obj.job_id)

        # Compare data
        self.log.info("Performing data comparison between source & destination MAs")
        source_path = self.client_machine_obj.join_path(self.content_path,str(1))
        dest_path = self.client_machine_obj.join_path(self.restore_path, str(1))
        self.log.info("Comparing Source & Destination for restore operation - Source [%s] Destination [%s]",
                      source_path, dest_path)
        diff_files = self.client_machine_obj.compare_folders(self.client_machine_obj, source_path, dest_path)

        if not diff_files:
            self.log.info("Restore validation successful")
        else:
            self.log.error("Restore Validation Failed : Diff = %s", str(diff_files))
            raise Exception("Checksum Validation after restore failed for Backup which used 2 resources (mountpaths)")

        hostname = self.ma1_name
        for attempt in range(2):
            if attempt == 1:
                hostname = self.ma1_name.upper()
            verify_str = f"Loading the VolId={self.lanfree_volumeid} HostName={hostname}"
            self.log.info("Verifying following string in Logs : %s", verify_str)
            volumeid_match_str = self.dedup_helper_obj.parse_log(
                self.ma1_name, "CVD.log", verify_str, job_obj.job_id, True)[0]
            self.log.info(volumeid_match_str)
            if volumeid_match_str:
                self.log.info("Successfully verified that Restore operation used Lan-Free Datapath")
                break
            else:
                if attempt == 1:
                    self.log.error("Failed to verify log which indicates that Restore operation might not have used "
                               "Lan-Free Datapath.")
                    self.error_string += "[Restore job did not use Lan-Free Datapath]"
                else:
                    self.log.warning("Failed to verify log, will check with capitalized Hostname")

    def run(self):
        """Run function of this test case"""
        try:

            self.clean_test_environment()
            self.configure_tc_environment()

            self.log.info("Test 1 : Use Preferred Data Path Option")
            job_list = self.run_parallel_backups()
            self.get_reservation_ids(job_list, 1)

            self.verify_lanfree_restore()
            if not self.error_string:
                self.log.info("Test 1 : SUCCESS : Test case completed successfully")
            else:
                self.log.error("Test 1 : FAILURE : %s", self.error_string)

            #Reinitializing error_string to avoid scenario where TC1 failure leads to TC2 failure as well even when
            #it has passed just because error_string is not ""
            _error_string_backup = self.error_string
            self.error_string = ""
            self.log.info("Test 2 : Round-Robin between Data Paths Option")

            self.configure_resources_for_roundrobin()
            job_list = self.run_parallel_backups()
            self.get_reservation_ids(job_list, 2)


            if not self.error_string:
                self.log.info("Test 2 : SUCCESS : Test case completed successfully")
            else:
                self.log.error("Test 2 : FAILURE : %s", self.error_string)

            _error_string_backup += self.error_string
            self.error_string = ""

            self.log.info("Test 3 : Failover between Data Paths Option")
            self.enable_preferred_datapath(3)
            big_bkp_job = self.run_big_backup()
            self.start_stop_ma_services(action="stop")
            self.validate_job_pending(big_bkp_job)
            self.wait_till_ma_offline(big_bkp_job)
            self.start_stop_ma_services(action="start")
            self.get_reservation_ids([big_bkp_job], 3)
            if not self.error_string:
                self.log.info("Test 3 : SUCCESS : Test case completed successfully")
            else:
                self.log.error("Test 3 : FAILURE : %s", self.error_string)
            _error_string_backup += self.error_string
            if _error_string_backup:
                raise Exception(_error_string_backup)

        except Exception as exp:
            self.status = constants.FAILED
            self.result_string = str(exp)
            self.log.error('Failed to execute test case with error: %s', (str(exp)))

    def tear_down(self):
        """Tear down function of this test case"""
        self.ma1_machine_obj.start_all_cv_services()
        if self.status == constants.FAILED:
            self.log.info("Not performing cleanup as test case has failed.")
        else:
            self.log.info("Cleaning up Tescase Environment")
            self.clean_test_environment()
