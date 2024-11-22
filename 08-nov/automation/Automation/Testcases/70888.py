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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    previous_run_cleanup() -- for deleting the left over backupset and storage pool,plan from the previous run

    run_backup_job() -- for running a backup job of given type

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    get_table_row_count()  -- get total count of rows from a table

    wait_for_pruning()      --wait till mmdeletedaf and mmdeletedarchfiletracking table is 0 for a store

    get_latest_pri_sec_count(): function returns latest primary or secondary count from the idxsidbusagehistory table.

    update_store_creationtime()   -- function will update the store creation time to one day old

    check_pri_sec_count()    -- checks if pri count >0 and sec count =0 for the substore from idxsidbusagehistory table

    get_last_MS_runtime()    --  function finds when the last MS was run for a substore  from mmentityprop table.

    update_last_MS_runtime()  --   function checks last run time and updates its to one day old.

    validate_MS_run()       --  function validates in MM triggered MS or not

    validate_pruning_and_MSRun()  -- function waits for pruning to happen for the store and validates MS was triggered
                                    by MM after pruning was done

    update_primary_count()  --   function will update the primary count to exceed the config difference


    Prerequisites: None

Input format:
    "70888" : {
            "ClientName": "Name of the client",
            "AgentName":  "Type of Agent",
            "MediaAgentName": "Name of MediaAgent",
            "mount_path": "path where the data is to be stored",
            "dedup_path": "path where dedup store to be created"
             }

    [for linux MediaAgents, User must explicitly provide a dedup path that is inside a Logical Volume.
    (LVM support required for DDB)]

            note --
                    ***********************************
                    if mountpath_location_given -> create_library_with_this_mountpath
                        else:
                            auto_generate_mountpath_location
                            create_library_with_this_mountpath

                    if dedup_path_given -> use_given_dedup_path
                    else it will auto_generate_dedup_path
                    ***********************************
Design steps:
1. create resources and generate data
Case1: sec count =0 and pri count >0 and dependent copy exits
2) run a backup job
3) delete the job and wait for phase2 pruning to happen
4) check the sec count should be 0 and pri count > 0
4)	Check when the last MS runtime and update it to 1 day before

Select dbo.getdatettime(longlongval),* from mmentityprop where propertyname like ‘%DDBMSRuntime%’ and entityid = <substoreid >
5) store the time after update and make sure this gets updated after MS is triggered from MM
(since default MS interval is 24 hours and DDB is not being launched we can rely on lastMSruntime for validation)

case2 : when the difference between pri and sec count is as per config param 'MMCONFIG_DEDUP_MAX_ALLOWED_PRIMAY_SECONDARY_DIFFERENCE'
6) run backup
7) update config param value to 10000
8) get sec count and update pri count =sec count + config param value
9) update MS run time and store is
10) make sure now MS time gets updated which means MM triggered MS

case3: pri count >0 and plan is deleted
11)remove plan association
12)	Delete the plan
13) Run DA couple of times. Make sure pri > 0 and sec =0
14)	Check if MS is triggered by MM by checking MS run time is updated.
15). Remove the resources created for this testcase.
"""

import time
from cvpysdk import (storage, deduplication_engines)
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils import mahelper
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from AutomationUtils import commonutils


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MM triggering MS on certain conditions"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.restore_path = None
        self.library_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.testcase_path = None
        self.client_machine = None
        self.media_agent_machine = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.backup_set = None
        self.subclient_ob = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.plan_name = None
        self.plan_ob = None
        self.storage_pool_name = None
        self.agent = None
        self.storage_assigned_ob = None
        self.plan_type = None
        self.store_obj = None
        self.dedup_path_1 = None
        self.sql_password = None
        self.substore_id = None
        self.substore_id_1 = None
        self.error_flag = []


    def setup(self):
        """Setup function of this test case"""

        self.sql_password = commonutils.get_cvadmin_password(self.commcell)
        suffix = str(self.tcinputs["MediaAgentName"]) + str(self.tcinputs["ClientName"])
        self.plan_name = "plan" + str(self.id) + str(suffix)
        self.storage_pool_name = "pool" + str(self.id) + suffix
        self.plan_type = "Server"
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.library_name = "{0}_lib{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client)
        self.media_agent_machine = Machine(
            self.tcinputs["MediaAgentName"], self.commcell)

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        # create the required resources for the testcase
        # get the drive path with required free space

        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)

        self.testcase_path_media_agent = f"{drive_path_media_agent}{self.id}"
        # creating testcase directory, mount path, content path, dedup
        # store path

        self.testcase_path_client = f"{drive_path_client}{self.id}"

        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        self.restore_path = self.client_machine.join_path(
            self.testcase_path_client, "restore_path")
        if self.client_machine.check_directory_exists(self.restore_path):
            self.log.info("restore path directory already exists")
            self.client_machine.remove_directory(self.restore_path)
            self.log.info("existing restore path deleted")
        self.client_machine.create_directory(self.restore_path)
        self.log.info("restore path created")

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mount_path = self.media_agent_machine.join_path(self.tcinputs["mount_path"], self.id)
        else:

            self.mount_path = self.media_agent_machine.join_path(self.testcase_path_media_agent, "mount_path")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id ,
                                                                       "DedupDDB1")
            self.dedup_path_1 = self.media_agent_machine.join_path(self.tcinputs.get('dedup_path'),
                                                                   str(self.id),"DedupDDB2")

        else:
            self.dedup_store_path = self.media_agent_machine.join_path(self.testcase_path_media_agent,
                                                                       str(self.id),"DedupDDB1")
            self.dedup_path_1 = self.media_agent_machine.join_path(self.testcase_path_media_agent,
                                                                   str(self.id), "DedupDDB2")



    def create_resources(self):
        # create the required resources for the testcase
        #  create storage pool
        self.log.info(f"creating storage pool [{self.storage_pool_name}]")
        self.storage_assigned_ob = self.commcell.storage_pools.add(storage_pool_name=self.storage_pool_name,
                                                                   mountpath=self.mount_path,
                                                                   media_agent=self.tcinputs['MediaAgentName'],
                                                                   ddb_ma=self.tcinputs['MediaAgentName'],
                                                                   dedup_path=self.dedup_store_path)
        self.log.info(f"storage pool [{self.storage_pool_name}] created")

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
        self.store_obj.refresh()

        self.substore_id = self.store_obj.all_substores[0][0]
        self.log.info("Substoreid is .. [%s] ", self.substore_id)


        self.substore_id_1 = self.store_obj.all_substores[1][0]
        self.log.info("Substoreid is .. [%s] ", self.substore_id_1)



        # create plan
        self.log.info(f"creating plan [{self.plan_name}]")
        self.plan_ob = self.commcell.plans.add(plan_name=self.plan_name, plan_sub_type=self.plan_type,
                                               storage_pool_name=self.storage_pool_name)
        self.log.info(f"plan [{self.plan_name}] created")

        # Disabling schedule policy from plan
        self.plan_ob.schedule_policies['data'].disable()

        # create backupset
        self.log.info(f"Creating Backupset [{self.backupset_name}]")
        self.backup_set = self.mm_helper.configure_backupset(
            self.backupset_name, self.agent)
        self.log.info(f"Backupset created [{self.backupset_name}]")

        # generate the content
        if self.mm_helper.create_uncompressable_data(
                self.client.client_name, self.content_path, 0.5, 1):
            self.log.info(
                "generated content for subclient %s", self.subclient_name)


        self.log.info(f"Creating subclient [{self.subclient_name}]")

        # Adding Subclient to Backupset
        self.subclient_ob = self.backup_set.subclients.add(self.subclient_name)
        self.log.info(f"Added subclient to backupset [{self.subclient_name}]")
        self.log.info("Adding plan to subclient")

        # Associating plan and content path to subclient
        self.subclient_ob.plan = [self.plan_ob, [self.content_path]]
        self.log.info("Added content and plan to subclient")


    def previous_run_clean_up(self):
        """deletes items from the previous run of the testcase"""
        self.log.info("********* previous run clean up started **********")
        try:
            # deleting Backupset
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset.")
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Backupset deleted.")


            # deleting Plan
            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Plan exists, deleting that")
                self.commcell.plans.delete(self.plan_name)
                self.log.info("Plan deleted.")


            # deleting storage pool
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(f"pool[{self.storage_pool_name}] exists, deleting that")
                self.commcell.storage_pools.delete(self.storage_pool_name)
                self.log.info("pool primary deleted.")

            self.log.info("********* previous run clean up ended **********")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)


    def run_backup_job(self, job_type):
        """running a backup job depending on argument
            job_type       (str)           type of backjob job
                                            (FULL, Synthetic_full)
        """
        self.log.info("Starting backup job")
        job = self.subclient_ob.backup(job_type)
        self.log.info(f"Backup job: {job.job_id}")
        self.log.info(f"job type is {job_type}")

        if not job.wait_for_completion():
            raise Exception(
                "Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))

        self.log.info(f"job { job.job_id} completed")
        return job

    def update_store_creationtime(self):
        """
                    This function will update the store creation time to one day old

        """
        self.log.info("---Updating store creation time to one day old---")
        query = f"""UPDATE IdxSIDbstore
                      SET CreatedTime =CreatedTime -86400 
                      WHERE SIDBStoreId = {self.store_obj.store_id}"""

        self.log.info(query)
        self.opt_selector.update_commserve_db(query)



    def get_table_row_count(self):

        """ Get distinct AF count for the given table

            Returns:
                (int) - total number of rows
        """
        query = f"select count(*) from mmdeletedaf where sidbstoreid  = {self.store_obj.store_id} "
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        num_rows_mmdel = int(self.csdb.fetch_one_row()[0])
        self.log.info("number of mmdeletedaf rows ==> %s", num_rows_mmdel)
        query = f"select count(*) from mmdeletedarchfiletracking where sidbstoreid  = {self.store_obj.store_id} "
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        num_rows_tracking = int(self.csdb.fetch_one_row()[0])
        self.log.info("number of mmdeletedarchfiletracking rows ==> %s", num_rows_tracking)
        total_count = num_rows_mmdel + num_rows_tracking
        return total_count

    def wait_for_pruning(self, plan_ob):
        """
        wait till mmdeletedaf and mmdeletedarchfiletracking table is 0 for a store
        args: plan_ob :(obj) instance of plan created
        """
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 60, 60)

        # Running data aging job

        aging_job = self.mm_helper.submit_data_aging_job(
            copy_name='Primary',
            storage_policy_name=self.plan_ob.storage_policy.storage_policy_name,
            is_granular=True,
            include_all_clients=True)

        self.log.info(f"Data aging job {aging_job.job_id}")

        if not aging_job.wait_for_completion():
            if aging_job.status.lower() == "completed":
                self.log.info(f"Job {aging_job.job_id} completed")
            else:
                raise Exception(f"Job {aging_job.job_id} failed with { aging_job.delay_reason}")

        totalcount = self.get_table_row_count()

        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        pruning_done = False
        for i in range(10):
            aging_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                              storage_policy_name=plan_ob.storage_policy.storage_policy_name,
                                                              is_granular=True, include_all_clients=True)

            self.log.info(f"Data aging job {aging_job.job_id}")

            if not aging_job.wait_for_completion():
                if aging_job.status.lower() == "completed":
                    self.log.info(f"Job {aging_job.job_id} completed")
                else:
                    raise Exception(f"Job {aging_job.job_id} failed with {aging_job.delay_reason}")

            time.sleep(180)

            totalcount = self.get_table_row_count()
            if totalcount == 0:
                pruning_done = True
                self.log.info("Pruning is done")
                return pruning_done

        return pruning_done

    def get_latest_pri_sec_count(self, value):
        """
        This function returns latest primary or secondary count from the idxsidbusagehistory table.
        param value:
                value (str) = "primary" or "secondary"
        return:
                count (int) : primary or the secondary count
        """

        table_entries = None

        if value.lower() == "primary":
            table_entries = "PrimaryEntries"
        elif value.lower() == "secondary":
            table_entries = "SecondaryEntries"
        else:
            raise Exception(
                f"Error: incorrect string value passed to function get_latest_pri_sec_count-- {table_entries}")

        query = f"""
          select * from (SELECT TOP 1 substoreid ,{table_entries} FROM IdxSIDBUsageHistory 
            WHERE SubStoreId= {self.substore_id} 
            ORDER BY ModifiedTime DESC) as subquery1
            
            UNION ALL

          select * from (SELECT TOP 1 substoreid ,{table_entries} FROM IdxSIDBUsageHistory 
           WHERE  SubStoreId= {self.substore_id_1} 
           ORDER BY ModifiedTime DESC) as subquery2
        
        """
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        count = self.csdb.fetch_all_rows()
        self.log.info(f"substoreid and Count is : {count}")
        return count

    def check_pri_sec_count(self):
        """
        checks if pri count >0 and sec count =0
        returns:  (Str) True : if primary count > 0 and secondary count =0 for a substore.

        """

        sec_count = self.get_latest_pri_sec_count("secondary")
        if int(sec_count[0][1]) == 0 and int(sec_count[1][1]) == 0:
            pri_count = self.get_latest_pri_sec_count("primary")
            if int(pri_count[0][1]) > 0 and int(pri_count[1][1]) > 0:
                self.log.info("Pri count is > 0 and sec count is 0 ")
                return True
            else:
                self.error_flag += ["Exception Primary count is not greater 0 "]
                return False

        else:
            self.error_flag += ["Exception Secondary count is NOT equal to 0 "]
            return False


    def get_last_MS_runtime(self):

        """
        method finds when the last MS was run for a substore  from mmentityprop table.
        retuns : (int)   time when last MS run

        """

        query = f"""Select entityid,longlongval from mmentityprop
                                where propertyname like '%DDBMSRuntime%' 
                                and entityid in ({self.substore_id}, {self.substore_id_1})"""

        self.log.info(query)
        self.csdb.execute(query)
        LastMSRuntime=self.csdb.fetch_all_rows()
        self.log.info(f"Last MS run time is {LastMSRuntime}")
        return LastMSRuntime


    def update_last_MS_runtime(self):
        """
            this function checks last run time and updates its to one day old.
            retuns :
                (int)  last updated time of MS
        """

        LastMSRuntime = self.get_last_MS_runtime()
        self.log.info("Last MS run time before update is ==> %s", LastMSRuntime)
        if int(LastMSRuntime[0][1]) > 0 and int(LastMSRuntime[1][1]) > 0:
            query = f"""update mmentityprop
            set longlongVal = longlongVal - 86400
            where propertyname like 'DDBMSRunTime' 
            and entityid in ({self.substore_id},{self.substore_id_1})"""

            self.log.info(query)
            self.opt_selector.update_commserve_db(query)
            LastMSRuntime = self.get_last_MS_runtime()
            self.log.info(f"Last MS run time after update is ==> {LastMSRuntime}")
            return LastMSRuntime

        else:
            raise Exception(f"DDMSRuntime property is either not created or is 0.. {LastMSRuntime}")


    def validate_MS_run(self,lastruntime):
        """
        function validates in MM triggered MS or not
        args:
            (int) the last run time in mmentityprop beforeMM triggering MS
        return:
            (str) true : if MS was triggered by MM else false
        """

        for i in range(10):
            self.log.info(f"Attempt number :: {i}")
            latestruntime = self.get_last_MS_runtime()
            self.log.info(f"Latest run time is : {latestruntime} and previous runtime is {lastruntime}")

            if int(latestruntime[0][1]) > int(lastruntime[0][1]) and int(latestruntime[1][1]) > int(lastruntime[1][1]) :
                self.log.info(f"MS request triggered by MM as expected")
                return True
            else:
                self.log.info(f"MS request has not been triggered by MM  :Attempt [{i}] ")
            time.sleep(180)

        self.log.info("MS request was not triggered by MM even after checking for 10 attempts..ERROR Please check.")
        return False


    def validate_pruning_and_MSRun(self):
        """
         function waits for pruning to happen for the store and validates MS was triggered by MM after pruning was done

         return:
            (str) true : if MS was triggered by MM else false
        """
        pruning_done = self.wait_for_pruning(self.plan_ob)
        self.store_obj.refresh()
        if pruning_done:
            self.store_obj.refresh()
            result = self.check_pri_sec_count()
            if result:
                lastruntime=self.update_last_MS_runtime()
                res = self.validate_MS_run(lastruntime)
                return res
            else:
                self.log.info("Sec count is not zero yet.Cannot validate futher.")
        else:

            self.error_flag += [" Phase2 Pruning Failed, Raising Exception -- Phase2 Pruning is not over even after "
                                "10 attempts"]

        return False


    def update_primary_count(self):
        """
                    this function will update the primary count to exceed the config difference

        """

        result= self.get_latest_pri_sec_count("secondary")
        sec_count = int(result[0][1])
        pri_Count = sec_count+11000

        self.log.info("---Updating the primary count to exceed the config difference---")
        query = f"update idxsidbusagehistory set PrimaryEntries = {pri_Count} where substoreid = {self.substore_id}"
        self.log.info(query)
        self.opt_selector.update_commserve_db(query)



    def run(self):
        """Run function of this test case"""
        try:


            self.previous_run_clean_up()
            self.create_resources()
            self.log.info(f"storeid is {self.store_obj.store_id}")
            self.update_store_creationtime()



            #Case 1: When primary count >0 and sec count =0 ,dependent SP to pool still exists

            # Run FULL backup

            self.log.info("----Case 1 : when pricount >0 and sec count =0, dependent SP exists---")
            self.log.info("Running full backup...")

            job = self.run_backup_job("FULL")
            time.sleep(15)
            #Delete the job
            sp_copy_obj = self.plan_ob.storage_policy.get_copy("Primary")
            sp_copy_obj.delete_job(job.job_id)
            self.log.info("Deleted job from %s with job id %s", self.plan_ob.storage_policy.storage_policy_name,
                               job.job_id)

            result=self.validate_pruning_and_MSRun()
            if result:
                self.log.info("Case1 : PASSED : MM triggering MS when sec count =0")
            else:
                self.error_flag += ["Case 1 : FAILED : MM triggering MS when sec count =0 has failed"]


            #Case 2: when difference in primary and sec count is greater than the config value

            self.log.info("----Case 2: MM triggering MS when difference in primary and sec count is greater than the config value----")
            job = self.run_backup_job("FULL")
            self.log.info("update the config param MMCONFIG_DEDUP_MAX_ALLOWED_PRIMAY_SECONDARY_DIFFERENCE...")
            self.mm_helper.update_mmconfig_param('MMCONFIG_DEDUP_MAX_ALLOWED_PRIMAY_SECONDARY_DIFFERENCE',1000,10000)
            self.update_primary_count()
            lastMSRuntime = self.update_last_MS_runtime()
            result = self.validate_MS_run(lastMSRuntime)
            if result:
                self.log.info("Case 2 : PASSED : MM triggering MS when difference in primary and sec count is greater than the config value has passed")
            else:
                self.error_flag += ["Case 2 : FAILED: MM triggering MS when difference in primary and sec count is greater than the config value has failed"]

            # Case 3 : dependent copies/plan deleted ,still seeing MS run
            self.log.info("-----Case 3 : MM triggering MS when no dependent copies to pool. -------")

            job = self.run_backup_job("FULL")

            #remove plan association from subclient
            self.log.info("Removing subclient association from plan...")
            self.subclient_ob.plan = None

            #Delete plan
            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Plan exists, deleting that")
                self.commcell.plans.delete(self.plan_name)
                self.log.info("Plan deleted.")
            pri_count = self.get_latest_pri_sec_count("primary")
            self.log.info(f"pri count returned is :: {pri_count}")

            if int(pri_count[0][1]) > 0 and int(pri_count[1][1]) > 0 :
                lastruntime = self.update_last_MS_runtime()
                result = self.validate_MS_run(lastruntime)
                if result:
                    self.log.info("Case 3: PASSED : MM triggering MS when no dependent copies are present passed")
                else:
                    self.error_flag += ["Case 3:FAILED :MM triggering MS when no dependent copies are present has failed"]
            else:
                self.log.info("primary count is not greater than 0")

            self.log.info(self.error_flag)

        except Exception as exp:
            self.log.error(
                'Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        if self.error_flag:
            self.log.info(self.error_flag)
            self.result_string = str(self.error_flag)
            self.status = constants.FAILED

    def tear_down(self):
        "delete all the resources for this testcase"
        self.log.info("Tear down function of this test case")
        try:

            self.log.info("*********************************************")
            self.log.info("restoring defaults")

            self.log.info("setting default value for config param")
            self.mm_helper.update_mmconfig_param('MMCONFIG_DEDUP_MAX_ALLOWED_PRIMAY_SECONDARY_DIFFERENCE',1000,10000000)


            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            if self.client_machine.check_directory_exists(self.restore_path):
                self.client_machine.remove_directory(self.restore_path)
                self.log.info("Deleted the restored data.")
            else:
                self.log.info("Restore directory does not exist.")

            # run the previous_run_cleanup again to delete the backupset,
            # plan, storage pool after running the case
            self.previous_run_clean_up()
            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)
