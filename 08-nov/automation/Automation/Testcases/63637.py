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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    login_to_command_center()   -- logins to the command center

    create_nas_client() --  creates a nas client

    wait_for_job_completion()   -- waits for backup / restore job completion

    access_agent_and_backup()   -- backup from fssubclient class

    backup_subclient()  -- backups from file servers page

    restore_subclient() -- restore from file servers page

    mount_and_generate_data()   -- mounts share and generates test data

    verify_subclient_properties()   -- Verifies default subclient properties

"""

"""
"63637":{
        "ClientName": "",
        "AgentName": "Windows / Linux File System",
        "DataAccessNodes": [dan-1, dan-2],
        "TestPath": None,
        "PlanName": None,
        "IsMetallic": None
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers as RFileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils

from Web.AdminConsole.Helper.nas_helper import Nashelper
import base64
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from time import sleep
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.config import get_config


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.fshelper = None
        self.admin_console = None
        self.browser = None
        self.impersonate_user = None
        self.impersonate_password = None
        self.rfs_fileServers = None
        self.is_cifs_agent = None
        self.service = None
        self.fsSubclient = None
        self.rfsSubclient = None
        self.fsUtils = None
        self.nasHelper = None
        self.dashboard = None
        self.base_path = None
        self.UNC_base_path = None
        self.temp_mount_path = None
        self.is_metallic = None
        self.config = get_config()
        self.tcinputs = {
            "AgentName": None,
            "DataAccessNodes": None,
            "TestPath": None,
            "PlanName": None,
            "IsMetallic": None
        }

    def setup(self):
        """Setup function of the testcase
        Initializing Pre-requisites for this testcase """

        self.fshelper = FSHelper(self)
        self.name = "Create, Retire and Delete NAS clients from Command Center"
        self.fshelper.populate_tc_inputs(self, mandatory=False)
        self.plan_name = self.tcinputs.get("PlanName")
        self.impersonate_user = self.tcinputs.get("ImpersonateUser", None)
        self.impersonate_password = self.tcinputs.get("ImpersonatePassword", None)

        if self.impersonate_password:
            self.impersonate_password = str(base64.b64decode(self.impersonate_password), 'utf-8')

        self.is_metallic = self.tcinputs.get("IsMetallic").lower() == "true"

    def login_to_command_center(self):
        """
        Logins to the commandcenter
        """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)
        if self.is_metallic:
            from Web.AdminConsole.Hub.dashboard import Dashboard
            from Web.AdminConsole.Hub.constants import HubServices
            self.service = HubServices.file_system
            self.dashboard = Dashboard(self.admin_console, self.service)
            self.dashboard.choose_service_from_dashboard()

        self.table = Rtable(self.admin_console)
        self.rfs_fileServers = RFileServers(self.admin_console)
        self.fsUtils = FileServersUtils(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.fsSubclient = FsSubclient(self.admin_console)
        self.rfsSubclient = Subclient(self.admin_console)
        self.nasHelper = Nashelper(self.admin_console)

    def verify_subclient_properties(self, subclient, access_nodes=None, is_cifs_agent=True):
        """
        Verifies the default subclient properties

        Args:
            subclient (Subclient object) : CVPySDK subclient object
            access_nodes (list) (str)    : List of data access nodes
            is_cifs_agent     (bool)           : True if CIFS agent

        Retuns:
            None
        Raises:
            Exception if any property is not correct
        """

        self.log.info("Checking the subclient properties")

        # Using mulitple if statements to check if any one property is incorrect

        subclient.refresh()

        # Using local var to reduce mutliple requests
        subclient_props = subclient.properties

        if access_nodes is not None:

            curr_dan = []

            backup_config = ""

            if "backupConfigurationIDA" in subclient_props["fsSubClientProp"]:
                backup_config = "backupConfigurationIDA"

            elif "backupConfiguration" in subclient_props["fsSubClientProp"]:
                backup_config = "backupConfiguration"

            else:
                raise Exception("Unable to find the data access nodes subclient property")

            for dan in subclient_props["fsSubClientProp"][backup_config]["backupDataAccessNodes"]:
                curr_dan.append(dan["displayName"])

            if self.fshelper.compare_lists(curr_dan, access_nodes, True):
                self.log.info("Data Access Nodes are set correctly")
            else:
                raise Exception("Data Access Nodes are not set correctly")

            if not is_cifs_agent:
                if subclient_props["fsSubClientProp"]["enableNetworkShareAutoMount"]:
                    self.log.info("enableNetworkShareAutoMount is set to True")
                else:
                    raise Exception("enableNetworkShareAutoMount is set to False, this should be True")

                if subclient_props["fsSubClientProp"]["enableFolderLevelMultiThread"]:
                    self.log.info("Folder Level Multi-Threading is enabled")
                else:
                    raise Exception("Folder Level Multi-Threading is not enabled")
        else:
            if subclient_props["fsSubClientProp"]["followMountPointsMode"] == 1:
                self.log.info("Follow mount points is enabled")
            else:
                raise Exception("Follow mount points is not enabled")

        if subclient_props["fsSubClientProp"]["isTrueUpOptionEnabledForFS"]:
            self.log.info("TrueUp Option is enabled")
        else:
            raise Exception("TrueUp is not enabled")

        if subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"] == 30:
            self.log.info("TrueUp days is set to 30")
        else:
            raise Exception(
                f'TrueUp days is set to {subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"]} \
                this should be 30 by default')

        if subclient_props["commonProperties"]["numberOfBackupStreams"] == 0:
            self.log.info("Optimal data readers are set")
        else:
            raise Exception("Optimal Data Readers are not set")

        if subclient_props["commonProperties"]["allowMultipleDataReaders"]:
            self.log.info("Allow multiple readers is set to True")
        else:
            raise Exception("Multiple data readers are not set")

        self.log.info("Successfully verfied the subclient properties")

    def create_nas_client(self, client_name):
        """
        Creates a NAS client from FileServers page
        Args:
            ClientName (str) : Name of the client
        """
        self.log.info(f"Creating NAS Client:{client_name}")

        if self.is_cifs_agent:
            self.rfs_fileServers.add_nas_client(client_name,
                                               client_name,
                                               self.plan_name,
                                               cifs={
                                                   'access_nodes': self.data_access_nodes,
                                                   'impersonate_user':
                                                       {
                                                           'username': self.impersonate_user,
                                                           'password': self.impersonate_password
                                                       },
                                                   'client_level_content': self.UNC_base_path
                                               })
        else:
            self.rfs_fileServers.add_nas_client(client_name,
                                               client_name,
                                               self.plan_name,
                                               nfs={
                                                   'access_nodes': self.data_access_nodes,
                                                   'client_level_content': [self.UNC_base_path]
                                               })

        # Sleeping for 20 seconds to load page
        sleep(20)
        self.log.info(f"Successfully created the NAS client: {client_name}")

        self.log.info("Checking default subclient properties")

        self.commcell.clients.refresh()
        self.client = self.commcell.clients.get(client_name)
        self.client_name = self.client.display_name

        if self.is_cifs_agent:
            self.agent = self.client.agents.get("windows file system")
        else:
            self.agent = self.client.agents.get("linux file system")

        backupset_obj = self.agent.backupsets.get('defaultBackupSet')
        subclient_obj = backupset_obj.subclients.get('default')

        self.verify_subclient_properties(subclient_obj,
                                        self.data_access_nodes,
                                        self.is_cifs_agent)

    def wait_for_job_completion(self, job_id):
        """
        Waits for completion of a backup / restore job.

        Args:
            job_id (str): Job id
        Returns:
            None
        Raises:
            Exception: If the job failed
        """

        job_obj = self.commcell.job_controller.get(int(job_id))

        if not job_obj.wait_for_completion():
            raise Exception(f"{job_obj.job_type} job {job_id} was {job_obj.status}")
        else:
            self.log.info(f"{job_obj.job_type} job {job_id} completed successfully!")

    def access_agent_and_backup(self):
        """
        Access the agent details page and backup default subclient of default Backupset.
        Also waits for completion of the backup

        Args:
            None
        Returns:
            None
        Raise Exception if accessing the subclient Details page
        """

        self.rfs_fileServers.access_server(self.client_name)

        if self.is_cifs_agent:
            self.fsUtils.access_protocol("CIFS")
        else:
            self.fsUtils.access_protocol("NFS")

        self.admin_console.wait_for_completion()

        self.admin_console.access_tab("Subclients")

        self.log.info("Backing up default subclient of the defaultBackupSet")

        job_id = self.rfsSubclient.backup_subclient(backupset_name='defaultBackupSet', subclient_name='default', backup_type=Backup.BackupType.FULL)
        self.wait_for_job_completion(job_id)

    def backup_subclient(self):
        """
        Backup the default subclient of default BackupSet for CIFS and NFS agents.

        Args:
            None
        Returns:
            None
        Raises Exception if the restore job fails
        """

        agent = "NFS"
        if self.is_cifs_agent:
            agent = "CIFS"

        job_id = self.rfs_fileServers.backup_subclient(client_name=self.client_name,
                                                   backup_level=Backup.BackupType.FULL,
                                                   agent=agent)

        self.wait_for_job_completion(job_id)

    def restore_subclient(self):
        """
        Unconditional Overwrite and In place Restore of the default subclient for CIFS and NFS agents.
        And verifies if the data is restored correctly.

        Args:
            None
        Returns:
            None
        Raises Exception if the restore job fails
        """

        self.admin_console.refresh_page()

        if self.is_cifs_agent:
            self.fshelper.mount_cifs_share_on_drive(self.client_machine,
                                                    self.test_path,
                                                    self.impersonate_user,
                                                    self.impersonate_password,
                                                    self.temp_mount_path)

            source_checksum = self.client_machine.get_checksum_list(self.base_path)

            job_id = self.rfs_fileServers.restore_subclient(client_name=self.client_name,
                                                        dest_client=self.data_access_nodes[0],
                                                        unconditional_overwrite=True,
                                                        selected_files=[self.UNC_base_path[2:]],
                                                        impersonate_user={
                                                            "username": self.impersonate_user,
                                                            "password": self.impersonate_password
                                                        },
                                                        agent="CIFS",
                                                        cifs=self.is_cifs_agent,
                                                        nfs=not self.is_cifs_agent,
                                                        nas=True)
        else:
            server, share = self.test_path.split(":")
            self.client_machine.mount_nfs_share(self.temp_mount_path, server, share)
            source_checksum = self.client_machine.get_checksum_list(self.base_path)

            job_id = self.rfs_fileServers.restore_subclient(client_name=self.client_name,
                                                        dest_client=self.data_access_nodes[0],
                                                        unconditional_overwrite=True,
                                                        selected_files=[self.UNC_base_path],
                                                        agent="NFS",
                                                        cifs=self.is_cifs_agent,
                                                        nfs=not self.is_cifs_agent,
                                                        nas=True)

        self.wait_for_job_completion(job_id)

        self.log.info("Comparing checksum for the restore jobs")

        dest_checksum = self.client_machine.get_checksum_list(self.base_path)

        if self.is_cifs_agent:
            self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)
        else:
            self.client_machine.unmount_path(self.temp_mount_path)

        if (self.fshelper.compare_lists(source_checksum, dest_checksum)):
            self.log.info("Checksum comparision successful")

    def mount_and_generate_data(self):
        """
        Mounts the share and generates data

        Args:
            None : Uses self.test_path to generate data on cifs share
                Uses self.test_path2 to generate data on nfs share
        Returns:
            None
        Raises Exception if error in generating data on the share.
        """

        if self.is_cifs_agent:
            self.log.info("Generating data on the cifs share")

            self.fshelper.generate_data_on_share(self.client_machine,
                                                self.test_path,
                                                self.temp_mount_path,
                                                self.impersonate_user,
                                                self.impersonate_password)

            self.log.info("Successfully generated data on the cifs share")
        else:
            self.log.info("Generating data on the nfs share")
            self.fshelper.generate_data_on_share(self.client_machine,
                                                self.test_path,
                                                self.temp_mount_path)

            self.log.info("Successfully generated data on the nfs share")
    
    def accesss_file_server_tab(self):
        self.admin_console.access_tab("File servers")
    
    def navigate_to_file_servers(self):
        """
        Navigates to file server page and clicks on File servers tab
        """

        self.navigator.navigate_to_file_servers()
        self.accesss_file_server_tab()

    def run(self):

        try:
            if "windows" in self.client_machine.os_info.lower():
                self.is_cifs_agent = True
                self.temp_mount_path = "Y:"
                auto_client_name = f"AUTOMATION_NAS_CLIENT_{self.id}_CIFS_1"
            else:
                self.is_cifs_agent = False
                self.temp_mount_path = self.client_machine.join_path('/', f'_{self.id}')
                if self.client_machine.check_directory_exists(self.temp_mount_path):
                    if self.client_machine.is_path_mounted(self.temp_mount_path):
                        self.client_machine.unmount_path(self.temp_mount_path)
                auto_client_name = f"AUTOMATION_NAS_CLIENT_{self.id}_NFS_1"

            self.base_path = self.client_machine.join_path(self.temp_mount_path, f"{self.id}")
            self.UNC_base_path = self.client_machine.join_path(self.test_path, f"{self.id}")

            self.login_to_command_center()

            self.log.info("Performing the following steps:")
            self.log.info("""
            Create NAS Client
            Retire Client
            Create NAS Client
            Backup default subclient for both the agents
            Retire the client
            Restore in place (unconditional overwrite) the default subclient for both the agents
            Reconfigure the client
            Backup default subclient for both the agents
            Retire the client
            Delete the client
            """)

            self.navigate_to_file_servers()
            if self.rfs_fileServers.is_client_exists(auto_client_name):
                self.log.info("Deleting existing File Server")
                self.nasHelper.validate_retire_and_delete_server(auto_client_name, should_delete_server=True)

            self.log.info("Create NAS Client and retire it")
            self.create_nas_client(auto_client_name)
            self.navigate_to_file_servers()
            self.nasHelper.validate_retire_and_delete_server(self.client_name)

            self.log.info("Create NAS Client -> backup -> retire -> restore -> reconfigure -> backup -> delete")
            if self.is_cifs_agent:
                auto_client_name = f"AUTOMATION_NAS_CLIENT_{self.id}_CIFS_2"
            else:
                auto_client_name = f"AUTOMATION_NAS_CLIENT_{self.id}_NFS_2"

            if self.rfs_fileServers.is_client_exists(auto_client_name):
                self.log.info("Deleting existing File Server")
                self.nasHelper.validate_retire_and_delete_server(auto_client_name, should_delete_server=True)

            self.create_nas_client(auto_client_name)
            self.mount_and_generate_data()
            self.navigate_to_file_servers()
            self.table.reload_data()
            self.access_agent_and_backup()
            self.navigate_to_file_servers()
            self.nasHelper.validate_retire_and_delete_server(self.client_name)
            self.log.info("Sleeping for 1 min after retiring the server")
            sleep(60)
            self.restore_subclient()
            self.log.info(f"Reconfiguring client : {self.client_name}")
            self.navigate_to_file_servers()
            self.rfs_fileServers.reconfigure_server(self.client_name)
            self.log.info(f"Successfully reconfigured the client: {self.client_name}")
            self.admin_console.wait_for_completion()
            self.table.reload_data()
            self.backup_subclient()
            self.nasHelper.validate_retire_and_delete_server(self.client_name, should_delete_server=True)
            self.log.info("Removing the content created for the testcase")
            if self.is_cifs_agent:
                self.fshelper.mount_cifs_share_on_drive(self.client_machine,
                                                        self.test_path,
                                                        self.impersonate_user,
                                                        self.impersonate_password,
                                                        self.temp_mount_path)

                self.client_machine.remove_directory(self.base_path)
            else:
                server, share = self.test_path.split(":")
                self.client_machine.mount_nfs_share(self.temp_mount_path,
                                                    server,
                                                    share)

                self.client_machine.remove_directory(self.base_path)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            if self.is_cifs_agent:
                if self.fshelper.is_drive_mounted(self.client_machine, self.temp_mount_path):
                    self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)
            else:
                if self.client_machine.is_path_mounted(self.temp_mount_path):
                    self.client_machine.unmount_path(self.temp_mount_path)
                if self.client_machine.check_directory_exists(self.temp_mount_path):
                    self.client_machine.remove_directory(self.temp_mount_path)

            self.log.info("Logging out from the command center and and closing the browser")
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
