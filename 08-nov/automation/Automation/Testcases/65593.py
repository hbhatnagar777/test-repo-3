# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Validation of non-beamimg commcells registration
Inputs to the testcase-
    "commcell_name" : "<commcell to register>",
    "commcell_id" :"<commcell ID to register>",
    "password" : "<password for registration>",
    "emailaddress" : "<Email id of user>",
    "firstname":"<First name of user>",
    "lastname":"<Last name of user>",
    "GuiUser":"<User name of user>"
"""
from datetime import datetime
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
from Web.WebConsole.webconsole import WebConsole

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Validation of non-beamimg commcells registration"
        self.navigator = None
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.company_name = 'sp34'
        self.temp_user = {
            'user_name': 'dummy_65593',
            'email': 'dummy_65593@automation1.com'
        }
        self.usergroup = None
        self.user = None
        self.dashboard = None
        self.first_commcell = None
        self.tcinputs = {
            "commcell_name": None,
            "commcell_id": None,
            "first_user": None,
            "first_password": None,
            "password": None,
            "emailaddress": None,
            "firstname": None,
            "lastname": None,
            "GuiUser": None}
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
        if self.commcell.clients.has_client(self.tcinputs['GuiUser']):
            self.commcell.clients.delete(self.tcinputs['GuiUser'], 'admin')

    @test_step
    def verify_delete_commcell(self):
        """Delete commcell, verify commcell is deleted"""

        self.log.info("Deleting [%s] commcell from commcell monitoring page "
                      "user", self.tcinputs['commcell_name'])
        self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                self.inputJSONnode['commcell']['commcellPassword'])
        self.webconsole.goto_commcell_dashboard()
        self.navigator.goto_worldwide_commcells()
        expected_commcell = self.company_name + " - NB_Commcell"
        sleep(2)
        monitoring_form = ManageCommcells(self.webconsole)
        if monitoring_form.is_commcell_exists(expected_commcell):
            monitoring_form.delete_commcell(expected_commcell)
            self.log.info("[%s] commcell deleted successfully "
                          "user", expected_commcell)
        self.webconsole.logout()

    @test_step
    def register_with_new_user(self):
        """Register commcell with new user """
        self.first_commcell = Commcell(self.tcinputs['commcell_name'],
                                       self.tcinputs['first_user'], self.tcinputs['first_password'])
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

    @test_step
    def verify_nonBeamingCommcell_from_dashboard(self, commcell_id):
        """Verify non-beaming commcell from dashboard"""
        self.log.info('Validating non beaming commcell is registered')
        self.webconsole.goto_commcell_dashboard()
        self.navigator.goto_commcells_in_group()
        sleep(2)
        monitoring_form = ManageCommcells(self.webconsole)
        company_commcellsId = monitoring_form.get_column_values('CommCell ID')
        if commcell_id not in company_commcellsId:
            raise CVTestStepFailure(f"Commcell {commcell_id} "
                                    f"is not present in Commcells list - {company_commcellsId}")
        company_commcellsName = monitoring_form.get_column_values('CommCell Name')
        expected_commcell = self.company_name + " - NB_Commcell"
        if expected_commcell not in company_commcellsName:
            raise CVTestStepFailure(f"Commcell {expected_commcell} "
                                    f"is not present in Commcells list - {company_commcellsName}")
        self.log.info("Non-beaming commcell found!")

    def run(self):
        try:
            self.cleanup()
            self.init_tc()
            self.verify_delete_commcell()
            self.log.info("Registering a commcell with New user")
            self.register_with_new_user()
            self.log.info("Logging using Commcell Group admin "
                          "user to verify first commcell registered")
            self.webconsole.login(
                self.tcinputs['emailaddress'],
                self.tcinputs['first_password'])
            self.verify_commcell_registered(self.first_commcell, 1)  # count of commcells in Commcell list
            now = datetime.now()
            minutes = 65 - now.minute
            self.log.info(f"Non-beaming commcells processing is supposed to be done in {minutes} minutes , waiting")
            sleep(minutes * 60)
            self.verify_nonBeamingCommcell_from_dashboard(self.tcinputs['commcell_id'])

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
