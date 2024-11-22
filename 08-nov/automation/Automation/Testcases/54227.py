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
from AutomationUtils.options_selector import CVEntities
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
    """Class for executing store workflow Delete Client Level Additional Ports"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [Software Store]- Check Linux Client 1-Touch Readiness "
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser = None
        self.webconsole = None
        self.store = None
        self.storeutils = StoreUtils(self)
        self.workflow = "Check Linux Client 1-Touch Readiness"
        self.workflow_id = "Check Linux Client 1-Touch Readiness"
        self._workflow = None
        self.entities = None

    def init_tc(self):
        """Login to store"""
        try:
            self.entities = CVEntities(self)
            inputs = self.tcinputs
            self.ClientGroup = inputs['ClientGroup']
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
        if forms.is_form_open(self.workflow_id) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.workflow}]"
            )
        forms.close_form()

    def run(self):
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()
            self._workflow = WorkflowHelper(self, self.workflow_id, deploy=False)
            workflow_inputs = {

                'ClientGroupName': self.tcinputs['ClientGroup']
            }
            self._workflow.execute(workflow_inputs, wait_for_job=True)

        except Exception as err:
            self.storeutils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            self._workflow.delete(self.workflow_id)
            self.entities.cleanup()
