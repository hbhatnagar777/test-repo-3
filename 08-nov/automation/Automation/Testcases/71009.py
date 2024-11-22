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

    init_tc()       -- Initial configuration for the test case using command center

    clean_test_environment() --  To perform cleanup operation before setting the environment and
                                 after testcase completion

    setup()         --  setup function of this test case

    configure_tc_environment() -- Create storage pool, storage policy and associate to subclient

    run_backups() -- Run backups on subclients based on number of jobs required

    run_backup() -- Runs backup by generating new content to get unique blocks for dedupe backups

    set_do_not_dedup_against_n_days() -- Sets the Do not deduplicate against objects older than n days setting
    
    change_time_restart_services() -- Changes the system time in days by keeping services off and turning it on
                                        afterwards
    
    move_system_days() -- Changes the system time in days
    
    run_synthetic_full_job() -- Runs the Synthetic full Job

    get_primary_and_sec_record_count() -- Get the primary and secondary record count from IdxSIDBUsageHistory table
    
    validate_record_counts() -- Validate the primary and secondary record counts before and after time shift

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample Input:
    "71009": {
          "ClientName": "client anme",
          "MediaAgentName": "Media Agent Name",
          "AgentName": "File System",
          "CSUsername": "CS machine username",
          "CSPassword": "CS machine password",
          **Optional**
          "mount_path": "mount path"
          "dedup_path": "dedupe path"
        }
        
    Note: In this case, the DDB MA will be the commserve machine itself. This is becuase the time is shifted here
          and both CS and DDB should be shifted by same time to simulate the test scenario.

Steps:
    -> clean the testcase environment
    -> Configure test case environment
        a. Create storage pool with 2 partitions
        b. Create storage policy
        c. Create backupset, subclient and content path
    -> Set oldestEligibleObjArchiveTime to 2 days
    -> Generate data in content path and run multiple backups on first storage policy -> 1 full, 2 incrementals
    -> Get primary and secondary record count before time shift
    -> Change system time by 4 days and restart services on CS
    -> Run Synthetic full job -> it should create new primary and secondary records
    -> Get primary and secondary record count after time shift
    -> Validate primary & secondary record count has increased (doubled) as expected
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from AutomationUtils.machine import Machine
from Web.Common.page_object import TestStep, handle_testcase_exception
from AutomationUtils import config
from math import isclose
import time


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Testcase to validate Do Not Deduplicate against objects older than n days setting"
        self.mmhelper = None
        self.dedup_helper = None
        self.common_util = None
        self.client_machine = None
        self.backupset_name = None
        self.subclient_name = None
        self.storage_pool_name = None
        self.storage_policy_name = None
        self.subclient_obj_list = []
        self.utility = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.ddb_path = None
        self.ma_machine = None
        self.ma_path = None
        self.storage_pool = []
        self.storage_policy_list = []
        self.content_path_list = []
        self.mount_path = None
        self.ma_client = None
        self.backup_jobs = []
        self.query_results = []
        self.copy_id = None
        self.ma_machine_name = None
        self.sidb_store_id = None
        self.commserve_client = None
        self.commserv_machine = None
        self.total_time_changed = 0
        self.prim_recs_before_timeshift = None
        self.sec_recs_before_timeshift = None
        self.prim_recs_after_timeshift = None
        self.sec_recs_after_timeshift = None
        self.cs_ddb_path = None
        self.sql_username = None
        self.sql_password = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        self.utility = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine_name = self.tcinputs['MediaAgentName']
        self.ma_machine = Machine(self.ma_machine_name, self.commcell)

        self.commserve_client = self.commcell.commserv_client
        self.commserv_machine = Machine(
            self.commserve_client.client_name,
            username=self.tcinputs.get('CSUsername'),
            password=self.tcinputs.get('CSPassword')
        )

        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.ma_machine, size=20 * 1024)
            self.ma_path = self.ma_machine.join_path(ma_1_drive, 'test_' + str(self.id))

        if not self.is_user_defined_mp:
            self.mount_path = self.ma_machine.join_path(self.ma_path, "MP")
        else:
            self.mount_path = self.ma_machine.join_path(
                self.tcinputs['mount_path'], 'test_' + self.id, 'MP')

        if not self.is_user_defined_dedup and "unix" in self.ma_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        cs_drive = self.utility.get_drive(self.commserv_machine, size=20 * 1024)
        self.cs_ddb_path = self.commserv_machine.join_path(cs_drive, 'test_' + str(self.id))

        if self.is_user_defined_dedup:
            self.log.info("custom source dedup path supplied")
            self.ddb_path = self.commserv_machine.join_path(self.tcinputs["dedup_path"],
                                                            'test_' + self.id, "DDB")
        else:
            self.ddb_path = self.commserv_machine.join_path(self.cs_ddb_path + "DDBs")

        self.log.info(f"Source DDB path : {self.ddb_path}")

        # names of various entities
        self.backupset_name = f"bkpset_tc_{self.id}"
        self.subclient_name = f"subc_tc_{self.id}"
        self.storage_policy_name = f"sp_tc_{self.id}"
        self.storage_pool_name = f"storage_pool_tc_{self.id}"
        self.dedup_helper = DedupeHelper(self)
        self.ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
        self.sql_username = config.get_config().SQL.Username
        self.sql_password = config.get_config().SQL.Password

    @test_step
    def clean_test_environment(self):
        """
        Clean up test environment
        """
        try:
            self.log.info("** STEP: Cleaning up test environment **")

            self.commcell.refresh()

            if self.content_path_list:
                if self.client_machine.check_directory_exists(self.content_path_list[-1]):
                    self.log.info(f"Deleting already existing content directory {self.content_path_list[-1]}")
                    self.client_machine.remove_directory(self.content_path_list[-1])

            # check for sp with same name if pre-existing with mark and sweep enabled
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info(f"deleting storage policy: {self.storage_policy_name}", )
                sp_obj = self.commcell.storage_policies.get(self.storage_policy_name)
                sp_obj.reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(f"deleting storage pool: {self.storage_pool_name}")
                self.commcell.storage_pools.delete(self.storage_pool_name)

            self.commcell.refresh()

            self.log.info("Cleanup completed")

        except Exception as excp:
            self.log.warning(f"***Failure in Cleanup with error {excp}***")

    @test_step
    def configure_tc_environment(self):
        """Create storage pool, storage policy and associate to subclient"""
        self.log.info("** STEP: Configuring Testcase environment **")
        self.storage_pool, self.storage_policy_list, self.content_path_list, self.subclient_obj_list \
            = self.dedup_helper.configure_mm_tc_environment(self.commserv_machine,
                                                            self.ma_machine_name,
                                                            self.mount_path,
                                                            self.ddb_path,
                                                            2,
                                                            same_path=False)
        self.sidb_store_id = self.dedup_helper.get_sidb_ids(
            self.storage_pool.storage_pool_id, 'Primary')[0]

    @test_step
    def run_backups(self, subclient_idx, new_data=True):
        """
        Run backups on subclients based on number of jobs required
        param:
            subclient_idx (int)  : index of the subclient from subclient list from which to run backups
            
            new_data (bool) : flag to generate new data for backup
        """
        self.log.info("Running full backup followed by incremental backups")
        self.backup_jobs.append(self.run_backup())
        for _ in range(0, 3):
            job = self.run_backup(backup_type="incremental", subclient_idx=subclient_idx, new_data=new_data)
            self.backup_jobs.append(job)

    def run_backup(self,
                   backup_type="FULL",
                   size=1,
                   subclient_idx=0,
                   new_data=True):
        """
        This function runs backup by generating new content to get unique blocks for dedupe backups
        Args:
            backup_type (str): type of backup to run
            size (float): size of backup content to generate
            subclient_idx (int)  : index of the subclient from subclient list from which to run backups
            new_data (bool) : flag to generate new data for backup

        Returns:
            job (object) -- returns job object to backup job
        """
        # add content
        if new_data:
            self.mmhelper.create_uncompressable_data(self.tcinputs["ClientName"],
                                                     self.content_path_list[subclient_idx], size)
        self._log.info("Running %s backup...", backup_type)
        job = self.subclient_obj_list[subclient_idx].backup(backup_type)
        self._log.info("Backup job: %s", job.job_id)
        self.log.info(f"Waiting for the Job {job.job_id} to be completed")
        if not job.wait_for_completion(timeout=20):
            raise Exception(
                f"Failed to run {backup_type} backup with error: {job.delay_reason}"
            )
        self._log.info("Backup job completed.")
        return job

    def set_do_not_dedup_against_n_days(self, num_days):
        """
        Sets the Do not deduplicate against objects older than n days setting
        
        Args:
            num_days (int)  : number of days to set
        """
        query = f"UPDATE IdxSIDBStore set oldestEligibleObjArchiveTime = {num_days} " \
                f"WHERE SIDBStoreId = {self.sidb_store_id}"
        self.log.info(
            f"""Setting Do not deduplicate against objects older than {num_days} days,
            on SIDB store: {self.sidb_store_id}""")
        self.log.info(f"Executing query: {query}")
        self.utility.update_commserve_db(query)
        self.log.info("Successfully updated oldestEligibleObjArchiveTime")

    @test_step
    def change_time_restart_services(self, days):
        """Changes the system time in days by keeping services off and turning it on afterwards

            Args:
                days        (int)   --      The number of days to move

            Returns:
                None

            Raises:
                Exception if unable to change the system time

        """
        self.log.info('***** Stopping all services *****')
        self.commserv_machine.stop_all_cv_services()

        self.move_system_days(days)

        services_up = False
        attempt = 0

        while not services_up:
            self.log.info('***** Starting all services *****')
            self.commserv_machine.start_all_cv_services()

            self.log.info('Waiting for 5 minutes')
            time.sleep(300)

            self.log.info('Checking if API server is up and reachable.')
            try:
                attempt += 1
                self.commserve_client.refresh()
                self.log.info('API server is up.')
                services_up = True
            except Exception as e:
                self.log.error('Exception while checking API server after restart [%s]. Attempt [%s]', e, attempt)
                time.sleep(30)
                if attempt > 3:
                    break

    def move_system_days(self, days):
        """Changes the system time in days

            Args:
                days        (int)   --      The number of days to move

            Returns:
                None

            Raises:
                Exception if unable to change the system time

        """
        self.log.info(f'Moving system time by [{days}] days')

        current_time = self.commserv_machine.current_time()
        self.log.info(f'Current machine time [{current_time}]')

        total_attempts = 3
        attempt = 1

        self.commserv_machine.toggle_time_service(stop=True)

        while attempt <= total_attempts:
            self.log.info(f'Changing system time Attempt [{attempt}/{total_attempts}]')

            # Adding in exception block since sometimes webservice crashes/times out after changing system time
            try:
                self.commserv_machine.change_system_time(86400 * days)
            except Exception as exp:
                self.log.exception(exp)
                self.log.error('Exception while changing system time. Ignoring and proceeding further')

            time.sleep(30)

            try:
                changed_time = self.commserv_machine.current_time()
            except Exception as exp:
                self.log.exception(exp)
                self.log.error('Exception while getting system time. Waiting sometime and getting again')
                time.sleep(30)
                changed_time = self.commserv_machine.current_time()

            self.log.info(f'After change machine time [{changed_time}]')

            if current_time.date() == changed_time.date():
                self.log.error('System time has not changed. Changing again.')
                attempt += 1
                continue
            else:
                self.log.info('********** System time has changed **********')
                self.total_time_changed += days
                return

        raise Exception('Unable to change system time after multiple attempts')

    @test_step
    def run_synthetic_full_job(self):
        """
        Runs the Synthetic full Job
        """
        self.log.info('Running the Synthetic full Job ')
        self.run_backup(backup_type="SYNTHETIC_FULL", new_data=False)
        
    def get_primary_and_sec_record_count(self):
        """
        Get the primary and secondary record count from IdxSIDBUsageHistory table
        
        Returns:
            primary_records (int)  : primary record count
            secondary_records (int)  : secondary record count
        """
        self.log.info(
            "Waiting for 150 secs for IdxSIDBUsageHistory table updates to happen")
        time.sleep(150)

        primary_records = self.dedup_helper.get_primary_recs_count(
            self.sidb_store_id, db_password=self.sql_password, db_user=self.sql_username)
        secondary_records = self.dedup_helper.get_secondary_recs_count(
            self.sidb_store_id, db_password=self.sql_password, db_user=self.sql_username)

        return primary_records, secondary_records

    @test_step
    def validate_record_counts(self):
        """
        Validate the primary and secondary record counts
        """
        self.log.info("Validating primary record count has increased as expected")
        # record counts should double after time shift
        if isclose(self.prim_recs_after_timeshift, 2*self.prim_recs_before_timeshift, rel_tol=100):
            self.log.info("Primary records has doubled as expected")
        else:
            self.log.error("Primary records has not doubled as expected")
            self.log.error(f"Primary recs before shift {self.prim_recs_before_timeshift},"
                           f" Primary recs after shift {self.prim_recs_after_timeshift}")
            raise Exception("Primary records has not doubled as expected")

        if isclose(self.sec_recs_after_timeshift, 2*self.sec_recs_before_timeshift, rel_tol=100):
            self.log.info("Secondary records has doubled as expected")
        else:
            self.log.error("Secondary records has not doubled as expected")
            self.log.error(f"Secondary recs before shift {self.sec_recs_before_timeshift},"
                           f" Secondary recs after shift {self.sec_recs_after_timeshift}")
            raise Exception("Secondary records has not doubled as expected")

    def run(self):
        """
        Main function for test case execution
        """
        try:
            self.clean_test_environment()
            self.configure_tc_environment()
            self.set_do_not_dedup_against_n_days(2)
            self.run_backups(subclient_idx=0)
            self.prim_recs_before_timeshift, self.sec_recs_before_timeshift = self.get_primary_and_sec_record_count()
            self.change_time_restart_services(4)
            self.run_synthetic_full_job()
            self.prim_recs_after_timeshift, self.sec_recs_after_timeshift = self.get_primary_and_sec_record_count()
            self.validate_record_counts()

        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear Down Function of this Case"""
        try:
            self.clean_test_environment()

            if self.status != constants.FAILED:
                self.log.info("Test Case PASSED.")
            else:
                self.log.warning("Test Case FAILED.")

        except Exception as excp:
            self.log.info(f"tear_down:: cleanup failed. {str(excp)}")
            
        finally:
            attempts = 0
            while self.total_time_changed != 0:
                attempts += 1
                self.log.info(f'Resetting system time as earlier [-{self.total_time_changed}]')

                if attempts == 3:
                    break

                try:
                    self.move_system_days(-self.total_time_changed)
                    self.commserv_machine.toggle_time_service(stop=False)
                except Exception as exp:
                    self.log.exception(exp)
                    self.log.error('Failed to reset system time.')
                    time.sleep(120)
