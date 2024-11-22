# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Metrics : SubCompany
Inputs to the testcase-
    "customer_user":"<Group admin user>",
    "password":"<pwd>",
    "commcell_to_add" : "<Commcell to add while creating>",
    "commcell" : "<Commcell to add while editing>"
"""

from time import sleep
from cvpysdk.security.usergroup import UserGroups
from cvpysdk.security.user import Users as UserApi

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Company.RegisteredCompanies import RegisteredCompanies
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard, Users

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics : Create/Edit/Delete SubCompany"
        self.navigator = None
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.sub_company_name = 'AutoSubCompany'
        self.prefix = 'CompanyAutomation'
        self.user_to_create = {
            'user_name': 'AutoSubNewUser',
            'email': 'Autosubnewuser@automation1.com'
        }
        self.temp_user = {
            'user_name': 'dummy_53829',
            'email': 'dummy_53829@automation1.com'
        }
        self.ug = None
        self.user = None
        self.dashboard = None
        self.reg_companies = None

    def setup(self):
        self.ug = UserGroups(self.commcell)
        self.user = UserApi(self.commcell)

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.navigator = Navigator(self.webconsole)
            self.reg_companies = RegisteredCompanies(self.webconsole)
            self.webconsole.login(
                self.tcinputs['customer_user'],
                self.tcinputs['password']
            )
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup(self):
        """
        cleanup the existing users in the company
        """
        grp_name = self.prefix + ' - ' + self.sub_company_name
        if self.ug.has_user_group(grp_name):
            self.ug.delete(grp_name, new_usergroup='master')
        if self.user.has_user(self.user_to_create['user_name']):
            self.user.delete(self.user_to_create['user_name'], 'admin')
        if self.commcell.client_groups.has_clientgroup(clientgroup_name=grp_name):
            self.commcell.client_groups.delete(grp_name)

    @test_step
    def create_subcompany(self):
        """Verify creating new Commcell Group as a Commcell Group admin user"""
        sub_company = self.reg_companies.create_company()
        sub_company.create(
            prefix=self.prefix,
            name=self.sub_company_name,
            commcells=[self.tcinputs['commcell_to_add']],
            users=[self.user_to_create]
        )
        expected_msg = (
            "Your request was submitted. It might take some time to process. "
            "After the CommCell group is created, you will receive a confirmation email. "
            "At that time, please log on to Web Console again to see the CommCell group."
        )
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info("wait for 2 minutes for registration to complete")
        sleep(60)
        self.sub_company_name = self.prefix + ' - ' + self.sub_company_name
        self.log.info("CommCell group created successfully.")
        self.log.info("New CommCell group name: " + self.sub_company_name)

    @test_step
    def verify_user_from_dashboard(self):
        """Verify user management from dashboard"""
        self.reg_companies.access_company(company_name=self.sub_company_name)
        self.dashboard = Dashboard(self.webconsole)
        sleep(2)  # for the menu to be available
        self.verify_admin_user()
        self.log.info(f"Verified that created user {self.user_to_create['email']} is marked as admin")
        self.add_user_from_dashboard()
        self.mark_user_admin(self.temp_user['email'])
        self.mark_user_non_admin(self.temp_user['email'])
        self.delete_user_from_dashboard(self.temp_user['email'])

    def verify_admin_user(self):
        """Verify created user is marked as admin user from dashboard"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        if self.user_to_create['email'] not in user.get_users():
            raise CVTestStepFailure(
                f"user with email {self.user_to_create['email']} is not associated with new "
                f"sub company [{self.sub_company_name}]"
            )
        email_id = self.user.get(self.tcinputs['customer_user']).email
        if not user.is_admin_user(email_id):
            raise CVTestStepFailure(f"Commcell group created user not associated as admin with"
                                    f" new Commcell group [{self.sub_company_name}]")
        user.close()
        self.log.info(f"Verified that user {self.tcinputs['customer_user']} is marked as admin user from dashboard")
        self.log.info(f"Verified that user {self.user_to_create['email']} is associated with subcompany")

    @test_step
    def add_user_from_dashboard(self):
        """Verify adding user from dashboard"""
        self.log.info("Adding a user to dashboard")
        self.dashboard.access_add_user()
        user = Users(self.webconsole)
        user.add_user(self.temp_user['user_name'], self.temp_user['email'])
        expected_msg = (
            "The information you provided is being verified."
            " The new user will be notified via email once the account is created.")
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info("wait for 2 minutes to sync updates")
        sleep(60)
        self.log.info(f"Added user {self.temp_user['user_name']} from Company dashboard")

    @test_step
    def mark_user_admin(self, email):
        """Verify user is marked as admin"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        user.make_user_admin(email)
        self.log.info(f"User {email} is marked as admin")

    @test_step
    def mark_user_non_admin(self, email):
        """Verify user is marked as non-admin"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        user.make_user_non_admin(email)
        self.log.info(f"User {email} is marked as Non-admin")

    @test_step
    def delete_user_from_dashboard(self, email):
        """Verify user is deleted"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        user.delete_user(email)
        expected_msg = "Successfully removed the user from customer group."
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info(f"User {email} is deleted from Dashboard")

    @test_step
    def edit_subcompany(self):
        """Editing Commcell group by adding commcell and user"""
        self.reg_companies.filter_by_company_name(self.sub_company_name)
        sub_company = self.reg_companies.edit_company(self.sub_company_name)
        sub_company.add_commcells([self.tcinputs['commcell']])
        sub_company.add_user(self.temp_user['user_name'], self.temp_user['email'])
        sub_company.update()
        expected_msg = (
            "Your request was submitted. It might take some time to process."
        )
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info("wait for 1 minutes for update workflow to complete")
        sleep(60)
        self.log.info(f"Edited Commcell Group {self.sub_company_name} successfully")

    @test_step
    def verify_subcompany_updated(self):
        """Verify commcell and user is added"""
        self.log.info('Validating commcell and user added to the commcell group')
        self.reg_companies.filter_by_company_name(self.sub_company_name)
        sub_company = self.reg_companies.edit_company(self.sub_company_name)
        commcells = sub_company.get_commcells()
        users = sub_company.get_associated_users()
        if self.temp_user['email'] not in users:
            raise CVTestStepFailure(
                f"Added user {self.temp_user['email']} doesn't exist "
                f"in Commcell group {self.sub_company_name}"
            )
        if self.tcinputs['commcell'] not in commcells:
            raise CVTestStepFailure(
                f"Added commcell {self.tcinputs['commcell']} doesn't exist "
                f"in Commcell group {self.sub_company_name}"
            )
        self.log.info(f"Verified that commcell {self.tcinputs['commcell']} and user {self.temp_user['email']} are "
                      f"added to commcell group")
        sub_company.cancel()

    @test_step
    def delete_from_subcompany(self):
        """Delete user and commcell from Commcell group"""
        sub_company = self.reg_companies.edit_company(self.sub_company_name)
        sub_company.delete_commcells([self.tcinputs['commcell']])
        sub_company.delete_user(self.temp_user['email'])
        sub_company.save_user()
        expected_msg = (
            "Your request was submitted. It might take some time to process."
        )
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info("wait for 1 minutes for update workflow to complete")
        sleep(60)
        self.log.info(f"Deleted commcell {self.tcinputs['commcell']} and user {self.temp_user['email']}"
                      f" from Commcell group successfully")

    @test_step
    def verify_deleted_entities(self):
        """Verify deleted user and commcell from Commcell group"""
        self.log.info('Validating user and commcell deleted from the Commcell group')
        sub_company = self.reg_companies.edit_company(self.sub_company_name)
        commcells = sub_company.get_commcells()
        users = sub_company.get_associated_users()
        if self.temp_user['email'] in users:
            raise CVTestStepFailure(
                f"Deleted user {self.temp_user['email']} still exists "
                f"in Commcell group {self.sub_company_name}"
            )
        if self.tcinputs['commcell'] in commcells:
            raise CVTestStepFailure(
                f"Deleted commcell {self.tcinputs['commcell']} still exists "
                f"in Commcell group {self.sub_company_name}"
            )
        sub_company.save_user()
        self.log.info(f"Verified that user{self.temp_user['email']} and commcell {self.tcinputs['commcell']} are "
                      f"deleted from the Commcell group")

    @test_step
    def delete_subcompany(self):
        """Delete Commcell group and verify user group and client group are also deleted"""
        self.reg_companies.filter_by_company_name(self.sub_company_name)
        self.reg_companies.delete_company(self.sub_company_name)
        grp_name = self.prefix + ' - ' + self.sub_company_name
        if self.ug.has_user_group(grp_name):
            raise CVTestStepFailure(
                f"Usergroup {grp_name} exists even after deleting Commcell group"
            )
        if self.commcell.client_groups.has_clientgroup(clientgroup_name=grp_name):
            raise CVTestStepFailure(
                f"Clientgroup {grp_name} exists even after deleting Commcell group"
            )

    def run(self):
        try:
            self.cleanup()
            self.init_tc()
            self.log.info("Creating a Commcell Group using Commcell Group admin user")
            self.create_subcompany()
            self.webconsole.logout(timeout=100)
            self.log.info("Logging using master admin and editing the created Commcell group")
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()
            self.edit_subcompany()
            self.webconsole.logout()
            self.log.info("Logging using Commcell Group admin user to verify changes")
            self.webconsole.login(
                self.tcinputs['customer_user'],
                self.tcinputs['password']
            )
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()
            self.verify_subcompany_updated()
            self.delete_from_subcompany()
            self.webconsole.logout()
            self.log.info("Logging back using Commcell Group admin user"
                          " for delete action to take effect")
            self.webconsole.login(
                self.tcinputs['customer_user'],
                self.tcinputs['password']
            )
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()
            self.verify_deleted_entities()
            # Verification from dashboard
            self.verify_user_from_dashboard()
            self.navigator.goto_companies()
            self.delete_subcompany()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
