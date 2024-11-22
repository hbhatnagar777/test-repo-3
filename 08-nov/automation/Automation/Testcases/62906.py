"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    cleanup()       --  cleans up the entities

    create_resources()--	Create the resources required to run backups

    create_content()        --  creates content for subclient

    get_table_row_count()   --  Get distinct AF count for the given table

    get_active_files_store()    --  return store object

    delete_alternate_content()  --  delete alternate files from current content path directory

    run_backup()			--	Run backup job on subclient

    verify_phase2_pruning() --  verify logical pruning finishes successfully

    run_ms()                --  run mark and sweep to create zeroref entries

    verify_phase3_pruning() --  verify physical pruning finishes successfully

    drill_hole_check()      --  check if drill holes happened or not for given chunks

    verify_compact()        --  verofu given chunk was compacted during defrag job

    get_mountpath_folder()		--	Fetch the mountpath folder details for volumes associated with given SIDB store

    prune_jobs()			--	Prunes jobs from storage policy copy

    perform_defrag_tuning()		--	This function enables or disables defrag related settings

    get_mountpath_physical_size()	--	Get physical size of the mount path

    run_space_reclaim_job()		--	runs space reclaim job on the provided store object

    get_chunks()            --  get chunks of the job from CSDB

    verify_restore()    --  run restore job followed by verification of source and destination data

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case


    TcInputs to be passed in JSON File:
    "62906": {
        "ClientName"    : "Name of a Client",
        "AgentName"     : "File System",
        "MediaAgentName": "Name of a MediaAgent","
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "mount_path"    : "Path to be used as MP for Library, only necessary for linux ma",
        "dedup_path"    : "Path to be used for creating Dedupe-Partitions, only necessary for linux ma"
    }


Design steps:

1)	Create SP and set device stream to 1 on the storage policy.
2)	Create subclient and disable compression and create content
3)  Set below reg key on MA MEdiaAgent/MaxSFileContainerSize to  (to  increase container size to 256MB)
4)  Run backup job 1
5) Delete alternate files in content
6) run backup job 2
7) set dedupdrillhole regkey to 0 and remove attribute 128 on MP
8) Delete backup job 1 and let pruning catch up
9) run compaction (make sure chunk is compacted)
10) delete alternate files in content
11) run backup job 3
12) remove  dedupdrillhole regkey  and set attribute 128 on MP
13) delete job2 and let pruning catch up
14) verify from SIDBPhysicaldelete logs drill hole did not happen on compacted chunk
15) create non-dedupe copy and run auxcopy job
16) Run Restore from secondary copy


"""
import time
from AutomationUtils import constants
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
        self.name = "Verify drill hole doesnt happen on compacted chunk"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.mountpath = None
        self.ma_name = None
        self.store_obj = None
        self.sp_obj_list = []
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.client_machine_obj = None
        self.ma_machine_obj = None
        self.ma_library_drive = None
        self.dedup_path = None
        self.content_path = None
        self.subclient_obj = None
        self.bkpset_obj = None
        self.client_system_drive = None
        self.backup_job_list = []
        self.sqlobj = None
        self.mm_admin_thread = None
        self.optionobj = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.storage_pool_name = None
        self.storage_pool_name2 = None
        self.storage_pool = None
        self.storage_pool2 = None
        self.content_path_list = []
        self.error_list = ""
        self.mount_path_folder = None
        self.media_agent_obj = None
        self.dedup_helper = None
        self.restore_dest_path = None
        self.windows_machine_obj = None
        self.error_flag = []
        self.plan = None
        self.plan_name = None
        self.ma_client = None
        self.substore_list = None
        self.first_pruning_lines = None

    def setup(self):
        """Setup function of this test case"""
        self.optionobj = OptionsSelector(self.commcell)
        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)
        self.ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 25 * 1024)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 25 * 1024)

        self.storage_pool_name = f"StoragePool_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"
        self.storage_pool_name2 = f"StoragePool2_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"
        self.plan_name = f"PLAN_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"
        self.backupset_name = f"BkpSet_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"
        self.subclient_name = f"Subc_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))[1:]}"

        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"), self.id)
        else:
            self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, self.id, "MP")

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, str(self.id), "DedupDDB")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get('dedup_path'), str(self.id), "DedupDDB")

        for content in range(0, 2):
            self.content_path_list.append(self.client_machine_obj.join_path(self.client_system_drive, self.id,
                                                                            f"subc{content+1}"))

        self.restore_dest_path = self.client_machine_obj.join_path(self.client_system_drive,
                                                                   str(self.id), "Restoredata")

        if self.client_machine_obj.check_directory_exists(self.restore_dest_path):
            self.client_machine_obj.remove_directory(self.restore_dest_path)
        self.client_machine_obj.create_directory(self.restore_dest_path)

    def cleanup(self):
        """
        Clean up the entities created by this test case
        """

        self.log.info("Cleaning up content directories of these subclients")
        for content in range(0, 2):
            if self.client_machine_obj.check_directory_exists(self.content_path_list[content]):
                self.log.info("Deleting already existing content directory [%s]", self.content_path_list[content])
                self.client_machine_obj.remove_directory(self.content_path_list[content])

        if self.client_machine_obj.check_directory_exists(self.restore_dest_path):
            self.log.info("Deleting restore directory [%s]", self.restore_dest_path)
            self.client_machine_obj.remove_directory(self.restore_dest_path)

        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.bkpset_obj = self.agent.backupsets.get(self.backupset_name)
            if self.bkpset_obj.subclients.has_subclient(self.subclient_name):
                self.subclient_obj = self.bkpset_obj.subclients.get(self.subclient_name)
                self.log.info(f'disassociating any plans from subclient {self.subclient_name}')
                self.subclient_obj.plan = None
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info(f'deleted backupset {self.backupset_name}')
        if self.commcell.plans.has_plan(self.plan_name):
            self.commcell.plans.delete(self.plan_name)
            self.log.info(f'deleted plan {self.plan_name}')
        if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.commcell.storage_pools.delete(self.storage_pool_name)
            self.log.info(f'deleted pool {self.storage_pool_name}')
        if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name2):
            self.commcell.storage_pools.delete(self.storage_pool_name2)
            self.log.info(f'deleted pool {self.storage_pool_name2}')

    def create_resources(self):
        """Create all the resources required to run backups"""

        self.log.info("===STEP: Configuring TC Environment===")

        if self.client_machine_obj.check_directory_exists(self.content_path_list[0]):
            self.log.info("Deleting already existing content directory [%s]", self.content_path_list[0])
            self.client_machine_obj.remove_directory(self.content_path_list[0])
        self.client_machine_obj.create_directory(self.content_path_list[0])

        if not self.ma_machine_obj.check_directory_exists(self.mountpath):
            self.log.info("Creating mountpath directory [%s]", self.mountpath)
            self.ma_machine_obj.create_directory(self.mountpath)

        # create Storage Pool
        self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mountpath,
                                                            self.ma_name, self.ma_name,
                                                            self.dedup_path)

        # create plan
        self.commcell.storage_pools.refresh()
        self.commcell.plans.refresh()
        self.log.info(f'Creating the plan {self.plan_name}')
        self.commcell.plans.refresh()
        self.plan = self.commcell.plans.add(self.plan_name, "Server", self.storage_pool_name)
        self.log.info(f'Plan {self.plan_name} created')

        # disabling the schedule policy
        self.plan.schedule_policies['data'].disable()

        self.sp_obj_list.append(self.plan.storage_policy)

        # get store object
        self.get_active_files_store()
        self.store_obj.refresh()
        self.substore_list = []
        for substores in self.store_obj.all_substores:
            self.substore_list.append(substores[0])

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mm_helper.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        self.subclient_obj = self.bkpset_obj.subclients.add(self.subclient_name)
        self.subclient_obj.plan = [self.plan, [self.content_path_list[0]]]
        self.log.info("Successfully configured Subclient [%s]", f"{self.subclient_name}")

        self.subclient_obj.allow_multiple_readers = False

        # disable compression
        self.log.info("Disabling compression on subclient ")
        self.subclient_obj.software_compression = 4

    def create_content(self):
        """
        create desired content for subclient
        """

        if not self.client_machine_obj.check_directory_exists(self.content_path_list[0]):
            self.client_machine_obj.create_directory(self.content_path_list[0])

        source_dir = f"{self.content_path_list[0]}"

        self.log.info(source_dir)
        self.log.info("Generating content for subclient [%s] at [%s]", self.subclient_obj.name,
                      source_dir)
        self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'], source_dir, 0.240)
        self.log.info("created content")

        self.windows_machine_obj = Machine(self.client)
        list_of_files = []
        list_of_files = self.windows_machine_obj.get_files_in_path(source_dir)
        self.log.info(list_of_files)

    def get_table_row_count(self, table, storeid):
        """ Get distinct AF count for the given table
            Args:
                table (str) - tablename to get count
                storeid (object) - storeid

            Returns:
                num_rows    (int) - number of rows
        """
        query = f"select count(distinct archfileid) from {table} where sidbstoreid  = {storeid} "
        self.log.info(f"Query => {query}")
        self.csdb.execute(query)
        num_rows = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"Output ==> {num_rows}")
        return num_rows

    def get_active_files_store(self):
        """returns active store object for files iDA"""

        self.commcell.deduplication_engines.refresh()
        dedup_engines_obj = self.commcell.deduplication_engines
        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])

    def delete_alternate_content(self):
        """
            delete alternate files from content folder
        """

        source_dir = f"{self.content_path_list[0]}"
        target = ""
        target_folders = self.client_machine_obj.get_folders_in_path(source_dir)
        self.log.info(target_folders)
        if target_folders:
            target = target_folders[0]
        self.log.info(f"Deleting every alternate file from {target}")
        self.optionobj.delete_nth_files_in_directory(self.client_machine_obj, target, 2, "delete")

    def run_backup(self):
        """
         Run backup job
        """

        self.log.info("Starting backup on subclient %s", self.subclient_obj.name)
        self.backup_job_list.append(self.subclient_obj.backup("FULL"))
        if not self.backup_job_list[-1].wait_for_completion():
            raise Exception(
                "Failed to run backup job with error: {0}".format(self.backup_job_list[-1].delay_reason)
            )
        self.log.info("Backup job [%s] on subclient [%s] completed", self.backup_job_list[-1].job_id,
                      self.subclient_obj.name)

    def verify_phase2_pruning(self, storeid):
        """
        this method verifies that phase 2 pruning and MS have finished for the given storeid
        Args:
            storeid (int) - store id
        """
        # confirm phase 2 pruning is finished
        phase2_pruning_done = False
        iterations = 0
        while not phase2_pruning_done and iterations < 4:
            table_count_mmdel = self.get_table_row_count('mmdeletedaf', storeid)
            self.log.info(f'Count of AFs in mmdeletedaf table for store {storeid} '
                          f'is {table_count_mmdel}')
            table_count_mmtracking = self.get_table_row_count('mmdeletedarchfiletracking', storeid)
            self.log.info(f'Count of AFs in mmdelTracking table for store {storeid} '
                          f'is {table_count_mmtracking}')
            if table_count_mmdel == 0 and table_count_mmtracking == 0:
                phase2_pruning_done = True
                self.log.info(f'phase2 pruning finished successfully for store {storeid}')
            else:
                self.log.info(f'iteration {iterations} of 4: {storeid} still has entries in '
                              f'mmdel tables, wait 5 minutes and try again')
                iterations += 1
                time.sleep(300)
        if not phase2_pruning_done:
            self.log.error(f'FAILURE: phase2 pruning didnt finish for store {storeid}')
            raise Exception("TC FAILED, phase2 pruning didnt finish")

    def run_ms(self):
        """
        add reg key, run backup that immediately triggers MS, remove reg key
        """

        # temporarily set pruning interval back to 60 and wait for any existing sidb2 process
        # to come down
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)
        self.log.info("check if sidb process is running, and wait for it to come down")
        if not self.dedup_helper.wait_till_sidb_down(str(self.store_obj.store_id), self.commcell.clients.get(
                self.tcinputs.get("MediaAgentName"))):
            raise Exception("sidb process did not come down in 10 minutes, cleanup failed")
        else:
            self.log.info(f'sidb process is down for store {self.store_obj.store_id}')

        # get last ms run time for each substore
        self.store_obj.refresh()
        substore_str = ','.join(map(str, self.substore_list))
        query = f"""select entityid, longlongVal from mmentityprop where propertyname = 
                                       'DDBMSRunTime' and entityid in 
                                       ({substore_str})"""
        self.log.info(f"QUERY: {query} ")
        self.csdb.execute(query)
        first_ms_run_time = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {first_ms_run_time}")

        # add reg key to force MS to get triggered immediately next time sidb2 comes up
        self.log.info("setting DDBMarkAndSweepRunIntervalSeconds additional setting to 120")
        self.ma_client.add_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds",
                                              "INTEGER", "120")
        self.log.info("sleeping 15 seconds so reg key is set before backup's sidb2 comes up")
        time.sleep(15)

        ms_ran = False
        iterations = 0
        while not ms_ran and iterations < 4:
            self.log.info("running new backup just to trigger MS to run immediately")
            self.store_obj.refresh()
            self.run_backup()
            self.csdb.execute(query)
            second_ms_run_time = self.csdb.fetch_all_rows()
            self.log.info(f"QUERY OUTPUT : {second_ms_run_time}")
            if int(second_ms_run_time[0][1]) > int(first_ms_run_time[0][1]):
                self.log.info(f"confirmed MS ran on substores of store {self.store_obj.store_id}")
                ms_ran = True
            else:
                self.log.info(f"iteration {iterations} of 4: MS didnt run yet, so run another dv2 to induce it")
                iterations += 1
        if not ms_ran:
            self.log.error(f"MS never ran on both substores of store {self.store_obj.store_id}")
            raise Exception(f"MS never ran on both substores of store {self.store_obj.store_id}")

        # remove reg key that runs Mark and Sweep immediately
        self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting")
        self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

        # set pruning interval back to 2 minutes to allow phase 3 pruning to run
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)

    def verify_phase3_pruning(self, firstpruningpass=True):
        """
        verify phase 3 pruning occurs

        Args:
            firstpruningpass (bool) -- pass true for first job deletion, false for second job deletion

        """

        pruning_done = False
        iterations = 0
        while not pruning_done and iterations < 10:

            matched_lines = self.dedup_helper.validate_pruning_phase(self.store_obj.store_id,
                                                                     self.tcinputs['MediaAgentName'])
            self.log.info(matched_lines)

            if matched_lines:
                if firstpruningpass:
                    self.first_pruning_lines = len(matched_lines)
                else:
                    if self.first_pruning_lines < len(matched_lines):
                        self.log.info(f"Successfully validated the phase 3 pruning on sidb for job deletion - "
                                      f"{self.store_obj.store_id}")
                        pruning_done = True
                        break
                self.log.info(f"Successfully validated the phase 3 pruning on sidb for job deletion - "
                              f"{self.store_obj.store_id}")
                pruning_done = True
                break

            else:
                self.log.info(f"Iteration {iterations} of 10: No phase 3 pruning activity on sidb - "
                              f"{self.store_obj.store_id} yet. "
                              f"Checking after 240 seconds")
                iterations += 1
                time.sleep(240)

        if not pruning_done:
            self.log.error(f'FAILURE: phase3 pruning didnt finish for store {self.store_obj.store_id}')
            raise Exception("TC FAILED, phase3 pruning didnt finish")

    def drill_hole_check(self, chunks):
        """
        check if drill holes happened or not for given chunks
        Args:
            chunks (list) - a list of chunk ids
        """

        log_file = "SIDBPhysicalDeletes.log"
        match_regex = [" H "]
        drill_hole = False

        self.log.info("----Check if drill hole happened on compacted chunks---")

        matched_lines, matched_strings = self.dedup_helper.parse_log(
            self.tcinputs['MediaAgentName'], log_file, match_regex[0], single_file=True)

        for matched_line in matched_lines:
            line = matched_line.split()
            # self.log.info(line)
            if int(line[7]) in chunks:
                drill_hole = True
                drill_hole_chunk = int(line[7])

        if drill_hole:
            raise Exception("Drill hole happened on chunk %s ", drill_hole_chunk)
        else:
            self.log.info("Drill hole did not happen on compacted chunk.Passing the case")

    def verify_compact(self, chunks):
        """
        verify compact of chunk occurs

        Args:
            chunks (list) - list of chunks from first backup job
        """

        # log_file = "SIDBPhysicalDeletes.log"
        log_file = "DefragPhysicalDeletes.log"
        match_regex = [" O "]
        compact_occurrence = False
        compact_records = []
        self.log.info("Check for compacted chunks")

        matched_lines, matched_strings = self.dedup_helper.parse_log(
            self.tcinputs['MediaAgentName'], log_file, match_regex[0], single_file=True)

        for matched_line in matched_lines:
            line = matched_line.split()
            if int(line[7]) in chunks:
                compact_occurrence = True
                compact_records.append(line[7])
        if compact_occurrence:
            self.log.info(f"CHUNK WAS COMPACTED: {compact_records} ")
        else:
            raise Exception("compaction did not occur")

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

    def prune_jobs(self, list_of_jobs):
        """
        Prunes jobs from storage policy copy

        Args:
            list_of_jobs (list) - List of job objects
        """
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        sp_copy_obj = self.sp_obj_list[0].get_copy("Primary")
        for job in list_of_jobs:
            sp_copy_obj.delete_job(job.job_id)
            self.log.info("Deleted job from %s with job id %s", self.sp_obj_list[0].name, job.job_id)
        self.mm_helper.submit_data_aging_job(
            copy_name="Primary",
            storage_policy_name=self.plan.storage_policy.storage_policy_name,
            is_granular=True, include_all=False,
            include_all_clients=True,
            select_copies=True,
            prune_selected_copies=True)

    def perform_defrag_tuning(self, enable=True):
        """
        This function enables or disables defrag related settings
        - 128 attribute on MountPath
        - DedupeDrillHoles on MediaAgent
        -MaxSFileContainerItems and MaxSFileContainerSize on MediaAgent
        Args:
            enable(boolean) - Boolean value for enabling or disabling the Defrag related settings
        """
        # Find Mountpath and turn off 128 bit if enable=True, turn on 128 if enable=False
        mountpath_attributes = "& ~128"

        if not enable:
            self.log.info("Removing Drill Holes Regkey")
            self.ma_client.delete_additional_setting("MediaAgent", "DedupDrillHoles")
            self.log.info("Removing Max container size Regkey")
            self.ma_client.delete_additional_setting("MediaAgent", "MaxSFileContainerSize")
            self.log.info("Removing Max container items Regkey")
            self.ma_client.delete_additional_setting("MediaAgent", "MaxSFileContainerItems")

            self.log.info("adding 128 attribute back to mountpaths of pool %s", self.storage_pool_name)
            mountpath_attributes = "|128"

            self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)
        else:
            self.log.info("setting drill holes regkey to 0")
            self.ma_client.add_additional_setting("MediaAgent", "DedupDrillHoles", 'INTEGER', '0')
            self.log.info("Setting Max container size regkey to 268435456")
            self.ma_client.add_additional_setting("MediaAgent", "MaxSFileContainerSize", 'INTEGER', '268435456')

            self.log.info("Setting Max container items regkey to 2048")
            self.ma_client.add_additional_setting("MediaAgent", "MaxSFileContainerItems", 'INTEGER', '2048')

            self.log.info("removing 128 attribute from mountpaths of pool %s", self.storage_pool_name)

        query = f"""update MMMountpath set attribute = attribute {mountpath_attributes} where mountpathid in (
                    select mountpathid from MMMountpath where libraryid in (
                    select libraryid from MMLibrary where aliasname = '{self.storage_pool_name}'))"""

        self.log.info("QUERY => %s", query)
        self.optionobj.update_commserve_db(query)

    def get_mountpath_physical_size(self):
        """
        Get physical size of the mount path

        """
        self.get_mountpath_folder()
        return round(self.ma_machine_obj.get_folder_size(self.mount_path_folder, size_on_disk=True))

    def run_space_reclaim_job(self):
        """
        runs space reclaim job on the provided store object

        """
        self.store_obj.refresh()

        space_reclaim_job = self.store_obj.run_space_reclaimation(level=4, clean_orphan_data=True,
                                                                  use_scalable_resource=True)
        self.log.info("Space reclaim job with OCL: %s", space_reclaim_job.job_id)

        exit_condition = 900
        while space_reclaim_job.phase == "Validate Dedupe Data" and space_reclaim_job.status != "Running":
            self.log.info("Job Status : [%s]. Will check again after 10 Seconds", space_reclaim_job.status)
            time.sleep(10)
            exit_condition -= 10
            if not exit_condition:
                self.log.error("Job is not in Validate Dedupe  Data phase even after 15 minutes")

        self.log.info("Waiting for job completion ")
        if not space_reclaim_job.wait_for_completion():
            raise Exception(f"Failed to run space reclamation job with error: {space_reclaim_job.delay_reason}")
        self.log.info("DDB Space Reclamation completed.")

    def get_chunks(self, joblist):
        """
        get chunks for jobs in joblist
        Args:
            joblist (list of job objects) - list of job objects
        Returns:
            chunks_job  (list)  - list of data chunks in the job
        """

        jobid = joblist[-1].job_id
        self.log.info("Jobid to get the chunks is : ", jobid)
        query = f"SELECT  archchunkid   FROM  archchunkmapping  WHERE archfileid IN (SELECT id FROM archfile" \
                f" WHERE     jobid= {jobid}   AND       filetype=1)"
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")
        chunks_job = []
        for count, item in enumerate(res):
            chunks_job.append(int(item[0]))
            self.log.info("got the chunks belonging to the backup job %s", jobid)
            self.log.info("Chunks are: {0}".format(chunks_job))
        return chunks_job

    def verify_restore(self):
        """
        Run a restore job followed by verification between source and destination
        Returns:
            boolean - false if restored data validation fails, true if it succeeds
        """

        self.log.info("----Running restore job from sec copy ---")
        restore_job = self.subclient_obj.restore_out_of_place(self.client, self.restore_dest_path,
                                                              [self.content_path_list[0]], copy_precedence=2)
        self.log.info("restore job from non-dedupe copy has started.")
        if not restore_job.wait_for_completion():
            self.log.error(
                "restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
            raise Exception(
                "restore job [{0}] has failed with {1}.".format(restore_job.job_id, restore_job.delay_reason))

        self.log.info("restore job [%s] from non-dedupe copy has completed  ", restore_job.job_id)

        self.log.info("Performing Data Validation after Restore")

        difference = self.client_machine_obj.compare_folders(self.client_machine_obj,
                                                             self.content_path_list[0], self.restore_dest_path +
                                                             "\subc1")
        if difference:
            self.log.error("Validating Data restored  Failed")
            return False

        self.log.info("Data Restore Validation passed")
        return True

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.create_resources()
            self.perform_defrag_tuning(enable=True)
            self.create_content()
            self.run_backup()

            # get chunks for first job for validations
            chunks = []
            chunks = self.get_chunks(self.backup_job_list)

            self.delete_alternate_content()
            self.run_backup()

            # Delete Job 1
            self.prune_jobs(list_of_jobs=[self.backup_job_list[0]])
            self.log.info(f"deleting job {self.backup_job_list[0].job_id}")

            self.verify_phase2_pruning(self.store_obj.store_id)
            self.run_ms()
            self.verify_phase3_pruning()

            size_before_defrag = self.get_mountpath_physical_size()
            self.run_space_reclaim_job()
            size_after_defrag = self.get_mountpath_physical_size()
            self .log.info(f"Size before {size_before_defrag} and size after defrag is {size_after_defrag}")
            self.log.info("==SPACE RECLAMATION VALIDATION==")
            if not size_after_defrag < size_before_defrag:
                self.log.error("Size of Mountpath Folder has not reduced after Space Reclamation")
                self.error_list += " [Size of Mountpath Folder has not reduced after Space Reclamation] "
            else:
                self.log.info("Space Reclamation Size validation successful")

            self.verify_compact(chunks)

            # Run backup Job 3
            self.delete_alternate_content()
            self.run_backup()
            self.perform_defrag_tuning(enable=False)

            # Delete backup job 2
            self.log.info(f'deleting job {self.backup_job_list[1].job_id} and {self.backup_job_list[2].job_id}')
            self.prune_jobs(list_of_jobs=[self.backup_job_list[1], self.backup_job_list[2]])

            self.verify_phase2_pruning(self.store_obj.store_id)
            self.run_ms()
            self.verify_phase3_pruning(firstpruningpass=False)

            # Check if holes were drilled on compacted chunk
            self.drill_hole_check(chunks)

            # create non dedupe storage pool and sec non dedupe copy and run restore from sec job
            copy2 = 'nondedupe_copy'
            self.storage_pool2 = self.commcell.storage_pools.add(self.storage_pool_name2, self.mountpath + '_2',
                                                                 self.ma_name,
                                                                 ddb_ma=None, dedup_path=None)
            self.plan.storage_policy.create_secondary_copy(copy_name=copy2, library_name=self.storage_pool_name2,
                                                           media_agent_name=self.ma_name)

            # Removing association with System Created Autocopy schedule
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, copy2)
            auxcopy_job = self.sp_obj_list[0].run_aux_copy()
            self.log.info("Auxcopy job [%s] has started.", auxcopy_job.job_id)
            if not auxcopy_job.wait_for_completion():
                self.log.error("Auxcopy job [%s] has failed with %s.", auxcopy_job.job_id, auxcopy_job.delay_reason)
                raise Exception("Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id,
                                                                                auxcopy_job.delay_reason))
            self.log.info("Auxcopy job [%s] has completed.", auxcopy_job.job_id)

            # Run restore from sec copy and validate data restored
            if not self.verify_restore():
                self.status = constants.FAILED
            else:
                self.log.info("Restore Verification Succeeded.")

            if self.error_list:
                raise Exception(self.error_list)

        except Exception as exp:
            self.log.error("Failing test case : Error Encountered - %s", str(exp))
            self.status = constants.FAILED
            self.result_string = str(exp)

    def tear_down(self):
        # Tear down function of this test case

        self.perform_defrag_tuning(enable=False)
        self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting if it exists")
        self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")
        self.log.info("Performing unconditional cleanup of test environment")
        try:
            self.cleanup()
        except Exception as exp:
            self.log.error("Cleanup failed, Please check the setup manually - [%s]", str(exp))
