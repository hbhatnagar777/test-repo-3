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
from AutomationUtils.machine import Machine

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing store workflow Configure Third Party Connections"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("NFS ObjectStore - AD integration workflow")
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser = None
        self.webconsole = None
        self.store = None
        self.storeutils = StoreUtils(self)
        self.workflow = "AD Integration Of Linux Client"
        self.workflow_id = "Add Linux MA to AD"
        self._workflow = None
        self.pkg_status = None

        self.tcinputs = {
            "LinuxClientName": None,
            "SkipPreRequisites": None,
            "Realm":None,
            "NetBIOSName": None,
            "ADControllerHostname": None,
            "ADControllerIP": None,
            "ADDomainAdminUsername": None,
            "ADDomainAdminPassword": None
        }

    def init_tc(self):
        """Login to the Store"""

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
    def check_workflow_status(self):
        """Install, Open or Update status should be shown for the workflow"""

        pkg_status = self.store.get_package_status(
            self.workflow,
            category="Workflows"
        )
        if pkg_status == "Open" or "Install" or "Update":
            self.pkg_status = pkg_status
            return True
        else:
            raise CVTestStepFailure(
                f"[{self.workflow}] does "
                f"not have [Install] or [Open] status, found [{pkg_status}]"
            )

    @test_step
    def install_wf(self):
        """If the status is 'Install', then install the workflow"""

        self.webconsole.wait_till_load_complete()
        self.store.install_workflow(
            self.workflow, refresh=True
        )
        self.webconsole.wait_till_load_complete()
        self.store.open_package(
            self.workflow,
            category="Workflows"
        )

    @test_step
    def update_wf(self):
        """If the status is 'Update', the update the workflow"""

        self.webconsole.wait_till_load_complete()
        self.store.update_workflow(
            self.workflow
        )
        self.webconsole.wait_till_load_complete()
        self.store.open_package(
            self.workflow,
            category="Workflows"
        )

    @test_step
    def join_or_leave_domain(self, join_domain, skip_pre_req="true"):
        """Run the workflow. Fill the required inputs in the pop-up window and proceed"""

        self.forms = Forms(self.webconsole)
        if self.forms.is_form_open(self.workflow_id) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.workflow}]"
            )

        self.forms.click_action_button("OK")

        self.forms.select_dropdown("clientList", self.tcinputs["LinuxClientName"])

        if join_domain:
            # Set these options to join the domain
            self.forms.select_radio_value("Operation Type",
                                          "Join an existing Active Directory Domain")
            if skip_pre_req == "true":  # Else leave the checkbox unchecked
                self.forms.set_boolean("Skip Pre-requisites Check for Join operation", True)
        else:
            # Set this option to leave the domain
            self.forms.select_radio_value("Operation Type",
                                    "Revert all effects of Active Directory Domain Join operation")
        self.forms.set_textbox_value("Active Directory Realm", self.tcinputs["Realm"])
        self.forms.set_textbox_value("NetBIOS Name", self.tcinputs["NetBIOSName"])
        self.forms.set_textbox_value("AD Domain Controller Hostname",
                                     self.tcinputs["ADControllerHostname"])
        self.forms.set_textbox_value("AD Domain Controller IP Address",
                                     self.tcinputs["ADControllerIP"])
        self.forms.set_textbox_value("AD Domain Admin Username",
                                     self.tcinputs["ADDomainAdminUsername"])
        self.forms.set_textbox_value("AD Domain Admin User Password",
                                     self.tcinputs["ADDomainAdminPassword"])
        self.forms.click_action_button("OK")

    def is_client_in_domain(self):
        """Check if the Linux client is part of the given domain"""

        self.log.info("Checking if the client is in the domain")
        self.log.info("Running 'net ads info' command on the Linux client")
        output = self.machine_object.execute_command("net ads info")
        if output.formatted_output:
            self.log.info("The output of the command is: %s",
                          output.formatted_output)
            if output.formatted_output[2][1] == self.tcinputs["Realm"].upper():
                return True
        else:
            return False

    def run(self):
        try:
            self.init_tc()
            self._workflow = WorkflowHelper(self, self.workflow_id, deploy=False)
            self.machine_object = Machine(self.tcinputs["LinuxClientName"], self.commcell)

            self.log.info("Check for the workflow 'Add Linux MA to AD' from the commcell's"
                          " Software Store")
            self.check_workflow_status()
            if self.pkg_status == "Install":
                self.log.info("If the status is 'Install', then go ahead and install the workflow")
                self.install_wf()
                self.webconsole.wait_till_load_complete()  # Wait till Install completes
            elif self.pkg_status == "Update":  # If newer version is available on the Store
                self.log.info("If the status is 'Update', then go ahead and update the workflow")
                self.update_wf()
                self.webconsole.wait_till_load_complete()  # Wait till Update completes

            # Add the Linux client to the given domain
            self.webconsole.wait_till_load_complete()
            self.log.info("Adding the client to the given domain. Running the workflow")
            self.join_or_leave_domain(True, self.tcinputs["SkipPreRequisites"])  # Join domain
            self._workflow.workflow_job_status(self.workflow_id)
            if self.is_client_in_domain():
                self.log.info("Addition of the Linux client to the domain SUCCESS. "
                              "Proceeding to remove..")
            else:
                raise CVTestStepFailure(
                    f"Addition of the Linux client to the domain FAILED"
                )

            # Once addition to the domain is successful, proceed with removal.
            self.webconsole.wait_till_load_complete()
            self.forms.open_workflow(self.workflow_id)
            self.log.info("Removing the client from the given domain. Running the workflow.")
            self.join_or_leave_domain(False)  # Leave domain
            self._workflow.workflow_job_status(self.workflow_id)
            if not self.is_client_in_domain():
                self.log.info("The Linux client has been successfully REMOVED from the domain.")
            else:
                raise CVTestStepFailure(
                    f"Removal of the Linux client from the domain FAILED"
                )

        except Exception as err:
            self.storeutils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            self._workflow.delete(self.workflow_id)