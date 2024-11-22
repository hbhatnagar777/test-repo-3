# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()  --  initialize TestCase class

    run()  --  run function of this test case

    setup()  --  Setup function of this test case

    power_off_all_cloud_mediaagents()   -   Power-off all cloud MediaAgents

    power_on_all_cloud_mediaagents()    -   Power-on all cloud MediaAgents

    verify_mediaagents_are_on() -   Verifies if the MediaAgents are power-on

    create_pseudo_client()  --  Creates Pseudo client (cloud controller)

    create_multi_partitioned_pool() -   Creates multti partitioned storage pool

    create_secondary_copy()  --  Creates aux copy

    create_multi_partitioned_pool()  --  Creates dedupe storage pool

    verify_non_cloud_media_agents()  --  Verify that PowerManagemet is disabled

    cleanup()  --  Cleanup SC, BS,SP, Library

    tear_down() --  Tear Down Function of this Case

    Input Example:

    "testCases": {
				"57931": {
					"ClientName": "client1",
					"AgentName": "File System",
					"CloudMA1": "MA1",
					"MA1":"MA2",
					"MA2":"MA3",
					"MA3":"MA4",
					"PsudoClientName": "MyAzure",
					"VSAProxyForPsudoClient":"proxy1",
					"AzureSubsID":"****",
					"AzureTenantID":"****",
					"AzureAppID":"****",
					"AzureAppPassword":"****"
				}
                }
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper, PowerManagement


class TestCase(CVTestCase):
    """Power Management Aux Copy :: Primary Copy-Non-Cloud and Aux Copy-cloud and DDB1-Non-cloud and DDB2-non-Cloud"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Power Management Aux Copy :: Primary Copy-Non-Cloud and Aux Copy-cloud and DDB1-Non-cloud and DDB2-non-Cloud"

        self.storage_policy = None
        self.sub_client = None
        self.source_ma = None
        self.destination_ma = None
        self.ddb_ma1 = None
        self.ddb_ma2 = None
        self.ddb_ma1_obj = None
        self.source_ma_obj = None
        self.destination_ma_obj = None
        self.ddb_ma2_obj = None
        self.backup_set = None
        self.mm_helper = None
        self.ddb_ma1_obj = None
        self.source_ma_obj = None
        self.destination_ma_obj = None
        self.ddb_ma2_obj = None
        self.source_ma_machine = None
        self.destination_ma_machine = None
        self.client_machine = None
        self.source_ma_drive = None
        self.destination_ma_drive = None
        self.ddb_ma1_drive = None
        self.ddb_ma2_drive = None
        self.client_drive = None
        self.source_ma_path = None
        self.destination_ma_path = None
        self.ddb_ma1_path = None
        self.ddb_ma2_path = None
        self.client_path = None
        self.source_library_path = None
        self.destination_library_path = None
        self.ddb1_path = None
        self.ddb2_math = None
        self.client_content = None
        self.sp_obj = None
        self.pool_primary_copy_name = None
        self.pool_obj = None
        self.copy_name1 = None
        self.copy_name2 = None
        self.storage_pool = None
        self.storage_pool_obj = None
        self.secondary_pool1 = None
        self.secondary_pool2 = None
        self.is_case_failed = None
        self.is_source_ma_directory_created = None
        self.is_destination_ma_directory_created = None
        self.is_ddb_ma1_directory_created = None
        self.is_ddb_ma2_directory_created = None
        self.is_client_directory_created = None
        self.power_management = None
        self.ma_helper = None
        self.dedupe_helper = None
        self.ddb_ma1_machine = None
        self.ddb_ma2_machine = None
        self.ddb2_path = None
        self.backup_set_obj = None
        self.job_obj = None
        self.path_suffix = None
        self.store_o = None
        self.source_ddb_path = None

        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "CloudMA1": None,
            "MA1": None,
            "MA2": None,
            "MA3": None,
            "PsudoClientName": None,
            "VSAProxyForPsudoClient": None,
            "AzureSubsID": None,
            "AzureTenantID": None,
            "AzureAppID": None,
            "AzureAppPassword": None
        }

    def setup(self):
        """Setup function of this test case"""

        utility = OptionsSelector(self.commcell)
        self.log.info("Starting test case setup")
        self.storage_policy = f"PowerManagement_{self.id}_SP"
        self.sub_client = f"PowerManagement_{self.id}_SC"
        self.backup_set = f"PowerManagement_{self.id}_BS"
        self.source_ma = self.tcinputs['MA1']
        self.destination_ma = self.tcinputs['CloudMA1']
        self.ddb_ma1 = self.tcinputs['MA2']
        self.ddb_ma2 = self.tcinputs['MA3']
        self.client = self.tcinputs['ClientName']
        self.copy_name1 = "auxCopy1"
        self.copy_name2 = "auxCopy2"
        self.storage_pool = f"PowerManagement_{self.id}_Primary_Pool"
        self.secondary_pool1 = f"PowerManagement_{self.id}_Sec_Pool1"
        self.secondary_pool2 = f"PowerManagement_{self.id}_Sec_Pool2"
        self.log.info("Creating all MA objects")
        self.ddb_ma1_obj = self.commcell.media_agents.get(self.ddb_ma1)
        self.source_ma_obj = self.commcell.media_agents.get(self.source_ma)
        self.destination_ma_obj = self.commcell.media_agents.get(self.destination_ma)
        self.ddb_ma2_obj = self.commcell.media_agents.get(self.ddb_ma2)
        self.log.info("Done. Created all MA objects")

        self.ma_helper = MMHelper(self)
        self.power_management = PowerManagement()
        self.dedupe_helper = DedupeHelper(self)

        # all MAs and client have to be unique
        list_of_ma = [self.source_ma, self.destination_ma, self.ddb_ma1, self.ddb_ma2, self.tcinputs['ClientName']]
        if len(set(list_of_ma)) != 5:
            raise Exception(
                'Each MediaAgent and client have to be unique machine. Make sure you have provided 4 unique MediaAgents and one client.')

        # Checking if the PsudoClientName exists, else creating that
        if self._commcell.clients.has_client(self.tcinputs['PsudoClientName']):
            self.log.info("Psudo exists. Not creating a new one")
        else:
            self.log.info(
                f"Pseudo client(cloud controller) is not present with name [{self.tcinputs['PsudoClientName']}]")
            self.create_pseudo_client()

        # Verifying the non-power managed MAs
        self.verify_non_cloud_media_agents()

        # Verify and Configure cloud MA
        self.power_management.configure_cloud_mediaagent(self.tcinputs['PsudoClientName'], self.destination_ma_obj)

        self.log.info("Powering-on MediaAgents")
        self.power_on_all_cloud_mediaagents()

        self.log.info("Getting paths for all machines")
        (
            self.ddb_ma1_machine,
            self.ddb_ma1_drive,
        ) = self.ma_helper.generate_automation_path(self.ddb_ma1, 12000)
        (
            self.ddb_ma2_machine,
            self.ddb_ma2_drive,
        ) = self.ma_helper.generate_automation_path(self.ddb_ma2, 12000)
        (
            self.source_ma_machine,
            self.source_ma_drive,
        ) = self.ma_helper.generate_automation_path(self.source_ma, 12000)
        (
            self.destination_ma_machine,
            self.destination_ma_drive,
        ) = self.ma_helper.generate_automation_path(self.destination_ma, 12000)
        (
            self.client_machine,
            self.client_drive,
        ) = self.ma_helper.generate_automation_path(self.client, 12000)

        self.log.info("Generating parent paths for all MAs and client")

        self.log.info("Generating paths")

        self.source_library_path = self.source_ma_drive + "MP"
        self.log.info(f"Source library path : {self.source_library_path}")

        self.source_ddb_path = self.source_ma_drive + "DDB"
        self.log.info(f"Source copy DDB path: {self.source_ddb_path}")

        self.destination_library_path = self.destination_ma_drive + "MP"
        self.log.info(f"Destination library path : {self.destination_library_path}")

        self.ddb1_path = self.ddb_ma1_drive + "DDB"
        self.log.info(f"DDB path [{self.ddb1_path}] on MA[{self.ddb_ma1}]")

        self.ddb2_path = self.ddb_ma2_drive + "DDB"
        self.log.info(f"DDB path [{self.ddb2_path}] on MA[{self.ddb_ma2}]")

        self.client_content = self.client_drive + "subclient_content"
        self.log.info(f"Client content: {self.client_content}")

    def power_off_all_cloud_mediaagents(self):
        """
        Power-off all cloud MediaAgents
        """
        self.power_management.power_off_media_agents([self.destination_ma_obj,])

    def power_on_all_cloud_mediaagents(self):
        """
        Power-on all cloud MediaAgents
        """
        self.power_management.power_on_media_agents([self.destination_ma_obj,])

    def verify_mediaagents_are_on(self, ma_obj_list):
        """
        Verifies if the MediaAgents are power-on

        Args:
            ma_obj_list (list) - list of MediaAgent class object to verify
        """
        for ma in ma_obj_list:
            ma.refresh()
            if ma.is_online:
                self.log.info(f"MediaAgent [{ma.media_agent_name}] is online. Verification successful")
                continue
            self.log.error(f"MediaAgent [{ma.media_agent_name}] should be online. Verification failed.")
            raise Exception(f"MediaAgent [{ma.media_agent_name}] should be online")

    def create_pseudo_client(self):
        """
        Creates Pseudo client (cloud controller)
        """

        self.log.info(f"Creating Azure pseudo client(cloud controller) [{self.tcinputs['PsudoClientName']}]")

        self.commcell.clients.add_azure_client(self.tcinputs['PsudoClientName'],
                                               self.tcinputs['VSAProxyForPsudoClient'], azure_options={
                "subscription_id": self.tcinputs['AzureSubsID'],
                "tenant_id": self.tcinputs['AzureTenantID'],
                "application_id": self.tcinputs['AzureAppID'],
                "password": self.tcinputs['AzureAppPassword'],
            })
        self.log.info("Created successfully")

    def create_multi_partitioned_pool(self, pool_name):
        """
        Creates secondary copy
        Args:
            pool_name (str) - Storage Pool name
        """
        self.log.info(f"Creating Storage Pool [{pool_name}]")
        pool_obj = self.commcell.storage_pools.add(pool_name, self.destination_library_path, self.destination_ma_obj,
                                                   self.ddb_ma1_obj, self.ddb1_path)
        self.is_ddb_ma1_directory_created = True
        self.log.info("Storage pool created with one partition. Adding 2nd partition")

        self.ddb_engine_o = self.commcell.deduplication_engines.get(pool_obj.storage_pool_name, pool_obj.copy_name)
        store_id = self.ddb_engine_o.all_stores[0]
        self.store_o = self.ddb_engine_o.get(int(store_id[0]))
        self.store_o.add_partition(self.ddb2_path, self.ddb_ma2)
        self.is_ddb_ma2_directory_created = True

        self.log.info(f"Storage Pool [{pool_name}] created successfully")

    def create_secondary_copy(self, pool_name, copy_name):
        """
        Creates secondary copy
        Args:
            pool_name (str) - Storage Pool name
            copy_name ( str) - Secondary copy name
        """
        self.log.info("Powering-on all MAs")
        self.power_on_all_cloud_mediaagents()
        self.create_multi_partitioned_pool(pool_name)
        self.log.info(f"Creating copy [{copy_name}] with storage pool [{pool_name}]")
        self.sp_obj.create_secondary_copy(copy_name, global_policy=pool_name)
        self.log.info(f"Copy[{copy_name}] created successfully")

        self.log.info(f"Removing copy [{copy_name}] from auto copy schedule")
        self.ma_helper.remove_autocopy_schedule(self.storage_policy, copy_name)

    def verify_non_cloud_media_agents(self):
        """
            Verify that PowerManagemet is disabled
        """
        if self.source_ma_obj._is_power_management_enabled or self.ddb_ma1_obj._is_power_management_enabled or self.ddb_ma2_obj._is_power_management_enabled:
            raise Exception('Expected non-power managed MediaAgent')

    def cleanup(self):
        """Cleanup SC, BS,SP, Library """

        self.log.info("Deleting BackupSet if exists")
        if self._agent.backupsets.has_backupset(self.backup_set):
            self.log.info(f"BackupSet[{self.backup_set}] exists, deleting that")
            self._agent.backupsets.delete(self.backup_set)

        self.log.info("Deleting Storage Policy if exists")
        if self.commcell.storage_policies.has_policy(self.storage_policy):
            self.log.info(f"Storage Policy[{self.storage_policy}] exists")
            self.log.info("Reassociating all sub clients before deleting the SP")
            self.sp_obj_to_reassociate = self.commcell.storage_policies.get(self.storage_policy)
            self.sp_obj_to_reassociate.reassociate_all_subclients()
            self.log.info(f"Deleting the SP {self.storage_policy}")
            self.commcell.storage_policies.delete(self.storage_policy)

        self.log.info(f"Deleting Storage Pool[{self.storage_pool}] if exists")
        if self.commcell.storage_policies.has_policy(self.storage_pool):
            self.log.info(f"Storage Pool [{self.storage_pool}] exists, deleting that")
            self.commcell.storage_policies.delete(self.storage_pool)

        self.log.info(f"Deleting Storage Pool[{self.secondary_pool1}] if exists")
        if self.commcell.storage_policies.has_policy(self.secondary_pool1):
            self.log.info(f"Storage Pool [{self.secondary_pool1}] exists, deleting that")
            self.commcell.storage_policies.delete(self.secondary_pool1)

        self.log.info(f"Deleting Storage Pool[{self.secondary_pool2}] if exists")
        if self.commcell.storage_policies.has_policy(self.secondary_pool2):
            self.log.info(f"Storage Pool [{self.secondary_pool2}] exists, deleting that")
            self.commcell.storage_policies.delete(self.secondary_pool2)

        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")

        self.log.info("Powering-on MediaAgents for clean up")
        self.power_on_all_cloud_mediaagents()

        self.log.info(f"Disabling Ransomware [{self.source_ma}]")
        self.source_ma_obj.set_ransomware_protection(False)

        self.log.info(f"Disabling Ransomware [{self.destination_ma}]")
        self.destination_ma_obj.set_ransomware_protection(False)

        self.log.info(f"Disabling Ransomware [{self.ddb_ma1}]")
        self.ddb_ma1_obj.set_ransomware_protection(False)

        self.log.info(f"Disabling Ransomware [{self.ddb_ma2}]")
        self.ddb_ma2_obj.set_ransomware_protection(False)

        try:
            if not self.is_case_failed:
                self.log.info("Test case completed, deleting BS, SP, Library")
                self.cleanup()
            else:
                self.log.info("Test case failed, NOT deleting SC, BS, SP, Library")

            if self.is_client_directory_created:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_drive, self.client_machine)

            if self.is_source_ma_directory_created:
                self.log.info(f"Deleting [{self.source_ma_drive}] on {self.source_ma}")
                self.ma_helper.remove_content(self.source_ma_drive, self.source_ma_machine)

            if self.is_destination_ma_directory_created:
                self.log.info(f"Deleting [{self.destination_ma_drive}] on {self.destination_ma}")
                self.ma_helper.remove_content(self.destination_ma_drive, self.destination_ma_machine)

            if self.is_ddb_ma1_directory_created:
                self.log.info(f"Deleting [{self.ddb_ma1_drive}] on {self.ddb_ma1}")
                self.ma_helper.remove_content(self.ddb_ma1_drive, self.ddb_ma1_machine)

            if self.is_ddb_ma2_directory_created:
                self.log.info(f"Deleting [{self.ddb_ma2_drive}] on {self.ddb_ma2}")
                self.ma_helper.remove_content(self.ddb_ma2_drive, self.ddb_ma2_machine)

        except Exception as excp:
            self.log.error(f"Cleanup failed with error: {excp}")
            self.result_string = str(f"Cleanup failed. {excp}")

    def run(self):
        try:

            self.log.info("Cleaning-up SC,BS,SP, Libraries if exists")
            self.cleanup()

            # Creating storage pool
            self.log.info(f"Creating storage pool [{self.storage_pool}]")
            self.pool_obj = self.commcell.storage_pools.add(self.storage_pool, self.source_library_path,
                                                            self.source_ma_obj, self.source_ma_obj,
                                                            self.source_ddb_path)
            self.log.info("Storage pool created successfully")

            # Creating SP
            self.log.info(f"Creating storage policy[{self.storage_policy}]")
            self.sp_obj = self.commcell.storage_policies.add(self.storage_policy, global_policy_name=self.storage_pool,
                                                             global_dedup_policy=False)
            self.log.info("Storage Policy created successfully")

            # Creating secondary copy
            self.create_secondary_copy(self.secondary_pool1, self.copy_name1)
            self.create_secondary_copy(self.secondary_pool2, self.copy_name2)

            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(self.client, self.client_content, 0.5)
            self.is_client_directory_created = True

            # creating backup set
            self.log.info("Creating backup set")
            self.backup_set_obj = self._agent.backupsets.add(self.backup_set)

            # Creating sub client
            self.log.info(f"Creating subclient[{self.sub_client}]")
            self.subclient = self.ma_helper.configure_subclient(self.backup_set, self.sub_client, self.storage_policy,
                                                                self.client_content)

            # Starting backup
            self.log.info("Starting backup")
            self.job_obj = self.subclient.backup("FULL")
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.ma_helper.wait_for_job_completion(self.job_obj)

            # Powering off the Cloud MA for aux copy (DASH job) job to a single copy
            self.log.info("Powering off the cloud MAs for next aux job [One Copy + DASH]")
            self.power_off_all_cloud_mediaagents()
            self.log.info("Successfully powered-off. Starting aux copy [One Copy + DASH] job")
            self.job_obj = self.sp_obj.run_aux_copy(self.copy_name1, use_scale=True, all_copies=False)
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.ma_helper.wait_for_job_completion(self.job_obj)
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id,
                                                                     self.destination_ma_obj._media_agent_id, self.csdb)
            self.verify_mediaagents_are_on([self.destination_ma_obj,])

            self.log.info("Starting a BACKUP for aux copy (ALL COPY + DASH) job")
            self.job_obj = self.subclient.backup("FULL")
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.ma_helper.wait_for_job_completion(self.job_obj)

            self.log.info("Powering off the MA for aux copy (ALL COPY+DASH) job")
            self.power_off_all_cloud_mediaagents()
            self.log.info("Powered off the cloud MAs for aux copy (ALL COPY:DASH) job. Starting the aux job.")
            self.job_obj = self.sp_obj.run_aux_copy(use_scale=True, all_copies=True)
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.ma_helper.wait_for_job_completion(self.job_obj)
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id,
                                                                     self.destination_ma_obj._media_agent_id, self.csdb)
            self.verify_mediaagents_are_on([self.destination_ma_obj,])

            self.log.info(f"Powering off MA for DV2")
            self.power_off_all_cloud_mediaagents()

            self.log.info("Starting DV2")
            self.ddb_engine_o.refresh()
            self.store_o.refresh()
            self.job_obj = self.store_o.run_ddb_verification(incremental_verification=False, quick_verification=False)
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.ma_helper.wait_for_job_completion(self.job_obj)
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id,
                                                                     self.destination_ma_obj._media_agent_id, self.csdb)
            self.verify_mediaagents_are_on([self.destination_ma_obj,])

            self.log.info("Test case completed successfully.")

        except Exception as excp:
            self.is_case_failed = True
            self.log.error(f"Failed with error: {excp}")
            self.result_string = str(excp)
            self.status = constants.FAILED