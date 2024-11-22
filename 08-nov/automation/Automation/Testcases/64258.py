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
    create_resources() -- creates required resources
    do_initial_check() -- Do checking of defrag option and setup mmconfig params
    perform_defrag_tuning()    --  Update MP to not support drill holes
    update_schedule_info()    --  gets information about defrag schedules and updates defaults
    run_backup()  -- run backup
    run_defrag() -- run defag
    validate_defrag() -- validate defrag phase numbers and status
    revert_defaults()   -- change mmconfigs settings to default
    run()           --  run function of this test case
    cleanup()     --  cleanup resources function of this test case
    tear_down()     -- tear down function
    tcinputs to be passed in JSON File --
    "64258": {
                "ClientName": "client name",
                "AgentName": "File System",
                "MediaAgent":"Media Agent",
                "SystemCreatedSchedulePolicyName" : eg. "System Created DDB Space Reclamation schedule policy"  - system create schedule policy name
				"SystemCreatedSchedulePolicyOptions" : eg. ["Defrag"] or ["Defrag", "OCL"],  -- List of Options. Note: Defrag  value is mandatory.
				"UserCreatedSchedulePolicyName" : " e.g. User Created DDB Space Reclaim",   -- User Created DDB space reclaimation schedule policy name
				"UserCreatedSchedulePolicyOptions" : e.g ["Defrag","OCL"] or ["Defrag"] or ["OCL"]	   -- List of options
            }
            Optional values in Json:
                "MP" : path for MP
                "DDBPath": path where dedup store to be created [for linux MediaAgents,
                                        User must explicitly provide a
                                        dedup path that is inside a Logical Volume.
                                        (LVM support required for DDB)]
Steps:
1: Configure the environment: Create storage pool, storage policy, backup set and subclient
2: Do initial check of schedule policy from CSDB(make sure defrag option is present)
3: Set mmconfigs and mmmount path parameters to facilitate Defrag for system created schedule - watermark and drill holes
4. Update the defrag schedules to run every 30 mins and 2 hours from now for system and user created respectively
5: Run backup
6: Run Defrag via system created schedule policy
7: Do Defarg validations for Phase numbers
8: Repeat steps 5,6,7 for User Created Schedule Policy
9: CleanUp the environment
"""
import time
from datetime import datetime
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from Server.Scheduler.schedulepolicyhelper import SchedulePolicyHelper
from cvpysdk.schedules import Schedule
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
        self.name = "Defrag using system and user created schedule policy"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgent": None,
            "SystemCreatedSchedulePolicyName": None,
            "SystemCreatedSchedulePolicyOptions": None,
            "UserCreatedSchedulePolicyName": None,
            "UserCreatedSchedulePolicyOptions": None
        }
        self.utility = None
        self.mm_helper = None
        self.ma_machine_1 = None
        self.client_machine = None
        self.ddb_path = None
        self.mount_path = None
        self.client_path = None
        self.content_path = None
        self.primary_ma_path = None
        self.subclient = None
        self.storage_policy = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_policy_name = None
        self.storage_pool_name1 = None
        self.storage_pool_id1 = None
        self.gdsp1 = None
        self.dedupe_helper = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.low_watermark = 50
        self.low_watermark_nmax = 95
        self.defrag_interval = 30
        self.defrag_min_days = 7
        self.schedule_policy = None
        self.sys_schedule_id = None
        self.user_schedule_id = None
        self.schedule_obj = None
        self.sys_created_name = None
        self.sys_created_options = []
        self.user_created_name = None
        self.user_created_options = []
        self.sys_defrag = False
        self.sys_ocl = False
        self.user_defrag = False
        self.user_ocl = False

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs['MediaAgent'], self.commcell)
        self.utility = OptionsSelector(self.commcell)
        client_drive = self.utility.get_drive(self.client_machine, 25600)
        self.client_path = self.client_machine.join_path(client_drive, 'test_' + str(self.id))
        self.content_path = self.client_machine.join_path(self.client_path, 'content')
        self.subclient_name = f"{self.id}_SC"
        self.backupset_name = f"{self.id}_BS"
        self.storage_policy_name = f"{self.id}_SP_{self.tcinputs['MediaAgent']}"
        self.storage_pool_name1 = f"{self.id}_Pool1Primary_{self.tcinputs['MediaAgent']}"
        self.sys_created_name = self.tcinputs['SystemCreatedSchedulePolicyName']
        self.log.info(f"System Created Schedule Policy Name is  : [{self.sys_created_name}]")
        self.sys_created_options = self.tcinputs['SystemCreatedSchedulePolicyOptions']
        self.log.info(f"System Created Schedule Policy Options expected are : [{self.sys_created_options}]")
        self.user_created_name = self.tcinputs['UserCreatedSchedulePolicyName']
        self.log.info(f"User Created Schedule Policy Name is  : [{self.user_created_name}]")
        self.user_created_options = self.tcinputs['UserCreatedSchedulePolicyOptions']
        self.log.info(f"User Created Schedule Policy Options expected are : [{self.user_created_options}]")
        # validation for system created schedule policy inputs
        for item in self.sys_created_options:
            if item == "Defrag":
                self.sys_defrag = True
            if item == "OCL":
                self.sys_ocl = True
        if self.sys_defrag is False and self.sys_ocl is False or self.sys_defrag is False:
            raise Exception(f"Incorrect System Options provided. Alteast one input is needed or Defrag needs to be provided")
        # validation for user created schedule policy inputs
        for item in self.user_created_options:
            if item == "Defrag":
                self.user_defrag = True
            if item == "OCL":
                self.user_ocl = True
        if self.user_defrag is False and self.user_ocl is False:
            raise Exception(f"Incorrect User Options provided. Alteast one input is needed")
        if self.tcinputs.get('MP'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('DDBPath'):
            self.is_user_defined_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.ma_machine_1.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.ma_machine_1, 25600)
            self.primary_ma_path = self.ma_machine_1.join_path(ma_1_drive, 'testprimary_' + str(self.id))
        if not self.is_user_defined_mp:
            self.mount_path = self.ma_machine_1.join_path(self.primary_ma_path, 'MP1')
        else:
            self.log.info("custom mount_path supplied")
            self.mount_path = self.tcinputs['MP']
        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.tcinputs["DDBPath"]
        else:
            self.ddb_path = self.ma_machine_1.join_path(self.primary_ma_path, "DDBprimary")
        self.mm_helper = MMHelper(self)
        self.schedule_policy = SchedulePolicyHelper(self)
        self.dedupe_helper = DedupeHelper(self)
    def run_backup(self):
        """Runs Backup
        """
        self.log.info("Submitting Full Backup Job")
        backup_job = self.subclient.backup(backup_level='Full')
        if backup_job.wait_for_completion():
            self.log.info("Backup Completed :Id - %s", backup_job.job_id)
        else:
            raise Exception(f"Backup job [{backup_job.job_id}] did not complete - [{backup_job.delay_reason}]")
        return backup_job.job_id
    def do_initial_check(self):
        """Do initial check of schedule policies and set values so that schedule policy runs every 30 mins"""
        # This query should return 0 rows when defrag option is correctly set.
        schedule_policy_query = "SELECT 0, sto.optionId, sto.type, sto.value, ST.taskId, sto.subtaskId, 0, 99, 0  \
                                FROM TM_SubTaskOptions sto INNER JOIN TM_SubTask ST WITH (READUNCOMMITTED) ON ST.subtaskId = sto.subTaskId \
                                WHERE optionId = 1658461134 AND  \
                                NOT EXISTS (SELECT 1 FROM TM_JobOptions JO WHERE JO.optionId = sto.optionId \
                                and JO.subTaskId = sto.subTaskId) and sto.value = 1"
        self.log.info(f"Query is : [{schedule_policy_query}]")
        self.csdb.execute(schedule_policy_query)
        result = self.csdb.fetch_one_row()
        self.log.info(f"Query result is : [{result}]")
        if result[0] == '':
            self.log.info(f"Case1: Query returned 0 rows for schedule policy for defrag option: PASSED")
        else:
            raise Exception(f"Case1: Query returned rows > 0 for schedule policy for defrag option.This is not expected")
        # Get initial default values from the system to reset them later
        mmconfig_query1 = "select value, nmax from mmconfigs where name like 'MMS2_CONFIG_LOW_WATERMARK_PERC_TO_SUBMIT_DEFRAG_JOB'"
        self.log.info(f"Query is : [{mmconfig_query1}]")
        self.csdb.execute(mmconfig_query1)
        result = self.csdb.fetch_one_row()
        self.low_watermark = int(result[0])
        self.low_watermark_nmax = int(result[1])
        self.log.info(f"Query result is : {result}")
        mmconfig_query2 = "select value,nmin from mmconfigs where name like 'MMS2_CONFIG_CHECKTWEAK_MPDEFRAGJOBSUBMITONSTORE_INTERVAL_DAYS'"
        self.log.info(f"Query is : [{mmconfig_query2}]")
        self.csdb.execute(mmconfig_query2)
        result = self.csdb.fetch_one_row()
        self.defrag_interval = int(result[0])
        self.defrag_min_days = int(result[1])
        self.log.info(f"Query result is : {result}")
        # Change the values so that system created defrag job launches. Without altering these system shedule won't launch.
        # One is for free space on MP and the other is for min interval in days it should check(min we can set is 1 day)
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_LOW_WATERMARK_PERC_TO_SUBMIT_DEFRAG_JOB', 1, 99, nmax=99)
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_CHECKTWEAK_MPDEFRAGJOBSUBMITONSTORE_INTERVAL_DAYS', 1, 1)

    def perform_defrag_tuning(self):
        """
        This function updates MP attribute to turn off drill holes
        """
        self.log.info("Disabling drill holes on the mount path created in this TC.")
        mountpath_attributes = "149064"
        query = f"update MMMountpath set attribute = {mountpath_attributes} where mountpathid in (" \
                f"select mountpathid from MMMountpath where libraryid in (" \
                f"select libraryid from MMLibrary where aliasname = '{self.storage_pool_name1}'))"
        self.log.info(f"QUERY is : [{query}]")
        self.utility.update_commserve_db(query)
    def update_schedule_info(self, policy_name):
        """
              This function updates schedule run times
              Args:
                policy_name    (str)    --   Defrag Schedule policy name
        """
        self.schedule_policy.schedule_policy_obj = self.commcell.schedule_policies.get(policy_name)
        row = self.schedule_policy.schedule_policy_obj.all_schedules
        self.log.info(self.schedule_policy.schedule_policy_obj.all_schedules)
        if policy_name == self.sys_created_name:
            self.sys_schedule_id = row[0]['schedule_id']
            self.log.info(self.sys_schedule_id)
            # First update the system created schedule to run every 30 mins
            query = f"update TM_Pattern set freq_type=4, freq_interval=1, freq_subday_interval=1800, active_start_time=0, active_end_time = 86340" \
                f" where patternId = (select patternid from TM_PatternAssoc where subtaskid= {self.sys_schedule_id})"
            self.log.info("Update system created schedule to run every 30 mins")
            self.log.info(f"Query is : [{query}]")
            self.utility.update_commserve_db(query)
            # Delete the old run_time so that next run time should be in the next 30 mins.
            query = f"DELETE FROM TM_RunTime WHERE patternid = " \
                    f"(select patternid from TM_PatternAssoc where subtaskid= {self.sys_schedule_id}) AND processed = 0"
            self.log.info("Delete the old run time so that next run time should be in the next 30 mins")
            self.log.info(f"Query is : [{query}]")
            self.utility.update_commserve_db(query)
        if policy_name == self.user_created_name:
            self.user_schedule_id = row[0]['schedule_id']
            self.log.info(self.user_schedule_id)
            # First update the user created schedule to run every 1 day with start time > 2 hours from current time.
            # So that it doesn't interfere with system created schedule policy
            ts = datetime.now()
            ts = (ts.hour + 2) * 3600
            query = f"update TM_Pattern set freq_type=4, freq_interval=1, freq_subday_interval=0, active_start_time={ts}, active_end_time = 86340" \
                    f" where patternId = (select patternid from TM_PatternAssoc where subtaskid= {self.user_schedule_id})"
            self.log.info("Changing user created schedule to run every day with start time > 2 hours from current time")
            self.log.info(f"Query is : [{query}]")
            self.utility.update_commserve_db(query)
            # Delete the old run_time so that next run time of 1 day is picked.
            query = f"DELETE FROM TM_RunTime WHERE patternid = " \
                    f"(select patternid from TM_PatternAssoc where subtaskid= {self.user_schedule_id}) AND processed = 0"
            self.log.info("Delete the old run time so that next run time should be in the next 1 day")
            self.log.info(f"Query is : [{query}]")
            self.utility.update_commserve_db(query)
    def run_defrag(self, policy_name):
        """ Run Defrag via schedule policy
            args:
                policy name  (str) --- Defrag Schedule Policy name
        """
        if policy_name == self.user_created_name:
            # get schedule object to trigger run now for user created schedule
            self.schedule_obj = Schedule(self.commcell, schedule_id=self.user_schedule_id)
            self.log.info(f"Start Defrag job via : [{policy_name}] Now")
            self.schedule_obj.run_now()
        if policy_name == self.sys_created_name:
            # let the schedule run on its own
            self.log.info(f"Start Defrag job via schedule: [{policy_name}] by Scheduler")
    def validate_defrag(self, policy_type):
        """ Validate Defrag flags from CSDB
            args:
                policy_type (str) -- policy type where user or system
        """
        # check if defrag job has started or not - poll every 5 mins for 9 times(max 40 mins).
        # we will have to get the archgrpid
        schedule_id = None
        if policy_type == 'system':
            schedule_id = self.sys_schedule_id
        if policy_type == 'user':
            schedule_id = self.user_schedule_id
        for counter in range(1, 9):
            query = f"select jobid,status from JMAdminJobStatsTable where optype=31 and " \
                    f"archgrpid = {self.storage_pool_id1} and subtaskid= {schedule_id} order by jobid desc"
            self.log.info(f"Query is : [{query}]")
            self.csdb.execute(query)
            result = self.csdb.fetch_one_row()
            self.log.info(f"Query result is : [{result}]")
            if result[0] == '':
                self.log.info("Defrag did not run or complete yet. Wait for another 5 mins")
                time.sleep(300)
            else:
                jobid = int(result[0])
                status = int(result[1])
                if status != 1:
                    raise Exception(f"Defrag job status is not complete. It must have failed status is: %s", status)
                else:
                    self.log.info("Defrag job has completed. Will proceed with phase number vaildations")
                    query = f"select phasenum from JMAdminJobAttemptStatsTable where jobid={jobid} order by phasenum"
                    self.log.info(f"Query is : [{query}]")
                    self.csdb.execute(query)
                    result = self.csdb.fetch_all_rows()
                    self.log.info(f"Query result is : [{result}]")
                    if policy_type == 'system':
                        # get the system created options from self.sys_created_options
                        self.log.info(f"System Created Schedule Policy Options expected are:[{self.sys_created_options}]")
                        option_length = len(self.sys_created_options)
                        if len(result) != (option_length+1):
                            raise Exception("Total phases need to be min 2")
                        # 3 - OCL, 4 - Defrag
                        if self.sys_ocl is True and self.sys_defrag is True:
                            self.log.info(f"Defrag and OCL is expected")
                            if int(result[1][0]) == 3 and int(result[2][0]) == 4:
                                self.log.info("Case2: Defrag and OCL (4,3) phases were passed by scheduled job. PASSED")
                            else:
                                raise Exception("Case2: Defrag and OCL (4,3) phases were not passed by scheduled job")
                        if self.sys_defrag is True and self.sys_ocl is False:
                            self.log.info(f"Only Defrag is expected")
                            if int(result[1][0]) == 4:
                                self.log.info("Case3: Defrag phase (4) was passed by scheduled job. PASSED")
                            else:
                                raise Exception("Case3: Defrag phase (4) was not passed by scheduled job")
                        if self.sys_defrag is False and self.sys_ocl is True:
                            raise Exception(f"Only OCL is not expected from system created schedule policy")
                    if policy_type == 'user':
                        # get the user created options from self.user_created_options
                        self.log.info(f"User Created Schedule Policy Options expected are : [{self.user_created_options}]")
                        option_length = len(self.user_created_options)
                        if len(result) != (option_length+1):
                            raise Exception("Total phases need to be min 2")
                        # 3 - OCL, 4 - Defrag
                        if self.user_ocl is True and self.user_defrag is True:
                            self.log.info(f"Defrag and OCL is expected")
                            if int(result[1][0]) == 3 and int(result[2][0]) == 4:
                                self.log.info("Case4: Defrag and OCL (4,3) phases were passed by scheduled job. PASSED")
                            else:
                                raise Exception("Case4: Defrag and/or OCL (4,3) phase was not passed by scheduled job")
                        if self.user_defrag is True and self.user_ocl is False:
                            self.log.info(f"Only Defrag is expected")
                            if int(result[1][0]) == 4:
                                self.log.info("Case5: Defrag phase (4) was passed by scheduled job. PASSED")
                            else:
                                raise Exception("Case5: Defrag phase (4) was not passed by scheduled job")
                        if self.user_defrag is False and self.user_ocl is True:
                            self.log.info(f"Only OCL is expected")
                            if int(result[1][0]) == 3:
                                self.log.info("Case6: OCL phase (3) was passed by scheduled job. PASSED")
                            else:
                                raise Exception("Case6: OCL phase (3) was not passed by scheduled job")
                    break
    def revert_defaults(self):
        """" Changing deafult values of mmconfigs and Defrag schedules"""
        if self.low_watermark > 50 or self.low_watermark_nmax > 95:
            self.low_watermark = 50
            self.low_watermark_nmax = 95
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_LOW_WATERMARK_PERC_TO_SUBMIT_DEFRAG_JOB',1,
                                             self.low_watermark, nmax=self.low_watermark_nmax)
        if self.defrag_min_days < 7 or self.defrag_interval < 30:
            self.defrag_interval = 30
            self.defrag_min_days = 7
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_CHECKTWEAK_MPDEFRAGJOBSUBMITONSTORE_INTERVAL_DAYS',
                                             self.defrag_min_days, self.defrag_interval)
        # Default DDB system created schedule is daily with starttime as 11am and endtime as 11:59pm
        query = f"update TM_Pattern set freq_type=4, freq_interval=1, freq_subday_interval=0, active_start_time=39600, active_end_time=86340" \
                f"where patternId = (select patternid from TM_PatternAssoc where subtaskid= {self.sys_schedule_id})"
        self.log.info("Revert system created schedule to every say at 11am")
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)
        # User system created schedule is daily with starttime as 1pm and endtime as 11:59pm
        query = f"update TM_Pattern set freq_type=4, freq_interval=1, freq_subday_interval=0, active_start_time=46800, active_end_time=86340" \
                f"where patternId = (select patternid from TM_PatternAssoc where subtaskid= {self.user_schedule_id})"
        self.log.info("Revert user created schedule to every say at 1pm")
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)
        # Delete the old run_times for both system and user created schedules so that it picks up the next run time correctly
        query = f"DELETE FROM TM_RunTime WHERE patternid = " \
                f"(select patternid from TM_PatternAssoc where subtaskid= {self.sys_schedule_id}) AND processed = 0"
        self.log.info("Delete the old run time so that next run time should be in the next 1 day")
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)
        query = f"DELETE FROM TM_RunTime WHERE patternid = " \
                f"(select patternid from TM_PatternAssoc where subtaskid= {self.user_schedule_id}) AND processed = 0"
        self.log.info("Delete the old run time so that next run time should be in the next 1 day")
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)
    def create_resources(self):
        """Create resources needed by the Test Case"""
        self.cleanup()
        # Configure the environment
        # Creating a storage pool and associate to SP
        self.log.info("Configuring Storage Pool for Primary ==> %s", self.storage_pool_name1)
        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name1):
            self.gdsp1 = self.commcell.storage_pools.add(self.storage_pool_name1, self.mount_path,
                                                         self.tcinputs['MediaAgent'],
                                                         self.tcinputs['MediaAgent'], self.ddb_path)
        else:
            self.gdsp1 = self.commcell.storage_pools.get(self.storage_pool_name1)
        self.log.info("Done creating a storage pool for Primary")
        self.commcell.disk_libraries.refresh()
        self.log.info("Configuring Storage Policy ==> %s", self.storage_policy_name)
        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                     global_policy_name=self.storage_pool_name1)
        else:
            self.storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)
        self.storage_pool_id1 = self.gdsp1.storage_pool_id
        self.log.info("Storage Pool ID is ==> %s", self.storage_pool_id1)
        # Configure backupset, subclients and create content
        self.mm_helper.configure_backupset(self.backupset_name)
        self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.subclient_name,
                self.storage_policy_name,
                self.content_path,
                self.agent)
        self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 0.4)
    def run(self):
        """Run Function of This Case"""
        try:
            self.create_resources()
            self.do_initial_check()
            self.perform_defrag_tuning()
            self.update_schedule_info(self.sys_created_name)
            self.update_schedule_info(self.user_created_name)
            self.run_backup()
            self.run_defrag(self.sys_created_name)
            self.validate_defrag('system')
            # run another backup. Then run user created DDB space reclamation schedule.
            self.run_backup()
            self.run_defrag(self.user_created_name)
            self.validate_defrag('user')
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error("Exception Raised: %s", str(exe))
    def cleanup(self):
        """Cleanup Function of this Case"""
        try:
            # CleanUp the environment
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Deleting storage policy  %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name1}"):
                self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name1}")
                self.commcell.storage_policies.delete(f"{self.storage_pool_name1}")
            self.log.info("Refresh libraries")
            self.commcell.disk_libraries.refresh()
            self.log.info("Refresh Storage Policies")
            self.commcell.storage_policies.refresh()
        except Exception as exe:
            self.log.warning("ERROR in Cleanup. Might need to Cleanup Manually: %s", str(exe))
    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info("Test Case PASSED.")
        else:
            self.log.warning("Test Case FAILED.")
        self.revert_defaults()
        self.cleanup()
