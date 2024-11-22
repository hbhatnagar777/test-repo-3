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

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
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

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing store workflow CvNetworkTestTool Gui Workflow"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("WORKFLOW - [Software Store] Validate CvNetworkTestTool "
                     "Gui workflow")
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser = None
        self.webconsole = None
        self.store = None
        self.storeutils = StoreUtils(self)
        self.workflow = "CV Network Test Tool GUI"
        self.workflow_id = "CvNetworkTestTool Gui"
        self._workflow = None
        self.tcinputs = {
            "ClientModeClient": None,
            "ServerModeClient": None,
            "StoragePolicy": None
        }

    def init_tc(self):
        """Login to store"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])
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
        forms = Forms(self.webconsole)
        self._workflow = WorkflowHelper(self, self.workflow_id, deploy=False)
        if forms.is_form_open(self.workflow_id) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.workflow}]"
            )

        forms.select_dropdown("Mode of execution", "Host to Host")
        forms.click_action_button("OK")
        self.webconsole.wait_till_load_complete(overlay_check=True)

        # Mandatory inputs for the workflow
        forms.select_dropdown("Host 1 (Runs in Server Mode)",
                              self.tcinputs["ServerModeClient"])
        forms.select_dropdown("Host 2 (Runs in Client Mode)",
                              self.tcinputs["ClientModeClient"])

        # Optional inputs for the workflow
        forms.set_textbox_value("Buffer Size (in Bytes)",
                                self.tcinputs.get("BufferSize", "16384"))
        forms.set_textbox_value("Total Size (in MB)",
                                self.tcinputs.get("TotalSize", "390.625"))
        forms.set_textbox_value("Server Port",
                                self.tcinputs.get("ServerPort", "25000"))

        # Checkbox for firewall connect
        if self.tcinputs.get("FirewallConnectFlag", False):
            forms.select_checkbox_value("Use firewall connect")

            forms.set_textbox_value("First Buffer Delay",
                                    self.tcinputs.get("FirstBufferDelay", "0"))

            forms.set_textbox_value("Inter Buffer Delay",
                                    self.tcinputs.get("InterBufferDelay", "0"))

            forms.set_textbox_value("Bind to Inteface",
                                    self.tcinputs.get("BindToInterfaceHostToHost", ""))

            forms.set_textbox_value("Server Side Port",
                                    self.tcinputs.get("ServerSidePort", "25001"))

            forms.set_textbox_value("Client Side Port",
                                    self.tcinputs.get("ClientSidePort", "25002"))

        # Executing the workflow
        forms.click_action_button("OK")

        self._workflow.workflow_job_status(self.workflow_id)
        forms.open_workflow(self.workflow_id)
        if forms.is_form_open(self.workflow_id) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.workflow}]"
            )

        # Client to Media Agent type execution
        forms.select_dropdown("Mode of execution", "Client to MediaAgents")
        forms.click_action_button("OK")
        self.webconsole.wait_till_load_complete(overlay_check=True)
        forms.select_dropdown("Client", self.tcinputs["ClientModeClient"])
        forms.click_action_button("Next")
        self.webconsole.wait_till_load_complete(overlay_check=True)
        forms.select_dropdown("Storage Policy", "All Storage Policies")
        forms.click_action_button("Finish")
        self._workflow.workflow_job_status(self.workflow_id)
        forms.open_workflow(self.workflow_id)
        if forms.is_form_open(self.workflow_id) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.workflow}]"
            )
        # Media Agent in a Storage Policy
        forms.select_dropdown("Mode of execution", "MediaAgents in Storage Policy")
        forms.click_action_button("OK")
        self.webconsole.wait_till_load_complete(overlay_check=True)
        forms.select_dropdown("Storage Policy", self.tcinputs["StoragePolicy"])
        forms.click_action_button("Next")
        self.webconsole.wait_till_load_complete(overlay_check=True)
        forms.select_dropdown("Copy", "All Copies for the SP")
        forms.click_action_button("Finish")
        self._workflow.workflow_job_status(self.workflow_id)

    def run(self):
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()

        except Exception as err:
            self.storeutils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            self._workflow.delete(self.workflow_id)
