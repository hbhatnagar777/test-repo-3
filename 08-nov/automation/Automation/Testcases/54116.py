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
from Server.Workflow.workflowhelper import WorkflowHelper
from Web.AdminConsole.adminconsole import AdminConsole

_STORE_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing Software store workflow Clone Client Dataset"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate Clone Client Dataset workflow"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.browser = None
        self.webconsole = None
        self.adminconsole = None
        self.store = None
        self.storeutils = StoreUtils(self)
        self.workflow = "Clone Client DataSet"
        self.tcinputs = {
            "Source client": None,
            "Target clients": None,
            "Target client groups": None,
            "User email": None
        }

    def init_tc(self):
        """ Initialize store and browser objects """
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

        except Exception as excp:
            raise CVTestCaseInitFailure(excp) from excp

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
        """After installing workflow, status should be Open"""
        self.store.install_workflow(
            self.workflow, refresh=True
        )

    @test_step
    def start_step3(self):
        """When clicked on Open, workflow form should open """
        self.store.open_package(
            self.workflow,
            category="Workflows"
        )
        self.adminconsole = AdminConsole(
            self.browser,
            self.commcell.webconsole_hostname
        )
        forms = Forms(self.adminconsole)
        self.adminconsole.close_popup()
        self.adminconsole.wait_for_completion()
        if forms.is_form_open(self.workflow) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.workflow}]"
            )
        forms.close_form()

    def run(self):
        """Main function for test case execution"""

        try:
            # Class Initializations
            workflow_name = self.workflow
            workflow_helper = WorkflowHelper(self, workflow_name, deploy=False)

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                1) Install workflow from store on local CS
                2) Execute Workflow to clone client dataset
                3) Get workflow job id and wait for the workflow to complete.
                4) Make sure workflow completes and passes
            """, 200)
            # ---------------------------------------------------------------------------------------------------------

            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Execute Workflow to clone client dataset from source to destination clients
                Get workflow job id and wait for the workflow to complete.
            """)
            workflow_inputs = {
                'INP_EMAIL': self.tcinputs['User email'],
                'INP_TARGET_CLIENT': self.tcinputs['Target clients'].split(","),
                'INP_CLIENT_GROUP': self.tcinputs['Target client groups'].split(","),
                'INP_SOURCE_CLIENT': self.tcinputs['Source client']
            }
            workflow_helper.execute(workflow_inputs)
            # ---------------------------------------------------------------------------------------------------------

        except Exception as excp:
            self.storeutils.handle_testcase_exception(excp)
            workflow_helper.test.fail(excp)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            WorkflowHelper(self, workflow_name, deploy=False).delete(workflow_name)
