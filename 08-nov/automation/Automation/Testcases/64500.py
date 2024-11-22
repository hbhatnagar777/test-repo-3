# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""This testcase verifies single pruner MA for disk library"""

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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
    
    clean_test_environment() -- cleanup of created entities
    
    create_resources()--	Create the resources required to run backups

    run_backups()			--	Run backup jobs on subclient 3cycles
    
    create_content()        --  creates content for subclient    
    
    validate_softaging_on_job()  -- get attribute value from jmbkpstats table for job
    
    validate_softaging_on_copy() -- get soft age flag value from jmjobdatastats table for a copy
    
    update_start_end_date()  -- update start and end time for a job by x number of days
    
    perform_validation()    -- checks the values of soft age flags on given joblist and copy
    
    create_pool()   -- creates storage pool with 2 partition DDB
    
        
This testcase verifies soft aging of a job

1)Create SP with 2 copies.
Retention on Pri 2d,10c
Retention on sec 5d ,10c

Run a F1 ,I1,I2 ,F2, I1,I2, F3
 
2)Move jobs start time and end time to 3 days behind for F1 and I1,I3
3)Run data aging job, jobs should not be soft aged. 
4)make sure aux copy is not run .Confirm flags is not set in jmjobdatastats table for pri copy
5)Jobs will not be marked soft aged until copied to sec copy.


select disabled&65536 from jmjobdatastats where jobid=<> and copyid = <> 

select BkpAttributesEx & 0x2000000000000000,* from jmbkpstats where jobid=<>


6)Run aux copy job and make sure data is copied. Run data aging job, jobs should be soft aged only on Pri copy
disabled&65536 à this should be set for jobs only on PRi and agedtime be changed to DA time

jmbkpstats will not be updated 

7)Disable DA on sec copy
8)Move jobs start time and end time to 3 days behind for F1,I1,I2
8)Run DA and verify the jobs don’t get soft aged on sec copy(flag should be 0)
9)Enable DA on copy
10)Confirm  job is marked soft aged on sec copy and bkpstats table will  be updated too.
11) disable DA on client
12) cycle goes by 3 days
13) jobs should not be marked soft aged on primary


input json file arguments required:
                        
                64500 :{
                        "ClientName": "name of the client machine as in commserve",
                        "AgentName": "File System",
                        "MediaAgentName": "name of the media agents as in commserve" 
                        Optional parameters:  
                        "ddb_path" : path for DDB for primary copy                        
                        "copy_ddb_path": path for DDB for sec copy
                        "mount_path" : mountpath location      
                        "copy_mount_path" : mountpath location for secondary pool    
                        }

"""

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        # Initializes test case class object
        super(TestCase, self).__init__()
        self.name = "Validate soft aging of jobs"
        self.library_name = None
        self.mountpath = None
        self.copy_mountpath = None
        self.ma_name = None
        self.pruner_ma_name = None
        self.store_obj = None
        self.storage_policy_name = None
        self.sp_obj = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.client_machine_obj = None
        self.ma_machine_obj = None
        self.ma_library_drive = None
        self.dedup_path = None
        self.copy_ddb_path = None
        self.content_path = None
        self.subclient_obj = None
        self.bkpset_obj = None
        self.client_system_drive = None
        self.backup_job_list = []
        self.sqlobj = None
        self.mm_admin_thread = None
        self.optionobj = None
        self.is_user_defined_mp = False
        self.is_user_defined_copy_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_dedup_1 = False
        self.storage_pool_name = None
        self.error_list = ""
        self.mount_path_folder = None
        self.media_agent_obj = None
        self.dedup_helper = None
        self.windows_machine_obj = None
        self.time_moved = False
        self.sql_password = None
        self.ma_client = None
        self.mount_location =None
        self.library=None
        self.primary_copy=None
        self.sec_copy = None
        self.copyName=None
        self.sql_username=None
        self.storage_pool_name_sec=None



    def setup(self):
        """Setup function of this test case"""
        self.optionobj = OptionsSelector(self.commcell)
        self.sql_password = commonutils.get_cvadmin_password(self.commcell)
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get('copy_mount_path'):
            self.is_user_defined_copy_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        if self.tcinputs.get("copy_ddb_path"):
            self.is_user_defined_dedup_1 = True
        self.ma_name = self.tcinputs.get('MediaAgentName')

        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 25*1024)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 25*1024)
        self.library_name = f"Lib_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.is_user_defined_dedup_1 and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.tcinputs.get("mount_path")
        else:
            self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, "MP")

        if self.is_user_defined_copy_mp:
            self.log.info("custom mount path supplied for sec pool")
            self.copy_mountpath = self.tcinputs.get("copy_mount_path")
        else:
            self.copy_mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, "MP2")



        self.storage_pool_name = f"StoragePool_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"
        self.storage_pool_name_sec = f"StoragePool_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}_sec"
        self.storage_policy_name = f"SP_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"
        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, str(self.id), "DedupDDB")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.tcinputs.get('dedup_path'), str(self.id))

        if not self.is_user_defined_dedup_1:
            self.copy_ddb_path= self.ma_machine_obj.join_path(self.ma_library_drive, str(self.id), "DedupDDB1")
        else:
            self.copy_ddb_path =self.ma_machine_obj.join_path(self.tcinputs.get('copy_ddb_path'),str(self.id))

        self.backupset_name = f"BkpSet_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"
        self.subclient_name = f"Subc_TC_{self.id}_{self.tcinputs.get('MediaAgentName')}"

        self.content_path= self.client_machine_obj.join_path(self.client_system_drive, self.id, "subc")
        self.log.info(f"Content path is ::  {self.content_path}")

        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)

    def create_pool(self,pool_name,ddb_path,mp_path):
        """
        creates pool and adds 2nd partition to it
        Args:
            pool_name(string) : storage pool name
            ddb_path (string) :path for DDB folder
            mp_path (string) : path for mountpath folder
        """

        self.log.info(f"Configuring Storage Pool for {pool_name}")
        if not self.commcell.storage_pools.has_storage_pool(pool_name):
            self.commcell.storage_pools.add(pool_name, mp_path,
                                                        self.tcinputs['MediaAgentName'],
                                                        self.tcinputs['MediaAgentName'], ddb_path)
        else:
            self.commcell.storage_pools.get(pool_name)

        self.log.info(f"Done creating a storage pool :  {pool_name}")


        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)

        if dedup_engines_obj.has_engine(pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores

            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])
                self.log.info(f"Storage pool created with one partition. Adding 2nd partition for pool {pool_name}")
                self.store_obj.add_partition(ddb_path, self.tcinputs['MediaAgentName'])





    def create_resources(self):
        """Create all the resources required to run backups"""

        self.log.info("===STEP: Configuring TC Environment===")
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", self.content_path)
            self.client_machine_obj.remove_directory(self.content_path)
        self.client_machine_obj.create_directory(self.content_path)

            # Creating primary copy storage pool and associate to SP
        self.create_pool(self.storage_pool_name, self.dedup_path, self.mountpath )

        self.log.info("Configuring Storage Policy ==> %s", self.storage_policy_name)
        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.sp_obj =self.commcell.storage_policies.add(storage_policy_name=f"{self.storage_policy_name}",
                global_policy_name=self.storage_pool_name,global_dedup_policy=True)
        else:
            self.sp_obj =self.commcell.storage_policies.get(f"{self.storage_policy_name}")

        # update retention to 2 day, 10 cycle
        self.primary_copy = self.sp_obj.get_copy('Primary')
        self.log.info("Setting retention on Primary copy as 2days,10cycles")
        self.primary_copy.copy_retention = (2, 10, 1)


        # Creating a sec storage pool and associate a copy to it
        self.create_pool(self.storage_pool_name_sec, self.copy_ddb_path,self.copy_mountpath)

        #create sec copy
        self.copyName= "sec_copy"
        self.sp_obj.create_secondary_copy(self.copyName, global_policy=self.storage_pool_name_sec)
        self.log.info("Done creating a SecCopy")

        # update retention to 5 day, 10 cycle
        self.sec_copy = self.sp_obj.get_copy(self.copyName)
        self.log.info("Setting retention on sec Copy as 5days,10cycles")
        self.sec_copy.copy_retention = (5, 10, 1)

        # remove association from autocopy schedule
        self.log.info("removing association from autocopy aux schedule so that jobs are not copied immediately")
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.copyName)

        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mm_helper.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        self.subclient_obj= self.mm_helper.configure_subclient(self.backupset_name,self.subclient_name,
                                                               self.storage_policy_name,self.content_path)
        self.log.info(f"Successfully configured Subclient [{self.subclient_name}]")

        #disable compression
        self.log.info("Disabling compression on subclient ")
        self.subclient_obj.software_compression = 4


    def create_content(self,size):
        """
        create desired content for subclient
        Args:
        size (int) = size of the content directory to be created
        """
        self.log.info(self.content_path)
        self.log.info("Generating content for subclient [%s] at [%s]", self.subclient_obj.name,
                      self.content_path)
        self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'], self.content_path, size)
        self.log.info("created content")

    def update_start_end_date(self,cycle_number):
        """
            Update the servstarttime and servendtime for job from jmbkpstats table
            Args:
                cycle_number(int) - cycle number for jobs we want to move the date behind
        """
        if cycle_number == 1:
            start,end = 0,3
        elif cycle_number == 2:
            start,end = 3,6
        elif cycle_number == 3:
            start,end =6,7
        else :
            raise Exception("Incorrect cycle number is passed")


        job_ids_str = ', '.join(str(self.backup_job_list[i].job_id) for i in range(start, end))

        query = f"UPDATE JMBkpStats SET servStartDate = servStartDate - 3 * 86400, " \
                f"servEndDate = servEndDate - 3 * 86400 " \
                f"WHERE jobId IN ({job_ids_str})"
        self.log.info("Query => %s", query)
        self.mm_helper.execute_update_query(query, db_password=self.sql_password, db_user="sqladmin_cv")
        self.log.info("Update succeeded")


    def run_backups(self,subclient_obj):
        """
         Run backup jobs
         args:
            subclient object (object) -- object of subclient
        """

        for i in range (1,4):
            job_type= "FULL"
            time.sleep(30)
            self.create_content(0.2)
            self.log.info("Starting %s backup on subclient %s",job_type, subclient_obj.name)
            self.backup_job_list.append(subclient_obj.backup(job_type))
            self.log.info(f"Backup jobid submitted is :: {self.backup_job_list[-1].job_id}")
            if not self.backup_job_list[-1].wait_for_completion():
                raise Exception("Failed to run backup job with error:{0}".format(self.backup_job_list[-1].delay_reason))
            self.log.info("Backup job [%s] on subclient [%s] completed", self.backup_job_list[-1].job_id,
                      subclient_obj.name)
            if i==3:
                break
            for j in range (1,3):
                job_type = "Incremental"
                time.sleep(30)
                self.create_content(0.2)
                self.log.info("Starting %s backup on subclient %s", job_type, subclient_obj.name)
                self.backup_job_list.append(subclient_obj.backup(job_type))
                self.log.info(f"Backup jobid submitted is :: %s", self.backup_job_list[-1].job_id)
                if not self.backup_job_list[-1].wait_for_completion():
                    raise Exception("Failed to run backup job with error:{0}".format(self.backup_job_list[-1].delay_reason))
                self.log.info("Backup job [%s] on subclient [%s] completed", self.backup_job_list[-1].job_id,
                          subclient_obj.name)





    def clean_test_environment(self):
        """
        Clean up test environment
        """
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.client_machine_obj.remove_directory(self.content_path)
            self.log.info("Deleted the Content Directory.")
        else:
            self.log.info("Content directory does not exist.")
        try:
            self.log.info("Deleting BackupSet")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
        except Exception as excp:
            self.log.info("***Failure in deleting backupset during cleanup - %s "
                          "Treating as soft failure as backupset will be reused***", str(excp))
        try:
            self.log.info("Deleting Storage Policy")
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
        except Exception as excp:
            self.log.info("***Failure in deleting storage policy during cleanup. "
                          "Treating as soft failure as storage policy will be reused***")

        try:
            self.log.info("Cleaning up storage pool - [%s]", self.storage_pool_name)
            if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name}"):
                self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name}")
                self.commcell.storage_policies.delete(f"{self.storage_pool_name}")
        except Exception as excp:
            self.log.info("***Failure in deleting storage pool during cleanup. "
                          "Treating as soft failure as storage pool will be reused***")
        try:
            self.log.info("Cleaning up storage pool - [%s]", self.storage_pool_name_sec)
            if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name_sec}"):
                self.log.info("Deleting Storage Pool for sec copy - [%s]", f"{self.storage_pool_name_sec}")
                self.commcell.storage_policies.delete(f"{self.storage_pool_name_sec}")
        except Exception as excp:
            self.log.info("***Failure in deleting storage pool during cleanup. "
                          "Treating as soft failure as storage pool will be reused***")


    def validate_softaging_on_copy(self,Job,CopyId):
        """
        Args:
            Job (object) -- backup job object
            Copyid (int) -- copy id for which copy we want to check job is aged
        Returns:
              flag (int) -- soft aged flag 0 or 65536
        """

        query=f"select distinct(disabled&65536) from jmjobdatastats where jobid = {format(Job.job_id)} and archgrpcopyid = {CopyId}"
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        self.log.info(f"result of above query is : {self.csdb.fetch_all_rows()}")
        if len(self.csdb.fetch_all_rows()) != 1:
            raise Exception("Multiple values for disable flag for same jobid ")
        flag = int(self.csdb.fetch_one_row()[0])
        self.log.info("query result is ==> %s", flag)
        if flag == 65536:
            self.log.info("Job is soft aged on copy ,verifying if agedtime is set")
            query = f"select distinct(agedtime) from jmjobdatastats where jobid = {format(Job.job_id)} and archgrpcopyid = {CopyId}"
            self.log.info("Query => %s", query)
            self.csdb.execute(query)
            agedtime = int(self.csdb.fetch_one_row()[0])
            self.log.info(f"Agedtime is : {agedtime}")
            if agedtime == 0:
                raise Exception(f"Agedtime is not set correctly for Job Id {format(Job.job_id)} in jmjobdatastats table during soft aging ")
            else :
                return flag
        return flag

    def validate_softaging_on_job(self,Job):
        """
        Args:
            Job (object) : backup job object

        Returns:
            attribute (int) : soft aged flag set at job level in jmbkpstats 0,2305843009213693952
        """
        jobid = format(Job.job_id)
        query = f"select BkpAttributesEx & 0x2000000000000000 from jmbkpstats where jobid = {jobid}"
        self.log.info("Query => %s", query)
        self.csdb.execute(query)
        attribute = int(self.csdb.fetch_one_row()[0])
        self.log.info("query result is ==> %s", attribute)
        return attribute

    def perform_validation(self,joblist,expected_flags,copyid):
        """
        Args:
            joblist (list) --  list of jobs on which we want to do validations
            expected flags (list)  --  list [0,0,0] or [65536,65536,65536]
            copyid (int)  --   copyid on which we want to check the flags

        Returns:
            flags (Boolean) -- True or False

        """
        flags=[self.validate_softaging_on_copy(job, copyid) for job in joblist]
        self.log.info(f"flag value is :: {flags}")
        if flags == expected_flags:
            return True
        else:
            return False


    def run(self):
        """Run function of this test case"""
        try:
            self.clean_test_environment()
            self.create_resources()

            # Run 2 cycles F11,I11,I12 ,F22,I21,I22 ,F3
            self.run_backups(self.subclient_obj)

            # Moving date behind by 3 days for jobs in 1st cycle

            self.update_start_end_date(1)
            self.log.info("cyclenumber 1 jobs updated")

            aging_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                             storage_policy_name=self.storage_policy_name,
                                                             is_granular=True, include_all_clients=True)
            aging_job.wait_for_completion()

            #check if jobs soft aged job on copy

            if self.perform_validation(self.backup_job_list[0:3], [0,0,0],self.primary_copy.copy_id):
                self.log.info("Pass:jobs are not soft aged even when days retention are met as they are not copied.")
            else:
                raise Exception("Incorrect value for soft age flag for first cycle")

            #Run Auxcopy Job

            auxcopy_job = self.sp_obj.run_aux_copy()
            self.log.info(f"Waiting for AuxCopy job {auxcopy_job.job_id} to complete")
            if not auxcopy_job.wait_for_completion():
                raise Exception(f"AuxCopy job {auxcopy_job.job_id} failed with JPR: {auxcopy_job.delay_reason}")
            self.log.info("AuxCopy Job %s completed", auxcopy_job.job_id)

            aging_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                             storage_policy_name=self.storage_policy_name,
                                                             is_granular=True, include_all_clients=True)
            aging_job.wait_for_completion()
            self.log.info("Checking if soft aging happened after auxcopy job")

            # check if jobs soft aged job on pri copy after auxcopy

            if self.perform_validation(self.backup_job_list[0:3], [65536, 65536, 65536], self.primary_copy.copy_id):
                self.log.info("Pass:jobs are Soft aged as days retention are met and they are copied.")
                job_attribute = self.validate_softaging_on_job(self.backup_job_list[0])
                if job_attribute != 0:
                    raise Exception("Job is marked soft aged even when not aged on sec copy")
            else:
                raise Exception("Incorrect value for soft age flag for first cycle after auxcopy job is run")

            #move date behind by another 3 days for jobs in cycle1 to soft age jobs on sec copy
            self.update_start_end_date(1)

            # Disable DA on sec copy

            self.sec_copy._copy_properties['retentionRules']['retentionFlags']['enableDataAging'] = 0
            self.sec_copy._set_copy_properties()

            #Run DA job

            aging_job = self.mm_helper.submit_data_aging_job(copy_name='sec_copy',
                                                             storage_policy_name=self.storage_policy_name,
                                                             is_granular=True, include_all_clients=True)
            aging_job.wait_for_completion()
            self.log.info("Checking if soft aging happened after disabling DA on copy")

            #perform validations

            if self.perform_validation(self.backup_job_list[0:3], [0, 0, 0], self.sec_copy.copy_id):
                self.log.info("Pass:jobs are not soft aged on sec copy as DA is disabled.")
                job_attribute = self.validate_softaging_on_job(self.backup_job_list[0])
                if job_attribute != 0:
                    raise Exception("Job status is marked soft aged even when not aged on sec copy")
            else:
                raise Exception("Incorrect value for first cycle on sec copy when DA disabled on sec copy")

            # Enable DA on sec copy

            self.sec_copy._copy_properties['retentionRules']['retentionFlags']['enableDataAging'] = 1
            self.sec_copy._set_copy_properties()

            # Run DA job couple of times

            for i in range (1,3):
                aging_job = self.mm_helper.submit_data_aging_job(copy_name='sec_copy',
                                                             storage_policy_name=self.storage_policy_name,
                                                             is_granular=True, include_all_clients=True)
                aging_job.wait_for_completion()

            if self.perform_validation(self.backup_job_list[0:3], [65536, 65536, 65536], self.sec_copy.copy_id):
                self.log.info("Pass:jobs are soft aged on copy as DA is enabled")
                job_attribute = self.validate_softaging_on_job(self.backup_job_list[0])
                if job_attribute == 0:
                    raise Exception("Job status is not marked soft aged even when soft aged on sec copy")
                else:
                    self.log.info("Pass:Job is marked soft aged in jmbkpstats table.")
            else:
                raise Exception("Incorrect value for soft age flag for first cycle after enabling DA on sec copy")

            #disable DA on client
            self.client.disable_data_aging()
            self.log.info("disabled DA on client")

            #move start end time for 2nd cycle by 3 days
            self.update_start_end_date(2)

            aging_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                             storage_policy_name=self.storage_policy_name,
                                                             is_granular=True, include_all_clients=True)
            aging_job.wait_for_completion()

            # check if jobs soft aged job on copy

            if self.perform_validation(self.backup_job_list[3:6], [0, 0, 0], self.primary_copy.copy_id):
                self.log.info("Jobs are not soft aged even when days retention are met as DA is disabled on client")
                self.log.info("PASS:All validations have passed")
            else:
                raise Exception("Incorrect value for soft age flag for second cycle when DA is disabled on Client")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        # Tear down function of this test case
        try:
            self.log.info("Enabling DA on client")
            self.client.enable_data_aging()
            self.clean_test_environment()
        except Exception as exp:
            self.log.error("Cleanup failed, Please check the setup manually - [%s]", str(exp))