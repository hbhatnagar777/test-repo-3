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
    __init__()              --  initialize TestCase class
    setup()                 --  setup function of this test case
    create_resources()      --  creates required resources
    do_initial_check()      --  Do checking of defrag option and setup mmconfig params
    perform_defrag_tuning() --  Update MP and Archgroup to mimic HSX
    run_backup()            --  run backup
    run_auxcopy()           --  run auxcopy
    update_schedule_info    --  gets information about defrag schedules and updates defaults
    update_freespace        --  Update free space on the MPs
    validate_defrag()       --  validate defrag phase numbers and status
    validate_logs()         --  validate the space reclaim percentage from logs
    revert_defaults()       --  change mmconfigs settings to default
    run()                   --  run function of this test case
    cleanup()               --  cleanup resources function of this test case
    tear_down()             --  tear down function
    tcinputs to be passed in JSON File --
    "64516": {
            "ClientName": "client name",
            "AgentName": "File System",
            "MediaAgent":"Media Agent",
            "SecondaryCopyMediaAgent":"Media Agent2",
            "SystemCreatedSchedulePolicyName" : eg. "System Created DDB Space Reclamation schedule policy"
			"SystemCreatedSchedulePolicyOptions" : eg.["Defrag"] or ["Defrag", "OCL"] Note: Defrag  value is mandatory
			}
            Optional values in Json:
                "MP" : path for primary MP
                "SecondaryCopyMP" : path for secondary MP
                "DDBPath": path where dedup store to be created [for linux MediaAgents,
                                        User must explicitly provide a
                                        dedup path that is inside a Logical Volume.
                                        (LVM support required for DDB)]
                "SecondaryCopyDDBPath": path where dedup store to be created for auxcopy [for linux MediaAgents,
                                        User must explicitly provide a
                                        dedup path that is inside a Logical Volume.
                                        (LVM support required for DDB)]
Steps:
1: Configure the environment: Create storage pool, storage policy, backup set and subclient
2: Do initial check of schedule policy from CSDB(make sure defrag option is present)
3: Set mmconfigs and mmmount path parameters to facilitate Defrag for system created schedule
4. Update the defrag schedule to run every 15 mins
5: Run backup
6. Run Auxcopy
7. Update free space percentage on mountpaths
8: Run Defrag via system created schedule policy
9: Do Defrag validations for Phase numbers
10: Do log file validation for defrag percentage
11: Repeat steps 8-10 for secondary pool
12: CleanUp the environment
"""
import time
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from Server.Scheduler.schedulepolicyhelper import SchedulePolicyHelper
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
        self.name = "Defrag on HSX using system created schedule policy"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgent": None,
            "SecondaryCopyMediaAgent": None,
            "SystemCreatedSchedulePolicyName": None,
            "SystemCreatedSchedulePolicyOptions": None,
        }
        self.utility = None
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.client_machine = None
        self.ddb_path = None
        self.copy1_ddb_path = None
        self.mount_path = None
        self.mount_path_2 = None
        self.content_path = None
        self.primary_ma_path = None
        self.secondary_ma_path = None
        self.subclient = None
        self.storage_policy = None
        self.subclient_name = None
        self.backupset_name = None
        self.bkpset_obj = None
        self.storage_policy_name = None
        self.storage_policy_copy1 = None
        self.storage_pool_name1 = None
        self.storage_pool_id1 = None
        self.gdsp1 = None
        self.storage_pool_name2 = None
        self.storage_pool_id2 = None
        self.gdsp2 = None
        self.copy1_name = None
        self.plan = None
        self.plan_name = None
        self.dedupe_helper = None
        self.is_user_defined_mp = False
        self.is_user_defined_copy_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_copy_dedup = False
        self.defrag_interval = 30
        self.defrag_min_days = 7
        self.vol_interval = 5
        self.vol_interval_min = 5
        self.schedule_policy = None
        self.sys_schedule_id = None
        self.user_schedule_id = None
        self.schedule_obj = None
        self.sys_created_name = None
        self.sys_created_options = []
        self.sys_defrag = False
        self.sys_ocl = False
        self.config_strings = None
    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs['MediaAgent'], self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        self.utility = OptionsSelector(self.commcell)
        suffix = round(time.time())
        client_drive = self.utility.get_drive(self.client_machine, 25600)
        self.content_path = self.client_machine.join_path(client_drive, f"TC_{self.id}_CONTENT")
        self.subclient_name = f"{self.id}_SC"
        self.backupset_name = f"{self.id}_BS"
        self.storage_pool_name1 = f"{self.id}_Pool1Primary_{self.tcinputs['MediaAgent']}"
        self.storage_pool_name2 = f"{self.id}_Pool2Secondary_{self.tcinputs['SecondaryCopyMediaAgent']}"
        self.copy1_name = f"{self.id}_Copy1"
        self.plan_name = f"PLAN_{self.id}_{self.tcinputs['MediaAgent']}_{self.tcinputs['SecondaryCopyMediaAgent']}"

        self.sys_created_name = self.tcinputs['SystemCreatedSchedulePolicyName']
        self.log.info(f"System Created Schedule Policy Name is  : [{self.sys_created_name}]")
        self.sys_created_options = self.tcinputs['SystemCreatedSchedulePolicyOptions']
        self.log.info(f"System Created Schedule Policy Options expected are : [{self.sys_created_options}]")
        # validation for system created schedule policy inputs
        for item in self.sys_created_options:
            if item == "Defrag":
                self.sys_defrag = True
            if item == "OCL":
                self.sys_ocl = True
        if self.sys_defrag is False and self.sys_ocl is False or self.sys_defrag is False:
            raise Exception(f"Incorrect System Options.At least one input is needed and Defrag needs to be provided")
        if self.tcinputs.get('MP'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('SecondaryCopyMP'):
            self.is_user_defined_copy_mp = True
        if self.tcinputs.get('DDBPath'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('SecondaryCopyDDBPath'):
            self.is_user_defined_copy_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.ma_machine_1.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
        if not self.is_user_defined_copy_dedup and "unix" in self.ma_machine_2.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            self.primary_ma_path = self.utility.get_drive(self.ma_machine_1, 25600)
        if not self.is_user_defined_copy_mp or not self.is_user_defined_copy_dedup:
            self.secondary_ma_path = self.utility.get_drive(self.ma_machine_2, 25600)

        if not self.is_user_defined_mp:
            self.mount_path = self.ma_machine_1.join_path(self.primary_ma_path, f"TC_{self.id}", f"MP1_{suffix}")
        else:
            self.log.info("custom mount_path supplied")
            self.mount_path = self.ma_machine_1.join_path(self.tcinputs["MP"], f"TC_{self.id}", f"MP1_{suffix}")

        if not self.is_user_defined_copy_mp:
            self.mount_path_2 = self.ma_machine_2.join_path(self.secondary_ma_path, f"TC_{self.id}", f"MP2_{suffix}")
        else:
            self.log.info("custom copy_mount_path supplied")
            self.mount_path_2 = self.ma_machine_2.join_path(self.tcinputs["SecondaryCopyMP"], f"TC_{self.id}", f"MP2_{suffix}")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.ma_machine_1.join_path(self.tcinputs["DDBPath"], f"TC_{self.id}", f"DDBprimary_{suffix}")
        else:
            self.ddb_path = self.ma_machine_1.join_path(self.primary_ma_path, f"TC_{self.id}", f"DDBprimary_{suffix}")

        if self.is_user_defined_copy_dedup:
            self.log.info("custom copy dedup path supplied")
            self.copy1_ddb_path = self.ma_machine_2.join_path(self.tcinputs["SecondaryCopyDDBPath"], f"TC_{self.id}", f"DDBcopy1_{suffix}")
        else:
            self.copy1_ddb_path = self.ma_machine_2.join_path(self.secondary_ma_path, f"TC_{self.id}", f"DDBcopy1_{suffix}")
        self.mm_helper = MMHelper(self)
        self.schedule_policy = SchedulePolicyHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        self.config_strings = ['Phase [4:1], Verify all chunks [0], DV Reg. flgs [0], Sfile Frag threshold 40%',
                               'Phase [4:1], Verify all chunks [0], DV Reg. flgs [0], Sfile Frag threshold 20%']
    def run_backup(self):
        """Runs Backup
        """
        self.log.info("Submitting Full Backup Job")
        backup_job = self.subclient.backup(backup_level='Full')
        self.log.info("Submitted Full Backup Job %s", backup_job.job_id)
        if backup_job.wait_for_completion():
            self.log.info("Backup Completed :Id - %s", backup_job.job_id)
        else:
            raise Exception(f"Backup job [{backup_job.job_id}] did not complete - [{backup_job.delay_reason}]")
    def run_auxcopy(self, copy_name):
        """Runs Auxcopy
                    Args:
                            copy_name    (str)  --   copy name on which auxcopy should run
                """
        self.log.info("Submitting AuxCopy job")
        aux_copy_job = self.plan.storage_policy.run_aux_copy(copy_name, use_scale=True)
        self.log.info("Submitted Auxcopy Job %s", aux_copy_job.job_id)
        if aux_copy_job.wait_for_completion():
            self.log.info("AuxCopy Completed :Id - %s", aux_copy_job.job_id)
        else:
            raise Exception(f"Auxcopy job [{aux_copy_job.job_id}] did not complete - [{aux_copy_job.delay_reason}]")
    def do_initial_check(self):
        """Do initial check of schedule policies and set values so that schedule policy runs every 15 mins"""
        # This query should return 0 rows when defrag option is correctly set.
        schedule_policy_query = "SELECT sto.optionId, sto.type, sto.value, ST.taskId, sto.subtaskId FROM \
                                TM_SubTaskOptions sto INNER JOIN TM_SubTask ST WITH (READUNCOMMITTED) \
                                ON ST.subtaskId = sto.subTaskId WHERE optionId = 1658461134 AND \
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
        mmconfig_query2 = "select value,nmin from mmconfigs where name like 'MMS2_CONFIG_CHECKTWEAK_MPDEFRAGJOBSUBMITONSTORE_INTERVAL_DAYS'"
        self.log.info(f"Query is : [{mmconfig_query2}]")
        self.csdb.execute(mmconfig_query2)
        result = self.csdb.fetch_one_row()
        self.log.info(f"Query result is : {result}")
        self.defrag_interval = int(result[0])
        self.defrag_min_days = int(result[1])
        mmconfig_query2 = "select value,nmin from mmconfigs where name like 'MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN'"
        self.log.info(f"Query is : [{mmconfig_query2}]")
        self.csdb.execute(mmconfig_query2)
        result = self.csdb.fetch_one_row()
        self.log.info(f"Query result is : {result}")
        self.vol_interval = int(result[0])
        self.vol_interval_min = int(result[1])
        # Change the values so that system created defrag job launches. Without altering these system shedule won't launch.
        # Min interval in days it should check(min we can set is 1 day)
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_CHECKTWEAK_MPDEFRAGJOBSUBMITONSTORE_INTERVAL_DAYS', 1, 1)
        # update MMconfigs to do space check interval in minutes to 60mins.
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', self.vol_interval_min, 60)
        # restart MM services on CS
        self.mm_helper.restart_mm_service()
    def update_schedule_info(self):
        """
              This function updates schedule run times
        """
        self.schedule_policy.schedule_policy_obj = self.commcell.schedule_policies.get(self.sys_created_name)
        row = self.schedule_policy.schedule_policy_obj.all_schedules
        self.log.info(self.schedule_policy.schedule_policy_obj.all_schedules)
        self.sys_schedule_id = row[0]['schedule_id']
        self.log.info(self.sys_schedule_id)
        # First update the system created schedule to run every 15 mins
        query = f"update TM_Pattern set freq_type=4, freq_interval=1, freq_subday_interval=900, active_start_time=0, active_end_time = 86340" \
                f"where patternId = (select patternid from TM_PatternAssoc where subtaskid= {self.sys_schedule_id})"
        self.log.info("Update system created schedule to run every 15 mins")
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)
        # Delete the old run_time so that next run time should be in the next 15 mins.
        query = f"DELETE FROM TM_RunTime WHERE patternid = " \
                f"(select patternid from TM_PatternAssoc where subtaskid= {self.sys_schedule_id}) AND processed = 0"
        self.log.info("Delete the old run time so that next run time should be in the next 15 mins")
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)
    def perform_defrag_tuning(self, storage_pool_name, archgroupid):
        """
        This function updates MP and archgroup attributes to mimic HSX
         args:
            storage_pool_name (str) -- Storage pool name
            archgroupid (int)  -- storage pool id
        """
        self.log.info("Updating MMMountpath to mimic HSX.")
        mountpath_attributes = "16384 "
        query = f"update MMMountpath set attribute = {mountpath_attributes} where mountpathid in (" \
                f"select mountpathid from MMMountpath where libraryid in (" \
                f"select libraryid from MMLibrary where aliasname = '{storage_pool_name}'))"
        self.log.info(f"QUERY is : [{query}]")
        self.utility.update_commserve_db(query)
        self.log.info("Updating archgroup to mimic HSX.")
        query = f"update archgroup set flags = flags | 33554432 where id =  '{archgroupid}'"
        self.log.info(f"QUERY is : [{query}]")
        self.utility.update_commserve_db(query)
    def update_freespace(self, storage_pool_name, counter):
        """
        This function updates the free space on the MPs so that defrag launches with level 3 and 4 based on free space
        args:
            storage_pool_name (str) -- Storage pool name
            counter (int)  -- counter to specify whether it is pool1 or 2
        """
        # get the capacity first
        query = f"select totalspaceMB,MediaSideID,freebytesMB from MMMediaSide where MediaSideID in " \
                f"(select mediasideid from mmmountpath where mountpathid in (" \
                f"select mountpathid from MMMountpath where libraryid in (" \
                f"select libraryid from MMLibrary where aliasname = '{storage_pool_name}')))"
        self.log.info(f"Query is : [{query}]")
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info(f"Query result is : {result}")
        totalspaceMB = int(result[0])
        mediasideid = int(result[1])
        freebytesMB = int(result[2])
        self.log.info(f"Current free space is {freebytesMB} and Total size is {totalspaceMB}")
        if counter == 1:
            self.log.info(f"Get 40% of totalspaceMB so that defrag launches with 40% threshold (level 3)")
            val1 = (40/100) * totalspaceMB
        else:
            self.log.info(f"Get 20% of totalspaceMB so that defrag launches with 20% threshold (level 4)")
            val1 = (20 / 100) * totalspaceMB
        self.log.info(f"free space is : {round(val1)}")
        # update mmmediaside to update the free space.
        self.log.info(f"Update mmmediaside to update the free space so that defrag launches with level 3 or level 4")
        query = f"update MMMediaSide set freebytesMB = {round(val1)} where mediasideid= {mediasideid}"
        self.log.info(f"QUERY is : [{query}]")
        self.utility.update_commserve_db(query)
        self.log.info(f"Updated free space for storage pool {storage_pool_name} to {round(val1)} MB ")
    def validate_defrag(self, storage_pool_id):
        """ Validate Defrag flags from CSDB
            args:
                storage_pool_id (int) -- Storage pool ID
            return:
                jobid (int)  -- jobid of defrag job
        """
        # check if defrag job has started or not - poll every 5 mins for 9 times(max 45 mins).
        # we will have to get the archgrpid
        schedule_id = self.sys_schedule_id
        for counter in range(1, 10):
            query = f"select jobid,status from JMAdminJobStatsTable where optype=31 and " \
                    f"archgrpid = {storage_pool_id} and subtaskid= {schedule_id} order by jobid desc"
            self.log.info(f"Query is : [{query}]")
            self.csdb.execute(query)
            result = self.csdb.fetch_one_row()
            self.log.info(f"Query result is : [{result}]")
            if result[0] == '':
                if counter == 10:
                    raise Exception(f"Defrag job did not start.Volume size updates might have run and freespace might have been updated")
                else:
                    self.log.info("Defrag did not run or complete yet. Wait for another 5 mins")
                    time.sleep(300)
            else:
                jobid = int(result[0])
                status = int(result[1])
                if status != 1:
                    raise Exception(f"Defrag job status is not complete. It must have failed. Status is : %s ", status)
                else:
                    self.log.info("Defrag job has completed. Will proceed with phase number vaildations")
                    query = f"select phasenum from JMAdminJobAttemptStatsTable where jobid in ({jobid}) order by phasenum"
                    self.log.info(f"Query is : [{query}]")
                    self.csdb.execute(query)
                    result = self.csdb.fetch_all_rows()
                    self.log.info(f"Query result is : [{result}]")
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
                            return jobid
                        else:
                            raise Exception("Case2: Defrag and OCL (4,3) phases were not passed by scheduled job")
                    if self.sys_defrag is True and self.sys_ocl is False:
                        self.log.info(f"Only Defrag is expected")
                        if int(result[1][0]) == 4:
                            self.log.info("Case3: Defrag phase (4) was passed by scheduled job. PASSED")
                            return jobid
                        else:
                            raise Exception("Case3: Defrag phase (4) was not passed by scheduled job")
                    if self.sys_defrag is False and self.sys_ocl is True:
                        raise Exception(f"Only OCL is not expected from system created schedule policy")
                break
    def validate_logs(self, jobid, ma, pattern):
        """ Validate Defrag flags from CSDB whether it ran with level 3 or 4
            args:
                jobid (int) -- Defrag jobid
                ma (str)    -- Ma on which to check logs
                pattern(str) -- pattern to match from log files
        """
        log_file = 'ScalableDDBVerf.log'
        self.log.info('*** Fragmentation percent validation ***')
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            ma, log_file,
            pattern, jobid)
        if matched_line:
            self.log.info(f'Fragmentation percent matched for jobid {jobid}')
            self.log.error('Success  Result : Passed')
        else:
            self.log.info('Error Result : Failed')
            self.status = constants.FAILED
    def revert_defaults(self):
        """" Changing deafult values of mmconfigs and Defrag schedules"""
        if self.defrag_min_days < 7 or self.defrag_interval < 30:
            self.defrag_interval = 30
            self.defrag_min_days = 7
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_CHECKTWEAK_MPDEFRAGJOBSUBMITONSTORE_INTERVAL_DAYS',
                                             self.defrag_min_days, self.defrag_interval)
        if self.vol_interval < 5 or self.vol_interval_min < 5:
            self.vol_interval = 5
            self.vol_interval_min = 5
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN',
                                             self.vol_interval_min, self.vol_interval)
        # Default DDB system created schedule is daily with starttime as 11am and endtime as 11:59pm
        query = f"update TM_Pattern set freq_type=4, freq_interval=1, freq_subday_interval=0, active_start_time=39600, active_end_time=86340" \
                f"where patternId = (select patternid from TM_PatternAssoc where subtaskid= {self.sys_schedule_id})"
        self.log.info("Revert system created schedule to every say at 11am")
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)
        # Delete the old run_times for system created schedule so that it picks up the next run time correctly
        query = f"DELETE FROM TM_RunTime WHERE patternid = " \
                f"(select patternid from TM_PatternAssoc where subtaskid= {self.sys_schedule_id}) AND processed = 0"
        self.log.info("Delete the old run time so that next run time should be in the next 1 day")
        self.log.info(f"Query is : [{query}]")
        self.utility.update_commserve_db(query)
    def create_resources(self):
        """Create resources needed by the Test Case"""
        self.cleanup()
        # Configure the environment
        # Creating a storage pool1 and associate to SP
        self.log.info(f"Configuring Storage Pool for Primary {self.storage_pool_name1}")
        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name1):
            self.gdsp1 = self.commcell.storage_pools.add(self.storage_pool_name1, self.mount_path,
                                                         self.tcinputs['MediaAgent'],
                                                         [self.tcinputs['MediaAgent']]*2, [self.ddb_path, self.ddb_path])
        else:
            self.gdsp1 = self.commcell.storage_pools.get(self.storage_pool_name1)
        self.log.info("Done creating a storage pool for Primary")
        self.commcell.disk_libraries.refresh()
        if not self.commcell.plans.has_plan(self.plan_name):
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.storage_pool_name1)
            self.log.info(f"Plan [{self.plan_name}] created")
        else:
            self.plan = self.commcell.plans.get(self.plan_name)

        self.plan.schedule_policies['data'].disable()

        self.storage_pool_id1 = self.gdsp1.storage_pool_id
        self.log.info(f"Primary Storage Pool ID is {self.storage_pool_id1}")
        # Create storage pool for secondary copy
        self.log.info(f"Configuring Secondary Storage Pool {self.storage_pool_name2}")
        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name2):
            self.gdsp2 = self.commcell.storage_pools.add(self.storage_pool_name2, self.mount_path_2,
                                                         self.tcinputs['SecondaryCopyMediaAgent'],
                                                         [self.tcinputs['SecondaryCopyMediaAgent']]*2,
                                                         [self.copy1_ddb_path, self.copy1_ddb_path])
        else:
            self.gdsp2 = self.commcell.storage_pools.get(self.storage_pool_name2)
        self.storage_pool_id2 = self.gdsp2.storage_pool_id
        self.log.info(f"Secondary Storage Pool ID is {self.storage_pool_id2}")
        self.log.info("Done creating a storage pool for secondary copy")
        self.commcell.disk_libraries.refresh()
        self.commcell.storage_policies.refresh()
        # Create secondary copy1
        self.log.info("Adding Secondary Copy to Plan")
        self.plan.add_storage_copy(self.copy1_name, self.storage_pool_name2)
       
        # Remove Association with System Created AutoCopy Schedule
        self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.copy1_name)

        # Configure backupset, subclients and create content
        self.log.info(f"Configuring Backupset - {self.backupset_name}")
        self.bkpset_obj = self.mm_helper.configure_backupset(self.backupset_name)
        # Create subclient
        self.subclient = self.bkpset_obj.subclients.add(self.subclient_name)
        self.subclient.plan = [self.plan, [self.content_path]]
        self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path, 1.0)

    def run(self):
        """Run Function of This Case"""
        try:
            self.create_resources()
            self.do_initial_check()
            # mimic hsx
            self.perform_defrag_tuning(self.storage_pool_name1, self.storage_pool_id1)
            self.perform_defrag_tuning(self.storage_pool_name2, self.storage_pool_id2)
            self.run_backup()
            self.run_auxcopy(self.copy1_name)
            self.update_schedule_info()
            self.update_freespace(self.storage_pool_name1, 1)
            self.update_freespace(self.storage_pool_name2, 2)
            self.log.info(f"Wait for Defrag job by Scheduler for storage pool1")
            jobid = self.validate_defrag(self.storage_pool_id1)
            self.validate_logs(jobid, self.tcinputs['MediaAgent'], self.config_strings[0])
            self.log.info(f"Wait for Defrag job by Scheduler for storage pool2")
            jobid = self.validate_defrag(self.storage_pool_id2)
            self.validate_logs(jobid, self.tcinputs['SecondaryCopyMediaAgent'], self.config_strings[1])
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error("Exception Raised: %s", str(exe))
    def cleanup(self):
        """Cleanup Function of this Case"""
        try:
            # CleanUp the environment
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info(f"Deleting content from {self.content_path}")
                self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Reassociating all subclients to None")
                self.plan.storage_policy.reassociate_all_subclients()
                self.log.info(f"Deleting plan {self.plan_name}")
                self.commcell.plans.delete(self.plan_name)
            if self.commcell.storage_pools.has_storage_pool(f"{self.storage_pool_name1}"):
                self.log.info(f"Deleting Primary Storage Pool {self.storage_pool_name1}")
                self.commcell.storage_pools.delete(f"{self.storage_pool_name1}")
            if self.commcell.storage_pools.has_storage_pool(f"{self.storage_pool_name2}"):
                self.log.info(f"Deleting Secondary Storage Pool {self.storage_pool_name2}")
                self.commcell.storage_pools.delete(f"{self.storage_pool_name2}")
            self.log.info("Refresh libraries")
            self.commcell.disk_libraries.refresh()
            self.log.info("Refresh Storage Pools")
            self.commcell.storage_pools.refresh()
        except Exception as exe:
            self.log.warning(f"ERROR in Cleanup. Might need to Cleanup Manually: {str(exe)}")
    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info("Test Case PASSED.")
        else:
            self.log.warning("Test Case FAILED.")
        self.revert_defaults()
        self.cleanup()
