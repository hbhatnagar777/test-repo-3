# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    cleanup()       --  cleans up the entities

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    create_resources()  -- Create all the resources required to run backups

    run_backups()       --  Run backups on subclient

    set_ransomware_protection() --	toggle ransomware protection on client

    get_sidb_store()            --  Initialize the SIDB Store object

    run_job_for_compact2_recovery() -- Run Restore / Aux or DV2 job to check if compact2 recovery is performed as expected

    validate_compact2_recovery()    -- Validate compact2 file recovery after running the required job

    generate_compact2_file()        --  Generate Compact2 files in couple of chunks crated by given job

    TcInputs to be passed in JSON File:
    "62860": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "MediaAgentName": Name of a MediaAgent - we create Libraries here
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
    }

    STEPS:

    1. Configure Storage Pool / Plan / Backup Set and Subclient

    2. Run backup and fetch list of chunks written by the backup job

    3. Rename SFILE_CONTAINER_001 to SFILE_CONTAINER_001.compact2 in couple of chunks identified in step 2

    4. Run Restore job

    5. Verify that SFILE_CONTAINER_001.compact2 doesn't exist in chunk but SFILE_CONATAINER_001 exists

    6. Perform Step 2 to 5 but run Auxcopy job instead of Restore job

    7. Perform Step 2 to 5 but run Full Complete DV2 job instead of Restore job

    8. Clean up the entities
"""
import time
from cvpysdk import deduplication_engines
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Defrag job Compact2 Recovery Cases"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.ma_name = None
        self.client_name = None
        self.library_name = None
        self.plan_name = None
        self.pool_name = None
        self.mountpath = None
        self.backupset_name = None
        self.subclient_name = None
        self.ma_machine_obj = None
        self.client_machine_obj = None
        self.mmhelper_obj = None
        self.deduphelper_obj = None
        self.option_obj = None
        self.content_path = None
        self.client_drive = None
        self.ma_drive = None
        self.is_user_defined_dedup = False
        self.is_user_defined_mp = False
        self.dedup_path = None
        self.pool_obj = None
        self.sp_obj = None
        self.bkpset_obj = None
        self.subclient_obj = None
        self.store_obj = None
        self.media_agent_obj = None
        self.result_list = []
        self.restore_path = None
        self.copy_name = None
        self.disabled_ransomware_protection = False

    def setup(self):
        """Setup function of this test case"""
        self.option_obj = OptionsSelector(self.commcell)
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.client_name = self.tcinputs.get('ClientName')
        self.copy_name = "SecondaryCopy"
        self.client_machine_obj = Machine(self.client)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)

        self.client_drive = self.option_obj.get_drive(self.client_machine_obj, 30*1024)
        self.ma_drive = self.option_obj.get_drive(self.ma_machine_obj, 30*1024)

        self.library_name = f"LIB_{self.id}_{self.ma_name}"
        self.pool_name = f"STORAGEPOOL_{self.id}_{self.ma_name}"
        self.plan_name = f"PLAN_{self.id}_{self.ma_name}"


        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_mp:
            self.mountpath = self.tcinputs.get("mount_path")
            self.log.info(f"Using user provided mount path {self.mountpath}")
        else:
            self.mountpath = self.ma_machine_obj.join_path(self.ma_drive, self.id)

        if not self.is_user_defined_dedup:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_drive, "DDB", f"TC_{self.id}")
        else:
            self.dedup_path = self.tcinputs.get("dedup_path")
            self.log.info(f"Using user provided dedup path {self.dedup_path}")



        self.backupset_name = f"BKPSET_{self.id}_{self.client_name}"
        self.subclient_name = f"SUBC_{self.id}_{self.client_name}"
        self.content_path = self.client_machine_obj.join_path(self.client_drive, f"TC_{self.id}", "CONTENT")
        self.restore_path = self.client_machine_obj.join_path(self.client_drive, f"TC_{self.id}", "RESTORE")

        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)
        self.mmhelper_obj = MMHelper(self)
        self.deduphelper_obj = DedupeHelper(self)

    def get_sidb_store(self):
        """
        Get SIDB store for the storage pool
        """
        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        if dedup_engines_obj.has_engine(self.pool_name, self.pool_obj.copy_name):
            dedup_engine_obj = dedup_engines_obj.get(self.pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])


    def create_resources(self):
        """Create all the resources required to run backups"""

        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info(f"Content directory {self.content_path} already exists. Removing it.")
            self.client_machine_obj.remove_directory(self.content_path)
        self.log.info(f"Creating content directory {self.content_path}")
        self.client_machine_obj.create_directory(self.content_path)

        if self.client_machine_obj.check_directory_exists(self.restore_path):
            self.log.info(f"Content directory {self.restore_path} already exists. Removing it.")
            self.client_machine_obj.remove_directory(self.restore_path)
        self.log.info(f"Creating content directory {self.restore_path}")
        self.client_machine_obj.create_directory(self.restore_path)


        #Create Required Directories
        if not self.is_user_defined_mp and not self.ma_machine_obj.check_directory_exists(self.mountpath):
            self.log.info("Creating mountpath directory [%s]", self.mountpath)
            self.ma_machine_obj.create_directory(self.mountpath)

        if not self.is_user_defined_dedup and not self.ma_machine_obj.check_directory_exists(self.dedup_path):
            self.log.info("Creating dedup path directory [%s]", self.dedup_path)
            self.ma_machine_obj.create_directory(self.dedup_path)
            self.ma_machine_obj.create_directory(self.ma_machine_obj.join_path(self.dedup_path, "1"))
            self.ma_machine_obj.create_directory(self.ma_machine_obj.join_path(self.dedup_path, "2"))

        #Create a storage pool
        if not self.commcell.storage_pools.has_storage_pool(self.pool_name):
            self.log.info(f"Creating Storage Pool - {self.pool_name}")
            self.pool_obj = self.commcell.storage_pools.add(self.pool_name, self.mountpath,
                                                           self.ma_name, self.ma_name,
                                                            self.ma_machine_obj.join_path(self.dedup_path, "1"))
        else:
            self.pool_obj = self.commcell.storage_pools.get(self.pool_name)
        self.get_sidb_store()

        #Create a dependent storage policy
        if not self.commcell.plans.has_plan(self.plan_name):
            self.log.info(f"creating plan [{self.plan_name}]")
            self.plan_ob = self.commcell.plans.add(plan_name=self.plan_name, plan_sub_type="Server",
                                                   storage_pool_name=self.pool_name)
            # Disabling schedule policy from plan
            self.plan_ob.schedule_policies['data'].disable()
        else:
            self.sp_obj = self.commcell.storage_policies.get(self.pool_name)

        #Create a Secondary Copy in same plan
        if not self.commcell.storage_pools.has_storage_pool(f"{self.pool_name}_secondary"):
            self.log.info(f"Creating Storage Pool - {self.pool_name}_secondary")
            self.pool_obj = self.commcell.storage_pools.add(f"{self.pool_name}_secondary", self.mountpath,
                                                           self.ma_name, self.ma_name,
                                                            self.ma_machine_obj.join_path(self.dedup_path, "1"))
        else:
            self.pool_obj = self.commcell.storage_pools.get(f"{self.pool_name}_secondary")

        self.log.info(f"Adding the secondary copy [{self.copy_name}]")
        self.plan_ob.add_storage_copy(self.copy_name, f"{self.pool_name}_secondary")
        self.log.info(f"secondary copy [{self.copy_name}] added.")

        self.log.info("Adding 2nd partition")
        self.store_obj.add_partition(self.ma_machine_obj.join_path(self.dedup_path, "2"), self.ma_name)

        # Remove Association with System Created AutoCopy Schedule
        self.mmhelper_obj.remove_autocopy_schedule(self.plan_ob.storage_policy.storage_policy_name, self.copy_name)

        #Create a backupset
        self.log.info(f"Configuring Backupset - {self.backupset_name}")
        self.bkpset_obj = self.mmhelper_obj.configure_backupset(self.backupset_name)

        #Create a Subclient
        self.log.info(f"Configuring Subclient - {self.subclient_name}")
        if not self.bkpset_obj.subclients.has_subclient(self.subclient_name):
            self.subclient_obj = self.bkpset_obj.subclients.add(self.subclient_name)
            self.log.info(f"Added subclient [{self.subclient_name}] to backupset")
        else:
            self.subclient_obj = self._backupset.subclients.get(self.subclient_name)
        # Associating plan and content path to subclient
        self.subclient_obj.plan = [self.plan_ob, [self.content_path]]

        self.log.info("Setting Number of Streams to 5 and Allow Multiple Data Readers to True")
        self.subclient_obj.data_readers = 5
        self.subclient_obj.allow_multiple_readers = True


    def run_backups(self):
        """
        Run backups on subclient
        """
        self.log.info(f"Generating content for subclient {self.subclient_name} at {self.content_path}")
        self.mmhelper_obj.create_uncompressable_data(self.client_name, self.content_path, 0.5)
        self.log.info(f"Starting backup on subclient {self.subclient_name}")
        backup_job = self.subclient_obj.backup("Incremental")
        self.log.info(f"Backup Job Id : {backup_job.job_id}")
        if not backup_job.wait_for_completion():
            raise Exception(f"Failed to run backup job {backup_job.job_id} with error:{backup_job.delay_reason}")
        self.log.info(f"Backup job {backup_job.job_id} on subclient {self.subclient_name} completed")
        self.store_obj.refresh()
        return backup_job

    def cleanup(self):
        """
        Clean up the entities created by this test case
        """
        if not "unix" in self.ma_machine_obj.os_info.lower() and self.disabled_ransomware_protection:
            self.log.info("Enabling the Ransomware Protection Back")
            self.set_ransomware_protection(self.media_agent_obj, "enable")
        self.log.info(f"Cleaning up FileSystem subclients by deleting the backupset {self.backupset_name}")
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.log.info(f"Deleting backupset {self.backupset_name}")
            self.agent.backupsets.delete(self.backupset_name)

        self.log.info("Cleaning up content directories of these subclients")
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info(f"Deleting already existing content directory {self.content_path}")
            self.client_machine_obj.remove_directory(self.content_path)

        if self.commcell.plans.has_plan(self.plan_name):
            self.log.info("Plan exists, deleting that")
            self.commcell.plans.delete(self.plan_name)
            self.log.info("Plan deleted.")

        self.log.info(f"Cleaning up storage pool {self.pool_name}")
        if self.commcell.storage_pools.has_storage_pool(self.pool_name):
            self.log.info(f"Deleting Storage Pool {self.pool_name}")
            self.commcell.storage_pools.delete(self.pool_name)

        self.log.info(f"Cleaning up secondary storage pool {self.pool_name}_secondary")
        if self.commcell.storage_pools.has_storage_pool(f"{self.pool_name}_secondary"):
            self.log.info(f"Deleting Storage Pool {self.pool_name}_secondary")
            self.commcell.storage_pools.delete(f"{self.pool_name}_secondary")


    def set_ransomware_protection(self, media_agent_obj, status="disable"):
        """
            toggle ransomware protection on MA

            Args:
                media_agent_obj (obj)  --  MediaAgent object for the testcase run
                status          (str)   --  enable or disable the Ransomware Protection
        """
        if not "unix" in self.ma_machine_obj.os_info.lower():
            ransomware_status = self.mmhelper_obj.ransomware_protection_status(
                self.commcell.clients.get(media_agent_obj.name).client_id)
            self.log.info("Current ransomware status is: %s", ransomware_status)
            if not ransomware_status and status.lower() == 'enable':
                self.log.info("Enabling Ransomware Protection")
                media_agent_obj.set_ransomware_protection(True)
            elif ransomware_status and status.lower() == 'disable':
                self.log.info("Disabling Ransomware Protection")
                self.disabled_ransomware_protection = True
                self.mmhelper_obj.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)
                media_agent_obj.set_ransomware_protection(False)
            else:
                self.log.info(f"Not performing any action as current Ransomware Protection Status is {ransomware_status} "
                              f"and requested operation is {status}")

    def generate_compact2_file(self, job_obj):
        """
        Generate Compact2 files in couple of chunks crated by given job

        Args:
            job_obj (Object)        --  Job object

        Returns:
            list of path of chunks where compact2 files are created

        """
        self.log.info(f"Fetching chunks created by job id {job_obj.job_id}")
        chunks_path = self.mmhelper_obj.get_chunks_for_job(job_id = job_obj.job_id, afile_type=1,
                                                           log_query=True, order_by=1 )
        #Construct paths for first 2 chunks
        #[['A:\MP1', 'XYZBARCODE', 'V_123', '123']]
        slash = self.ma_machine_obj.os_sep
        chunk = chunks_path[0]

        chunk_1 = f"{chunk[0]}{slash}{chunk[1]}{slash}CV_MAGNETIC{slash}{chunk[2]}{slash}CHUNK_{chunk[3]}"
        self.log.info(f"Chunk_1 for creating .compact2 file ==> {chunk_1}")
        chunk = chunks_path[1]
        chunk_2 = f"{chunk[0]}{slash}{chunk[1]}{slash}CV_MAGNETIC{slash}{chunk[2]}{slash}CHUNK_{chunk[3]}"
        self.log.info(f"Chunk_2 for creating .compact2 file ==> {chunk_2}")

        self.log.info(f"{chunk_1} ==> Renaming SFILE_CONTAINER_001 to SFILE_CONTAINER_001.compact2")
        self.ma_machine_obj.rename_file_or_folder(f"{chunk_1}{slash}SFILE_CONTAINER_001", 
                                                  f"{chunk_1}{slash}SFILE_CONTAINER_001.compact2")

        self.log.info(f"{chunk_2} ==> Renaming SFILE_CONTAINER_001 to SFILE_CONTAINER_001.compact2")
        self.ma_machine_obj.rename_file_or_folder(f"{chunk_2}{slash}SFILE_CONTAINER_001",
                                                  f"{chunk_2}{slash}SFILE_CONTAINER_001.compact2")
        if not self.ma_machine_obj.check_file_exists(f"{chunk_1}{slash}SFILE_CONTAINER_001.compact2"):
            self.log.error(f"Failed to verify compact2 file at {chunk_1} after renaming SFILE_CONTAINER_001")
            raise Exception(f"Renaming of SFILE_CONTAINER_001 to SFILE_CONTAINER_001.compact2 failed for chunk - {chunk_1}")
        else:
            self.log.info(f"Successfully verified presence of SFILE_CONTAINER_001.compact2 file at {chunk_1}")

        if not self.ma_machine_obj.check_file_exists(f"{chunk_2}{slash}SFILE_CONTAINER_001.compact2"):
            self.log.error(f"Failed to verify compact2 file at {chunk_2} after renaming SFILE_CONTAINER_001")
            raise Exception(
                f"Renaming of SFILE_CONTAINER_001 to SFILE_CONTAINER_001.compact2 failed for chunk - {chunk_2}")
        else:
            self.log.info(f"Successfully verified presence of SFILE_CONTAINER_001.compact2 file at {chunk_2}")

        return [chunk_1, chunk_2]

    def validate_compact2_recovery(self, chunks_list):
        """
        Validate compact2 file recovery after running the required job

        Args:
            chunks_list     (List Obj)  --  List of paths of chunks to validate
        """
        slash = self.ma_machine_obj.os_sep
        for chunk in chunks_list:
            self.log.info(f"Validating SFILE_CONTAINER_001.compact2 recovery at {chunk}")
            if not self.ma_machine_obj.check_file_exists(f"{chunk}{slash}SFILE_CONTAINER_001.compact2"):
                self.log.info(f"Successfully verified absence of compact2 file at {chunk}")
            else:
                self.log.error(f"Failed to verify absence of compact2 file at {chunk}")
                return False

            if self.ma_machine_obj.check_file_exists(f"{chunk}{slash}SFILE_CONTAINER_001"):
                self.log.info(f"Successfully verified presence of renamed SFILE_CONTAINER_001 file at {chunk}")
            else:
                self.log.info(f"Failed to verify presence of renamed SFILE_CONTAINER_001 file at {chunk}")
                return False
        return True

    def run_job_for_compact2_recovery(self, job_type):
        """
        Run Restore / Aux or DV2 job to check if compact2 recovery is performed as expected

        Args:
            job_type    (str)       --      AUXCOPY / RESTORE  / DV2

        Returns:
            True or False based on validation of compact2 files after the job
        """
        job_obj = self.run_backups()
        chunks_list = self.generate_compact2_file(job_obj)

        if job_type.upper() == "RESTORE":
            self.log.info("TEST 1 : RESTORE JOB COMPACT2 FILE RECOVERY")
            restore_job = self.subclient_obj.restore_out_of_place(self.client, self.restore_path, [self.content_path])
            if not restore_job.wait_for_completion():
                raise Exception(f"Failed to run {restore_job.job_id} restore with error: {restore_job.delay_reason}")
            else:
                self.log.info(f"Restore job {restore_job.job_id} completed.")

        elif job_type.upper() == "AUXCOPY":
            self.log.info("TEST 2 : AUXCOPY JOB COMPACT2 FILE RECOVERY")
            aux_job = self.plan_ob.storage_policy.run_aux_copy(use_scale=True)
            if not aux_job.wait_for_completion():
                raise Exception(f"Failed to run auxcopy job {aux_job.job_id}  with error: {aux_job.delay_reason}")
            else:
                self.log.info(f"Aux job {aux_job.job_id} completed.")

        elif job_type.upper() == "DV2":
            self.log.info("TEST 3 : DV2 JOB COMPACT2 FILE RECOVERY")
            dv2_job = self.store_obj.run_ddb_verification(incremental_verification=False,
                                                          quick_verification=False, use_scalable_resource=True)
            if not dv2_job.wait_for_completion():
                raise Exception(f"Failed to run DV2 job {dv2_job.job_id}  with error: {dv2_job.delay_reason}")
            else:
                self.log.info(f"DV2 job {dv2_job.job_id} completed.")

        self.log.info(f"Validating compact2 recovery for {job_type} job")
        if self.validate_compact2_recovery(chunks_list):
            return True
        else:
            return False

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            if not "unix" in self.ma_machine_obj.os_info.lower():
                self.log.info("Disabling the Ransomware Protection and sleeping for 5 minutes for it to take effect")
                self.set_ransomware_protection(self.media_agent_obj, "disable")
                time.sleep(300)
            self.create_resources()
            restore_success = aux_success = dv2_success = False
            if self.run_job_for_compact2_recovery("RESTORE"):
                self.log.info("TEST 1 : RESTORE JOB COMPACT2 FILE RECOVERY ==> PASS")
                self.result_string += "TEST 1 : RESTORE JOB COMPACT2 FILE RECOVERY ==> PASS"
                restore_success = True
            else:
                self.log.info("TEST 1 : RESTORE JOB COMPACT2 FILE RECOVERY ==> FAIL")
                self.result_string += "TEST 1 : RESTORE JOB COMPACT2 FILE RECOVERY ==> FAIL"

            if self.run_job_for_compact2_recovery("AUXCOPY"):
                self.log.info("TEST 2 : AUXCOPY JOB COMPACT2 FILE RECOVERY ==> PASS")
                self.result_string += "TEST 2 : AUXCOPY JOB COMPACT2 FILE RECOVERY ==> PASS"
                aux_success = True
            else:
                self.log.info("TEST 2 : AUXCOPY JOB COMPACT2 FILE RECOVERY ==> FAIL")
                self.result_string += "TEST 2 : AUXCOPY JOB COMPACT2 FILE RECOVERY ==> FAIL"

            if self.run_job_for_compact2_recovery("DV2"):
                self.log.info("TEST 3 : DV2 JOB COMPACT2 FILE RECOVERY ==> PASS")
                self.result_string += "TEST 3 : DV2 JOB COMPACT2 FILE RECOVERY ==> PASS"
                dv2_success = True
            else:
                self.log.info("TEST 3 : DV2 JOB COMPACT2 FILE RECOVERY ==> FAIL")
                self.result_string += "TEST 3 : DV2 JOB COMPACT2 FILE RECOVERY ==> FAIL"

            if restore_success and aux_success and dv2_success:
                self.log.info("Successfully completed test case")
            else:
                self.log.info("Failure in executing test case")
                raise Exception(self.result_string)

        except Exception as exp:
            self.log.error("Failing test case : Error Encountered - %s", str(exp))
            self.status = constants.FAILED
            self.result_string = str(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Performing Unconditional Cleanup")
        try:
            self.cleanup()
        except Exception as ex:
            self.log.info(f"Cleanup failed with exception - {ex}")