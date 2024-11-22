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

    login_to_commandcenter()    --  Logins to the command center

    access_agent()  --  Access the CIFS / NFS agent page

    delete_backupset()  -- Delete the backupset

    add_backupset() -- Adds a new backupset

    wait_for_job_completion()   --  Waits for the completion of a job

    backup_subclient()  -- Backups a subclient

    run_restore_verify()    -- Restores from a subclient and verifies the data restored

    generate_or_modify_data()   -- Generates / modifies the data on the share
"""

"""
Sample JSON for the Testcase

"63386":{
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
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils
import base64
from Web.AdminConsole.Components.panel import Backup
from time import sleep
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.config import get_config


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.navigator = None
        self.fs_agent_adv = None
        self.fs_common_Helper = None
        self.fshelper = None
        self.subclient_name = None
        self.plan_name = None
        self.admin_console = None
        self.browser = None
        self.impersonate_user = None
        self.impersonate_password = None
        self.fileServers = None
        self.deleted_items_checksum = None
        self.service = None
        self.base_path = None
        self.UNC_base_path = None
        self.file3_checksums = None
        self.fsSubclient = None
        self.file3_job2_checksum = None
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

        self.name = "Network Share : Browse and Restore: Deleted items, All versions, Point in Time"
        self.fshelper = FSHelper(self)
        self.fshelper.populate_tc_inputs(self, mandatory=False)
        self.subclient_name = "default"
        self.plan_name = self.tcinputs.get("PlanName")
        self.impersonate_user = self.tcinputs.get("ImpersonateUser")
        self.is_metallic = self.tcinputs.get("IsMetallic").lower() == "true"
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
        self.fsSubclient = Subclient(self.admin_console)
        self.fs_common_Helper = FileServersUtils(self.admin_console)
        self.fs_agent_adv = FsAgentAdvanceOptions(self.admin_console)

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
        if self.fsSubclient.is_backupset_exists(backupset_name):
            self.log.info(f"Deleting backupset: {backupset_name}")
            self.fsSubclient.delete_backup_set(backupset_name)
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

        self.RFs_agent_details.add_backupset(
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

        job_id = self.fsSubclient.backup_subclient(backupset_name=backupset_name, subclient_name=self.subclient_name,
                                                   backup_type=backup_type)

        self.wait_for_job_completion(job_id)

        return job_id

    def run_restore_verify(self, path, in_place=True, is_cifs_agent=True, deleted_items=False,
                           restore_all_vers=False, point_in_time=False, job_id=None):
        """
        Run restore for the subclient from agentDetails page -> subclient restore action button.
        Also Verifies if the data was restored correctly.

        Args:
            path (str) : Share path
            in_place (bool) : True if in-place restore
                default : True
            is_cifs_agent (bool) : True if CIFS agent
                default : True
            deleted_items (bool) : True to replace deleted items test[0..2]
                default : False
            restore_all_vers (bool) : True to restore all versions of test3
                default : False
            point_in_time (bool) : True to restore point in time for job2
                default : False
            job_id (str) : Job id if point_in_time restore is selected

        Returns:
            None
        Raises Exception if data is not restored correctly / Restore job failed.
        """

        source_checksum = []
        destination_checksum = []
        proxy_node = None
        UNC_rest_path = None
        rest_path = None
        selected_files = None
        impersonate_user = None
        UNC_base_path = None
        file_system = None
        exp_msg = ""

        proxy_node = self.data_access_nodes[0]

        if not in_place:
            UNC_rest_path = self.client_machine.join_path(path,
                                                          f'{self.id}_tmp_restore')

            rest_path = self.client_machine.join_path(self.temp_mount_path,
                                                      f'{self.id}_tmp_restore')

        if is_cifs_agent:

            file_system = "Windows"
            UNC_base_path = self.UNC_base_path
            impersonate_user = {
                "username": self.impersonate_user,
                "password": self.impersonate_password
            }

            selected_files = []

            self.fshelper.mount_cifs_share_on_drive(self.client_machine,
                                                    path,
                                                    self.impersonate_user,
                                                    self.impersonate_password,
                                                    self.temp_mount_path)
        else:

            file_system = "Unix"
            UNC_base_path = "/" + self.UNC_base_path.replace(":", "")
            server, share = path.split(":")

            self.client_machine.mount_nfs_share(self.temp_mount_path, server, share)

        rest_job_id = None

        if self.client_machine.check_directory_exists(rest_path):
            self.client_machine.remove_directory(rest_path)

        if deleted_items:
            exp_msg = "Deleted items"

            rest_job_id = self.fsSubclient.restore_subclient(subclient_name=self.subclient_name,
                                                             backupset_name=self.backupset_name,
                                                             dest_client=proxy_node,
                                                             show_deleted_items=True,
                                                             deleted_items_path=[UNC_base_path],
                                                             impersonate_user=impersonate_user,
                                                             cifs=is_cifs_agent,
                                                             nfs=not is_cifs_agent
                                                             )

            self.wait_for_job_completion(rest_job_id)

            source_checksum = self.deleted_items_checksum

            for file_num in range(3):
                destination_checksum.append(
                    self.client_machine.get_checksum_list(
                        self.client_machine.join_path(self.base_path,
                                                      f'test{file_num}')
                    )[0]
                )

        elif restore_all_vers:
            exp_msg = "All versions"

            selected_files = self.client_machine.join_path(
                UNC_base_path, 'test3')

            rest_job_id = self.fsSubclient.restore_subclient(subclient_name=self.subclient_name,
                                                             backupset_name=self.backupset_name,
                                                             modified_file=selected_files,
                                                             dest_client=proxy_node,
                                                             version_nums=['1', '2', '3'],
                                                             destination_path=UNC_rest_path,
                                                             impersonate_user=impersonate_user,
                                                             cifs=is_cifs_agent,
                                                             nfs=not is_cifs_agent
                                                             )
            self.wait_for_job_completion(rest_job_id)

            source_checksum = self.file3_checksums

            destination_checksum = self.client_machine.get_checksum_list(rest_path)

        elif point_in_time:
            exp_msg = "Point in time"

            selected_files = self.client_machine.join_path(
                UNC_base_path, 'test3'
            )

            rest_job_id = self.fsSubclient.restore_subclient_by_job(self.backupset_name,
                                                                    self.subclient_name,
                                                                    job_id,
                                                                    proxy_node,
                                                                    restore_path=UNC_rest_path,
                                                                    selected_files=[selected_files],
                                                                    cifs=is_cifs_agent,
                                                                    impersonate_user=impersonate_user,
                                                                    nfs=not is_cifs_agent)

            self.wait_for_job_completion(rest_job_id)

            source_checksum = self.file3_job2_checksum

            destination_checksum = self.client_machine.get_checksum_list(rest_path)

        if not self.fshelper.compare_lists(source_checksum, destination_checksum, True):
            raise Exception(f"{exp_msg} not restored correctly")
        else:
            self.log.info("Checksum comparision successfull")

        if not in_place:
            self.log.info("Removing the temporary directory for Out-of-place restore")
            self.client_machine.remove_directory(rest_path)

        if is_cifs_agent:
            self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)
        else:
            self.client_machine.unmount_path(self.temp_mount_path)

    def generate_or_modify_data(self, path, is_cifs_agent=True,
                                scenario_num=1):

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

        base_path = self.client_machine.join_path(self.temp_mount_path, f'{self.id}')
        file_path = self.client_machine.join_path(base_path, 'test')

        if scenario_num == 1:
            self.log.info(f"Creating directory: {base_path}")
            self.client_machine.create_directory(base_path, force_create=True)

            self.log.info("Creating files test[0..9]")

            for file_num in range(10):
                content = f"This is file {file_num}"
                self.client_machine.create_file(file_path + f'{file_num}', content)

                if file_num in range(4):
                    if file_num == 3:
                        self.file3_checksums.append(
                            self.client_machine.get_checksum_list(
                                file_path + f'{file_num}'
                            )[0]
                        )
                    else:
                        self.deleted_items_checksum.append(
                            self.client_machine.get_checksum_list(
                                file_path + f'{file_num}'
                            )[0]
                        )

        elif scenario_num == 2:

            self.log.info("Modifying test3 file")
            self.client_machine.append_to_file(file_path + '3', "1st Modified file3")

            self.file3_job2_checksum.append(
                self.client_machine.get_checksum_list(file_path + '3')[0]
            )

            self.file3_checksums.append(
                self.file3_job2_checksum[-1]
            )

            self.log.info("Deleting test[0..2] files")
            for file_num in range(3):
                self.client_machine.delete_file(file_path + f'{file_num}')

        elif scenario_num == 3:
            self.log.info("Adding test[10..11] files")

            for file_num in range(10, 12):
                content = f"This is file {file_num}"
                self.client_machine.create_file(file_path + f'{file_num}', content)

            self.log.info("Modifying test3 file again")
            self.client_machine.append_to_file(file_path + '3', "2nd Modified file3")

            self.file3_checksums.append(
                self.client_machine.get_checksum_list(file_path + '3')[0]
            )

        if is_cifs_agent:
            self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)
        else:
            self.client_machine.unmount_path(self.temp_mount_path)

    def run(self):
        is_cifs_agent = False
        try:

            self.login_to_commandcenter()

            self.RFs_agent_details = FsAgentAdvanceOptions(self.admin_console)

            self.log.info("*" * 10)
            self.log.info(f"Started executing testcase")

            self.deleted_items_checksum = []
            self.file3_checksums = []
            self.file3_job2_checksum = []

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

            self.generate_or_modify_data(self.test_path,
                                         is_cifs_agent)

            self.backup_subclient(self.backupset_name, Backup.BackupType.FULL)

            self.generate_or_modify_data(self.test_path,
                                         is_cifs_agent,
                                         scenario_num=2)

            job2 = self.backup_subclient(self.backupset_name)

            self.generate_or_modify_data(self.test_path,
                                         is_cifs_agent,
                                         scenario_num=3)

            self.backup_subclient(self.backupset_name)

            self.admin_console.refresh_page()

            self.log.info("Restore deleted items inplace")

            self.run_restore_verify(self.test_path,
                                    is_cifs_agent=is_cifs_agent,
                                    deleted_items=True
                                    )

            self.admin_console.driver.back()
            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()

            self.admin_console.access_tab("Subclients")

            self.log.info("Restore all versions Out-of-place")

            self.run_restore_verify(self.test_path,
                                    in_place=False,
                                    restore_all_vers=True,
                                    is_cifs_agent=is_cifs_agent
                                    )

            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()

            self.log.info("Point in time restore for Job2")

            self.run_restore_verify(self.test_path,
                                    in_place=False,
                                    is_cifs_agent=is_cifs_agent,
                                    point_in_time=True,
                                    job_id=job2
                                    )

            self.access_agent(is_cifs_agent)
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
