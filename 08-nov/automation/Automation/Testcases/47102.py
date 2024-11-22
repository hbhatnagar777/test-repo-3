# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Metrics : Auto-created Commcell Groups
Inputs to the testcase-
    "commcell_name" : "<first commcell to register>",
    "second_commcell_name" :"<first commcell to register>",
    "password" : "<password for registration>",
    "emailaddress" : "<Email id of user>",
    "firstname":"<First name of user>",
    "lastname":"<Last name of user>",
    "GuiUser":"<User name of user>",
    "Guipwd" : "<pwd of the user to login>"
"""

from time import sleep
from cvpysdk.security.usergroup import UserGroups
from cvpysdk.security.user import Users as UserApi
from cvpysdk.commcell import Commcell

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase

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


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics : Auto-created Commcell Groups"
        self.navigator = None
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.company_name = 'RegAutomation'
        self.temp_user = {
            'user_name': 'dummy_53829',
            'email': 'dummy_53829@automation1.com'
        }
        self.usergroup = None
        self.user = None
        self.dashboard = None
        self.first_commcell = None
        self.second_commcell = None
        self.tcinputs = {
                        "commcell_name": None,
                        "second_commcell_name": None,
                        "password": None,
                        "emailaddress": None,
                        "firstname": None,
                        "lastname": None,
                        "GuiUser": None,
                        "Guipwd": None}
        self.config = get_config()

    def setup(self):
        self.usergroup = UserGroups(self.commcell)
        self.user = UserApi(self.commcell)

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory: %s", download_directory)
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.navigator = Navigator(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup(self):
        """
        cleanup the existing users in the company
        """
        if self.usergroup.has_user_group(self.company_name):
            self.usergroup.delete(self.company_name, new_usergroup='master')
        if self.user.has_user(self.tcinputs['GuiUser']):
            self.user.delete(self.tcinputs['GuiUser'], 'admin')
        if self.user.has_user(self.temp_user['user_name']):
            self.user.delete(self.temp_user['user_name'], 'admin')
        if self.commcell.client_groups.has_clientgroup(clientgroup_name=self.company_name):
            self.commcell.client_groups.delete(self.company_name)

    @test_step
    def register_with_new_user(self):
        """Register commcell with new user """
        self.first_commcell = Commcell(self.tcinputs['commcell_name'],
                                       self.config.ADMIN_USERNAME, self.config.ADMIN_PASSWORD)
        self.log.info("Starting registering Commcell with New user")
        xml_response = f"""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
        <EVGui_SetRegistrationInfoReq>
        <commCell _type_="1" commCellId="2" type="0"/>
        <registrationInformation ccguid="{self.first_commcell.commserv_guid}" ccinstalltime="1452247766"
        commcellId="0" commcellName="" companyName="automation cs" description=""
        emailAddress="{self.tcinputs['emailaddress']}" ipAddress="" isRegistered="0" majorbrandid="1" minibrandid="1"
        password="{self.tcinputs['password']}" phoneNumber="123"><customerAddress address1="" address2="" city=""
        country="" state="" zip=""/>
        <customerName firstName="{self.tcinputs['firstname']}" lastName="{self.tcinputs['lastname']}"/>
        </registrationInformation>
        </EVGui_SetRegistrationInfoReq>"""
        self.run_registration(self.first_commcell, xml_response)
        self.log.info(f"Registered Commcell {self.first_commcell} with new user successfully!")

    @test_step
    def register_with_existing_user(self):
        """Register commcell with Existing user """
        self.second_commcell = Commcell(self.tcinputs['second_commcell_name'],
                                        self.config.ADMIN_USERNAME, self.config.ADMIN_PASSWORD)
        self.log.info("Starting registering Commcell with Existing user")
        xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
        <EVGui_SetRegistrationInfoReq>
        <commCell _type_="1" commCellId="2" type="0"/>
        <registrationInformation ccguid="{self.second_commcell.commserv_guid}" ccinstalltime="1437592236" 
        commcellId="0" commcellName="" companyName="" description="" emailAddress="{self.tcinputs['emailaddress']}" 
        ipAddress="" isRegistered="1" majorbrandid="1" minibrandid="1" password="{self.tcinputs['password']}" 
        phoneNumber="1234567890">
        <customerAddress address1="" address2="" city="" country="" state="" zip=""/>
        <customerName firstName="" lastName=""/></registrationInformation>
        </EVGui_SetRegistrationInfoReq>"""
        self.run_registration(self.second_commcell, xml)
        self.log.info(f"Registered Commcell {self.second_commcell} "
                      f"with Existing user successfully!")

    def run_registration(self, commcell, xml):
        """Triggers User Registration for Metrics Server"""
        try:
            self.log.info(f"Starting Registration of commcell {commcell}")
            response = commcell.execute_qcommand("qoperation execute", xml)
            if response.status_code == 200:
                if response.json()["errorCode"] != 0:
                    raise CVTestStepFailure("Error in Registration. Response : ", response.text)
            else:
                raise CVTestStepFailure("Error in Registration. Response : ", response.text)
            self.log.info("Waiting for 2 minutes to complete Registration")
            sleep(120)
            self.log.info(f"Commcell {commcell} registered successfully!")
        except Exception as excep:
            raise CVTestStepFailure("Failed registering commcell with error : ", excep)

    @test_step
    def verify_user_from_dashboard(self):
        """Verify user management from dashboard"""
        self.navigator.goto_companies()
        reg_companies = RegisteredCompanies(self.webconsole)
        reg_companies.access_company(company_name=self.company_name)
        self.dashboard = Dashboard(self.webconsole)
        sleep(2)
        self.add_user_from_dashboard()
        self.mark_user_admin(self.temp_user['email'])
        self.mark_user_non_admin(self.temp_user['email'])
        self.delete_user_from_dashboard(self.temp_user['email'])
        self.save_as_csv_from_dashboard()
        self.log.info("Verification of user from dashboard completed!")

    @test_step
    def add_user_from_dashboard(self):
        """Verify adding user from dashboard"""
        self.dashboard.access_add_user()
        user = Users(self.webconsole)
        user.add_user(self.temp_user['user_name'], self.temp_user['email'])
        expected_msg = (
            "The information you provided is being verified."
            " The new user will be notified via email once the account is created.")
        self.webconsole.get_all_unread_notifications(expected_notifications=[expected_msg])
        self.log.info("wait for 2 minutes to sync updates")
        sleep(120)
        self.log.info(f"Added user {self.temp_user['user_name']} from Company dashboard")

    @test_step
    def mark_user_admin(self, email):
        """Mark user as admin user"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        user.make_user_admin(email)
        self.log.info(f"User {email} is marked as admin")

    @test_step
    def mark_user_non_admin(self, email):
        """Mark user as non-admin user"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        user.make_user_non_admin(email)
        self.log.info(f"User {email} is marked as Non-admin")

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
    def save_as_csv_from_dashboard(self):
        """Verify Save as CSV option from dashboard"""
        self.dashboard.access_view_user()
        user = Users(self.webconsole)
        user.save_as_csv()
        self.utils.wait_for_file_to_download('csv')
        self.utils.validate_tmp_files("csv")
        self.log.info("CSV export completed successfully")
        file_name = self.utils.poll_for_tmp_files(ends_with="csv")[0]
        csv_content = self.utils.get_csv_content(file_name)
        csv_users = []
        index = csv_content[1].index('Email')
        for row in range(2, len(csv_content)):
            csv_users.append(csv_content[row][index])
        self.dashboard.access_view_user()
        dashboard_users = user.get_users()
        user.close()
        self.log.info("CSV Users:%s", str(csv_users))
        self.log.info("Dashboard Users:%s", str(dashboard_users))
        if dashboard_users != csv_users:
            self.log.error("Users in CSV are not matching with users in dashboard")
            raise CVTestStepFailure("Users in CSV export are not matching with users in dashboard")
        self.log.info(f"Save as CSV option verified from Dashboard")

    @test_step
    def verify_commcell_registered(self, reg_commcell, expected_commcell_count):
        """Verify commcell is registered"""
        self.log.info('Validating commcell is registered')
        self.webconsole.goto_commcell_dashboard()
        self.navigator.goto_commcells_in_group()
        sleep(2)
        monitoring_form = ManageCommcells(self.webconsole)
        company_commcells = monitoring_form.get_column_values('CommCell Name')
        expected_commcell = self.company_name + " - " + reg_commcell.commserv_name
        if len(company_commcells) != expected_commcell_count:
            raise CVTestStepFailure(f"{len(company_commcells)} Commcell found in Commcell list, "
                                    f"Expected {expected_commcell_count}")
        if expected_commcell not in company_commcells:
            raise CVTestStepFailure(f"Commcell {expected_commcell} "
                                    f"is not present in Commcells list - {company_commcells}")
        self.log.info(f"Commcell {reg_commcell} registered successfully!")

    def run(self):
        try:
            self.cleanup()
            self.init_tc()
            self.log.info("Registering a commcell with New user")
            self.register_with_new_user()
            self.log.info("Logging using Commcell Group admin "
                          "user to verify first commcell registered")
            self.webconsole.login(
                                self.tcinputs['GuiUser'],
                                self.tcinputs['Guipwd'])
            self.verify_commcell_registered(self.first_commcell, 1)  # count of commcells in Commcell list
            self.log.info("Registering a commcell with existing user")
            self.register_with_existing_user()
            self.webconsole.logout()
            self.log.info("Logout and Logging using Commcell Group admin user "
                          "to verify second commcell registered")
            self.webconsole.login(self.tcinputs['GuiUser'], self.tcinputs['Guipwd'])
            self.verify_commcell_registered(self.second_commcell, 2)  # count of commcells in Commcell list
            self.verify_user_from_dashboard()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
