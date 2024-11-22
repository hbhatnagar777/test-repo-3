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
    __init__()                --  initialize TestCase class

    setup()                   --  setup function of this test case

    run()                     --  run function of this test case

    tear_down()               --  tear down function of this test case

    run_cleanup()   --  delete previous run items

    disable_ransomware_protection(client_id, media_agent_obj) --  disable ransomware protection on client

    create_resources()        --  create resources for testcase

    run_backup(backup_level)  --  runs backup job

    get_volume_id(chunk_id)   --  get the volume id of the chunk

    get_chunk_path(volume_id, chunk_id) --  get physical size of each volume from mountpath

    remove_permissions(chunk_path)  --  remove the permissions to allow for manipulations on the backup

    rename_sfile(chunk_path, orig_name, new_name) --  rename the SFILE from the backup

    run_ddb_verification(storage_policy, dv2_type, verification_level) --  run ddb verification

    mark_next_backup_full() --  mark the next backup as full if DV2 failed with database update and stored
                                        procedure

    verify_dv2_job_status(dv2_job, error_present) --  check if DV2 job succeeded

    verify_backup_leel(backup_job, backup_level) --  check if backup job automatically changed the backup level

    verify_chunk_in_archchunkddbdrop(store_id, job_id, chunk_id, chunk_present) --  verify if Chunk shows up in
                                                                                    ArchChunkDDBDrop table

    verify_archcheck_status(job_id) --  verify that the archcheckstatus in csdb for jobid is failed

    get_active_files_store()    -- Get active SIDB store object for storage policy

Sample Input:
    "63279": {
        "ClientName": "Client Name",
        "AgentName": "File System",
        "MediaAgentName": "MA Name",
        [Optional ***
        "dedup_path" : "ddb path",
         "mount_path" : "mount path"
         ]
    }


Design Steps :

Cleanup previous run environment
Create test environment

1) Run 1st Backup job
2) Get the Sfile Location
3) Raname the sfile to sfile_org
4) Run Incremetnal DV2 job
5) Validate chunk marked bad in DDBDrop table and job verification status should be fail
6) Submit 2nd backup job
7) check the data written for job1 and job2 - both should be same as job2 will not reference job1
8) Add the Reverf Regkey
9) Raname back the chunk sfile_org to sfile
10) pick the job for verification
11) Run Incremental DV2
12) Check if we repick the chunk for verification which marked bad at #5
13) DV2 phase 2 should mark the job status as verificaiton successful.

"""

import time
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Force reverification of bad chunks and jobs during DV2 job"
        self.storage_policy_copy = None
        self.sidb_store_obj = None
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.sidb_id = None
        self.substore_id = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.media_agent_name = None
        self.storage_pool = None
        self.storage_pool_name = None
        self.plan_name = None
        self.plan = None
        self.media_agent_obj = None
        self.chunk_path_1 = None
        self.chunk_path_2 = None
        self.reset_ransomware = False
        self.is_user_defined_dedup = False
        self.is_user_defined_mp = False
        self.ma_library_drive = None
        self.tcinputs = {
            "MediaAgentName": None
        }

    def setup(self):
        """sets up the variables to be used in testcase"""
        self.log.info("Setting up testcase variables and objects")
        self.media_agent_name = self.tcinputs["MediaAgentName"]
        suffix = round(time.time())
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True

        self.storage_pool_name = f"STORAGEPOOL_{self.id}_{self.media_agent_name}"
        self.plan_name = f"PLAN_{self.id}_{self.media_agent_name}"
        self.backupset_name = f"{self.id}_BS"
        self.subclient_name = f"{self.id}_SC"

        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(self.media_agent_name, self.commcell)
        self.media_agent_obj = self.commcell.media_agents.get(self.media_agent_name)

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25 * 1024)
        if not self.is_user_defined_mp:
            self.ma_library_drive = self.opt_selector.get_drive(self.media_agent_machine, 25 * 1024)

        if self.is_user_defined_mp:
            self.mount_path = self.media_agent_machine.join_path(self.tcinputs.get("mount_path"), f"TC_{self.id}", f"LIB_{suffix}")
            self.log.info(f"Using user provided mount path {self.mount_path}")
        else:
            self.mount_path = self.media_agent_machine.join_path(self.ma_library_drive, f"TC_{self.id}", f"LIB_{suffix}")

        if not self.is_user_defined_dedup:
            self.dedup_store_path = self.media_agent_machine.join_path(self.ma_library_drive, f"TC_{self.id}", f"DDB_{suffix}")
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs.get("dedup_path"), f"TC_{self.id}", f"DDB_{suffix}")
            self.log.info(f"Using user provided dedup path {self.dedup_store_path}")

        self.content_path = self.client_machine.join_path(drive_path_client, f"TC_{self.id}_CONTENT")
        self.mark_next_backup_full(enable=False)

    def run_cleanup(self):
        """delete previous run items"""
        self.log.info("********* Clean UP **********")
        try:
            if self.media_agent_machine.check_registry_exists('MediaAgent', 'SIDBDVReverifyChunksFlg'):
                self.log.info("Removing SIDBDVReverifyChunksFlg reg key from MA")
                self.media_agent_machine.remove_registry('MediaAgent', value='SIDBDVReverifyChunksFlg')
                self.log.info("Removed the registry key")
            else:
                self.log.info("Reg key does not exist.")
            self.mark_next_backup_full(enable=False)
            if self.media_agent_machine.os_info.lower() == 'windows':
               self.log.info(f"Enabling ransomware protection on {self.media_agent_name}")
               self.media_agent_obj.set_ransomware_protection(True) 

            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("backup set deleted")
            else:
                self.log.info("backup set does not exist")
            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Reassociating all subclients to None")
                self.plan.storage_policy.reassociate_all_subclients()
                self.log.info(f"Deleting plan {self.plan_name}")
                self.commcell.plans.delete(self.plan_name)
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info("deleting storage pool: %s", self.storage_pool_name)
                self.commcell.storage_pools.delete(self.storage_pool_name)
            self.log.info("Refresh libraries")
            self.commcell.disk_libraries.refresh()
            self.log.info("Refresh Storage Pools")
            self.commcell.storage_pools.refresh()
            self.log.info("Refresh Plans")
            self.commcell.plans.refresh() 
            self.log.info("Clean COMPLETED")
        except Exception as exp:
            self.log.info(f"ERROR: {exp}")

    def disable_ransomware_protection(self, media_agent_obj):
        """
            disable ransomware protection on client
            Args:
                media_agent_obj (obj)  --  MediaAgent object for the testcase run
        """
        ransomware_status = self.mm_helper.ransomware_protection_status(
            self.commcell.clients.get(media_agent_obj.name).client_id)
        self.log.info("Current ransomware status is: %s", ransomware_status)
        if ransomware_status:
            self.reset_ransomware = True
            self.log.info("Disabling ransomware protection on %s", media_agent_obj.name)
            media_agent_obj.set_ransomware_protection(False)
        else:
            self.log.info(f"Ransomware protection is already disabled on {media_agent_obj.name}")

    def create_resources(self):
        """
            create resources for testcase
        """
        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.log.info(f"Creating a storage pool {self.storage_pool_name}")
            self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mount_path,
                                                                self.media_agent_name,
                                                                [self.media_agent_name] * 2,
                                                                [self.dedup_store_path, self.dedup_store_path])
        else:
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)
            self.log.info(f"Pool [{self.storage_pool_name}] exists")

        if not self.commcell.plans.has_plan(self.plan_name):
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.storage_pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")
        else:
            self.plan = self.commcell.plans.get(self.plan_name)
            self.log.info(f"Plan [{self.plan_name}] exists")

        self.storage_policy_copy = self.plan.storage_policy.get_copy('Primary')
        self.plan.schedule_policies['data'].disable()

        # use the storage policy object
        # from it get the storage policy id
        # get the sidb store id and sidb sub store id
        return_list = self.dedup_helper.get_sidb_ids(self.plan.storage_policy.storage_policy_id, "Primary")
        self.sidb_id = int(return_list[0])
        self.substore_id = int(return_list[1])

        # create backupset and subclient
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
        self.log.info("Backup set created")
        if not self.backup_set.subclients.has_subclient(self.subclient_name):
            self.subclient = self.backup_set.subclients.add(self.subclient_name)
            self.subclient.plan = [self.plan, [self.content_path]]
            self.log.info(f"Created subclient {self.subclient_name}")
        else:
            self.log.info(f"subclient {self.subclient_name} exists")
            self.subclient = self.backup_set.subclients.get(self.subclient_name)
        self.log.info(f"set the data readers for subclient {self.subclient_name} to 1")
        self.subclient.data_readers = 1

        # generate unique random data for the testcase
        data_size = 1
        if self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path,
                                                     float("{0:.1f}".format(data_size)), 1):
            self.log.info("generated unique data for subclient")
        else:
            raise Exception("couldn't generate unique data")

        if self.media_agent_machine.os_info.lower() == 'windows':
           self.disable_ransomware_protection(self.media_agent_obj)

    def run_backup(self, backup_level):
        """
            runs backup job
            Args:
                backup_level (str)  --  full or incremental backup level
            Returns
                tuple that contains backup job object and list of chunk IDs
        """
        # run the backup job
        self.log.info("Starting %s backup job", backup_level)
        backup_job = self.subclient.backup(backup_level.upper())
        self.log.info("Backup job ID: %s", backup_job.job_id)
        if not backup_job.wait_for_completion():
            raise Exception(
                f"Job {backup_job.job_id} Failed with {backup_job.delay_reason}")

        query = f"""SELECT    archchunkid
                    FROM      archchunkmapping
                    WHERE     archfileid
                    IN       ( SELECT    id
                                FROM      archfile 
                                WHERE     jobid={backup_job.job_id} 
                                AND       filetype=1)"""
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"Result of query : {res}")
        chunks = []
        for i in range(len(res)):
            chunks.append(res[i][0])
        self.log.info("got the chunks belonging to the backup job")
        self.log.info("Chunks are: %s", chunks)
        return backup_job, chunks

    def get_volume_id(self, chunk_id):
        """
        get the volume id of the chunk
            Args:
                chunk_id (str)  --  Chunk ID
            Return:
                volume id of the chunk
        """
        self.log.info("Getting volume id of chunk %s", chunk_id)
        query = f"""SELECT    volumeid
                    FROM archchunk
                    WHERE id = {chunk_id}"""
        self.log.info(f"EXECUTING QUERY {query}")
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()
        self.log.info(f"Result of query : {res}")
        volume_id = res[0]
        self.log.info(f"Volume id of chunk {chunk_id}, {volume_id}")
        return volume_id

    def get_chunk_path(self, volume_id, chunk_id):
        """
        get physical size of each volume from mountpath
        Args:
            volume_id (str)  --  Volume ID
            chunk_id (str)   --  Chunk ID

        Return:
            String of chunk path
        """
        # Get physical location of the volume
        self.log.info("Fetching physical location of volume : %s", volume_id)
        query = "select MMV.volumeid, MMDC.folder, MNTPATH.MountPathName, CL.name " \
                "from MMMountpath MNTPATH, MMDeviceController MMDC, MMMountPathToStorageDevice MMPS, MMVOLUME MMV " \
                ", App_Client CL where MMPS.MountPathId = MMV.CurrMountPathId and " \
                "MNTPATH.MountPathId = MMV.CurrMountPathId and CL.id = MMDC.clientid " \
                f" and MMDC.deviceid = MMPS.DeviceId and MMV.volumeid = {volume_id}"
        self.log.info(f"Query {query}")
        self.csdb.execute(query)
        # Now work out the path for each of the volume and fetch its size
        physical_location_list = self.csdb.fetch_all_rows()[0]
        self.log.info(f"Query output: {physical_location_list}")
        chunk_path = self.media_agent_machine.join_path(physical_location_list[1], 
                                                        physical_location_list[2],
                                                        "CV_MAGNETIC",
                                                        f"V_{volume_id}",
                                                        f"CHUNK_{chunk_id}")
        self.log.info(f"Chunk path is {chunk_path}")
        return chunk_path

    def remove_permissions(self, chunk_path):
        """
            remove the permissions to allow for manipulations on the backup
            Args:
                chunk_path (str)  --  Path of the chunk
        """
        self.log.info(
            "Removing permissions from volume to allow for manipulations on the backup")
        volume_path_list = chunk_path.split(self.media_agent_machine.os_sep)[:-1]
        volume_path = self.media_agent_machine.os_sep.join(volume_path_list)

        self.media_agent_machine.modify_ace('Everyone', volume_path,
                                            'DeleteSubdirectoriesAndFiles',
                                            'Deny', remove=True, folder=True)
        self.media_agent_machine.modify_ace('Everyone', volume_path,
                                            'Delete',
                                            'Deny', remove=True, folder=True)

    def rename_sfile(self, chunk_path, orig_name, new_name):
        """
            rename the SFILE from the backup
            Args:
                chunk_path (str)  --  Path of the chunk
                orig_name (str)   --  Original name of the file
                new_name (str)    --  New name of the file
        """
        self.log.info("Renaming %s to %s", orig_name, new_name)
        old_file_path = self.media_agent_machine.join_path(
            chunk_path, orig_name)
        new_file_path = self.media_agent_machine.join_path(
            chunk_path, new_name)
        self.log.info(old_file_path)
        self.log.info(new_file_path)
        self.media_agent_machine.rename_file_or_folder(
            old_file_path, new_file_path)

    def run_ddb_verification(self, is_incr_dv2, is_quick_dv2):
        """
            run ddb verification
            Args:
                is_incr_dv2 (bool)           --  Is Incremental DV2 to be submitted or not
                is_quick_dv2 (bool)       --  Is this a quick DV2 request
            Returns:
                job object of the verification job
        """
        self.log.info("Running DDB verification")
        job = self.sidb_store_obj.run_ddb_verification(incremental_verification=is_incr_dv2,
                                                       quick_verification=is_quick_dv2)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run dv2 job with error: {job.delay_reason}")
        self.log.info(f"DV2 job completed having job id {job.job_id}.")
        return job

    def mark_next_backup_full(self, enable=True):
        """
            mark the next backup as full if DV2 failed with database update and stored procedure
        """
        # use for tear_down == 0
        if not enable:
            self.mm_helper.update_mmconfig_param('MMCONFIG_MARK_NEXT_BKP_FULL_FOR_DV_FAILED_SUBCLIENTS', 0, 0)
        else:
            self.log.info("Running stored proc ArchMarkNextBackupFullForDVFailedSCs")
            self.mm_helper.update_mmconfig_param('MMCONFIG_MARK_NEXT_BKP_FULL_FOR_DV_FAILED_SUBCLIENTS', 0, 1)
            self.mm_helper.execute_stored_proc("ArchMarkNextBackupFullForDVFailedSCs", ("0",))
        self.log.info("Sleeping for 60 seconds")
        time.sleep(60)

    def verify_dv2_job_status(self, dv2_job, error_present):
        """
            check if DV2 job succeeded
            Args:
                dv2_job (object)      --  DV2 job object
                error_present (bool)  --  True if error should be present, False otherwise
        """
        if (error_present is False and dv2_job.state.lower() == 'completed') \
                or (error_present is True and dv2_job.state == 'Completed w/ one or more errors'):
            self.log.info("DV2 Job %s Verifying Status Success",
                          dv2_job.job_id)
        else:
            raise Exception(f"DV2 Job {dv2_job.job_id} Verifying Status Failed")

    def verify_backup_level(self, backup_job, backup_level):
        """
            check if backup job automatically changed the backup level
            Args:
                backup_job (object)  --  backup job object
                backup_level (str)   --  expected backup level
        """
        if backup_job.backup_level.lower() == backup_level.lower():
            self.log.info(f"Verified backup level of job {backup_job.job_id}, {backup_level}")
        else:
            raise Exception(f"Failed to verify backup level of job {backup_job.job_id}: Result is not {backup_level}")

    def verify_chunk_in_archchunkddbdrop(self, store_id, job_id, chunk_id, chunk_present):
        """
        verify if Chunk shows up in ArchChunkDDBDrop table
            Args:
                store_id (int)        --  Store ID
                job_id (str)          --  DV2 Job ID
                chunk_id (str)        --  Chunk ID
                chunk_present (bool)  --  True if chunk should be present, False otherwise
        """
        self.log.info("Verifying if chunk is present in the table")
        query = f"""SELECT archchunkid
                    FROM archchunkddbdrop
                    WHERE sidbstoreid={store_id}
                    AND reserveint={job_id}"""
        self.log.info("Query => %s", query)                    
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"Result of query : {res}")

        if chunk_present:
            if chunk_id == res[0][0]:
                self.log.info("Chunk present in the table")
            else:
                raise Exception("Chunk not present in the table")
        else:
            if res[0][0] == "":
                self.log.info("Chunk not present in the table")
            else:
                raise Exception("Chunk present in the table")

    def verify_archcheck_status(self, job_id, archstatus):
        """
            verify that the archcheckstatus in csdb for jobid is failed
            Args:
                job_id (str)  --  Backup Job ID
                archstatus (int) -- status of data verification
        """
        query = f'''select distinct archCheckStatus
            from JMJobDataStats
            where jobId = {job_id} and dataType = 1'''
        self.log.info(f"Query {query}")
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info(f"Result of query : {rows}")
        if rows[0][0] == str(archstatus):
            self.log.info(f"Sucessfully Verified archCheckStatus, expected = {archstatus} and actual = {rows[0][0]}")
            return rows
        else:
            raise Exception(f"archCheckStatus Verification Failed expected = {archstatus} and actual = {rows[0][0]}")

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.storage_pool_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def run(self):
        """run function of this testcase"""
        try:
            self.run_cleanup()
            self.create_resources()
            self.log.info("Starting backup #1")
            backup_result_1 = self.run_backup("Full")
            backup_job_1 = backup_result_1[0]
            chunk_id_1 = backup_result_1[1][0]

            self.verify_backup_level(backup_job_1, "Full")
            self.sidb_store_obj = self.get_active_files_store()
            volume_id_1 = self.get_volume_id(chunk_id_1)
            self.chunk_path_1 = self.get_chunk_path(volume_id_1, chunk_id_1)
            self.log.info("Starting verification #1")

            ddb_verification_job_1 = self.run_ddb_verification(is_incr_dv2=True, is_quick_dv2=False)
            self.verify_dv2_job_status(ddb_verification_job_1, error_present=False)
            self.verify_chunk_in_archchunkddbdrop(
                self.sidb_id, ddb_verification_job_1.job_id, chunk_id_1, chunk_present=False)
            if self.media_agent_machine.os_info.lower() == 'windows':    
                self.remove_permissions(self.chunk_path_1)
            self.rename_sfile(self.chunk_path_1, 'SFILE_CONTAINER_001', 'SFILE_CONTAINER_001_RENAMED')

            self.log.info("Starting verification #2")
            ddb_verification_job_2 = self.run_ddb_verification(is_incr_dv2=False, is_quick_dv2=False)
            self.verify_dv2_job_status(ddb_verification_job_2, error_present=True)

            self.verify_chunk_in_archchunkddbdrop(self.sidb_id, ddb_verification_job_2.job_id, chunk_id_1, chunk_present=True)
            self.verify_archcheck_status(backup_job_1.job_id, 6)

            backup_result_2_pre = self.run_backup("Incremental")
            backup_job_2_pre = backup_result_2_pre[0]

            self.verify_backup_level(backup_job_2_pre, "Incremental")
            self.mark_next_backup_full()
            self.log.info("Starting backup #2")
            backup_result_2 = self.run_backup("Incremental")
            backup_job_2 = backup_result_2[0]
            self.verify_backup_level(backup_job_2, "Full")

            # Add Reg key to re-verify bad chunks.
            self.media_agent_machine.create_registry('MediaAgent', value='SIDBDVReverifyChunksFlg',
                                                     data='466816', reg_type='DWord')
            self.log.info("adding regkey to force reverification of bad chunks and jobs")

            # Rename backup the sfile to Original one
            self.rename_sfile(self.chunk_path_1, 'SFILE_CONTAINER_001_RENAMED', 'SFILE_CONTAINER_001')

            self.storage_policy_copy.pick_jobs_for_data_verification(backup_job_1.job_id)
            self.log.info("Starting verification #3")
            ddb_verification_job_3 = self.run_ddb_verification(is_incr_dv2=True, is_quick_dv2=False)
            self.verify_dv2_job_status(ddb_verification_job_3, error_present=False)
            self.verify_archcheck_status(backup_job_1.job_id, 5)
            self.verify_archcheck_status(backup_job_2.job_id, 5)
        except Exception as exp:
            self.log.error(f"Failed to execute test case with error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all objects created for the testcase"""
        self.log.info("Performing unconditional cleanup")
        if self.status != constants.FAILED:
            self.log.info("Test Case PASSED")
        else:
            self.log.warning("Test Case FAILED")
        self.run_cleanup()
