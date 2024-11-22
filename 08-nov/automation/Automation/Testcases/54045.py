# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from cvpysdk.commcell import Commcell
from cvpysdk.security.user import User
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Reports.storeutils import StoreUtils
from Server.Security.userhelper import UserHelper
from Server.Workflow.workflowhelper import WorkflowHelper
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [Software Store] Validate Check Duplicate Email ID workflow"
        self.browser = None
        self.webconsole = None
        self.store = None
        self.workflow_id = "Check Duplicate Email ID"
        self.workflow_name = "Check Duplicate Email ID "
        self.show_to_user = False
        self.tcinputs = {
            'EmailId1': None,
            'EmailId2': None
        }
        self.storeutils = None

    def init_tc(self):
        """Initialize the webconsole Object"""
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
            self.workflow_id,
            category="Workflows"
        )
        if pkg_status != "Install":
            raise CVTestStepFailure(
                f"[{self.workflow_id}] does "
                f"not have [Install] status, found [{pkg_status}]"
            )

    @test_step
    def start_step2(self):
        """Install Workflow"""
        self.store.install_workflow(
            self.workflow_id, refresh=True
        )

    @test_step
    def start_step3(self):
        """When clicked on Open, workflow form should open """
        self.store.open_package(
            self.workflow_id,
            category="Workflows"
        )

    def run(self):
        try:
            workflow_helper = WorkflowHelper(self, self.workflow_id, deploy=False)
            self.init_tc()
            user1 = '{0}_Automation_User1'.format(self.id)
            user2 = '{0}_Automation_User2'.format(self.id)
            user_helper = UserHelper(self.commcell)
            self.start_step1()
            self.start_step2()
            self.start_step3()
            password = _STORE_CONFIG.Workflow.ComplexPasswords.CommonPassword
            user_helper.create_user(user_name=user1, full_name=user1, password=password,
                                    email=self.tcinputs['EmailId1'])
            try:
                self.log.info("Validation through REST API")
                self.log.info("Attempting to create user [%s] with duplicate emailId", user2)
                user_helper.create_user(user_name=user2, full_name=user2, password=password,
                                        email=self.tcinputs['EmailId1'])
            except Exception as excp:
                if 'Duplicate Email ID already present in Database' in str(excp):
                    self.log.info(
                        "User Creation with Duplicate Email ID is blocked as expected from business logic workflow")
                else:
                    self.log.error(str(excp))
                    raise Exception("Validation of create user with duplicate Email id is failed")
            user_helper.create_user(user_name=user2, full_name=user2, password=password,
                                    email=self.tcinputs['EmailId2'], local_usergroups=['master'])
            try:
                self.log.info("Validation through REST API")
                self.log.info("Attempting to modify user[%s] with duplicate emailId", user2)
                user2_commcell = Commcell(self.commcell.commserv_name, user2, password)
                user2_userobj = User(user2_commcell, user_name=user2)
                user2_userobj.email = self.tcinputs['EmailId1']
                raise Exception("User emailId modified successfully. Expected to restrict from business logic workflow")
            except Exception as excp:
                self.log.info("Exception raised is %s", excp)
                if 'Duplicate Email ID already present in Database' in str(excp):
                    self.log.info(
                        "User modification with Duplicate Email ID is blocked as expected from business logic workflow")
                else:
                    self.log.error(str(excp))
                    raise Exception("Validation of modify user with duplicate Email id is failed")

        except Exception as err:
            self.storeutils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            workflow_helper.delete(self.workflow_name)
            user_helper.delete_user(user1, new_user='admin')
            user_helper.delete_user(user2, new_user='admin')
