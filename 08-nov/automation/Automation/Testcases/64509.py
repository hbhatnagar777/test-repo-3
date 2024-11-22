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

    run_space_reclaim_job()     --  run_space_reclaim_job

    suspend_defrag_job()        --  Suspend the Space Reclamation job when job enters the given phase

    manipulate_sidb_tables()    --  Manipulate the SIDB table files for DedupChunks and ChunkIntegrity tables

    get_sidb_store()            --  Initialize the SIDB Store object

    resume_defrag_job()         -- Resume suspended Space Reclamation job and validate the expected outcome

    TcInputs to be passed in JSON File:
    "64509": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "MediaAgentName": Name of a MediaAgent - we create Libraries here
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
    }

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
        self.name = "OCL and Defrag phases of Space Reclamation job should connect to correct SIDB tables"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.ma_name = None
        self.client_name = None
        self.library_name = None
        self.sp_name = None
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

    def setup(self):
        """Setup function of this test case"""
        self.option_obj = OptionsSelector(self.commcell)
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.client_name = self.tcinputs.get('ClientName')

        self.client_machine_obj = Machine(self.client)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)

        self.client_drive = self.option_obj.get_drive(self.client_machine_obj, 30*1024)
        self.ma_drive = self.option_obj.get_drive(self.ma_machine_obj, 30*1024)

        self.library_name = f"LIB_{self.id}_{self.ma_name}"
        self.pool_name = f"STORAGEPOOL_{self.id}_{self.ma_name}"
        self.sp_name = f"SP_{self.id}_{self.ma_name}"


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

    def run_space_reclaim_job(self, with_ocl=False):
        """
        Runs space reclaim job with given options

        Args:
            with_ocl (bool) - set True if the job needs to run with OCL phase

        Returns:
            (object) job object for the space reclaim job
        """
        space_reclaim_job = self.store_obj.run_space_reclaimation(level=4, clean_orphan_data=with_ocl)
        self.log.info(f"Running Space Reclaim job {space_reclaim_job.job_id} with OCL = {with_ocl}")
        return space_reclaim_job

    def create_resources(self):
        """Create all the resources required to run backups"""
        self.mmhelper_obj.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)
        self.set_ransomware_protection(self.media_agent_obj, "disable")
        self.log.info("Sleeping for 5 minutes in order to disbale ransomware protection feature")
        time.sleep(300)

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
        if not self.commcell.storage_policies.has_policy(self.sp_name):
            self.log.info(f"Creating Storage Policy - {self.sp_name}")
            self.sp_obj = self.commcell.storage_policies.add(storage_policy_name=self.sp_name, library=self.pool_name,
                                               media_agent=self.ma_name, global_policy_name=self.pool_name,
                                               dedup_media_agent="", dedup_path="")
        else:
            self.sp_obj = self.commcell.storage_policies.get(self.sp_name)

        self.log.info("Adding 2nd partition")
        self.store_obj.add_partition(self.ma_machine_obj.join_path(self.dedup_path, "2"), self.ma_name)

        #Create a backupset
        self.log.info(f"Configuring Backupset - {self.backupset_name}")
        self.bkpset_obj = self.mmhelper_obj.configure_backupset(self.backupset_name)

        #Create a Subclient
        self.log.info(f"Configuring Subclient - {self.subclient_name}")
        self.subclient_obj = self.mmhelper_obj.configure_subclient(self.backupset_name, f"{self.subclient_name}",
                                              self.sp_name, self.content_path)
        self.log.info("Setting Number of Streams to 5 and Allow Multiple Data Readers to True")
        self.subclient_obj.data_readers = 5
        self.subclient_obj.allow_multiple_readers = True



    def suspend_defrag_job(self, defrag_job, target_phase="orphan chunk listing"):
        """Suspend the Space Reclamation job when job enters the given phase

        Args:
            defrag_job  (object)            :   Job object for Defrag Job
            target_phase       (str)       :   Phase at the beginning of which job should get suspended.
                                                Possible options:
                                                orphan chunk listing
                                                defragment data
        """
        attempts = 600
        self.log.info("Checking at 1 second interval if Space Reclamation job has entered given phase")
        while attempts > 0:
            job_phase = defrag_job.phase
            #self.log.info("Job Phase - {job_phase}")
            if job_phase.lower() == target_phase.lower():
                self.log.info("Job has entered the required phase. Suspending the job.")
                defrag_job.pause(wait_for_job_to_pause=True)
                break
            else:
                time.sleep(1)
                attempts-=1

        if attempts <= 0:
            self.log.error("Space Reclamation job did not enter desired phase even after 10 minutes. Raising Exception")
            raise Exception(f"Space Reclamation Job {defrag_job.job_id} did not enter desired phase even after 10 minutes")
        else:
            self.log.info(f"Suspended Space Reclamation job when job entered the {target_phase} phase.")

    def manipulate_sidb_tables(self, table_name, change_name=True):
        """
        Manipulate the SIDB table files for DedupChunks and ChunkIntegrity tables

        Args:
            table_name  (str)       --      DedupChunkQ or ChunkIntegrityQ table
            change_name(Bool)       --      Set the operation to be performed on DedupChunksQ and ChunkIntegrityQ tables
                                            Possible Operations:
                                            True    : Rename table files from original to different name
                                            False   : Rename table files back to original name
        """

        self.log.info("Waiting for SIDB to go down before starting with sidb table file manipulations")
        self.deduphelper_obj.wait_till_sidb_down(str(self.store_obj.store_id), self.commcell.clients.get(self.ma_name))
        #self.log.info("Sleeping for 2 minutes before attempting rename")
        #time.sleep(120)
        table = ""
        modified_table = ""
        if table_name.lower() == "dedupchunkq":
            table = self.ma_machine_obj.join_path(self.dedup_path, "1", "CV_SIDB", "2",
                                                    f"{self.store_obj.store_id}", "Split00", "DedupChunkQ.dat")
            modified_table = f"{table}_renamed"
        if table_name.lower() == "chunkintegrityq":
            table = self.ma_machine_obj.join_path(self.dedup_path, "1", "CV_SIDB", "2",
                                                            f"{self.store_obj.store_id}", "Split00", "ChunkIntegrityQ.dat")
            modified_table = f"{table}_renamed"

        if change_name:
            self.log.info(f"Renaming {table} to {modified_table}")
            self.ma_machine_obj.rename_file_or_folder(table, modified_table)
        else:
            self.log.info(f"Renaming {modified_table} to {table}")
            self.ma_machine_obj.rename_file_or_folder(modified_table, table)


    def resume_defrag_job(self, defrag_job, job_state="suspended", expected_success=True):
        """"
        Resume suspended Space Reclamation job and validate the expected outcome
        Args:
            defrag_job (object) --  Space Reclamation job object for the suspended job
            job_state   (str)   --  Expected Job state : suspended or pending
            expected_success (Bool) --  Whether Job should succeed when resumed or should go Pending.
                                        True    : Job should succeed
                                        False   : Job should go pending with JPR
        """
        defrag_job.refresh()
        self.log.info(f"Job {defrag_job.job_id} is in {defrag_job.status.lower()} state")
        if defrag_job.status.lower() == job_state:
            self.log.info("Resuming Space Reclamation job")
            defrag_job.resume(wait_for_job_to_resume=True)
        attempts = 200
        if expected_success:
            self.log.info("Waiting for job to complete successfully")
            if not defrag_job.wait_for_completion():
                raise Exception(f"Space Reclamation Job {defrag_job.job_id} did not complete successfully - "
                                f"{defrag_job.delay_reason}")
            else:
                self.log.info(f"Space Reclamation Job {defrag_job.job_id} completed successfully.")
                return True, "PASS"
        else:
            self.log.info("Waiting for job to go into pending state with timeout of 600 seconds")

            while attempts > 0:
                if defrag_job.status.lower() == "pending":
                    self.log.info(f"Successfully validated that job is in {defrag_job.phase.lower()} state")
                    self.log.info(f"JPR : {defrag_job.pending_reason}")
                    return True, "PASS"
                else:
                    if 0 == attempts % 5:
                        self.log.info(f"Job is still not in expected state. Current Phase : {defrag_job.phase.lower()} "
                                    f"Current Status : {defrag_job.status.lower()}")
                    time.sleep(1)
                    attempts-=1

        if attempts <= 0:
            self.log.error(f"Space Reclamation job {defrag_job.job_id} did not enter expected state even after timeout")
            return False, "FAIL"

    def run_backups(self):
        """
        Run backups on subclient
        """
        for bkp in range(1, 3):
            self.log.info(f"Generating content for subclient {self.subclient_name} at {self.content_path}")
            self.mmhelper_obj.create_uncompressable_data(self.client_name, self.content_path, 0.5)
            self.log.info(f"Starting backup on subclient {self.subclient_name}")
            backup_job = self.subclient_obj.backup("Incremental")
            self.log.info(f"Backup Job Id : {backup_job.job_id}")
            if not backup_job.wait_for_completion():
                raise Exception(f"Failed to run backup job {backup_job.job_id} with error:{backup_job.delay_reason}")
            self.log.info(f"Backup job {backup_job.job_id} on subclient {self.subclient_name} completed")

        self.store_obj.refresh()

    def cleanup(self):
        """
        Clean up the entities created by this test case
        """
        if not "unix" in self.ma_machine_obj.os_info.lower():
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

        self.log.info("Cleaning up dependent storage policies")
        if self.commcell.storage_policies.has_policy(self.sp_name):
            self.log.info(f"Deleting Dependent SP - {self.sp_name}")
            self.commcell.storage_policies.delete(self.sp_name)

        self.log.info(f"Cleaning up storage pool {self.pool_name}")
        if self.commcell.storage_pools.has_storage_pool(self.pool_name):
            self.log.info(f"Deleting Storage Pool {self.pool_name}")
            self.commcell.storage_pools.delete(self.pool_name)


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
            #TODO: Change mmconfig param - refer to existing ransomware protection test case
            if not ransomware_status and status.lower() == 'enable':
                self.log.info("Enabling Ransomware Protection")
                media_agent_obj.set_ransomware_protection(True)
            elif ransomware_status and status.lower() == 'disable':
                self.log.info("Disabling Ransomware Protection")
                media_agent_obj.set_ransomware_protection(False)
            else:
                self.log.info(f"Not performing any action as current Ransomware Protection Status is {ransomware_status} "
                              f"and requested operation is {status}")



    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.create_resources()
            self.run_backups()

            self.log.info("####CASE1 : Missing DedupChunkQ table before OCL Phase####")
            defrag_job = self.run_space_reclaim_job(with_ocl=True)
            self.suspend_defrag_job(defrag_job, "orphan chunk listing")
            self.manipulate_sidb_tables('DedupChunkQ')
            result1, status = self.resume_defrag_job(defrag_job, expected_success=False)
            self.result_list.append(f'CASE1 : Missing DedupChunkQ table before OCL Phase ==> {status}')
            self.log.info(f'####CASE1 : Missing DedupChunkQ table before OCL Phase ==> {status}####')

            self.log.info("CASE : Space Reclamation Job should succeed after error correction")
            self.manipulate_sidb_tables('DedupChunkQ', change_name=False)
            result2, status = self.resume_defrag_job(defrag_job, job_state="pending", expected_success=True)
            self.log.info(f'CASE : Space Reclamation Job should succeed after error correction ==> {status}')

            self.log.info("####CASE2 : Missing ChunkIntegrityQ table before OCL Phase####")
            defrag_job = self.run_space_reclaim_job(with_ocl=True)
            self.suspend_defrag_job(defrag_job, "orphan chunk listing")
            self.manipulate_sidb_tables('ChunkIntegrityQ')
            result3, status = self.resume_defrag_job(defrag_job, expected_success=False)
            self.result_list.append(f'CASE2 : Missing ChunkIntegrityQ table before OCL Phase ==> {status}')
            self.log.info(f"####CASE2 : Missing ChunkIntegrityQ table before OCL Phase ==> {status}####")

            self.log.info("CASE : Space Reclamation Job should succeed after error correction")
            self.manipulate_sidb_tables('ChunkIntegrityQ', change_name=False)
            result4, status = self.resume_defrag_job(defrag_job, job_state="pending", expected_success=True)
            self.log.info(f'CASE : Space Reclamation Job should succeed after error correction ==> {status}')

            self.log.info("####CASE3 : Missing DedupChunkQ table before Defrag Phase####")
            defrag_job = self.run_space_reclaim_job(with_ocl=False)
            self.suspend_defrag_job(defrag_job, "defragment data")
            self.manipulate_sidb_tables('DedupChunkQ')
            result5, status = self.resume_defrag_job(defrag_job, expected_success=False)
            self.result_list.append(f'CASE3 : Missing DedupChunkQ table before Defrag Phase ==> {status}')
            self.log.info(f'####CASE3 : Missing DedupChunkQ table before Defrag Phase ==> {status}####')
            self.log.info("CASE : Space Reclamation Job should succeed after error correction")
            self.manipulate_sidb_tables('DedupChunkQ', change_name=False)
            result6, status = self.resume_defrag_job(defrag_job, job_state="pending", expected_success=True)
            self.log.info(f'CASE : Space Reclamation Job should succeed after error correction ==> {status}')

            self.log.info("####CASE4 : Missing ChunkIntegrityQ table before Defrag Phase####")
            defrag_job = self.run_space_reclaim_job(with_ocl=False)
            self.suspend_defrag_job(defrag_job, "defragment data")
            self.manipulate_sidb_tables('ChunkIntegrityQ')
            result7, status = self.resume_defrag_job(defrag_job, expected_success=False)
            self.result_list.append(f'CASE4 : Missing ChunkIntegrityQ table before Defrag Phase ==> {status}')
            self.log.info(f'####CASE4 : Missing ChunkIntegrityQ table before Defrag Phase ==> {status}####')

            self.log.info("CASE : Space Reclamation Job should succeed after error correction")
            self.manipulate_sidb_tables('ChunkIntegrityQ', change_name=False)
            result8, status = self.resume_defrag_job(defrag_job, job_state="pending", expected_success=True)
            self.log.info(f'CASE : Space Reclamation Job should succeed after error correction ==> {status}')

            self.result_string = "\n".join(res for res in self.result_list)
            self.log.info(self.result_string)
            if result1 & result3 & result5 & result7:
                self.log.info("Successfully verified all the 4 cases. Test case completed successfully.")
            else:
                self.log.error("Test case completed with error")
                raise Exception("Test case failure as one of the sub cases did not complete successfully.")

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




