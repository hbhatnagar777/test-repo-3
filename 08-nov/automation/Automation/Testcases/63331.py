# coding=utf-8
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    setup_environment() -- configures entities based on inputs

    cleanup()   --  cleanups all created entities

    run_backup()    -- runs backup need for the case

    get_active_files_store() -- gets active files DDB store id

    validate_rows_from_csdb()    -- validates if no rows were returned for the schedule policy job from the csdb.

    check_ddb_verf_schedule_policy()    -- verifies whether DDB Verification Schedule Policy is disabled for the corresponding cloud lib

    check_ddb_space_reclamation_schedule_policy()   -- checks if the DDB Space Reclamation Schedule Policy is disabled for the corresponding cloud lib.

Sample JSON: values under [] are optional
"63331": {
            "ClientName": "",
            "AgentName": "File System",
            "MediaAgentName": "",
            "S3CloudBucket": "",
            "S3Region": "",
            "S3AccessKey": "",
            "S3SecretKey": "",
            "CloudVendor": "",
            ["dedup_path": "",
            "ScaleFactor": "12",
            "mount_path":]


Note:
    1. for linux, its mandatory to provide ddb path for a lvm volume
    2. ensure that MP on cloud library is set with pruner MA

    design:

    add dedupe sp with provided DDB path or self search path (use provided cloud lib)
    disable garbage collection on dedupe store

    generate content considering scale factor true or false
    Run job with X files - J1
    
    Run DDB Verification Schedule Policy and ensure that the job is not run for the cloud lib.
    Run DDB Space Reclamation Schedule Policy and ensure that the job is not run for the cloud lib.

    For CloudVendor, refer mediaagentconstans.py

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from MediaAgents.MAUtils.mahelper import DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Cloud Store association to DV2 and Defrag Schedule policy"
        self.tcinputs = {
            "MediaAgentName": None,
            "CloudVendor": None
        }
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.store_obj = None
        self.content_path = None
        self.ddb_path = None
        self.mmhelper = None
        self.dedupehelper = None
        self.client_machine = None
        self.library = None
        self.cloud_vendor = None
        self.storage_policy = None
        self.gdsp_name = None
        self.gdsp = None
        self.ma_name = None
        self.backupset = None
        self.subclient = None
        self.primary_copy = None
        self.media_agent_machine = None
        self.mountpath = None
        self.is_user_defined_mp = None
        self.is_user_defined_dedup = None
        self.scale_factor = None
        self.is_scheduler_disabled = None
        self.store_name = None

    def setup(self):
        """ Setup function of this test case. """
        # input values
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        # get value or set None
        self.ddb_path = self.tcinputs.get('dedup_path', None)
        self.scale_factor = self.tcinputs.get('ScaleFactor', 10)

        # defining names
        self.client_machine = Machine(self.client)
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.subclient_name = f"{self.id}_SC_{self.ma_name[::-1]}"
        self.backupset_name = f"{self.id}_BS_{self.ma_name[::-1]}"
        self.gdsp_name = f"{self.id}_GDSP_{self.ma_name[::-1]}"
        self.storage_policy_name = f"{self.id}_SP_{self.ma_name[::-1]}"
        self.media_agent_machine = Machine(self.ma_name, self.commcell)
        self.optionobj = OptionsSelector(self.commcell)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine, 2)
        self.ma_library_drive = self.optionobj.get_drive(self.media_agent_machine, 2)
        self.library_name = f"{self.id}_cloud_lib_{self.ma_name[::-1]}"
        self.cloud_vendor = self.tcinputs.get("CloudVendor")

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.media_agent_machine.join_path(self.tcinputs.get("mount_path"), self.id)
        else:
            self.mountpath = self.media_agent_machine.join_path(self.ma_library_drive, self.id)

        # select drive on client & MA for content and DDB

        self.content_path = self.client_machine.join_path(self.client_system_drive, 'content_path')

        if not self.ddb_path:
            if "unix" in self.media_agent_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not provided for Unix MA!..")
            self.ddb_path = self.media_agent_machine.join_path(self.ma_library_drive, 'DDB')
        else:
            self.log.info("will be using user specified path [%s] for DDB path configuration", self.ddb_path)   

        # helper objects
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)


    def setup_environment(self):
        """
        Configures all entities based on tcInputs. If path is provided TC will use this path instead of self selecting
        """
        self.log.info("setting up environment...")

        if not self.media_agent_machine.check_directory_exists(self.mountpath):
            self.log.info("Creating mountpath directory [%s]", self.mountpath)
            self.media_agent_machine.create_directory(self.mountpath)

        # if self.commcell.activity_control.is_enabled('SCHEDULER') is True means that scheduler is disabled.
        self.is_scheduler_disabled = self.commcell.activity_control.is_enabled('SCHEDULER')

        # if scheduler is disabled, enable the scheduler
        if self.is_scheduler_disabled:
            self.log.info("Scheduler is disabled. Enabling it on the CS.")
            self.commcell.activity_control.set('SCHEDULER', 'Enable')

        # Creating a cloud library

        self.mmhelper.configure_cloud_library(self.library_name, self.ma_name, self.tcinputs.get("S3CloudBucket"),
                                              self.tcinputs.get("S3Region") + "//" + self.tcinputs.get("S3AccessKey"),
                                              self.tcinputs.get("S3SecretKey"), self.cloud_vendor)

        self.log.info("Creating a global dedup storage policy")

        # Creating a storage policy using cloud library
        if not self.commcell.storage_policies.has_policy(self.gdsp_name):
            self.gdsp = self.dedupehelper.configure_global_dedupe_storage_policy(self.gdsp_name, self.library_name,
                                                                     self.ma_name, self.ddb_path, self.ma_name)
        else:
            self.gdsp = self.commcell.storage_policies.get(self.gdsp_name)

        self.log.info("Configuring dependent Storage Policy ==> %s", self.storage_policy_name)

        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                     global_policy_name=self.gdsp_name)
        else:
            self.storage_policy = self.commcell.storage_policies.has_policy(self.storage_policy_name)

        self.mmhelper.configure_backupset(self.backupset_name, self.agent)

        self.subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                           self.subclient_name,
                                                           self.storage_policy_name,
                                                           self.content_path,
                                                           self.agent)
        self.get_active_files_store()

    def cleanup(self):
        """Performs cleanup of all entities"""
        try:
            self.commcell.refresh()

            self.log.info("cleanup started")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("deleting content")
                self.client_machine.remove_directory(self.content_path)

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("deleting backupset: %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("deleting storage policy: %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.commcell.storage_pools.has_storage_pool(self.gdsp_name):
                self.log.info("deleting storage pool: %s", self.gdsp_name)
                self.commcell.storage_pools.delete(self.gdsp_name)
            
            self.commcell.disk_libraries.refresh()

            self.commcell.refresh()

            self.log.info("cleanup completed")

        except Exception as exe:
            self.log.warning("error in cleanup: %s. please cleanup manually", str(exe))

    def run_backup(self, backup_type="FULL", size=1024.0):
        """Run backup by generating new content to get unique blocks for dedupe backups.
        If ScaleFactor in tcInputs, creates factor times of backup data

        Args:
            backup_type (str): type of backup to run
                Default - FULL

            size (int): size of backup content to generate
                Default - 1024 MB

        Returns:
            (Job): returns job object of the backup job
        """

        additional_content = self.client_machine.join_path(self.content_path, 'generated_content')
        # add content
        if self.client_machine.check_directory_exists(additional_content):
            self.client_machine.remove_directory(additional_content)
        # if scalefactor param is passed in input json, multiple size factor times and generate content
        if self.scale_factor:
            size = size * int(self.scale_factor)
        file_size = 512
        self.mmhelper.create_uncompressable_data(self.client_machine,
                                                 additional_content, size // 1024, file_size=file_size)
        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run {backup_type} backup job {job.job_id} with error: {job.delay_reason}")
        self.log.info(f"Backup job {job.job_id} completed.")

    def validate_rows_from_csdb(self):
        """
        Checks if any rows were returned from csdb for the schedule policy job.

        Args: No Args needed be passed for this method.

        Returns:
            (bool) : True if no rows were returned
                     False if any rows were returned
        """

        query = f"""select * from RunningAdminJobs where opType=106 and cloudName='{self.store_name}'"""
        self.log.info(f"Executing query.....\n {query}")
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"Query output : {res}")
        if len(res) == 1 and res[0][0] == '':
            self.log.info(f"Verified no rows were present for the schedule policy and cloudName {self.store_name}")
            return True
        else:
            return False

    def check_ddb_verf_schedule_policy(self):
        """
        Checks if the DDB Verification Schedule Policy is disabled for the corresponding cloud lib.
        Also runs a DDB Verification Schedule Policy job and checks if the job was started not not.
        
        Returns:
            (bool) : True if 
                        no rows were returned for the corresponding cloud lib if the job has started.
                        no job has started.

                     False if
                        any row was returned for the corresponding cloud lib if the job has started.
        """

        job_id = None
        schedule_policy = self.commcell.schedule_policies.get("system created ddb verification schedule policy")
        for storage_policy in schedule_policy._associations:
            if "storagePolicyName" in storage_policy and storage_policy["storagePolicyName"] == self.gdsp_name:
                # storage_policy['flags']['exclude'] should be true for cloudlib
                if (storage_policy['flags']['exclude']):
                    self.log.info(f"DDB Verification Schedule policy for {self.gdsp_name} is disabled.")
                    self.log.info("Running a DV2 schdule policy job")
                    ddb_verf_policy = self.commcell.schedule_policies.get(
                        'system created ddb verification schedule policy')
                    ddb_verf_schedule = self.commcell.schedules.get(
                                                   schedule_id=int(ddb_verf_policy.all_schedules[0]['schedule_id']))
                    try:
                        job_id = ddb_verf_schedule.run_now()
                    except Exception as exe:
                        self.log.info("Entered exception, no job_id was returned when the job was run.")
                    finally:
                        if job_id is not None:
                            self.log.info("Verify no rows have been returned for the current job and store id.")
                            if self.validate_rows_from_csdb():
                                return True
                            else:
                                self.log.info("Rows were present on executing the query when the DDB Verification Schedule Policy Job was run.")
                                return False
                        else:
                            # Job is not run, so we return True
                            return True
        raise Exception(f"Cannot find a ddb verification schedule policy for {self.gdsp_name}")

    def get_active_files_store(self):
        """Returns active store object for files iDA"""

        self.commcell.deduplication_engines.refresh()
        dedup_engines_obj = self.commcell.deduplication_engines
        if dedup_engines_obj.has_engine(self.gdsp_name, 'Primary_Global'):
            dedup_engine_obj = dedup_engines_obj.get(self.gdsp_name, 'Primary_Global')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])
                self.store_name = self.store_obj.store_name

    def check_ddb_space_reclamation_schedule_policy(self):
        """
        Checks if the DDB Space Reclamation Schedule Policy is disabled for the corresponding cloud lib.
        Also runs a DDB Space Reclamation Schedule Schedule Policy job and checks if the job was started not not.
        
        Returns:
            (bool) : True if 
                        no rows were returned for the corresponding cloud lib if the job has started.
                        no job has started.

                     False if
                        any row was returned for the corresponding cloud lib if the job has started.
        """

        job_id = None
        try:
            space_verf_policy = self.commcell.schedule_policies.get('system created ddb space reclamation schedule policy')
            space_verf_schedule = self.commcell.schedules.get(
                schedule_id=int(space_verf_policy.all_schedules[0]['schedule_id']))
            job_id = space_verf_schedule.run_now()
            # sleep(15)
        except Exception as exec:
            self.log.info("Entered SDK Exception as expected because the job has not started.")
        finally:
            if job_id is not None:
                self.log.info("Verify no rows have been returned for the current job and store id.")
                if self.validate_rows_from_csdb():
                    return True
                else:
                    self.log.info("Rows were present on executing the query when the DDB Space Reclamation Schedule Policy Job was run.")
                    return False
            else:
                # Job is not run, so we return true
                return True

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()
            self.run_backup()

            check_rows_returned = 0

            if not self.check_ddb_verf_schedule_policy() or (not self.check_ddb_space_reclamation_schedule_policy()):
                check_rows_returned = 1

            if check_rows_returned:
                raise Exception("Rows were present on executing the query when the Job was run.")

        except Exception as exc:
            self.log.error('Failed to execute test case with error: %s', str(exc))
            self.result_string = str(exc)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        # Cleanup even if the tc fails
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED')

        self.log.info("Cleaning Up the Entities")
        self.cleanup()
        if self.is_scheduler_disabled:
            self.log.info("Scheduler is disabled before starting the testcase. Disabling it on the CS.")
            self.commcell.activity_control.set('SCHEDULER', 'Disable')