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

    create_pseudo_client()  --  Creates Pseudo client (cloud controller)

    wait_for_job_complete()  --  Waits for the job to complete

    create_disk_library()   --  Creates disk library after powering-on the MA

    create_multi_partition_dedupe_copy()  --  Creates aux copy with 2 DDB partitions

    verify_non_cloud_media_agents()  --  Verify that PowerManagemet is disabled

    cleanup()  --  Cleanup SC, BS,SP, Library

    tear_down() --  Tear Down Function of this Case



    Input Example:

    "testCases": {


				"57832": {
					"ClientName": "client",
					"AgentName": "File System",
					"CloudMA1": "CloudMA1",
					"MA1":"MA1",
					"MA2":"MA2",
					"MA3":"MA3",
					"PsudoClientName": "AzurecLIENT",
					"VSAProxyForPsudoClient":"proxy1",
					"AzureSubsID":"****************",
					"AzureTenantID":"****************",
					"AzureAppID":"****************",
					"AzureAppPassword":"****************"
				}

                }
"""
import time
import threading
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper, PowerManagement


class TestCase(CVTestCase):
    """Power management test case. Configuration : Power Management Aux Copy Case. (Source :non-Cloud, Destination : non-Cloud, DDB1 : non-Cloud, " \
                    "DDB2 : Cloud. Single Copy (non-DASH, DASH). All Copy (non-DASH, dash)"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Power Management Aux Copy Case. (Source :non-Cloud, Destination : non-Cloud, DDB1 : non-Cloud, " \
                    "DDB2 : Cloud. Single Copy (non-DASH, DASH). All Copy (non-DASH, dash)"

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
        self.library1 = None
        self.library2 = None
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
        self.copy_name1 = None
        self.copy_name2 = None
        self.thread1 = None
        self.thread2 = None
        self.is_case_failed = None
        self.is_source_ma_directory_created = None
        self.is_destination_ma_directory_created = None
        self.is_ddb_ma1_directory_created = None
        self.is_ddb_ma2_directory_created = None
        self.is_client_directory_created = None
        self.power_management = None
        self.ma_helper = None
        self.ddb_ma1_machine = None
        self.ddb_ma2_machine = None
        self.ddb2_path = None
        self.backup_set_obj = None
        self.job_obj = None
        self.path_suffix = None

        self.tcinputs = {
            "ClientName": None,
            "AgentName":  None,
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
        self.storage_policy = "PowerManagement_57832_SP"
        self.sub_client = "PowerManagement_57832_SC"
        self.backup_set = "PowerManagement_57832_BS"
        self.library1 = "PowerManagement_57832_Library1"
        self.library2 = "PowerManagement_57832_Library2"
        self.source_ma = self.tcinputs['MA1']
        self.destination_ma = self.tcinputs['MA2']
        self.ddb_ma1 = self.tcinputs['CloudMA1']
        self.ddb_ma2 = self.tcinputs['MA3']
        self.client = self.tcinputs['ClientName']
        self.copy_name1 = "auxCopy1"
        self.copy_name2 = "auxCopy2"

        self.log.info("Creating all MA objects")
        self.ddb_ma1_obj = self.commcell.media_agents.get(self.ddb_ma1)
        self.source_ma_obj = self.commcell.media_agents.get(self.source_ma)
        self.destination_ma_obj = self.commcell.media_agents.get(self.destination_ma)
        self.ddb_ma2_obj = self.commcell.media_agents.get(self.ddb_ma2)
        self.log.info("Done. Created all MA objects")

        self.ma_helper = MMHelper(self)
        self.power_management = PowerManagement()

        # all MAs and client have to be unique
        list_of_ma = [self.source_ma, self.destination_ma, self.ddb_ma1, self.ddb_ma2, self.tcinputs['ClientName']]
        if len(set(list_of_ma)) != 5:
            raise Exception('Each MediaAgent and client have to be unique machine. '
                            'Make sure you have provided 4 unique MediaAgents and one client.')

        # Checking if the PsudoClientName exists, else creating that
        if self._commcell._clients.has_client(self.tcinputs['PsudoClientName']):
            self.log.info("Psudo exists. Not creating a new one")
        else:
            self.log.info("Pseudo client(cloud controller) is not present with name [%s]",
                          self.tcinputs['PsudoClientName'])
            self.create_pseudo_client()

        # Verifying the non-power managed MAs
        self.verify_non_cloud_media_agents()

        # Verify and Configure cloud MA
        self.power_management.configure_cloud_mediaagent(self.tcinputs['PsudoClientName'], self.ddb_ma1_obj)

        self.log.info("Powering-on the MA[%s] for setup", self.ddb_ma1)
        self.ddb_ma1_obj.power_on()

        self.log.info("Getting paths for all machines")
        (
            self.ddb_ma1_machine,
            self.ddb_ma1_drive,
        ) = self.ma_helper.generate_automation_path(self.ddb_ma1, 10000)
        (
            self.ddb_ma2_machine,
            self.ddb_ma2_drive,
        ) = self.ma_helper.generate_automation_path(self.ddb_ma2, 10000)
        (
            self.source_ma_machine,
            self.source_ma_drive,
        ) = self.ma_helper.generate_automation_path(self.source_ma, 10000)
        (
            self.destination_ma_machine,
            self.destination_ma_drive,
        ) = self.ma_helper.generate_automation_path(self.destination_ma, 10000)
        (
            self.client_machine,
            self.client_drive,
        ) = self.ma_helper.generate_automation_path(self.client, 10000)

        self.log.info("Generating parent paths for all MAs and client")

        self.log.info("Generating paths")

        self.source_library_path = self.source_ma_drive + "MP"
        self.log.info("Source library path : %s", self.source_library_path)

        self.destination_library_path = self.destination_ma_drive + "MP"
        self.log.info("Destination library path : %s", self.destination_library_path)

        self.ddb1_path = self.ddb_ma1_drive + "DDB"
        self.log.info("DDB path %s on MA[%s]", self.ddb1_path, self.ddb_ma1)

        self.ddb2_path = self.ddb_ma2_drive + "DDB"
        self.log.info("DDB path %s on MA[%s]", self.ddb2_path, self.ddb_ma2)

        self.client_content = self.client_drive + "subclient_content"
        self.log.info("Client content %s", self.client_content)


    def create_pseudo_client(self):
        """
                Creates Pseudo client (cloud controller)
        """

        self.log.info("Creating Azure pseudo client(cloud controller) [%s]", self.tcinputs['PsudoClientName'])

        self.commcell.clients.add_azure_client(self.tcinputs['PsudoClientName'], self.tcinputs['VSAProxyForPsudoClient'], azure_options={
                        "subscription_id": self.tcinputs['AzureSubsID'],
                        "tenant_id": self.tcinputs['AzureTenantID'],
                        "application_id": self.tcinputs['AzureAppID'],
                        "password":self.tcinputs['AzureAppPassword'],
        })
        self.log.info("Created successfully")

    def create_disk_library(self, library_name, mount_path, ma_obj):
        """
                Creates disk library after powering-on the MA

                Args:
                    library_name -- (str) -- Library to create
                    mount_path -- (str) -- Mount path directory
                    ma_obj -- (MediaAgent class object) -- MediaAgent class Object of the MA where library will be created
        """
        self.log.info("Received library[%s] creation request on MA[%s]", library_name, ma_obj._media_agent_name)

        self.log.info("Will try to power-on if power management is enabled and MA is NOT online to create library[%s]", library_name)
        if ma_obj.current_power_status != "Online" and  ma_obj._is_power_management_enabled:
            self.log.info("Powering-on the MA to create the library[%s]", library_name)
            ma_obj.power_on()
        self.log.info("Creating library[%s] now", library_name)
        self.commcell.disk_libraries.add(library_name, ma_obj._media_agent_name, mount_path)
        self.log.info("Library[%s] created successfully", library_name)

    def create_multi_partition_dedupe_copy(self, aux_copy_name):
        """
            Creates aux copy with 2 DDB partitions

            Args:
                aux_copy_name -- (str) -- Copy name
        """
        self.log.info("Creating secondary copy[%s]", aux_copy_name)

        self.log.info("Powering-on DDB MA[%s] to create copy[%s]", self.ddb_ma1_obj._media_agent_name, aux_copy_name)
        self.ddb_ma1_obj.power_on()

        dedupehelper = DedupeHelper(self)
        self.log.info("Creating aux copy. Copy Name : %s", aux_copy_name)
        dedupehelper.configure_dedupe_secondary_copy(self.sp_obj, aux_copy_name, self.library2,
                                                     self.destination_ma, self.ddb1_path+aux_copy_name, self.ddb_ma1)
        self.is_ddb_ma1_directory_created = True
        self.log.info("Created the copy[%s] with 1 partition. "
                      "Adding 1 more partition to the SIDB store on MA[%s]", aux_copy_name, self.ddb_ma2)

        sidb_store_ids = dedupehelper.get_sidb_ids(self.sp_obj.storage_policy_id, aux_copy_name)
        sp_copy_obj = self.sp_obj.get_copy(str(aux_copy_name))
        self.log.info("SIDB Store ID %s", str(sidb_store_ids))
        self.sp_obj.add_ddb_partition(str(sp_copy_obj.get_copy_id()), str(sidb_store_ids[0]),
                                      self.ddb2_path+aux_copy_name, self.ddb_ma2)
        self.is_ddb_ma2_directory_created = True
        self.log.info("Copy[%s] created successfully", aux_copy_name)

    def verify_non_cloud_media_agents(self):
        """
            Verify that PowerManagemet is disabled
        """

        if self.source_ma_obj._is_power_management_enabled or self.destination_ma_obj._is_power_management_enabled or self.ddb_ma2_obj._is_power_management_enabled:
            raise Exception('Expected non-power managed MediaAgents but found at least one powered managed MediaAgent')

    def cleanup(self):
        """Cleanup SC, BS,SP, Library """


        self.log.info("Deleting BackupSet if exists")
        if self._agent.backupsets.has_backupset(self.backup_set):
            self.log.info("BackupSet[%s] exists, deleting that", self.backup_set)
            self._agent.backupsets.delete(self.backup_set)

        self.log.info("Deleting Storage Policy if exists")
        if self.commcell.storage_policies.has_policy(self.storage_policy):
            self.log.info("Storage Policy[%s] exists", self.storage_policy)
            self.log.info("Reassociating all sub clients before deleting the SP")
            self.sp_obj_to_reassociat =  self.commcell.storage_policies.get(self.storage_policy)
            self.sp_obj_to_reassociat.reassociate_all_subclients()
            self.log.info(f"Deleting the SP {self.storage_policy}")
            self.commcell.storage_policies.delete(self.storage_policy)

        self.log.info("Deleting library[%s] if exists", self.library1)
        if self.commcell.disk_libraries.has_library(self.library1):
            self.log.info("Library[%s] exists, deleting that", self.library1)
            self.commcell.disk_libraries.delete(self.library1)

        self.log.info("Deleting library[%s] if exists", self.library2)
        if self.commcell.disk_libraries.has_library(self.library2):
            self.log.info("Library[%s] exists, deleting that", self.library2)
            self.commcell.disk_libraries.delete(self.library2)

        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")

        self.log.info("Powering-on for clean up [%s]", self.ddb_ma1)
        self.ddb_ma1_obj.power_on()
        
        self.log.info("Disabling Ransomware [%s]", self.source_ma)
        self.source_ma_obj.set_ransomware_protection(False)
        
        self.log.info("Disabling Ransomware [%s]", self.destination_ma)
        self.destination_ma_obj.set_ransomware_protection(False)
        
        self.log.info("Disabling Ransomware [%s]", self.ddb_ma1)
        self.ddb_ma1_obj.set_ransomware_protection(False)
        
        self.log.info("Disabling Ransomware [%s]", self.ddb_ma2)
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
            self.log.error('Cleanup failed with error: %s', str(excp))
            self.result_string = str(f"Cleanup failed. {excp}")

    def run(self):
        try:

            self.log.info("Cleaning-up SC,BS,SP, Libraries if exists")
            self.cleanup()

            # Creating the libraries if not exists
            self.create_disk_library(self.library1, self.source_library_path, self.source_ma_obj)
            self.is_source_ma_directory_created = True
            
            self.create_disk_library(self.library2, self.destination_library_path, self.destination_ma_obj)
            self.is_destination_ma_directory_created = True
            
            #Creating SP
            self.log.info(f"Creating storage policy [{self.storage_policy}]")
            self.sp_obj = self.commcell.storage_policies.add(self.storage_policy, self.library1, self.source_ma_obj._media_agent_name)

            # Creating secondary copy
            self.create_multi_partition_dedupe_copy(self.copy_name1)
            self.log.info(f"Removing copy [{self.copy_name1}] from auto copy schedule")
            self.ma_helper.remove_autocopy_schedule(self.storage_policy, self.copy_name1)

            self.create_multi_partition_dedupe_copy(self.copy_name2)
            self.log.info(f"Removing copy [{self.copy_name2}] from auto copy schedule")
            self.ma_helper.remove_autocopy_schedule(self.storage_policy, self.copy_name2)

            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(self.client, self.client_content, 0.3)
            self.is_client_directory_created = True

            # creating backup set
            self.log.info("Creating backup set")
            self.backup_set_obj = self._agent.backupsets.add(self.backup_set)

            # Creating sub client
            self.log.info("Creating subclient[%s]", self.sub_client)
            self.subclient = self.ma_helper.configure_subclient(self.backup_set, self.sub_client, self.storage_policy,
                                                                self.client_content)

            # Starting backup
            self.log.info("Starting backup")
            self.job_obj = self.subclient.backup("FULL")
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.job_obj.wait_for_completion()

            # Powering off the Cloud MA for aux copy (DASH job) job to a single copy
            self.log.info("Powering off the cloud MAs for next aux job [One Copy + DASH]")
            self.log.info("Powering off MA %s", self.ddb_ma1_obj.media_agent_name)
            self.ddb_ma1_obj.power_off()
            self.log.info("Successfully powered-off. Starting aux copy [One Copy + DASH] job")
            self.job_obj = self.sp_obj.run_aux_copy(self.copy_name1, use_scale=True, all_copies=False)
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.job_obj.wait_for_completion()
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id, self.ddb_ma1_obj._media_agent_id, self.csdb)

            self.log.info("Starting a BACKUP for aux copy (ALL COPY + DASH) job")
            self.job_obj = self.subclient.backup("FULL")
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.job_obj.wait_for_completion()

            self.log.info("Powering off the MA for aux copy (ALL COPY+DASH) job")
            self.log.info("Powering off MA %s", self.ddb_ma1_obj.media_agent_name)
            self.ddb_ma1_obj.power_off()
            self.log.info("Powered off the cloud MAs for aux copy (ALL COPY:DASH) job. Starting the aux job.")
            self.job_obj = self.sp_obj.run_aux_copy(use_scale=True, all_copies=True)
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.job_obj.wait_for_completion()
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id, self.ddb_ma1_obj._media_agent_id, self.csdb)

            self.log.info("Powering off MA[%s] for DV2", self.ddb_ma1)
            self.ddb_ma1_obj.power_off()
            self.log.info("Starting DV2")
            self.job_obj = self.sp_obj.run_ddb_verification(self.copy_name1, "Full", "DDB_AND_DATA_VERIFICATION")
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id} ")
            self.job_obj.wait_for_completion()
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id,
                                                                     self.ddb_ma1_obj._media_agent_id, self.csdb)

            self.log.info("Test case completed successfully.")

        except Exception as excp:
            self.is_case_failed = True
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED