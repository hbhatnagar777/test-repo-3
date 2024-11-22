# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 54052

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
from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Forms.forms import Forms
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.config import get_config
from Web.AdminConsole.adminconsole import AdminConsole

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Software store workflow DBMaintenance"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [Software Store] - Validate DBMaintenance workflow"
        self.browser = None
        self.webconsole = None
        self.adminconsole = None
        self.store = None
        self.workflow = "DBMaintenance"
        self.workflow_id = "DBMaintenance"
        self._workflow = None
        self.show_to_user = False
        self.tcinputs = {
            'MaintenanceType': None,
            'DatabaseName': None
            }

    def init_tc(self):
        """Setup function for this testcase"""
        try:
            self.storeutils = StoreUtils(self)
            username = _STORE_CONFIG.Cloud.username
            password = _STORE_CONFIG.Cloud.password
            if not username or not password:
                self.log.info("Cloud username and password are not configured in config.json")
                raise Exception("Cloud username and password are not configured. Please update "\
                                "the username and password details under "\
                                "<Automation_Path>/CoreUtils/Templates/template-config.json")
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
        if forms.is_form_open(self.workflow_id) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.workflow}]"
            )
        forms.close_form()

    def run(self):
        """Main function for test case execution"""
        try:
            workflow_helper = WorkflowHelper(self, self.workflow_id, deploy=False)
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()
            workflow_helper.execute(
                {
                    'type': self.tcinputs['MaintenanceType'],
                    'DBNAMES': self.tcinputs['DatabaseName']
                }
            )
        except Exception as err:
            self.storeutils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            workflow_helper.delete(self.workflow_id)
