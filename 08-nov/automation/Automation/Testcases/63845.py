# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Metrics : Singlecompany
Inputs to the testcase-
    "customer_user":"<Group admin user>",
    "password":"<pwd>",
    "commcell_to_add" : "<Commcell to add while creating>",
    "commcell" : "<Commcell to add while editing>"
"""
import re
from time import sleep
from cvpysdk.security.user import Users as UserApi
from cvpysdk.security.user import User

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard, Users

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.user_obj = None
        self.user = None
        self.dashboard = None
        self.name = "Metrics : Single Company validation"
        self.navigator = None
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.company_name = 'Single_CS_Automation'
        self.temp_user = {
            'user_name': 'dummy_63845',
            'email': 'dummy_63845@automation1.com'
        }
        self.temp_user2 = {
            'user_name': 'dummy2_63845',
            'email': 'dummy2_63845@automation1.com'
        }
        self.tcinputs = {
            "user_name": None,
            "email": None
        }

    def cleanup(self, temp_user_name):
        """
        cleanup the existing users in the company
        """
        user = UserApi(self.commcell)
        if user.has_user(temp_user_name):
            user.delete(temp_user_name, 'admin')
        self.log.info(f"Successfully delete user {temp_user_name}")

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.navigator = Navigator(self.webconsole)
            self.webconsole.login(
                self.tcinputs['customer_user'],
                self.tcinputs['password']
            )
            self.dashboard = Dashboard(self.webconsole)
            self.webconsole.goto_commcell_dashboard()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_user_from_dashboard(self, temp_email):
        """Verify user management from dashboard"""
        self.verify_user_associated(temp_email)
        self.mark_user_admin(temp_email)
        self.mark_user_non_admin(temp_email)

    def verify_user_associated(self, temp_email):
        """Verify created user is associated to the commcell group dashboard"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        if temp_email not in user.get_users():
            raise CVTestStepFailure(
                f"user with email {temp_email} is not associated with new "
                f"company [{self.company_name}]"
            )
        self.log.info(f"Verified that user {self.temp_user['email']} is associated with {self.company_name} company")
        user.close_users_panel()

    @test_step
    def add_user_from_singe_cs_dashboard(self, temp_user, temp_email):
        """ Add user from dashboard"""
        self.log.info("Adding a user to dashboard")
        self.dashboard.access_add_user()
        user = Users(self.webconsole)
        user.add_user(temp_user, temp_email)
        expected_msg = (
            "The information you provided is being verified."
            " The new user will be notified via email once the account is created.")
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info("wait for 1 minutes to sync updates")
        sleep(40)
        self.log.info(f"Added user {temp_user} from Company dashboard")

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
    def add_user_from_dashboard(self, user_name, email_id):
        """Verify adding user from dashboard"""
        self.log.info("Adding a user to dashboard")
        self.dashboard = Dashboard(self.webconsole)
        self.dashboard.access_add_user()
        user = Users(self.webconsole)
        user.add_user(user_name, email_id)
        expected_msg = (
            "The information you provided is being verified."
            " The new user will be notified via email once the account is created.")
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info("wait for 1 minutes to sync updates")
        sleep(40)
        self.log.info(f"Added user {user_name} from Company dashboard")

    def run(self):
        try:
            self.init_tc()
            self.log.info("Logging using Commcell Group admin user to verify add/remove user")
            # add user from singe company landing page
            self.add_user_from_singe_cs_dashboard(self.temp_user['user_name'], self.temp_user['email'])
            self.verify_user_from_dashboard(self.temp_user['email'])
            self.cleanup(self.temp_user['user_name'])
            self.dashboard.access_commcell_count()
            self.navigator.goto_worldwide_dashboard()
            self.add_user_from_dashboard(self.tcinputs['user_name'], self.tcinputs['email'])
            self.verify_user_from_dashboard(self.tcinputs['email'])
            self.cleanup(self.tcinputs['user_name'])
            current_URL = self.webconsole.browser.driver.current_url
            new_url = re.sub('[commUniId]+=[0-9]+&', '', current_URL)
            self.browser.driver.get(new_url)
            self.webconsole.wait_till_load_complete()
            self.add_user_from_dashboard(self.temp_user2['user_name'], self.temp_user2['email'])
            self.verify_user_from_dashboard(self.temp_user2['email'])
            self.cleanup(self.temp_user2['user_name'])
            self.webconsole.logout(timeout=100)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
