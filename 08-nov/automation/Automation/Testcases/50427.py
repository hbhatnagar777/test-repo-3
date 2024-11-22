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

    disable_ransomware_protection(client_id, media_agent_obj) --  disable ransomware protection on client

    create_resources()        --  create resources for testcase

    run_backup(backup_level)  --  runs backup job

    get_object_count(job_id)  --  get the object count of the backup job

    get_volume_id(chunk_id)   --  get the volume id of the chunk

    get_chunk_path(volume_id, chunk_id) --  get physical size of each volume from mountpath

    remove_permissions(chunk_path)  --  remove the permissions to allow for manipulations on the backup

    rename_sfile(chunk_path, orig_name, new_name) --  rename the SFILE from the backup

    corrupt_sfie(chunk_path, file_name) --  corrupt the SFILE from the backup

    run_ddb_verification(storage_policy, dv2_type, verification_level) --  run ddb verification

    mark_next_backup_full() --  mark the next backup as full if DV2 failed with database update and stored
                                        procedure
    
    verify_dv2_job_status(dv2_job, error_present) --  check if DV2 job succeeded

    verify_backup_leel(backup_job, backup_level) --  check if backup job automatically changed the backup level

    verify_chunk_in_archchunkddbdrop(store_id, job_id, chunk_id, chunk_present) --  verify if Chunk shows up in
                                                                                    ArchChunkDDBDrop table

    verify_archcheck_status(job_id) --  verify that the archcheckstatus in csdb for jobid is failed
    
    verify_sidb_logs(media_agent_name, sidb_id, substore_id, chunk_id) --  verify that the SIDB Engine logs show
                                                                            marking of chunk as BAD

    get_active_files_store()    -- Get active SIDB store object for storage policy

    modify_chunks()  -- gets and modifies the chunks to modify from list of chunks

Sample Input:
    "50427": {
        "ClientName": "Client Name",
        "AgentName": "File System",
        "MediaAgentName": "MA Name",
        Optional:  ** these will be used to create storage pool**
        "dedup_path": DDB path location  -- For linux please specify LVM path
        "mount_path": mount path location
    }
"""

import time
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "DV2 Chunk Corruption Scenario with Mark Next Backup Job Full"

        self.deduphelper_obj = None
        self.sidb_id = None
        self.substore_id = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.chunk_path_1 = None
        self.chunk_path_2 = None
        self.reset_ransomware = False
        self.sidb_store_obj = None
        self.pool_name = None
        self.plan_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.mount_path = None
        self.agent_name = None
        self.ddb_path = None
        self.scale_factor = None
        self.bkpset_obj = None
        self.subclient = None
        self.client = None
        self.primary_copy = None
        self.ma_name = None
        self.client_name = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.client_machine_obj = False
        self.ma_machine_obj = False
        self.client_drive = False
        self.ma_drive = False
        self.media_agent_obj = None
        self.mmhelper_obj = None
        self.plan = None
        self.option_obj = None
        self.chunk_to_modify = []
        self.status = constants.PASSED

    def setup(self):
        """sets up the variables to be used in testcase"""
        self.log.info("Setting up testcase variables and objects")
        self.option_obj = OptionsSelector(self.commcell)
        self.mmhelper_obj = MMHelper(self)
        self.deduphelper_obj = DedupeHelper(self)
        suffix = round(time.time())
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.client_name = self.tcinputs.get('ClientName')

        self.ma_machine_obj = machine.Machine(self.ma_name, self.commcell)
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)
        self.client_machine_obj = Machine(self.client)

        self.client_drive = self.option_obj.get_drive(self.client_machine_obj, 25 * 1024)
        if not self.is_user_defined_mp:
            self.ma_drive = self.option_obj.get_drive(self.ma_machine_obj, 25 * 1024)

        self.pool_name = f"STORAGEPOOL_{self.id}_{self.ma_name}"
        self.plan_name = f"PLAN_{self.id}_{self.ma_name}"

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_mp:
            self.mount_path = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"), f"TC_{self.id}",
                                                            f"LIB_{suffix}")
            self.log.info(f"Using user provided mount path {self.mount_path}")
        else:
            self.mount_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"LIB_{suffix}")

        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"DDB_{suffix}")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get("dedup_path"), f"TC_{self.id}",
                                                            f"DDB_{suffix}")
            self.log.info(f"Using user provided dedup path {self.dedup_path}")

        self.backupset_name = f"BKPSET_{self.id}_{self.client_name}"
        self.subclient_name = f"SUBC_{self.id}_{self.client_name}"
        self.content_path = self.client_machine_obj.join_path(self.client_drive, f"TC_{self.id}_CONTENT")

    def create_resources(self):
        """Create resources needed by the Test Case"""
        # Configure the environment
        # Create a storage pool
        if not self.commcell.storage_pools.has_storage_pool(self.pool_name):
            self.log.info(f"Creating Storage Pool - {self.pool_name}")
            self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                                            self.ma_name, [self.ma_name] * 2,
                                                            [self.dedup_path, self.dedup_path])
        else:
            self.log.info(f"Storage Pool already exists - {self.pool_name}")
            self.pool_obj = self.commcell.storage_pools.get(self.pool_name)
        # Create plan
        if not self.commcell.plans.has_plan(self.plan_name):
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")
        else:
            self.plan = self.commcell.plans.get(self.plan_name)

        self.primary_copy = self.plan.storage_policy.get_copy('Primary')
        self.plan.schedule_policies['data'].disable()
        # Create a backupset
        self.log.info(f"Configuring Backupset - {self.backupset_name}")
        self.bkpset_obj = self.mmhelper_obj.configure_backupset(self.backupset_name)
        # Create subclient
        self.subclient = self.bkpset_obj.subclients.add(self.subclient_name)
        self.subclient.plan = [self.plan, [self.content_path]]
        if self.ma_machine_obj.os_info.lower() == 'windows':
            self.disable_ransomware_protection(self.media_agent_obj)
        # get sidb store id and substore id
        return_list = self.deduphelper_obj.get_sidb_ids(self.plan.storage_policy.storage_policy_id, "Primary")
        self.sidb_id = int(return_list[0])

        # add content
        size = 1
        additional_content = self.client_machine_obj.join_path(self.content_path, 'generated_content')
        if self.client_machine_obj.check_directory_exists(additional_content):
            self.client_machine_obj.remove_directory(additional_content)
        # if scale test param is passed in input json, multiply size by scale factor times and generate content
        if self.scale_factor:
            size = size * int(self.scale_factor)
        self.mmhelper_obj.create_uncompressable_data(self.client_name, additional_content, size)

    def disable_ransomware_protection(self, media_agent_obj):
        """
            disable ransomware protection on client
            Args:
                media_agent_obj (obj)  --  MediaAgent object for the testcase run
        """
        ransomware_status = self.mmhelper_obj.ransomware_protection_status(self.commcell.clients.get(media_agent_obj.name).client_id)
        self.log.info(f"Current ransomware status is: {ransomware_status}")
        if ransomware_status:
            self.reset_ransomware = True
            self.log.info(f"Disabling ransomware protection on {media_agent_obj.name}")
            media_agent_obj.set_ransomware_protection(False)
        else:
            self.log.info(f"Ransomware protection is already disabled on {media_agent_obj.name}")

    def run_backup(self, backup_level):
        """
            runs backup job

            Args:
                backup_level (str)  --  full or incremental backup level

            Returns
                tuple that contains backup job object and list of chunk IDs
        """

        # run the backup job
        self.log.info(f"Starting {backup_level} backup job")
        backup_job = self.subclient.backup(backup_level.upper())
        self.log.info(f"Backup job ID: {backup_job.job_id}")
        if not backup_job.wait_for_completion():
            if backup_job.status.lower() == "completed":
                self.log.info(f"job {backup_job.job_id} completed")
            else:
                raise Exception(
                    f"Job {backup_job.job_id} Failed with {backup_job.delay_reason}")

        query = f"""SELECT    archchunkid
                    FROM      archchunkmapping
                    WHERE     archfileid
                    IN       ( SELECT    id
                                FROM      archfile 
                                WHERE     jobid={backup_job.job_id} 
                                AND       filetype=1) order by archchunkid asc"""
        self.log.info(f"EXECUTING QUERY {query}")
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        chunks = []
        for i in range(len(res)):
            chunks.append(res[i][0])
        self.log.info("got the chunks belonging to the backup job")
        self.log.info(f"Chunks are {chunks}")
        return backup_job, chunks

    def get_object_count(self, job_id):
        """
            get the object count of the backup job

            Args:
                job_id (str)  --  Job Id for which records to be checked

            Returns
                tuple with primary and secondary object counts
        """
        self.log.info(f"Getting object count of job id {job_id}")
        pri_count = self.deduphelper_obj.get_primary_objects(job_id)
        sec_count = self.deduphelper_obj.get_secondary_objects(job_id)
        self.log.info(f"Object count for primary: {pri_count}")
        self.log.info(f"Object count for secondary: {sec_count}")
        return pri_count, sec_count

    def get_volume_id(self, chunk_id):
        """
            get the volume id of the chunk

            Args:
                chunk_id (str)  --  Chunk ID

            Return:
                volume id of the chunk
        """

        self.log.info(f"Getting volume id of chunk {chunk_id}")
        query = f"SELECT volumeid FROM archchunk WHERE id = {chunk_id}"
        self.log.info(f"EXECUTING QUERY {query}")
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()
        volume_id = res[0]
        self.log.info(f"Volume id of chunk {chunk_id} is {volume_id}")
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
        self.log.info(f"Fetching physical location of volume : {volume_id}")
        query = "select MMV.volumeid, MMDC.folder, MNTPATH.MountPathName, CL.name " \
                "from MMMountpath MNTPATH, MMDeviceController MMDC, MMMountPathToStorageDevice MMPS, MMVOLUME MMV " \
                ", App_Client CL where MMPS.MountPathId = MMV.CurrMountPathId and " \
                "MNTPATH.MountPathId = MMV.CurrMountPathId and CL.id = MMDC.clientid " \
                f" and MMDC.deviceid = MMPS.DeviceId and MMV.volumeid = {volume_id}"
        self.log.info(f"Query is {query}")
        self.csdb.execute(query)
        # Now work out the path for each of the volume and fetch its size
        physical_location_list = self.csdb.fetch_all_rows()[0]

        chunk_path = f"{physical_location_list[1]}{self.ma_machine_obj.os_sep}{physical_location_list[2]}"\
            f"{self.ma_machine_obj.os_sep}CV_MAGNETIC{self.ma_machine_obj.os_sep}V_{volume_id}"\
            f"{self.ma_machine_obj.os_sep}CHUNK_{chunk_id}"
        self.log.info("Chunk path is %s", chunk_path)
        return chunk_path

    def remove_permissions(self, chunk_path):
        """
            remove the permissions to allow for manipulations on the backup

            Args:
                chunk_path (str)  --  Path of the chunk
        """
        self.log.info(
            "Removing permissions from volume to allow for manipulations on the backup")
        volume_path_list = chunk_path.split(self.ma_machine_obj.os_sep)[:-1]
        volume_path = self.ma_machine_obj.os_sep.join(volume_path_list)

        self.ma_machine_obj.modify_ace('Everyone', volume_path,
                                            'DeleteSubdirectoriesAndFiles',
                                            'Deny', remove=True, folder=True)
        self.ma_machine_obj.modify_ace('Everyone', volume_path,
                                            'Delete',
                                            'Deny', remove=True, folder=True)

        self.log.info(
            "Removing permissions from chunk to allow for manipulations on the backup")
        self.ma_machine_obj.modify_ace('Everyone', chunk_path,
                                            'DeleteSubdirectoriesAndFiles',
                                            'Deny', remove=True, folder=True)
        self.ma_machine_obj.modify_ace('Everyone', chunk_path,
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
        old_file_path = self.ma_machine_obj.join_path(
            chunk_path, orig_name)
        new_file_path = self.ma_machine_obj.join_path(
            chunk_path, new_name)
        self.log.info(old_file_path)
        self.log.info(new_file_path)
        self.ma_machine_obj.rename_file_or_folder(
            old_file_path, new_file_path)

    def corrupt_sfile(self, chunk_path, file_name):
        """
            corrupt the SFILE from the backup

            Args:
                chunk_path (str)  --  Path of the chunk
                file_name (str)   --  Name of the file to be corrupted
        """
        self.log.info("Corrupting sfile",)
        file_path = self.ma_machine_obj.join_path(
            chunk_path, file_name)
        self.log.info(file_path)
        self.ma_machine_obj.delete_file(file_path)
        self.ma_machine_obj.create_file(
            file_path, 'This file is corrupted for testing purposes')

    def run_ddb_verification(self, is_incr_dv2, is_quick_dv2):
        """
            run ddb verification

            Args:
                dv2_type (bool)           --  Is Incremental DV2 to be submitted or not
                is_quick_dv2 (bool)       --  Is this a quick DV2 request

            Returns:
                job object of the verification job
        """
        self.log.info("Running DDB verification")
        job = self.sidb_store_obj.run_ddb_verification(incremental_verification=is_incr_dv2, quick_verification=is_quick_dv2)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run dv2 job with error: {job.delay_reason}")
        self.log.info("DV2 job completed.")
        return job

    def mark_next_backup_full(self):
        """
            mark the next backup as full if DV2 failed with database update and stored procedure
        """
        self.log.info("Running stored proc ArchMarkNextBackupFullForDVFailedSCs")
        self.mmhelper_obj.update_mmconfig_param(
            'MMCONFIG_MARK_NEXT_BKP_FULL_FOR_DV_FAILED_SUBCLIENTS', 0, 1)
        self.mmhelper_obj.execute_stored_proc("ArchMarkNextBackupFullForDVFailedSCs", ("0",))
        self.log.info("Sleeping for 60 seconds")
        time.sleep(60)

    def verify_dv2_job_status(self, dv2_job, error_present):
        """
            check if DV2 job succeeded
            Args:
                dv2_job (object)      --  DV2 job object
                error_present (bool)  --  True if error should be present, False otherwise
        """
        if (error_present is False and dv2_job.state == 'Completed')\
                or (error_present is True and dv2_job.state == 'Completed w/ one or more errors'):
            self.log.info(f"DV2 Job {dv2_job.job_id} Verifying Status Success")
        else:
            raise Exception(f"DV2 Job {dv2_job.job_id} Verifying Status Failed")

    def verify_backup_level(self, backup_job, backup_level):
        """
            check if backup job automatically changed the backup level
            Args:
                backup_job (object)  --  backup job object
                backup_level (str)   --  expected backup level
        """
        if backup_job.backup_level == backup_level:
            self.log.info(f"Verified backup level of job {backup_job.job_id} {backup_level}")
        else:
            raise Exception(
                f"Failed to verify backup level of job {backup_job.job_id}: Result is not {backup_level}")

    def verify_chunk_in_archchunkddbdrop(self, store_id, job_id):
        """
        verify if Chunk shows up in ArchChunkDDBDrop table
            Args:
                store_id (int)        --  Store ID
                job_id (str)          --  DV2 Job ID
        """
        self.log.info(f"Verifying if {self.chunk_to_modify} is present in the table")
        query = f"""SELECT archchunkid
                    FROM archchunkddbdrop
                    WHERE sidbstoreid={store_id}
                    AND reserveint={job_id} order by archchunkid asc"""
        self.log.info(f"Query is {query}")
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"Result length is: {len(res)} and Result is: {res}")
        chunks1 = []
        for i in range(len(res)):
            chunks1.append(res[i][0])
        if set(chunks1) == set(self.chunk_to_modify):
            self.log.info("Chunk present in archchunkddb drop table")
        else:
            raise Exception("Chunk is not present in archchunkddb table")

    def verify_archcheck_status(self, job_id):
        """
            verify that the archcheckstatus in csdb for jobid is failed

            Args:
                job_id (str)  --  Backup Job ID
        """
        query = f'''select distinct archCheckStatus
            from JMJobDataStats
            where jobId = {job_id} and dataType = 1'''
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        if rows[0][0] == '6':
            self.log.info("Verified archCheckStatus is Failed")
        else:
            raise Exception("Failed to verify archCheckStatus is Failed")

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.pool_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def modify_chunks(self, chunks):
        """ This function gets and modifies the chunks from the chunk list
        args:
            chunks (list)  --  chunk list
        """
        chunks_path = []
        chunk_path_to_modify = []
        count = 0
        for i in range(0, len(chunks)):
            if count == 2:
                break
            volume = self.get_volume_id(chunks[i])
            chunks_path.append(self.get_chunk_path(volume, chunks[i]))
            # Find if sfile container_001 exists in the chunk path or not and then rename and corrupt
            files = self.ma_machine_obj.get_files_in_path(chunks_path[i])
            for file in files:
                exit_condition = 0
                if 'SFILE_CONTAINER_001' in file:
                    self.log.info(f"Chunk Paths where sfile containers are present are: {chunks[i]} {chunks_path[i]}")
                    self.chunk_to_modify.append(chunks[i])
                    chunk_path_to_modify.append(chunks_path[i])
                    if self.ma_machine_obj.os_info.lower() == 'windows':
                        self.remove_permissions(chunk_path_to_modify[i])
                    if count == 0:
                        self.rename_sfile(chunk_path_to_modify[i], 'SFILE_CONTAINER_001', 'SFILE_CONTAINER_001_RENAMED')
                    if count == 1:
                        self.corrupt_sfile(chunk_path_to_modify[i], 'SFILE_CONTAINER_001')
                    count = int(count) + 1
                    exit_condition = 1
                if exit_condition == 1:
                    break
        if count == 0:
            raise Exception("No sfile containers present in chunk")

    def run(self):
        """run function of this testcase"""
        try:
            self.cleanup()
            self.create_resources()
            self.log.info("Starting backup #1")
            backup_result_1 = self.run_backup("Full")
            backup_job_1 = backup_result_1[0]
            chunks = backup_result_1[1]

            self.verify_backup_level(backup_job_1, "Full")
            self.sidb_store_obj = self.get_active_files_store()
            object_count_1 = self.get_object_count(backup_job_1.job_id)
            primary_object_count_1 = object_count_1[0]
            secondary_object_count_1 = object_count_1[1]
            to_match0 = int(primary_object_count_1) + int(secondary_object_count_1)

            self.log.info("Starting verification #1")
            ddb_verification_job_1 = self.run_ddb_verification(is_incr_dv2=True, is_quick_dv2=False)
            self.verify_dv2_job_status(ddb_verification_job_1, error_present=False)

            # Rename and Corrupt 2 different sfile containers
            self.modify_chunks(chunks)
            # Run DV2 and it should get corrupt chunks
            ddb_verification_job_2 = self.run_ddb_verification(is_incr_dv2=False, is_quick_dv2=False)
            self.verify_dv2_job_status(ddb_verification_job_2, error_present=True)
            time.sleep(60)
            self.verify_chunk_in_archchunkddbdrop(self.sidb_id, ddb_verification_job_2.job_id)
            self.verify_archcheck_status(backup_job_1.job_id)

            backup_result_2_pre = self.run_backup("Incremental")
            backup_job_2_pre = backup_result_2_pre[0]
            self.verify_backup_level(backup_job_2_pre, "Incremental")
            self.mark_next_backup_full()

            self.log.info("Starting backup #2")
            backup_result_2 = self.run_backup("Incremental")
            backup_job_2 = backup_result_2[0]
            self.verify_backup_level(backup_job_2, "Full")

            object_count_2 = self.get_object_count(backup_job_2.job_id)
            primary_object_count_2 = object_count_2[0]
            secondary_object_count_2 = object_count_2[1]
            to_match1 = int(primary_object_count_2) + int(secondary_object_count_2)
            self.log.info(f"Primary+Secondary Object count for first and 2nd fulls: {to_match0} {to_match1}")
            if to_match0 == to_match1 and primary_object_count_2 != 0:
                self.log.info("Primary object count is matching between first full and 2nd full")
            else:
                raise Exception("Primary object count is not matching between first full and 2nd full. Check DV2 logs")

            self.log.info("Starting Quick INCR DV2 : verification #3")
            ddb_verification_job_3 = self.run_ddb_verification(is_incr_dv2=False, is_quick_dv2=True)
            self.verify_dv2_job_status(ddb_verification_job_3, error_present=False)

            self.log.info("Starting Complete DV2 : verification #4")
            ddb_verification_job_4 = self.run_ddb_verification(is_incr_dv2=True, is_quick_dv2=False)
            self.verify_dv2_job_status(ddb_verification_job_4, error_present=False)
            self.log.info("Testcase completed successfully")
        except Exception as exp:
            self.log.error(f"Failed to execute test case with error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def cleanup(self):
        self.log.info(
            "Deleting all objects created for the testcase and reverting machine changes")
        try:
            self.mmhelper_obj.update_mmconfig_param(
                'MMCONFIG_MARK_NEXT_BKP_FULL_FOR_DV_FAILED_SUBCLIENTS', 0, 0)
            if self.ma_machine_obj.os_info.lower() == 'windows':
                self.log.info(f"Enabling ransomware protection on {self.ma_name}")
                self.media_agent_obj.set_ransomware_protection(True)

            self.log.info("Deleting resources")
            # delete the generated content for this testcase
            if self.client_machine_obj.check_directory_exists(self.content_path):
                self.client_machine_obj.remove_directory(self.content_path)
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
            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info(f"Deleting Storage Pool {self.pool_name}")
                self.commcell.storage_pools.delete(self.pool_name)
            self.log.info("Refresh libraries")
            self.commcell.disk_libraries.refresh()
            self.log.info("Refresh Storage Pools")
            self.commcell.storage_pools.refresh()
            self.log.info("Refresh Plans")
            self.commcell.plans.refresh()
            self.log.info("clean up successful")
        except Exception as exp:
            self.log.info(f"Cleanup was not successful: {exp}")

    def tear_down(self):
        self.log.info("Performing unconditional cleanup")
        if self.status != constants.FAILED:
            self.log.info("Test Case PASSED")
        else:
            self.log.warning("Test Case FAILED")
        self.cleanup()



