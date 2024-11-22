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

    login_to_commandcenter()    -- Logins to the command center

    access_agent()  --  Access the CIFS / NFS agent

    delete_backupset()  --  Deletes the backupset

    add_backupset() --  Adds a new backupset

    wait_for_job_completion() -- Waits for the completion of a job

    backup_subclient()  --  Backups a subclient

    generate_data() --  Generates data on the share

    return_checksum()   -- Returns the checksum of the path

    find_and_restore_files()    --  Finds and restores the files from Agent details page

"""

"""
Sample JSON for the Testcase

"63387":{
        "AgentName":"Windows/Linux File System",
        "ClientName":"",
        "PlanName":"plan-name",
        "DataAccessNodes": ["DAN-1", "DAN-2"],
        "TestPath": "CIFS / NFS share path",
        ["ImpersonateUser":,
        "ImpersonatePassword":,]
        "IsMetallic":
    }

Note: The inputs mentioned in [] are required only for Windows File System agent
"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient, FsAgentAdvanceOptions
import base64
from Web.AdminConsole.Components.panel import Backup
from time import sleep
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.config import get_config
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.fshelper = None
        self.subclient_name = None
        self.plan_name = None
        self.admin_console = None
        self.browser = None
        self.impersonate_user = None
        self.impersonate_password = None
        self.service = None
        self.base_path = None
        self.UNC_base_path = None
        self.temp_mount_path = None
        self.backupset_name = None
        self.dashboard = None
        self.config = get_config()
        self.tcinputs = {
            "TestPath": None,
            "AgentName": None,
            "ClientName": None,
            "DataAccessNodes": None,
            "PlanName": None,
            "IsMetallic": None
        }

    def setup(self):
        """Setup function of the testcase
        Initializing Pre-requisites for this testcase """

        self.name = "READ - Network Share : Data Protection - Full,Incremental,Find and Restore"
        self.fshelper = FSHelper(self)
        self.fshelper.populate_tc_inputs(self, mandatory=False)
        self.subclient_name = "default"
        self.plan_name = self.tcinputs.get("PlanName")
        self.is_metallic = self.tcinputs.get("IsMetallic").lower() == "true"
        self.impersonate_user = self.tcinputs.get("ImpersonateUser")
        self.impersonate_password = self.tcinputs.get("ImpersonatePassword", None)
        if self.impersonate_password:
            self.impersonate_password = str(base64.b64decode(self.tcinputs.get("ImpersonatePassword")), 'utf-8')
        self.backupset_name = f"AUTO_BKPSET_{self.id}"

    def login_to_commandcenter(self):
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

        self.fileServers = FileServers(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.agent_advanceoptions = FsAgentAdvanceOptions(self.admin_console)
        self.agent_subclient = Subclient(self.admin_console)
        self.fs_common_Helper = FileServersUtils(self.admin_console)

    def access_agent(self, is_cifs_agent=True):

        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")

        self.fileServers.access_server(self.client_name)

        if is_cifs_agent:
            self.fs_common_Helper.access_protocol("CIFS")
        else:
            self.fs_common_Helper.access_protocol("NFS")
        self.admin_console.access_tab("Subclients")

    def delete_backupset(self, backupset_name):
        """
        Deletes the backupset
        Args:
            backupset_name (str) : Name of the backupset
        Returns:
            None
        Raises:
            Exception if backupset not found
        """
        if self.agent_subclient.is_backupset_exists(backupset_name):
            self.log.info(f"Deleting backupset: {backupset_name}")
            self.agent_subclient.delete_backup_set(backupset_name)
        self.admin_console.wait_for_completion()
        sleep(20)

    def add_backupset(self, backupset_name, plan, backup_data, is_cifs_agent=True, force_create=False):
        """
        Adds a backupset from fsAgent page

        Args:
            backupset_name (str): Name of the backupset
            plan (str): Name of the plan
            backup_data (list): Data to be backed up
            is_cifs_agent (bool): True if the agent is CIFS Agent
            force_create (bool): Delete existing backupset and create a new one
        Returns:
            None
        Raises:
            Exception if error creating backupset
        """

        impersonate_user = None

        if force_create:
            self.log.info("Force Create Option passed. Deleting existing one and creating new backupset")
            self.delete_backupset(backupset_name)

        if is_cifs_agent:
            impersonate_user = {
                "username": self.impersonate_user,
                "password": self.impersonate_password
            }

        self.log.info("Creating a new backupset : {self.backupset_name}")
        self.agent_advanceoptions.add_backupset(
                                            backupset_name=backupset_name,
                                            plan_name=plan,
                                            content=backup_data,
                                            impersonate_user=impersonate_user,
                                            is_nas_backupset=True,
                                            exclusions=[],
                                            exceptions=[]
                                            )

    def wait_for_job_completion(self, job_id):
        """
        Waits for job completion
        Args:
            job_id (str): Job id
        Returns:
            None
        Raises:
            Exception if job was failed
        """

        job_obj = self.commcell.job_controller.get(int(job_id))

        self.log.info(f"{job_obj.job_type} Job {job_id} has started. Waiting for job completion")

        if not job_obj.wait_for_completion():
            raise Exception(f"{job_obj.job_type} Job {job_id} was {job_obj.status}")

        self.log.info(f"{job_obj.job_type} Job {job_id} successfully completed")

    def backup_subclient(self, backupset_name, backup_type=Backup.BackupType.INCR):
        """
        Backups the default subclient for the specified backupset

        Args:
            backupset_name (str) : Name of the backupset
            backup_type (Backup.BackupType.FULL / INCR / SYNTH) : Type of backup
                default: Backup.BackupType.INCR
        Returns:
            job_id
        """

        job_id = self.agent_subclient.backup_subclient(subclient_name=self.subclient_name, backup_type=backup_type,
                                                        backupset_name=backupset_name)

        self.wait_for_job_completion(job_id)

        return job_id

    def generate_data(self, path, is_cifs_agent=True, for_incr=False):
        """
        Generates data on the given path

        Args:
            path (str) : Path where the data has to be generated
            is_cifs_agent (bool) : True for cifs agent
            for_incr (bool) : True to generate data for incremental
        Returns:
            None
        """

        if is_cifs_agent:
            self.fshelper.mount_cifs_share_on_drive(self.client_machine,
                                                    path,
                                                    self.impersonate_user,
                                                    self.impersonate_password,
                                                    self.temp_mount_path)
        else:
            server, share = path.split(":")
            self.client_machine.mount_nfs_share(self.temp_mount_path,
                                                server,
                                                share)

        file_ext = ".full"

        if not for_incr:
            self.log.info(f"Creating directory: {self.base_path}")
            self.client_machine.create_directory(self.base_path, force_create=True)
        else:
            file_ext = ".incr"

        for file_num in range(10):
            file_path = self.client_machine.join_path(self.base_path, f'test{file_num}{file_ext}')
            content = f"This is file {file_num}{file_ext}"
            self.client_machine.create_file(file_path, content)

        if is_cifs_agent:
            self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)
        else:
            self.client_machine.unmount_path(self.temp_mount_path)

    def return_checksum(self, file_name, base_path):
        """
        Returns the checksum list of the files

        Args:
            file_name (str) : File name or wildcard
            base_path (str) : Parent directory of the file_name

        Returns:
            None
        """

        checksum_list = []

        if '*' not in file_name:
            checksum_list.append(self.client_machine.get_checksum_list(
                self.client_machine.join_path(base_path,
                                              file_name)
            ))

        else:
            file_ext = file_name[1:]

            for file_num in range(10):
                checksum_list.append(
                    self.client_machine.get_checksum_list(
                        self.client_machine.join_path(base_path,
                                                      f"test{file_num}{file_ext}")
                    )
                )

        return checksum_list

    def find_and_restore_files(self, file_name, is_cifs_agent=True):
        """
        Finds files from the fsagentDetails page and runs a restore job
        Also verifies the data restored

        Args:
            file_name (str) : File name or wildcard to be searched
            is_cifs_agent (bool) : True for CIFS agent, else False
        Returns:
            None
        Raises:
            Exception if files are not restored correctly / Restore job failed
        """

        impersonate_user = None

        source_checksum = []
        destination_checksum = []

        if is_cifs_agent:
            self.fshelper.mount_cifs_share_on_drive(self.client_machine,
                                                    self.test_path,
                                                    self.impersonate_user,
                                                    self.impersonate_password,
                                                    self.temp_mount_path)
            impersonate_user = {
                "username": self.impersonate_user,
                "password": self.impersonate_password
            }
        else:
            server, share = self.test_path.split(":")

            self.client_machine.mount_nfs_share(self.temp_mount_path, server, share)

        source_checksum = self.return_checksum(file_name, self.base_path)

        UNC_rest_path = self.client_machine.join_path(self.test_path,
                                                      f"{self.id}_tmp_restore")

        rest_path = self.client_machine.join_path(self.temp_mount_path,
                                                  f"{self.id}_tmp_restore")

        if self.client_machine.check_directory_exists(rest_path):
            self.client_machine.remove_directory(rest_path)

        self.admin_console.access_tab("Overview")

        self.fs_common_Helper.search_files_for_restore(filename=file_name, backupset_name=self.backupset_name)

        job_id = self.fs_common_Helper.restore(subclient_name=self.subclient_name,
                                               backupset_name=self.backupset_name,
                                               dest_client=self.data_access_nodes[0],
                                               destination_path=UNC_rest_path,
                                               impersonate_user=impersonate_user,
                                               cifs=is_cifs_agent,
                                               nfs=not is_cifs_agent)

        self.wait_for_job_completion(job_id)

        destination_checksum = self.return_checksum(file_name, rest_path)

        if not self.fshelper.compare_lists(source_checksum, destination_checksum, True):
            raise Exception("Data not restored correctly")
        else:
            self.log.info("Data is restored correctly")

        self.log.info("Removing the temporary directory for Out-of-place restore")
        self.client_machine.remove_directory(rest_path)

        if is_cifs_agent:
            self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)
        else:
            self.client_machine.unmount_path(self.temp_mount_path)

    def run(self):
        is_cifs_agent = False
        try:

            self.login_to_commandcenter()

            self.log.info("*" * 10)
            self.log.info(f"Started executing testcase")

            if "windows" in self.client_machine.os_info.lower():
                is_cifs_agent = True
                self.temp_mount_path = "Z:"

            else:
                self.temp_mount_path = self.client_machine.join_path('/', f'_{self.id}')
                server, share = self.test_path.split(":")

                if self.client_machine.check_directory_exists(self.temp_mount_path):
                    if self.client_machine.is_path_mounted(self.temp_mount_path):
                        self.client_machine.unmount_path(self.temp_mount_path)
                else:
                    self.client_machine.create_directory(self.temp_mount_path, force_create=True)

            self.base_path = self.client_machine.join_path(self.temp_mount_path, f'{self.id}')

            self.UNC_base_path = self.client_machine.join_path(
                self.test_path, f'{self.id}')

            self.access_agent(is_cifs_agent)

            self.add_backupset(self.backupset_name,
                               self.plan_name,
                               [self.UNC_base_path],
                               is_cifs_agent,
                               True)

            self.generate_data(self.test_path, is_cifs_agent=is_cifs_agent)
            self.backup_subclient(self.backupset_name, Backup.BackupType.FULL)

            self.find_and_restore_files("test1.full", is_cifs_agent)

            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()
            self.generate_data(self.test_path, is_cifs_agent=is_cifs_agent, for_incr=True)

            self.admin_console.access_tab("Subclients")

            self.backup_subclient(self.backupset_name)

            self.find_and_restore_files("*.incr", is_cifs_agent)

            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()

            self.admin_console.access_tab("Subclients")

            self.backup_subclient(self.backupset_name, Backup.BackupType.SYNTH)

            self.find_and_restore_files("*.full", is_cifs_agent)

            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()

            self.admin_console.access_tab("Subclients")

            self.delete_backupset(self.backupset_name)

            self.log.info("Deleting the content created for the testcase")

            if is_cifs_agent:
                self.fshelper.mount_cifs_share_on_drive(self.client_machine,
                                                        self.test_path,
                                                        self.impersonate_user,
                                                        self.impersonate_password,
                                                        self.temp_mount_path)

                self.client_machine.remove_directory(self.base_path)

                self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)
            else:
                self.client_machine.mount_nfs_share(self.temp_mount_path,
                                                    server,
                                                    share)
                self.client_machine.remove_directory(self.base_path)
                self.client_machine.unmount_path(self.temp_mount_path)
                self.client_machine.remove_directory(self.temp_mount_path)

            self.log.info("Testcase executed successfully")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            if is_cifs_agent:
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
