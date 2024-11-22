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

    access_agent()  --  Access to the agent page

    delete_backupset()  -- Delete the backupset

    add_subclient() -- Adds a new subclient

    wait_for_job_completion()   --  Waits for the completion of a job

    backup_subclient()  -- Backups a subclient

    run_restore_verify()    -- Restores from a subclient and verifies the data restored

    generate_or_modify_data()   -- Generates  the data on the path
"""

"""
Sample JSON for the Testcase

"63386":{
        "AgentName":"File System",
        "ClientName":"",
        "PlanName":"plan-name",
        "BackupsetName":"backupsetname",
        "TestPath": "path",
    }

Note: The inputs mentioned in [] are required only for Windows File System agent
"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FileServerPages.fsagent import FsAgent, FsSubclient
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient, FsAgentAdvanceOptions
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils
from Web.AdminConsole.Components.panel import Backup
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.config import get_config


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.RFs_agent_details = None
        self.fshelper = None
        self.subclient_name = None
        self.plan_name = None
        self.admin_console = None
        self.browser = None
        self.impersonate_user = None
        self.impersonate_password = None
        self.fileServers = None
        self.fsAgent = None
        self.deleted_items_checksum = None
        self.service = None
        self.base_path = None
        self.UNC_base_path = None
        self.file3_checksums = None
        self.fsSubclient = None
        self.file3_job2_checksum = None
        self.test_path = None
        self.backupset_name = None
        self.dashboard = None
        self.config = get_config()
        self.tcinputs = {
            "TestPath": None,
            "AgentName": None,
            "ClientName": None,
            "PlanName": None,
            "BackupsetName": None
        }

    def setup(self):
        """Setup function of the testcase
        Initializing Pre-requisites for this testcase """

        self.name = "Basic Backups and Restores for Regular FS"
        self.fshelper = FSHelper(self)
        self.fshelper.populate_tc_inputs(self, mandatory=False)
        self.subclient_name = f"AUTO_Subclient_{self.id}"
        self.plan_name = self.tcinputs.get("PlanName")
        self.backupset_name = self.tcinputs.get("BackupsetName")

    def login_to_commandcenter(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)

        self.fileServers = FileServers(self.admin_console)
        self.fsAgent = FsAgent(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.fsSubclient = Subclient(self.admin_console)
        self.fs_common_Helper = FileServersUtils(self.admin_console)
        self.fs_agent_adv = FsAgentAdvanceOptions(self.admin_console)

    def access_agent(self):

        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")

        self.fileServers.access_server(self.client_name)
        self.admin_console.access_tab("Subclients")

    def delete_subclient(self, subclient_name, backupset_name):
        """
        Deletes the subclient
        Args:
            subclient_name (str) : Name of the subclient
            backupset_name (str) : Name of the backupset
        Returns:
            None
        Raises:
            Exception if backupset not found
        """

        self.log.info(f"Deleting subclient: {subclient_name}")
        self.fsSubclient.delete_subclient(subclient_name, backupset_name)
        self.admin_console.wait_for_completion()

    def add_subclient(self, subclient_name, plan_name, backup_data, force_create=False):
        """
        Adds a backupset from fsAgent page

        Args:
            subclient_name (str): Name of the subclient
            plan_name (str): Name of the plan
            backup_data (list): Data to be backed up
            force_create (bool): Delete existing backupset and create a new one
        Returns:
            None
        Raises:
            Exception if error creating subclient
        """

        if force_create:
            self.log.info("Force Create Option passed. Deleting existing one and creating new Subclient")
            self.delete_subclient(subclient_name,self.backupset_name)

        if ':\\' in self.tcinputs['TestPath']:
            disablesystemstate=True
        else:
            disablesystemstate=False

        self.RFs_agent_details.add_subclient(
            subclient_name=subclient_name,
            backupset_name=self.backupset_name,
            plan_name=plan_name,
            contentpaths=backup_data,
            define_own_content=True,
            remove_plan_content=True,
            disablesystemstate=disablesystemstate
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

    def run_restore_verify(self, data=True, acl=True, overwrite=False
                           ):
        """
        Run restore for the subclient from agentDetails page -> subclient restore action button.
        Also Verifies if the data was restored correctly.

        Args:
            data (bool) : True to restore data
            acl (bool) : True to restore acl
            overwrite (bool) : True to unconditionally overwrite

        Returns:
            None
        Raises Exception if data is not restored correctly / Restore job failed.
        """

        rest_path = self.client_machine.join_path(self.test_path,
                                                  f'{self.id}_tmp_restore')

        source_checksum = self.client_machine.get_checksum_list(self.base_path)

        rest_job_id = self.fsSubclient.restore_subclient(subclient_name=self.subclient_name,
                                                         backupset_name=self.backupset_name,
                                                         dest_client=self.tcinputs["ClientName"],
                                                         restore_acl=acl,
                                                         restore_data=data,
                                                         destination_path=rest_path,
                                                         unconditional_overwrite=overwrite
                                                         )

        rest_job_obj = self.commcell.job_controller.get(int(rest_job_id))

        self.log.info(f"Restore job {rest_job_id} has started. Waiting for completion")

        if not rest_job_obj.wait_for_completion():
            raise Exception(f"Restore Job {rest_job_id} was {rest_job_obj.status}")

        self.log.info(f"Restore job {rest_job_id} has completed")

        destination_checksum = self.client_machine.get_checksum_list(rest_path)

        if self.fshelper.compare_lists(source_checksum, destination_checksum):
            self.log.info("Checksum comparision successful")
        else:
            self.log.info("Checksum comparission failed")

    def generate_or_modify_data(self, acls):

        base_path = self.client_machine.join_path(self.test_path, f'{self.id}')
        file_path = self.client_machine.join_path(base_path, 'test')

        self.log.info(f"Creating directory: {base_path}")
        self.client_machine.create_directory(base_path, force_create=True)

        self.client_machine.generate_test_data(file_path, acls=acls)

    def run(self):
        try:

            self.login_to_commandcenter()

            self.RFs_agent_details = Subclient(self.admin_console)

            self.log.info("*" * 10)
            self.log.info(f"Started executing testcase")

            self.base_path = self.client_machine.join_path(self.test_path, f'{self.id}')

            self.access_agent()

            self.add_subclient(self.subclient_name,
                               self.plan_name,
                               [self.base_path],
                               force_create=True)

            self.generate_or_modify_data(acls=True)

            self.backup_subclient(self.backupset_name, Backup.BackupType.FULL)

            self.admin_console.refresh_page()

            self.log.info("Restore all versions Out-of-place")

            self.run_restore_verify(
                                    data=True,
                                    acl=True
                                    )

            self.admin_console.driver.back()
            self.admin_console.wait_for_completion()

            self.admin_console.access_tab("Subclients")

            self.delete_subclient(self.subclient_name,self.backupset_name)

            self.log.info("Deleting the content created for the testcase")

            self.log.info("Testcase executed successfully")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.client_machine.remove_directory(self.base_path)
            self.client_machine.remove_directory(self.test_path)
            self.log.info("Logging out from the command center and and closing the browser")
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
