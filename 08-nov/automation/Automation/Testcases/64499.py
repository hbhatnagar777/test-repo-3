# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  create objects etc

    allocate_resources()  --  create environment

    deallocate_resources() -- cleanup

    get_active_files_store() -- returns store object

    run_backup_job() --  run supplied number of backup jobs

    identify_distributor() -- returns the partition that has the distributor bit set

    run_ms()    --  add reg key and run backup to trigger MS immediately

    rename_partition()  -- rename the ddb path to the current distributor partition

    prune_job() -- delete a job and run data aging

    logical_pruning_empty() -- check supplied table and confirm it has no afids for supplied store

    toggle_phase_3_pruning() -- add or remove additional setting DedupPrunerDisablePhase3

    get_zeroref_count_for_substore()  --  get latest pending delete count for one substore of ddb store

    zeroref_drain() -- confirms either zeroref has been built up, or has been drained

    confirm_distributor_change() -- confirms the partition marked as the distributor has changed

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Input JSON:

"64499": {
        "AgentName": "File System",
        "MediaAgentName": "bbcs7_2",
        "ClientName" : "mmdedup35",
        "linux_ddb_path": "/mat36MP1/automationDDBs"
}

    *linux_ddb_path is only necessary for a linux mediaagent

Design Steps:
-cleanup - remove disablephase3pruning reg key if it exists
-disable RWP, create entities
-confirm distributor partition and save its substoreid and ddbpath and ma name
-run 2 backups, create source content each time
-disable phase 3 pruning using reg key on datamover mediaagent
-delete latest backup job, confirm entries got added to mmdeletedaf, increase pruning interval frequency, run data aging
-confirm phase 2 pruning finishes
-add reg key to immediately trigger MS
-run backup to trigger MS
-remove reg key
-confirm zeroref buildup on all partitions
-rename distributor partition so it goes offline
-first, save id and path of partition we're going to rename, to be used later when we need to rename back
-second, wait for any sidb2 pids to go down for the 0 partiiton
-third, rename distributor partition path by appending _renamed to it
-wait for up to an hour, looping every 5 mins to confirm if distributor has changed
-here, ddb partition path will eventually automatically get marked offline, and soon after that, distributor will change
-re-enable phase 3 pruning
-confirm that we drain zeroref successfully for the 3 online partitions,
and keep the same zeroref count for the offline partition
-tear_down


"""
import time
from AutomationUtils import constants
from AutomationUtils import config
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "phase 3 pruning when group 0 is offline"
        self.tcinputs = {
            "MediaAgentName": None,
        }

        self.mm_helper = None
        self.dedupe_helper = None
        self.optionobj = None
        self.backupset_obj = None
        self.sp_copy_obj = None
        self.storage_pool = None
        self.subclient_obj = None
        self.store_obj = None
        self.client_machineobj = None
        self.ma_machineobj = None
        self.mediaagentname = None
        self.mountpath = None
        self.storage_pool_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.client_system_drive = None
        self.ma_system_drive = None
        self.partition_paths = None
        self.linux_ddb_path = None
        self.is_user_defined_dedup = False
        self.distributor_partition = None
        self.distributor_substore_path = None
        self.distributor_substore_ma = None
        self.renamed_substore = None
        self.renamed_path = None
        self.dedup_path_base = None
        self.sqluser = None
        self.sqlpassword = None
        self.sidb_id = None
        self.substore_list = None
        self.backup_jobs_list = None
        self.result_string = ""
        self.plan = None
        self.plan_name = None
        self.ma_client = None

    def setup(self):
        """Setup function of this test case"""

        self.optionobj = OptionsSelector(self.commcell)
        self.mm_helper = mahelper.MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        self.mediaagentname = self.tcinputs["MediaAgentName"]
        self.client_machineobj = Machine(self.client)
        self.ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
        self.client_system_drive = self.optionobj.get_drive(self.client_machineobj, 25*1024)
        self.ma_machineobj = Machine(self.mediaagentname, self.commcell)
        self.ma_system_drive = self.optionobj.get_drive(self.ma_machineobj, 25*1024)
        suffix = str(self.mediaagentname) + "_" + str(self.client.client_name)

        if self.tcinputs.get('linux_ddb_path'):
            self.is_user_defined_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.ma_machineobj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for a linux MA!")
            raise Exception("LVM enabled dedup path not supplied for a linux MA!")
        if self.is_user_defined_dedup:
            self.dedup_path_base = self.ma_machineobj.join_path(self.tcinputs["linux_ddb_path"],
                                                                f'tc_{self.id}_{suffix}')
        else:
            self.dedup_path_base = self.ma_machineobj.join_path(self.ma_system_drive, "DDBs", f'tc_{self.id}_{suffix}')
        self.partition_paths = []
        self.partition_paths.append(self.ma_machineobj.join_path(self.dedup_path_base, "partition_0"))
        self.storage_pool_name = f'{str(self.id)}_POOL_{suffix}'
        self.plan_name = f'{str(self.id)}_PLAN_{suffix}'
        self.backupset_name = f'{str(self.id)}_BS_{suffix}'
        self.subclient_name = f'{str(self.id)}_SC_{suffix}'
        self.content_path = self.client_machineobj.join_path(self.client_system_drive, f'content_{self.id}')
        self.sqluser = config.get_config().SQL.Username
        self.sqlpassword = config.get_config().SQL.Password

        # Create mountpath
        self.mountpath = self.ma_machineobj.join_path(self.ma_system_drive, self.id, "mountpath")

    def allocate_resources(self):
        """create the resources needed before starting backups"""

        # disable ransomware protection so ddb path can be renamed later
        if self.ma_machineobj.os_info.lower() == 'windows':
            self.log.info('Disabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(False)
            self.log.info("Successfully disabled Ransomware protection on MA")

        # create Storage Pool
        self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mountpath,
                                                            self.mediaagentname, self.mediaagentname,
                                                            self.partition_paths[0])
        self.log.info(f'---Successfully configured Storage Pool - {self.storage_pool_name}')

        # create plan
        self.commcell.storage_pools.refresh()
        self.commcell.plans.refresh()
        self.log.info(f'Creating the plan {self.plan_name}')
        self.commcell.plans.refresh()
        self.plan = self.commcell.plans.add(self.plan_name, "Server", self.storage_pool_name)
        self.log.info(f'Plan {self.plan_name} created')

        # disabling the schedule policy
        self.plan.schedule_policies['data'].disable()

        # get dependent copy object to be referenced later
        self.sp_copy_obj = self.plan.storage_policy.get_copy("Primary")

        # adding second, third, and fourth partitions to the ddb store
        self.get_active_files_store()
        for partition in range(1, 4):
            self.partition_paths.append(self.ma_machineobj.join_path(self.dedup_path_base, f'partition_{partition}'))
            self.store_obj.add_partition(self.partition_paths[partition], self.mediaagentname)
            self.log.info(f'---Successfully added partition {partition}')
        self.log.info("---Successfully added second, third, and fourth partitions to the ddb---")

        # create store and substore objects to be used later
        self.commcell.deduplication_engines.refresh()
        self.store_obj.refresh()
        self.sidb_id = self.store_obj.store_id
        self.substore_list = []
        for substores in self.store_obj.all_substores:
            self.substore_list.append(substores[0])

        # Configure backup set and subclients
        self.log.info("---Configuring backup set---")
        self.backupset_obj = self.mm_helper.configure_backupset(self.backupset_name)
        if self.client_machineobj.check_directory_exists(self.content_path):
            self.client_machineobj.remove_directory(self.content_path)
        self.client_machineobj.create_directory(self.content_path)

        # create subclient
        self.log.info("---Configuring subclient object---")
        self.subclient_obj = self.backupset_obj.subclients.add(self.subclient_name)

        # add plan to the subclient
        self.log.info("adding plan to subclient")
        self.subclient_obj.plan = [self.plan, [self.content_path]]

        self.backup_jobs_list = []

    def deallocate_resources(self):
        """
        removes all resources allocated by the Testcase
        """

        # remove additional setting that disables phase 3 pruning if its present from previous run
        self.toggle_phase_3_pruning(add_key=False)

        if self.client_machineobj.check_directory_exists(self.content_path):
            self.client_machineobj.remove_directory(self.content_path)
            self.log.info("content_path deleted")
        else:
            self.log.info("content_path does not exist.")

        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.backupset_obj = self.agent.backupsets.get(self.backupset_name)
            if self.backupset_obj.subclients.has_subclient(self.subclient_name):
                self.subclient_obj = self.backupset_obj.subclients.get(self.subclient_name)
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
        self.commcell.disk_libraries.refresh()

        self.log.info("clean up successful")

    def get_active_files_store(self):
        """returns active store object for files iDA"""

        self.commcell.deduplication_engines.refresh()
        dedup_engines_obj = self.commcell.deduplication_engines
        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])

    def run_backup_job(self, num_backups=1, backuptype="Full"):
        """
        create source content data and run a backup job on subclient
        Args:
            num_backups (int) -- how many backup iterations to run
            backuptype (str) -- Backup type , Incremental by default.
        """

        for bkps in range(1, num_backups+1):
            self.log.info("---Creating uncompressable unique data---")
            self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 0.5)
            time.sleep(30)
            self.log.info(f'Starting backup iteration - [{bkps}]')
            job = self.subclient_obj.backup(backuptype)
            self.backup_jobs_list.append(job)
            if not job.wait_for_completion():
                raise Exception(f'Failed to run {backuptype} backup with error: {job.delay_reason}')
            self.log.info(f'Backup job [{job.job_id}] completed')
            # prevents problem where jobs overlap and next job fails to start
            time.sleep(5)
        self.store_obj.refresh()

    def identify_distributor(self, engine_id):
        """
        identifies the partition that has the distributor bit set

        args:
            engine_id (int) - store id
        returns:
            partition_id (int) - substore id

        """

        self.log.info(f'fetching current distributor partition for store id {engine_id}')
        query = f'select substoreid from idxsidbsubstore where extendedflags&32=32 and sidbstoreid  = {engine_id}'
        self.log.info(f'Query => {query}')
        self.csdb.execute(query)
        if len(self.csdb.fetch_all_rows()) > 1:
            raise Exception(f'store {engine_id} has multiple chunk distributor partitions set')
        elif self.csdb.fetch_all_rows()[0][0] == '':
            raise Exception(f'store {engine_id} has no chunk distributor set')
        else:
            self.distributor_partition = int(self.csdb.fetch_all_rows()[0][0])
        self.log.info(f'current distributor partition is {self.distributor_partition} for store id {engine_id}')

        for substore in self.store_obj.all_substores:
            if substore[0] == self.distributor_partition:
                self.distributor_substore_path = substore[1]
                self.distributor_substore_ma = substore[2]

    def run_ms(self):
        """
        add reg key, run a backup that immediately triggers MS, remove reg key
        """

        # temporarily set pruning interval back to 60 and wait for any existing sidb2 process
        # to come down
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)
        self.log.info("check if sidb process is running, and wait for it to come down")
        if not self.dedupe_helper.wait_till_sidb_down(str(self.sidb_id), self.commcell.clients.get(
                self.tcinputs.get("MediaAgentName"))):
            raise Exception("sidb process did not come down in 10 minutes, cleanup failed")
        else:
            self.log.info(f'sidb process is down for store {self.sidb_id}')

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
        while not ms_ran and iterations < 3:
            self.log.info("running new backup just to trigger MS to run immediately")
            self.run_backup_job()
            self.csdb.execute(query)
            second_ms_run_time = self.csdb.fetch_all_rows()
            self.log.info(f"QUERY OUTPUT : {second_ms_run_time}")
            if int(second_ms_run_time[0][1]) > int(first_ms_run_time[0][1]) and \
                    int(second_ms_run_time[1][1]) > int(first_ms_run_time[1][1]) and \
                    int(second_ms_run_time[2][1]) > int(first_ms_run_time[2][1]) and \
                    int(second_ms_run_time[3][1]) > int(first_ms_run_time[3][1]):
                self.log.info(f"confirmed MS ran on all substores of store {self.store_obj.store_id}")
                ms_ran = True
            else:
                self.log.info(f"iteration {iterations}: MS didnt run yet on all substores, "
                              f"so run another backup to induce it")
                iterations += 1
        if not ms_ran:
            self.log.error(f"MS never ran on both substores of store {self.store_obj.store_id}")
            raise Exception(f"MS never ran on both substores of store {self.store_obj.store_id}")

        # remove reg key that runs Mark and Sweep immediately
        self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting")
        self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

        # set pruning interval back to 2 minutes to allow phase 3 pruning to run quickly
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)

    def rename_partition(self):
        """
        rename distributor partition so it goes offline
        """

        self.log.info("set prune interval to 60 mins and sleeping 10 mins"
                      "to allow no chance for pruning requests to run before renaming partition")
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)
        time.sleep(600)

        self.log.info("check if sidb process is running, and wait for it to come down")
        if not self.dedupe_helper.wait_till_sidb_down(
                str(self.sidb_id), self.commcell.clients.get(self.distributor_substore_ma),
                self.distributor_partition):
            raise Exception("sidb process did not come down in 10 minutes, fail the case")
        else:
            self.log.info(f'sidb process is down for store {self.sidb_id}')

        self.log.info(f'renaming partition {self.distributor_partition} path {self.distributor_substore_path}')
        if not self.ma_machineobj.rename_file_or_folder(self.distributor_substore_path,
                                                        f'{self.distributor_substore_path}_renamed'):
            raise Exception(f'could not rename the ddb path {self.distributor_substore_path}, failing the case')
        else:
            self.renamed_substore = self.distributor_partition
            self.renamed_path = self.distributor_substore_path
            self.log.info("ddb path successfully renamed")
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        self.log.info("set prune process interval back to 2 min")

    def prune_job(self, job, engine_id):
        """
        deletes job, confirms entries got added to mmdeletdaf, and runs data aging

        args:
            job(obj) - job object to delete
            engine_id(int) - store id
        """

        self.log.info(f'Deleting backup job [{job.job_id}]')
        self.sp_copy_obj.delete_job(job.job_id)
        if self.logical_pruning_empty('mmdeletedaf', engine_id):
            for tries in range(1, 4):
                self.log.info(f'entries didnt get added to mmdelaf yet after try {tries} of 4, wait and check again')
                time.sleep(10)
        else:
            self.log.info("confirmed entries added to mmdeletedaf, as expected")
            self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
            data_aging_job = self.mm_helper.submit_data_aging_job(
                copy_name='Primary',
                storage_policy_name=self.plan.storage_policy.storage_policy_name,
                is_granular=True, include_all=False,
                include_all_clients=True,
                select_copies=True, prune_selected_copies=True)
            self.log.info(f'data aging job: {data_aging_job.job_id}')
            if not data_aging_job.wait_for_completion():
                self.log.info(f'Failed to run data aging with error: {data_aging_job.delay_reason}')

    def logical_pruning_empty(self, table, engine_id):
        """
        for given table, return true if the query returns nothing, otherwise false.

        args:
            table(string) - table to run the query on
            engine_id(int) - store id
        return:
            num_rows == 0 (bool) - returns true if query output is 0, otherwise returns false
        """

        self.log.info(f'fetching current afid count in {table} for store id {engine_id}')
        query = f'select count(distinct archfileid) from {table} where sidbstoreid  = {engine_id}'
        self.log.info(f'Query => {query}')
        self.csdb.execute(query)
        num_rows = int(self.csdb.fetch_one_row()[0])
        self.log.info(f'Current afid count in {table} for store id {engine_id} is {num_rows}')
        return num_rows == 0

    def toggle_phase_3_pruning(self, add_key):
        """
        either enables or disables phase 3 pruning on mediaagent

        args:
            add_key (bool) - True to add the key and disable phase 3 pruning,
            False to delete the key and allow phase 3 pruning
        """

        # add reg key to disable phase 3 pruning
        if add_key:
            self.log.info("setting DedupPrunerDisablePhase3 additional setting to 1")
            self.ma_client.add_additional_setting("MediaAgent", "DedupPrunerDisablePhase3", "INTEGER", "1")
        else:
            self.log.info("removing DedupPrunerDisablePhase3 regkey")
            self.ma_client.delete_additional_setting("MediaAgent", "DedupPrunerDisablePhase3")

    def get_zeroref_count_for_substore(self, substorelist):
        """
        Get latest pending delete count for one substore of ddb store as present in idxsidbusagehistory table
        Args:
            substorelist (list of ints) - list of substoreids

        Return:
            zeroref_count (list) -- A list of strings representing the latest pending delete count for each substore
        """
        substore_str = ','.join(map(str, substorelist))
        query = f"""select substoreid, zerorefcount from (select *, row_number() over (partition by substoreid 
                    order by modifiedtime desc) as rn from idxsidbusagehistory where historytype=0) USG 
                    where rn = 1 and substoreid in ({substore_str})"""
        self.log.info(f'QUERY: {query}')
        self.csdb.execute(query)
        zeroref_count = self.csdb.fetch_all_rows()
        self.log.info(f'QUERY OUTPUT : {zeroref_count}')
        return zeroref_count

    def zeroref_drain(self, substorelist, confirming_zeroref_drain):
        """
        check if zerorefcount in idxsidbusagehistory has drained or not

        args:
            substorelist (list) -- list of substoreid ints
            confirming_zeroref_drain (bool) -- False is to check that zeroref is built up,
            True is to check that it has drained

        return:
            zeroref_list(list) -- list that contains a bool, int and int of substore zeroref counts
        """
        zeroref_complete = False
        zeroref_iterations = 0
        if confirming_zeroref_drain:
            while not zeroref_complete and zeroref_iterations < 10:
                sublist_zeroref = self.get_zeroref_count_for_substore(substorelist)
                if all(int(zref[1]) == 0 for zref in sublist_zeroref):
                    zeroref_complete = True
                else:
                    zeroref_iterations += 1
                    self.log.info(f'iteration {zeroref_iterations} of 10 - '
                                  f'sleeping for 300 secs to give zeroref more time to be deleted')
                    time.sleep(300)
        else:
            while not zeroref_complete and zeroref_iterations < 5:
                sublist_zeroref = self.get_zeroref_count_for_substore(substorelist)
                if all(int(zref[1]) != 0 for zref in sublist_zeroref):
                    zeroref_complete = True
                else:
                    zeroref_iterations += 1
                    self.log.info(f'iteration {zeroref_iterations} of 5 - '
                                  f'sleeping for 300 secs to give zeroref more time to build up')
                    time.sleep(300)
        zeroref_list = [zeroref_complete, sublist_zeroref]
        return zeroref_list

    def confirm_distributor_change(self):
        """
        confirms the partition marked as the distributor has changed
        args:
            (none)
        returns:
            boolean
        """

        distributor_change = False
        iterations = 0
        current_distributor_partition = self.distributor_partition
        while not distributor_change and iterations != 13:
            self.identify_distributor(self.sidb_id)
            if current_distributor_partition == self.distributor_partition:
                self.log.info(f"iteration {iterations} of 13: distributor has not changed yet, sleeping 300 seconds")
                time.sleep(300)
                iterations += 1
            else:
                distributor_change = True
        return iterations != 13

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info("cleaning up previous run")
            self.deallocate_resources()

            self.log.info("TC environment configuration started")
            self.allocate_resources()
            self.log.info("----------TC environment configuration completed----------")

            # confirm which partition is the chunk distributor
            self.identify_distributor(self.sidb_id)

            # add reg key to disable phase 3 pruning
            self.toggle_phase_3_pruning(add_key=True)

            # run 2 backups
            self.run_backup_job(2)
            time.sleep(90)

            # Delete latest backup job and run data aging
            self.prune_job(self.backup_jobs_list[-1], self.sidb_id)

            # confirm phase 2 pruning is finished
            iterations = 0
            while (not self.logical_pruning_empty('mmdeletedaf', self.store_obj.store_id) or
                   not self.logical_pruning_empty('mmdeletedarchfiletracking', self.store_obj.store_id)) and \
                    iterations < 4:
                self.log.info(f'iteration {iterations} of 3: {self.store_obj.store_id} still has entries in '
                              f'mmdel tables, wait 5 minutes and try again')
                iterations += 1
                time.sleep(300)
            if iterations >= 4:
                self.log.error(f'FAILURE: phase2 pruning didnt finish for store {self.store_obj.store_id}')
                raise Exception("TC FAILED, phase2 pruning didnt finish")
            else:
                self.log.info(f'phase2 pruning finished successfully for store {self.store_obj.store_id}')

            # run MS after logical pruning so zeroref entries can be created
            self.run_ms()

            # confirm that we have positive zeroref buildup in all partitions
            positive_zeroref_buildup_list = self.zeroref_drain(self.substore_list, confirming_zeroref_drain=False)
            if not positive_zeroref_buildup_list[0]:
                raise Exception(f'zeroref buildup did not occur on store {self.sidb_id}')
            else:
                for sub in positive_zeroref_buildup_list[1]:
                    self.log.info(f'substore {sub[0]} zeroref {sub[1]}')

            # rename distributor partition so it goes offline
            self.rename_partition()

            # confirm that distributor changes to an online partition within an hour
            if not self.confirm_distributor_change():
                raise Exception(f'distributor did not change after 1 hour')
            else:
                self.log.info(f'confirmed new distributor substoreid {self.distributor_partition}')

            # re-enable phase 3 pruning by disabling additional setting
            self.toggle_phase_3_pruning(add_key=False)

            # confirm zeroref drains now for all partitions but the one that is renamed and offline
            zeroref_drain_list = self.zeroref_drain(self.substore_list, confirming_zeroref_drain=True)
            for sub in zeroref_drain_list[1]:
                if int(sub[0]) != self.renamed_substore:
                    if int(sub[1]) != 0:
                        raise Exception(f'online substore {sub[0]} still has zeroref of {sub[1]}')
                    else:
                        self.log.info(f'oneline substore {sub[0]} drained its zeroref as expected')
                else:
                    if int(sub[1]) == 0:
                        raise Exception(f'offline substore {sub[0]} drained its zeroref, unexpected!')
                    else:
                        self.log.info(f'offline substore {sub[0]} still has zeroref, as expected')
            self.log.info("TC PASSES")

        except Exception as exp:
            self.log.error(f'Failed to execute test case with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("In tear down method ...")

        # remove reg key that disables phase 3 pruning
        self.toggle_phase_3_pruning(add_key=False)

        # remove reg key that runs Mark and Sweep in case it was left by case failing
        self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting")
        self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

        # re-enable partition
        self.log.info("check if sidb process is running, and wait for it to come down")
        if not self.dedupe_helper.wait_till_sidb_down(str(self.sidb_id), self.commcell.clients.get(
                self.tcinputs.get("MediaAgentName")), self.distributor_partition):
            raise Exception("sidb process did not come down in 10 minutes, cleanup failed")
        else:
            self.log.info(f'sidb process is down for store {self.sidb_id}')

        self.log.info(f'renaming partition {self.renamed_substore} path {self.renamed_path}')
        if not self.ma_machineobj.rename_file_or_folder(f'{self.renamed_path}_renamed',
                                                        self.renamed_path):
            raise Exception(f'could not rename the ddb path {self.renamed_path}, cleanup failed')
        else:
            self.log.info("ddb path successfully renamed")

        # set prune process interval back to default
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)

        if self.ma_machineobj.os_info.lower() == 'windows':
            self.log.info('Enabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)
            self.log.info("Successfully enabled Ransomware protection on MA")

        # re-associate SP
        if self.commcell.storage_policies.has_policy(self.plan.storage_policy.storage_policy_name):
            self.log.info(f'reassociating storage policy {self.plan.storage_policy.storage_policy_name} '
                          f'in case it is associated to ddbbackup')
            self.plan.storage_policy.reassociate_all_subclients()

        self.log.info("Performing unconditional cleanup")
        self.deallocate_resources()
