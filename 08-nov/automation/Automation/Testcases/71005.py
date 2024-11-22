# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Delete Plan Authorization


Steps:
    0.  Previous run cleanup
    1.  Create entities.
        A.  Disk storage
        B.  Server plan
        C.  Backup set
        D.  Sub client
    2.  Case I  -  Delete plan without data (deny approval)
    3.  Case II -  Delete plan without data (accept approval)
    4.  Case III-  Delete plan with data (deny approval)
    5.  Case IV -  Delete plan with data (accept approval)
    *.  Cleanup

TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class object.

    _init_tc()      --  Initial configuration for the test case.
    _init_props()   --  Initializes parameters and names required for testcase.
    setup()         --  setup function of this test case.

    _cleanup()      --  Delete entities before/after running testcase.

    _create_plan()  --  Configures a new plan.
    _create_entities--  Create entities for the test case.

    _run_backups()  --  Run multiple backups.

    _delete_subclient_and_attempt_plan_deletion() -- Delete Subclient and attempt to delete Plan
    _perform_approval_request_action()            -- Perform approval action
    _check_if_plan_exists()                       -- Checks if plan exists

    run()           --  run function of this test case.
    tear_down()     --  tear down function of this test case.


Non-Admin User should have the following permissions:
        [Execute Workflow] permission on [Execute Query] workflow


Admin User should have the following permissions:
        View / Accept / Deny delete plan authorization requests


Sample Input:
"71005": {
    "ClientName": "Name of the client",
    "AgentName": "File System",
    "MediaAgentName": "Name of the media agent",
    "AdminUsername": "Admin user login name",
    "AdminPassword": "Admin user password"
    *** OPTIONAL ***
    "dedupe_path": "LVM enabled path for Unix MediaAgent",
    "enableWorkflow": true,
    "reuseStorage": "Disk storage name to be used instead of configuring new one",
    "reuseBackupset": "Backup set to be used instead of configuring new one",
}


NOTE:
    1. LVM enabled path must be supplied for Unix MA. Dedupe paths will be created inside this folder.
    2. commcellUsername is the login name for user who will attempt plan deletion.
    3. AdminUsername from test case inputs is the login name for user who will approve plan deletion.
    4. Testcase strictly requires usernames. Do not provide email IDs inplace of it.
"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector

from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, handle_testcase_exception

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from MediaAgents.MAUtils.mahelper import MMHelper

from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):
    """Test case to verify dual authorization for delete plan"""

    test_step = TestStep()
    WORK_FLOW_NAME = 'DeletePlanAuthorization'

    def __init__(self):
        """Initializes test case class object.

            Properties to be initialized:
                name        (str)       --  name of this test case

                tcinputs    (dict)      --  test case inputs with input name as dict key
                                            and value as input type
        """
        super(TestCase, self).__init__()

        self.name = 'Delete Plan Authorization'
        self.tcinputs = {
            'ClientName': None,
            'AgentName': None,
            'MediaAgentName': None,
            'AdminUsername': None,
            'AdminPassword': None,
        }

        self.browser = None
        self.admin_console: AdminConsole = None
        self.admin_browser = None
        self.admin_admin_console: AdminConsole = None

        self.storage_helper: StorageMain = None
        self.plan_helper: PlanMain = None
        self.mm_helper: MMHelper = None
        self.work_flow_helper: WorkflowHelper = None

        self.media_agent_name = None
        self.client_machine = None

        self.content_path = None
        self.content_path_template = None
        self.mount_path_template = None
        self.dedupe_path_template = None

        self.disk_storage_name = None
        self.plan_name = None
        self.plan_name_1 = None
        self.plan_name_2 = None

        self.storage_policy = None

        self.backup_set_name = None
        self.sub_client_name_template = None

        self.cleanup_storage = None
        self.cleanup_backup_set = None

    def _init_tc(self):
        """Initial configuration for the test case."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )

            self.admin_browser = BrowserFactory().create_browser_object()
            self.admin_browser.open()
            self.admin_admin_console = AdminConsole(self.admin_browser, self.commcell.webconsole_hostname)
            self.admin_admin_console.login(
                self.tcinputs["AdminUsername"],
                self.tcinputs["AdminPassword"]
            )

            self.storage_helper = StorageMain(self.admin_console)
            self.plan_helper = PlanMain(self.admin_console)
            self.mm_helper = MMHelper(self)
            if self.tcinputs.get('enableWorkflow'):
                self.work_flow_helper = WorkflowHelper(self, self.WORK_FLOW_NAME)
        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    def _init_props(self):
        """Initializes parameters and names required for testcase."""
        self.media_agent_name = self.tcinputs['MediaAgentName']

        options_selector = OptionsSelector(self.commcell)
        str_id = str(self.id)

        media_agent_machine = options_selector.get_machine_object(self.media_agent_name)
        ma_drive = options_selector.get_drive(media_agent_machine)

        self.client_machine = options_selector.get_machine_object(self.client.client_name)
        cl_drive = options_selector.get_drive(self.client_machine)

        self.content_path = self.client_machine.join_path(cl_drive, 'Automation', str_id, 'CONTENT')
        self.content_path_template = self.client_machine.join_path(self.content_path, 'COUNT(%s)')
        self.mount_path_template = media_agent_machine.join_path(ma_drive, 'Automation', str_id, 'MP(%s)')

        if 'unix' in media_agent_machine.os_info.lower():
            if 'dedupe_path' not in self.tcinputs:
                self.log.error('LVM enabled dedup path must be supplied for Unix MA')
                raise ValueError('LVM enabled dedup path must be supplied for Unix MA')
            self.dedupe_path_template = media_agent_machine.join_path(self.tcinputs["dedupe_path"],
                                                                      'Automation', str_id, f"DDB(%s)")
        else:
            self.dedupe_path_template = media_agent_machine.join_path(ma_drive, 'Automation', str_id, f"DDB(%s)")

        if isinstance(self.tcinputs.get('reuseStorage'), str):
            self.disk_storage_name = self.tcinputs.get('reuseStorage')
            self.cleanup_storage = False
        else:
            self.disk_storage_name = '%s_disk-storage_ma-%s_primary' % (str_id, self.media_agent_name)
            self.cleanup_storage = True
        self.plan_name_1 = '%s_plan_ma-%s' % (str_id, self.media_agent_name) + '_1'
        self.plan_name_2 = '%s_plan_ma-%s' % (str_id, self.media_agent_name) + '_2'

        if isinstance(self.tcinputs.get('reuseBackupset'), str):
            self.backup_set_name = self.tcinputs.get('reuseBackupset')
            self.cleanup_backup_set = False
        else:
            self.backup_set_name = '%s_backupset_cl-%s_ma-%s' % (str_id, self.client.client_name, self.media_agent_name)
            self.cleanup_backup_set = True
        self.sub_client_name_template = '%s_subclient' % str_id + "_count-%s"

    def setup(self):
        """Setup function of this test case."""
        self._init_tc()
        self._init_props()

    @test_step
    def _cleanup(self):
        """Delete entities before/after running testcase."""
        try:
            if self.cleanup_backup_set:
                self.log.info(f"Deleting backupset {self.backup_set_name}, if exits")
                if self.agent.backupsets.has_backupset(self.backup_set_name):
                    self.log.info(f"Deleting backupset {self.backup_set_name}")
                    self.agent.backupsets.delete(self.backup_set_name)
                    self.log.info(f"Deleted backupset {self.backup_set_name}")
            else:
                self.log.info(f"Backupset {self.backup_set_name} cleanup skipped, will be reused next time")

            self.plan_name = self.plan_name_1
            self.log.info(f"Deleting plan {self.plan_name}, if exits")
            if self._check_if_plan_exists(should_exist=None):
                self.log.info(f"Deleting plan {self.plan_name}")
                self.plan_helper.plan_name = {'server_plan': self.plan_name}
                self.plan_helper.delete_plans(
                    dual_auth_enabled=True,
                    automation_username=self.inputJSONnode["commcell"]["commcellUsername"],
                    reuse_admin_console=self.admin_admin_console
                )
                self.log.info(f"Deleted plan {self.plan_name}")

            self.plan_name = self.plan_name_2
            self.log.info(f"Deleting plan {self.plan_name}, if exits")
            if self._check_if_plan_exists(should_exist=None):
                self.log.info(f"Deleting plan {self.plan_name}")
                self.plan_helper.plan_name = {'server_plan': self.plan_name}
                self.plan_helper.delete_plans(
                    dual_auth_enabled=True,
                    automation_username=self.inputJSONnode["commcell"]["commcellUsername"],
                    reuse_admin_console=self.admin_admin_console
                )
                self.log.info(f"Deleted plan {self.plan_name}")

            if self.cleanup_storage:
                self.log.info(f"Deleting storage {self.disk_storage_name}, if exists")
                if self.commcell.storage_pools.has_storage_pool(self.disk_storage_name):
                    self.log.info(f"Deleting storage {self.disk_storage_name}")
                    self.storage_helper.delete_disk_storage(self.disk_storage_name)
                    self.log.info(f"Deleted storage {self.disk_storage_name}")
            else:
                self.log.info(f"Storage {self.disk_storage_name} cleanup skipped, will be reused next time")
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}') from exp

    def _create_plan(self, plan, pri_storage):
        """Configures a new plan and associates each copy to given storage.

            Args:
                plan        (str)   - Plan name
                pri_storage (str)   - Storage to be used for primary copy
        """
        self.plan_helper.plan_name = {'server_plan': plan}
        self.plan_helper.storage = {'pri_storage': pri_storage, 'pri_ret_period': '1', 'ret_unit': 'Day(s)'}

        self.plan_helper.retention = None
        self.plan_helper.rpo_hours = None
        self.plan_helper.backup_data = None
        self.plan_helper.allow_override = None
        self.plan_helper.allowed_features = None
        self.plan_helper.backup_data = None
        self.plan_helper.backup_day = None
        self.plan_helper.backup_duration = None
        self.plan_helper.snapshot_options = None
        self.plan_helper.database_options = None

        if not self._check_if_plan_exists(should_exist=None):
            self.log.info("Configuring new plan")
            self.plan_helper.add_plan()
        else:
            self.log.info("Plan already exists! Test run will reuse existing plan.")

    @test_step
    def _create_entities(self, case):
        """Create entities for the test case."""

        self.commcell.storage_pools.refresh()
        self.log.info(f"Configuring storage {self.disk_storage_name}, if not exists")
        if self.commcell.storage_pools.has_storage_pool(self.disk_storage_name):
            self.log.info("Disk storage already exists!, will be reused.")
        else:
            self.log.info(f"Creating disk storage")
            self.log.info(f"... Using storage name: {self.disk_storage_name}")
            self.log.info(f"... Using media agent: {self.media_agent_name}")
            self.log.info(f"... Using backup location: {self.mount_path_template % 'primary'}")
            self.storage_helper.add_disk_storage(
                disk_storage_name=self.disk_storage_name,
                media_agent=self.media_agent_name,
                backup_location=self.mount_path_template % 'primary',
                deduplication_db_location=[
                    self.dedupe_path_template % '10',
                    self.dedupe_path_template % '11',
                    self.dedupe_path_template % '12',
                    self.dedupe_path_template % '13',
                ]
            )
        self.commcell.storage_pools.refresh()

        self.log.info(f"Creating server plan, if not exists")
        self.log.info(f"... Using plan name: {self.plan_name}")
        self.log.info(f"... Using storage for primary copy: {self.disk_storage_name}")
        self._create_plan(self.plan_name, self.disk_storage_name)

        self.log.info(f"Configuring Backupset {self.backup_set_name}, if not exists")
        self.backupset = self.mm_helper.configure_backupset(backupset_name=self.backup_set_name, agent=self.agent)
        self.log.info(f"Configured Backupset {self.backup_set_name}")

        self.commcell.plans.refresh()
        self.storage_policy = self.commcell.plans.get(self.plan_name).storage_policy

        sub_client_name = self.sub_client_name_template % case
        self.log.info(f"Configuring Subclient {sub_client_name}, if not exists")
        self.mm_helper.configure_subclient(
            backupset_name=self.backup_set_name,
            subclient_name=sub_client_name,
            storage_policy_name=self.storage_policy.storage_policy_name,
            content_path=self.content_path_template % case,
            agent=self.agent,
        )
        self.log.info(f"Configured Subclient {sub_client_name}")
        self.backupset.refresh()

        self.commcell.refresh()
        self.commcell.storage_pools.refresh()

    @test_step
    def _run_backups(self, case):
        """Run multiple backups"""
        def __run_backups__(backup_cycle):
            for backup_level in backup_cycle:
                self.log.info("Running %s backup for Subclient in Backupset", backup_level)

                suffix = time.strftime("%H%M")
                sub_client = self.sub_client_name_template % case
                content_path = self.content_path_template % case
                self.log.info("Generating data at content path: %s", content_path)
                self.mm_helper.create_uncompressable_data(self.client,
                                                          self.client_machine.join_path(content_path, suffix),
                                                          0.1)
                self.log.info("Starting %s backup for sub client: %s", backup_level, sub_client)
                job = self.backupset.subclients.get(sub_client).backup(backup_level=backup_level)
                self.log.info(f"Started %s backup job: %s", backup_level, job.job_id)

                if not job.wait_for_completion():
                    jpr = job.delay_reason
                    raise Exception(f"Failed to run {backup_level} backup job {job.job_id} with error: {jpr}")
                self.log.info("Completed %s backup with Job ID: %s", backup_level, job.job_id)

                self.log.info("Waiting for 30 seconds to ensure job is no longer active")
                time.sleep(30)
                self.log.info("30 seconds wait finished.")

        # ---------------------------------
        __run_backups__(['full', 'incremental', 'synthetic_full'])

    @test_step
    def _delete_subclient_and_attempt_plan_deletion(self, case):
        """Delete Subclient and attempt to delete Plan

            Args:
                case        (int)   -   Case number
        """
        sub_client_name = self.sub_client_name_template % case

        self.log.info(f"Deleting subclient {sub_client_name}")
        self.backupset.subclients.delete(sub_client_name)
        self.log.info(f"Deleted subclient {sub_client_name}")

        self.plan_helper.delete_plan__attempt_deletion(self.plan_name, dual_auth_enabled=True)

    @test_step
    def _perform_approval_request_action(self, deny=False):
        """Perform approval action"""
        self.plan_helper.delete_plan__approve_deletion(
            plan_name=self.plan_name,
            automation_username=self.inputJSONnode["commcell"]["commcellUsername"],
            reuse_admin_console=self.admin_admin_console,
            deny=deny
        )

    def _check_if_plan_exists(self, should_exist):
        """ Checks if plan exists

            Args:
                should_exist        (bool)  --  If plan should exist
                    True    - Raises error if plan does not exist
                    False   - Raises error if plan still exists
                    None    - Does not raise error for any case, used during cleanup

            Returns:
                (bool)      --  True if plan exists else false
        """
        query = f"""
        SELECT  name
        FROM    App_Plan    WITH (NOLOCK)
        WHERE   name = '{self.plan_name}'
        """

        self.log.info(f"Checking plan {self.plan_name}, from CSDB query")
        self.log.info(f"Running query to check if plan exists: {query}")
        result = self.mm_helper.execute_select_query(query)
        self.log.info(f"Result obtained: {result}")
        if result[0] == "" or (
            isinstance(result[0], list) and
            result[0][0] == ""
        ):
            self.log.info(f"Plan does not exist in CSDB {self.plan_name}")
            if should_exist:
                self.log.info("Plan existence using CSDB query validation failed!")
                raise Exception("Plan existence using CSDB query validation failed!")
            return False
        self.log.info(f"Plan exists in CSDB {self.plan_name}")
        if should_exist == False:
            self.log.info("Plan still exists!")
            raise Exception("Plan still exists!")
        return True

    def run(self):
        """Run function of this test case."""

        try:
            if self.tcinputs.get('enableWorkflow'):
                self.log.info(f"Enabling workflow: {self.WORK_FLOW_NAME}")
                self.work_flow_helper.enable_workflow(workflow=self.WORK_FLOW_NAME)
                self.log.info(f"Enabled workflow: {self.WORK_FLOW_NAME}")

            self._cleanup()

            self.plan_name = self.plan_name_1

            self._create_entities(1)
            self._delete_subclient_and_attempt_plan_deletion(1)
            self._check_if_plan_exists(should_exist=True)
            self._perform_approval_request_action(deny=True)
            self._check_if_plan_exists(should_exist=True)

            self._create_entities(2)
            self._delete_subclient_and_attempt_plan_deletion(2)
            self._check_if_plan_exists(should_exist=True)
            self._perform_approval_request_action(deny=False)
            self._check_if_plan_exists(should_exist=False)

            self.plan_name = self.plan_name_2

            self._create_entities(3)
            self._run_backups(3)
            self._delete_subclient_and_attempt_plan_deletion(3)
            self._check_if_plan_exists(should_exist=True)
            self._perform_approval_request_action(deny=True)
            self._check_if_plan_exists(should_exist=True)

            self._create_entities(4)
            self._run_backups(4)
            self._delete_subclient_and_attempt_plan_deletion(4)
            self._check_if_plan_exists(should_exist=True)
            self._perform_approval_request_action(deny=False)
            self._check_if_plan_exists(should_exist=False)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case."""
        try:
            self.log.info(f"Deleting content path created by test case: {self.content_path}, if exists")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info(f"Deleting content path created by test case: {self.content_path}")
                self.client_machine.remove_directory(self.content_path)
                self.log.info(f"Deleted content path created by test case: {self.content_path}")

            self._cleanup()
        except Exception as exp:
            self.log.error('Failed to tear down test case with error: %s', exp)
        finally:
            if self.tcinputs.get('enableWorkflow'):
                self.log.info(f"Disabling workflow: {self.WORK_FLOW_NAME}")
                self.work_flow_helper.disable_workflow(workflow=self.WORK_FLOW_NAME)
                self.log.info(f"Disabled workflow: {self.WORK_FLOW_NAME}")

            AdminConsole.logout_silently(self.admin_admin_console)
            self.admin_browser.close()
            AdminConsole.logout_silently(self.admin_console)
            self.browser.close()
