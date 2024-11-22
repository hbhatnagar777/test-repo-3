# coding=utf-8
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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    setup_environment() -- configures entities based on inputs

    get_active_files_store() -- gets active files DDB store id

    clean_test_environment()   --  cleans all created entities

    generate_data_run_backup()   -- runs backup needed for the case

    insert_mmdeletedaf_rows ()  --inserts rows in mmdeletedaf table

    prune_jobs()                -- prunes jobs

    run_and_suspend_dv2_job () -- runs and suspends a dv2 job in phase1

    get_table_row_count()  --get count of distinct Afs from a table




Sample JSON: values under [] are optional
"60930": {
            "ClientName": "",
            "AgentName": "File System",
            "MediaAgentName": "",
            ["DDBPath": ""]
        }
ign:

    add dedupe sp with provided DDB path or self search path
    run  backup jobs
    prune few jobs
    increase mmpruneprocessinterval to 500 mins
    insert  rows in mmdeletedaf table for the store created
    keep note of the total count of mmdeletedaf entries  and mmdeletedtrackingaf entries for this store
    run DV2 job on the store and suspend it once it goes in phase1
    decrease mmpruneprocessinterval and let pruning happen.
    wait for 10 mins and let phase2 pruning happen as well(this would fail as Dv2 is running)
    Keep note of count of AFs having mpid=0 in mmdel* table having non-zero errorcode
    run Aging again  . make sure AFs are not removed from mmdel table and count remains the same with errorcode 53069.
"""


import time
from cvpysdk import deduplication_engines
from AutomationUtils import commonutils
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils import mahelper
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "pruning case - to check mmdeletedaf doesnt drop entries on phase2 pruning error"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.library_name = None
        self.mountpath = None
        self.ma_name = None
        self.storage_policy_name = None
        self.storage_policy_obj = None
        self.backupset_name = None
        self.subclient_name = None
        self.mahelper_obj = None
        self.client_machine_obj = None
        self.client_machine = None
        self.ma_machine_obj = None
        self.ma_library_drive = None
        self.dedup_path = None
        self.content_path = None
        self.subclient_obj = None
        self.bkpset_obj = None
        self.sp_obj = None
        self.client_system_drive = None
        self.dedup_helper_obj = None
        self.sqlobj = None
        self.user_lib = False
        self.user_sp = False
        self.optionobj = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.mmpruneprocess_value = None
        self.mm_helper = None
        self.content_path_list = []
        self.sql_password = None
        self.backup_job_list = []


    def setup(self):
        """Setup function of this test case"""
        self.optionobj = OptionsSelector(self.commcell)
        self.sql_password = commonutils.get_cvadmin_password(self.commcell)
        self.mm_helper = mahelper.MMHelper(self)

        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.client_machine = Machine(self.tcinputs['ClientName'], self.commcell)
        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 15*1024)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 15*1024)
        self.library_name = f"Lib_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.ma_machine_obj.join_path(self.tcinputs.get("mount_path"), self.id)
        else:
            self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive,f"MP_{self.id}")
            self.log.info("MP created at")


        self.storage_policy_name = f"SP_TC_{self.id}"
        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, "DDBs", f"TC_{self.id}")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get('dedup_path'), "DDBs", f"TC_{self.id}")

        self.backupset_name = f"BkpSet_TC_{self.id}"
        self.subclient_name = f"Subc_TC_{self.id}"
        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, self.id)


    def configure_tc_environment(self):
        """
        Configure testcase environment - library (if required), storage policy, backupset, subclient
        """
        self.log.info("===STEP: Configuring TC Environment===")
        self.mahelper_obj = MMHelper(self)
        self.dedup_helper_obj = DedupeHelper(self)
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", self.content_path)
            self.client_machine_obj.remove_directory(self.content_path)
        self.client_machine_obj.create_directory(self.content_path)

        if not self.ma_machine_obj.check_directory_exists(self.mountpath):
            self.log.info("Creating mountpath directory [%s]", self.mountpath)
            self.ma_machine_obj.create_directory(self.mountpath)
        self.log.info("Creating Library [%s]", self.library_name)
        if self.commcell.disk_libraries.has_library(self.library_name):
            self.log.info("Library [%s] already exists. Reusing the Library.", self.library_name)
        else:
            self.mahelper_obj.configure_disk_library(self.library_name, self.ma_name, self.mountpath)
            self.log.info("Library [%s] created successfully.", self.library_name)


        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.sp_obj = self.dedup_helper_obj.configure_dedupe_storage_policy(
            self.storage_policy_name, self.library_name, self.ma_name, self.dedup_path)
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)

        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        if dedup_engines_obj.has_engine(self.storage_policy_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_policy_name, 'Primary')
            #dedup_stores_list = dedup_engine_obj.all_stores
           # for dedup_store in dedup_stores_list:
            #    store_obj = dedup_engine_obj.get(dedup_store[0])
             #   self.log.info("Disabling Garbage Collection on DDB Store == %s", dedup_store[0])
              #  store_obj.enable_garbage_collection = False

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        self.log.info("Configuring Subclient [%s]", self.subclient_name)
        self.subclient_obj = self.mahelper_obj.configure_subclient(self.backupset_name, self.subclient_name,
                                                                   self.storage_policy_name, self.content_path)
        self.log.info("Successfully configured Subclient [%s]", self.subclient_name)


    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.storage_policy_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0





    def generate_data_run_backup(self, size_in_gb, backup_type="Incremental", mark_media_full=False,
                                 copy_data=False, copy_from_dir=""):
        """
        Generate subclient content and run given type of backup on subclient
        Args:
            size_in_gb (int)      -- Content Size in GB
            backup_type (str)     -- Backup Type [ Full or Incremental etc. ]
            mark_media_full(bool) -- Boolean Flag to decide if volumes are to be marked full after backup completion
            copy_data (bool)      -- Boolean Flag to decide if new data to be generated  or existing data to be copied
            copy_from_dir (str)   -- Source directory if copy_data is set to True
        Return:
            Returns content dir for job
        """
        self.log.info("Generating content of size [%s] at location [%s]", size_in_gb, self.content_path)
        content_dir = ""
        if not copy_data:
            content_dir = f"{self.content_path}{self.client_machine_obj.os_sep}{size_in_gb}"
            self.mahelper_obj.create_uncompressable_data(self.client.client_name, content_dir, size_in_gb, 1)
        else:
            target_content_dir = f"{copy_from_dir}_copied"
            if not self.client_machine_obj.check_directory_exists(target_content_dir):
                self.client_machine_obj.create_directory(target_content_dir)
            self.log.info("Generating duplicate content by copying from - %s", copy_from_dir)
            self.client_machine_obj.copy_folder(copy_from_dir, target_content_dir)

            copied_dir = self.client_machine_obj.get_folders_in_path(target_content_dir)
            self.log.info(f"Deleting every alternate file from {copied_dir[1]}")
            self.optionobj.delete_nth_files_in_directory(self.client_machine_obj, copied_dir[1], 2, "delete")
            content_dir = target_content_dir
        if mark_media_full:
            job_obj = self.subclient_obj.backup(backup_type, advanced_options={'mediaOpt': {'startNewMedia': True}})
        else:
            job_obj = self.subclient_obj.backup(backup_type)

        self.log.info("Successfully initiated a [%s] backup job on subclient with jobid [%s]", backup_type,
                      job_obj.job_id)
        if not job_obj.wait_for_completion():
            raise Exception("Backup job [%s] did not complete in given timeout" % job_obj.job_id)

        self.log.info("Successfully completed the backup job with jobid [%s]", job_obj.job_id)
        self.backup_job_list.append(job_obj)
        return content_dir



    def clean_test_environment(self):
        """
        Clean up test environment
        """
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
            self.log.info("Deleting Library")
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
                self.log.info("Library deleted")
        except Exception as excp:
            self.log.info("***Failure in deleting library during cleanup - %s "
                          "Treating as soft failure as library will be reused***", str(excp))

        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.client_machine_obj.remove_directory(self.content_path)
            self.log.info("Deleted the Content Directory.")
        else:
            self.log.info("Content directory does not exist.")



    def insert_mmdeletedaf_rows(self, num_of_rows, store):
        """
        insert rows in mmdeletedaf table.
        Args:
                number_of_rows  int)   -   minimum value of the parameter
                store      (int)   -   value to be set
        """

        try:
            AFid = 11111111
            for i in range(1,num_of_rows):
                query = f"insert into mmdeletedaf values ({AFid},0,2,0,0,0,0,0,0,{store},2,999999999,0,0,0,0,0,0,0)"
                self.optionobj.update_commserve_db(query)
                AFid=AFid+1

        except Exception as excp:
            self.log.info("***Failure in inserting rows.")




    def get_table_row_count(self, table, storeid, failureerrorcode):
        """ Get distinct AF count for the given table
            Args:
                store (object) - storeid
                failuererrorcode (str) - code to check
                table (str) - tablename to get count
            Returns:
                (int) - number of rows
        """
        query = f"select count(distinct archfileid) from {table} where sidbstoreid  = {storeid} and " \
                f"FailureErrorCode ={failureerrorcode} "
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        num_rows = int(self.csdb.fetch_one_row()[0])
        self.log.info("Output ==> %s", num_rows)
        return num_rows




    def run_and_suspend_dv2_job(self, store):
        """
        Runs DV2 job with type and option selected and waits for job to complete
        Args:
            store (object) - object of the store to run DV2 job on


        """
        store.refresh()
        self.log.info("running full quick DV2 job on store [%s]...", store.store_id)
        job = store.run_ddb_verification(incremental_verification=False)

        self.log.info("DV2 job: %s", job.job_id)
        if job.phase == "Validate Dedupe Data":
            self.log.info("Job Phase : [%s]. will suspend the job", job.phase)
            job.pause(wait_for_job_to_pause=True)
            return 1

        else:
            self.log.error("Job is not in Validate Dedupe Data")
            return 0



    def prune_jobs(self, list_of_jobs):
        """
        Prunes jobs from storage policy copy

        Args:
            list_of_jobs(obj) - List of jobs
        """
        sp_copy_obj = self.sp_obj.get_copy("Primary")
        for job in list_of_jobs:
            sp_copy_obj.delete_job(job.job_id)
            self.log.info("Deleted job from %s with job id %s", self.storage_policy_name, job.job_id)
        self.mahelper_obj.submit_data_aging_job()



    def run(self):
        """Run function of this test case"""
        try:
            self.clean_test_environment()

            self.configure_tc_environment()

            store = self.get_active_files_store()
            storeid=store.store_id
            self.backup_job_list = []
            backup_content_dirs = []

            self.log.info("==Run Backups==")
            for i in range(1, 4):
                backup_content_dirs.append(self.generate_data_run_backup(i * 1, mark_media_full=True, copy_data=False))
                self.generate_data_run_backup(i * 1, mark_media_full=False, copy_data=True,
                                              copy_from_dir=backup_content_dirs[i - 1])

            self.mm_helper.update_mmpruneprocess(db_user='sqladmin_cv', db_password=self.sql_password, min_value=2,
                                                 mmpruneprocess_value=2)
            self.log.info("==Prune the backup jobs==")
            self.prune_jobs([self.backup_job_list[x] for x in range(0, len(self.backup_job_list), 2)])
            time.sleep(130)
            self.mm_helper.submit_data_aging_job(storage_policy_name=self.storage_policy_name, copy_name='primary')
            time.sleep(130)


            self.mm_helper.update_mmpruneprocess(db_user='sqladmin_cv',db_password=self.sql_password, min_value=10,
                                                 mmpruneprocess_value=500)
            Num_of_rows =100

            self.log.info("storeid : %s  ", storeid)
            self.insert_mmdeletedaf_rows(Num_of_rows,storeid)

            failureerrorcode= 0
            table_count_mmdel=self.get_table_row_count('mmdeletedaf',storeid,failureerrorcode)

            self.log.info("Count of AFs before Dv2  in mmdeletedaf table is %s ", table_count_mmdel)

            table_count_mmtracking = self.get_table_row_count('mmdeletedarchfiletracking', storeid, failureerrorcode)

            self.log.info("Count of AFs before Dv2 in mmdeletedarchfiletracking table is %s ", table_count_mmtracking)

            total_count = table_count_mmdel + table_count_mmtracking

            self.log.info("Total Count of AFs before Dv2 is  %s ", total_count)



            #suspend dv2 job
            quick_dv2 = self.run_and_suspend_dv2_job(store)
            if quick_dv2 == 0:
                raise Exception("failed to suspend Dv2 job")

            self.mm_helper.update_mmpruneprocess(db_user='sqladmin_cv', db_password=self.sql_password, min_value=2,
                                                 mmpruneprocess_value=2)

            #assumption is after couple of DA jobs all rows from tracking table will be inserted in mmdeletedaf table.

            for attempt in range(5):
                da_job = self.mm_helper.submit_data_aging_job(storage_policy_name=self.storage_policy_name, copy_name='primary')
                if not da_job.wait_for_completion():
                    raise Exception(f"Data Aging job [{da_job.job_id}] did not complete in given timeout - {da_job.delay_reason}")
                failureerrorcode= 53069
                table_count_after_dv2=self.get_table_row_count('mmdeletedaf',storeid,failureerrorcode)
            
                if total_count != table_count_after_dv2:
                    if attempt < 4:
                        self.log.info(f"Attempt {attempt+1} : AF counts did not match. Will retry after 5 minutes.")
                        time.sleep(300)
                    else:
                        self.log.error(f"Attempt {attempt+1} : AF count mismatch even after25 minutes")
                        raise Exception("AF counts did not match: Before DV2 count  is %s and  After DV2 count is %s ",
                                        total_count , table_count_after_dv2)
            self.log.info("AF count is same even on error in phase2 pruning.No records dropped")


        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if self.mmpruneprocess_value:
                self.mm_helper.update_mmpruneprocess(db_user='sqladmin_cv',db_password=self.sql_password, min_value=10,
                                                     mmpruneprocess_value=10)
            self.clean_test_environment()

