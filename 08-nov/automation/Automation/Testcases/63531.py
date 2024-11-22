# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""mark and sweep takes place or not"""

import time
from cvpysdk import deduplication_engines
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from AutomationUtils import commonutils


"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case     

    create_resources()  --	Create the resources required to run backups
    
    create_content()        --  creates content for subclient
    
    verify_restore()    --  run restore job followed by verification of source and destination data
    
    prune_jobs()                -- prune jobs from a storage policy copy
    
    delete_alternate_content()  --  delete alternate files from content
    
    get_table_row_count()  --get count of distinct Afs from a table
    
    run_backup()			--	Run backup job on subclient
    
    clean_test_environment() -- cleanup of created entities
     
    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
    
This testcase verifies Garbage collection using table based bitmap

1) create pool and SP
2) disable compression,set blocksize to 32KB
3) set regkey MediaAgent\\DDBMarkAndSweepMaxBitmapMillions = 0 (for bitmap table)
3) create 35 GB content
4) run Backup, We should get 1million primary records
5) delete alternate files from content  and run another backup
6) delete job 1 and make sure pruning is completed
7) set MS interval to 1 hr
8) make sure MS runs 
9) bitmap file is created with below logging in SIDBEngine log
 
Mark And Sweep. Max Bmp Elems [0]
 
10) Once MS completes let phase3 pruning complete
12) run full dv2
11) run restore  and verify it completes fine.

input json file arguments required:

                        "ClientName": "name of the client machine as in commserve",
                        "AgentName": "File System",
                        "MediaAgentName": "name of the media agent as in commserve",
                        "library_name": name of the Library to be reused
                        "mount_path": path where the data is to be stored
                        "dedup_path": path where dedup store to be created

                        note --
                                ***********************************
                                if library_name_given then reuse_library
                                else:
                                    if mountpath_location_given -> create_library_with_this_mountpath
                                    else:
                                        auto_generate_mountpath_location
                                        create_library_with_this_mountpath
                                if dedup_path_given -> use_given_dedup_path
                                else it will auto_generate_dedup_path
                                ***********************************
"""


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Verify garbage collection using table based bitmap"
        self.tcinputs = {
            "MediaAgentName": None,
        }
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
        self.subclient_obj = None
        self.bkpset_obj = None
        self.client_system_drive = None
        self.backup_job_list = []
        self.sqlobj = None
        self.mm_admin_thread = None
        self.gdsp = None
        self.optionobj = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.storage_pool_name = None
        self.content_path_list = []
        self.error_list = ""
        self.mount_path_folder = None
        self.media_agent_obj = None
        self.dedup_helper = None
        self.restore_dest_path = None
        self.windows_machine_obj = None
        self.time_moved = False
        self.sql_password = None
        self.user_sp = False
        self.ma_client = None
        self.subclient_name_1 = None
        self.substore_id = None
        self.subclient_obj_1 = None

    def setup(self):
        """Setup function of this test case"""
        self.optionobj = OptionsSelector(self.commcell)
        self.sql_password = commonutils.get_cvadmin_password(self.commcell)
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        self.ma_name = self.tcinputs.get('MediaAgentName')

        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 80000)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))

        # if unix ma, use custom ddb and mp.  if windows, grab any drive with at least 80 GB space
        if "unix" in self.ma_machine_obj.os_info.lower():
            if self.is_user_defined_dedup:
                self.log.info("custom ddb path supplied")
                self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get('dedup_path'),
                                                                str(self.id), "DedupDDB")
            else:
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            if self.is_user_defined_mp:
                self.log.info("custom mount path supplied")
                self.mountpath = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"))
            else:
                self.log.error("Please use custom mp in json for this case, root may not have enough space")
                raise Exception("custom mp not supplied for Unix MA!")
        else:
            self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 80000)
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, str(self.id), "DedupDDB")
            self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, "MP")

        self.storage_pool_name = f"StoragePool_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))}"
        self.storage_policy_name = f"SP_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))}"
        self.backupset_name = f"BkpSet_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))}"
        self.subclient_name = f"Subc_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))}"
        self.subclient_name_1 = f"Subc1_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))}"
        for content in range(0, 2):
            self.content_path_list.append(self.client_machine_obj.join_path(self.client_system_drive, self.id,
                                                                            f"subc{content + 1}"))

        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)

        self.restore_dest_path = self.client_machine_obj.join_path(self.client_system_drive,
                                                                   str(self.id), "Restoredata")
        if self.client_machine_obj.check_directory_exists(self.restore_dest_path):
            self.client_machine_obj.remove_directory(self.restore_dest_path)
        self.client_machine_obj.create_directory(self.restore_dest_path)

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

            # Creating a storage pool and associate to SP
        self.log.info("Configuring Storage Pool for Primary ==> %s", self.storage_pool_name)
        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.gdsp = self.commcell.storage_pools.add(self.storage_pool_name, self.mountpath,
                                                        self.tcinputs['MediaAgentName'],
                                                        self.tcinputs['MediaAgentName'], self.dedup_path)
        else:
            self.gdsp = self.commcell.storage_pools.get(self.storage_pool_name)
        self.log.info("Done creating a storage pool for Primary")
        self.commcell.disk_libraries.refresh()
        self.log.info("Configuring Storage Policy ==> %s", self.storage_policy_name)
        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.sp_obj_list.append(self.commcell.storage_policies.add(
                    storage_policy_name=f"{self.storage_policy_name}",
                    global_policy_name=self.storage_pool_name))

        else:
            self.sp_obj_list.append(self.commcell.storage_policies.get(f"{self.storage_policy_name}"))

        # set the block deduplication factor 32kb
        self.log.info("set the dedup block size to 32 kb")

        xml = """<App_UpdateStoragePolicyReq>
                    <StoragePolicy>
                    <storagePolicyName>{0}</storagePolicyName>
                    </StoragePolicy>
                    <sidbBlockSizeKB>32</sidbBlockSizeKB>
                    </App_UpdateStoragePolicyReq>""".format(self.storage_policy_name)
        self.commcell._qoperation_execute(xml)

        xml = """<App_UpdateStoragePolicyReq>
                            <StoragePolicy>
                            <storagePolicyName>{0}</storagePolicyName>
                            </StoragePolicy>
                            <sidbBlockSizeKB>32</sidbBlockSizeKB>
                            </App_UpdateStoragePolicyReq>""".format(self.storage_pool_name)
        self.commcell._qoperation_execute(xml)

        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)

        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores

            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])
                self.substore_id = self.store_obj.all_substores[0][0]
                self.log.info("Substoreid is .. [%s] ", self.substore_id)

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mm_helper.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        self.subclient_obj = self.mm_helper.configure_subclient(self.backupset_name,
                                                                f"{self.subclient_name}",
                                                                f"{self.storage_policy_name}",
                                                                f"{self.content_path_list[0]}")
        self.log.info("Successfully configured Subclient [%s]", f"{self.subclient_name}")

        self.subclient_obj.allow_multiple_readers = False

        # disable compression
        self.log.info("Disabling compression on subclient ")
        self.subclient_obj.software_compression = 4

        self.subclient_obj_1 = self.mm_helper.configure_subclient(self.backupset_name,
                                                                  f"{self.subclient_name_1}",
                                                                  f"{self.storage_policy_name}",
                                                                  f"{self.content_path_list[1]}")

        self.log.info("Successfully configured Subclient [%s]", f"{self.subclient_name_1}")

        # disable compression
        self.log.info("Disabling compression on subclient ")
        self.subclient_obj_1.software_compression = 4

    def create_content(self, num, size):
        """
        create desired content for subclient
            Args:
                    num = subclient number
                    size = size of the content dir
            returns:
                    nothing
        """

        if not self.client_machine_obj.check_directory_exists(self.content_path_list[num]):
            self.client_machine_obj.create_directory(self.content_path_list[num])

        source_dir = f"{self.content_path_list[num]}"

        self.log.info(source_dir)
        self.log.info("Generating content for subclient [%s] at [%s]", self.subclient_obj.name,
                      source_dir)
        self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'], source_dir, size)

        self.log.info("created content")

    def verify_restore(self):
        """
        Run a restore job followed by verification between source and destination

        returns
            (bool) True if data validation succeeds else False.
        """

        self.log.info("----Running restore job  ---")
        restore_job = self.subclient_obj.restore_out_of_place(self.client, self.restore_dest_path,
                                                              [self.content_path_list[0]], copy_precedence=1)
        self.log.info("restore job from copy has started.")
        if not restore_job.wait_for_completion():
            self.log.error(
                "restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
            raise Exception(
                "restore job [{0}] has failed with {1}.".format(restore_job.job_id, restore_job.delay_reason))

        self.log.info("restore job [%s] has completed  ", restore_job.job_id)

        self.log.info("Performing Data Validation after Restore")

        os_sep = self.client_machine_obj.os_sep
        difference = self.client_machine_obj.compare_folders(self.client_machine_obj,
                                                             self.content_path_list[0], self.restore_dest_path + os_sep
                                                             + "subc1")
        if difference:
            self.log.error("Validating Data restored  Failed")
            return False

        self.log.info("Data Restore Validation passed")
        return True

    def prune_jobs(self, list_of_jobs):
        """
        Prunes jobs from storage policy copy

        Args:
            list_of_jobs(obj) - List of jobs
        Returns:
            nothing
        """
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        sp_copy_obj = self.sp_obj_list[0].get_copy("Primary")
        for job in list_of_jobs:
            sp_copy_obj.delete_job(job.job_id)
            self.log.info("Deleted job from %s with job id %s", self.sp_obj_list[0].name, job.job_id)
        da_job = self.mm_helper.submit_data_aging_job(storage_policy_name=self.storage_policy_name,
                                                      copy_name='primary', is_granular=True, include_all=False,
                                                      include_all_clients=True, select_copies=True,
                                                      prune_selected_copies=True)
        self.log.info("data aging job: %s", da_job.job_id)
        if not da_job.wait_for_completion():
            self.log.info("Failed to run data aging with error: %s", da_job.delay_reason)

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

    def get_table_row_count(self, table, storeid):
        """ Get distinct AF count for the given table
            Args:
                storeid (object) - storeid
                table (str) - tablename to get count
            Returns:
                num_rows    (int) - number of rows
        """
        query = f"select count(distinct archfileid) from {table} where sidbstoreid  = {storeid} "
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        num_rows = int(self.csdb.fetch_one_row()[0])
        self.log.info("Output ==> %s", num_rows)
        return num_rows

    def run_backup(self, subclient_obj):
        """
         Run backup job

            Args:
                subclient_obj   (subclient object)

            Returns:
                nothing
        """

        self.log.info("Starting backup on subclient %s", subclient_obj.name)
        self.backup_job_list.append(subclient_obj.backup("FULL"))
        if not self.backup_job_list[-1].wait_for_completion():
            raise Exception(
                "Failed to run backup job with error: {0}".format(self.backup_job_list[-1].delay_reason)
            )
        self.log.info("Backup job [%s] on subclient [%s] completed", self.backup_job_list[-1].job_id,
                      subclient_obj.name)

    def clean_test_environment(self):
        """
        Clean up test environment
        """
        for i in range(0, 2):
            self.log.info(self.content_path_list[i])
            if self.client_machine_obj.check_directory_exists(self.content_path_list[i]):
                self.client_machine_obj.remove_directory(self.content_path_list[i])
                self.log.info("Deleted the Content Directory.")
            else:
                self.log.info("Content directory does not exist.")

        if self.client_machine_obj.check_directory_exists(self.restore_dest_path):
            self.client_machine_obj.remove_directory(self.restore_dest_path)
            self.log.info("Deleted the Restore Directory.")
        else:
            self.log.info("Restore directory does not exist.")
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
                          "Treating as soft failure as storage policy will be reused***")

        try:
            self.log.info("Cleaning up storage pool - [%s]", self.storage_pool_name)
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(f"Deleting Storage Pool - {self.storage_pool_name}")
                self.commcell.storage_pools.delete(self.storage_pool_name)
        except Exception as excp:
            self.log.info("***Failure in deleting storage pool during cleanup. "
                          "Treating as soft failure as storage pool will be reused***")

    def run(self):
        """Run function of this test case"""
        try:

            self.clean_test_environment()
            self.create_resources()
            self.create_content(0, 35)
            self.log.info("setting regkey to create bitMap file to 1")
            self.ma_client.add_additional_setting("MediaAgent", "DDBMarkAndSweepMaxBitmapMillions", 'INTEGER', '0')
            self.run_backup(self.subclient_obj)

            self.delete_alternate_content()
            self.run_backup(self.subclient_obj)

            # Delete Job 1
            self.prune_jobs(list_of_jobs=[self.backup_job_list[0]])

            table_count_mmdel = self.get_table_row_count('mmdeletedaf', self.store_obj.store_id)

            self.log.info("Count of AFs in mmdeletedaf table is %s ", table_count_mmdel)

            table_count_mmtracking = self.get_table_row_count('mmdeletedarchfiletracking', self.store_obj.store_id)

            self.log.info("Count of AFs in mmdeletedarchfiletracking table is %s", table_count_mmtracking)

            totalcount = table_count_mmdel+table_count_mmtracking

            if totalcount == 0:
                raise Exception("AFs were not added to mmdeletedaf or tracking table after job deletion")

            else:
                da_job = self.mm_helper.submit_data_aging_job(storage_policy_name=self.storage_policy_name,
                                                              copy_name='primary', is_granular=True,
                                                              include_all=False,
                                                              include_all_clients=True,
                                                              select_copies=True,
                                                              prune_selected_copies=True)
                self.log.info("data aging job: %s", da_job.job_id)
                if not da_job.wait_for_completion():
                    self.log.info("Failed to run data aging with error: %s", da_job.delay_reason)
                time.sleep(30)
                da_job = self.mm_helper.submit_data_aging_job(storage_policy_name=self.storage_policy_name,
                                                              copy_name='primary', is_granular=True,
                                                              include_all=False,
                                                              include_all_clients=True,
                                                              select_copies=True,
                                                              prune_selected_copies=True)
                self.log.info("data aging job: %s", da_job.job_id)
                if not da_job.wait_for_completion():
                    self.log.info("Failed to run data aging with error: %s", da_job.delay_reason)
                time.sleep(300)
                pruning_done = False
                for i in range(10):
                    matched_lines = self.dedup_helper.validate_pruning_phase(self.store_obj.store_id, self.ma_client, 2)
                    self.log.info(matched_lines)

                    if matched_lines:
                        table_count_mmdel = self.get_table_row_count('mmdeletedaf', self.store_obj.store_id)
                        self.log.info("Count of AFs in mmdeletedaf table is %s ", table_count_mmdel)
                        table_count_mmtracking = self.get_table_row_count('mmdeletedarchfiletracking',
                                                                          self.store_obj.store_id)
                        self.log.info("Count of AFs in mmdeletedarchfiletracking table is %s", table_count_mmtracking)
                        if table_count_mmdel == 0 and table_count_mmtracking == 0:
                            pruning_done = True
                            break
                    else:
                        self.log.warning(f'phase 2 pruning did not occur yet - no matched lines found in attempt'
                                         f' [{i+1}]')

                if not pruning_done:
                    raise Exception("Pruning is not over even after 10 attempts. Raising Exception")

            error_flag = []

            # add reg key to override CS settings and run Mark and Sweep immediately
            self.log.info("setting DDBMarkAndSweepRunIntervalSeconds additional setting to 120")
            self.ma_client.add_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds", "INTEGER", "120")

            self.log.info("sleep for 300 seconds")
            time.sleep(300)

            self.log.info(
                "running a backup job so that sidb2 process picks up, mark and sweep takes places")
            # create new subclient with new data

            self.create_content(1, 1)
            self.run_backup(self.subclient_obj_1)

            # remove reg key that runs Mark and Sweep immediately
            self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting")
            self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

            self.log.info("sleep for 300 seconds")
            time.sleep(300)
            log_file = "SIDBEngine.log"

            common = str(self.store_obj.store_id) + "-0-" + str(self.substore_id) + "-0"
            # SIDBEngId-GrNo-SubStoId-SpltNo
            # check the logs to make sure that deletion actually took place by
            # mark and sweep.
            self.log.info(
                "*************************CASE VALIDATIONS***************************")
            self.log.info(
                "---------------------Check Logs to confirm Mark & Sweep -----------------------")

            self.log.info("Case Validation 1:Check for number of "
                          "primary objects made invalid and remaining valid")
            statement = r"Total \[[0-9]+\], Approx Valid \[[0-9]+\], Approx Invalid \[[0-9]+\]"
            found = False
            (matched_lines, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs["MediaAgentName"], log_file, regex=statement,
                escape_regex=False, single_file=True)
            for matched_line in matched_lines:
                line = matched_line.split()
                for commonstring in line:
                    if common in commonstring:
                        found = True

            bitmap_logging = False
            if found:
                self.log.info("MS was run..now checking if bitmap was used")
                statement = r"Mark And Sweep. Max Bmp Elems \[0\]"
                (matched_lines, matched_string) = self.dedup_helper.parse_log(
                    self.tcinputs["MediaAgentName"], log_file, regex=statement,
                    escape_regex=False, single_file=True)
                for matched_line in matched_lines:
                    line = matched_line.split()
                    for commonstring in line:
                        if common in commonstring:
                            bitmap_logging = True
                            self.log.info(line)
            else:
                self.log.error("Result: Failed..MS was not run..")
                error_flag += ["failed to find: " + statement]

            if bitmap_logging:
                self.log.info("Bitmap type [2] is used..Case Passed. now waiting for phase3 pruning to happen")

                for i in range(10):
                    da_job = self.mm_helper.submit_data_aging_job(storage_policy_name=self.storage_policy_name,
                                                                  copy_name='primary', is_granular=True,
                                                                  include_all=False,
                                                                  include_all_clients=True, select_copies=True,
                                                                  prune_selected_copies=True)
                    self.log.info("data aging job: %s", da_job.job_id)
                    if not da_job.wait_for_completion():
                        self.log.info("Failed to run data aging with error: %s", da_job.delay_reason)
                    time.sleep(300)
                    matched_lines = self.dedup_helper.validate_pruning_phase(self.store_obj.store_id, self.ma_client, 3)
                    self.log.info(matched_lines)
                    pruning_done = False
                    if matched_lines:
                        pruning_done = True
                        break

                if not pruning_done:
                    self.log.info("Phase3 pruning did not occur even after 50 mins..Case failed")
                    error_flag += ["phase3 pruning not done even after 50 minutes "]
                else:
                    self.store_obj.refresh()
                    self.log.info("running full dv2 job on the store [%s]...", self.store_obj.store_id)
                    job = self.store_obj.run_ddb_verification(incremental_verification=False, quick_verification=False)
                    self.log.info("DV2 job: %s", job.job_id)
                    if not job.wait_for_completion():
                        raise Exception(f"Failed to run dv2 job with error: {job.delay_reason}")
                    self._log.info("DV2 job completed.")

                    # Run restore and validate data restored
                    if not self.verify_restore():
                        self.status = constants.FAILED
                    else:
                        self.log.info("Restore Verification Succeeded.")

            else:
                self.log.info("Bitmap type 2 was not used..Case failed")
                error_flag += ["failed to find: " + statement]

            if error_flag:
                # if the list is not empty then error was there, fail the test
                # case
                self.log.info(error_flag)
                raise Exception(f"testcase failed: {error_flag}")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        # Tear down function of this test case
        self.log.info("Removing additional settings")
        self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepMaxBitmapMillions")
        self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")
        self.log.info("Cleaning up the test case environment")
        try:
            self.clean_test_environment()
        except Exception as exp:
            self.log.error("Cleanup failed, Please check the setup manually - [%s]", str(exp))
