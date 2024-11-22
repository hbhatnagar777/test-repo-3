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

    run()           --  run function of this test case
"""

# Test Suite imports
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (Browser, BrowserFactory)
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure)
from Web.Common.page_object import TestStep
from Web.WebConsole.Forms.forms import Forms
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils.options_selector import OptionsSelector
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.Security.userhelper import UserHelper
from Server.Workflow import workflowconstants as WC

_STORE_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing Software store workflow DeleteClientAuthorization"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate DeleteClientAuthorization workflow"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.browser = None
        self.webconsole = None
        self.store = None
        self.storeutils = StoreUtils(self)
        self.workflow = "DeleteClientAuthorization"
        self.workflow_store_name = "DeleteClientAuthorization"
        self.dependent_workflow = "GetAndProcessAuthorization"
        self.dependent_workflow_store_name = "GetAndProcessAuthorization"

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword']
            )
            self.webconsole.wait_till_load_complete()
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store(
                username=_STORE_CONFIG.Cloud.username,
                password=_STORE_CONFIG.Cloud.password
            )

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def start_step1(self):
        """Install status should be shown for workflow
        when it is not installed"""
        for workflow in [self.dependent_workflow_store_name, self.workflow_store_name]:
            pkg_status = self.store.get_package_status(workflow, category="Workflows")
            if pkg_status != "Install":
                raise CVTestStepFailure(
                    f"[{workflow}] does "
                    f"not have [Install] status, found [{pkg_status}]"
                )

    @test_step
    def start_step2(self):
        """After installing workflow, status should be Open"""
        for workflow in [self.dependent_workflow_store_name, self.workflow_store_name]:
            self.store.install_workflow(
                workflow, refresh=True
            )

    def run(self):
        """Main function for test case execution"""

        try:
            workflow_name = self.workflow
            dependent_workflow = self.dependent_workflow
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.commcell.workflows.refresh()

            # Class Initializations
            workflow_helper = WorkflowHelper(self, workflow_name, deploy=False)

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                1. Create non admin user and corresponding commcell object
                2. Validate if the business logic workflows DeleteClientAuthorization and
                    GetAndProcessAuthorization are deployed
                3. Create a new pseudo client
                4. Try deleting client from non admin user. It should be blocked.
                5. Approve the workflow user interaction request to delete the client
                6. Get workflow job id for the business logic workflow and wait for it to complete.
                7. Validate if client is deleted
            """, 200)
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Create non admin user and corresponding commcell object
                Validate if the BL workflows DeleteClientAuthorization and GetAndProcessAuthorization are deployed
                Create a pseudo client
            """)
            response = workflow_helper.bl_workflows_setup([workflow_name, dependent_workflow])
            user_commcell = response[1]
            user = response[0]
            client_name = OptionsSelector(self.commcell).get_custom_str()
            self.log.info("Creating a pseudo client [{0}]".format(client_name))
            self.commcell.clients.create_pseudo_client(client_name)
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Try deleting client from non admin user. It should be blocked by BL Workflow.
            """)
            try:
                self.log.info("Attempting to delete client. Should be blocked by workflow [{0}]".format(workflow_name))
                user_commcell.clients.delete(client_name)
                raise Exception("Client deletion succeeded. Expected to be blocked from business logic workflow")
            except Exception as excp:
                if 'An email has been sent to the administrator' in str(excp):
                    self.log.info("Error as expected: [{0}]".format(str(excp)))
                    self.log.info("Client deletion successfully blocked through business logic workflow.")
                else:
                    self.log.error(str(excp))
                    raise Exception("Client validation failed")
                user_commcell.clients.refresh()
                assert user_commcell.clients.has_client(client_name), "Client deleted unexpectedly. Test Failed"
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Approve the workflow user interaction request to delete the client
                Get workflow job id for the business logic workflow and wait for it to complete.
                Validate if client is deleted
            """)
            workflow_helper.process_user_requests(user, input_xml=WC.WORKFLOW_DEFAULT_USER_INPUTS % user)
            user_commcell.clients.refresh()
            assert not user_commcell.clients.has_client(client_name), "Client still exists. Test Failed"
            self.log.info("Client [{0}] deleted via Business logic workflow's [Approve] action".format(client_name))
            # ---------------------------------------------------------------------------------------------------------

        except Exception as excp:
            self.storeutils.handle_testcase_exception(excp)
            workflow_helper.test.fail(excp)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            WorkflowHelper(self, workflow_name, deploy=False).delete([workflow_name, dependent_workflow])
            UserHelper(self.commcell).delete_user(user_name=user, new_user='admin')
            workflow_helper.database.delete_client(client_name)
