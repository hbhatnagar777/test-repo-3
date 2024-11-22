# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    previous_run_clean_up() --  cleanup old entities

    create_resources()  --  create basic entities for case

    run_backup()   -- run a backup job

    prune_jobs()    -- prune the list of backup jobs

    run_data_aging()    --  run data aging job against primary copy

    extended_retention_validation() --  run validations for the supplied extended retention rule

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

JSON (doesnt need to be run on both OSs but should technically work on linux since its non-dedup):
    "53972": {
          "ClientName": "mmdedupe16",
          "AgentName": "File System",
          "MediaAgentName": "mmdedupe16",
          "SqlSaPassword": "Builder!12"
        }
Design Steps:
-set only 'last daily full' extended retention, to keep for 30 days, and day starts at midnight
-run 2 full backups (backup_jobs_day1[])
-set their time back 1 day
self.mm_helper.move_job_start_time(backup_jobs_day1, 1)
-run 1 more full backup
-run DA
-verify J1 is deleted, J2 is retained with extended retention last daily full (don’t care about J3, its only there to
satisfy J2 is not the active cycle)
-delete all jobs and run DA to clean slate
-update ext retention: set daily fulls to 1 day, 'last weekly full' extended retention to 30 days
run 2 full backups
-set their time back:
if its Thursday, move first backup back 8 days, and second backup back 7 days
d = datetime.date.today()
If d.weekday() == calendar.THURSDAY:
-otherwise, move first backup back 7 days, second backup back 6 days.
-run one more full backup
-run DA
-verify j1 is deleted, second backup is retained with weekly retention flag
-delete all jobs and run DA to clean slate
-update ext retention: set daily fulls 1 day, weekly fulls 2 days, 'last monthly full' extended retention to 90 days,
the month starts on first day of the month
-run 2 full backups
-set their time back:
-first backup sets back to first day of the previous month
-second backup sets back to 8th day of the previous month
-if moving the date back 23 days keeps the date in the same current month (meaning it’s the last week of the
current month), then move first backup back 37 days, and second backup 30 days
If 23dayold_datetime.month == current month:
self.mm_helper.move_job_start_time(J1, 37)
self.mm_helper.move_job_start_time(J2, 30)
Else:
self.mm_helper.move_job_start_time(J1, 30)
self.mm_helper.move_job_start_time(J1, 23)
-run one more full backup
-run DA
-verify J1 is deleted, J2 is kept with retention flag of monthly full
-tear down

"""
import datetime
import time
import calendar
from calendar import monthrange
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Extended retention basic case"
        self.tcinputs = {
            "MediaAgentName": None,
            "SqlSaPassword": None
        }
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.opt_selector = None
        self.storage_pool = None
        self.storage_pool_name = None
        self.client_machine = None
        self.testcase_path_client = None
        self.content_path = None
        self.media_agent_obj1 = None
        self.media_agent_machine1 = None
        self.drive_path_media_agent = None
        self.testcase_path_media_agent = None
        self.media_agent_path = None
        self.library = None
        self.copy = None
        self.storage_policy = None
        self.backup_set = None

    def setup(self):
        """Setup function of this test case"""
        self.opt_selector = OptionsSelector(self.commcell)
        self.library_name = '%s_Lib_%s' % (str(self.id), self.tcinputs.get("MediaAgentName"))
        self.backupset_name = '%s_BS_%s' % (str(self.id), self.tcinputs.get("MediaAgentName"))
        self.subclient_name = '%s_SC_%s' % (str(self.id), self.tcinputs.get("MediaAgentName"))
        self.storage_pool_name = '%s_POOL_%s' % (str(self.id), self.tcinputs.get("MediaAgentName"))
        self.storage_policy_name = '%s_SP_%s' % (str(self.id), self.tcinputs.get("MediaAgentName"))

        # create client source content path to be used as subclient content
        self.client_machine = machine.Machine(self.client, self.commcell)
        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25 * 1024)
        self.testcase_path_client = self.client_machine.join_path(drive_path_client, f'client_{self.id}')
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        # create mediaagent path to be used as mountpath
        self.media_agent_obj1 = self.commcell.media_agents.get(self.tcinputs.get("MediaAgentName"))
        self.media_agent_machine1 = machine.Machine(self.tcinputs.get("MediaAgentName"), self.commcell)
        self.drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine1, 25 * 1024)
        self.testcase_path_media_agent = self.media_agent_machine1.join_path(self.drive_path_media_agent,
                                                                             f'MA_{self.id}')
        self.media_agent_path = self.media_agent_machine1.join_path(self.testcase_path_media_agent, f"mount_path")
        self.mm_helper = MMHelper(self)

    def previous_run_clean_up(self):
        """delete previous run items"""
        self.log.info("********* previous run clean up **********")
        try:
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(
                    self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
            if self.commcell.storage_pools.has_storage_pool(
                    self.storage_pool_name):
                self.commcell.storage_pools.delete(self.storage_pool_name)
            time.sleep(10)
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def create_resources(self):
        """
        creates basic entities to start the case
        """

        # creating mountpath
        if not self.media_agent_machine1.check_directory_exists(self.media_agent_path):
            self.media_agent_machine1.create_directory(self.media_agent_path)

        # Creating a nondedup storage pool and associate to SP
        self.log.info("Configuring Storage Pool ==> %s", self.storage_pool_name)
        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.media_agent_path,
                                                                self.tcinputs['MediaAgentName'],
                                                                ddb_ma=None, dedup_path=None)
        else:
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)
        self.log.info("Done creating a storage pool")
        self.commcell.disk_libraries.refresh()

        self.storage_policy = self.commcell.policies.storage_policies.add(
            storage_policy_name=self.storage_policy_name, global_policy_name=self.storage_pool_name,
            global_dedup_policy=False)

        # create backupset and subclient
        self.opt_selector.create_uncompressable_data(self.client.client_name, self.content_path, size=1,
                                                     num_of_folders=1, delete_existing=True)
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
        self.subclient = self.mm_helper.configure_subclient(
            self.backupset_name, self.subclient_name, self.storage_policy_name,
            self.content_path, self.agent)

        # update retention to 1 day, 0 cycle
        self.log.info("setting retention to: 1 day, 0 cycle")
        self.copy = self.storage_policy.get_copy('Primary')

        self.copy.copy_retention = (1, 0, 1)
        self.copy.copy_retention_managed_disk_space = False

    def run_backup(self, backup_type="FULL"):
        """
           this function runs backup
        Args:
            backup_type (str): type of backup to run
                Default - FULL
        Returns:
            job - (object) -- returns job object to backup job
        """

        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(backup_type, job.delay_reason)
            )
        self.log.info("Backup job completed.")
        return job

    def prune_jobs(self, list_of_jobs):
        """
        Prunes jobs from storage policy copy

        Args:
            list_of_jobs    (list) - List of jobs

        """
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        for job in list_of_jobs:
            self.copy.delete_job(job)
            self.log.info("Deleted job from %s with job id %s", self.copy.copy_name, job)
        self.run_data_aging()

    def run_data_aging(self):
        """
        runs a granular data aging job on the primary copy

        """
        da_job = self.mm_helper.submit_data_aging_job(storage_policy_name=self.storage_policy_name,
                                                      copy_name='Primary',
                                                      is_granular=True, include_all=False,
                                                      include_all_clients=True, select_copies=True,
                                                      prune_selected_copies=True)
        self.log.info("data aging job: {0}".format(da_job.job_id))
        if not da_job.wait_for_completion():
            raise Exception(
                "Failed to run data aging with error: {0}".format(da_job.delay_reason)
            )
        self.log.info("Data aging job completed.")

    def extended_retention_validation(self, rule):
        """
        runs the validation tests for the supplied type of extended retention
        Args:
            rule    (int)      --the extended retention rule type (1 Daily, 2 Weekly, 3 Monthly)
        Returns:
            Result  (bool)      --returns true if the validation passed, false otherwise
        """

        result = True
        if rule == 1:
            self.log.info("setting extended retention for daily fulls to 30 days")
            rule_string = "EXTENDED_DAY"
            self.copy.extended_retention_rules = [1, True, "EXTENDED_DAY", 30, 0]
        elif rule == 2:
            self.log.info("updating extended retention to: Daily Fulls 1 day, "
                          "Weekly Fulls 30 days ")
            rule_string = "EXTENDED_WEEK"
            self.copy.extended_retention_rules = [1, True, "EXTENDED_DAY", 1, 0]
            self.copy.extended_retention_rules = [2, True, "EXTENDED_WEEK", 30, 0]
        elif rule == 3:
            self.log.info("updating extended retention to: Daily fulls 1 day, "
                          "Weekly Fulls 2 days, Monthly Fulls 90 days ")
            rule_string = "EXTENDED_MONTH"
            self.copy.extended_retention_rules = [1, True, "EXTENDED_DAY", 1, 0]
            self.copy.extended_retention_rules = [2, True, "EXTENDED_WEEK", 2, 0]
            self.copy.extended_retention_rules = [3, True, "EXTENDED_MONTH", 90, 0]

        # Run 2 FULL backups
        self.log.info("Run 2 Full Backup jobs")
        backup_jobs_list = []
        for i in range(0, 2):
            self.log.info("Running full backup J{0}...".format(i + 1))
            job = self.run_backup()
            backup_jobs_list += [job.job_id]
            # wait a bit after job completion to confirm its finished before next job starts
            time.sleep(15)

        if rule == 1:
            # Run the script to move backup to 1 day
            self.log.info("moving job run times back by 1 day")
            self.mm_helper.move_job_start_time(backup_jobs_list[0], 1)
            self.mm_helper.move_job_start_time(backup_jobs_list[1], 1)
        elif rule == 2:
            # Run the script to move backup to previous week
            d = datetime.date.today()
            self.log.info("moving job run times back to previous week")
            # week starts on Friday, so making special rule if its Thursday so we dont have jobs that span 2 weeks
            if d.weekday() == calendar.THURSDAY:
                self.mm_helper.move_job_start_time(backup_jobs_list[0], 8)
                self.mm_helper.move_job_start_time(backup_jobs_list[1], 7)
            else:
                self.mm_helper.move_job_start_time(backup_jobs_list[0], 7)
                self.mm_helper.move_job_start_time(backup_jobs_list[1], 6)
        elif rule == 3:
            # Run the script to move jobs back to previous month
            current_date = datetime.date.today()
            current_day = current_date.day
            current_month = current_date.month
            current_year = current_date.year
            if current_month == 1:
                prev_month_range = monthrange(current_year - 1, 12)
            else:
                prev_month_range = monthrange(current_year, current_month - 1)
            days_to_move_back_j1 = (current_day + prev_month_range[1]) - 1
            days_to_move_back_j2 = (current_day + prev_month_range[1]) - 9
            self.log.info("moving job run times back to first and 8th of previous month")
            self.mm_helper.move_job_start_time(backup_jobs_list[0], days_to_move_back_j1)
            self.mm_helper.move_job_start_time(backup_jobs_list[1], days_to_move_back_j2)

        self.log.info("--------- run one more backup to satisfy cycle requirement -----------")
        # Run 1 FULL backup
        job = self.run_backup()
        backup_jobs_list += [job.job_id]

        # Run Data aging 1
        self.log.info("Running Data aging...")
        self.run_data_aging()

        # Validate J1 is aged
        self.log.info("VALIDATION: backup job J1 should be aged by regular retention")
        if self.mm_helper.validate_job_prune(backup_jobs_list[0], self.copy.copy_id):
            self.log.info("Validation success")
        else:
            result = False
            raise Exception(
                "Backup job {0} is expected to age".format(backup_jobs_list[0])
            )

        # Validate - J2 should not age
        self.log.info("VALIDATION: backup job J2 should not be aged")
        if not self.mm_helper.validate_job_prune(backup_jobs_list[1], self.copy.copy_id):
            self.log.info("Validation success")
        else:
            result = False
            raise Exception(
                "Backup job {0} is not expected to age".format(backup_jobs_list[1])
            )

        # Validate proper retention flag is set on J2
        self.log.info(f"VALIDATION: {rule_string} retention flag set in JMDataStats table")
        if self.mm_helper.validate_job_retentionflag(backup_jobs_list[1], rule_string):
            self.log.info("Validation success")
        else:
            result = False
            raise Exception(f"Backup job {backup_jobs_list[1]} is not set with {rule_string} retention flag")

        # delete all jobs to start next set of tests with clean slate
        self.prune_jobs(backup_jobs_list)

        return result

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            self.previous_run_clean_up()

            # create environment
            self.create_resources()

            # validation for last daily full:
            if not self.extended_retention_validation(1):
                self.log.error("FAIL - Last Daily Full validation")
            # validation for last weekly full:
            if not self.extended_retention_validation(2):
                self.log.error("FAIL - Last Weekly Full validation")
            # validation for last monthly full:
            if not self.extended_retention_validation(3):
                self.log.error("FAIL - Last Monthly Full validation")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all the resources and settings created for this testcase"""
        self.log.info("Tear down function of this test case")
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED')
        try:

            # unconditional cleanup
            self.log.info("running unconditional cleanup")
            self.previous_run_clean_up()

        except Exception as exp:
            self.log.info("clean up ERROR %s", exp)
