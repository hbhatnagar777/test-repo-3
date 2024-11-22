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

    delete_subclient()  --  Deletes the subclient

    add_subclient() --  Adds a new subclient

    backup_subclient()  --  Backups a subclient

    run_verify_restore()    --  Runs a restore job and verifies the sparse tag

"""

"""
Sample JSON for the Testcase

"71223":{
        "AgentName":"File System",
        "ClientName":"",
        "PlanName":"plan-name",
        "StoragePolicyName": "StoragePolicyName",
        "TestPath": "Content",
        "IsMetallic":
    }

"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient, FsAgentAdvanceOptions
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils
from AutomationUtils.machine import Machine
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Rtable
from time import sleep
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.config import get_config


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.rest_path = None
        self.RFs_agent_details = None
        self.client_machine = None
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
            "PlanName": None,
            "IsMetallic": None
        }

    def setup(self):
        """Setup function of the testcase
        Initializing Pre-requisites for this testcase """

        self.name = """
        Basic validation for sparse files"""

        self.fshelper = FSHelper(self)
        self.fshelper.populate_tc_inputs(self, mandatory=False)

        self.subclient_name = f"AUTO_SUBCLIENT_{self.id}"
        self.plan_name = self.tcinputs.get("PlanName")
        self.is_metallic = self.tcinputs.get("IsMetallic").lower() == "true"
        self.backupset_name = "defaultBackupSet"
        self.test_path = self.tcinputs["TestPath"]

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
        self.__rtable = Rtable(self.admin_console)
        self.fs_utils = FileServersUtils(self.admin_console)
        self.fs_agent_adv = FsAgentAdvanceOptions(self.admin_console)
        self.fsSubclient = Subclient(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.fs_common_Helper = FileServersUtils(self.admin_console)

    def access_agent(self):

        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")

        self.fileServers.access_server(self.client_name)
        self.admin_console.access_tab("Subclients")

    def delete_subclient(self, backupset_name):
        """
        Deletes the subclient
        Args:
            backupset_name (str) : Name of the backupset
        Returns:
            None
        Raises:
            Exception if backupset not found
        """
        if self.fsSubclient.is_subclient_exists(subclient_name=self.subclient_name, backupset_name=backupset_name):
            self.log.info(f"Deleting subclient: {self.subclient_name}")
            self.fsSubclient.delete_subclient(subclient_name=self.subclient_name, backupset_name=backupset_name)
        self.admin_console.wait_for_completion()
        sleep(20)

    def add_subclient(self, backupset_name, subclient_name, plan_name, backup_content, force_create=False,
                      disablesystemstate=True):
        """
        Adds a backupset from fsAgent page

        Args:
            backupset_name (str): Name of the backupset
            subclient_name (str) : Name of the subclient
            plan_name (str): Name of the plan
            backup_content (list): Data to be backed up
            force_create (bool): Delete existing backupset and create a new one
            disablesystemstate (bool) : By default it is true
        Returns:
            None
        Raises:
            Exception if error creating backupset
        """

        if force_create:
            self.log.info("Force Create Option passed. Deleting existing one and creating new subclient")
            self.delete_subclient(backupset_name)

        self.log.info("Creating a new subclient : {self.subclient_name}")

        if self.test_path.startswith("/"):
            disablesystemstate = False

        self.RFs_agent_details.add_subclient(backupset_name=backupset_name,
                                             subclient_name=subclient_name,
                                             plan_name=plan_name,
                                             contentpaths=backup_content,
                                             disablesystemstate=disablesystemstate,
                                             define_own_content=True,
                                             remove_plan_content=True
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

    def run_verify_restore(self, file_name, path, data=True, acl=True, overwrite=False
                           ):
        """
        Run restore for the subclient from agentDetails page -> subclient restore action button.
        Also Verifies if the data was restored correctly or filters are validated.

        Args:
            file_name (str) : File name
            path (str) : Share path
            data (bool) : True to restore data
            acl (bool) : True to restore acl
            overwrite (bool) : True to unconditionally overwrite

        Returns:
            None
        Raises Exception if sparse tag is not showed or restore fails
        """


        proxy_node = None
        rest_path = rest_base = None
        proxy_node = self.tcinputs["ClientName"]

        rest_path = self.client_machine.join_path(path,
                                                  f'{self.id}_tmp_restore')

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

        self.fsSubclient.select_backupset(backupset_name=self.backupset_name)

        self.__rtable.access_action_item(self.subclient_name, self.admin_console.props['label.globalActions.restore'])

        self.admin_console.wait_for_completion()

        self.fs_common_Helper.search_files_for_restore(filename=file_name)

        self.fs_common_Helper.validate_sparse_tag()

        rest_job_id = self.fs_common_Helper.restore(subclient_name=self.subclient_name,
                                                    backupset_name=self.backupset_name,
                                                    dest_client=proxy_node,
                                                    destination_path=rest_path,
                                                    restore_acl=acl,
                                                    restore_data=data,
                                                    unconditional_overwrite=overwrite
                                                    )

        rest_job_obj = self.commcell.job_controller.get(int(rest_job_id))

        self.log.info(f"Restore job {rest_job_id} has started. Waiting for completion")

        if not rest_job_obj.wait_for_completion():
            raise Exception(f"Restore Job {rest_job_id} was {rest_job_obj.status}")

        self.log.info(f"Restore job {rest_job_id} has completed")

    def run(self):
        try:

            self.login_to_commandcenter()

            self.client_machine = Machine(machine_name=self.tcinputs['ClientName'], commcell_object=self.commcell)
            self.RFs_agent_details = Subclient(self.admin_console)

            self.log.info("*" * 10)
            self.log.info(f"Started executing testcase")

            self.base_path = self.client_machine.join_path(
                self.test_path, f'regular{self.id}')

            self.client_machine.generate_test_data(file_path=self.base_path, dirs=1, files=5, file_size=100,
                                                   sparse=True)

            self.access_agent()

            self.add_subclient(self.backupset_name,
                               self.subclient_name,
                               self.plan_name,
                               [self.base_path],
                               True)

            self.backup_subclient(self.backupset_name, Backup.BackupType.FULL)

            self.admin_console.refresh_page()

            self.log.info("Restore both data and acls")

            self.run_verify_restore(file_name="sparsefile*",
                                    path=self.base_path,
                                    data=True,
                                    acl=True,
                                    overwrite=False)

            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()

            self.access_agent()

            self.log.info("Deleting the subclient created for the testcase")
            self.delete_subclient(self.backupset_name)

            self.log.info("Deleting the content created for the testcase")

            self.log.info("Testcase executed successfully")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            if self.client_machine.check_directory_exists(self.base_path):
                self.client_machine.remove_directory(self.base_path)
            if self.client_machine.check_directory_exists(self.rest_path):
                self.client_machine.remove_directory(self.rest_path)
            self.log.info("Logging out from the command center and and closing the browser")
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
