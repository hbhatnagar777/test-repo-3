# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    init_tc()       --  Setup function for this testcase

    start_step1()   --  Check the status of workflow in Store

    start_step2()   --  Install the workflow from Store

    start_step3()   --  Validates the change of status once workflow installed

    run()           --  Main funtion for testcase execution

"""
#Test Suite Imports
from cvpysdk.commcell import Commcell
from cvpysdk.clientgroup import ClientGroups, ClientGroup
from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.Security.userhelper import UserHelper
from AutomationUtils.config import get_config
from AutomationUtils.constants import CONFIG_FILE_PATH
from AutomationUtils.options_selector import OptionsSelector

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Software store workflow Uninstall/Delete Client Restriction"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate Uninstall/Delete Client Restriction Workflow"
        self.browser = None
        self.webconsole = None
        self.store = None
        self.workflow = "Uninstall/Delete Client Restriction"
        self.client_name = None
        self.client_groups_name = None
        self.user_name = None
        self.dependent_workflow = "GetAndProcessAuthorization"
        self.dependent_workflow_store_name = "GetAndProcessAuthorization"
        self.tcinputs = {
            'UserWithDeletePrivilege': None,
            'Password': None
        }

    def init_tc(self):
        """Setup function for this testcase"""
        try:
            self.storeutils = StoreUtils(self)
            username = _STORE_CONFIG.Cloud.username
            password = _STORE_CONFIG.Cloud.password
            if not username or not password:
                self.log.info("Cloud username and password are not configured in config.json")
                raise Exception("Cloud username and password are not configured. Please update creds under {}".
                                format(CONFIG_FILE_PATH))
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(
                _STORE_CONFIG.ADMIN_USERNAME,
                _STORE_CONFIG.ADMIN_PASSWORD
            )
            self.webconsole.wait_till_load_complete()
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store(
                username=username,
                password=password
            )

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def start_step1(self):
        """Install status should be shown for workflow
        when it is not installed"""
        for workflow in [self.dependent_workflow_store_name, self.workflow]:
            pkg_status = self.store.get_package_status(
                workflow,
                category="Workflows"
            )
            if pkg_status != "Install":
                raise CVTestStepFailure(
                    f"[{workflow}] does "
                    f"not have [Install] status, found [{pkg_status}]"
                )

    @test_step
    def start_step2(self):
        """Installing workflow Uninstall/Delete Client
        Restriction"""
        for workflow in [self.dependent_workflow_store_name, self.workflow]:
            self.store.install_workflow(
                workflow, refresh=True
            )

    @test_step
    def start_step3(self):
        """Open status should be shown"""
        pkg_status = self.store.get_package_status(
            self.workflow,
            category="Workflows"
        )
        if pkg_status != "Open":
            raise CVTestStepFailure(
                f"[{self.workflow}] does"
                f"not have [Open] status after installation,"
                f"found status [{pkg_status}]"
            )

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()
            self.commcell.workflows.refresh()
            user_helper = UserHelper(self.commcell)
            workflow_helper = WorkflowHelper(self, self.workflow, deploy=False)
            try:
                user_commcell = Commcell(self.commcell.commserv_name, self.tcinputs['UserWithDeletePrivilege'],
                                         self.tcinputs['Password'])
                self.client_name = OptionsSelector(user_commcell).get_custom_str()
                user_commcell.clients.create_pseudo_client(self.client_name)
                self.log.info("Created Pseudo client %s successfully", self.client_name)
                self.commcell.refresh()
                client_groups = ClientGroups(self.commcell)
                self.client_groups_name = OptionsSelector(self.commcell).get_custom_str()
                client_groups.add(self.client_groups_name, clients=[self.client_name])
                self.log.info("Created Client Group %s successfully", self.client_groups_name)
                client_group_obj = ClientGroup(self.commcell, self.client_groups_name)
                client_group_id = client_group_obj.clientgroup_id
                workflow_helper.is_deployed(self.workflow)
                config_xml = """<Config_ClientGroup><clientGroupId>{0}</clientGroupId>
                <clientGroupName>{1}</clientGroupName></Config_ClientGroup>""".\
                    format(client_group_id, self.client_groups_name)
                workflow_helper.modify_workflow_configuration(config_xml)
                user_commcell.clients.delete(self.client_name)
                raise Exception("Client deletion succeeded by user of non-master usergroup "
                                "Expected to be restrict from Business Logic workflow")
            except Exception as excp:
                if 'An email has been sent to the administrator to authorize the Delete Client request' in str(excp):
                    self.log.info("Client Deletion is restricted as expected from Business Logic Workflow")
                else:
                    self.log.error(str(excp))
                    raise Exception("Validation of Limit restore Operation BL workflow failed with error {}".
                                    format(str(excp)))
            user_response = workflow_helper.bl_workflows_setup([self.workflow])
            self.user_name = user_response[0]
            user1_user_commcell = user_response[1]
            user1_user_commcell.clients.delete(self.client_name)
            self.log.info("Client deletion succeeded by user of master usergroup as "
                          "expected from Business Logic Workflow")
        except Exception as err:
            self.storeutils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            WorkflowHelper(self, self.workflow, deploy=False).delete([self.workflow, self.dependent_workflow])
            client_groups.delete(self.client_groups_name)
            user_helper.delete_user(self.user_name, new_user='admin')
