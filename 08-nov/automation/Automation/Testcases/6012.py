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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    push_install()  -- installs a new media agent client.

    verify_mmhost_table() 
                        -- verify if MediaAgent in MMHost table.

    validate_license() -- verifies is licese is installed or not. 

    verify_lib_controller()
                        -- verifies library has no controller.

Design Steps:
    1. Install a MediaAgent MA1 [Win or Linux]
    2. Configure storage:
        - Disk Library
        - Cloud library

    3. Configure two storage policies
        - SP1 - Disk Library
        - SP2 - Cloud Library
    4. Configure two Subclients
    5. Run a full backup to these two subclients
    6. Delete MA1
    7. Verify MMHost table entry should be deleted for MA1
    8. Validate Storages are not deconfigured but have no MA on them
    9. Storage policy should not be deleted.
    10. Check for licenses are released as well.

Sample Input:
    "6012": {
                "ClientName": "ClientName",
                "AgentName": "File System",
                "MachineHostName": "Hostname
                "MachineUsername": "Username",
                "MachinePassword": "Password",
                "CloudMountPath":"MountPath",
                "CloudUserName": "Username",
                "CloudPassword": "Password",
                "CloudServerType":"ServerType"
            }
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test case of MediaAgent delete"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Uninstall MA - ALL"
        self.MA_Client = None
        self.MMHelper = None
        self.install_helper = None
        self.common_util = None
        self.ma_machine_obj = None
        self.ma_name = None
        self.client_machine_obj = None
        self.hostname = None

        self.disk_lib_name = None
        self.cloud_library_name = None
        self.disk_lib_mountpath = None
        self.disk_storage_policy_name = None
        self.cloud_storage_policy_name = None
        self.backupset_name1 = None
        self.backupset_name2 = None
        self.disk_subclient = None
        self.cloud_subclinet = None

        self.MediaAgentName = None

        self.content_path = None
        self.restore_dest_path = None

        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MachineHostName": None,
            "MachineUsername": None,
            "MachinePassword": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Starting test case setup")
        self.client = self.tcinputs['ClientName']
        self.MMHelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        options_selector = OptionsSelector(self.commcell)

        # Media agent machine object
        self.ma_machine_obj = options_selector.get_machine_object(
            self.tcinputs['MachineHostName'], self.tcinputs['MachineUsername'],
            self.tcinputs['MachinePassword']
        )
        self.hostname = self.ma_machine_obj.machine_name

        # Client machine object
        self.client_machine_obj = options_selector.get_machine_object(self.tcinputs['ClientName'])

        # Install Helper
        self.install_helper = InstallHelper(self.commcell, self.ma_machine_obj)

        # Push install  on MA machine.
        self.MA_Client = self.push_install()
        self.MediaAgentName = self.MA_Client.display_name
        self.log.info(f"MEDIA AGENT NAME {self.MediaAgentName}")
        self.log.info(f"push install completed on {self.hostname}")

        # Selecting Drive in Machines
        ma_drive = options_selector.get_drive(self.ma_machine_obj, size=10 * 1024)
        client_drive = options_selector.get_drive(self.client_machine_obj, size=10 * 1024)

        # Storage_policy
        self.disk_storage_policy_name = f"{self.id}_disk_storage_policy"
        self.cloud_storage_policy_name = f"{self.id}_cloud_storage_policy"

        # Backupset
        self.backupset_name1 = f"{self.id}_backupset1"
        self.backupset_name2 = f"{self.id}_backupset2"

        # Subclient
        self.disk_subclient = f"{self.id}_disk_subclient"
        self.cloud_subclient = f"{self.id}_cloud_subclient"

        # Disk Library
        self.disk_lib_name = '%s_disk_lib' % str(self.id)
        self.disk_lib_mountpath = self.ma_machine_obj.join_path(
            ma_drive, 'Automation', str(self.id), 'MP'
        )

        # Cloud library
        self.cloud_library_name = '%s_cloud_lib' % str(self.id)

        # Content path
        self.content_path = self.client_machine_obj.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata')

        # Restore path
        self.restore_dest_path = self.client_machine_obj.join_path(
            client_drive, 'Automation', str(self.id), 'Restoredata')
        
        # clean up 
        self._cleanup()
        self.log.info("Successfully completed test case setup")

    def push_install(self):
        """
        Installs a new Media Agent using push install. 
        """
        # Check if MA is already installed.
        if self.commcell.clients.has_client(self.hostname):
            client_obj = self.commcell.clients.get(self.hostname)
            self.log.info("%s already installed", self.hostname)
            self.install_helper.uninstall_client(delete_client=True, instance=client_obj.instance)

        # Pushing Packages from CS to the windows client
        self.log.info(f"Starting a Push Install Job: {self.hostname}")
        push_job = self.install_helper.install_software(
                            client_computers=[self.hostname],
                            features=['FILE_SYSTEM', 'MEDIA_AGENT'],
                            username=self.tcinputs['MachineUsername'],
                            password=self.tcinputs['MachinePassword']
        )
        self.log.info(f"Job Launched Successfully for Windows, Will wait until Job: {push_job.job_id} Completes")
        if push_job.wait_for_completion():
            self.log.info("Push Upgrade Job Completed successfully")
        else:
            job_status = push_job.delay_reason
            self.log.error(f"Job failed with an error: {job_status}")
            raise Exception(job_status)

        # Check Readiness Test --
        # Refreshing the Client list to me the New Client Visible on GUI
        self.log.info("Refreshing Client List on the CS")
        self.commcell.refresh()

        # Check if the services are up on Client and is Reachable from CS
        self.log.info("Initiating Check Readiness from the CS")
        if self.commcell.clients.has_client(self.hostname):
            client_obj = self.commcell.clients.get(self.hostname)
            if client_obj.is_ready:
                self.log.info("Check Readiness of CS successful")
                return client_obj
        else:
            self.log.error("Client failed Registration to the CS")
            raise Exception(f"Client: {self.hostname} failed registering to the CS, "
                            f"Please check client logs")

    def verify_mmhost_table(self):
        """
        Verify that host details deleted from MMHost table
        """
        self.log.info("Validating MMHost table.")
        query = """select count(*) from mmhost where ClientId={0}""".format(self.MA_Client.client_id)
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        count = self.csdb.fetch_one_row()[0]

        if int(count) != 0:
            raise Exception('Validation Failed :: MMHost table is not cleaned-up')
        self.log.info("MMHost table cleaned-up for the deleted MediaAgent.")
        return True
    
    def verify_lib_controller(self, lib_id):
        """
        Verify that there is no MA controller for library. 
        """
        self.log.info("Validating MMDeviceController table.")
        query = f"""
                    select count(DeviceControllerId)
                    from MMDeviceController MDC 
                    Join MMMountPathToStorageDevice MPTS on MDC.DeviceId = MPTS.DeviceId 
                    Join MMMountPath MP on MPTS.MountPathId = MP.MountPathId
                    Join MMLibrary ML on MP.LibraryId = ML.LibraryId 
                    Where ML.LibraryId = {lib_id}
                """
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        count = self.csdb.fetch_one_row()[0]

        if int(count) != 0:
            raise Exception(f'Validation Failed :: Controller present for library {lib_id}')
        self.log.info(f"Validation Success :: No controller for library {lib_id}")
        return True

    def validate_license(self):
        """
        Validates if MediaAgent license is installed or not. 
        """
        self.log.info("Validating LicUsage Table.")
        query = """select distinct OpType 
                    from LicUsage where LicType = 11 
                    and CId = {0}""".format(self.MA_Client.client_id)
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info("RESULT %s", res)
        for obj in res:
            if obj != ['UnInstall']:
                raise Exception("Validation Failed:: Licenses are not released.")
        self.log.info("Licenses are released.")
        return True

    def _cleanup(self):
        """Cleanup the existing entities"""
        self.log.info(
            "********************** CLEANUP STARTING *************************")
        try:
            # Deleting Backupsets
            self.log.info("Deleting BackupSet if exists")
            if self._agent.backupsets.has_backupset(self.backupset_name1):
                self.log.info("BackupSet[%s] exists, deleting that", self.backupset_name1)
                self._agent.backupsets.delete(self.backupset_name1)

            self.log.info("Deleting BackupSet if exists")
            if self._agent.backupsets.has_backupset(self.backupset_name2):
                self.log.info("BackupSet[%s] exists, deleting that", self.backupset_name2)
                self._agent.backupsets.delete(self.backupset_name2)

            # Deleting Storage Policies
            self.log.info("Deleting Storage Policy if exists")
            if self.commcell.storage_policies.has_policy(self.disk_storage_policy_name):
                self.log.info("Storage Policy[%s] exists, deleting that", self.disk_storage_policy_name)
                self.commcell.storage_policies.delete(self.disk_storage_policy_name)

            self.log.info("Deleting Storage Policy if exists")
            if self.commcell.storage_policies.has_policy(self.cloud_storage_policy_name):
                self.log.info("Storage Policy[%s] exists, deleting that", self.cloud_storage_policy_name)
                self.commcell.storage_policies.delete(self.cloud_storage_policy_name)

            # Deleting Libraries
            self.log.info("Deleting disk library if exists")
            if self.commcell.disk_libraries.has_library(self.disk_lib_name):
                self.log.info("Library[%s] exists, deleting that", self.disk_lib_name)
                self.commcell.disk_libraries.delete(self.disk_lib_name)
            self.log.info("Cleanup completed")

            self.log.info("Deleting cloud library if exists")
            if self.commcell.disk_libraries.has_library(self.cloud_library_name):
                self.log.info("Library[%s] exists, deleting that", self.cloud_library_name)
                self.commcell.disk_libraries.delete(self.cloud_library_name)
            self.log.info("Cleanup completed")

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception(
                "Error encountered during cleanup: {0}".format(str(exp)))
        self.log.info(
            "********************** CLEANUP COMPLETED *************************")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")
        if self.status != constants.FAILED:
            self.log.info(
                "Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
        # Uninstall Media Agent Client
            if self.commcell.clients.has_client(self.hostname):
                client_obj = self.commcell.clients.get(self.hostname)
                self.log.info("%s is installed", self.hostname)
                self.install_helper.uninstall_client(delete_client=True, instance=client_obj.instance)
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment ...")

    def run(self):
        """Main test case logic"""
        try:
            # Creating a disk library
            self.log.info("Creating Disk Library")
            disk_lib = self.MMHelper.configure_disk_library(
                library_name=self.disk_lib_name,
                ma_name=self.MediaAgentName,
                mount_path=self.disk_lib_mountpath
            )
            lib_id1 = disk_lib.library_id

            # Create cloud library.
            self.log.info("creating cloud library")
            if (("CloudMountPath" and "CloudUserName" and "CloudPassword" and "CloudServerType" in self.tcinputs) and
                    (self.tcinputs["CloudMountPath"] and self.tcinputs["CloudUserName"]
                     and self.tcinputs["CloudPassword"] and self.tcinputs["CloudServerType"])):
                cloud_lib = self.MMHelper.configure_cloud_library(self.cloud_library_name,
                                                      self.MediaAgentName,
                                                      self.tcinputs["CloudMountPath"],
                                                      self.tcinputs["CloudUserName"],
                                                      self.tcinputs["CloudPassword"],
                                                      self.tcinputs["CloudServerType"])
            else:
                raise Exception("No Cloud Library details provided.")
            
            lib_id2 = cloud_lib.library_id
            # Storage Policy - Disk Library
            self.MMHelper.configure_storage_policy(
                self.disk_storage_policy_name, self.disk_lib_name,
                self.MediaAgentName
            )
            # Storage Policy - Cloud Library
            self.MMHelper.configure_storage_policy(
                self.cloud_storage_policy_name, self.cloud_library_name,
                self.MediaAgentName
            )

            # Creating Backupsets - Disk Library
            self.MMHelper.configure_backupset(self.backupset_name1)
            # Creating Backupsets - Cloud Library
            self.MMHelper.configure_backupset(self.backupset_name2)

            # Creating Subclient - Disk Storage Policy
            disk_subclinet = self.MMHelper.configure_subclient(
                self.backupset_name1, self.disk_subclient,
                self.disk_storage_policy_name, self.content_path
            )
            # Creating Subclient - Cloud Storage Policy
            cloud_subclient = self.MMHelper.configure_subclient(
                self.backupset_name2, self.cloud_subclient,
                self.cloud_storage_policy_name, self.content_path
            )

            # Run Full Backup job
            # Create unique content
            if not self.MMHelper.create_uncompressable_data(self.client_machine_obj, self.content_path, 0.1, 5):
                self.log.error(
                    "unable to Generate Data at %s", self.content_path)
                raise Exception(
                    "unable to Generate Data at {0}".format(self.content_path))
            self.log.info("Generated Data at %s", self.content_path)

            # Perform Backup - Disk Subclient
            self.log.info("Starting backup jobs for subclient %s", self.disk_subclient)
            job_id = self.common_util.subclient_backup(
                disk_subclinet, 'full').job_id

            self.log.info('Backup completed successfully on %s with job_id %s', self.disk_subclient, job_id)

            # Perform Backup - Cloud Library
            job_id = self.common_util.subclient_backup(
                cloud_subclient, 'full').job_id

            self.log.info('Backup completed successfully on %s with job_id %s', self.cloud_subclient, job_id)

            # Delete MA
            self.log.info("deleting Media Agent %s", self.MediaAgentName)
            self.commcell.media_agents.delete(self.MediaAgentName, force=True)

            # Verify MMHost table.
            self.verify_mmhost_table()

            # Verify Storage Policy are not deleted
            if not self.commcell.storage_policies.has_policy(self.disk_storage_policy_name):
                raise Exception(f"Validation Failure :: Storage Policy {self.disk_storage_policy_name} deleted.")
            
            if not self.commcell.storage_policies.has_policy(self.cloud_storage_policy_name):
                raise Exception(f"Validation Failure :: Storage Policy {self.cloud_storage_policy_name} deleted.")
            
            # Verify Library has no controller MA. 
            self.verify_lib_controller(lib_id1)
            self.verify_lib_controller(lib_id2)
            
            # Validate Licenses are released.
            self.validate_license()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
