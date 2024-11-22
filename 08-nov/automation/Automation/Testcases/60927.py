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

    cleanup()       --  cleans up the entities

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    disable_ransomware_protection() --	disable ransomware protection on client

    create_resources()		--	Create all the resources required to run backups

    run_backups()			--	Run backups on subclient

    archchunktoverify_validations()	--	Verify archchunktoverify/archchunktoverify2 table for various values

    validate_scalable_job_jmtables() --	Validate JMJobStats table for details regarding DV2/Space Reclamation job

    is_dv2_in_progress_flag_set()	--	Check if dv2 in progress flag is set on store

    run_dv2_job()			--	Runs DV2 job with type and option selected and waits for job to complete

    get_mountpath_folder()		--	Fetch the mountpath folder details for volumes associated with given SIDB store

    create_orphan_data()		--	This method creates a dummy dedupe chunk with testcase id

    wait_for_pruning_complete()	        --	Wait for Pruning to complete

    prune_jobs()			--	Prunes jobs from storage policy copy

    perform_defrag_tuning()		--	This function enables or disables defrag related settings

    is_orphan_chunk_present()	--	Verify if orphan chunk is present on disk

    get_mountpath_physical_size()	--	Get physical size of the mount path

    run_space_reclaim_job()		--	runs space reclaim job on the provided store object

    verify_bad_chunks_absent()  --  Verify that no bad chunks are added by given DV2 job id in ArchChunkDDBDrop table
    TcInputs to be passed in JSON File:
    "60927": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "MediaAgentName": Name of a MediaAgent - we create Libraries here
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
    }

"""
import time
from cvpysdk import deduplication_engines
from AutomationUtils import constants
from AutomationUtils import cvhelper
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "DDB Verification,Defrag and OCL with Scalable Resource Allocation"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.library_name = None
        self.mountpath = None
        self.ma_name = None
        self.store_obj = None
        self.storage_policy_name = None
        self.sp_obj_list = []
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.client_machine_obj = None
        self.ma_machine_obj = None
        self.ma_library_drive = None
        self.dedup_path = None
        self.content_path = None
        self.subclient_obj_list = []
        self.bkpset_obj = None
        self.drillhole_key_added = False
        self.client_system_drive = None
        self.backup_job_list = []
        self.volumes_list = []
        self.sqlobj = None
        self.volume_physical_size_dict = {}
        self.mm_admin_thread = None
        self.volume_update_interval = None
        self.gdsp = None
        self.optionobj = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.storage_pool_name = None
        self.sidb_stores_list = []
        self.content_path_list = []
        self.orphan_chunks_file = None
        self.orphan_chunks_folder = None
        self.error_list = ""
        self.mount_path_folder = None
        self.reset_ransomware  = False
        self.media_agent_obj = None
        self.dedup_helper   = None
        self.ma_client = None
        self.sql_password = None

        self.total_space_reclaimed_mb = None

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
        self.library_name = f"Lib_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"), self.id)
        else:
            self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, self.id)

        self.storage_pool_name = f"StoragePool_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"
        self.storage_policy_name = f"SP_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"
        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, "DDBs", f"TC_{self.id}")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get('dedup_path'), "DDBs", f"TC_{self.id}")

        self.backupset_name = f"BkpSet_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"
        self.subclient_name = f"Subc_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"
        for content in range(0,2):
            self.content_path_list.append(self.client_machine_obj.join_path(self.client_system_drive, self.id,
                                                                                f"subc{content+1}"))

        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)
        self.ma_client = self.commcell.clients.get(self.ma_name)
        encrypted_pass = Machine(self.commcell.commserv_client).get_registry_value("Database", "pAccess")
        self.sql_password = cvhelper.format_string(self._commcell, encrypted_pass).split("_cv")[1]
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
            self.log.info(
                "Disabling ransomware protection on %s", media_agent_obj.name)
            media_agent_obj.set_ransomware_protection(False)
        else:
            self.log.info("Ransomware protection is already disabled on %s", media_agent_obj.name)

    def cleanup(self):
        """
        Clean up the entities created by this test case
        """
        self.log.info("Cleaning up FileSystem subclients by deleting the backupset [%s]", self.backupset_name)
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.log.info("Deleting backupset %s", self.backupset_name)
            self.agent.backupsets.delete(self.backupset_name)

        self.log.info("Cleaning up content directories of these subclients")
        for content in range(0,2):
            if self.client_machine_obj.check_directory_exists(self.content_path_list[content]):
                self.log.info("Deleting already existing content directory [%s]", self.content_path_list[content])
                self.client_machine_obj.remove_directory(self.content_path_list[content])

        self.log.info("Cleaning up depenednt storage policies")
        for sp in range(1, 3):
            if self.commcell.storage_policies.has_policy(f"{sp}_{self.storage_policy_name}"):
                self.log.info("Deleting Dependent SP - [%s]", f"{sp}_{self.storage_policy_name}")
                self.commcell.storage_policies.delete(f"{sp}_{self.storage_policy_name}")

        self.log.info("Cleaning up storage pool - [%s]", self.storage_pool_name)
        if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name}"):
            self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name}")
            self.commcell.storage_policies.delete(f"{self.storage_pool_name}")

    def create_resources(self):
        """Create all the resources required to run backups"""

        self.log.info("===STEP: Configuring TC Environment===")

        for content in range(0,2):
            if self.client_machine_obj.check_directory_exists(self.content_path_list[content]):
                self.log.info("Deleting already existing content directory [%s]", self.content_path_list[content])
                self.client_machine_obj.remove_directory(self.content_path_list[content])
            self.client_machine_obj.create_directory(self.content_path_list[content])

        if not self.ma_machine_obj.check_directory_exists(self.mountpath):
            self.log.info("Creating mountpath directory [%s]", self.mountpath)
            self.ma_machine_obj.create_directory(self.mountpath)
        self.log.info("Creating Library [%s]", self.library_name)
        if self.commcell.disk_libraries.has_library(self.library_name):
            self.log.info("Library [%s] already exists. Reusing the Library.", self.library_name)
        else:
            self.mm_helper.configure_disk_library(self.library_name, self.ma_name, self.mountpath)
            self.log.info("Library [%s] created successfully.", self.library_name)
            #Reset flag 128 on the library & set DedupeDrillHoles to 0 on MA

        self.log.info("Configuring Storage Pool ==> %s", self.storage_pool_name)
        if not self.commcell.storage_policies.has_policy(self.storage_pool_name):
            self.gdsp = self.dedup_helper.configure_global_dedupe_storage_policy(
                                                                global_storage_policy_name=self.storage_pool_name,
                                                                library_name=self.library_name,
                                                                media_agent_name=self.tcinputs['MediaAgentName'],
                                                                ddb_path=self.dedup_path,
                                                                ddb_media_agent=self.tcinputs['MediaAgentName'])
        for sp in range(1,3):
            if not self.commcell.storage_policies.has_policy(f"{sp}_{self.storage_policy_name}"):
                self.sp_obj_list.append(self.commcell.storage_policies.add(
                                                    storage_policy_name=f"{sp}_{self.storage_policy_name}",
                                                    library=self.library_name,
                                                    media_agent=self.tcinputs['MediaAgentName'],
                                                    global_policy_name=self.storage_pool_name,
                                                    dedup_media_agent="",
                                                    dedup_path=""))
            else:
                self.log.info("Getting Storage Policy Objects")
                self.sp_obj_list.append(self.commcell.storage_policies.get(f"{sp}_{self.storage_policy_name}"))

        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary_Global'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary_Global')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])
                self.log.info("Disabling Garbage Collection on DDB Store == %s", dedup_store[0])
                self.store_obj.enable_garbage_collection = False

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mm_helper.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        for subc in range(1,3):
            self.log.info("Configuring Subclient [%s]", f"{self.subclient_name}_{subc}")
            self.subclient_obj_list.append(self.mm_helper.configure_subclient(self.backupset_name,
                                                       f"{self.subclient_name}_{subc}",
                                                       f"{subc}_{self.storage_policy_name}",
                                                       f"{self.content_path_list[subc-1]}"))
            self.log.info("Successfully configured Subclient [%s]",  f"{self.subclient_name}_{subc}")
            self.log.info("Setting Number of Streams to 5 and Allow Multiple Data Readers to True")
            self.subclient_obj_list[subc-1].data_readers = 5
            self.subclient_obj_list[subc-1].allow_multiple_readers = True


    def run_backups(self):
        """
        Run backups on subclient
        """
        for subc in range(0,2):
            if not self.client_machine_obj.check_directory_exists(self.content_path_list[subc]):
                self.client_machine_obj.create_directory(self.content_path_list[subc])

        for bkp in range(1,4):

            source_dir = f"{self.content_path_list[0]}{self.client_machine_obj.os_sep}{bkp}"
            target_dir = f"{self.content_path_list[1]}{self.client_machine_obj.os_sep}{bkp}"
            self.client_machine_obj.create_directory(source_dir)
            self.client_machine_obj.create_directory(target_dir)

            self.log.info("Generating content for subclient [%s] at [%s]", self.subclient_obj_list[0].name,
                          source_dir)
            self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'], source_dir, 1)
            self.log.info("Starting backup on subclient %s", self.subclient_obj_list[0].name)
            self.backup_job_list.append(self.subclient_obj_list[0].backup("Incremental"))
            if not self.backup_job_list[-1].wait_for_completion():
                raise Exception(
                    "Failed to run backup job with error: {0}".format(self.backup_job_list[-1].delay_reason)
                )
            self.log.info("Backup job [%s] on subclient [%s] completed", self.backup_job_list[-1].job_id,
                          self.subclient_obj_list[0].name)

            self.log.info("Copying half content from subclient [%s] to subclient [%s] to directory [%s]",
                          self.subclient_obj_list[0].name,
                          self.subclient_obj_list[1].name, target_dir)
            self.client_machine_obj.copy_folder(source_dir, f"{self.content_path_list[1]}"
                                                            f"{self.client_machine_obj.os_sep}")
            new_target = ""
            folders_list = self.client_machine_obj.get_folders_in_path(target_dir)
            self.log.info(folders_list)
            if folders_list:
                new_target = folders_list[0]
            self.log.info(f"Deleting every alternate file from {new_target}")
            self.optionobj.delete_nth_files_in_directory(self.client_machine_obj, new_target, 2, "delete")
            self.log.info("Starting backup on subclient %s", self.subclient_obj_list[1].name)
            self.backup_job_list.append(self.subclient_obj_list[1].backup("Incremental"))
            if not self.backup_job_list[-1].wait_for_completion():
                raise Exception(
                    "Failed to run backup job with error: {0}".format(self.backup_job_list[-1].delay_reason)
                )
            self.log.info("Backup job [%s] on subclient [%s] completed", self.backup_job_list[-1].job_id,
                          self.subclient_obj_list[1].name)

    def archchunktoverify_validations(self, table_list, job_id, validate_defrag=False):
        """"
        Verify archchunktoverify/archchunktoverify2 table for various values

        table_list  (list)      -   List of CSDB tables on which query needs to be run
        job_id      (int)       -   DV2/Space Reclamation job id
        validate_defrag (bool)  -   Declare if the job is Space Reclamation job or not
        """
        query_outputs = []
        for num in range(0, 2):
            table = table_list[num]
            query = f"select count(*) from {table} where adminjobid  = {job_id} "
            self.log.info("Query => %s", query)
            self.csdb.execute(query)
            num_rows = int(self.csdb.fetch_one_row()[0])
            self.log.info("Output ==> %s", num_rows)
            query_outputs.append(num_rows)

        # We expect first two outputs to be non-zero and zero respectively.
        self.log.info("Table : %s ==> [%s] Rows : %s ==> [%s] Rows", table_list[0], query_outputs[0],
                        table_list[1], query_outputs[1])
        if not validate_defrag:
            self.log.info("Verifying for DDB Verification Job")
            if query_outputs[0] != 0 and query_outputs[1] == 0:
                self.log.info("Validation ==> SUCCESS")
            else:
                self.log.error("Validation ==> FAIL")
                self.error_list+=f" [CSDB Table [{table}] validation failure during DDB Verification Job] "
        else:
            self.log.info("Verifying for Space Reclamation Job")
            if query_outputs[0] == 0 and query_outputs[1] == 0:
                self.log.info("Table : %s ==> Zero Rows and Table : %s ==> Zero Rows", table_list[0], table_list[1])
                self.log.info("Validation ==> SUCCESS")
            else:
                self.log.error("Validation ==> FAIL")
                self.error_list+=f" [CSDB Table [{table}] validation failure during DDB Space Reclamation Job] "

    def validate_scalable_job_jmtables(self,jobtype_str, job_obj):
        """
        Validate JMJobStats table for details regarding DV2/Space Reclamation job

        jobtype_str     (str)       -   Jobtype string
        job_obj         (object)    -   DV2/Space Reclamation job object
        """
        self.log.info("VALIDATION: sub optype for %s with Scalable Resource Allocation", jobtype_str)
        query = f"select opType, subOpType from jmjobstats where jobid = {job_obj.job_id}"
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("RESULT (optype and suboptype): %s", result)
        if not result:
            raise Exception("no result returned from query")
        if int(result[0]) != 31 and int(result[1]) != 106:
            raise Exception(f"{jobtype_str} job optype is not correct")
        self.log.info("%s job optype is set as expected", jobtype_str)

    def is_dv2_in_progress_flag_set(self):
        """
        Check if dv2 in progress flag is set on store

        Returns:
            True if flag is set, False otherwise
        """

        self.log.info("Checking if dv2_in_progress flag is set on store [%s]", self.store_obj.store_id)
        self.store_obj.refresh()
        self.log.info("RESULT (flags): %s", self.store_obj.store_flags)
        if self.store_obj.store_flags & 67108864 == 67108864:
            self.log.info("DDB_VERIFICATION_INPROGRESS Flag is Set")
            return True
        else:
            self.log.info("DDB_VERIFICATION_INPROGRESS Flag is NOT Set")
            return False

    def run_dv2_job(self, dv2_type, option):
        """
        Runs DV2 job with type and option selected and waits for job to complete

        Args:
            dv2_type (str) - specify type either full or incremental

            option (str) - specify option, either quick or complete

        Returns:
             (object) - completed DV2 job object
        """

        self.log.info("running [%s] [%s] DV2 job on store [%s]...", dv2_type, option, self.store_obj.store_id)
        self.store_obj.refresh()
        if dv2_type == 'incremental' and option == 'quick':
            job = self.store_obj.run_ddb_verification()
        elif dv2_type == 'incremental' and option == 'complete':
            job = self.store_obj.run_ddb_verification(quick_verification=False, use_scalable_resource=True)
        elif dv2_type == 'full' and option == 'quick':
            job = self.store_obj.run_ddb_verification(incremental_verification=False, use_scalable_resource=True)
        else:
            job = self.store_obj.run_ddb_verification(incremental_verification=False, quick_verification=False,
                                                      use_scalable_resource=True)
        self.log.info("DV2 job: %s", job.job_id)

        #Validate that in Phase 2, we have 0 rows in ArchChunkToVerify and non-zero in ArchChunkToVerify2
        #Table List
        exit_condition = 900
        while job.phase == "Validate Dedupe Data":
            self.log.info("Job Phase : [%s]. Will check again after 10 Seconds", job.phase)
            time.sleep(10)
            exit_condition-=10
            if not exit_condition:
                self.log.error("Job is not in Verify Data phase even after 15 minutes")

        self.log.info("DV2 Job Current Phase : [%s], Status : [%s]", job.phase, job.status)
        exit_condition = 600
        while job.status.lower() != 'running' and exit_condition > 0:
            self.log.info("Job is not in running state. Current Status = [%s]", job.status)
            time.sleep(2)
            exit_condition -= 2

        table_list = ['ArchChunkToVerify2', 'ArchChunkToVerify', ]
        self.log.info("Performing CSDB Validations for ArchChunkToVerify2 table")
        self.archchunktoverify_validations(table_list, job.job_id)

        self.log.info("Check if DDB_VERIFICATION_INPROGRESS flag is set")
        if self.is_dv2_in_progress_flag_set():
            self.log.error("ERROR:DDB_VERIFICATION_INPROGRESS flag is set even when DV2 job is in Verify Data phase.")
            self.error_list += " [DDB_VERIFICATION_INPROGRESS validation failure during DDB Verification Job] "
        else:
            self.log.info("DDB_VERIFICATION_INPROGRESS flag is not set when DV2 job is in Verify Data phase.")

        self.log.info("Waiting for job completion")
        if not job.wait_for_completion():
            raise Exception(f"Failed to run dv2 job with error: {job.delay_reason}")
        self.log.info("DV2 job completed.")

        table_list = ['ArchChunkToVerify2History', 'ArchChunkToVerifyHistory', ]
        self.log.info("Performing CSDB Validations for ArchChunkToVerify2History table")
        self.archchunktoverify_validations(table_list, job.job_id)

        self.validate_scalable_job_jmtables("DDB Verification", job)
        if not self.verify_bad_chunks_absent(job.job_id):
            self.log.error("DV2 job [%s] found bad chunks in ArchChunkDDBDrop", job.job_id)
            self.error_list += f" [DV2 job {job.job_id} added Bad Chunks to ArchChunkToDDBDrop] "
        return job

    def get_mountpath_folder(self):
        """
        Fetch the mountpath folder details for volumes associated with given SIDB store
        """
        if not self.mount_path_folder:
            query = f"""
                   select top 1 DC.folder, MP.mountpathname,'CV_MAGNETIC', V.volumename from archChunk AC,
                   mmvolume V, MMMountPath MP, MMMountpathToStorageDevice MPSD, MMDeviceController DC
                   where V.SIDBStoreId = {self.store_obj.store_id}
                   and MP.mountpathid = V.currmountpathid
                   and MPSD.mountpathid = MP.mountpathid
                   and DC.deviceid = MPSD.deviceid"""
            self.log.info("QUERY: %s", query)
            self.csdb.execute(query)
            result = self.csdb.fetch_one_row()
            self.log.info(f"QUERY OUTPUT : {result}")
            if not result:
                raise Exception("mount path folder not found")
            mount_path_location = self.ma_machine_obj.os_sep.join(result)
            self.log.info("RESULT (mount path folder): %s", mount_path_location)
            self.mount_path_folder = mount_path_location


    def create_orphan_data(self):
        """
        This method creates a dummy dedupe chunk with testcase id

        Args:
            store_id (int)  - store id on which dummy chunks needs to be created"""

        self.log.info("creating orphan data...")

        self.log.info("Generating  unique data of size 1 GB")
        self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path_list[0], 0.1)
        self.log.info("Setting number of Readers on subclient to 1")
        self.subclient_obj_list[0].data_readers = 1
        self.log.info("Running 1 backup of size 1 GB")

        job = self.subclient_obj_list[0].backup("Incremental")
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run Incremental backup with error: {job.delay_rason}")
        self.log.info("Backup job completed.")
        file_size = 0
        folder_size = 0
        self.log.info("Fetching chunk to be made orphan")
        orphan_chunks_list = []
        chunks_list = self.mm_helper.get_chunks_for_job(job.job_id, order_by = 1)
        os_sep = self.ma_machine_obj.os_sep
        chunk_details = chunks_list[0]
        chunk = os_sep.join(chunk_details[0:2])
        chunk = f"{chunk}{os_sep}CV_MAGNETIC{os_sep}{chunk_details[2]}{os_sep}CHUNK_{chunk_details[3]}"
        orphan_chunks_list.append(chunk)
        orphan_data_path =f"{chunk_details[0]}{os_sep}{chunk_details[1]}{os_sep}CV_MAGNETIC{os_sep}{chunk_details[2]}"

        #Sometimes when the commcell is new and doesn't have chunk IDs reaching upto test case ID, this orphan
        #chunk id may not get removed by OCL

        self.orphan_chunks_folder = orphan_chunks_list[-1]
        self.orphan_chunks_file = self.ma_machine_obj.join_path(orphan_data_path,
                                                                 f'CHUNKMAP_TRAILER_{chunk_details[-1]}')

        self.log.info(f"Orphan Chunk ==> {self.orphan_chunks_folder}")


        self.log.info("Disable Phase 3 pruning on MA by adding additional setting DedupPrunerDisablePhase3 at MediaAgent level")
        self.ma_client.add_additional_setting('MediaAgent', 'DedupPrunerDisablePhase3', 'INTEGER', '1')
        log_lines_before = 0
        matched_lines = self.dedup_helper.validate_pruning_phase(self.store_obj.store_id, self.tcinputs['MediaAgentName'], phase=2)
        if matched_lines:
            log_lines_before = len(matched_lines)
        self.log.info(f"Total number of phase 2 pruning log lines before deleting job = {log_lines_before}")

        self.log.info(f"Deleting job {job.job_id}")
        sp_copy_obj = self.sp_obj_list[0].get_copy("Primary")
        sp_copy_obj.delete_job(job.job_id)

        self.log.info("Waiting for Phase 2 pruning to complete")

        for i in range(10):
            self.log.info("data aging + sleep for 240 seconds: RUN %s", (i + 1))

            job = self.mm_helper.submit_data_aging_job()

            self.log.info(f"Data Aging job: {job.job_id}")
            if not job.wait_for_completion():
                if job.status.lower() == "completed":
                    self.log.info(f"job {job.job_id} completed")
                else:
                    raise Exception(f"Job {job.job_id} Failed with {job.delay_reason}")
            matched_lines = self.dedup_helper.validate_pruning_phase(self.store_obj.store_id, self.tcinputs['MediaAgentName'], phase=2)

            if matched_lines and len(matched_lines) != log_lines_before:
                self.log.info(matched_lines)
                self.log.info(f"Successfully validated the phase 2 pruning on sidb - {self.store_obj.store_id}")
                pruning_done = True
                break
            else:
                self.log.info(f"Continuing with next attempt")

        self.log.info("Preparing store for Corruption")


        self.log.info("Marking store for corruption after checking that SIDB2 is not running")

        self.log.info("Explicitly marking store for recovery after 60 seconds")
        time.sleep(60)
        if self.dedup_helper.wait_till_sidb_down(str(self.store_obj.store_id), self.ma_client, timeout=600):
            self.log.info("SIDB2 process is not running, can mark the store for recovery")

        else:
            self.log.error("SIDB2 process is still running and can't mark the store for recovery")
            raise Exception("SIDB2 process is still running and can't mark the store for recovery")


        substore_obj = self.store_obj.get(self.store_obj.all_substores[0][0])
        substore_obj.mark_for_recovery()


        self.log.info("Starting Full Reconstruction Job")
        recon_job = self.store_obj.recover_deduplication_database(full_reconstruction=True)
        self.log.info(f"Started DDB Recon job id {recon_job.job_id}")
        if recon_job.wait_for_completion():
            self.log.info(f"Full recon with job id {recon_job.job_id} completed successfully")
        else:
            raise Exception(f"Full recon with job id {recon_job.job_id} failed to complete with JPR {recon_job.delay_reason}")

        self.log.info("Removing additional setting to disable Phase 3")
        self.ma_client.delete_additional_setting('MediaAgent', 'DedupPrunerDisablePhase3')

        self.log.info("Orphan chunks generated successfully.")


    def wait_for_pruning_complete(self):
        """
        Wait for Pruning to complete
        """
        pruning_count = 0
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15, 15)
        self.log.info("Verifying if pruning has completed on sidb store : %s", self.store_obj.store_id)

        for _ in range(0, 10):
            self.log.info("Submitting a data aging")
            da_job = self.mm_helper.submit_data_aging_job()
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job with error : {0}".format(da_job.delay_reason)
                )
            if self.dedup_helper.validate_pruning_phase(self.store_obj.store_id, self.tcinputs['MediaAgentName']):
                self.log.info(f"Phase 3 pruning complete for store - {self.store_obj.store_id}")
                return True
            else:
                self.log.info(f"Phase 3 pruning not yet complete on store - {self.store_obj.store_id}.")
                self.log.info("Will check again after 4 minutes")
                time.sleep(240)

        self.log.error(f"Phase 3 pruning did not complete on store {self.store_obj.store_id} after 40+ minutes")
        raise Exception(f"Phase 3 pruning did not complete on store {self.store_obj.store_id} after 40+ minutes")

    def prune_jobs(self, list_of_jobs):
        """
        Prunes jobs from storage policy copy

        Args:
            list_of_jobs(obj) - List of jobs
        """
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        sp_copy_obj = self.sp_obj_list[0].get_copy("Primary")
        for job in list_of_jobs:
            sp_copy_obj.delete_job(job.job_id)
            self.log.info("Deleted job from %s with job id %s", self.sp_obj_list[0].name, job.job_id)
        self.log.info("Updating RMSpareStatusUpdateTime to -1 for all volumes in store")
        query = f"update mmvolume set RMSpareStatusUpdateTime=-1 where sidbstoreid={self.store_obj.store_id}"
        self.log.info("QUERY => %s", query)
        self.optionobj.update_commserve_db(query)
        self.mm_helper.submit_data_aging_job()



    def perform_defrag_tuning(self, enable=True):
        """
        This function enables or disables defrag related settings
        - 128 attribute on MountPath
        - DedupeDrillHoles on MediaAgent

        Args:
            enable(boolean) - Boolean value for enabling or disabling the Defrag related settings
        """
        #Find Mountpath and turn off 128 bit if enable=True, turn on 128 if enable=False
        mountpath_attributes = "& ~128"
        self.ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
        if not enable:
            self.log.info("Removing Drill Holes Regkey")
            self.ma_client.delete_additional_setting("MediaAgent", "DedupDrillHoles")
            self.log.info("adding 128 attribute back to mountpaths of library %s", self.library_name)
            mountpath_attributes = "|128"
        else:
            self.log.info("setting drill holes regkey to 0")
            self.ma_client.add_additional_setting("MediaAgent", "DedupDrillHoles", 'INTEGER', '0')
            self.log.info("removing 128 attribute from mountpaths of library %s", self.library_name)

        query = f"update MMMountpath set attribute = attribute {mountpath_attributes} where mountpathid in (" \
                f"select mountpathid from MMMountpath where libraryid in (" \
                f"select libraryid from MMLibrary where aliasname = '{self.library_name}'))"


        self.log.info("QUERY => %s", query)
        self.optionobj.update_commserve_db(query)

    def is_orphan_chunk_present(self):
        """
        Verify if orphan chunk is present on disk
        """
        if self.ma_machine_obj.check_file_exists(self.orphan_chunks_file) \
                and self.ma_machine_obj.check_directory_exists(self.orphan_chunks_folder):
            self.log.info("Orphan chunk exists")
            return True
        self.log.info("Orphan chunk is removed")
        return False

    def get_mountpath_physical_size(self):
        """
        Get physical size of the mount path
        """
        self.get_mountpath_folder()
        return round(self.ma_machine_obj.get_folder_size(self.mount_path_folder, size_on_disk=True))

    def run_space_reclaim_job(self):
        """
        runs space reclaim job on the provided store object

        Args:
            store (object) - store object wher espace reclaim job needs to run

            with_ocl (bool) - set True if the job needs to run with OCL phase

        Returns:
            (object) job object for the space reclaim job
        """
        space_reclaim_job = self.store_obj.run_space_reclaimation(level=4, clean_orphan_data=True,
                                                                  use_scalable_resource= True)
        self.log.info("Space reclaim job with OCL: %s", space_reclaim_job.job_id)

        exit_condition = 900
        while space_reclaim_job.phase == "Validate Dedupe Data" and space_reclaim_job.status != "Running":
            self.log.info("Job Status : [%s]. Will check again after 10 Seconds", space_reclaim_job.status)
            time.sleep(10)
            exit_condition-=10
            if not exit_condition:
                self.log.error("Job is not in Validate Dedupe  Data phase even after 15 minutes")

        table_list = ['ArchChunkToVerify2', 'ArchChunkToVerify', ]
        self.log.info("Performing CSDB Validations for ArchChunkToVerify2 table")
        self.archchunktoverify_validations(table_list, space_reclaim_job.job_id, validate_defrag=True)

        # validate resync scheduled immediately on job start
        self.log.info("VALIDATION: if store was marked for Validate and Prune?")

        count = 60
        while space_reclaim_job.phase != "Defragment Data" and count > 0:
            self.log.info(f"Attempt {61-count} : Waiting for job {space_reclaim_job.job_id} to enter the Defragment Data phase")
            time.sleep(10)
        if count > 0:
            self.log.info(f"Job {space_reclaim_job.job_id} is in Defragment Data Phase. Chekcing Resync Flags in 15 seconds")
            time.sleep(15)
            self.store_obj.refresh()
            self.log.info("RESULT (flags): %s", self.store_obj.store_flags)
            if self.store_obj.store_flags & 33554432:
                self.log.info("validate and prune flags were set on store as expected")
            else:
                raise Exception("validate and prune flags were not set on store after space reclaim operation")
        else:
            self.log.error(f"Job {space_reclaim_job.job_id} did not enter Defragment Data phase even after 10 minutes timeout")
            raise Exception(f"Job {space_reclaim_job.job_id} did not enter Defragment Data phase even after 10 minutes timeout")

        self.log.info("Waiting for job completion ")
        if not space_reclaim_job.wait_for_completion():
            raise Exception(f"Failed to run space reclamation job with error: {space_reclaim_job.delay_reason}")
        self.log.info("DDB Space Reclamation completed.")

        self.log.info("Check if DDB_VERIFICATION_INPROGRESS flag is set")
        if self.is_dv2_in_progress_flag_set():
            self.log.error("ERROR : DDB_VERIFICATION_INPROGRESS flag is set even when "
                           "Space Reclamation job is complete.")
            self.error_list += " [DDB_VERIFICATION_INPROGRESS validation failure during DDB Space Reclamation Job] "
        else:
            self.log.info("DDB_VERIFICATION_INPROGRESS flag is not set when Space Reclamation job is complete.")


        table_list = ['ArchChunkToVerify2History', 'ArchChunkToVerifyHistory', ]
        self.log.info("Performing CSDB Validations for ArchChunkToVerify2History table")
        self.archchunktoverify_validations(table_list, space_reclaim_job.job_id, validate_defrag=True)
        self.validate_scalable_job_jmtables("Space Reclamation", space_reclaim_job)

        query_get_total_space_reclaimed = f"""
SELECT uncompBytes
FROM JMAdminJobStatsTable WITH (NOLOCK)
WHERE jobId = {space_reclaim_job.job_id}"""
        self.log.info(f"Executing query: {query_get_total_space_reclaimed}")
        total_space_reclaimed_bytes = self.mm_helper.execute_select_query(query_get_total_space_reclaimed)
        self.log.info(f"Query result: {total_space_reclaimed_bytes}")
        self.total_space_reclaimed_mb = int(total_space_reclaimed_bytes[0][0]) / (1024 * 1024)
        self.log.info(f"Total Space Reclaimed value reported: {self.total_space_reclaimed_mb} MB")

    def verify_bad_chunks_absent(self, dv2_job_id):
        """
        Verify that no bad chunks are added by given DV2 job id in ArchChunkDDBDrop table

        Args:
            dv2_job_id (int)    --  DV2 Job ID

        Returns:
            True if no bad chunks are added by this job, False otherwise.
        """

        self.log.info("Checking bad chunks added by job ID - [%s]", dv2_job_id)
        query = f"Select count(*) from ArchChunkDDBDrop where SIDBStoreID={self.store_obj.store_id} and " \
                f"reserveint = {dv2_job_id}"
        self.log.info("QUERY ==> %s", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_one_row()
        self.log.info("Bad chunks fetched by query = %s", str(rows))
        if str(rows[0]) != '0':
            self.log.info("Bad chunks were found.")
            return False
        self.log.info("No bad chunks were found.")
        return True

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            if not "unix" in self.ma_machine_obj.os_info.lower():
                self.disable_ransomware_protection(self.media_agent_obj)
            self.create_resources()
            self.perform_defrag_tuning(enable=True)
            self.run_backups()
            self.run_dv2_job('full', 'quick')
            self.run_dv2_job('full', 'complete')

            self.prune_jobs(list_of_jobs = [self.backup_job_list[j] for j in range(0,len(self.backup_job_list), 2)])
            self.wait_for_pruning_complete()
            self.create_orphan_data()
            size_before_defrag = self.get_mountpath_physical_size()
            self.run_space_reclaim_job()
            size_after_defrag = self.get_mountpath_physical_size()

            self.log.info("==ORPHAN CHUNK LISTING VALIDATION==")
            if self.is_orphan_chunk_present():
                self.log.error("Orphan Chunk still exists after Space Reclamation with OCL")
                self.error_list+=" [Orphan Chunk still exists after Space Reclamation with OCL] "
            else:
                self.log.info("Orphan Chunk Listing validation successful")

            self.log.info("==SPACE RECLAMATION VALIDATION==")
            if not size_after_defrag < size_before_defrag:
                self.log.error("Size of Mountpath Folder has not reduced after Space Reclamation")
                self.error_list += " [Size of Mountpath Folder has not reduced after Space Reclamation] "
            else:
                self.log.info(f"Size of mount path reduced by: {size_before_defrag - size_after_defrag} MB")
                self.log.info(f"Total Space Reclaimed value reported: {self.total_space_reclaimed_mb} MB")

                diff = abs(self.total_space_reclaimed_mb - (size_before_defrag - size_after_defrag))
                percent_diff = diff * 100 / self.total_space_reclaimed_mb
                self.log.info(f"mount path physical size vs space reclaimed value reported = {percent_diff}%")
                if percent_diff > 25:
                    self.log.error("mount path physical size vs space reclaimed value reported => 25%")
                    self.error_list += " [mount path physical size vs space reclaimed value reported => 25%]"
                else:
                    self.log.info("mount path physical size vs space reclaimed value reported =< 25%")
                    self.log.info("Space Reclamation Size validation successful")

            self.log.info("Run Full DV2 to make sure that there are no bad chunks after Space Reclamation")
            self.run_dv2_job('full', 'complete')

            if self.error_list:
                raise Exception(self.error_list)
        except Exception as exp:
            self.log.error("Failing test case : Error Encountered - %s", str(exp))
            self.status = constants.FAILED
            self.result_string = str(exp)




    def tear_down(self):
        """Tear down function of this test case"""
        if self.reset_ransomware:
            self.log.info(
                "Enabling ransomware protection on client %s", self.client.client_id)
            self.media_agent_obj.set_ransomware_protection(True)
        self.perform_defrag_tuning(enable=False)

        self.log.info("Cleaning up the test case environment")
        try:
            self.cleanup()
        except Exception as exp:
            self.log.error("Cleanup failed, Please check the setup manually - [%s]", str(exp))

