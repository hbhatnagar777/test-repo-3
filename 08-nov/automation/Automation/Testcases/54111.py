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
from AutomationUtils.options_selector import OptionsSelector
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.Security.userhelper import UserHelper
from Server.Security.userconstants import USERGROUP

_STORE_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing Software store workflow  Check Password Complexity"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate Check Password Complexity workflow"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.browser = None
        self.webconsole = None
        self.store = None
        self.storeutils = StoreUtils(self)
        self.workflow = "Check Password Complexity"

    def init_tc(self):
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

    def run(self):
        """Main function for test case execution"""

        try:
            workflow_name = self.workflow
            wrong_password = _STORE_CONFIG.Workflow.ComplexPasswords.WrongPassword  # Less than 5 digit
            right_password = _STORE_CONFIG.Workflow.ComplexPasswords.RightPassword  # Greater than 6 digit
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.commcell.workflows.refresh()

            # ---------------------------------------------------------------------------------------------------------
            # Class Initializations
            workflow_helper = WorkflowHelper(self, workflow_name, deploy=False)
            workflow_helper.test.log_step("""
                Validate if the business logic workflow CreatePasswordComplexity is deployed
                Change workflow configuration to check for minimum 5 digit in the password
                Create user with password with less than 5 digits in the password
                User creation should be blocked.
                Create user with more than 5 digits in the password
                User creation should go through
                Delete the user
            """, 200)
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Validate if the business logic workflows CreatePasswordComplexity worklflow is deployed
                Change workflow configuration to check for minimum 5 digit in the password
            """)
            workflow_helper.is_deployed(workflow_name)
            config_xml = """<NumOfDigitsToCheckInPassword>5</NumOfDigitsToCheckInPassword>
                <NumOfSpecialCharsToCheckInPassword>0</NumOfSpecialCharsToCheckInPassword>
                <NumOfLowerCaseCharsToCheckInPassword>0</NumOfLowerCaseCharsToCheckInPassword>
                <NumOfUpperCaseCharsToCheckInPassword>0</NumOfUpperCaseCharsToCheckInPassword>
                <MinCharsInPassword>8</MinCharsInPassword>
                <MaxCharsInPassword>24</MaxCharsInPassword>
                <RegularExpressionToMatchPassword></RegularExpressionToMatchPassword>
            """
            workflow_helper.modify_workflow_configuration(config_xml)
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Create user with password with less than 5 digits in the password
                User creation should be blocked.
                Create user with more than 5 digits in the password
                User creation should go through
                Delete the user
            """)
            username = 'workflow_' + OptionsSelector.get_custom_str()
            user_helper = UserHelper(self._commcell)
            try:
                self.log.info("Attempting to create user with password not matching criterion (< 5 digits)")
                self.log.info("With user password [{0}]".format(wrong_password))
                user_helper.create_user(user_name=username, full_name=username, email=username+'@commvault.com',
                                        password=wrong_password, local_usergroups=[USERGROUP.MASTER])
                raise Exception("User created successfully. Expected to be blocked from business logic workflow")
            except Exception as excp:
                if 'Password should contain minimum' in str(excp):
                    self.log.info("Error as expected: [{0}]".format(str(excp)))
                    self.log.info("User creation successfully blocked through business logic workflow.")
                else:
                    self.log.error(str(excp))
                    raise Exception("Business logic validation failed")
            self.commcell.users.refresh()
            assert not self.commcell.users.has_user(username), "Failed!! .. User created. Should have been blocked."

            self.log.info("With user password [{0}]".format(right_password))
            user_helper.create_user(user_name=username, full_name=username, email=username+'@commvault.com',
                                    password=right_password, local_usergroups=[USERGROUP.MASTER])
            self.commcell.users.refresh()
            assert self.commcell.users.has_user(username), "User does not exist on commcell."

        except Exception as excp:
            self.storeutils.handle_testcase_exception(excp)
            workflow_helper.test.fail(excp)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            WorkflowHelper(self, workflow_name, deploy=False).delete(workflow_name)
            UserHelper(self.commcell).delete_user(user_name=username, new_user='admin')
