# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initialize TestCase class

    setup()                 --  initial settings for the test case

    init_workflow()         --  initialize the required Workflow for execution.

    run()                   --  run function of this test case
"""

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils.constants import CONFIG_FILE_PATH
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import CVTestStepFailure
from Web.WebConsole.Forms.forms import Forms
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from Server.serverhelper import ServerTestCases

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing of workflow CCM-ClientByStoragePolicy testcase """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [Software Store] - Validate CCM-ClientByStoragePolicy workflow"
        self.workflow = "CCM-ClientByStoragePolicy"
        self.workflow_id = "CCM-ClientByStoragePolicy"
        self.browser = None
        self.server = None
        self._workflow = None
        self.webconsole = None
        self.store = None
        self.storeutils = None
        self.tcinputs = {
            "StoragePolicy": None,
            "ExportLocation": None
        }

    def setup(self):
        """Setup function of this testcase"""

        self.server = ServerTestCases(self)
        self.storeutils = StoreUtils(self)

    def init_workflow(self):
        """Check the status of the workflow and
        perform action accordingly"""
        username = _STORE_CONFIG.Cloud.username
        password = _STORE_CONFIG.Cloud.password
        if not username or not password:
            self.log.info("Cloud username and password are not configured in config.json")
            raise Exception("Cloud username and password are not configured."
                            " Please update creds under {0}".format(CONFIG_FILE_PATH))

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

        workflow_status = self.store.get_package_status(
            self.workflow,
            category="Workflows"
        )
        if workflow_status != "Install":
            raise CVTestStepFailure(
                f"[{self.workflow}] does "
                f"not have [Install] status, found [{workflow_status}]"
            )

    def run(self):
        """Main function for test case execution"""

        try:
            self.init_workflow()
            self.store.install_workflow(self.workflow,
                                        refresh=True)
            self.store.open_package(self.workflow,
                                    category="Workflows")
            forms = Forms(self.webconsole)
            if forms.is_form_open(self.workflow_id) is False:
                raise CVTestStepFailure(
                    f"Forms page is not loaded on clicking Workflow : [{self.workflow_id}]"
                )
            forms.select_dropdown_list_value("Select Storage Policy for Migration",
                                             [self.tcinputs["StoragePolicy"]])
            forms.set_textbox_value("Export Location", self.tcinputs["ExportLocation"])
            forms.submit()
            if forms.is_form_open("Information ") is False:
                raise CVTestStepFailure("Information message is not displayed upon submitting")
            forms.submit()

        except Exception as excp:
            self.server.fail(excp)
        finally:
            self.storeutils.delete_workflow(self.workflow_id)
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)