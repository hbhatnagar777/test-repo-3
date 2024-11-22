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

    configure_cloud_mediaagent() -- Setup and configure cloud MediaAgent

    create_disk_library()   --  Creates disk library after powering-on the MA

    cleanup()  --  Cleanup SC, BS,SP, Library

    tear_down() --  Tear Down Function of this Case

    Input Example:

    "testCases": {
				"63057": {
					"ClientName": "client1",
					"AgentName": "File System",
					"CloudMA1": "CloudMA1",
					"CloudMA2": "CloudMA2",
					"CloudMA3": "CloudMA3",
					"CloudMA4": "CloudMA4",
					"PsudoClientName": "Azure",
					"VSAProxyForPsudoClient":"proxy1",
					"AzureSubsID":"1234",
					"AzureTenantID":"1234",
					"AzureAppID":"1234",
					"AzureAppPassword":"1234"
				}
                }

"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper, PowerManagement


class TestCase(CVTestCase):
    """Submit power-off request when job is running"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Submit power-off request when job is running"

        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "CloudMA1": None,
            "CloudMA2": None,
            "CloudMA3": None,
            "CloudMA4": None,
            "PsudoClientName": None,
            "VSAProxyForPsudoClient": None,
            "AzureSubsID": None,
            "AzureTenantID": None,
            "AzureAppID": None,
            "AzureAppPassword": None
        }

        self.status = None
        self.is_ddb_directory_created = None
        self.is_client_directory_created = None
        self.is_secondary_ma_directory_created = None
        self.is_primary_ma_directory_created = None
        self.is_ddb_secondary_directory_created = None

        self.ma_helper =  None
        self.power_management = None
        self.dedupehelper = None
        self.status = None

        self.primary_ma = None
        self.secondary_ma = None
        self.ddb_ma = None
        self.client = None
        self.ddb_ma_secondary = None

        self.storage_policy_name = None
        self.backup_set_name = None
        self.sub_client_name = None
        self.primary_library = None
        self.secondary_library = None
        self.aux_copy_name = None

        self.azure_client_name = None
        self.vsa_proxy = None
        self.azure_subscription_id = None
        self.azure_tenant_id = None
        self.azure_app_id = None
        self.azure_app_password = None

        self.primary_ma_obj = None
        self.secondary_ma_obj = None
        self.ddb_ma_obj = None
        self.client_ma_obj = None
        self.ddb_ma_secondary_obj = None

        self.primary_ma_machine = None
        self.secondary_ma_machine = None
        self.client_machine = None
        self.ddb_ma_machine = None
        self.ddb_ma_secondary_machine = None

        self.primary_ma_path = None
        self.secondary_ma_path = None
        self.ddb_ma_path = None
        self.ddb_ma_secondary_path = None
        self.client_path = None

        self.primary_library_path = None
        self.secondary_library_path = None
        self.ddb_path = None
        self.ddb_secondary_path = None
        self.content_path = None

        self.storage_policy_obj = None
        self.backup_set_obj = None
        self.subclient_obj = None
        self.job_obj = None


    def setup(self):
        """Setup function of this test case"""

        self.ma_helper =  MMHelper(self)
        self.power_management = PowerManagement()
        self.dedupehelper = DedupeHelper(self)
        self.status = constants.PASSED

        self.is_ddb_directory_created = False
        self.is_client_directory_created = False
        self.is_secondary_ma_directory_created = False
        self.is_primary_ma_directory_created = False
        self.is_ddb_secondary_directory_created = False

        self.primary_ma = self.tcinputs['CloudMA1']
        self.secondary_ma = self.tcinputs['CloudMA2']
        self.ddb_ma = self.tcinputs['CloudMA3']
        self.client = self.tcinputs['ClientName']
        self.ddb_ma_secondary = self.tcinputs['CloudMA4']

        self.storage_policy_name = "Storage_Policy_"+self.id
        self.backup_set_name = "Backup_Set_"+self.id
        self.sub_client_name = "SC_"+self.id
        self.primary_library = "Library_Primary_"+self.id
        self.secondary_library = "Library_Secondary_"+self.id
        self.aux_copy_name = "Copy-2"

        self.azure_client_name = self.tcinputs['PsudoClientName']
        self.vsa_proxy = self.tcinputs['VSAProxyForPsudoClient']
        self.azure_subscription_id = self.tcinputs['AzureSubsID']
        self.azure_tenant_id = self.tcinputs['AzureTenantID']
        self.azure_app_id = self.tcinputs['AzureAppID']
        self.azure_app_password = self.tcinputs['AzureAppPassword']

        self.log.info("Primary MA, secondary MA, DDB MA, client have to be unique machines, verifying that")
        if len(set([self.primary_ma, self.secondary_ma, self.ddb_ma, self.client])) != 4:
            raise ("Primary MA, secondary MA, DDB MA, Client have to be unique machines")

        self.log.info("Creating MediAgent objects")
        self.primary_ma_obj = self.commcell.media_agents.get(self.primary_ma)
        self.secondary_ma_obj = self.commcell.media_agents.get(self.secondary_ma)
        self.ddb_ma_obj = self.commcell.media_agents.get(self.ddb_ma)
        self.client_ma_obj = self.commcell.media_agents.get(self.client)
        self.ddb_ma_secondary_obj = self.commcell.media_agents.get(self.ddb_ma_secondary)
        self.log.info("Successfully created all the objects")

        self.log.info("Checking if Azure Psudo Client exists")
        if self.commcell.clients.has_client(self.azure_client_name):
            self.log.info("Azure Psudo Client exists")
        else:
            self.log.info("Azure Psudo Client does not exists, creating a new one")
            self.create_pseudo_client()

        self.log.info("Verifing and Configuring Cloud MediaAgents")
        self.power_management.configure_cloud_mediaagent(self.azure_client_name, self.primary_ma_obj)
        self.power_management.configure_cloud_mediaagent(self.azure_client_name, self.secondary_ma_obj)
        self.power_management.configure_cloud_mediaagent(self.azure_client_name, self.ddb_ma_obj)
        self.power_management.configure_cloud_mediaagent(self.azure_client_name, self.ddb_ma_secondary_obj)

        self.log.info("Powering-on all the Cloud Media Agents for setup")
        self.power_management.power_on_media_agents([self.primary_ma_obj, self.secondary_ma_obj, self.ddb_ma_obj, self.ddb_ma_secondary_obj])

        self.log.info("Creating Machine class objects and generating paths")
        (self.primary_ma_machine, self.primary_ma_path) = self.ma_helper.generate_automation_path(self.primary_ma, 12000)
        (self.secondary_ma_machine, self.secondary_ma_path) = self.ma_helper.generate_automation_path(self.secondary_ma, 12000)
        (self.ddb_ma_machine, self.ddb_ma_path) = self.ma_helper.generate_automation_path(self.ddb_ma, 12000)
        (self.ddb_ma_secondary_machine, self.ddb_ma_secondary_path) = self.ma_helper.generate_automation_path(self.ddb_ma_secondary, 12000)
        (self.client_machine, self.client_path) = self.ma_helper.generate_automation_path(self.client, 12000)
        self.log.info("Completed Machines class object creation and path generation")

        self.primary_library_path = self.primary_ma_path+"lib"
        self.log.info(f"Primary library path : {self.primary_library_path}")
        self.secondary_library_path = self.secondary_ma_path+"lib"
        self.log.info(f"Secondary librray path: {self.secondary_library_path}")
        self.ddb_path = self.ddb_ma_path+"ddb"
        self.log.info(f"DDB path: {self.ddb_path}")
        self.ddb_secondary_path = self.ddb_ma_secondary_path + "ddb"
        self.log.info(f"Secondary DDB path : {self.ddb_secondary_path}")
        self.content_path = self.client_path+"content"
        self.log.info(f"Sub-client content path : {self.content_path}")

    def create_pseudo_client(self):
        """
                Creates Pseudo client (cloud controller)
        """

        self.log.info(f"Creating Azure pseudo client(cloud controller) [{self.azure_client_name}]")

        self.commcell.clients.add_azure_client(self.azure_client_name,
                                               self.vsa_proxy, azure_options={
                "subscription_id": self.azure_subscription_id,
                "tenant_id": self.azure_tenant_id,
                "application_id": self.azure_app_id,
                "password": self.azure_app_password,
            })
        self.log.info("Created successfully")

    def verify_for_backup_job(self, timeout=60 * 60):
        """
                Power-off verification for backup job

                :argument
                    Time out -- (int) -- Time-out for the job

                :exception
                    If the verification not completed in 60 mins
                    If verification failed

        """
        start_time = time.time()
        self.log.info(f"Starting verification for backup job[{self.job_obj.job_id}]")
        self.job_obj.refresh()

        while self.job_obj.state.lower() != "completed":

            self.log.info(f"Job state[{self.job_obj.state}] and phase[{self.job_obj.phase}]")
            if (self.job_obj.state.lower() == "running") and ( self.job_obj.phase.lower() == "backup"):
                self.log.info(f"Job state[{self.job_obj.state}] and phase[{self.job_obj.phase}]. Trying to power-off primary MediaAgent[{self.primary_ma}]")

                try:
                    self.primary_ma_obj.power_off(False)
                    return False # if powered-off successfully then only this line will execute

                except Exception as excp:
                    self.log.info(str(excp))
                    self.log.info("Power-off failed. It's expected")

                self.log.info(f"Job state[{self.job_obj.state}] and phase[{self.job_obj.phase}]. Trying to power-off of DDB MediaAgent[{self.ddb_ma}]")
                try:
                    self.ddb_ma_obj.power_off(False)
                    return False  # if powered-off successfully then only this line will execute

                except Exception as excp:
                    self.log.info(str(excp))
                    self.log.info("Power-off failed. It's expected")
                    return True

            if time.time() > (start_time+timeout):
                raise Exception('Job is NOT completed within expected time')

            time.sleep(10)
            self.job_obj.refresh()

        raise Exception('verify_for_backup_job::Power-off successful which is not expected, verification failed')

    def verify_for_aux_job(self, timeout=60 * 60):
        """
                Power-off verification for aux copy job

                :argument
                    Time out -- (int) -- Time-out for the job

                :exception
                    If the verification not completed in 60 mins
                    If verification failed

        """
        start_time = time.time()
        self.log.info(f"Starting verification for aux job[{self.job_obj.job_id}]")
        self.job_obj.refresh()

        while self.job_obj.state.lower() != "completed":

            self.log.info(f"Job state[{self.job_obj.state}]")
            if self.job_obj.state.lower() == "running":
                self.log.info(f"Job state[{self.job_obj.state}]. Trying to power-off primary MediaAgent[{self.primary_ma}]")
                try:
                    self.primary_ma_obj.power_off()
                    return False # if powered-off successfully then only this line will execute

                except Exception as excp:
                    self.log.info(str(excp))
                    self.log.info("Power-off failed. It's expected")

                self.log.info(f"Job state[{self.job_obj.state}]. Trying to power-off secondary MediaAgent[{self.secondary_ma}]")
                try:
                    self.secondary_ma_obj.power_off()
                    return False # if powered-off successfully then only this line will execute

                except Exception as excp:
                    self.log.info(str(excp))
                    self.log.info("Power-off failed. It's expected")

                self.log.info(f"Job state[{self.job_obj.state}]. Trying to power-off secondary DDB MediaAgent[{self.ddb_ma_secondary}]")
                try:
                    self.ddb_ma_secondary_obj.power_off()
                    return False # if powered-off successfully then only this line will execute

                except Exception as excp:
                    self.log.info(str(excp))
                    self.log.info("Power-off failed. It's expected")

                self.log.info(f"Job state[{self.job_obj.state}]. Trying to power-off of DDB MediaAgent[{self.ddb_ma}]")
                self.log.info(f"Power-off of MediaAgent[{self.ddb_ma}] should be successful as it's DDB MediaAgent of source copy( Primary copy)")
                self.ddb_ma_obj.power_off(False)

                return True

            if time.time() > (start_time+timeout):
                raise Exception('Job is NOT completed within expected time')

            time.sleep(10)
            self.job_obj.refresh()

        raise Exception('verify_for_aux_job::Power-off successful which is not expected, verification failed')


    def create_disk_library(self, library_name, mount_path, ma_obj):
        """
                Creates disk library after powering-on the MA

                Args:
                    library_name -- (str) -- Library to create
                    mount_path -- (str) -- Mount path directory
                    ma_obj -- (MediaAgent class object) -- MediaAgent class Object of the MA where library will be created
        """
        self.log.info(f"Received library[{library_name}] creation request on MA[{ma_obj.media_agent_name}]")
        self.log.info("Will try to power-on if power management is enabled and MA is NOT online to create library")
        if ma_obj.current_power_status != "Online" and ma_obj._is_power_management_enabled:
            self.log.info(f"Powering-on the MA to create the library[{library_name}]")
            ma_obj.power_on()
        self.log.info(f"Creating library[{library_name}] now")
        self.commcell.disk_libraries.add(library_name, ma_obj.media_agent_name, mount_path)
        self.log.info("Library[library_name] created successfully")


    def cleanup(self):
        """Cleanup SC, BS,SP, Library """

        self.log.info("Starting cleanup")

        if self._agent.backupsets.has_backupset(self.backup_set_name):
            self.log.info(f"BackupSet [{self.backup_set_name}] exists, deleting that")
            self._agent.backupsets.delete(self.backup_set_name)

        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.log.info(f"Storage Policy[{self.storage_policy_name}] exists, deleting that")
            self.log.info("Reassociating all sub clients before deleting the SP")
            self.sp_obj_to_reassociate = self.commcell.storage_policies.get(self.storage_policy_name)
            self.sp_obj_to_reassociate.reassociate_all_subclients()
            self.log.info("Deleting SP")
            self.commcell.storage_policies.delete(self.storage_policy_name)

        if self.commcell.disk_libraries.has_library(self.primary_library):
            self.log.info(f"Library[{self.primary_library}] exists, deleting that")
            self.commcell.disk_libraries.delete(self.primary_library)

        if self.commcell.disk_libraries.has_library(self.secondary_library):
            self.log.info(f"Library[{self.secondary_library}] exists, deleting that")
            self.commcell.disk_libraries.delete(self.secondary_library)

        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")

        self.log.info("Powering-on MediaAgents for cleanup")
        self.power_management.power_on_media_agents([self.primary_ma_obj, self.secondary_ma_obj, self.ddb_ma_obj, self.ddb_ma_secondary_obj])

        if self.status == constants.PASSED:
            self.log.info("Test case completed, deleting BS, SP, Library")
            self.cleanup()
        else:
            self.log.info("Test case failed, NOT deleting SC, BS, SP, Library")

        self.log.info(f"Disabling ransomware on {self.primary_ma}")
        self.primary_ma_obj.set_ransomware_protection(False)

        self.log.info(f"Disabling ransomware on {self.secondary_ma}")
        self.secondary_ma_obj.set_ransomware_protection(False)

        self.log.info(f"Disabling ransomware on {self.ddb_ma}")
        self.ddb_ma_obj.set_ransomware_protection(False)

        self.log.info(f"Disabling ransomware on {self.client}")
        self.client_ma_obj.set_ransomware_protection(False)

        self.log.info(f"Disabling ransomware on {self.ddb_ma_secondary}")
        self.ddb_ma_secondary_obj.set_ransomware_protection(False)

        if self.is_client_directory_created:
            self.log.info("Deleting client directory")
            self.ma_helper.remove_content(self.client_path, self.client_machine)

        if self.is_primary_ma_directory_created:
            self.log.info("Deleting primary MA path")
            self.ma_helper.remove_content(self.primary_ma_path, self.primary_ma_machine)

        if self.is_secondary_ma_directory_created:
            self.log.info("Deleting secondary MA path")
            self.ma_helper.remove_content(self.secondary_ma_path, self.secondary_ma_machine)

        if self.is_ddb_directory_created:
            self.log.info("Deleting Primary DDB path")
            self.ma_helper.remove_content(self.ddb_ma_path, self.ddb_ma_machine)

        if self.is_ddb_secondary_directory_created:
            self.log.info("Deleting Secondary DDB path")
            self.ma_helper.remove_content(self.ddb_secondary_path, self.ddb_ma_secondary_machine)

    def run(self):
        try:
            self.cleanup()
            self.log.info("Creating libraries")
            self.create_disk_library(self.primary_library, self.primary_library_path, self.primary_ma_obj)
            self.is_primary_ma_directory_created = True
            self.create_disk_library(self.secondary_library, self.secondary_library_path, self.secondary_ma_obj)
            self.log.info("Libraries created successfully")
            self.is_secondary_ma_directory_created = True

            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(self.client, self.content_path, 0.3)
            self.is_client_directory_created = True

            self.log.info(f"Creating Storage Policy[{self.storage_policy_name}]")
            self.storage_policy_obj = self.commcell.storage_policies.add(self.storage_policy_name,self.primary_library, self.primary_ma,self.ddb_path,dedup_media_agent=self.ddb_ma)
            self.is_ddb_directory_created = True

            self.log.info(f"Creating BackupSet[{self.backup_set_name}]")
            self.backup_set_obj = self._agent.backupsets.add(self.backup_set_name)

            self.log.info(f"Creating Sub-Client[{self.sub_client_name}]")
            self.subclient_obj = self.ma_helper.configure_subclient(self.backup_set_name, self.sub_client_name, self.storage_policy_name,
                                                                self.content_path)

            self.log.info("Powering-on all the Cloud Media Agents")
            self.power_management.power_on_media_agents([self.primary_ma_obj, self.secondary_ma_obj])

            self.log.info("Starting full backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Job started. Job id : {self.job_obj.job_id}")
            if not self.verify_for_backup_job():
                self.log.error("Power-off operation should not be successful")
                self.job_obj.kill()
                raise Exception("Power-off operation should not be successful")
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id,self.primary_ma_obj.media_agent_id, self.csdb)
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id,self.ddb_ma_obj.media_agent_id, self.csdb)
            self.log.info("Verification completed")
            self.log.info(f"Waiting for the job[{self.job_obj.job_id}] to complete")
            self.job_obj.wait_for_completion(60)
            self.log.info(f"Job[{self.job_obj.job_id}] completed")

            self.log.info("Creating secondary copy")
            self.dedupehelper.configure_dedupe_secondary_copy(self.storage_policy_obj, self.aux_copy_name, self.secondary_library, self.secondary_ma, self.ddb_secondary_path,self.ddb_ma_secondary)
            self.is_ddb_secondary_directory_created = True

            self.log.info("Powering-on all the Cloud Media Agents")
            self.power_management.power_on_media_agents([self.primary_ma_obj, self.secondary_ma_obj, self.ddb_ma_obj, self.ddb_ma_secondary_obj])
            self.job_obj = self.storage_policy_obj.run_aux_copy()
            self.log.info(f"Started aux copy job. Job ID : {self.job_obj.job_id}")
            if not self.verify_for_aux_job():
                self.log.error("Power-off operation should not be successful")
                self.job_obj.kill()
                raise Exception("Power-off operation should not be successful")
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id,self.primary_ma_obj.media_agent_id, self.csdb)
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id,self.secondary_ma_obj.media_agent_id, self.csdb)
            self.power_management.validate_powermgmtjobtovmmap_table(self.job_obj.job_id,self.ddb_ma_secondary_obj.media_agent_id, self.csdb)

            self.log.info("Verification completed")

            self.log.info(f"Waiting for the job[{self.job_obj.job_id}] to complete")
            self.job_obj.wait_for_completion()

            self.log.info("Test case completed successfully.")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

