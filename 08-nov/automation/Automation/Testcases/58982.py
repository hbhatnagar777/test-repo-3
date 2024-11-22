# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify overview dashboard page loading without any errors."""
import random

from cvpysdk.commcell import Commcell

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.metallic_helper import MetallicMain

from Reports.utils import TestCaseUtils

class TestCase(CVTestCase):
    """Test case to verify User redirection and security validations after on-prem CS
    subscribes to metallic services"""
    test_step = TestStep()

    def __init__(self):
        super().__init__()
        self.name = ("User redirection and security validations after on-prem CS "
                     "subscribes to metallic services")
        self.tcinputs = {
            "OnPremCS": None,
            "OnPremUserName": None,
            "OnPremPassword": None,
            "CloudCompanyName": None,
            "CloudCompanyUsername": None,
            "CloudCompanyPassword": None,
        }
        self.browser = None
        self.admin_console = None
        self.onprem_cs_obj = None
        self.metallic_helper_obj = None
        self.solutions_marked_completed = None
        self.utils = TestCaseUtils(self)

        # Setup Variables
        self.user1 = None
        self.user1_email = None
        self.user2 = None
        self.user2_email = None
        self.strong_password = None
        self.admin_mgmt_role = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # Test Case constants
        self.user1 = f'{self.id}user1'
        self.user1_email = f'{self.id}user1@domain.com'
        self.user2 = f'{self.id}user2'
        self.user2_email = f'{self.id}user2@domain.com'
        self.strong_password = '#####'
        self.admin_mgmt_role = [f'{self.id}amrole',['Administrative Management']]

    def login_to_on_prem_cs(self, logout_first=False, username=None, password=None):
        """Login to OnpremCS"""
        if logout_first:
            self.admin_console.logout()
        if not username:
            username = self.tcinputs['OnPremUserName']
        if not password:
            password = self.tcinputs['OnPremPassword']
        self.admin_console = AdminConsole(self.browser, self.tcinputs['OnPremCS'])
        self.admin_console.login(username=username, password=password)

    def init_tc(self):
        """Initialize browser and redirect to page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.login_to_on_prem_cs()
            self.onprem_cs_obj = Commcell(self.tcinputs['OnPremCS'],
                                          self.tcinputs['OnPremUserName'],
                                          self.tcinputs['OnPremPassword'])
            self.metallic_helper_obj = MetallicMain(self.admin_console)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def cleanup(self):
        """Cleanup function to run before and after test steps"""
        self.metallic_helper_obj.getting_started.navigate_to_metallic()
        if self.metallic_helper_obj.getting_started.get_metallic_link_status():
            self.metallic_helper_obj.getting_started.unlink_metallic_account()
        self.metallic_helper_obj.delete_additional_settings(self.onprem_cs_obj)
        for user in [self.user1, self.user2]:
            if self.onprem_cs_obj.users.has_user(user):
                self.onprem_cs_obj.users.delete(user, new_user=self.tcinputs['OnPremUserName'])
        if self.onprem_cs_obj.roles.has_role(self.admin_mgmt_role[0]):
            self.onprem_cs_obj.roles.delete(self.admin_mgmt_role[0])

    def pre_requisites_tc(self):
        """Pre requisites before the test steps begin"""
        self.metallic_helper_obj.add_additional_settings(
            self.onprem_cs_obj, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.onprem_cs_obj.roles.add(self.admin_mgmt_role[0], self.admin_mgmt_role[1])
        users_dict = {self.user1:self.user1_email,self.user2:self.user2_email}
        for user_name, email in users_dict.items():
            self.onprem_cs_obj.users.add(user_name, email, password=self.strong_password)

    def associate_user_with_admin_mgmt_rights(self, user_name):
        """Associating given user with administrative rights"""
        self.metallic_helper_obj.update_users_with_roles(
            self.onprem_cs_obj, [user_name], [self.admin_mgmt_role[0]],'UPDATE')

    def dissociate_user_with_admin_mgmt_rights(self, user_name):
        """Dissociating given user with administrative rights"""
        self.metallic_helper_obj.update_users_with_roles(
            self.onprem_cs_obj, [user_name], [self.admin_mgmt_role[0]],'DELETE')

    def delete_on_prem_user_on_metallic(self, user_name):
        """Deletes on prem user which got created on metallic"""
        self.commcell.users.delete(
            self.tcinputs['CloudCompanyName']+'\\'+user_name,
            new_user=self.tcinputs['CloudCompanyUsername'])

    def add_users_to_metallic_service_commcell(self, users):
        """Adds the given list of users to Metallic Service Commcell"""
        self.admin_console.navigator.navigate_to_service_commcell()
        self.metallic_helper_obj.service_commcell.select_service_commcell(
            self.metallic_helper_obj.metallic_name)
        self.metallic_helper_obj.service_commcell.associate_entities(users)

    @test_step
    def register_to_metallic(self):
        """Register to metallic services"""
        self.metallic_helper_obj.getting_started.navigate_to_metallic()
        self.metallic_helper_obj.getting_started.link_metallic_account(
            self.tcinputs['CloudCompanyUsername'], self.tcinputs['CloudCompanyPassword'])

    @test_step
    def verify_metallic_navigation_tile_not_found(self):
        """Verifies metallic navigation tile visibility on the left navigation bar"""
        if self.metallic_helper_obj.metallic.get_metallic_navigation_status():
            raise CVTestStepFailure("Metallic navigation found")

    @test_step
    def verify_metallic_solution_redirect(self, user_name):
        """Verifies if a randomly selected solution is redirected to metallic"""
        self.admin_console.navigator.navigate_to_metallic()
        if not self.metallic_helper_obj.verify_solutions_redirect(
            [random.choice(self.metallic_helper_obj.metallic.get_solutions())],
            hostname=self.inputJSONnode['commcell']['webconsoleHostname'],
            username=self.tcinputs['CloudCompanyName']+'\\'+user_name,
            service_commcell_name=self.metallic_helper_obj.metallic_name):
            raise CVTestStepFailure("Solution redirect validation failed")

    @test_step
    def verify_users_in_tenant_admin_group(self, users):
        """Verifies if the given users are part of tenant admin group of the company"""
        tenant_admin_group = (
            self.tcinputs['CloudCompanyName']+'\\'+self.metallic_helper_obj.tenant_admin)
        users = [self.tcinputs['CloudCompanyName']+'\\'+user for user in users]
        if not self.metallic_helper_obj.verify_users_in_user_group(
            self.commcell, tenant_admin_group, users):
            raise CVTestStepFailure("User/s not part of the tenant admin group")

    @test_step
    def verify_users_in_tenant_user_group(self, users):
        """Verifies if the given users are part of tenant user group of the company"""
        tenant_users_group = (
            self.tcinputs['CloudCompanyName']+'\\'+self.metallic_helper_obj.tenant_users)
        users = [self.tcinputs['CloudCompanyName']+'\\'+user for user in users]
        if not self.metallic_helper_obj.verify_users_in_user_group(
            self.commcell, tenant_users_group, users):
            raise CVTestStepFailure("User/s not part of the tenant users group")

    @test_step
    def unregister_to_metallic(self):
        """Unregister to metallic services"""
        self.metallic_helper_obj.getting_started.unlink_metallic_account()

    @test_step
    def verify_login_redirection_from_cloud_to_on_prem(self, username, password):
        """ Verify onprem user authentication redirection from cloud to onprem"""
        self.admin_console = AdminConsole(
            self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        username = self.tcinputs['CloudCompanyName']+'\\'+username
        self.admin_console.login(username=username, password=password,
                                 on_prem_redirect_hostname=self.tcinputs['OnPremCS'])
        cs_items = {'hostname': self.inputJSONnode['commcell']['webconsoleHostname']}
        if not self.metallic_helper_obj.validate_commcell(cs_items):
            raise CVTestStepFailure("Metallic Cloud Redirection Failed")
        self.admin_console.goto_adminconsole()

    def run(self):
        try:
            self.init_tc()
            self.cleanup()
            self.pre_requisites_tc()
            self.associate_user_with_admin_mgmt_rights(self.user1)
            self.login_to_on_prem_cs(True, self.user1, self.strong_password)
            self.register_to_metallic()
            self.verify_metallic_navigation_tile_not_found()
            self.login_to_on_prem_cs(logout_first=True)
            self.add_users_to_metallic_service_commcell([self.user1,self.user2])
            self.login_to_on_prem_cs(True, self.user1, self.strong_password)
            self.verify_metallic_solution_redirect(self.user1)
            self.verify_users_in_tenant_admin_group([self.user1])
            self.login_to_on_prem_cs(True, self.user2, self.strong_password)
            self.verify_metallic_solution_redirect(self.user2)
            self.verify_users_in_tenant_user_group([self.user2])
            self.dissociate_user_with_admin_mgmt_rights(self.user1)
            self.associate_user_with_admin_mgmt_rights(self.user2)
            self.verify_metallic_solution_redirect(self.user2)
            self.verify_users_in_tenant_admin_group([self.user2])
            self.login_to_on_prem_cs(True, self.user1, self.strong_password)
            self.verify_metallic_solution_redirect(self.user1)
            self.verify_users_in_tenant_user_group([self.user1])
            self.delete_on_prem_user_on_metallic(self.user1)
            self.verify_metallic_solution_redirect(self.user1)
            self.verify_users_in_tenant_user_group([self.user1])
            self.admin_console.logout()
            self.verify_login_redirection_from_cloud_to_on_prem(self.user1, self.strong_password)
            self.login_to_on_prem_cs(logout_first=True)
            self.unregister_to_metallic()
            self.cleanup()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
