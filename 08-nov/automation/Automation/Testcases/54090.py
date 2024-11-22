# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 54090

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
# Test Suite Imports
from cvpysdk.commcell import Commcell
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
from AutomationUtils.config import get_config
from AutomationUtils.constants import CONFIG_FILE_PATH
from AutomationUtils.options_selector import OptionsSelector, CVEntities

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Software store workflow Exclude Content Filter - Restriction - GUI"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate Exclude Content Filter - Restriction - GUI workflow"
        self.browser = None
        self.webconsole = None
        self.store = None
        self.workflow = "Exclude Content Filter - Restriction - GUI"
        self.tcinputs = {
            'UserWithSubclientPrivilege': None,
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
                raise Exception("Cloud username and password are not configured. Please update creds under {}".format(CONFIG_FILE_PATH))
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
        pkg_status = self.store.get_package_status(
            self.workflow,
            category="Workflows"
        )
        if pkg_status != "Install":
            raise CVTestStepFailure(
                f"[{self.workflow}] does "
                f"not have [Install] status, found [{pkg_status}]"
            )

    @test_step
    def start_step2(self):
        """Installing workflow Exclude Content Filter - Restriction - GUI"""
        self.store.install_workflow(
            self.workflow, refresh=True
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
            self.commcell.refresh()
            workflow_helper = WorkflowHelper(self, self.workflow, deploy=False)
            utility = OptionsSelector(self.commcell)
            user = self.tcinputs['UserWithSubclientPrivilege']
            password = self.tcinputs['Password']
            entities = CVEntities(self)
            client = self.client.client_name
            user_commcell = Commcell(self.commcell.commserv_name, user, password)
            entity_inputs = (['subclient'])
            # Create subclient
            entity_props = entities.create(entity_inputs)
            self.subclient = entity_props['subclient']['object']
            subclient_name = entity_props['subclient']['name']
            dir = utility.create_directory(client)
            subclient_content = self.subclient.content
            subclient_content.append(dir)
            # Update new content to subclient
            self.subclient.content = subclient_content
            self.log.info("Successfully updated the content of subclient")
            instances = user_commcell.clients.get(client).agents.get(self.tcinputs['AgentName']).instances
            subclient = instances.get(
                self.tcinputs['InstanceName']
            ).backupsets.get(self.tcinputs['BackupsetName']).subclients
            user_subc_object = subclient.get(subclient_name)
            workflow_helper.is_deployed(self.workflow)
            user_commcell.refresh()
            self.log.info("Initialising the update subclient with exclude content "
                          "properties as non-admin user")
            exclusion_content = []
            exclusion_content.append(dir)
            try:
                user_subc_object.filter_content = exclusion_content
                raise Exception("Exclude filter content is updated sucessfully by non-admin user. "
                                "Expected to restrict"
                                " through Business Logic workflow")
            except Exception as excp:
                excp_msg = 'You dont have permission to add/delete exclude file/folder content'
                if excp_msg in str(excp):
                    self.log.info("Exclude filter content update is restricted as expected"
                                  " from Business Logic Workflow")
                else:
                    self.log.error(str(excp))
                    raise Exception("Validation of Business Logic workflow [{}] failed".format(self.workflow))
            self.log.info("Initialising the update subclient with exclude content "
                          "properties as master user")
            self.subclient = self.backupset.\
                subclients.get(subclient_name)
            self.subclient.filter_content = exclusion_content
            self.log.info("Exclude filter content is updated successfully by master "
                          "user as expected")
        except Exception as excp:
            raise Exception("Exception {0}".format(str(excp)))
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            workflow_helper.delete(self.workflow)
            entities.cleanup()
