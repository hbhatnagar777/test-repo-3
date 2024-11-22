# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Metrics : CASP Group testcase

Inputs to the testcase-
    "commcell_id":"<Commcell id of Commcell to add to casp group>",
    "linked_server" : "<linked server>",
    "casp_group" : "<casp group name>",
    "user_name" : "<user whihc is already part of 1 commcell>",
    "email" : "<email>",
    "password":"<pwd>"
"""

from time import sleep
from cvpysdk.security.user import Users as UserApi
from cvpysdk.security.user import User

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper

from Web.API.customreports import CustomReportsAPI

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.monitoringform import ManageCommcells
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Company.RegisteredCompanies import RegisteredCompanies
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard, Users
from Web.WebConsole.webconsole import WebConsole
from Reports.utils import TestCaseUtils
from Reports import reportsutils

REPORTS_CONFIG = reportsutils.get_reports_config()
_CONFIG = get_config()


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics : Casp Group"
        self.navigator = None
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.temp_user = {
            'user_name': 'dummy_58655',
            'email': 'dummy_58655@automation1.com'
        }
        self.workflow_name = 'Refresh CASP Companies'
        self.workflow_inputs = {"userEmail": _CONFIG.email.email_id}
        self.cre_api = None
        self.monitoring_form = None
        self.user = None
        self.user_obj = None
        self.dashboard = None
        self.reg_companies = None
        self._workflow = None
        self.tcinputs = {
            "commcell_id": None,
            "linked_server": None,
            "casp_group": None,
            "user_name": None,
            "email": None,
            "password": None
        }

    def setup(self):
        self.user = UserApi(self.commcell)
        self.user_obj = User(self.commcell, self.tcinputs['user_name'])

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self._workflow = WorkflowHelper(self, self.workflow_name, deploy=False)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.navigator = Navigator(self.webconsole)
            self.reg_companies = RegisteredCompanies(self.webconsole)
            self.webconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.cre_api = CustomReportsAPI(self.commcell.webconsole_hostname,
                                            username=self.inputJSONnode['commcell']["commcellUsername"],
                                            password=self.inputJSONnode['commcell']["commcellPassword"])
            self.utils = TestCaseUtils(self,
                                            username=self.inputJSONnode['commcell']["commcellUsername"],
                                            password=self.inputJSONnode['commcell']["commcellPassword"])
            self.dashboard = Dashboard(self.webconsole)
            self.monitoring_form = ManageCommcells(self.webconsole)
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup(self):
        """
        cleanup the existing users in the company
        """
        if self.user.has_user(self.temp_user['user_name']):
            self.user.delete(self.temp_user['user_name'], 'admin')
        if self.tcinputs['casp_group'] in self.user_obj.associated_usergroups:
            self.user_obj.remove_usergroups([self.tcinputs['casp_group']])

    @test_step
    def add_commcell_to_casp(self):
        """Add Commcells to casp group in license DB"""
        global_id = self.utils.get_account_global_id(self.tcinputs['casp_group'])
        query = f"""Update [{self.tcinputs['linked_server']}].[CvLicGen].dbo.LACCMCommCellinfo set 
                    SupportPartnerAccountGlobalId ={global_id} where COmmcellid = '{self.tcinputs['commcell_id']}' """
        self.log.info("Executing the query: [%s]", query)
        self.cre_api.execute_sql(query)
        self.log.info(f"Commcell {self.tcinputs['commcell_id']} is added to Casp group")

    @test_step
    def verify_commcells_in_casp(self, expected_commcells):
        """Verify expected commcells are present in commcell group"""
        actual_commcells = self.get_commcells_from_caspgroup()
        if sorted(expected_commcells) != sorted(actual_commcells):
            self.log.info(f"Expected Commcells : {expected_commcells}")
            self.log.info(f"Actual Commcells : {actual_commcells}")
            raise CVTestStepFailure(
                f"Expected Commcells are not present in Commcell Group"
            )
        self.log.info(f"Verified that expected commcells are present in commcell group")

    def get_commcells_from_caspgroup(self):
        """ Get Commcells in Commcell group from Commcell Groups listing"""
        self.log.info('Fetching Commcells in the commcell group')
        self.reg_companies.access_company(company_name=self.tcinputs['casp_group'])
        sleep(1)
        self.navigator.goto_commcells_in_group()
        sleep(2)
        company_commcells = self.monitoring_form.get_column_values('CommCell ID')
        return company_commcells

    @test_step
    def remove_commcell_from_casp(self):
        """Remove Commcell from casp group in license DB"""
        query = f"""Update [{self.tcinputs['linked_server']}].[CvLicGen].dbo.LACCMCommCellinfo set 
                           SupportPartnerAccountGlobalId =0 where COmmcellid = '{self.tcinputs['commcell_id']}' """
        self.log.info("Executing the query: [%s]", query)
        self.cre_api.execute_sql(query)
        self.log.info(f"Commcell {self.tcinputs['commcell_id']} is removed from Casp group")

    @test_step
    def verify_user_from_dashboard(self):
        """Verify user management from dashboard"""
        self.reg_companies.access_company(company_name=self.tcinputs['casp_group'])
        sleep(5)  # for menu option to become interactable
        self.add_user_from_dashboard(self.tcinputs['user_name'], self.tcinputs['email'])
        self.mark_user_admin(self.tcinputs['email'])
        self.log.info("User is added and marked as admin user")
        self.log.info("Adding a non_admin user")
        self.add_user_from_dashboard(self.temp_user['user_name'], self.temp_user['email'])
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        if self.tcinputs['email'] not in user.get_users():
            raise CVTestStepFailure(
                f"user with email {self.tcinputs['email']} is not associated with new "
                f"sub company [{self.tcinputs['casp_group']}]"
            )
        elif not user.is_admin_user(self.tcinputs['email']):
            raise CVTestStepFailure(f"User {self.tcinputs['email']} is not an admin user")
        if self.temp_user['email'] not in user.get_users():
            raise CVTestStepFailure(
                f"user with email {self.temp_user['email']} is not associated with new "
                f"sub company [{self.tcinputs['casp_group']}]"
            )
        elif user.is_admin_user(self.temp_user['email']):
            raise CVTestStepFailure(f"User {self.temp_user['email']} is marked as an admin user")
        user.close()

    @test_step
    def add_user_from_dashboard(self, user_name, email):
        """Verify adding user from dashboard"""
        self.dashboard.access_add_user()
        user = Users(self.webconsole)
        user.add_user(user_name, email)
        expected_msg = (
            "The information you provided is being verified. The new user will be notified via email once the account "
            "is created.")
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info("wait for 2 minutes to sync updates")
        sleep(120)
        self.log.info(f"Added user {user_name} from Company dashboard")

    @test_step
    def mark_user_admin(self, email):
        """Mark user admin and Verify user is marked as admin"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        user.make_user_admin(email)
        self.log.info(f"User {email} is marked as admin")

    @test_step
    def verify_casp_group_present(self):
        """Verify casp group is present in comcell groups listing page"""
        companies = self.reg_companies.get_companies_list()
        if self.tcinputs['casp_group'] not in companies:
            self.log.info(f"Commcell groups displayed are : {companies}")
            raise CVTestStepFailure(
                f"Casp Group {self.tcinputs['casp_group']} is NOT displayed in Commcell Groups list"
            )
        self.log.info(f"Casp Group {self.tcinputs['casp_group']} is displayed in Commcell Groups list")

    @test_step
    def delete_user_from_dashboard(self, email):
        """Delete user from dashboard"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        user.delete_user(email)
        expected_msg = "Successfully removed the user from customer group."
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info(f"User {email} is deleted from Dashboard")

    @test_step
    def delete_users(self):
        """Delete admin and non-admin users from dashbaord"""
        self.reg_companies.access_company(company_name=self.tcinputs['casp_group'])
        self.delete_user_from_dashboard(self.temp_user['email'])
        self.delete_user_from_dashboard(self.tcinputs['email'])

    def run(self):
        try:
            self.cleanup()
            self.init_tc()
            company_commcells = self.get_commcells_from_caspgroup()

            # Check if Commcell is already part of CASP, if yes then delete it before proceeding
            if self.tcinputs['commcell_id'] in company_commcells:
                self.log.info(f"Commcell Id {self.tcinputs['commcell_id']} is already present in Casp Group")
                self.log.info("Removing Commcell from Casp group")
                self.remove_commcell_from_casp()
                self._workflow.execute(workflow_json_input=self.workflow_inputs,
                                       wait_for_job=True)
                self.log.info("Workflow job completed")
                company_commcells.remove(self.tcinputs['commcell_id'])

            # Add Commcell
            self.add_commcell_to_casp()
            self._workflow.execute(workflow_json_input=self.workflow_inputs,
                                   wait_for_job=True)
            self.log.info("Workflow job completed")

            self.webconsole.logout()
            self.log.info("Logging back using master admin to verify Commmcell added")
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()
            added_commcells_list = list(company_commcells)
            added_commcells_list.append(self.tcinputs['commcell_id'])
            self.verify_commcells_in_casp(added_commcells_list)
            self.remove_commcell_from_casp()
            self._workflow.execute(workflow_json_input=self.workflow_inputs,
                                   wait_for_job=True)
            self.log.info("Workflow job completed")

            self.webconsole.logout()
            self.log.info("Logging back using master admin to verify Commmcell removed")
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()
            self.verify_commcells_in_casp(list(company_commcells))
            self.navigator.goto_companies()
            # Verification from dashboard
            self.verify_user_from_dashboard()

            self.webconsole.logout()
            self.log.info(f"Logging as user {self.tcinputs['user_name']} to verify casp group added")
            self.webconsole.login(
                self.tcinputs['user_name'],
                self.tcinputs['password']
            )
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()
            self.verify_casp_group_present()

            self.webconsole.logout()
            self.log.info("Logging using master admin to delete users")
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()
            self.delete_users()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
