# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case
TestCase for performing Basic Backward Compatilibility Test. 
TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    run_util()      --  performs create backupset, SP, library and backup operations

    fresh_install() -- installs a new instance of media agent client.

    create_ddb_resources
                    -- creates dummy libraries and storage policy for DDBSubclients on MA1 and MA2. 

Design Steps:
    1. Install and register one Windows and one Linux MediaAgent with service pack lower than CS but from the same release.
		1. if CS is at V11 SP#N then MAs will be at V11SP#(N-2) and V11SP#(N-4) with client on V11SP#(N-6)
	2. Configure
		1. Disk library DL1 and Cloud library CL1 on MA1
		3. Disk library DL2 and Cloud library CL2 on MA2
	3. Configure storage policy 1 with -
		1. Dedupe Primary copy pointing to DL1 on MA1 and DDB on MA2.
		2. Dedupe Copy 2 pointing to CL2 on MA2 and DDB is configured on MA1.
	4. Configure storage policy 2 with -
		1. Non-Dedupe Primary copy pointing to DL2 on MA2
		2. Non-Dedupe Copy 2 pointing to CL1 on MA1
    5. Configure and Run Backups -
		1. Configure a new backup-set and Sub-client on C1 and associate with SP1
		2. Set retention on copies as 0 days and 1 cycle
		3. Remove association from auto auxcopy schedule.
		4. Run backups (Full, Incremental, Incremental, Synthetic Full (SF), Incremental, SF2)
		5. Restore from primary copy
		6. Run aux copy job
		7. Restore from Copy 2
		8. Run granular DA
    6. Repeat step 5 for SP2    
    7. Negative Case
        1. Consume the FS client license on MA1
        2. Create a new backup-set and sub-client on MA1 client and associate with SP2
        3. Run backup on subclient
        4. Backup should error out.

Sample Input - 
    "29845": {
                "Machine":{
                    "ClientMachine": {
                        "Hostname": "hostname",
                        "Username": "usename",
                        "Password": "password"
                    },
                    "MA1Machine": {
                        "Hostname": "hostname",
                        "Username": "username",
                        "Password": "password"
                    },
                    "MA2Machine": {
                        "Hostname": "hostname",
                        "Username": "username",
                        "Password": "password"
                    }
                },
                "AgentName": "File System",
                "ClientName": "ClientName",
                "CloudMountPath":"CloudMountPath",
                "CloudUserName": "CloudUserName",
                "CloudPassword": "CloudPassword",
                "CloudServerType":"MicrosoftAzure"
            }
    Additional parameters for Unix Machine
    mediaPath: "\\\\SoftwareMedia-Filer-Location\\Provide-SP_DVD\\Location", for installation
    partition_path : for DDB
    Ex - for SP28 installation
    "MA1Machine": {
                    "Hostname": "hostname",
                    "Username": "root",
                    "Password": "password",
                    "partition_path": "VolPath",
                    "mediaPath": "\\\\SoftwareMedia-Filer-Location\\Provide-SP_DVD\\Location"
                }
"""

from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import (constants, commonutils)
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from cvpysdk.policies.storage_policies import StoragePolicy


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MediaAgent Backward Compatibility"
        self.install_helper = None
        self.ma_machine_obj = None
        self.config_json = None
        self.ma_machine_name = None
        self.MA1_client = None
        self.MAAgent = None
        self.remote_client = None
        self.ClientAgent = None
        self.common_util = None
        self.MMHelper = None
        self.DedupeHelper = None
        self.ddb_path = None
        self.content_path = None
        self.restore_dest_path = None
        self.ddb_ma_name = None
        self.cs_backupset_name = None
        self.cs_subclient_name = None
        self.CS_client = None
        self.cs_content_path = None
        self.cs_restore_path = None
        self.CS_agent = None
        self.cs_machine_obj = None
        self.agent = None
        self.Agent = None

        # DDB Client. 
        self.ddb_lib_name1 = None
        self.ddb_lib_name2 = None 
        self.ddb_policy_name1 = None 
        self.ddb_policy_name2 = None 
        self.ddb_mount_path1 = None
        self.dbb_mount_path2 = None
        self.ddb_partition_path1 = None
        self.ddb_partition_path2 = None

        self.MA1_details = {
            "MediaAgentName": None,
            "disk_lib_name": None,
            "MountPath": None,
            "storage_policy_name": None,
            "cloud_lib_name": None,
            "secondary_copy_name": None,
            "backupset_name": None,
            "subclient_name": None,
            "partition_path": None
        }
        self.MA2_details = {
            "MediaAgentName": None,
            "disk_lib_name": None,
            "MountPath": None,
            "storage_policy_name": None,
            "cloud_lib_name": None,
            "secondary_copy_name": None,
            "backupset_name": None,
            "subclient_name": None,
            "partition_path": None
        }

        self.tcinputs = {
            "Machine": {
                "ClientMachine": {
                    "Hostname": None,
                    "Username": None,
                    "Password": None
                },
                "MA1Machine": {
                    "Hostname": None,
                    "Username": None,
                    "Password": None
                },
                "MA2Machine": {
                    "Hostname": None,
                    "Username": None,
                    "Password": None
                }
            },
            "AgentName": None,
            "ClientName": None,
            "CloudMountPath": None,
            "CloudUserName": None,
            "CloudPassword": None,
            "CloudServerType": None
        }

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        self.MA1_details["MediaAgentName"] = '%s_media_agent_1' % str(self.id)
        self.MA2_details["MediaAgentName"] = '%s_media_agent_2' % str(self.id)
        self.ClientAgent = 'client_agent'

        # Media Agents Details
        self.MA1_details["disk_lib_name"] = '%s_library_M1DL' % str(self.id)
        self.MA2_details["disk_lib_name"] = '%s_library_M2DL' % str(self.id)
        self.MA1_details["cloud_lib_name"] = '%s_library_M1CL' % str(self.id)
        self.MA2_details["cloud_lib_name"] = '%s_library_M2CL' % str(self.id)
        self.MA1_details["storage_policy_name"] = '%s_storage_policy_1' % str(self.id)
        self.MA2_details["storage_policy_name"] = '%s_storage_policy_2' % str(self.id)
        self.MA1_details["secondary_copy_name"] = '%s_copy1' % str(self.id)
        self.MA2_details["secondary_copy_name"] = '%s_copy2' % str(self.id)
        self.MA1_details["backupset_name"] = '%s_backup_set_1' % str(self.id)
        self.MA2_details["backupset_name"] = '%s_backup_set_2' % str(self.id)
        self.cs_backupset_name = '%s_CS_backup_set' % str(self.id)
        self.MA1_details["subclient_name"] = '%s_subclient_1' % str(self.id)
        self.MA2_details["subclient_name"] = '%s_subclient_2' % str(self.id)
        self.cs_subclient_name = '%s_CS_subclient' % str(self.id)

        # DDB Details 
        self.ddb_lib_name1 = '%s_DDBLib' % str(self.MA1_details.get("MediaAgentName"))
        self.ddb_lib_name2 = '%s_DDBLib' % str(self.MA2_details.get("MediaAgentName"))
        self.ddb_policy_name1 = '%s_DDBPolicy' % str(self.MA1_details.get("MediaAgentName"))
        self.ddb_policy_name2 = '%s_DDBPolicy' % str(self.MA2_details.get("MediaAgentName"))

        Machine = self.tcinputs.get("Machine")
        # Creating CS Machine Object
        self.cs_machine_obj = options_selector.get_machine_object(
            self.tcinputs['ClientName'])
        # Creating Client Machine Object
        self.log.info("Creating Client Machine Object")
        ClientMachine = Machine.get("ClientMachine")
        self.client_machine_obj = options_selector.get_machine_object(
            ClientMachine['Hostname'], ClientMachine['Username'], ClientMachine['Password']
        )

        # Creating MA1 Machine Object
        self.log.info("Creating Media Agent 1 Machine Object")
        MA1Machine = Machine.get("MA1Machine")
        self.ma1_machine_obj = options_selector.get_machine_object(
            MA1Machine['Hostname'], MA1Machine['Username'], MA1Machine['Password']
        )
        # Creating MA2 Machine Object
        self.log.info("Creating Media Agent 2 Machine Object")
        MA2Machine = Machine.get("MA2Machine")
        self.ma2_machine_obj = options_selector.get_machine_object(
            MA2Machine['Hostname'], MA2Machine['Username'], MA2Machine['Password']
        )

        # Get Commserve Version
        commserve_version = int(self.commcell.commserv_version)
        self.log.info("commcell version %s", commserve_version)

        # Installing Media Agent 1
        self.log.info("Installating fresh MediaAgent client 1 for version %s", commserve_version - 2)
        self.MA1_client = self.fresh_install(
            self.ma1_machine_obj, self.MA1_details["MediaAgentName"],
            commserve_version - 2, ['FILE_SYSTEM', 'MEDIA_AGENT'],
            MA1Machine.get("mediaPath")
        )

        # Installing Media Agent 2
        self.log.info("Installating fresh MediaAgent client 2 for version %s", commserve_version - 4)
        self.MA2_client = self.fresh_install(
            self.ma2_machine_obj, self.MA2_details["MediaAgentName"],
            commserve_version - 4, ['FILE_SYSTEM', 'MEDIA_AGENT'],
            MA2Machine.get("mediaPath")
        )

        # Installing Client
        self.log.info("Installating fresh client for version %s", commserve_version - 6)
        self.remote_client = self.fresh_install(
            self.client_machine_obj, self.ClientAgent,
            commserve_version - 6, ['FILE_SYSTEM'],
            ClientMachine.get("mediaPath")
        )

        if self.MA1_client:
            self.MAAgent = self.MA1_client.agents.get(self.tcinputs['AgentName'])
        if self.remote_client:
            self.Agent = self.remote_client.agents.get(self.tcinputs['AgentName'])

        # Initialize MMHelper
        self.MMHelper = MMHelper(self)

        # Initialize DedupeHelper
        self.DedupeHelper = DedupeHelper(self)

        # Initialize CommonUtils
        self.common_util = CommonUtils(self)

        # select drive in client machine
        self.log.info(
            'Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(
            self.client_machine_obj, size=10 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        # select drive in cs machine
        self.log.info(
            'Selecting drive in the CS machine based on space available')
        cs_drive = options_selector.get_drive(
            self.cs_machine_obj, size=10 * 1024)
        if cs_drive is None:
            raise Exception("No free space for generating data on CS")
        self.log.info('selected drive: %s', cs_drive)

        # select drive in media agent 1.
        self.log.info('Selecting drive in the media agent machine 1 based on space available')
        ma_drive_1 = options_selector.get_drive(self.ma1_machine_obj, size=20 * 1024)
        if ma_drive_1 is None:
            raise Exception("No space for hosting backup and ddb")
        self.log.info('selected drive: %s', ma_drive_1)

        # select drive in media agent 2.
        self.log.info('Selecting drive in the media agent machine 2 based on space available')
        ma_drive_2 = options_selector.get_drive(self.ma2_machine_obj, size=20 * 1024)
        if ma_drive_2 is None:
            raise Exception("No space for hosting backup and ddb")
        self.log.info('selected drive: %s', ma_drive_2)

        # Mount Paths
        self.MA1_details["MountPath"] = self.ma1_machine_obj.join_path(
            ma_drive_1, 'Automation', str(self.id), 'MP1')
        self.MA2_details["MountPath"] = self.ma2_machine_obj.join_path(
            ma_drive_2, 'Automation', str(self.id), 'MP2')
        
        self.ddb_mount_path1 = self.ma1_machine_obj.join_path(
            ma_drive_1, 'Automation', str(self.id), 'DDB_MP1')
        self.ddb_mount_path2 = self.ma2_machine_obj.join_path(
            ma_drive_2, 'Automation', str(self.id), 'DDB_MP2')

        # Content Path
        self.content_path = self.client_machine_obj.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata')
        self.cs_content_path = self.cs_machine_obj.join_path(
            cs_drive, "Automation", str(self.id), 'Testdata'
        )

        # Restore Path
        self.restore_dest_path = self.client_machine_obj.join_path(
            client_drive, 'Automation', str(self.id), 'Restoredata')
        self.cs_restore_path = self.cs_machine_obj.join_path(
            cs_drive, 'Automation', str(self.id), 'Restoredata')

        # Partition Path
        if MA1Machine.get("partition_path"):
            self.MA1_details["partition_path"] = MA1Machine.get("partition_path")
        else:
            self.MA1_details["partition_path"] = self.ma1_machine_obj.join_path(ma_drive_1, 'Automation', str(self.id), 'DDB1')

        self.log.info(f"Partition Path selected for Media Agent 1 - {self.MA1_details['partition_path']}")

        if MA2Machine.get("partition_path"):
            self.MA2_details["partition_path"] = MA2Machine.get("partition_path")
        else:
            self.MA2_details["partition_path"] = self.ma2_machine_obj.join_path(ma_drive_2, 'Automation', str(self.id), 'DDB2')

        self.log.info(f"Partition Path selected for Media Agent 2 - {self.MA2_details['partition_path']}")

        self.ddb_partition_path1 = self.ma1_machine_obj.join_path(ma_drive_1, 'Automation', str(self.id), 'DDB_partition_path1')
        self.ddb_partition_path2 = self.ma2_machine_obj.join_path(ma_drive_2, 'Automation', str(self.id), 'DDB2_partition_path2')

        # clean up
        self._cs_cleanup()
        self._client_cleanup()
        self._ma_cleanup()

    def fresh_install(self, machine_obj, client_name, feature_release, packages, mediaPath):
        """
        Silent installs a new Media Agent Client

        Args:
            client_name -- (str) -- Client name provided for installation
            feature_release -- (int) - Feature release of the bootstrapper.

        Exception:
                If installation fails
        """
        self.log.info("Creating Install Helper")
        install_helper = InstallHelper(self.commcell, machine_obj)
        self.log.info("Checking if client already on CS for %s", client_name)
        if self.commcell.clients.has_client(client_name):
            client_obj = self.commcell.clients.get(client_name)
            self.log.info(f"comparing version  {client_obj.service_pack} - {feature_release}")
            if str(client_obj.service_pack) == str(feature_release):
                self.log.info("Check Readiness of Client")
                if client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
                    return client_obj
                else:
                    raise Exception("Client Readiness failed!")
            else:
                self._ddb_cleanup()
                install_helper.uninstall_client(delete_client=False, instance=client_obj.instance)

        silent_install_dict = {
            "csClientName": self.commcell.commserv_name,
            "csHostname": self.commcell.commserv_hostname,
            "authCode": self.commcell.enable_auth_code(),
            "mediaPath": mediaPath
        }
        self.log.info(f"Service Pack to be Installed on the client: {feature_release}")
        install_helper.silent_install(
            client_name=client_name,
            tcinputs=silent_install_dict,
            feature_release=f"SP{feature_release}",
            packages=packages
        )

        self.log.info("Refreshing Client List on the CS")
        self.commcell.refresh()

        self.log.info("Initiating Check Readiness from the CS for %s", client_name)
        if self.commcell.clients.has_client(client_name):
            client_obj = self.commcell.clients.get(client_name)
            if client_obj.is_ready:
                self.log.info("Check Readiness of Client is successful")
        else:
            self.log.error("Client failed Registration to the CS")
            raise Exception(f"Client: {client_name} failed registering to the CS, Please check client logs")

        self.log.info("Starting Install Validation")
        install_validation = InstallValidator(client_obj.client_hostname, self)
        self.log.info(f"Validating Services running on the Client with hostname {client_obj.client_hostname}")
        install_validation.validate_services()
        self.log.info("Packages successfully installed on client machine")
        return client_obj

    def _ma_cleanup(self):
        """Cleanup the entities created"""

        self.log.info(
            "********************** MA CLEANUP STARTING *************************")
        # Delete backupsets
        self.log.info("Deleting BackupSet: %s if exists",
                      self.MA1_details.get("backupset_name"))
        if self.MAAgent.backupsets.has_backupset(self.MA1_details.get("backupset_name")):
            self.MAAgent.backupsets.delete(self.MA1_details.get("backupset_name"))
            self.log.info("Deleted BackupSet: %s", self.MA1_details.get("backupset_name"))

        self.log.info("Deleting BackupSet: %s if exists",
                      self.MA1_details.get("backupset_name"))
        if self.Agent.backupsets.has_backupset(self.MA1_details.get("backupset_name")):
            self.Agent.backupsets.delete(self.MA1_details.get("backupset_name"))
            self.log.info("Deleted BackupSet: %s", self.MA1_details.get("backupset_name"))
        
        self.log.info("Deleting BackupSet: %s if exists",
                      self.MA2_details.get("backupset_name"))
        if self.Agent.backupsets.has_backupset(self.MA2_details.get("backupset_name")):
            self.Agent.backupsets.delete(self.MA2_details.get("backupset_name"))
            self.log.info("Deleted BackupSet: %s", self.MA2_details.get("backupset_name"))

        # Delete Storage Policy
        self.log.info("Deleting Storage Policy: %s if exists",
                      self.MA1_details.get("storage_policy_name"))
        if self.commcell.storage_policies.has_policy(self.MA1_details.get("storage_policy_name")):
            self.commcell.storage_policies.delete(self.MA1_details.get("storage_policy_name"))
            self.log.info("Deleted Storage Policy: %s",
                          self.MA1_details.get("storage_policy_name"))
        
        self.log.info("Deleting Storage Policy: %s if exists",
                      self.MA2_details.get("storage_policy_name"))
        if self.commcell.storage_policies.has_policy(self.MA2_details.get("storage_policy_name")):
            self.commcell.storage_policies.delete(self.MA2_details.get("storage_policy_name"))
            self.log.info("Deleted Storage Policy: %s",
                          self.MA2_details.get("storage_policy_name"))

        # Delete Library
        self.log.info(
            "Deleting library: %s if exists", self.MA1_details.get("disk_lib_name"))
        if self.commcell.disk_libraries.has_library(self.MA1_details.get("disk_lib_name")):
            self.commcell.disk_libraries.delete(self.MA1_details.get("disk_lib_name"))
            self.log.info("Deleted library: %s", self.MA1_details.get("disk_lib_name"))
        
        self.log.info(
            "Deleting library: %s if exists", self.MA2_details.get("disk_lib_name"))
        if self.commcell.disk_libraries.has_library(self.MA2_details.get("disk_lib_name")):
            self.commcell.disk_libraries.delete(self.MA2_details.get("disk_lib_name"))
            self.log.info("Deleted library: %s", self.MA2_details.get("disk_lib_name"))

        self.log.info(
            "Deleting library: %s if exists", self.MA2_details.get("cloud_lib_name"))
        if self.commcell.disk_libraries.has_library(self.MA2_details.get("cloud_lib_name")):
            self.commcell.disk_libraries.delete(self.MA2_details.get("cloud_lib_name"))
            self.log.info("Deleted library: %s", self.MA2_details.get("cloud_lib_name"))
        
        self.log.info(
            "Deleting library: %s if exists", self.MA1_details.get("cloud_lib_name"))
        if self.commcell.disk_libraries.has_library(self.MA1_details.get("cloud_lib_name")):
            self.commcell.disk_libraries.delete(self.MA1_details.get("cloud_lib_name"))
            self.log.info("Deleted library: %s", self.MA1_details.get("cloud_lib_name"))
        self.log.info(
            "********************** MA CLEANUP COMPLETED *************************")

    def _client_cleanup(self):
        """Cleanup the entities created"""

        self.log.info(
            "********************** CLIENT CLEANUP STARTING *************************")
        # Restore and content folder if created.
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.client_machine_obj.remove_directory(self.content_path)
        self.log.info("Removed Content directory")

        if self.client_machine_obj.check_directory_exists(self.restore_dest_path):
            self.client_machine_obj.remove_directory(self.restore_dest_path)
        self.log.info("Removed Restore directory")
        self.log.info(
            "********************** CLIENT CLEANUP COMPLETED *************************")

    def _cs_cleanup(self):
        """Cleanup the entities created"""
        self.log.info(
            "********************** CS CLEANUP STARTING *************************")
        # Deleting Backupset
        self.log.info("Deleting BackupSet: %s if exists",
                      self.cs_backupset_name)
        if self.agent.backupsets.has_backupset(self.cs_backupset_name):
            self.agent.backupsets.delete(self.cs_backupset_name)
            self.log.info("Deleted BackupSet: %s", self.cs_backupset_name)

        # Delete CS Content
        if self.cs_machine_obj.check_directory_exists(self.restore_dest_path):
            self.cs_machine_obj.remove_directory(self.restore_dest_path)
        self.log.info("Removed CS Restore directory")
        # CS Content
        if self.cs_machine_obj.check_directory_exists(self.cs_content_path):
            self.cs_machine_obj.remove_directory(self.cs_content_path)
        self.log.info("Removed CS Content directory")
        self.log.info(
            "********************** CS CLEANUP COMPLETED *************************")
    
    def _ddb_cleanup(self):
        """
        Cleanup DDB Resources
        """
        # Deleting DDB Storage Policies.
        self.log.info("Deleting Storage Policy: %s if exists", self.ddb_policy_name1)
        if self.commcell.storage_policies.has_policy(self.ddb_policy_name1):
            self.log.info(f"Re-Associating Storage Policy {self.ddb_policy_name1}")
            StoragePolicy(self.commcell, self.ddb_policy_name1).reassociate_all_subclients()
            self.commcell.storage_policies.delete(self.ddb_policy_name1)
            self.log.info("Deleted Storage Policy: %s", self.ddb_policy_name1)
        
        self.log.info("Deleting Storage Policy: %s if exists", self.ddb_policy_name2)
        if self.commcell.storage_policies.has_policy(self.ddb_policy_name2):
            self.log.info(f"Re-Associating Storage Policy {self.ddb_policy_name2}")
            StoragePolicy(self.commcell, self.ddb_policy_name2).reassociate_all_subclients()
            self.commcell.storage_policies.delete(self.ddb_policy_name2)
            self.log.info("Deleted Storage Policy: %s", self.ddb_policy_name2)
        # Deleting DDB Libraries.
        self.log.info("Deleting library: %s if exists", self.ddb_lib_name1)
        if self.commcell.disk_libraries.has_library(self.ddb_lib_name1):
            self.commcell.disk_libraries.delete(self.ddb_lib_name1)
            self.log.info("Deleted library: %s", self.ddb_lib_name1)
        
        self.log.info("Deleting library: %s if exists", self.ddb_lib_name2)
        if self.commcell.disk_libraries.has_library(self.ddb_lib_name2):
            self.commcell.disk_libraries.delete(self.ddb_lib_name2)
            self.log.info("Deleted library: %s", self.ddb_lib_name2)
    
    def _restore_verify(self, machine, src_path, dest_path):
        """
            Performs the verification after restore

            Args:
                machine          (object)    --  Machine class object.

                src_path         (str)       --  path on source machine that is to be compared.

                dest_path        (str)       --  path on destination machine that is to be compared.

            Raises:
                Exception - Any difference from source data to destination data

        """
        self.log.info("Comparing source:%s destination:%s", src_path, dest_path)
        diff_output = machine.compare_folders(machine, src_path, dest_path)

        if not diff_output:
            self.log.info("Checksum comparison successful")
        else:
            self.log.error("Checksum comparison failed")
            self.log.info("Diff output: \n%s", diff_output)
            raise Exception("Checksum comparison failed")

    def create_ddb_resources(self):
        """
            Creates DDB Resources for Media Agent 1 and Media Agent 2 Client. 
        """
        # Creating DDB Libraries
        self.log.info(f"Creating DDB Library {self.ddb_lib_name1} if not exists")
        lib_obj1 = self.MMHelper.configure_disk_library(
            self.ddb_lib_name1,
            self.MA1_details.get("MediaAgentName"),
            self.ddb_mount_path1)
        self.log.info(f"Creating DDB Library {self.ddb_lib_name2} if not exists")
        lib_obj2 = self.MMHelper.configure_disk_library(
            self.ddb_lib_name2,
            self.MA2_details.get("MediaAgentName"),
            self.ddb_mount_path2)
        # Creating Storage Policies
        if not self.commcell.storage_policies.has_policy(self.ddb_policy_name1):
            self.DedupeHelper.configure_dedupe_storage_policy(
                self.ddb_policy_name1, lib_obj1,
                self.MA1_details.get("MediaAgentName"),
                self.ddb_partition_path1)
        if not self.commcell.storage_policies.has_policy(self.ddb_policy_name2):
            self.DedupeHelper.configure_dedupe_storage_policy(
                self.ddb_policy_name2, lib_obj2,
                self.MA2_details.get("MediaAgentName"),
                self.ddb_partition_path2)

    def run_util(self, storage_policy, details):
        """
            Run util helper function.

            Args:
                storage_policy -- storage policy object.
                details (dict) -- dict object with Media Agent details.
        """
        # remove association of secondary and primary copy with system created autocopy schedule.
        self.log.info("remove association of secondary copy with system created autocopy schedule")
        self.MMHelper.remove_autocopy_schedule(
            storage_policy_name=details.get("storage_policy_name"),
            copy_name=details.get("secondary_copy_name"))

        # create backupset
        self.log.info("creating backupset %s", details.get("backupset_name"))

        self.MMHelper.configure_backupset(details.get("backupset_name"), self.Agent)

        # create subclient
        self.log.info("creating subclient %s", details.get("subclient_name"))
        subclient = self.MMHelper.configure_subclient(
            details.get("backupset_name"), details.get("subclient_name"),
            details.get("storage_policy_name"), self.content_path, self.Agent
        )

        # run backup
        self.log.info("Starting backup jobs for subclient %s", details.get("subclient_name"))
        job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full', 'incremental',
                                       'synthetic_full']

        for sequence_index in range(len(job_types_sequence_list)):
            # Create unique content
            if job_types_sequence_list[sequence_index] != 'synthetic_full':
                if not self.MMHelper.create_uncompressable_data(self.client_machine_obj, self.content_path, 0.1, 10):
                    self.log.error(
                        "unable to Generate Data at %s", self.content_path)
                    raise Exception(
                        "unable to Generate Data at {0}".format(self.content_path))
                self.log.info("Generated Data at %s", self.content_path)

            # Perform Backup
            job_id = self.common_util.subclient_backup(
                subclient, job_types_sequence_list[sequence_index]).job_id

            self.log.info('Backup Job %s Completed', job_id)

        # Run Restore Job on primary copy
        self.log.info("stating restore job for %s", subclient)
        restore_job = subclient.restore_out_of_place(self.remote_client, self.restore_dest_path,
                                                     [self.content_path])
        self.log.info(
            "restore job [%s] has started from primary copy.", restore_job.job_id)
        if not restore_job.wait_for_completion():
            self.log.error(
                "restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
            raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                            restore_job.delay_reason))
        self.log.info(
            "restore job [%s] has completed.", restore_job.job_id)
        
        # Verify restored data
        if self.client_machine_obj.os_info == 'UNIX':
            dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '/')
        else:
            dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '\\')

        dest_path = self.client_machine_obj.join_path(dest_path, 'Testdata')

        self._restore_verify(self.client_machine_obj, self.content_path, dest_path)

        # Run Aux copy Job
        auxcopy_job = storage_policy.run_aux_copy()
        self.log.info("Auxcopy job [%s] has started.", auxcopy_job.job_id)
        if not auxcopy_job.wait_for_completion():
            self.log.error(
                "Auxcopy job [%s] has failed with %s.", auxcopy_job.job_id, auxcopy_job.delay_reason)
            raise Exception(
                "Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id, auxcopy_job.delay_reason))
        self.log.info(
            "Auxcopy job [%s] has completed.", auxcopy_job.job_id)

        # Remove content and Restore from non dedupe secondary copy -- add restore validation ----add
        self.client_machine_obj.remove_directory(self.restore_dest_path)
        restore_job = subclient.restore_out_of_place(self.remote_client, self.restore_dest_path, [self.content_path],
                                                     copy_precedence=2)
        self.log.info(
            "restore job [%s] has started from non dedupe secondary copy.", restore_job.job_id)
        if not restore_job.wait_for_completion():
            self.log.error(
                "restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
            raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                            restore_job.delay_reason))

        # Run DataAging on Storage Policy 1 on MA1
        data_aging_job = self.commcell.run_data_aging(storage_policy_name=details.get("storage_policy_name"),
                                                      is_granular=True, include_all_clients=True)
        self.log.info(
            "Data Aging job [%s] has started.", data_aging_job.job_id)
        if not data_aging_job.wait_for_completion():
            self.log.error(
                "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
            raise Exception(
                "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                   data_aging_job.delay_reason))
        self.log.info(
            "Data Aging job [%s] has completed.", data_aging_job.job_id)


    def run(self):
        """Run function of this test case"""
        try:
            # Create DDB Resources 
            self.create_ddb_resources()

            # Create Disk Library DL1 on MA1
            self.MMHelper.configure_disk_library(
                library_name=self.MA1_details.get("disk_lib_name"),
                ma_name=self.MA1_details.get("MediaAgentName"),
                mount_path=self.MA1_details.get("MountPath")
            )
            # Create Cloud Library CL1 on MA1
            self.log.info("Creating Cloud Library 1")
            if (("CloudMountPath" and "CloudUserName" and "CloudPassword" and "CloudServerType" in self.tcinputs) and
                    (self.tcinputs["CloudMountPath"] and self.tcinputs["CloudUserName"]
                     and self.tcinputs["CloudPassword"] and self.tcinputs["CloudServerType"])):
                self.MMHelper.configure_cloud_library(
                    self.MA1_details.get("cloud_lib_name"),
                    self.MA1_details.get('MediaAgentName'),
                    self.tcinputs["CloudMountPath"],
                    self.tcinputs["CloudUserName"],
                    self.tcinputs["CloudPassword"],
                    self.tcinputs["CloudServerType"]
                )

            # Create Disk Library DL2 on MA2
            self.MMHelper.configure_disk_library(
                library_name=self.MA2_details.get("disk_lib_name"),
                ma_name=self.MA2_details.get("MediaAgentName"),
                mount_path=self.MA2_details.get("MountPath")
            )

            # Create Cloud Library CL2 on MA2
            self.log.info("Creating Cloud Library 2")
            if (("CloudMountPath" and "CloudUserName" and "CloudPassword" and "CloudServerType" in self.tcinputs) and
                    (self.tcinputs["CloudMountPath"] and self.tcinputs["CloudUserName"]
                     and self.tcinputs["CloudPassword"] and self.tcinputs["CloudServerType"])):
                self.MMHelper.configure_cloud_library(
                    self.MA2_details.get("cloud_lib_name"),
                    self.MA2_details.get('MediaAgentName'),
                    self.tcinputs["CloudMountPath"],
                    self.tcinputs["CloudUserName"],
                    self.tcinputs["CloudPassword"],
                    self.tcinputs["CloudServerType"]
                )

        # Configuration for Storage Policy 1
            # Dedupe Primary Copy points to DL1 + MA1 and DDB on MA2
            self.log.info("Creating Dedupe Primary Copy")
            self.log.info(f"DDB Path {self.MA2_details.get('partition_path')}")
            storage_policy_1 = self.DedupeHelper.configure_dedupe_storage_policy(
                storage_policy_name=self.MA1_details.get("storage_policy_name"),
                library_name=self.MA1_details.get("disk_lib_name"),
                ma_name=self.MA1_details.get("MediaAgentName"),
                ddb_path=self.MA2_details.get("partition_path"),
                ddb_ma_name=self.MA2_details.get("MediaAgentName")
            )

            # Dedupe Secondary Copy 2 points to CL2 + MA2 and DDB on MA1
            self.log.info("Creating Dedupe Enabled Secondary Copy")
            sec_copy = self.DedupeHelper.configure_dedupe_secondary_copy(
                storage_policy=storage_policy_1,
                copy_name=self.MA1_details.get("secondary_copy_name"),
                library_name=self.MA2_details.get("cloud_lib_name"),
                media_agent_name=self.MA2_details.get("MediaAgentName"),
                partition_path=self.MA1_details.get("partition_path"),
                ddb_media_agent=self.MA1_details.get("MediaAgentName")
            )
            self.log.info("Setting Retention: 0-days and 1-cycle on all copies")
            retention = (0, 1, -1)
            primary_copy = storage_policy_1.get_copy("Primary")
            sec_copy.copy_retention = retention
            primary_copy.copy_retention = retention
            # Run Util for Storage policy 1 and Media Agent 1.
            self.run_util(storage_policy_1, self.MA1_details)

        # Configuration for Storage Policy 2
            # Non-Dedupe Primary Copy points to DL2 + MA2
            storage_policy_2 = self.MMHelper.configure_storage_policy(
                storage_policy_name=self.MA2_details.get("storage_policy_name"),
                library_name=self.MA2_details.get("disk_lib_name"),
                ma_name=self.MA2_details.get("MediaAgentName")
            )
            # Non-Dedupe Copy2 points to CL1+MA1
            sec_copy = self.MMHelper.configure_secondary_copy(
                sec_copy_name=self.MA2_details.get("secondary_copy_name"),
                storage_policy_name=self.MA2_details.get("storage_policy_name"),
                library_name=self.MA1_details.get("cloud_lib_name"),
                ma_name=self.MA1_details.get("MediaAgentName")
            )
            self.log.info("Setting Retention: 0-days and 1-cycle on all copies")
            primary_copy = storage_policy_2.get_copy("Primary")
            sec_copy.copy_retention = retention
            primary_copy.copy_retention = retention
            # Run Util for Storage policy 2 and Media Agent 2
            self.run_util(storage_policy_2, self.MA2_details)

        # Negative Test Case Using MA1

            # Backupset
            self.log.info("creating backupset on CS %s", self.MA1_details.get('backupset_name'))

            self.MMHelper.configure_backupset(self.MA1_details.get('backupset_name'), self.MAAgent)

            # create subclient -
            self.log.info("creating subclient %s", self.MA1_details.get('subclient_name'))
            ma_subclient = self.MMHelper.configure_subclient(
                self.MA1_details.get('backupset_name'), self.MA1_details.get('subclient_name'),
                self.MA2_details.get("storage_policy_name"), self.content_path,
                self.MAAgent
            )

            # Generating data on CS machine.
            if not self.MMHelper.create_uncompressable_data(self.cs_machine_obj, self.cs_content_path, 0.1, 10):
                self.log.error(
                    "unable to Generate Data at %s", self.cs_content_path)
                raise Exception(
                    "unable to Generate Data at {0}".format(self.cs_content_path))
            self.log.info("Generated Data at %s", self.cs_content_path)

            # Backup Job
            self.log.info("Stating backup job for %s", self.MA1_details.get('subclient_name'))
            ma_job = ma_subclient.backup(r'full')
            while True:
                status = ma_job.status.lower()
                self.log.info("Job Status", status)
                if status == 'pending':
                    self.log.info("Negative Case: Failed to run FULL backup job: {0}".format(ma_job.delay_reason))
                    ma_job.kill()
                    self.log.info("Negative Case: Job Killed Successfully")
                    break
                if status == 'completed':
                    self.log.info("Negative Case: Job completed")
                    raise Exception(
                        "Negative Case: Test case failed for job {0}.".format(ma_job.job_id))
            self.log.info("Negative case completed. ")

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""
        if self.status != constants.FAILED:
            self.log.info(
                "Testcase shows successful execution, cleaning up the test environment ...")
            try:
                self._cs_cleanup()
                self._client_cleanup()
                self._ma_cleanup()
            except Exception as exp:
                raise Exception(
                    "Error encountered during ma cleanup: {0}".format(str(exp)))
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment ...")
