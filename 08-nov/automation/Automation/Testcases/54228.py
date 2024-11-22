# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

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

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [Software Store] - System Discovery for NAS"
        self.browser = None
        self.webconsole = None
        self.store = None
        self.workflow = "System Discovery for NAS"
        self.workflow_id = "System Discovery for NAS"
        self._workflow = None
        self.show_to_user = False
        #self.tcinputs = None


    def init_tc(self):
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
        return pkg_status


    @test_step
    def start_step2(self):
        """After installing workflow, status should be Open"""
        self.store.install_workflow(
            self.workflow, refresh=True
        )

    @test_step
    def start_step3(self):
        """Update the workflow and then status will be set to open """
        self.store.update_workflow(
            self.workflow,
        )

    def run(self):
        try:
            workflow_helper = WorkflowHelper(self, self.workflow_id, deploy=False)
            self.init_tc()
            pkg_status = self.start_step1()
            if pkg_status == "Install":
                self.start_step2()
            elif pkg_status == "Update":
                self.start_step3()
            self._workflow = WorkflowHelper(self, self.workflow_id, deploy=False)
            self._workflow.execute()

        except Exception as err:
            self.storeutils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            workflow_helper.delete(self.workflow_id)
