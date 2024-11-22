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

    previous_run_cleanup() -- for deleting the left over
     backupset and storage policy from the previous run

    run_backup_job() -- for running a backup job of given type

    get_active_files_store() -- Return active stores

    run_space_reclaim_job_without_pruner_ma()  --  space reclaim job without pruner MA

    run_space_reclaim_job_with_pruner_ma()  -- space reclaim job with pruner MA

    set_pruning_using_datapath_ma()   -- set/unset Pruning aged data based on the associated copy’s datapaths

    set_pruning_ma_using_devicecontroller ()  -- Set/unset pruner MA

    set_datapath_flag()  -- Set the correct flag on datapath

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase checks if Pruner MA is set or not. If pruner MA not set then fail the case


Prerequisites:

Note:
    1. providing cloud library is must as there are various vendors for configuration. best is to have it ready
    [mmhelper.configure_cloud_library can be used if need to create library]
    2. for linux, its mandatory to provide ddb path for a lvm volume


Input format:
            "ClientName": Name of the client
            "AgentName":  Type of Agent
            "MediaAgentName": Name of MediaAgent
            "library_name": name of the Library to be reused
            "dedup_path": path where dedup store to be created [for linux MediaAgents, User must explicitly provide a
                                                                dedup path that is inside a Logical Volume.
                                                                (LVM support required for DDB)]
            "is_scalable" : Optionally provide value as False in order to run Space Reclamation without SRA framework
Design Steps :
1) create resources and generate data on cloud lib
2) Don’t set the pruner MA on cloud LIB
3) Run defrag job -- It should immediately fail saying no pruner MA set
4) Enable “Select MA for pruning aged data based on the associated copy’s datapaths”
5) Run defrag job – it should complete using default data path MA.
6) Disable  “Select MA for pruning aged data based on the associated copy’s datapaths”
7) Set Pruner MA on cloud LIB
8) Run defrag job – it should complete using correct Pruner MA
10. Remove the resources created for this testcase.
"""

from cvpysdk import deduplication_engines
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils import mahelper
from MediaAgents.MAUtils.mahelper import  MMHelper

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Space Reclmation job with and without Pruner MA"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.storage_policy_id = None
        self.sidb_id = None
        self.substore_id = None
        self.testcase_path = None
        self.client_machine = None
        self.media_agent_machine = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.is_user_defined_lib = False
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.store = None
        self.mmhelper_obj = None
        self.utility = None
        self.is_scalable = True

    def setup(self):
        """Setup function of this test case"""

        self.mmhelper_obj = MMHelper(self)

        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        suffix = f'{self.tcinputs["MediaAgentName"]}_{self.tcinputs["ClientName"]}'

        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get('library_name')

        self.storage_policy_name = f"{self.id}_SP{suffix}"
        self.backupset_name = f"{self.id}_BS{suffix}"
        self.subclient_name = f"{self.id}_SC{suffix}"
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.utility = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client)
        self.media_agent_machine = Machine(self.tcinputs["MediaAgentName"], self.commcell)

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

            # create the required resources for the testcase
            # get the drive path with required free space

        drive_path_client = self.utility.get_drive(self.client_machine)
        drive_path_media_agent = self.utility.get_drive(self.media_agent_machine)
        self.testcase_path_media_agent = f'{drive_path_media_agent}{self.id}'

        # creating testcase directory, mount path, content path, dedup
        # store path

        self.testcase_path_client = f'{drive_path_client}{self.id}'

        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")



        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")

        self.is_scalable = self.tcinputs.get('is_scalable', True)

    def previous_run_clean_up(self):
        """delete the resources from previous run """
        self.log.info("********* previous run clean up **********")
        try:
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(
                    self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def run_backup_job(self, job_type):
        """running a backup job depending on argument
            job_type       (str)           type of backjob job
                                            (FULL, Synthetic_full)
        """
        self.log.info("Starting backup job")
        job = self.subclient.backup(job_type)
        self.log.info("Backup job: %s", str(job.job_id))
        self.log.info("job type: %s", job_type)
        if not job.wait_for_completion():
            raise Exception(
                f"Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))

        self.log.info("job %s complete", job.job_id)
        return job

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        engine = dedup_engines_obj.get(self.storage_policy_name, 'Primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0
		
    def run_space_reclaim_job_without_pruner_ma(self, defrag_level, with_ocl=False):
        """
        runs space reclaim job on the provided store object

        Args:
            with_ocl (bool) - set True if the job needs to run with OCL phase

            defrag_level (integer) - level of defragmentation
                                        level_map = {
                                                        1: 80,
                                                        2: 60,
                                                        3: 40,
                                                        4: 20
                                                    }

        Returns:
            (object) job object for the space reclaim job
        """

        expected_jpr = 'Pruner media agent not found to run Defrag phase on DDB, Please configure pruner media agent'

        space_reclaim_job = self.store.run_space_reclaimation(level=defrag_level, clean_orphan_data=with_ocl,
                                                         use_scalable_resource=self.is_scalable)
        self.log.info("Space reclaim job with OCL[%s]: %s", with_ocl, space_reclaim_job.job_id)
        if not space_reclaim_job.wait_for_completion():
            if space_reclaim_job.delay_reason.count(expected_jpr):
                self.log.info("Successfully verified that Space Reclamation job fails when no Pruner MA is set")

            else:
                self.log.error("result: Failed")
                self.log.info("DDB Space reclaim job failed")
                raise Exception(f"Failure reason is not as expected : Expected : {expected_jpr} Actual"
                                f" : {space_reclaim_job.delay_reason}")
        else:
            self.log.error("result: Failed")
            self.log.info("DDB Space reclaim job completed.")
            raise Exception("Pruner Media Agent Found to Run Defrag phase - Failing the case")

        return space_reclaim_job

    def run_space_reclaim_job_with_pruner_ma(self, defrag_level, with_ocl=False):

        """
        runs space reclaim job on the provided store object

        Args:
            with_ocl (bool) - set True if the job needs to run with OCL phase

            defrag_level (integer) - level of defragmentation
                                        level_map = {
                                                        1: 80,
                                                        2: 60,
                                                        3: 40,
                                                        4: 20
                                                    }

        Returns:
            (object) job object for the space reclaim job"""

        space_reclaim_job = self.store.run_space_reclaimation(level=defrag_level, clean_orphan_data=with_ocl,
                                                         use_scalable_resource=self.is_scalable)
        self.log.info("Space reclaim job with OCL[%s]: %s", with_ocl, space_reclaim_job.job_id)
        if not space_reclaim_job.wait_for_completion():
            raise Exception(f"Failed to run DDB Space reclaim with error: {space_reclaim_job.delay_reason}")
        self.log.info("DDB Space reclaim job completed.")
        return space_reclaim_job


    def set_pruning_using_datapath_ma(self, library_name, enable=True):

        """
         Enable/Disable "Select MA for pruning aged data based on the associated copy’s datapaths" option in GUI
         Arg "

        Args:
                enable(str)  : Specify option,  True/False

         Raises:
            Exception:
                if any error occurs in setting datapath.
        """

        condition = "Attribute | 256"
        if not enable:
            condition = "Attribute & ~256"
        query = f"""
             update mmmountpath set Attribute = {condition} where mountpathid = (
             select mountpathid from mmmountpath where libraryid = (
             select libraryid from mmlibrary where aliasname = '{library_name}'))
        """
        self.log.info("Query => %s", query)
        self.utility.update_commserve_db(query)
        self.log.info("Updated datapath successfully.")


    def set_pruning_ma_using_devicecontroller(self, library_name, usecount):

        """
         Set/Unset Pruner MA

         Args:
                usecount(int)  : setPruner MA 1 / unsetPruner MA 0

         Raises:
            Exception:
                if any error occurs in setting usecount.
        """
        query = f"""
                        update MMDeviceController set UseCount={usecount} where DeviceId in (select
                        DeviceId from mmmountpathtostoragedevice where mountpathid in (select
                        MountPathId from mmmountpath where LibraryId in ( select LibraryId from
                        MMLibrary where aliasName = '{library_name}')))"""

        self.log.info("Query => %s", query)
        self.utility.update_commserve_db(query)
        self.log.info("Updated Pruner MA successfully.")

    def set_datapath_flag(self, flag):


        """
         Set the correct flag on datapath after enabling "Select MA for pruning aged data based on the
         associated copy’s datapaths"

         Args:
             flag(int)  : Data Path flag

         Raises:
            Exception:
                if any error occurs in setting flag.

        """
        copyid = self.mmhelper_obj.get_copy_id(self.storage_policy_name, 'Primary')
        query = f"update MMDataPath set flag={flag} where copyid = {copyid}"
        self.log.info("Query => %s", query)
        self.utility.update_commserve_db(query)
        self.log.info("Updated datapath successfully.")

    def run(self):
        """Run function of this test case"""
        try:
            self.previous_run_clean_up()
            # create the required resources for the testcase

            # create SP
            self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
                self.storage_policy_name,
                self.library_name,
                self.tcinputs["MediaAgentName"],
                self.dedup_store_path)

            # create backupset
            self.backup_set = self.mm_helper.configure_backupset(
                self.backupset_name, self.agent)

            # generate the content
            if self.mm_helper.create_uncompressable_data(
                    self.client.client_name, self.content_path, 0.1, 1):
                self.log.info(
                    "generated content for subclient %s", self.subclient_name)

            # create subclient and add subclient content
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.subclient_name,
                self.storage_policy_name,
                self.content_path,
                self.agent)

            # Run FULL backup
            self.log.info("Running full backup...")

            job = self.run_backup_job("FULL")

            # initializing store object
            self.store = self.get_active_files_store()

            # UnSet pruning MediaAgent for cloud library.
            self.log.info("CASE 1: Defrag job without Pruner MA ")

            self.log.info("UnSet pruning MediaAgent for cloud library UseCount=0..")
            self.set_pruning_ma_using_devicecontroller(self.library_name, usecount=0)

            # Run defrag -- Defrag job should fail with correct JPR
            self.log.info("starting space reclaim job..")
            reclamation_job = self.run_space_reclaim_job_without_pruner_ma(defrag_level=4)

            self.log.info("CASE 2: Defrag job with Pruner MA enabled based on copy datapaths ")

            # Enable "Media Agent for pruning aged data based on associated copy datapaths"
            self.set_pruning_using_datapath_ma(self.library_name, enable=True)
            self.set_datapath_flag(flag=69)

            # Run defrag it should complete
            self.log.info("starting space reclaim job with based on assoicated copy datapath enabled  ..")
            reclamation_job = self.run_space_reclaim_job_with_pruner_ma(defrag_level=4)

            self.log.info("CASE 3: Defrag job with Pruner MA enabled UseCount=1 ")

            # Disable "Media Agent for pruning aged data based on associated copy datapaths" and set correct Flag on DP
            self.set_pruning_using_datapath_ma(self.library_name, enable=False)
            self.set_datapath_flag(flag=5)

            # set pruning MediaAgent for cloud library.
            self.log.info('set Pruning MediaAenet for cloud Library')
            self.set_pruning_ma_using_devicecontroller(self.library_name, usecount=1)

            # Run defrag it should complete
            self.log.info("starting space reclaim job with Pruner MA set..")
            reclamation_job = self.run_space_reclaim_job_with_pruner_ma(defrag_level=4)


        except Exception as exp:
            self.log.error(
                'Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        "delete all the resources for this testcase"
        self.log.info("Tear down function of this test case")
        try:
            self.log.info("*********************************************")
            self.log.info("restoring defaults")

            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            # Set the default values on data path and  MMdevicecontroller
            self.set_pruning_using_datapath_ma(self.library_name, enable=False)
            self.set_pruning_ma_using_devicecontroller(self.library_name, usecount=1)
            self.set_datapath_flag(flag=5)

            self.log.info("deleting backupset and SP of the test case")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("backup set deleted")
            else:
                self.log.info("backup set does not exist")

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("storage policy deleted")
            else:
                self.log.info("storage policy does not exist.")

            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)
