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

    run()           --  run function of this test case

    tear_down()     --  teardown function of this test case

    _cleanup()      --  cleanup the entities created

    _validate_sa_package()  --  validate if client had storage accelerator package installed

    _validate_ma_package()  --  validate if client has media agent package installed or not

    _validate_sa_auto_install() --  validate if storage accelerator package auto push install was scheduled

    _validate_sa_auto_install_enabled() --  validate if storage accelerator auto install feature is enabled on CommCell

    _reset_mmentity_prop()  --  updates the mmentity prop val to 10 days before if entry exists

Sample Input:
            {
                "ClientName": "client_name",
                "MediaAgentName": "MA name",
                "AgentName": "File System"
            }
    Additional Inputs -
        "CloudLibraryName": "library name"
        OR
        "CloudMountPath": "mount path"
        "CloudUserName": "user name",
        "CloudPassword": "password",
        "CloudServerType": "Microsoft Azure Storage"
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import commonutils
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Storage Accelerator -- Auto push SA package"
        self.mmhelper = None
        self.common_util = None
        self.cs_machine = None
        self.client_machine = None
        self.cloud_library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.cloud_lib_obj = None
        self.content_path = None
        self.job_manager = None
        self.current_time = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }

    def _validate_sa_auto_install(self):
        """
        Validate if storage accelerator package auto push install was scheduled
        """

        self.log.info("Validating if storage accelerator package auto push install was scheduled")
        query = f""" 
                    SELECT 1 FROM MMEntityProp WITH (NOLOCK)
                    WHERE EntityId ={self.client.client_id} 
                    AND EntityType = 18 AND propertyName = 'ClientStorageAcceleratorPushInstallTime'
                    AND longlongVal > ({self.current_time})
                """

        self.log.info(f"Query: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"Result: {cur}")
        if cur[0] != '1':
            self.log.error("Storage accelerator package auto push install MMEntityProp table entry was not updated")
            raise Exception("Storage accelerator package auto push install MMEntityProp table entry was not updated")
        self.log.info("Storage accelerator package auto push install MMEntityProp table entry was updated")

        query = f""" 
                    SELECT 1
                    FROM TM_CreateTaskRequest WITH(NOLOCK)
                    WHERE xmlValue.value('(/TMMsg_CreateTaskReq/taskInfo/associations/clientId)[1]', 'varchar(max)') 
                    = '{self.client.client_id}' AND 
                    xmlValue.value('(/TMMsg_CreateTaskReq/taskInfo/subTasks/subTask/operationType)[1]', 'varchar(max)')
                    ='INSTALL_CLIENT' AND created > {self.current_time}
                """
        self.log.info(f"Query: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] != '1':
            self.log.error("Storage accelerator package auto push install was not scheduled")
            raise Exception("Storage accelerator package auto push install was not scheduled")
        self.log.info("Storage accelerator package auto push install was scheduled successfully.")

    def _validate_sa_auto_install_enabled(self):
        """
        Validate if storage accelerator auto install feature is enabled on CommCell.
        """
        self.log.info("Validate if storage accelerator auto install feature is enabled on CommCell")
        query = f""" 
                    SELECT value 
                    FROM MMConfigs WITH (NOLOCK)
                    WHERE name = 'MMCONFIG_CONFIG_STORAGE_ACCELERATOR_PUSH_INSTALL_ENABLED'"""
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] != '1':
            self.log.error("Storage Accelerator auto install is disabled on the CommCell.")
            raise Exception("Storage Accelerator auto install is disabled on the CommCell")
        self.log.info("Storage Accelerator auto install is enabled on CommCell")

    def _reset_mmentity_prop(self):
        """
        Updates the mmentity prop val to 10 days before if entry exists
        """
        self.log.info("Updating the mmentity prop val to 10 days before if entry exists")
        query = f"""UPDATE E
                    SET longlongVal = {self.current_time - 864000},
                    modified = {self.current_time - 864000}
                    FROM MMEntityProp E
                    WHERE E.EntityId = {self.client.client_id}
                    AND E.EntityType = 18
                    AND E.propertyName = 'ClientStorageAcceleratorPushInstallTime'
                    AND E.propDataType = 1"""
        self.log.info("QUERY: %s", query)
        sql_password = commonutils.get_cvadmin_password(self.commcell)
        self.mmhelper.execute_update_query(query, sql_password, "sqladmin_cv")

    def _validate_sa_package(self):
        """
        Validate if client had storage accelerator package installed
        """
        self.log.info("Validating if the client has storage accelerator package installed")
        query = f""" select count(1) from simInstalledPackages where simPackageID IN  (54, 1305)
                    and ClientId = {self.client.client_id} """
        self.log.info(f"Query: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"Result: {cur}")
        if cur[0] == '0':
            self.log.info(f"Client {self.client.name} doesn't have storage accelerator package installed.")
            return False
        self.log.info(f"Client {self.client.name} has storage accelerator package installed.")
        return True

    def _validate_ma_package(self):
        """
        Validate if client has media agent package installed or not.
        """
        self.log.info("Validating if client has MediaAgent package installed")
        query = f""" select count(1) from simInstalledPackages where simPackageID IN (51, 1301)
                        and ClientId = {self.client.client_id}"""
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info(f"RESULT: {cur}")
        if cur[0] == '0':
            self.log.info(f"Client {self.client.name} doesn't have MediaAgent package installed on it.")
            return False
        self.log.info (f"Client {self.client.name} has MediaAgent package on it.")
        return True

    def _cleanup(self):
        """cleanup the entities created"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Deleting Content Path
            self.log.info("Deleting content path: %s if exists", self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted content path: %s", self.content_path)

            # Deleting Backupsets
            self.log.info("Deleting BackupSet if exists")
            if self._agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("BackupSet[%s] exists, deleting that", self.backupset_name)
                self._agent.backupsets.delete(self.backupset_name)

            # Deleting Storage Policies
            self.log.info("Deleting Storage Policy if exists")
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Storage Policy[%s] exists, deleting that", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            # Deleting Libraries
            if not self.tcinputs.get("CloudLibraryName"):
                self.log.info(f"Deleting library {self.cloud_library_name}")
                if self.commcell.disk_libraries.has_library(self.cloud_library_name):
                    self.log.info("Library[%s] exists, deleting that", self.cloud_library_name)
                    self.commcell.disk_libraries.delete(self.cloud_library_name)
                    self.log.info(f"{self.cloud_library_name} deleted successfully!")

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception(
                "Error encountered during cleanup: {0}".format(str(exp)))
        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        options_selector = OptionsSelector(self.commcell)
        self.cloud_library_name = '%s_cloud_library-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                          self.tcinputs['ClientName'])
        self.storage_policy_name = '%s_policy-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                    self.tcinputs['ClientName'])
        self.backupset_name = '%s_bs-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                           self.tcinputs['ClientName'])
        self.client_machine = options_selector.get_machine_object(self.client)
        self.cs_machine = options_selector.get_machine_object(self.commcell.commserv_client)
        self.current_time = int(self.cs_machine.current_time().timestamp())
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        self.job_manager = JobManager(commcell=self.commcell)

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=30 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating content")
        self.log.info('selected drive: %s', client_drive)
        # Content path
        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'TestData')

    def run(self):
        """Main test case logic"""
        try:

            # Validate if storage accelerator auto install is enabled
            self._validate_sa_auto_install_enabled()

            # Cleanup
            self._cleanup()

            # Uninstall SA related packages if present
            if self._validate_sa_package() or self._validate_ma_package():
                self.job_manager.job = self.client.uninstall_software(software_list=['MediaAgent', 'MediaAgent Core'])
                self.job_manager.wait_for_state('completed', time_limit=30)
                if self._validate_sa_package() or self._validate_ma_package():
                    self.log.error(f"Client {self.client.name} still has SA related package installed")
                    raise Exception(f"Client {self.client.name} still has SA related package installed")

            # Creating cloud storage.
            if self.tcinputs.get("CloudLibraryName"):
                self.cloud_library_name = self.tcinputs.get("CloudLibraryName")
                if not self.commcell.disk_libraries.has_library(self.cloud_library_name):
                    raise Exception("Cloud library name provided is invalid!")
                self.cloud_lib_obj = self.commcell.disk_libraries.get(self.cloud_library_name)

            elif (("CloudMountPath" and "CloudUserName" and "CloudPassword" and "CloudServerType" in self.tcinputs) and
                  (self.tcinputs["CloudMountPath"] and self.tcinputs["CloudUserName"]
                   and self.tcinputs["CloudPassword"] and self.tcinputs["CloudServerType"])):
                self.cloud_lib_obj = self.mmhelper.configure_cloud_library(self.cloud_library_name,
                                                                           self.tcinputs['MediaAgentName'],
                                                                           self.tcinputs["CloudMountPath"],
                                                                           self.tcinputs["CloudUserName"],
                                                                           self.tcinputs["CloudPassword"],
                                                                           self.tcinputs["CloudServerType"])
            else:
                raise Exception("No cloud library details provided.")

            # create deduplication enabled storage policy
            self.mmhelper.configure_storage_policy(self.storage_policy_name, self.cloud_library_name,
                                                   self.tcinputs['MediaAgentName'])

            # create backupset
            self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            # create subclient
            sc_obj = self.mmhelper.configure_subclient(self.backupset_name, "%s_SC1" % str(self.id),
                                                       self.storage_policy_name, self.content_path, self.agent)

            # update MMEntityProp entry to more than 7 day before to allow auto install again
            self._reset_mmentity_prop()

            if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 10):
                self.log.error("unable to Generate Data at %s", self.content_path)
                raise Exception("unable to Generate Data at {0}".format(self.content_path))
            self.log.info("Generated Data at %s", self.content_path)

            # Run a Backup and validate storage accelerator functionality with log parsing
            self.common_util.subclient_backup(sc_obj, 'full')

            self._validate_sa_auto_install()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this Case"""
        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment."
                "Please check for failure reason and manually clean up the environment..."
            )
