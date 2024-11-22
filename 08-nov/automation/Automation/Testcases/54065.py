# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 54065

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
from cvpysdk.commcell import Commcell
from Server.Security.userhelper import UserHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.cvhelper import format_string
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
from AutomationUtils.constants import CONFIG_FILE_PATH
from Web.AdminConsole.adminconsole import AdminConsole

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for validating the execution of Store Workflow Reissuing Secret Key"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [Software Store] Validate Reissuing Secret Key workflow"
        self.browser = None
        self.webconsole = None
        self.adminconsole = None
        self.store = None
        self.workflow = "Reissuing Secret Key"
        self.workflow_id = "Reissuing Secret key"
        self._workflow = None
        self.show_to_user = False
        self.tcinputs = {
            'EmailId': None
        }

    def init_tc(self):
        """Setup function for this testcase"""
        try:
            self.storeutils = StoreUtils(self)
            username = _STORE_CONFIG.Cloud.username
            password = _STORE_CONFIG.Cloud.password
            if not username or not password:
                self.log.info("Cloud username and password are not configured in config.json")
                raise Exception("Cloud username and password are not configured. Please update creds under {0}".format(
                    CONFIG_FILE_PATH))
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
        """Install Workflow"""
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
        """Main funtion for testcase execution"""
        try:
            workflow_helper = WorkflowHelper(self, self.workflow_id, deploy=False)
            self.init_tc()
            user1 = '{0}_Automation_User1'.format(self.id)
            user_helper = UserHelper(self.commcell)
            self.start_step1()
            self.start_step2()
            self.start_step3()
            password = _STORE_CONFIG.Workflow.ComplexPasswords.CommonPassword
            user_helper.create_user(user_name=user1, full_name=user1, password=password,
                                    email=self.tcinputs['EmailId'], local_usergroups=['master'])
            self.log.info("Attempt to enable two factor authentication")
            user1_commcell = Commcell(self.commcell.commserv_name, user1, password)
            user1_workflow = WorkflowHelper(self, self.workflow_id, deploy=False, commcell=user1_commcell)
            user_helper.enable_tfa()
            user_helper.gui_login(self.commcell.commserv_hostname, user1, password)
            query = "select UP.attrVal from UMUsersProp UP inner join UMUsers U on UP.componentNameId=U.id " \
                    "where UP.attrName='secret' " \
                    "and U.login='{0}'".format(user1)
            self.csdb.execute(query)
            row = self.csdb.fetch_one_row()
            secret_key = format_string(self.commcell, row[0])
            self.log.info("Secret Key before Workflow execution {0}".format(secret_key))
            user1_workflow.execute()
            self.log.info("Trying to GUI login after the workflow execution")
            user_helper.gui_login(self.commcell.commserv_hostname, user1, password)
            self.csdb.execute(query)
            modified_row = self.csdb.fetch_one_row()
            modified_secret_key = format_string(self.commcell, modified_row[0])
            self.log.info("Modified Secret key after workflow execution {0}".format(modified_secret_key))
            if modified_secret_key not in secret_key:
                self.log.info("New Secret key is generated successfully for the user [{0}]".format(user1))
            else:
                raise Exception("New Secret key is not generated after the workflow execution")
        except Exception as err:
            self.storeutils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            user_helper.disable_tfa()
            workflow_helper.delete(self.workflow_id)
            user_helper.delete_user(user1, new_user='admin')
