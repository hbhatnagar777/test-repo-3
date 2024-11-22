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

    access_agent()  --  Access the CIFS / NFS agent

    delete_backupset()  --  Deletes the backupset

    add_backupset() --  Adds a new backupset

    backup_subclient()  --  Backups a subclient

    run_restore_verify()    --  Runs a restore job and verifies the data

"""

"""
Sample JSON for the Testcase

"63385":{
        "AgentName":"Windows/Linux File System",
        "ClientName":"",
        "PlanName":"plan-name",
        "DataAccessNodes": ["DAN-1", "DAN-2"],
        "TestPath": "CIFS / NFS share path",
        ["ImpersonateUser":,
        "ImpersonatePassword":,
        "ImpersonateUser2":,]
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
        self.fshelper = None
        self.subclient_name = None
        self.plan_name = None
        self.admin_console = None
        self.browser = None
        self.impersonate_user = None
        self.impersonate_password = None
        self.fileServers = None
        self.fsSubclient = None
        self.base_path = None
        self.UNC_base_path = None
        self.service = None
        self.fs_agent_adv = None
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

        self.name = """
        Network share : Unconditional Overwrite, 
        Restore ACLs Only, 
        Restore Data Only, 
        Restore Both ACLs and Data"""

        self.fshelper = FSHelper(self)
        self.fshelper.populate_tc_inputs(self, mandatory=False)

        self.subclient_name = "default"
        self.plan_name = self.tcinputs.get("PlanName")
        self.impersonate_user = self.tcinputs.get("ImpersonateUser", None)
        self.impersonate_user2 = self.tcinputs.get("ImpersonateUser2", None)
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
            self.dashboard.click_get_started()

        self.fileServers = FileServers(self.admin_console)
        self.fs_utils = FileServersUtils(self.admin_console)
        self.fs_agent_adv = FsAgentAdvanceOptions(self.admin_console)
        self.fsSubclient = Subclient(self.admin_console)
        self.navigator = self.admin_console.navigator
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

    def backup_subclient(self, backupset_name, backup_type):
        """
        Back ups the default subclient for the specified backupset

        Args:
            backupset_name (str) : Name of the backupset
            backup_type (Backup.BackupType.FULL / INCR / SYNTH) : Type of backup
        Returns:
            None
        """

        job_id = self.fsSubclient.backup_subclient(backupset_name=backupset_name, subclient_name=self.subclient_name,
                                                   backup_type=backup_type)
        job_obj = self.commcell.job_controller.get(int(job_id))

        self.log.info(f"Backup job {job_id} has started. Waiting for job completion")

        if not job_obj.wait_for_completion():
            raise Exception(f"Backup Job {job_id} was {job_obj.status}")

        self.log.info(f"Backup Job {job_id} successfully completed")

    def run_restore_verify(self, path, in_place=True, is_cifs_agent=True, data=True, acl=True, overwrite=False,
                           additional_user=False, source_checksum=None):
        """
        Run restore for the subclient from agentDetails page -> subclient restore action button.
        Also Verifies if the data was restored correctly or filters are validated.

        Args:
            path (str) : Share path
            in_place (bool) : True if in-place restore
            is_cifs_agent (bool) : True if CIFS agent
            data (bool) : True to restore data
            acl (bool) : True to restore acl
            overwrite (bool) : True to unconditionally overwrite
            additional_user (bool) : User2 acls to retrieve for base path
            source_checksum (list)(str) : source checksum before modifying data

        Returns:
            None
        Raises Exception if data is not restored correctly / Filter validation failed / Restore job failed.
        """

        destination_checksum = None
        source_acl = destination_acl = None
        proxy_node = None
        rest_path = rest_base = None
        impersonate_user = None
        proxy_node = self.data_access_nodes[0]

        if is_cifs_agent:
            impersonate_user = {
                "username": self.impersonate_user,
                "password": self.impersonate_password
            }
            rest_path = self.client_machine.join_path(path,
                                                      f'{self.id}_tmp_restore')
            self.fshelper.mount_cifs_share_on_drive(self.client_machine,
                                                    path,
                                                    self.impersonate_user,
                                                    self.impersonate_password,
                                                    self.temp_mount_path)

            if not source_checksum:
                source_checksum = self.client_machine.get_checksum_list(self.base_path)
            source_acl = self.client_machine.get_ace(self.impersonate_user, self.base_path)

            if additional_user:
                source_acl.append(
                    self.client_machine.get_ace(self.impersonate_user2, self.base_path)[0]
                )

        else:
            rest_path = self.client_machine.join_path(path,
                                                      f'{self.id}_tmp_restore')
            server, share = path.split(":")
            self.client_machine.mount_nfs_share(self.temp_mount_path, server, share)

            if not source_checksum:
                source_checksum = self.client_machine.get_checksum_list(self.base_path)

            source_acl = str(self.client_machine.nfs4_getfacl(self.base_path))
            source_acl = source_acl.split('\n')[1:]

        rest_job_id = None

        self.log.info("Running a restore job")

        # If data and acl are False then we need to specify atleast one option from cc
        """
        Changing both to true and 
        checking if the acls and data are correct because no data has to be restored when
        unconditional overwrite is not selected.
        """

        if data is False and acl is False:
            data = True
            acl = True

        if in_place:
            rest_job_id = self.fsSubclient.restore_subclient(subclient_name=self.subclient_name,
                                                             backupset_name=self.backupset_name,
                                                             dest_client=proxy_node,
                                                             restore_acl=acl,
                                                             restore_data=data,
                                                             unconditional_overwrite=overwrite,
                                                             selected_files=[self.UNC_base_path],
                                                             impersonate_user=impersonate_user,
                                                             cifs=is_cifs_agent,
                                                             nfs=not is_cifs_agent
                                                             )
        else:
            rest_job_id = self.fsSubclient.restore_subclient(subclient_name=self.subclient_name,
                                                             backupset_name=self.backupset_name,
                                                             dest_client=proxy_node,
                                                             restore_acl=acl,
                                                             restore_data=data,
                                                             destination_path=rest_path,
                                                             unconditional_overwrite=overwrite,
                                                             selected_files=[self.UNC_base_path],
                                                             impersonate_user=impersonate_user,
                                                             cifs=is_cifs_agent,
                                                             nfs=not is_cifs_agent
                                                             )

        rest_job_obj = self.commcell.job_controller.get(int(rest_job_id))

        self.log.info(f"Restore job {rest_job_id} has started. Waiting for completion")

        if not rest_job_obj.wait_for_completion():
            raise Exception(f"Restore Job {rest_job_id} was {rest_job_obj.status}")

        self.log.info(f"Restore job {rest_job_id} has completed")

        if in_place:
            if is_cifs_agent:
                destination_checksum = self.client_machine.get_checksum_list(self.base_path)
                destination_acl = self.client_machine.get_ace(self.impersonate_user, self.base_path)
                if additional_user:
                    destination_acl.append(
                        self.client_machine.get_ace(self.impersonate_user2, self.base_path)[0]
                    )
            else:
                destination_checksum = self.client_machine.get_checksum_list(self.base_path)
                destination_acl = str(self.client_machine.nfs4_getfacl(self.base_path))
                destination_acl = destination_acl.split('\n')[1:]
        else:
            rest_base = self.client_machine.join_path(self.temp_mount_path,
                                                      f'{self.id}_tmp_restore',
                                                      f'{self.id}')
            destination_checksum = self.client_machine.get_checksum_list(rest_base)

            if is_cifs_agent:
                destination_acl = self.client_machine.get_ace(self.impersonate_user, rest_base)
            else:
                destination_acl = str(self.client_machine.nfs4_getfacl(rest_base))
                destination_acl = destination_acl.split('\n')[1:]

        if self.fshelper.compare_lists(source_checksum, destination_checksum):
            self.log.info("Checksum comparision successful")
        else:
            if data:
                raise Exception("Checksum comparision failed")
            else:
                self.log.info("[EXPECTED] All the data was not restored.")

        if self.fshelper.compare_lists(source_acl, destination_acl):
            self.log.info("ACL comparision successful")
        else:
            if acl:
                raise Exception("ACL comparision failed")
            else:
                self.log.info("[EXPECTED] ACL's were not restored")

        self.log.info("Sleeping for 30 seconds after verfying data")
        sleep(30)

        if not in_place:
            # TC fails removing this directory hence adding sleep
            self.log.info("Sleeping for 120 seconds before removing the directory")

            sleep(120)
            self.log.info("Removing temporary directory used for out-of-place restore")

            self.client_machine.remove_directory(self.client_machine.join_path(self.temp_mount_path,
                                                                               f'{self.id}_tmp_restore'))

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

            if "windows" in self.client_machine.os_info.lower():
                is_cifs_agent = True
                self.temp_mount_path = "Z:"

                self.fshelper.generate_data_on_share(self.client_machine,
                                                     self.test_path,
                                                     self.temp_mount_path,
                                                     self.impersonate_user,
                                                     self.impersonate_password)
            else:
                self.temp_mount_path = self.client_machine.join_path('/', f'_{self.id}')
                server, share = self.test_path.split(":")

                if self.client_machine.check_directory_exists(self.temp_mount_path):
                    if self.client_machine.is_path_mounted(self.temp_mount_path):
                        self.client_machine.unmount_path(self.temp_mount_path)
                else:
                    self.client_machine.create_directory(self.temp_mount_path, force_create=True)

                self.fshelper.generate_data_on_share(self.client_machine,
                                                     self.test_path,
                                                     self.temp_mount_path)

            self.base_path = self.client_machine.join_path(self.temp_mount_path, f'{self.id}')

            self.UNC_base_path = self.client_machine.join_path(
                self.test_path, f'{self.id}')

            self.access_agent(is_cifs_agent)

            self.add_backupset(self.backupset_name,
                               self.plan_name,
                               [self.UNC_base_path],
                               is_cifs_agent,
                               True)

            self.backup_subclient(self.backupset_name, Backup.BackupType.FULL)

            self.admin_console.refresh_page()

            self.log.info("Restore both data and acls")

            self.run_restore_verify(self.test_path,
                                    in_place=False,
                                    is_cifs_agent=is_cifs_agent,
                                    data=True,
                                    acl=True)

            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()

            self.log.info("Restore Out-of-place data only")

            self.run_restore_verify(self.test_path,
                                    in_place=False,
                                    is_cifs_agent=is_cifs_agent,
                                    data=True,
                                    acl=False)

            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()

            self.log.info("Restore Out-of-place acl only")

            self.run_restore_verify(self.test_path,
                                    in_place=False,
                                    is_cifs_agent=is_cifs_agent,
                                    data=False,
                                    acl=True)

            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()

            self.log.info("Modifying test data")

            if is_cifs_agent:
                self.fshelper.mount_cifs_share_on_drive(self.client_machine,
                                                        self.test_path,
                                                        self.impersonate_user,
                                                        self.impersonate_password,
                                                        self.temp_mount_path)

                prev_checksum = self.client_machine.get_checksum_list(self.base_path)

                self.client_machine.modify_test_data(self.base_path,
                                                     modify=True)

                self.client_machine.modify_ace(
                    self.impersonate_user2,
                    self.base_path,
                    'Read',
                    'Allow')

                self.fshelper.unmount_network_drive(self.client_machine,
                                                    self.temp_mount_path)

            else:
                self.client_machine.mount_nfs_share(self.temp_mount_path,
                                                    server, share)

                prev_checksum = self.client_machine.get_checksum_list(self.base_path)

                self.client_machine.modify_test_data(self.base_path,
                                                     modify=True)

                self.client_machine.nfs4_setfacl(object_path=self.base_path,
                                                 ace_type='A',
                                                 ace_principal='1005',
                                                 ace_permissions='r')
                self.client_machine.unmount_path(self.temp_mount_path)

            self.log.info("Unconditionally Restore In-Place and Verify")

            self.run_restore_verify(self.test_path,
                                    is_cifs_agent=is_cifs_agent,
                                    overwrite=True,
                                    source_checksum=prev_checksum,
                                    data=True,
                                    acl=False,
                                    additional_user=True)

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
