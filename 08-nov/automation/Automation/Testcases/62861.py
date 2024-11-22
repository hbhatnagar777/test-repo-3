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

    get_active_files_store()		--		Returns active store object for files iDA

    run_backup()					--		Run backup by generating new content to get unique blocks for dedupe backups.

    run_space_reclaim_job()			--		Runs Defrag job with type and option selected and waits for job to complete

    suspend_defrag_job()			--		Suspend the Space Reclamation job when job enters the given phase

    cleanup()						--		Performs cleanup of all entities

Sample JSON: values under [] are optional
"62861": {
            "ClientName": "",
            "AgentName": "File System",
            "MediaAgentName": "",
            "CloudLibraryName": "",
            ["DDBPath": "",
            "ScaleFactor": "5",
            "UseScalable": true]
        }


Note:
    1. providing cloud library is must as there are various vendors for configuration. best is to have it ready
    [mmhelper.configure_cloud_library can be used if need to create library]
    2. for linux, its mandatory to provide ddb path for a lvm volume
    3. ensure that MP on cloud library is set with pruner MA

design:

    1. Configure Storage Pool / Plan / Backup Set and Subclients

    2. Run backups on multiple subclients with an aim to generate 100+ chunks

    3. Start a Space Reclamation job and suspend it the moment it enters Defragment Data Phase

    4. Resume the Space Reclamation job and immediately start the Restore job on one of the subclients

    5. Verify that Space Reclamation job goes to Suspended / Queued state.

    6. Verify that Restore job completes and later Space Reclamation job also complets.

    7. Repeat step 3 to 6 but start Auxcopy job instead of a Restore job

    8. Repeat step 3 to 6 but start 3 Synthetic Full jobs with slight delay to achieve the condition of parallel running Synthetic Full & Space Reclamation

    9. Perform Cleanup
"""

from time import sleep
from AutomationUtils import constants
from AutomationUtils import commonutils
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
        self.name = "Suspend Low priority job during Cloud Defrag job"
        self.tcinputs = {
            "MediaAgentName": None,
            "CloudLibraryName": None
        }
        self.opt_selector = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.ddb_path = None
        self.autocopy_schedule = None
        self.scale_factor = None
        self.mmhelper = None
        self.restore_path = None
        self.ma_name = None
        self.dedupehelper = None
        self.gdsp_name = None
        self.client_machine = None
        self.gdsp = None
        self.library = None
        self.storage_policy = None
        self.backupset = None
        self.subclient = None
        self.primary_copy = None
        self.media_agent_machine = None
        self.sql_password = None
        self.allow_compaction_key_added = False
        self.allow_compaction_key_updated = False
        self.subclient_list = []

    def setup(self):
        """ Setup function of this test case. """
        # input values
        self.library_name = self.tcinputs.get('CloudLibraryName')

        self.ddb_path = self.tcinputs.get('DDBPath')
        self.scale_factor = self.tcinputs.get('ScaleFactor', 12)
        self.opt_selector = OptionsSelector(self.commcell)

        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.subclient_name = f"{str(self.id)}_SC_{self.ma_name[::-1]}"
        self.backupset_name = f"{str(self.id)}_BS_{self.ma_name[::-1]}"
        self.storage_policy_name = f"{str(self.id)}_SP_{self.ma_name[::-1]}"
        self.gdsp_name = f"{self.id}_GDSP_{self.ma_name[::-1]}"
        self.secondary_library_name = f"Library2_TC_{self.id}_{self.ma_name}"
        self.utility = OptionsSelector(self.commcell)

        self.client_machine = Machine(self.tcinputs.get('ClientName'), self.commcell)
        self.media_agent_machine = Machine(self.tcinputs.get('MediaAgentName'), self.commcell)

        drive_path_client = self.utility.get_drive(self.client_machine, 51200)
        drive_path_media_agent = self.utility.get_drive(self.media_agent_machine, 51200)

        client_drive = self.client_machine.join_path(
            drive_path_client, 'automation', self.id)
        media_agent_drive = self.media_agent_machine.join_path(
            drive_path_media_agent, 'automation1', self.id)

        self.content_path = self.client_machine.join_path(client_drive, 'content_path')
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info(f"content directory {self.content_path} already exists")
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)

        for content in (1, 6):
            content_path = self.client_machine.join_path(self.content_path, str(content))
            if self.client_machine.check_directory_exists(content_path):
                self.log.info(f"content directory {content_path} already exists")
                self.client_machine.remove_directory(content_path)
                self.log.info(f"existing content path {content_path} deleted")
            self.client_machine.create_directory(content_path)
            self.log.info(f"content path {content_path} created")

        if not self.ddb_path:
            if "unix" in self.media_agent_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not provided for Unix MA!..")
            self.ddb_path = self.media_agent_machine.join_path(media_agent_drive ,'DDB')
        else:
            self.log.info("will be using user specified path [%s] for DDB path configuration", self.ddb_path)

        self.restore_path = self.client_machine.join_path(drive_path_client, "restore_path")
        if self.client_machine.check_directory_exists(self.restore_path):
            self.log.info("restore path directory already exists")
            self.client_machine.remove_directory(self.restore_path)
            self.log.info("existing restore path deleted")
        self.client_machine.create_directory(self.restore_path)
        self.log.info("restore path created")

        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)

        self.sql_password = commonutils.get_cvadmin_password(self.commcell)

    def setup_environment(self):
        """
        Configures all entities based on tcInputs. If path is provided TC will use this path instead of self selecting
        """
        self.log.info("Setting up environment")
        if not self.commcell.disk_libraries.has_library(self.library_name):
            self.log.error("Cloud library %s does not exist!", self.library_name)
            raise Exception(f"Cloud library {self.library_name} does not exist!")
        self.library = self.commcell.disk_libraries.get(self.library_name)


        self.log.info("Creating a global dedup storage policy")

        self.gdsp = self.dedupehelper.configure_global_dedupe_storage_policy(self.gdsp_name, self.library_name,
                                                                                self.ma_name, self.ddb_path,
                                                                                self.ma_name)

        self.log.info("Configuring dependent Storage Policy ==> %s", self.storage_policy_name)

        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                     global_policy_name=self.gdsp_name)
        else:
            self.storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)

        self.mmhelper.configure_backupset(self.backupset_name, self.agent)

        for subc in range(1,6):
            content_path = self.client_machine.join_path(self.content_path, str(subc))
            self.subclient_list.append(self.mmhelper.configure_subclient(self.backupset_name,
                                                           f"{self.subclient_name}_{subc}",
                                                           self.storage_policy_name,
                                                           content_path,
                                                           self.agent))
            self.subclient_list[-1].data_readers = 5
            self.subclient_list[-1].allow_multiple_readers = True

        copy1 = '%s_copy1' % str(self.id)
        self.dedupehelper.configure_dedupe_secondary_copy(self.storage_policy, copy1, self.library_name,
                                                          self.ma_name,
                                                          self.ddb_path,
                                                          self.ma_name)
        self.mmhelper.remove_autocopy_schedule(self.storage_policy_name, copy1)
        self.primary_copy = self.storage_policy.get_copy('Primary')
        self.primary_copy.copy_retention = (1, 0, 1)

        if not self.media_agent_machine.check_registry_exists('MediaAgent', 'AuxcopySfileFragPercent'):
            self.media_agent_machine.create_registry('MediaAgent', value='AuxCopySfileFragPercent',
                                                     data='0', reg_type='DWord')
            self.log.info("adding sfile fragment percentage to 0!")

    def get_active_files_store(self):
        """Returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.gdsp_name, 'Primary_Global')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

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

    def run_backup(self, backup_type="Incremental", size=1024.0, delete_alternative=False,
                   skip_data_modification=False):
        """Run backup by generating new content to get unique blocks for dedupe backups.
        If ScaleFactor in tcInputs, creates factor times of backup data

        Args:
            backup_type (str): type of backup to run
                Default - FULL

            size (int): size of backup content to generate
                Default - 2048 MB

            delete_alternative (bool): deleting alternate content(every 3rd file) before running backup
                Default - False
            
            skip_data_modification(bool) : Only runs a backup job for the subclient

        """


        self.log.info("Running %s backup...", backup_type)
        job_list = []
        for jobcount in range(1, 6):
            self.log.info(f"Creating Content for Subclient_{jobcount}")
            content_path = self.client_machine.join_path(self.content_path, str(jobcount))
            self.mmhelper.create_uncompressable_data(self.tcinputs['ClientName'], content_path , 0.5)

            job_list.append(self.subclient_list[jobcount-1].backup(backup_type))
            self.log.info(f"Backup job: {job_list[-1].job_id}")

        for jobcount in range(5):
            if not job_list[jobcount].wait_for_completion():
                raise Exception(f"Failed to run {job_list[jobcount]} backup with error: {job_list[jobcount].delay_reason}")
            else:
                self.log.info(f"Backup job {job_list[jobcount].job_id} completed.")


    def run_space_reclaim_job(self, store):
        """
        Runs Defrag job with type and option selected and waits for job to complete
        Args:
            store (object) - object of the store to run DV2 job on
        """

        self.log.info("Running Space Reclamation Job")
        store.refresh()
        space_reclaim_job = store.run_space_reclaimation(
            clean_orphan_data=False,
            use_scalable_resource=self.tcinputs.get("UseScalable", True),
            num_streams="1")

        #Wait till job enters Defragment Data Phase

        self.log.info("Space Reclaim job ID : %s", space_reclaim_job.job_id)

        return space_reclaim_job

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
                sleep(1)
                attempts-=1

        if attempts <= 0:
            self.log.error("Space Reclamation job did not enter desired phase even after 10 minutes. Raising Exception")
            raise Exception(f"Space Reclamation Job {defrag_job.job_id} did not enter desired phase even after 10 minutes")
        else:
            self.log.info(f"Suspended Space Reclamation job when job entered the {target_phase} phase.")

    def run(self):
        """Run function of this test case"""
        try:

            self.cleanup()
            self.setup_environment()
            restore_case_success = aux_case_success = synthfull_case_success = False
            store = self.get_active_files_store()

            for jobnum in range(1, 6):
                self.log.info(f"Running backup jobs Iteration - {jobnum}")
                self.run_backup()
                sleep(30)


            self.log.info("CASE 1 : RESTORE + DEFRAG")

            store.refresh()
            reclamation_job = self.run_space_reclaim_job(store)
            self.suspend_defrag_job(reclamation_job, "defragment data")
            self.log.info(f"Suspended Space Reclamation Job {reclamation_job.job_id} in Defragment Data Phase")

            self.log.info("Resume Space Reclamation Job and Immediately start Restore Job")
            reclamation_job.resume()
            self.log.info(f"Space Reclamation Job Status : {reclamation_job.status.lower()}")
            self.log.info("running restore job")
            restore_job = self.subclient_list[0].restore_out_of_place(
                self.client, self.restore_path, [self.client_machine.join_path(self.content_path, "1")])
            self.log.info("restore job: %s", restore_job.job_id)
            self.log.info(f"Restore Job Status : {restore_job.status.lower()}")

            self.log.info("During restore job defrag job should go to suspend/Queued state in Defrag phase...")
            count = 0

            while reclamation_job.status.lower() not in ["suspended", "queued"] and count < 150:
                count += 1
                self.log.info("Current Space Reclamation status [%s]", reclamation_job.status)
                self.log.info("Current Restore job status [%s]", restore_job.status)
                if count == 150:
                    self.result_string += "[ RESTORE + DEFRAG : FAIL ] "
                    self.log.info(f"Space Reclamation job was not Suspended when Restore was running in parallel")

            self.log.info("Waiting for restore job to complete")
            restore_job.wait_for_completion()
            self.log.info("Successfully completed restore job")
            self.log.info("Waiting for Space Reclamation job to complete")
            reclamation_job.wait_for_completion()
            self.log.info("Successfully completed Space Reclamation  job")
            restore_case_success = True
            self.result_string += "[ RESTORE + DEFRAG : PASS ] "
            self.log.info("CASE 1 : RESTORE + DEFRAG ==> PASS")

            self.log.info("CASE 2 : AUX + DEFRAG")

            store.refresh()
            reclamation_job = self.run_space_reclaim_job(store)
            self.suspend_defrag_job(reclamation_job, "defragment data")
            self.log.info(f"Suspended Space Reclamation Job {reclamation_job.job_id} in Defragment Data Phase")

            self.log.info("Resume Space Reclamation Job and Immediately start AuxCopy Job")
            reclamation_job.resume()
            self.log.info(f"Space Reclamation Job Status : {reclamation_job.status.lower()}")

            count = 0
            copy1 = '%s_copy1' % str(self.id)
            auxcopy_job = self.storage_policy.run_aux_copy(storage_policy_copy_name=copy1,
                                                           streams=1)
            self.log.info("Current Auxcopy job status [%s]", auxcopy_job.status)

            while reclamation_job.status.lower() not in ["suspended", "queued"] and count < 150:
                count += 1
                self.log.info("Current Space Reclamation status [%s]", reclamation_job.status)
                self.log.info("Current Aux copy status [%s]", auxcopy_job.status)
                if count == 150:
                    self.result_string += "[ AUX + DEFRAG : FAIL ]"
                    self.log.info(f"Space Reclamation job was not Suspended when Auxcopy was running in parallel")

            self.log.info("Space Reclamation status [%s]", reclamation_job.status)

            self.log.info("Waiting for Auxcopy job to complete")
            auxcopy_job.wait_for_completion()
            self.log.info("Auxcopy job completed successfully")

            self.log.info("Waiting for Space Reclamation job to complete")
            reclamation_job.wait_for_completion()
            self.log.info(f"Space Reclamation Job completed successfully")
            aux_case_success = True
            self.result_string += "[ AUX + DEFRAG : PASS ]"
            self.log.info("CASE 2 : AUX + DEFRAG ==> PASS")

            self.log.info("CASE 3 : SYNTHFULL + DEFRAG")
 
            self.log.info("During Synthetic full, Defrag job should not get suspend/Queued in Defrag phase...")

            store.refresh()
            reclamation_job = self.run_space_reclaim_job(store)
            self.suspend_defrag_job(reclamation_job, "defragment data")
            self.log.info(f"Suspended Space Reclamation Job {reclamation_job.job_id} in Defragment Data Phase")
            
            self.log.info("Starting synthetic Full Job on 3 subclients")
            job1 = self.subclient_list[0].backup("Synthetic_full")
            self.log.info(f"Launched Synthetic Full Job - {job1.job_id}")
            sleep(3)
            job2 = self.subclient_list[1].backup("Synthetic_full")
            self.log.info(f"Launched Synthetic Full Job - {job2.job_id}")
            sleep(3)
            job3 = self.subclient_list[2].backup("Synthetic_full")
            self.log.info(f"Launched Synthetic Full Job - {job3.job_id}")
            self.log.info("Starting Space Reclamation job after 15 seconds so that some Synthfull will run in parallel to Defragment Data phase")
            sleep(15)
            self.log.info("Resume Space Reclamation Job after starting Synthetic Full Job")
            reclamation_job.resume()
            

            count = 0
            while reclamation_job.status.lower() != "suspended" and count < 150:
                count += 1
                self.log.info("Current Space Reclamation status [%s]", reclamation_job.status)
                self.log.info("Current Synthetic_full status : [{job1.status}] [{job2.status}] [{job3.status}]")
                if count == 150:
                    self.result_string += "[ SYNTHFULL + DEFRAG : FAIL ]"
                    self.log.info(f"Space Reclamation job was not Suspended when Synthetic Full was running in parallel")

            self.log.info("Wait for Synthfull job to complete")
            job1.wait_for_completion()
            job2.wait_for_completion()
            job3.wait_for_completion()

            self.log.info("Synthfull jobs completed.")

            self.log.info("Waiting for Space Reclamation Job to complete")
            reclamation_job.wait_for_completion()
            self.log.info("space reclaim job completed")
            synthfull_case_success = True
            self.result_string += "[ SYNTHFULL + DEFRAG : PASS ]"
            self.log.info("CASE 3 : SYNTHFULL + DEFRAG ==> PASS")

            if aux_case_success and restore_case_success and synthfull_case_success:
                self.log.info("Successfully completed the test case")
                self.log.info(self.result_string)
            else:
                self.log.error("Failed to comlete the test case successfully")
                self.log.error(self.result_string)
                raise Exception(self.result_string)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        self.log.info("Performing Unconditional Cleanup")
        try:
            self.cleanup()
        except Exception as ex:
            self.log.info(f"Cleanup failed with exception - {ex}")
