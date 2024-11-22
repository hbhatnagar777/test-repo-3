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

    setup()         --  setup function of this test case

    validate_hidden_assoc() -- validates the hidden security associations

    validate_security_assoc() -- validates security association functionality

    validate_operator() -- validates operator functionality

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import time
from datetime import datetime

from cvpysdk.commcell import Commcell

from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.Users import Users

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mail_box import MailBox
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Helper.CompanyHelper import MSPHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "MSP Testcase :Edit Security tile of the company and validation"
        self.user_details_sec = None
        self.user_details_op = None
        self.client_details = None
        self.username = None
        self.company_name = None
        self.company_alias = None
        self.__users = None
        self.MSP_obj = None
        self.config = get_config()
        self.tcinputs = {
            "company_name": "",
            "company_alias": "",
            "client": "",
            'subclient': ""
        }

    @test_step
    def validate_hidden_assoc(self):
        """Method to validate the hidden security associations on company page"""
        self.navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        sec_associations = self.__company_details.get_security_associations(hidden=True)
        if 'master' not in sec_associations.keys():
            raise Exception("The master usergroup should be in the default security associations")

    @test_step
    def validate_security_assoc(self):
        """Method to validate security association functionality from company page"""
        self.log.info("Validate Security associations")
        self.MSP_obj.validate_security_functionality(self.user_details_sec, self.password, self.client_details)
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

    @test_step
    def validate_operator(self):
        """Method to validate operator functionality for company page"""
        self.log.info("Validate Operators")
        self.MSP_obj.validate_operator_functionality(self.user_details_op, self.password, self.client_details)
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.navigator = self.admin_console.navigator
        self.__table = Table(self.admin_console)
        self.__companies = Companies(self.admin_console)
        self.__company_details = CompanyDetails(self.admin_console)
        self.MSP_obj = MSPHelper(admin_console=self.admin_console, commcell=self.commcell)
        self.password = self.config.MSPCompany.tenant_password
        self.__users = Users(self.admin_console)
        self.random_str = str(time.time()).split(".")[0]

    def run(self):
        """Run function of this test case"""
        try:
            self.username = self.tcinputs['company_alias'] + "\\" + self.config.email.email_id.split('@')[0]
            self.company_name = self.MSP_obj.company_name = self.tcinputs['company_name']
            self.company_alias = self.MSP_obj.company_alias = self.tcinputs['company_alias']
            self.client_details = {
                'client': self.tcinputs['client'],
                'subclient': self.tcinputs['subclient'],
                'loc': self.config.MSPCompany.backup_loc,
                'OS': self.config.MSPCompany.OS
            }
            email = self.company_name + f'{self.random_str}@' + self.company_alias + '.com'
            self.user_details_sec = {
                "user1": {
                    "email": email,
                    "username": self.company_alias + '\\' + self.company_name + self.random_str
                },
                "user2": {
                    "email": '2' + email,
                    "username": '2' + self.company_name + ".local"
                }
            }
            self.user_details_op = {
                "user1": {
                    "email": '3' + email,
                    "username": '3' + self.company_name + ".local"
                },
                "user2": {
                    "email": '4' + email,
                    "username": '4' + self.company_name + ".local"
                }
            }

            self.validate_hidden_assoc()

            self.validate_security_assoc()

            self.validate_operator()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        username_list = [self.user_details_sec['user1']["username"],
                         self.user_details_sec['user2']["username"],
                         self.user_details_op['user1']["username"],
                         self.user_details_op['user2']["username"]]
        self.navigator.navigate_to_users()
        self.commcell.refresh()
        for username in username_list:
            self.commcell.users.delete(username.lower())

        self.browser.close_silently(self.browser)
