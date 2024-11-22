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

    previous_run_cleanup()    --  for deleting the left over
                                  backupset and storage policy
                                  from the previous run

    create_resources()        --  creates library, storage policy, backupset, and subclient, and returns the resources

    get_active_files_store()    -- gets store object

    run_full_backup_job()     --  for running a full backup job

    gather_afs_chunks_vols()        --  for running an initial backup job

    get_cloud_size()          --  for getting volume size of volumes in a cloud library

    modify_subclient_content()       --  remove half of the subclient content before the second backup job

    delete_first_backup()     --  for deleting the first backup job

    get_table_row_count()       -- runs query on table that is passed to it

    verify_phase2_pruning()     -- verifies that phase 2 pruning has finished

    run_ms()                    -- verifies mark and sweep runs before we check phase 3

    run_pruning_validation()  --  verify if the deleted job files have been moved to MMdeletedAF

    run_log_validation()      --  verify if the drill hole occurred for the chunks of the first job

    run_pruning_csdb_validation() --  Check for phase 3 count in idxSidbUsageHistory Table

    run_physical_size_validation() --  check if there is reduction in physical size of the chunks

    run_restore_job(second_backup_contents) --  Running a restore job for the second backup and verifying the files

    run()                           --  run function of this test case

    tear_down()               --  tear down function of this test case

This testcase verifies if cloud library is correctly performing micro pruning operations and drilling holes is working
as expected

input json file arguments required:

        "50883": {
                    "ClientName": "bbcs7_2",
                    "AgentName": "File System",
                    "MediaAgentName": "bbauto1_2",
                    "dedup_path": "/ddb",
                    "CloudMountPath": "suseela",
                    "AccessKeyAuthTypeUsername": "http://<AccessHostIPAddr>//__CVCRED__",
                    "AccessKeyAuthTypeCredentialName": "Pure",
                    "CloudVendorName": "s3 compatible storage"
                }

        dedup_path is an optional parameter and needs to be provided only when Media Agent is Linux.
        CloudMountPath is the bucket
        AccessKeyAuthTypeUsername is the access host ip address, followed by //__CVCRED__
        AccessKeyAuthTypeCredentialName *IMPORTANT* must specify an existing cloud type credential in credential
        manager as AccessKeyAuthTypeCredentialName.  Above example "Pure" is an existing credential on linux7.
        CloudVendorName - refer to mediagentconstants.py for the exact phrase mappings for the storage you want to use


Design Steps:
1.	Create resources
2.	Content: generate 100 directories, each with one 10 MB file that is unique
3.	Subclient level: data reader streams : 1
4.	First backup job , get the sidb id,
    archfiles., chunks -> first backup job
5.	Delete every alternate directory from source content list in UI
6.	Second backup job
7.	Delete first backup job
8.	MMdeleted AF check
9.	Change mm prune process interval to 2 min
10.	MMdeletedArchFileTracking table check
11.	Checks ->  chunks deleted drill hole
    sidbphysicaldeletes.log, phase 3 count 0 idxsidbusagehistory,
    physical size reduction, restore job, md5 hash compare
"""

import time
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper
from MediaAgents import mediaagentconstants


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Cloud Library Pruning with Drill Hole Testcase"

        self.tcinputs = {
            "MediaAgentName": None,
            "CloudMountPath": None,
            "AccessKeyAuthTypeUsername": None,
            "AccessKeyAuthTypeCredentialName": None,
            "CloudVendorName": None
        }

        self.mount_path = None
        self.dedup_store_path = None
        self.restore_path = None
        self.content_path = None
        self.library_name = None
        self.library = None
        self.storage_pool_name = None
        self.storage_pool = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.sidb_id = None
        self.substore_id = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.ddb_basepath = None
        self.backup_set = None
        self.subclient = None
        self.is_user_defined_dedup = False
        self.is_user_defined_lib = False
        self.plan_name = None
        self.plan = None
        self.ma_client = None
        self.store_obj = None
        self.content_folders = None

    def setup(self):
        """sets up the variables to be used in testcase"""

        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        suffix = str(self.tcinputs["MediaAgentName"]) + str(self.tcinputs["ClientName"])[1:]

        self.storage_pool_name = f"{self.id}_POOL_{suffix}"
        self.backupset_name = f"{self.id}_BS_{suffix}"
        self.subclient_name = f"{self.id}_SC_{suffix}"
        self.plan_name = f"{self.id}_PLAN_{suffix}"
        self.client_machine = machine.Machine(self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(self.tcinputs["MediaAgentName"], self.commcell)

        # get the drive path with required free space
        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25 * 1024)
        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25 * 1024)
        self.ddb_basepath = f"{drive_path_media_agent}{self.id}"
        self.testcase_path_client = f"{drive_path_client}{self.id}"
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        self.restore_path = self.client_machine.join_path(self.testcase_path_client, "restore_path")

    def previous_run_clean_up(self):
        """delete previous run items"""
        self.log.info("********* previous run clean up **********")
        try:

            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the old source content.")
            else:
                self.log.info("source content directory does not exist.")

            # delete the restored directory
            if self.client_machine.check_directory_exists(self.restore_path):
                self.client_machine.remove_directory(self.restore_path)
                self.log.info("Deleted the old restored data.")
            else:
                self.log.info("Restore directory does not exist.")

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                if self.backupset.subclients.has_subclient(self.subclient_name):
                    self.subclient = self.backupset.subclients.get(self.subclient_name)
                    self.log.info(f'disassociating any plans from subclient {self.subclient_name}')
                    self.subclient.plan = None
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info(f'deleted backupset {self.backupset_name}')
            if self.commcell.plans.has_plan(self.plan_name):
                self.commcell.plans.delete(self.plan_name)
                self.log.info(f'deleted plan {self.plan_name}')
            if not self.is_user_defined_lib:
                if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                    self.commcell.storage_pools.delete(self.storage_pool_name)
                    self.log.info(f"Successfully deleted the pool - {self.storage_pool_name}.")
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def create_resources(self):
        """
            create resources for testcase

        """

        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        if self.client_machine.check_directory_exists(self.restore_path):
            self.log.info("restore path directory already exists")
            self.client_machine.remove_directory(self.restore_path)
            self.log.info("existing restore path deleted")
        self.client_machine.create_directory(self.restore_path)
        self.log.info("restore path created")

        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for a linux MA!")
            raise Exception("LVM enabled dedup path not supplied for a linux MA!")
        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.tcinputs["dedup_path"], self.id)
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.ddb_basepath, "dedup_store_path")

        # create storage pool
        self.log.info("creating pool")
        self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name,
                                                            self.tcinputs["CloudMountPath"],
                                                            self.tcinputs["MediaAgentName"],
                                                            self.tcinputs["MediaAgentName"],
                                                            self.dedup_store_path,
                                                            username=self.tcinputs["AccessKeyAuthTypeUsername"],
                                                            password="",
                                                            credential_name=self.tcinputs
                                                            ["AccessKeyAuthTypeCredentialName"],
                                                            cloud_server_type=mediaagentconstants.CLOUD_SERVER_TYPES
                                                            [self.tcinputs['CloudVendorName']])

        # create plan
        self.commcell.storage_pools.refresh()
        self.log.info(f'Creating the plan {self.plan_name}')
        self.plan = self.commcell.plans.add(self.plan_name, "Server", self.storage_pool_name)
        self.commcell.plans.refresh()
        self.log.info(f'Plan {self.plan_name} created')

        self.plan.schedule_policies['data'].disable()

        # get store object
        self.get_active_files_store()
        self.sidb_id = self.store_obj.store_id

        part2_dir = self.media_agent_machine.join_path(self.ddb_basepath, "partition2")
        if not self.media_agent_machine.check_directory_exists(part2_dir):
            self.media_agent_machine.create_directory(part2_dir)
        self.log.info("adding partition for the dedup store")
        self.plan.storage_policy.add_ddb_partition(self.storage_pool.get_copy().copy_id, str(self.store_obj.store_id),
                                                   part2_dir, self.tcinputs["MediaAgentName"])

        # create backupset
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
        self.log.info("Backup set created")

        # generate 100 subdirectories as source content, each with 10 MB of data
        iterations = 0
        while iterations < 100:
            try:
                self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                          self.content_path,
                                                          0.01, num_of_folders=1, file_size=10000)
                time.sleep(1)
                iterations += 1
            except:
                self.log.info("something went wrong in creating the source data")
                if iterations >= 10:
                    self.log.info("we created enough data, so continue with the case")
                    break
                else:
                    raise Exception("didnt create enough source content, failing the case")

        self.content_folders = sorted(
            self.client_machine.get_folders_in_path(self.content_path, recurse=False))
        content_size = self.client_machine.get_folder_size(self.content_path)
        self.log.info(f'number of source content folders before first backup: {len(self.content_folders)}')
        self.log.info(f'size of source content path before first backup: {content_size}')

        # create subclient
        self.log.info("check SC: %s", self.subclient_name)
        if not self.backup_set.subclients.has_subclient(self.subclient_name):
            self.subclient = self.backup_set.subclients.add(self.subclient_name)
            self.log.info("created subclient %s", self.subclient_name)
        else:
            self.log.info("subclient %s exists", self.subclient_name)
            self.subclient = self.backup_set.subclients.get(self.subclient_name)

        # add subclient content
        self.log.info("add all the generated folders as content to the subclient")
        self.subclient.plan = [self.plan, self.content_folders]

        # set the subclient data reader / streams to one
        self.log.info("set the data readers for subclient %s to 1", self.subclient_name)
        self.subclient.data_readers = 1

        self.ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
        if self.media_agent_machine.check_registry_exists('MediaAgent', 'DedupDrillHoles'):
            self.log.info("DeduprillHoles registry key found on MA")
            self.log.info("Deleting DedupDrillHoles Additional Setting on MA Client from CS side")
            self.ma_client.delete_additional_setting("MediaAgent", "DedupDrillHoles")
            self.log.info("Deleting DedupDrillHoles Registry key from MA")
            self.media_agent_machine.remove_registry('MediaAgent', value='DedupDrillHoles')
            self.log.info("Successfully removed DedupDrillHoles setting from MA")

    def get_active_files_store(self):
        """returns active store object for files iDA"""

        self.commcell.deduplication_engines.refresh()
        dedup_engines_obj = self.commcell.deduplication_engines
        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])

    def run_full_backup_job(self, mark_full_on_success=False):
        """
            run a full backup job
            Arg:
                mark_full_on_success (bool) : set to true if we want to mark all vols of this job full on success
            Returns:
                an object of running full backup job
        """
        self.log.info("Starting backup job")
        if mark_full_on_success:
            job = self.subclient.backup("FULL", advanced_options={'mediaOpt': {'markMediaFullOnSuccess': True}})
        else:
            job = self.subclient.backup("FULL")
        self.log.info("Backup job: %s", str(job.job_id))
        if not job.wait_for_completion():
            if job.status.lower() == "completed":
                self.log.info("job %s complete", job.job_id)
            else:
                raise Exception(
                    f"Job {job.job_id} Failed with {job.delay_reason}")
        return job

    def gather_afs_chunks_vols(self, job_object):
        """
            fetches info for the given job object
            Args:
                job_object

            Returns:
                tuple that contains results from the backup job    
        """

        query = f"""SELECT    archchunkid 
                    FROM      archchunkmapping 
                    WHERE     archfileid 
                    IN       ( SELECT    id 
                    FROM      archfile 
                    WHERE     jobid={job_object.job_id}  
                    AND       filetype=1)"""
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")
        chunks_list = []
        for i in range(len(res)):
            chunks_list.append(int(res[i][0]))
        self.log.info("got the chunks belonging to the first backup job")
        self.log.info("Chunks are: %s", chunks_list)

        query = f"""SELECT    id
                    FROM      archFile
                    WHERE     jobId={job_object.job_id}"""
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")
        archfiles_list = []
        for i in range(len(res)):
            archfiles_list.append(int(res[i][0]))
        self.log.info("got the archfiles belonging to the first backup job")
        self.log.info("Archfiles are:%s", archfiles_list)

        chunks_list_string = ','.join(map(str, chunks_list))
        query = f"""select  distinct volumeid 
                    from    archchunk 
                    where   id in ({chunks_list_string})"""
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")
        volumes_list = []
        for i in range(len(res)):
            volumes_list.append(int(res[i][0]))

        return archfiles_list, chunks_list, volumes_list

    def get_cloud_size(self, sidb_id, volid_list):
        """
            gets volume size of volumes in a cloud library

            Args:
                sidb_id (int)  --  sidb id of the cloud library
                volid_list (list)     -- volume id whose size we want

            Returns:
                volume size of volumes in the cloud library
        """
        # get the exact mount path location
        volid_string = ','.join(map(str, volid_list))
        query = f"""UPDATE      mmvolume
                    SET         RMSpareStatusUpdateTime=RMSpareStatusUpdateTime-86400
                    WHERE       sidbstoreid={sidb_id} and volumeid = {volid_string}"""
        self.log.info("EXECUTING QUERY: %s", query)
        self.opt_selector.update_commserve_db(query)
        self.mm_helper.update_mmconfig_param(
            'MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15, 15)

        for attempt in range(1, 3):

            self.log.info("Waiting for volume size update - attempt %s", attempt)
            self.log.info("Sleeping for 17 minutes")
            time.sleep(17*60)

            query = f"""select distinct(RMSpareStatusUpdateTime) from mmvolume where 
                        sidbstoreid={sidb_id} and volumeid = {volid_string}"""
            self.log.info("EXECUTING QUERY: %s", query)
            self.csdb.execute(query)
            result = self.csdb.fetch_all_rows()
            self.log.info(f"QUERY OUTPUT : {result}")
            if result == [['-1']]:
                self.log.info("volume size update completed in attempt %s out of 2", attempt)
                break
            self.log.info("volume size update did not complete in attempt %s out of 2. Waiting for 1 more round.",
                          attempt)

        query = f"""SELECT    physicalbytesmb  
                    FROM      mmvolume where sidbstoreid={sidb_id} and volumeid = {volid_string}"""
        self.log.info("EXECUTING QUERY: %s", query)
        self.csdb.execute(query)
        size_cloud = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"QUERY OUTPUT : {size_cloud}")
        return size_cloud

    def modify_subclient_content(self):
        """
            modifies subclient content by deleting every other subclient content folder

        """
        second_backup_content = []
        # change the content on the subclient for the second backup job
        for i in range(0, len(self.content_folders), 2):
            second_backup_content.append(self.content_folders[i])
        self.log.info(f'number of source content folders before second backup: {len(second_backup_content)}')
        self.log.info("deleted every alternate folder from the content folders list ")
        self.log.info("maximises the chance of drill hole taking place while pruning ")

        # add the modified content folders list to subclient
        self.log.info("MODIFIED content folders list added as content to the subclient")
        self.subclient.content = second_backup_content

    def delete_first_backup(self, first_job):
        """
            deletes the first backup job

            Args:
                first_job (obj)  --  first backup job object
        """
        # delete the first backup job
        storage_policy_copy = self.plan.storage_policy.get_copy("Primary")
        # because only copy under storage policy was created above
        storage_policy_copy.delete_job(first_job.job_id)
        self.log.info("deleted the first backup job: id %s", str(first_job.job_id))

        # after deletion of job, the archFiles should be moved to
        # MMdeletedAF table
        self.log.info("sleeping for 30 seconds")
        time.sleep(30)

    def get_table_row_count(self, table, storeid):
        """ Get distinct AF count for the given table
            Args:
                storeid (object) - storeid
                table (str) - tablename to get count
            Returns:
                num_rows    (int) - number of rows
        """
        query = f"select count(distinct archfileid) from {table} where sidbstoreid  = {storeid} "
        self.log.info(f"Query => {query}")
        self.csdb.execute(query)
        num_rows = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"Output ==> {num_rows}")
        return num_rows

    def verify_phase2_pruning(self, afids_first_job, error_flag=None):
        """
        verify that entries get added to mmdeletedaf table and then removed from mmdeletedaf table

        Args:
            afids_first_job (list) -- list of the afids from the first backup job
            error_flag (list) -- error flag list from previous validations

        Returns:
            error_flag (list) -- any errors occurred during runtime of the method appended to provided error_list
        """
        self.mm_helper.update_mmconfig_param(
            'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 0, 2)

        if error_flag is None:
            error_flag = []
        self.log.info("SETUP VALIDATION 1:"
                      " Verify if the deleted job files have been moved to MMdeletedAF")

        query = f"""SELECT    archFileId 
                    FROM      MMDeletedAF 
                    WHERE     SIDBStoreId={self.sidb_id} """
        self.log.info(f"EXECUTING QUERY {query}")
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")

        mm_deleted_af_list = []
        for count, item in enumerate(res):
            mm_deleted_af_list.append(int(item[0]))

        if set(afids_first_job) == set(mm_deleted_af_list):
            self.log.info("Result: Pass")
            self.log.info(
                "archfiles of first job have been transferred to MMdeletedAF")
        else:
            self.log.error("WARNING: archfiles of deleted job have not been moved to MMDeletedAF")

        self.log.info("----------------------------------------------")
        self.log.info("waiting... to trigger MM Prune Process")

        for i in range(2):
            self.log.info(f"data aging + sleep for 5 seconds: RUN {i + 1}")
            job = self.mm_helper.submit_data_aging_job(
                copy_name="Primary",
                storage_policy_name=self.plan.storage_policy.storage_policy_name,
                is_granular=True, include_all=False,
                include_all_clients=True,
                select_copies=True,
                prune_selected_copies=True)
            self.log.info(f"Data Aging job: {str(job.job_id)}")
            if not job.wait_for_completion():
                if job.status.lower() == "completed":
                    self.log.info(f"job {job.job_id} complete")
                else:
                    raise Exception(f"Job {job.job_id} Failed with {job.delay_reason}")
            time.sleep(5)

        # confirm phase 2 pruning is finished
        phase2_pruning_done = False
        iterations = 0
        while not phase2_pruning_done and iterations < 3:
            table_count_mmdel = self.get_table_row_count('mmdeletedaf', self.store_obj.store_id)
            self.log.info(f'Count of AFs in mmdeletedaf table for store {self.store_obj.store_id} '
                          f'is {table_count_mmdel}')
            table_count_mmtracking = self.get_table_row_count('mmdeletedarchfiletracking', self.store_obj.store_id)
            self.log.info(f'Count of AFs in mmdelTracking table for store {self.store_obj.store_id} '
                          f'is {table_count_mmtracking}')
            if table_count_mmdel == 0 and table_count_mmtracking == 0:
                phase2_pruning_done = True
                self.log.info(f'phase2 pruning finished successfully for store {self.store_obj.store_id}')
            else:
                self.log.info(f'iteration {iterations}: {self.store_obj.store_id} still has entries in '
                              f'mmdel tables, wait 5 minutes and try again')
                iterations += 1
                time.sleep(300)
        if not phase2_pruning_done:
            self.log.error(f'FAILURE: phase2 pruning didnt finish for store {self.store_obj.store_id}')
            error_flag += ["phase2 pruning didnt finish for store"]
            raise Exception("TC FAILED, phase2 pruning didnt finish")
        return error_flag

    def run_ms(self):
        """
            add reg key to trigger MS on next backup, run that backup, confirm msruntime gets updated in the csdb,
            and remove reg key

        """

        # get last MS run time for all substores
        self.store_obj.refresh()
        query = f"""select entityid, longlongVal from mmentityprop where propertyname = 
                    'DDBMSRunTime' and entityid in
                    ({self.store_obj.all_substores[0][0]}, {self.store_obj.all_substores[1][0]})"""
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
            self.run_full_backup_job()
            self.csdb.execute(query)
            second_ms_run_time = self.csdb.fetch_all_rows()
            self.log.info(f"QUERY OUTPUT : {second_ms_run_time}")
            if int(second_ms_run_time[0][1]) > int(first_ms_run_time[0][1]) and \
                    int(second_ms_run_time[1][1]) > int(first_ms_run_time[1][1]):
                self.log.info(f"confirmed MS ran on substores of store {self.store_obj.store_id}")
                ms_ran = True
            else:
                self.log.info(f"iteration {iterations}: MS didnt run yet, so run another backup to induce it")
                iterations += 1
        if not ms_ran:
            self.log.error(f"MS never ran on both substores of store {self.store_obj.store_id}")
            raise Exception(f"MS never ran on both substores of store {self.store_obj.store_id}")

        # remove reg key that runs Mark and Sweep immediately
        self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting")
        self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

    def run_pruning_validation(self, error_flag=None):
        """
            verify if phase 3 pruning has run

            Args:
                error_flag (list)  --  error flag list from previous validations

            Returns:
                any errors occured during runtime of the method
                appended to provided error_list
        """

        self.log.info("===================================="
                      "===============================================")
        self.mm_helper.update_mmconfig_param(
            'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 0, 2)

        self.log.info("mmprune process interval set to two minute")

        self.log.info("waiting... to trigger MM Prune Process")
        pruning_done = False
        for i in range(10):
            self.log.info("data aging + sleep for 240 seconds: RUN %s", (i + 1))

            job = self.mm_helper.submit_data_aging_job(
                copy_name="Primary",
                storage_policy_name=self.plan.storage_policy.storage_policy_name,
                is_granular=True, include_all=False,
                include_all_clients=True,
                select_copies=True,
                prune_selected_copies=True)

            self.log.info("Data Aging job: %s", str(job.job_id))
            if not job.wait_for_completion():
                if job.status.lower() == "completed":
                    self.log.info("job %s complete", job.job_id)
                else:
                    raise Exception(
                        f"Job {job.job_id} Failed with {job.delay_reason}")
            matched_lines = self.dedup_helper.validate_pruning_phase(self.sidb_id, self.tcinputs['MediaAgentName'])
            self.log.info(matched_lines)

            if matched_lines:
                self.log.info(matched_lines)
                self.log.info(f"Successfully validated the phase 3 pruning on sidb - {self.sidb_id}")
                pruning_done = True
                break
            else:
                self.log.info(f"No phase 3 pruning activity on sidb - {self.sidb_id} yet. Checking after 240 seconds")
                time.sleep(240)

        if not pruning_done:
            self.log.error("Pruning is not over even after 40 minutes. Raising Exception")
            error_flag += ["Pruning is not over even after 40 minutes"]
        return error_flag
        
    def run_log_validation(self, chunks_first_job, error_flag):
        """
            verify if the drill hole occurred for the chunks of the first job

            Args:
                chunks_first_job (list)  --  list of chunks belonging to
                                             first backup job
                error_flag (list)  --  error flag list from previous validations

            Returns:
                any errors occured during runtime of the method
                appended to provided error_list
        """

        self.log.info("==========================================="
                      "========================================")
        self.log.info("CASE VALIDATION 1: verify if the drill hole occurred for the chunks of the first job")
        self.log.info("sleeping 5 minutes to handle case where first phase 3 pruning pass logged Finalized but didnt "
                      "actually prune anything")
        time.sleep(300)
        log_file = "SIDBPhysicalDeletes.log"
        match_regex = [" H "]
        drill_hole_records = []
        drill_hole_occurrance = False

        matched_lines, matched_strings = self.dedup_helper.parse_log(
            self.tcinputs['MediaAgentName'], log_file, match_regex[0])

        # convert list of chunks to strings and parse sidbphysicaldeletes to see if holes were drilled in them
        chunks_first_job_string = [str(chunk) for chunk in chunks_first_job]
        for matched_line in matched_lines:
            line = matched_line.split()
            for commonstring in line:
                if commonstring in chunks_first_job_string:
                    drill_hole_occurrance = True
                    drill_hole_records.append(commonstring)

        if drill_hole_occurrance:
            self.log.info("Result: Pass _ Atleast one chunk was deleted by using Drill Hole method")
            self.log.info("Chunk IDs with drilled holes are ")
            for drilled_hole_chunk in set(drill_hole_records):
                self.log.info(drilled_hole_chunk)
        else:
            self.log.info("Result: Fail")
            error_flag += ["No Chunk was deleted using Drill Hole method: Drill hole did not occur"]

        return error_flag

    def run_pruning_csdb_validation(self, error_flag):
        """
            check for phase 3 count in idxSidbUsageHistory Table

            Args:
                error_flag (list)  --  error flag list from previous validations

            Returns:
                any errors occured during runtime of the method
                appended to provided error_list
        """
        self.log.info("===================================="
                      "===============================================")
        self.log.info("CASE VALIDATION 2: Check for"
                      " phase 3 count in idxSidbUsageHistory Table")
        query = f"""SELECT    ZeroRefCount
                    FROM      IdxSIDBUsageHistory
                    WHERE     SIDBStoreId = {self.sidb_id}
                    AND       HistoryType = 0
                    ORDER BY(ModifiedTime) DESC"""
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        zero_ref_count_case3 = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"QUERY OUTPUT : {zero_ref_count_case3}")
        if zero_ref_count_case3 == 0:
            self.log.info("Result:Pass")
            self.log.info("Pending delete count is 0")
        else:
            self.log.info("Result:Fail")
            self.log.info("Deletion of items with no reference is still pending")
            error_flag += ["pending delete count in idxSidbUsageHistory Table is not zero"]

        return error_flag

    def run_physical_size_validation(self, initial_size, error_flag, volumes_list):
        """
            check if there is reduction in physical size of the chunks

            Args:
                initial_size (int)  --  initial size of the chunks
                error_flag (list)  --  error flag list from previous validations
                volumes_list (list) -- volumes we want to evaluate on size

            Returns:
                any errors occured during runtime of the method
                appended to provided error_list
        """

        self.log.info("======================================"
                      "=============================================")
        self.log.info("CASE VALIDATION 3: Checking if"
                      " there is reduction in physical size of the chunks")

        current_size = self.get_cloud_size(self.sidb_id, volumes_list)

        if current_size < initial_size:
            self.log.info("physical size after pruning [%s] by "
                          "drill hole is less than initial size [%s]", current_size, initial_size)
            self.log.info("RESULT: PASS")
        else:
            self.log.info("RESULT: FAIL")
            self.log.info("physical size after pruning [%s] by drill hole is not less than initial size [%s]",
                          current_size, initial_size)
            error_flag += ["physical size after pruning by drill hole is not less than initial size"]

        return error_flag

    def run_restore_job(self, second_backup_contents):
        """
            run a restore job for the second backup and verifying the files

            Args:
                second_backup_contents (list)  --  list of content folders that were backed up
        """
        self.log.info("===================================="
                      "===============================================")
        self.log.info("CASE VALIDATION 4: Running a restore job"
                      " for the second backup and verifying the files")
        restore_job = self.subclient.restore_out_of_place(self.client.client_name,
                                                          self.restore_path, second_backup_contents)
        self.log.info("Restore job: %s", restore_job.job_id)
        if not restore_job.wait_for_completion():
            if restore_job.status.lower() == "completed":
                self.log.info("job %d complete", restore_job.job_id)
            else:
                raise Exception(
                    f"Job {restore_job.job_id} Failed with {restore_job.delay_reason}")

        self.log.info("VERIFYING IF THE RESTORED FOLDERS ARE SAME OR NOT")
        restored_folders = self.client_machine.get_folders_in_path(
            self.restore_path)
        self.log.info("Comparing the files using MD5 hash")
        if len(restored_folders) == len(second_backup_contents):
            restored_folders.sort()
            second_backup_contents.sort()
            for original_folder, restored_folder in zip(
                    second_backup_contents, restored_folders):
                if self.client_machine.compare_folders(
                        self.client_machine, original_folder, restored_folder):
                    self.log.info("Result: Fail")
                    raise Exception("The restored folder is "
                                    "not the same as the original content folder")
                else:
                    self.log.info("file hashes are equal")
            self.log.info("Result: Pass")
        else:
            self.log.info("Result: Fail")
            raise Exception("The number of restored folders does not match the number of content folders")

    def run(self):
        """Run function of this test case"""
        try:
            error_flag = []
            self.previous_run_clean_up()
            self.create_resources()

            first_job = self.run_full_backup_job()
            first_result = self.gather_afs_chunks_vols(first_job)
            afids_first_job = first_result[0]
            chunks_first_job = first_result[1]
            volumes_first_job = first_result[2]

            self.modify_subclient_content()
            second_job = self.run_full_backup_job(mark_full_on_success=True)
            self.log.info("Checking the cloud size after second backup job")
            initial_size = self.get_cloud_size(self.sidb_id, volumes_first_job)

            self.delete_first_backup(first_job)

            error_flag = self.verify_phase2_pruning(afids_first_job)
            self.run_ms()
            error_flag = self.run_pruning_validation(error_flag)
            error_flag = self.run_log_validation(
                chunks_first_job, error_flag)
            error_flag = self.run_pruning_csdb_validation(error_flag)
            error_flag = self.run_physical_size_validation(
                initial_size, error_flag, volumes_first_job)
            self.run_restore_job(self.subclient.content)

            if error_flag:
                # if the list is not empty then error was there, fail the test case
                self.log.info(error_flag)
                raise Exception(error_flag)
            else:
                self.log.info("Testcase completed successfully")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all objects created for the testcase"""
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            self.mm_helper.update_mmconfig_param(
                'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)
            self.mm_helper.update_mmconfig_param(
                'MMS2_CONFIG_MAGNETIC_VOLUME_SIZE_UPDATE_INTERVAL_MINUTES', 15, 60)
            self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")
            self.log.info("Performing unconditional cleanup")

            self.previous_run_clean_up()

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR:%s", exp)
