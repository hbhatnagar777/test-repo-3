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

from time import sleep
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.WebConsole.Forms.forms import Forms
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from Server.Workflow.workflowhelper import WorkflowHelper

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing store workflow CommServe Port Forwarding Gateway"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("WORKFLOW - [Software Store] Validate CommServe "
                     "Port Forwarding Gateway")
        self.browser = None
        self.webconsole = None
        self.store = None
        self.workflow = "CommServe Port Forwarding Gateway"
        self._workflow = None
        self.forms = None

    def init_tc(self):
        """Login to store"""
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

    @test_step
    def install_workflow(self):
        """Install status should be shown for workflow
        when it is not installed"""
        pkg_status = self.store.get_package_status(
            self.workflow,
            category="Workflows"
        )
        if pkg_status == "Open":
            pass
        elif pkg_status == "Install":
            self.store.install_workflow(
                self.workflow, refresh=True
            )
        else:
            raise CVTestStepFailure(
                f"[{self.workflow}] does "
                f"not have [Install] status, found [{pkg_status}]"
            )

    @test_step
    def open_workflow(self):
        """When clicked on Open, workflow form should open """
        self.store.open_package(
            self.workflow,
            category="Workflows"
        )
        self.forms = Forms(self.webconsole)

        self._workflow = WorkflowHelper(self, self.workflow, deploy=False)
        if self.forms.is_form_open(self.workflow) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.workflow}]"
            )
    
    @test_step
    def execute_workflow(self):
        """Workflow Execution Start"""
        self.forms.select_radio_value(
            "Select operation to be performed",
            "Insert port forwarding configuration"
        )
        self.forms.click_action_button("OK")
        sleep(3)

        self.forms.select_dropdown("Select Client", self.commcell.commserv_name)
        self.forms.click_action_button("Next")
        sleep(3)

        web_option = self.forms.get_dropdown_list_value("POP1_WEBC_TO_CS_CLIENTS", "for")
        if web_option:
            self.forms.set_boolean("Webconsole to Webserver", "true")
            self.forms.select_dropdown_list_value("POP1_WEBC_TO_CS_CLIENTS", web_option, "for")

        gui_option = self.forms.get_dropdown_list_value("POP1_JAVAG_TO_CS_CLIENTS", "for")
        if gui_option:
            self.forms.set_boolean("Java GUI to Commserve", "true")
            self.forms.select_dropdown_list_value("POP1_JAVAG_TO_CS_CLIENTS", gui_option, "for")

        if web_option or gui_option:
            self.forms.select_checkbox_value(
                "Select port forwarding configuration:",
                "Select and assign common configuration to all clients"
            )
            self.forms.click_action_button("Next")
            sleep(5)

            self.forms.click_action_button("Submit")
            sleep(3)

            if web_option:
                self.forms.set_textbox_value("Provide source port:", "8888")
                self.forms.click_action_button("Submit")
                sleep(60)

            if gui_option:
                self.forms.set_textbox_value("Provide source port:", "8888")
                self.forms.click_action_button("Submit")
            self._workflow.workflow_job_status(self.workflow)

            self.check_network_summary(web_option, gui_option)
        else:
            self.forms.close_form()

    def check_network_summary(self, web_option, gui_option):
        """Checking network summary for clients to verify TPPM settings"""
        commsereve_net_summary = self.commcell.clients.get(self.commcell.commserv_name).get_network_summary()
        if web_option:
            if commsereve_net_summary.find("acl clnt=* dst=@self@ ports=81") == -1:
                raise Exception("TPPM did not set properly for webserver")
            for option in web_option:
                client_obj = self.commcell.clients.get(option).get_network_summary()
                if client_obj.find("tppm src=8888 dst=81") == -1:
                    raise Exception("TPPM did not set properly for webserver")

        if gui_option:
            if commsereve_net_summary.find("acl clnt=* dst=@self@ ports=8401") == -1:
                raise Exception("TPPM did not set properly for JAVA GUI")
            for option in gui_option:
                client_obj = self.commcell.clients.get(option).get_network_summary()
                if client_obj.find("tppm src=any:8888 dst=8401") == -1:
                    raise Exception("TPPM did not set properly for JAVA GUI")
    @test_step
    def delete_TPPM(self):
        """Clean up phase"""
        self.forms.select_radio_value(
            "Select operation to be performed",
            "Delete port forwarding configuration"
        )

        self.forms.click_action_button("OK")
        sleep(3)

        self.forms.select_checkbox_value("Select connections to delete", "Select All")
        self.forms.click_action_button("Submit")

        self._workflow.workflow_job_status(self.workflow)

    def set_TPPM(self):
        """Set TPPM through workflow"""
        self.init_tc()
        self.install_workflow()
        self.open_workflow()
        self.execute_workflow()
        
    def clean_phase(self):
        """Removes the TPPM through workflow"""
        self.forms = Forms(self.webconsole)
        self.forms.open_workflow(self.workflow)
        if self.forms.is_form_open(self.workflow) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.workflow}]"
            )

        self.delete_TPPM()


        

    def run(self):
        try:    
            self.set_TPPM()
            self.clean_phase()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            self._workflow.delete(self.workflow)
