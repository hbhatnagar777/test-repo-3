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

    new_content()       -- generates data of specified size in given directory

    deallocate_resources()      -- deallocates all the resources created for testcase environment

    allocate_resources()        -- allocates all the necessary resources for testcase environment

    previous_run_cleanup()      -- for deleting the left over backupset and storage policy from the previous run

    run_backup_job()        -- for running a backup job of given type

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    run_aux_copy()   --  runs auxcopy job for all copies

    _validate_sapackage()       -- checks if SA package is present on the client machine

    _sa_global_param()      --  checks if Storgae accelerator global param is enabled

    validateDestinationMA()     -- checks whether storage accelerator package overrode the destination MA

    validateLogs()      -- validates via logs that auxcopy used storage accelerator pipeline

    get_objects()  -- Gets the Primary and Secondary objects of the given copy name

    verify_block_size() -- verifies that cloud has 128KB of block size internally

    get_copy_objects() -- Stores Primary and Secondary objects and store it in primary_obj and secondary_obj arrays



Prerequisites: None

Input JSON:

"63865": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName1": "<Name of MediaAgent1>",
        "CloudLibraryMA": "<Name of MediaAgent for cloud library>",
        "CloudLibrary": "<Name of Cloud library>",
        "storage_pool_name": "<name of the storage pool to be reused>" (optional argument),
        "storage_pool_name2": "<name of the second storage pool to be reused>" (optional argument),
        "dedup_path1": "<path where dedup store to be created>" (optional argument),
        "dedup_path2": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:
1. Allocate resources
2. Configure a plan with a primary copy having datapth MA1 and a secondary cloud copy having datapath MA2
3. run backups to the policy
4. run auxcopy to secondary copy
5. if Storage Accelerator package is present on client, MA1 in this case(present by default since this is a Media agent)
    we will override the default pipeline and instead use MA1 to write directly to cloud lib
6. validate that we made use of Storage accelerator mode for auxcopy
7. deallocate resources
"""
import time
from time import sleep
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super().__init__()
        self.name = "Storage Accelerator mode for Auxcopy Validation Testcase"
        self.tcinputs = {
            "MediaAgentName1": None,
            "CloudLibraryMA": None,
            "CloudLibrary": None
        }
        self.cs_name = None
        self.mount_path = None
        self.dedup_store_path1 = None
        self.dedup_store_path2 = None
        self.content_path = None
        self.storage_pool_name = None
        self.storage_pool_name2 = None
        self.cloud_library_name = None
        self.plan_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.sidb_id = None
        self.job_ids = []
        self.aux_job_id = None
        self.primary_objs = []
        self.secondary_objs = []
        self.testcase_path = None
        self.cs_machine = None
        self.client_machine = None
        self.media_agent1 = None
        self.media_agent2 = None
        self.media_agent_machine1 = None
        self.media_agent_machine2 = None
        self.media_agent_obj1 = None
        self.media_agent_obj2 = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.testcase_path_media_agent1 = None
        self.testcase_path_media_agent2 = None
        self.media_agent_path = None
        self.storage_pool = None
        self.storage_pool2 = None
        self.pool = None
        self.cloud_library = None
        self.pool_name = None
        self.pool_name_2 = None
        self.pool = None
        self.pool2 = None
        self.plan = None
        self.backup_set = None
        self.subclient = None
        self.dedupe_engine = None
        self.primary_copy = None
        self.secondary_copy_name = None
        self.secondary_copy = None
        self.is_user_defined_storpool1 = False
        self.is_user_defined_storpool2 = False
        self.is_user_defined_dedup1 = False
        self.is_user_defined_dedup2 = False
        self.dedup_store_path_ma1_1 = None
        self.dedup_store_path_ma1_2 = None
        self.result_string = ""

    def setup(self):
        """Setup function of this test case"""
        if not self.tcinputs.get("storage_pool_name2") and not self.tcinputs.get("CloudLibrary"):
            self.log.error("""ERROR ::: Must provide either a storage pool for secondary copy <storage_pool_name2>, 
                                        or cloud library <CloudLibrary> as input!""")
            raise Exception("Missing input parameters for secondary copy creation!")
        if self.tcinputs.get("MediaAgentName1") == self.tcinputs.get("CloudLibraryMA"):
            raise Exception("The two input Media agents must not be the same!")
        # add datapath check for MA1 in cloudlib
        if self.tcinputs.get("storage_pool_name"):
            self.is_user_defined_storpool1 = True
        if self.tcinputs.get("storage_pool_name2"):
            self.is_user_defined_storpool2 = True
        if self.tcinputs.get("dedup_path1"):
            self.is_user_defined_dedup1 = True
        if self.tcinputs.get("dedup_path2"):
            self.is_user_defined_dedup2 = True

        self.cs_name = self.commcell.commserv_client.name
        self.media_agent1 = self.tcinputs["MediaAgentName1"]
        self.media_agent2 = self.tcinputs["CloudLibraryMA"]
        self.cloud_library_name = self.tcinputs["CloudLibrary"]

        suffix = f"{self.media_agent1}_{str(self.client.client_name)}"
        self.plan_name = f"{self.id}_Plan{suffix}"
        self.backupset_name = f"{self.id}_BS{suffix}"
        self.subclient_name = f"{self.id}_SC{suffix}"

        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.media_agent_obj1 = self.commcell.media_agents.get(self.media_agent1)
        self.media_agent_obj2 = self.commcell.media_agents.get(self.media_agent2)

        if self.is_user_defined_storpool1:
            self.storage_pool_name = self.tcinputs["storage_pool_name"]
            self.pool = self.commcell.storage_pools.get(self.storage_pool_name)
        if self.is_user_defined_storpool2:
            self.storage_pool_name2 = self.tcinputs["storage_pool_name2"]
            self.pool2 = self.commcell.storage_pools.get(self.storage_pool_name2)

        self.pool_name = "{0}_Pool{1}".format(str(self.id), suffix)
        self.pool_name_2 = "{0}_Pool{1}_2".format(str(self.id), suffix)

        self.client_machine, self.testcase_path_client = self.mm_helper.generate_automation_path(self.tcinputs['ClientName'], 25*1024)
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        self.media_agent_machine1, self.testcase_path_media_agent1 = self.mm_helper.generate_automation_path(self.tcinputs['MediaAgentName1'], 25*1024)
        self.media_agent_machine2, self.testcase_path_media_agent2 = self.mm_helper.generate_automation_path(
            self.tcinputs['CloudLibraryMA'], 25 * 1024)

        if not self.is_user_defined_dedup1 and "unix" in self.media_agent_machine1.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.is_user_defined_dedup2 and "unix" in self.media_agent_machine1.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")

        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        self.mount_path = self.media_agent_machine1.join_path(
            self.testcase_path_media_agent1, "mount_path")

        if self.is_user_defined_dedup1:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path1 = self.tcinputs["dedup_path1"]
            self.dedup_store_path_ma1_1 = self.media_agent_machine1.join_path(
                self.dedup_store_path1, "dedup_store_path1")
            self.dedup_store_path_ma1_2 = self.media_agent_machine1.join_path(
                self.dedup_store_path1, "dedup_store_path2")
        else:
            self.dedup_store_path_ma1_1 = self.media_agent_machine1.join_path(
                self.testcase_path_media_agent1, "dedup_store_path1")
            self.dedup_store_path_ma1_2 = self.media_agent_machine1.join_path(
                self.testcase_path_media_agent1, "dedup_store_path2")

        if self.is_user_defined_dedup2:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path2 = self.tcinputs["dedup_path2"]
        else:
            self.dedup_store_path2 = self.media_agent_machine2.join_path(
                self.testcase_path_media_agent2, "dedup_store_path")

        # # Check for the MA package on source machine for auxcopy, raise error if not present.
        self.log.info(f"Check if source machine {self.media_agent1} (with respect to auxcopy) has MA package installed or not.")
        if self._validate_mapackage(self.media_agent_obj1.media_agent_id) is True:
            self.log.info(f"source machine {self.media_agent1} has MA package installed on it.")
        else:
            self.log.error(f"selected source machine {self.media_agent1} does not have MA package installed on it.")
            raise Exception("MA package missing on source machine!")
        # Check global configuration parameter value
        self.log.info("Check what is the value of SA global config parameter value.")
        if self._sa_global_param is False:
            self.log.error("SA is disabled on the commcell, enable it and re-run the case.")
            raise Exception("SA is disabled on the commcell, enable the service configuration "
                            "'Config parameter to enable the storage accelerator feature'")
        else:
            self.log.info("SA is enabled on CS. Proceeding with the case run.")

    def new_content(self, dir_path, dir_size):
        """
        generates new incompressible data in given directory/folder

            Args:
                dir_path        (str)       full path of directory/folder in which data is to be added
                dir_size        (float)     size of data to be created(in GB)

        returns None
        """
        if self.client_machine.check_directory_exists(dir_path):
            self.client_machine.remove_directory(dir_path)
        self.client_machine.create_directory(dir_path)
        self.opt_selector.create_uncompressable_data(client=self.client_machine,
                                                     size=dir_size,
                                                     path=dir_path)

    def deallocate_resources(self):
        """removes all resources allocated by the Testcase"""
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info("content_path deleted")
        else:
            self.log.info("content_path does not exist.")

        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.backup_set = self.agent.backupsets.get(self.backupset_name)
            self.subclient = self.backup_set.subclients.get(self.subclient_name)
            if self.backup_set.subclients.has_subclient(self.subclient_name):
                self.subclient.plan = None
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("backup set deleted")
        else:
            self.log.info("backup set does not exist")

        if self.commcell.plans.has_plan(self.plan_name):
            self.commcell.plans.delete(self.plan_name)
            self.log.info("plan deleted")
        else:
            self.log.info("plan does not exist.")

        if not self.is_user_defined_storpool1:
            # here the storage pool is automatically created by pool and therefore has the same name as pool.
            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.commcell.storage_pools.delete(self.pool_name)
                self.log.info("pool deleted")
                self.commcell.storage_pools.refresh()
            else:
                self.log.info("pool does not exist.")

        if not self.is_user_defined_storpool2:
            # here the storage pool is automatically created by pool and therefore has the same name as pool.
            if self.commcell.storage_pools.has_storage_pool(self.pool_name_2):
                self.commcell.storage_pools.delete(self.pool_name_2)
                self.log.info("pool deleted")
                self.commcell.storage_pools.refresh()
            else:
                self.log.info("pool does not exist.")

        data_aging_job = self.mm_helper.submit_data_aging_job()
        self.log.info(f"Data Aging job {data_aging_job.job_id} has started.")
        if not data_aging_job.wait_for_completion():
            self.log.error(
                f"Data Aging job {data_aging_job.job_id} has failed with {data_aging_job.delay_reason}.")
            raise Exception(
                f"Data Aging job {data_aging_job.job_id} has failed with {data_aging_job.delay_reason}.")
        self.log.info(f"Data Aging job [{data_aging_job.job_id}] has completed.")

        self.log.info("clean up successful")

    def previous_run_clean_up(self):
        """delete the resources from previous run """
        self.log.info("********* previous run clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.error(f"previous run clean up ERROR ::: {exp}")
            raise Exception(f"ERROR:{exp}")

    def allocate_resources(self):
        """creates all necessary resources for testcase to run"""
        # create dedupe store paths
        if self.media_agent_machine1.check_directory_exists(self.dedup_store_path_ma1_1):
            self.log.info("store path 1-1 directory already exists")
        else:
            self.media_agent_machine1.create_directory(self.dedup_store_path_ma1_1)
            self.log.info("store path 1-1 created")
        if self.media_agent_machine1.check_directory_exists(self.dedup_store_path_ma1_2):
            self.log.info("store path 1-2 directory already exists")
        else:
            self.media_agent_machine1.create_directory(self.dedup_store_path_ma1_2)
            self.log.info("store path 1-2 created")

        if self.media_agent_machine2.check_directory_exists(self.dedup_store_path2):
            self.log.info("store path 2 directory already exists")
        else:
            self.media_agent_machine2.create_directory(self.dedup_store_path2)
            self.log.info("store path 2 created")

        # creation of pool
        if not self.is_user_defined_storpool1:
            self.log.info("Creating the storage pool1")
            self.pool = self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                                        self.tcinputs['MediaAgentName1'],
                                                        [self.tcinputs['MediaAgentName1'], self.tcinputs['MediaAgentName1']],
                                                        [self.dedup_store_path_ma1_1, self.dedup_store_path_ma1_2])

        if not self.is_user_defined_storpool2:
            self.log.info("Creating the storage pool2")
            self.pool2 = self.dedup_helper.configure_global_dedupe_storage_policy(self.pool_name_2,
                                                                                  self.cloud_library_name,
                                                                                  self.media_agent2,
                                                                                  self.dedup_store_path2,
                                                                                  self.media_agent2)

        # creation of plan
        self.log.info(f"Plan Present: {self.commcell.plans.has_plan(self.plan_name)}")
        self.log.info(f"Creating the Plan [{self.plan_name}]")
        self.commcell.plans.refresh()
        self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
        self.log.info(f"Plan [{self.plan_name}] created")

        # disabling the schedule policy
        self.log.info('Disabling the schedule policy')
        self.plan.schedule_policies['data'].disable()

        # add backupset
        self.log.info(f"Adding the backup set [{self.backupset_name}]")
        self.backupset = self.mm_helper.configure_backupset(self.backupset_name)
        self.log.info(f"Backup set Added [{self.backupset_name}]")

        # add subclient
        self.log.info(f"Adding the subclient set [{self.subclient_name}]")
        self.subclient = self.backupset.subclients.add(self.subclient_name)
        self.log.info(f"Subclient set Added [{self.subclient_name}]")

        # Add plan and content to the subclient
        self.client_machine.create_directory(self.content_path)
        self.log.info("Adding plan to subclient")
        self.subclient.plan = [self.plan, [self.content_path]]
        self.log.info("Added plan to subclient")

        # create primary copy object for storage policy
        self.log.info("Getting primary copy")
        self.primary_copy = self.plan.storage_policy.get_copy("Primary")
        self.log.info("Got primary copy")

        # create secondary copy for storage policy
        self.log.info("Adding secondary copy")
        self.secondary_copy_name = self.plan_name + '_secondary'
        self.commcell.storage_pools.refresh()
        self.log.info("pool Present: ", self.commcell.storage_pools.has_storage_pool(self.pool_name_2))
        self.plan.add_storage_copy(self.secondary_copy_name, self.pool_name_2)
        self.secondary_copy = self.plan.storage_policy.get_copy(self.secondary_copy_name)
        self.log.info("Added secondary copy..")

        # Remove Association with System Created AutoCopy Schedule
        self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.secondary_copy_name)

        # set multiple readers for subclient
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True

        # set enc on primary copy BlowFish 128
        self.primary_copy.set_encryption_properties(re_encryption=True, encryption_type="BlowFish",
                                                                       encryption_length=128)
        # set re-encrypt on secondary as GOST 256
        self.secondary_copy.set_encryption_properties(re_encryption=True, encryption_type="GOST",
                                                                        encryption_length=256)

    def run_aux_copy(self):
        """
        run auxcopy job for the subclient specified in Testcase

            Args:

        returns job id(int)
        """
        job = self.plan.storage_policy.run_aux_copy()
        self.log.info("*" * 10 + f" Starting Auxcopy job {job.job_id} " + "*" * 10)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run auxcopy with error: {0}".format(job.delay_reason)
            )
        self.log.info(f"Auxcopy job: {job.job_id} completed successfully")
        return job.job_id

    def _validate_mapackage(self, clientid):
        """
        Validate if windows client also has mediaagent package installed or not.
        Args:
            Clientid -- This is the client id for which we are verifying packages installed.
        Return:
            (Bool) True if it exists
            (Bool) False if doesn't exists
        """
        query = f""" select count(1) from simInstalledPackages where simPackageID = 51
                        and ClientId = {clientid}"""
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] == '0':
            return False
        return True

    def _sa_global_param(self):
        """
        Validate if media managament service configuration parameter "MMCONFIG_CONFIG_STORAGE_ACCELERATOR_ENABLED" is
        enabled or disabled.
        Args:

        Return:
            (Bool) True if enabled
            (Bool) False if disabled
        """
        query = f""" select value from MMConfigs where name = 'MMCONFIG_CONFIG_STORAGE_ACCELERATOR_ENABLED'"""
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] == '1':
            return True
        return False

    def _run_backup(self, subclient_obj, backup_type):
        """
        Initiates backup job and waits for completion
        Args:
            subclient_obj (object) -- subclient object on which backup is initiated
            backup_type (str)      -- backup type to initiate
                                      Eg: full, incremental
        Return:
            (int) backup job_id
        """
        self.log.info("*" * 10 + f" Starting Subclient {backup_type} Backup " + "*" * 10)
        job = subclient_obj.backup(backup_type)
        self.log.info(f"Started {backup_type} backup with Job ID: {job.job_id}")
        if not job.wait_for_completion():
            self.log.error(f"Backup job {job.job_id} has failed with {job.delay_reason}.")
            raise Exception(f"Backup job {job.job_id} has failed with {job.delay_reason}.")
        self.log.info(f"Successfully finished {backup_type} backup job: {job.job_id}")
        return job.job_id

    def validateDestinationMA(self, auxcopyJobId):
        """
        Validates whether the source and destination MAs are the same, which is expected in case of SA mode

        Return:
            (Bool) True if validation passes
            (Bool) False if doesn't

        Raises Exception:
            if source MA and destination MA do not match
        """
        query = f"""select name from app_client where id in
                    (select distinct destMAId from archJobStreamStatus where jobId = {auxcopyJobId})"""
        self.log.info(f"executing query :: {query}")
        self.csdb.execute(query)
        destMA = [row[0] for row in self.csdb.rows]
        if len(destMA) > 1:
            self.log.error(f"More than one MA was used! query result --> {destMA}")
            return False
        self.log.info(f"output of query :: {destMA}")
        if destMA[0] == self.media_agent1:
            self.log.info(f"source and destination MA {destMA} are the same. Override took place.")
            self.result_string += "Destination MA validation via CSDB :: PASSED |  \n"
            return True
        self.log.error(f"ERROR ::: source MA {self.media_agent1} and destination MA {destMA} are different! Override did not take place! SA mode was not honored!")
        self.result_string += "Destination MA validation via CSDB :: FAILED |  \n"
        return False

    def validateLogs(self, auxcopyJobId):
        """
        Verifies if override is logged, and checks further if chunk creation was triggered from source MA as part of override

        Return:
            (Bool) True if validation passes
            (Bool) False if doesn't

        Raises Exception :
            if override logging is missing
            if chunk creation logging is missing
        """
        archmgr_log_string = f'Overriding dest MA as this is detected as CORE MA' \
                             f'[{self.media_agent_obj1.media_agent_id}]'
        self.log.info(f"Parse string [{archmgr_log_string}] for Auxcopy job : {auxcopyJobId}")
        parse_result1 = self.dedup_helper.parse_log(self.commcell.commserv_name, 'ArchMgr.log',
                                                    archmgr_log_string, jobid=auxcopyJobId)
        if parse_result1[0]:
            self.log.info("Validated, over-ride was done to use Client as SA by ArchMgr.")
            self.log.info("Checking in Client cvd log for chunk creation")
            client_cvd_log_string = 'Creating new chunk id'
            parse_result2 = self.dedup_helper.parse_log(self.media_agent1, 'cvd.log',
                                                        client_cvd_log_string, jobid=auxcopyJobId)
            if parse_result2[0]:
                self.log.info("Validated, chunks are created by client. SA package is used.")
                self.result_string += "Override validation via logs :: PASSED |  \nchunk creation validation via logs :: PASSED"
                return True
            self.log.error("ERROR ::: Chunk not created by client, SA package not used.")
            self.result_string += "Override validation via logs :: PASSED |  \nchunk creation validation via logs :: FAILED"
            return False
        self.log.error("ERROR ::: ArchMgr didn't override to use client as SA.")
        self.result_string += "Override validation via logs :: FAILED |  chunk creation validation via logs :: FAILED"
        return False

    def get_objects(self, job_id, copy_name):
        """
            Gets the Primary and Secondary objects of the given copy name

            Args:
            job_id (integer) -- job_id of backup
            copy_name (str)      --  name of the copy

            Return:
                number of primary objects, number of secondary objects.
        """
        primary_objects = self.dedup_helper.get_primary_objects_sec(job_id, copy_name)
        secondary_objects = self.dedup_helper.get_secondary_objects_sec(job_id, copy_name)
        self.log.info(f"Primary objects: {primary_objects}")
        self.log.info(f"Secondary objects: {secondary_objects}")

        return primary_objects, secondary_objects

    def get_copy_objects(self, copy_name):
        """
            Stores Primary and Secondary objects and store it in primary_obj and secondary_obj arrays
            Args:
            copy_name (str)      --  name of the copy
        """
        total_primary_objects = 0
        total_secondary_objects = 0

        for i in range(len(self.job_ids)):
            primary_objects, secondary_objects = self.get_objects(self.job_ids[i], copy_name)
            total_primary_objects += int(primary_objects)
            total_secondary_objects += int(secondary_objects)

        self.log.info(f"Primary_objects primary: {total_primary_objects}")
        self.log.info(f"Secondary_objects primary: {total_secondary_objects}")
        self.primary_objs.append(total_primary_objects)
        self.secondary_objs.append(total_secondary_objects)

    def verify_block_size(self):
        """ verifies that cloud has 128KB of block size internally """
        self.log.info("Getting the primary copy primary and secondary objects")
        self.get_copy_objects(copy_name="Primary")

        self.log.info("Getting the secondary copy primary and secondary objects")
        self.get_copy_objects(copy_name=self.secondary_copy_name)

        self.log.info("********** CASE: Verify if cloud internally uses 128KB block size **********")

        if self.primary_objs[0] + self.secondary_objs[0] == self.primary_objs[1] + self.secondary_objs[1]:
            self.log.info("The total number of objects created are same.")
            self.log.info("Cloud storage-pool and primary storage-pool are using the same block size.")
        else:
            self.log.info("Cloud storage-pool and primary storage-pool are not using the same block size.")

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            # checking if dedup enabled
            if self.primary_copy.is_dedupe_enabled():
                self.log.info("dedup enabled..!")
            else:
                self.log.error("dedup not enabled..!")
                raise Exception(f"dedup not enabled on plan {self.plan_name}")

            # run backups
            job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full']

            for sequence_index in range(0, 4):
                # Create unique content
                if job_types_sequence_list[sequence_index] != 'synthetic_full':
                    self.log.info(f"Generating data at {self.content_path}")
                    if not self.client_machine.generate_test_data(self.content_path, dirs=1, file_size=(20 * 1024),
                                                                  files=2):
                        self.log.error(f"Unable to generate data at {self.content_path}")
                        raise Exception(f"unable to Generate Data at {self.content_path}")
                    self.log.info(f"Generated data at {self.content_path}")
                job_id = self._run_backup(self.subclient, job_types_sequence_list[sequence_index])
                time.sleep(60)
                self.job_ids.append(job_id)

            # run auxcopy
            auxcopy = self.run_aux_copy()

            self.verify_block_size()

            # do validations for auxcopy job
            self.log.info("*" * 10 + " Starting Validations for Auxcopy job " + "*" * 10)
            if self.validateDestinationMA(auxcopy) or self.validateLogs(auxcopy):
                self.log.info("All Validations Completed.. Testcase executed successfully..")
                self.log.info(self.result_string)
            else:
                self.log.info(self.result_string)
                raise Exception("SA Auxcopy validations failed!")

        except Exception as exp:
            self.log.error(f'Failed to execute test case with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        # removing initialized resources
        try:
            self.deallocate_resources()
        except Exception as exp:
            self.log.warning(f"Cleanup Failed, please check setup. Exception : {exp}")

