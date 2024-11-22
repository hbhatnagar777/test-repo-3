# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""This testcase verifies single pruner MA for disk library"""

import time
from cvpysdk import (storage, deduplication_engines)
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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    clean_test_environment() -- cleanup of created entities

    create_resources()--	Create the resources required to run backups

    run_backup()			--	Run backup job on subclient


    create_content()        --  creates content for subclient


    get_table_row_count()  -- get total count of rows from a table


    prune_jobs()                -- prune jobs from a storage policy copy

    get_Archfiles()         -- returns ArchFileids for the given job

    get_archchunks()       -- returns Archchunkids for the given job


    get_pruning_MAs()       -- get list of MA's when pruning is enabled

    get_pruning_MAs_disable() -- get list of MA's when pruning is disabled

    check_MA_for_Phase3_pruning()    -- checks pruning request is sent or not by verifying big archfile id

    set_unset_pruner_ma()      --set/unset pruner MA

    update_zeroref_count_in_DB()     -- updates zeroref count of store

    wait_for_pruning()      --wait till mmdeletedaf and mmdeletedarchfiletracking table is 0 for a store

    wait_for_pruning_for_non_dedup() -- wait till mmdeletedaf has archchunks of job 

    get_space_reclaim_MAs() -- gets list of MAs used by defrag phase

    run_space_reclaim_job()  -- runs space reclamation job without OCL on the given store

#add this part when pruner MA has been enabled
This testcase verifies single pruner MA for disk library

Take Pruner MA as input from json
Create disk library and share it with 2 Mas, one being the pruner MA
Create pool,  subclient

Run 5 backup jobs
Run below command to select pruner MA on disklib 
qoperation execscript -sn SetLibraryProperty -si crossmount_lin_lib -si EnableSinglePrunerMA -si 1 -si <input_prunerMA>
update MM_Prune_Process_Interval
update zerorefcount in idxsidbusagehistory table
Run DA
Verify whether pruning request is sent by checking the bigArchFile Id
Delete first 2 backup jobs
Run DA
Wait until pruning catches up. Mmdeletedaf and mmdeletedarchfiletracking table entries are 0
Verify from CSDB, the reserveint for Afs in mmdeletedafpruninglogs table is set to client id of the MA
Run defrag job and make sure defrag phase is run only via pruner MA

Create Non dedup pool,  subclient
Run 5 backup jobs
Run below command to select pruner MA on disklib 
Delete first 3 backup jobs
Run DA
Wait until pruning catches up. mmdeletedaf table entries are 0
Verify whether pruning is done

Disable puner ma and check whether pruning request is sent to all MA's in dedup
qoperation execscript -sn SetLibraryProperty -si crossmount_lin_lib -si EnableSinglePrunerMA -si 0 -si <input_prunerMA>
Delete couple of jobs and run DA 
Wait till the pruning catches up Mmdeletedaf and mmdeletedarchfiletracking table entries are 0
Make sure pruning request is sent to all Mas,confirm this from reserveint bit in mmdeletedafpruninglogs table.
Run defrag job and make sure defrag phase is run  via all MAs



input json file arguments required:

                64390 :{
                        "ClientName": "name of the client machine as in commserve",
                        "AgentName": "File System",
                        "MediaAgentName": "name of the Windows Media agents as in commserve",                        
                        "pruner_ma" : Windows MA that is to be set as pruner MA which is different than MA above
                        "username"  : Username of MediaAgent
                        "password" : Password of MediaAgent
                        }

"""


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        # Initializes test case class object
        super(TestCase, self).__init__()
        self.name = "Verify single pruner MA for disk library"
        self.tcinputs = {
            "MediaAgentName": None,
            "pruner_ma": None,
            "username": None,
            "password": None
        }
        self.library_name = None
        self.mountpath = None
        self.ma_name = None
        self.pruner_ma_name = None
        self.store_obj = None
        self.backupset_name = None
        self.subclient_name = None
        self.subclient_name_1 = None
        self.mm_helper = None
        self.client_machine_obj = None
        self.ma_machine_obj = None
        self.ma_library_drive = None
        self.dedup_path = None
        self.dedup_path_1 = None
        self.content_path = None
        self.content_path_1 = None
        self.subclient_obj = None
        self.subclient_obj_1 = None
        self.bkpset_obj = None
        self.client_system_drive = None
        self.backup_job_list = []
        self.backup_job_list_1 = []
        self.sqlobj = None
        self.mm_admin_thread = None
        self.gdsp = None
        self.optionobj = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.storage_pool_name = None
        self.media_agent_obj = None
        self.dedup_helper = None
        self.windows_machine_obj = None
        self.time_moved = False
        self.sql_password = None
        self.user_sp = False
        self.username = None
        self.password = None
        self.mount_location = None
        self.MA_name_FQDN = None
        self.library = None
        self.plan_name_1 = None
        self.plan_ob_1 = None
        self.plan_type = None
        self.non_dedup_pool_name = None
        self.non_dedup_pool_ob = None
        self.utils = None
        self.library_name = None
        self.library = None
        self.plan_ob = None
        self.plan_name = None
        self.error_flag = []

    def setup(self):
        """Setup function of this test case"""
        # creating necessary variables

        self.optionobj = OptionsSelector(self.commcell)
        self.sql_password = commonutils.get_cvadmin_password(self.commcell)
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.pruner_ma_name = self.tcinputs.get('pruner_ma')
        if self.pruner_ma_name.lower() == self.ma_name.lower():
            raise Exception("Pruner MA and MA cannot be the same")
        self.username = self.tcinputs.get('username')
        self.password = self.tcinputs.get('password')
        self.plan_type = "Server"
        self.flag = []

        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 25 * 1024)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.MA_name_FQDN = self.ma_machine_obj.client_object.client_hostname
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 25 * 1024)
        self.library_name = f"Lib_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"
        self.plan_name = "plan_for_dedup" + str(self.id)
        self.plan_name_1 = "plan_for_non_dedup" + str(self.id)

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        # creating dedup_path, mount_path and content_path

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"))
        else:
            self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, str(self.id), "MP")

        self.storage_pool_name = f"StoragePool_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"
        self.non_dedup_pool_name = f"Non_dedup_StoragePool_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"
        # self.storage_policy_name = f"SP_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"
        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, str(self.id), "DedupDDB")
            self.dedup_path_1 = self.ma_machine_obj.join_path(self.ma_library_drive, str(self.id), "DedupDDB1")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get('dedup_path'), str(self.id), "DedupDDB")
            self.dedup_path_1 = self.ma_machine_obj.join_path(self.tcinputs.get('dedup_path'), str(self.id),
                                                              "DedupDDB1")

        self.backupset_name = f"BkpSet_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"
        self.subclient_name = f"Subc_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"
        self.subclient_name_1 = f"Subc_TC_for_non_dedup{self.id}"

        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, self.id, "subc")
        self.log.info(f"Content path is ::  {self.content_path}")

        self.content_path_1 = self.client_machine_obj.join_path(self.client_system_drive, self.id, "subc_1")
        self.log.info(f"Content path for non_dedup is ::  {self.content_path_1}")

        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)

    def create_resources(self):
        """Create all the resources required to run backups"""

        self.log.info("===STEP: Configuring TC Environment===")

        # creating content path for dedup
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", self.content_path)
            self.client_machine_obj.remove_directory(self.content_path)
        self.client_machine_obj.create_directory(self.content_path)
        self.log.info(self.content_path)

        # Creating a storage pool
        self.log.info("Configuring Storage Pool for Primary ==> %s", self.storage_pool_name)
        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.gdsp = self.commcell.storage_pools.add(self.storage_pool_name, self.mountpath,
                                                        self.tcinputs['MediaAgentName'],
                                                        self.tcinputs['MediaAgentName'], self.dedup_path)
        else:
            self.gdsp = self.commcell.storage_pools.get(self.storage_pool_name)

        self.log.info(F"Done creating a storage pool [{self.storage_pool_name}] for Primary")

        # create plan
        self.log.info(f"creating plan [{self.plan_name}]")
        self.plan_ob = self.commcell.plans.add(plan_name=self.plan_name, plan_sub_type=self.plan_type,
                                               storage_pool_name=self.storage_pool_name)
        self.log.info(f"plan [{self.plan_name}] created")

        self.plan_ob.schedule_policies['data'].disable()
        self.mm_helper.remove_autocopy_schedule(self.plan_ob.storage_policy.storage_policy_name, "Primary")
        # self.plan_ob.disable_full_schedule()

        # checking library and sharing it

        self.library_name = self.storage_pool_name
        self.commcell.disk_libraries.refresh()

        if not self.commcell.disk_libraries.has_library(self.library_name):
            self.log.error("Disk library %s does not exist!", self.library_name)
            raise Exception(f"Disk library {self.library_name} does not exist!")

        else:
            self.library = self.commcell.disk_libraries.get(self.library_name)
            self.mount_location = f"share_{self.id}"
            self.log.info(self.mount_location)
            self.ma_machine_obj.share_directory(self.mount_location, self.mountpath, user=self.tcinputs["username"])
            self.mount_location = f"\\\\{self.MA_name_FQDN}\\share_{self.id}"
            self.log.info(self.mount_location)

            library_details = {
                "mountPath": self.mountpath,
                "mediaAgentName": self.ma_name
            }

            storage.DiskLibrary(
                self.commcell,
                self.library_name,
                library_details=library_details).share_mount_path(new_media_agent=self.pruner_ma_name,
                                                                  new_mount_path=self.mount_location,
                                                                  library_name=self.library_name,
                                                                  media_agent=self.ma_name, mount_path=self.mountpath,
                                                                  access_type=6, username=self.tcinputs["username"],
                                                                  password=self.tcinputs["password"])
            self.log.info("Library [%s] shared successfully.", self.library_name)

        self.log.info("Creating split partition")
        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)

        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores

            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])
                self.log.info("Storage pool created with one partition. Adding 2nd partition")
                self.store_obj.add_partition(self.dedup_path_1, self.tcinputs['MediaAgentName'])

        self.log.info("Split Partitions Created for storage pool")

        # creating backupset
        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mm_helper.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        # Adding Subclient to Backupset for dedup
        self.subclient_obj = self.bkpset_obj.subclients.add(self.subclient_name)
        self.log.info(f"Added subclient to backupset [{self.subclient_name}]")


        # creating uncompressable data
        self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'], self.content_path, 0.3)

        # Associating plan and content path to subclient for dedup

        self.subclient_obj.plan = [self.plan_ob, [self.content_path]]
        self.log.info("created content for dedup")

        # disable compression
        self.log.info("Disabling compression on subclient ")
        self.subclient_obj.software_compression = 4

        # Creating resources for non_dedup
        # creating content path for non dedup
        if self.client_machine_obj.check_directory_exists(self.content_path_1):
            self.log.info("Deleting already existing content directory [%s]", self.content_path_1)
            self.client_machine_obj.remove_directory(self.content_path_1)
        self.client_machine_obj.create_directory(self.content_path_1)
        self.log.info(self.content_path_1)

        # creating non dedup storage pool
        self.log.info(f"creating Non-dedup storage pool [{self.non_dedup_pool_name}]")
        if not self.commcell.storage_pools.has_storage_pool(self.non_dedup_pool_name):
            self.non_dedup_pool_ob = self.commcell.storage_pools.add(self.non_dedup_pool_name, self.mountpath,
                                                                     self.tcinputs['MediaAgentName'])
        else:
            self.non_dedup_pool_ob = self.commcell.storage_pools.get(self.non_dedup_pool_name)

        self.log.info(f"created Non-dedup storage pool [{self.non_dedup_pool_name}]")

        # create plan for non dedup
        self.log.info(f"creating plan [{self.plan_name_1}]")
        self.plan_ob_1 = self.commcell.plans.add(plan_name=self.plan_name_1, plan_sub_type=self.plan_type,
                                                 storage_pool_name=self.non_dedup_pool_name)
        self.log.info(f"plan [{self.plan_name_1}] created")

        self.plan_ob_1.schedule_policies['data'].disable()

        self.mm_helper.remove_autocopy_schedule(self.plan_ob_1.storage_policy.storage_policy_name, "Primary")
        # self.plan_ob_1.disable_full_schedule()

        # Adding Subclient to Backupset for non dedup
        self.subclient_obj_1 = self.bkpset_obj.subclients.add(self.subclient_name_1)
        self.log.info(f"Added subclient to backupset [{self.subclient_name_1}]")

        # creating uncompressable data
        self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'], self.content_path_1, 0.3)

        # Associating plan and content path to subclient for non_dedup

        self.subclient_obj_1.plan = [self.plan_ob_1, [self.content_path_1]]
        self.log.info("created content for non dedup")

        # disable compression
        self.subclient_obj_1.software_compression = 4

    def prune_jobs(self, plan_ob, list_of_jobs):
        """
        Prunes jobs from storage policy copy

        Args:
            plan_ob - instance of plan created
            list_of_jobs(obj) - List of jobs
        """
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)

        sp_copy_obj = plan_ob.storage_policy.get_copy("Primary")
        for job in list_of_jobs:
            sp_copy_obj.delete_job(job.job_id)
            self.log.info("Deleted job from %s with job id %s", plan_ob.storage_policy.storage_policy_name, job.job_id)

    def get_table_row_count(self, storeid):
        """ Get distinct AF count for the given table
            Args:
                storeid  - storeid
            Returns:
                (int) - total number of rows
        """
        query = f"select count(*) from mmdeletedaf where sidbstoreid  = {storeid} "
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        num_rows_mmdel = int(self.csdb.fetch_one_row()[0])
        self.log.info("number of mmdeletedaf rows ==> %s", num_rows_mmdel)
        query = f"select count(*) from mmdeletedarchfiletracking where sidbstoreid  = {storeid} "
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        num_rows_tracking = int(self.csdb.fetch_one_row()[0])
        self.log.info("number of mmdeletedarchfiletracking rows ==> %s", num_rows_tracking)
        total_count = num_rows_mmdel + num_rows_tracking
        return total_count

    def run_backup(self, subclient_obj, is_dedup):
        """
         Run backup job for dedup
         args:
            subclient object (object): instance of subclient created
            is_dedup = True/False- whether backup is carried out on dedup or not
        """

        time.sleep(45)
        self.log.info("Starting backup on subclient %s", subclient_obj.name)

        # running backup job for dedup
        if is_dedup:
            self.backup_job_list.append(subclient_obj.backup("FULL"))
            self.log.info(f"Backup job started{self.backup_job_list[-1].job_id}")
            self.mm_helper.wait_for_job_completion(self.backup_job_list[-1])
            self.log.info("Backup job [%s] on subclient [%s] completed", self.backup_job_list[-1].job_id,
                          subclient_obj.name)

        # running backup job for non_dedup
        else:
            self.backup_job_list_1.append(
                subclient_obj.backup("FULL", advanced_options={'mediaOpt': {'startNewMedia': True}}))
            self.log.info(f"Backup job started{self.backup_job_list_1[-1].job_id}")
            self.mm_helper.wait_for_job_completion(self.backup_job_list_1[-1])
            self.log.info("Backup job [%s] on subclient [%s] completed", self.backup_job_list_1[-1].job_id,
                          subclient_obj.name)

        return

    def set_unset_pruner_ma(self, libraryname, MAname, operation):
        """
            this function will Enable/Disable Pruner MA.
            Arguments:
                libraryname - Name of the library
                MAname      - name of the MA which is to be set as Pruner MA
                operation   - "enable' or 'disable'
        """
        if operation.lower() == "disable":
            command = "-sn SetLibraryProperty -si %s -si EnableSinglePrunerMA -si 0 -si %s" % (libraryname, MAname)
        elif operation.lower() == "enable":
            command = "-sn SetLibraryProperty -si %s -si EnableSinglePrunerMA -si 1 -si %s" % (libraryname, MAname)
        else:
            self.error_flag += ["Input is not correct in order to enable or disable prunerMA"]

        self.log.info("Executing Script - %s", command)
        self.commcell._qoperation_execscript(command)

    def get_archfiles(self, job):
        """
            this function will get the archFiles of the supplied job id.
            Arguments:
                job - job object for which details need to be checked.
            Returns:
                archFiles associated with the job
        """
        query = """SELECT    id
                   FROM      archFile
                   WHERE     jobId={0}""".format(job.job_id)
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(res)
        arch_files_job = []
        for count, item in enumerate(res):
            arch_files_job.append(int(item[0]))
        self.log.info(
            "got the archfiles belonging to the backup job %s", job.job_id)
        self.log.info("Archfiles are:{0}".format(arch_files_job))

        return arch_files_job

    def update_zeroref_count_in_DB(self):
        """
                    this function will update the ZerorefCount to non zero

        """
        query = """UPDATE IdxSIDBUsageHistory
                   SET ZeroRefCount = 11111 
                   WHERE SIDBStoreId = {0}""".format(self.store_obj.store_id)

        self.log.info(query)
        self.optionobj.update_commserve_db(query)

        return

    def run_space_reclaim_job(self, store):
        """
        runs space reclaim job on the provided store object
        Args:
            store (object) - store object where space reclaim job needs to run
        Returns:
            (object) job object for the space reclaim job
        """
        space_reclaim_job = store.run_space_reclaimation(level=4)
        self.log.info("Space reclaim job : %s", space_reclaim_job.job_id)
        if not space_reclaim_job.wait_for_completion():
            self.error_flag += [f"Failed to run DDB Space reclaim with error: {space_reclaim_job.delay_reason}"]
        self.log.info("DDB Space reclaim job completed.")
        return space_reclaim_job

    def get_pruning_MAs(self, storeid, arch_files_job):
        """
        List of Media agents used from mmdeletedafpruninglogs table
        Args:
            storeid (int)
            arch_files_job (list) AFids for which we need to get pruning MA names
        Returns:
            client_name (string) MA name used
        """
        arch_files_string = ', '.join(map(str, arch_files_job))
        query = "select name from app_client where id in(select distinct reserveint from " \
                "historydb.dbo.mmdeletedafpruninglogs where sidbstoreid = %s and " \
                "archfileid in ( %s ))" % (storeid, format(arch_files_string))

        self.log.info(query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(res)
        client_names = []
        for count, item in enumerate(res):
            client_names.append(str(item[0]))
        self.log.info("client names  are: (%s)" % format(client_names))
        return client_names

    def get_pruning_MAs_disable(self, storeid, arch_files_job):
        """
        List of Media agents used from mmdeletedafpruninglogs table
        Args:
            storeid (int)
            arch_files_job (list) AFids for which we need to get pruning MA names
        Returns:
            client_names (list) list of MA names used
        """
        arch_files_string = ', '.join(map(str, arch_files_job))
        query = "select name from app_client where id in(select distinct reserveint from " \
                "historydb.dbo.mmdeletedafpruninglogs where sidbstoreid = %s and " \
                "archfileid in ( %s ))" % (storeid, format(arch_files_string))

        self.log.info(query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(res)
        client_names = []
        for count, item in enumerate(res):
            client_names.append(str(item[0]))
        self.log.info("client names  are: (%s)" % format(client_names))
        return client_names

    def clean_test_environment(self):
        """
        Clean up test environment
        """
        try:

            self.mount_location = f"share_{self.id}"
            self.log.info(f"Removing sharing from {self.mount_location}")
            self.ma_machine_obj.unshare_directory(self.mount_location)
        except Exception as exe:
            self.log.error("UnShare failed: %s", self.mount_location)

        # deleting content directory for dedup
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.client_machine_obj.remove_directory(self.content_path)
            self.log.info("Deleted the Content Directory of dedup.")
        else:
            self.log.info("Content directory does not exist.")

        # deleting content directory for non_dedup
        if self.client_machine_obj.check_directory_exists(self.content_path_1):
            self.client_machine_obj.remove_directory(self.content_path_1)
            self.log.info("Deleted the Content Directory of non_dedup.")
        else:
            self.log.info("Content directory does not exist.")

        try:
            self.log.info(f"Deleting BackupSet{self.backupset_name}")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
        except Exception as excp:
            self.log.info("***Failure in deleting backupset during cleanup - %s "
                          "Treating as soft failure as backupset will be reused***", str(excp))

        # deleting dedup Plan
        if self.commcell.plans.has_plan(self.plan_name):
            self.log.info(f"Plan exists [{self.plan_name}], deleting that")
            self.commcell.plans.delete(self.plan_name)
            self.log.info(f"Plan deleted [{self.plan_name}].")

        # deleting non dedupe Plan
        if self.commcell.plans.has_plan(self.plan_name_1):
            self.log.info(f"Plan exists [{self.plan_name_1}], deleting that")
            self.commcell.plans.delete(self.plan_name_1)
            self.log.info(f"Plan deleted [{self.plan_name_1}].")

        # deleting storage pool
        if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.log.info(f"dedup pool[{self.storage_pool_name}] exists, deleting that")
            self.commcell.storage_pools.delete(self.storage_pool_name)
            self.log.info(f"dedup pool primary [{self.storage_pool_name}] deleted.")
        self.commcell.storage_pools.refresh()

        # deleting non dedup storage pool
        if self.commcell.storage_pools.has_storage_pool(self.non_dedup_pool_name):
            self.log.info(f"non dedupe pool[{self.non_dedup_pool_name}] exists, deleting that")
            self.commcell.storage_pools.delete(self.non_dedup_pool_name)
            self.log.info(f"non dedupe pool primary [{self.non_dedup_pool_name}] deleted.")
        self.commcell.storage_pools.refresh()

    def get_space_reclaim_MAs(self, reclamation_job):

        """
            function to get list of Media agents used for defrag phase
            Args:
                reclamation_job (object) - space reclamation job object
            returns:
                ma_names(list) - list of MediaAgent used for defrag phase
        """
        query = "select distinct name from app_client where id in " \
                " (select distinct SrcMAId from ArchJobStreamStatusHistory where JobId = {0}" \
                " and modifiedtime >(select startTime FROM JMAdminJobAttemptStatsTable JAS " \
                "WHERE JAS.JobId = {0} AND JAS.phaseNum = 4) and ModifiedReason = 'CREATE') ".format(reclamation_job.job_id)
        self.log.info(query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(res)
        ma_names = []
        for count, item in enumerate(res):
            ma_names.append(str(item[0]))
        self.log.info("MA names used by defrag phase are: (%s)" % format(ma_names))
        return ma_names

    def wait_for_pruning(self, storeid, plan_ob):
        """
        wait till mmdeletedaf and mmdeletedarchfiletracking table is 0 for a store
        args: storeid : (int) storeid got from store obj
              plan_ob :(obj) instance of plan created
        """
        totalcount = self.get_table_row_count(storeid)

        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        if totalcount == 0:
            self.error_flag += ["AFs were not added to mmdeletedaf or tracking table after job deletion"]

        else:
            pruning_done = False
            for i in range(10):
                da_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                              storage_policy_name=plan_ob.storage_policy.storage_policy_name,
                                                              is_granular=True, include_all_clients=True)

                self.log.info("data aging job: %s", da_job.job_id)
                da_job.wait_for_completion()
                time.sleep(180)
                totalcount = self.get_table_row_count(storeid)
                if totalcount == 0:
                    pruning_done = True
                    self.log.info("Pruning is done")
                    return pruning_done
            return pruning_done

    def wait_for_pruning_for_non_dedup(self, plan_ob_1, arch_chunks_job):
        """
                wait till mmdeletedaf  table is 0
                args: plan_ob : (instance) instance generated after creating plan
                      arch_chunks_job(list) :  list of archchunks related to each job
        """

        arch_chunks_string = ', '.join(map(str, arch_chunks_job))
        query = f"""SELECT COUNT(*) FROM MMDeletedAF 
                            WHERE ArchChunkId IN ({arch_chunks_string})
                                    """
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        totalcount = int(self.csdb.fetch_one_row()[0])
        self.log.info("number of mmdeletedaf rows ==> %s", totalcount)

        if totalcount == 0:
            self.error_flag += ["AF's are not added to mmdletedaf table"]

        else:
            pruning_done = False
            for i in range(10):

                self.log.info("data aging job started")
                da_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                              storage_policy_name=plan_ob_1.storage_policy.storage_policy_name,
                                                              is_granular=True, include_all_clients=True)
                self.log.info("data aging job: %s", da_job.job_id)
                da_job.wait_for_completion()
                time.sleep(180)
                query = f"""SELECT COUNT(*) FROM MMDeletedAF 
                                            WHERE ArchChunkId IN ({arch_chunks_string})
                                                    """
                self.log.info("Query => %s", query)
                self.csdb.execute(query)
                totalcount = int(self.csdb.fetch_one_row()[0])
                self.log.info("number of mmdeletedaf rows ==> %s", totalcount)

                if totalcount == 0:

                    # checking whether volumes are pruned from mmvolume table after pruning

                    query = f"""select count(*) from mmvolume where volumeid in (select distinct volumeid from historydb.dbo.mmdeletedafpruninglogs where
                                         ArchChunkId in ({arch_chunks_string}))"""
                    self.log.info("Query => %s", query)
                    self.csdb.execute(query)
                    num_rows_mmvol = int(self.csdb.fetch_one_row()[0])
                    self.log.info("number of mmvolume rows ==> %s", num_rows_mmvol)
                    if num_rows_mmvol == 0:
                        pruning_done = True
                        self.log.info("Pruning is done")
                        return pruning_done
                    else:
                        pruning_done = False
            return pruning_done

    def check_MA_for_Phase3_pruning(self):

        """
        checks whether pruning request is sent to pruner ma and bigarchfile id is generated

        returns:
            string - client_name
        """

        query = f""" select distinct reserveint from 
                historydb.dbo.mmdeletedafpruninglogs where sidbstoreid = {self.store_obj.store_id} and
                archfileid =  2147483647"""

        self.log.info(query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        if res == 0:
            self.error_flag += ["No rows found in mmdeletedafpruninglogs"]
        else:

            query_1 = f"""select name from app_client where id in ({query})"""

            self.log.info(query_1)
            self.csdb.execute(query_1)
            res = self.csdb.fetch_all_rows()
            self.log.info(res)
            ma_names = []
            for count, item in enumerate(res):
                ma_names.append(str(item[0]))
            self.log.info("MA names used by Phase3 Pruning are : (%s)" % format(ma_names))
            return ma_names

    def get_archchunks(self, job):
        """
                    this function will get the archFiles of the supplied job id.
                    Arguments:
                        job - job object for which details need to be checked.
                    Returns:
                        archFiles associated with the job
                """
        query = """SELECT    archChunkId
                           FROM      archChunkMapping
                           WHERE     jobId={0}""".format(job.job_id)
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(res)
        arch_chunks_job = []
        for count, item in enumerate(res):
            arch_chunks_job.append(int(item[0]))
        self.log.info(
            "got the archchunks belonging to the backup job %s", job.job_id)
        self.log.info("Archchunks are:{0}".format(arch_chunks_job))

        return arch_chunks_job

    def run(self):
        """Run function of this test case"""
        try:
            self.error_flag = []

            self.log.info("******************PERFORMING BACKUP FOR DEDUP**************************")
            self.clean_test_environment()
            self.create_resources()

            # Running the backup
            for i in range(1, 6):
                self.run_backup(self.subclient_obj, True)

            # enabling pruner ma
            self.set_unset_pruner_ma(self.library_name, self.pruner_ma_name, "enable")

            self.log.info("Case 1: ******************PERFORMING PHASE 3 PRUNING Validations**************************")

            # Make sure no pruning request is sent so increase prune interval.
            self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)

            # updating zerorefcount
            self.update_zeroref_count_in_DB()

            # Running data aging job

            aging_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                             storage_policy_name=self.plan_ob.storage_policy.storage_policy_name,
                                                             is_granular=True, include_all_clients=True)

            self.log.info("data aging job: %s", aging_job.job_id)
            aging_job.wait_for_completion()
            self.log.info(f"data aging job{aging_job.job_id} completed")
            time.sleep(30)

            pruning_done = self.wait_for_pruning(self.store_obj.store_id, self.plan_ob)
            self.store_obj.refresh()
            if pruning_done:
                MA_names = []
                # validating pruning request is sent to pruner ma
                MA_names = self.check_MA_for_Phase3_pruning()
                if (self.pruner_ma_name.lower() in [i.lower() for i in MA_names]) and len(MA_names) == 1:
                    self.log.info("validation passed. pruning request sent to pruner MA only for big Archfileid: %s",
                                  self.pruner_ma_name)
                else:
                    self.log.info("validation Failed. pruning request sent to multiple MA's ")
                    self.error_flag += ["Case 1 : Phase3 Pruning Failed, Raising Exception -- Phase3 Pruning request sent to Multiple MA's"]

            else:
                self.error_flag += ["Case 1: Phase3 Pruning Failed, Raising Exception -- Phase3 Pruning is not over even after 10 attempts"]

            # case 2:
            self.log.info("Case 2: ****************** DEDUPE PRUNING **************************")
            # getting archfiles related to each job
            arch_files_job = []
            arch_files_job = self.get_archfiles(self.backup_job_list[0])
            # add list of AFs for 2nd job
            arch_files_job.extend(self.get_archfiles(self.backup_job_list[1]))

            # Delete Job 1
            self.log.info("Delete Job 1 :: %s ", self.backup_job_list[0])
            self.prune_jobs(self.plan_ob, list_of_jobs=[self.backup_job_list[0]])
            # Delete Job 2
            self.log.info("Delete Job 2 ::  %s", self.backup_job_list[1])
            self.prune_jobs(self.plan_ob, list_of_jobs=[self.backup_job_list[1]])
            pruning_done = self.wait_for_pruning(self.store_obj.store_id, self.plan_ob)

            self.store_obj.refresh()
            if pruning_done:
                clients = []
                clients = self.get_pruning_MAs(self.store_obj.store_id, arch_files_job)
                self.log.info("MA names  are %s" % format(clients))
                if (self.pruner_ma_name.lower() in [i.lower() for i in clients]) and len(clients) == 1:
                    self.log.info("validation passed. pruning request sent to pruner MA only : %s", self.pruner_ma_name)

                    # run defrag job and do defrag validations
                    self.log.info("**** Doing space reclamation validations ****")
                    self.log.info("starting space reclaim job..")
                    reclamation_job = self.run_space_reclaim_job(self.store_obj)
                    MA_names = []
                    MA_names = self.get_space_reclaim_MAs(reclamation_job)
                    if (self.pruner_ma_name.lower() in [i.lower() for i in MA_names]) and len(MA_names) == 1:

                        self.log.info("validation passed. defrag phase used only pruner MA  : %s",
                                      self.pruner_ma_name)
                    else:
                        # defrag validation failed for regular dedupe pruning when pruner MA is enabled
                        self.error_flag += [
                            "Case 2: Dedupe Pruning , Raising Exception -- Defrag validation failed as defrag phase used multiple MAs"]
                else:
                    self.error_flag += ["Case 2: Dedupe Pruning , Raising Exception -- Pruning is sent to multiple MAs"]
            else:
                self.error_flag += ["Case 2: Dedupe Pruning , Raising Exception -- Pruning is not over even after 10 attempts"]

            # case 3: non dedupe pool validation
            self.log.info("Case 3: ****************** NON DEDUPE PRUNING **************************")

            # run backup job for 5 times with new media

            self.log.info("************* Running backup job for non dedup ***************")

            for i in range(1, 6):
                self.run_backup(self.subclient_obj_1, False)

            arch_chunks_job = []
            arch_chunks_job = self.get_archchunks(self.backup_job_list_1[0])
            # add chunks for job 2
            arch_chunks_job.extend(self.get_archchunks(self.backup_job_list_1[1]))

            arch_chunks_job.extend(self.get_archchunks(self.backup_job_list_1[2]))

            # deleting 3 backup jobs
            for j in range(3):
                self.log.info(f"Delete Job {j} with job id {self.backup_job_list_1[j]}")
                self.prune_jobs(self.plan_ob_1, list_of_jobs=[self.backup_job_list_1[j]])
                self.log.info(f"Job {self.backup_job_list_1[j]} deleted successfully")

            pruning_done = self.wait_for_pruning_for_non_dedup(self.plan_ob_1, arch_chunks_job)
            # Running data aging job
            if pruning_done:
                self.log.info("Non dedupe pruning is done and no entries in mmdel table")
            else:
                self.error_flag += [
                    "Case 3:Non dedupe pruning Failed, Raising Exception -- Pruning is not over even after 10 attempts"]

            # case 4 : disable pruner MA

            self.log.info("Case 4: ****************** CHECKING PRUNING AFTER DISABLING PRUNER MA **************************")

            # disable pruner MA
            self.set_unset_pruner_ma(self.library_name, self.pruner_ma_name, "disable")

            arch_files_job = []
            # add list of AFs for 3rd job
            arch_files_job = self.get_archfiles(self.backup_job_list[2])
            # add list of AFs for 4th job
            arch_files_job.extend(self.get_archfiles(self.backup_job_list[3]))

            # Delete Job 3 and 4
            self.prune_jobs(self.plan_ob, list_of_jobs=[self.backup_job_list[2]])
            self.prune_jobs(self.plan_ob, list_of_jobs=[self.backup_job_list[3]])
            pruning_done = self.wait_for_pruning(self.store_obj.store_id, self.plan_ob)
            if pruning_done:
                clients = []
                clients = self.get_pruning_MAs_disable(self.store_obj.store_id, arch_files_job)
                self.log.info("MA names are %s" % format(clients))
                if len(clients) > 1:
                    self.log.info("validation passed. pruning request sent to multiple MAs")

                    # run defrag job and do defrag validations
                    self.log.info("**** Doing space reclamation validations for multiple MAs ****")
                    self.log.info("starting space reclaim job..")
                    reclamation_job = self.run_space_reclaim_job(self.store_obj)
                    MA_names = []
                    MA_names = self.get_space_reclaim_MAs(reclamation_job)
                    if len(MA_names) > 1:
                        self.log.info("validation passed. defrag phase used multiple MAs")
                    else:

                        self.error_flag += [
                            "Case 4: Raising Exception -- Defrag phase used only single MA"]

                else:
                    self.error_flag += [
                        "Case 4: Checking Pruning after disabling Pruner MA , Raising Exception -- Pruning is sent to single MA"]
            else:
                self.error_flag += [
                    "Case 4: Checking Pruning after disabling Pruner MA , Raising Exception -- Pruning is not over even after 10 attempts"]

            self.log.info(self.error_flag)
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        if self.error_flag:
            self.log.info(self.error_flag)
            self.result_string = str(self.error_flag)
            self.status = constants.FAILED


    def tear_down(self):
        # Tear down function of this test case
        try:
            self.log.info("Starting cleanup")
            self.clean_test_environment()
            # reverting back prune process interval
            self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)


        except Exception as exe:
            self.log.error(exe)

