# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" MSP Testcase: Create Company and validation associated with it """
import time

from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.identity_servers import Domains
from Web.AdminConsole.Components.table import Table

""""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case
"""

import datetime
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mail_box import MailBox
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.CompanyHelper import MSPHelper, CompanyMain
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from cvpysdk.organization import Organizations
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception,TestStep
from Web.AdminConsole.AdminConsolePages.Users import Users


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
        self.name = "MSP Testcase :Create Company and validation of edited entities with it"
        self.browser = None
        self.admin_console = None
        self.mailbox = None
        self.msp_object = None
        self.config = None
        self.company_name = None
        self.company_alias = None
        self.username = None
        self.tcinputs = {
            "data_encrypt": {
                "company": "",
                "client": "",
                "username": "",
                "password": ""
            }
        }

    def setup(self):
        """Setup function of this test case"""
        self.config = get_config()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.__navigator = self.admin_console.navigator
        self.__user = Users(self.admin_console)
        self.mailbox = MailBox(mail_server=self.config.email.server,
                               username=self.config.email.username,
                               password=self.config.email.password)
        self.mailbox.connect()
        self.company_alias = "testing_alias_" + \
                datetime.datetime.strftime(datetime.datetime.now(), '%H_%M')
        self.company_name = "Company_" + \
                datetime.datetime.strftime(datetime.datetime.now(), '%H_%M_%S')
        self.child_name = "Child_" + \
                            datetime.datetime.strftime(datetime.datetime.now(), '%H_%M_%S')
        self.msp_object = MSPHelper(
                self.admin_console, self.commcell, self.mailbox)
        self.msp_admin_username = "{0}\\{1}".format(self.company_alias, self.config.MSPCompany.company.email.split('@')[0])
        
        self.msp_user = 'tenant_user' + \
             datetime.datetime.strftime(datetime.datetime.now(), '%H_%M')
        self.msp_user_username = "{0}\\{1}".format(self.company_alias,self.msp_user)
        self.navigator = self.admin_console.navigator
        self.__company_details = CompanyDetails(self.admin_console)
        self.__companies = Companies(self.admin_console)

    @test_step
    def validate_tfa_all(self):
        """To validate 2-factor authentiocation is enabled for all users in company"""
        self.msp_object.edit_company_general_settings(two_factor={'default': 'ON'})
        self.admin_console.logout_silently(self.admin_console)
        self.msp_object.validate_tfa_login(user_name=self.msp_admin_username, password=self.config.MSPCompany.tenant_password, tfa_enabled_group=True)
        self.msp_object.validate_tfa_login(user_name=self.msp_user_username,password=self.config.MSPCompany.tenant_password, tfa_enabled_group=True)
    
    @test_step
    def validate_tfa_tenant_admin(self):
        """To validate 2-factor authentiocation is enabled for Tenant admin in company"""
        self.msp_object.edit_company_general_settings(
                two_factor={'default': 'add', 'user_groups': [self.company_alias+'\\Tenant Admin']})
        self.admin_console.logout_silently(self.admin_console)
        self.msp_object.validate_tfa_login(user_name=self.msp_admin_username, password=self.config.MSPCompany.tenant_password, tfa_enabled_group=True)
        self.msp_object.validate_tfa_login(user_name=self.msp_user_username,password=self.config.MSPCompany.tenant_password, tfa_enabled_group=False)

    @test_step
    def validate_tfa_tenant_user(self):
        """To validate 2-factor authentiocation is enabled for Tenant user in company"""
        self.msp_object.edit_company_general_settings(
                two_factor={'default': 'add', 'user_groups': [self.company_alias+'\\Tenant Users']})
        self.msp_object.edit_company_general_settings(
                two_factor={'default': 'Remove', 'user_groups': [self.company_alias+'\\Tenant Admin']})
        self.admin_console.logout_silently(self.admin_console)
        self.msp_object.validate_tfa_login(user_name=self.msp_admin_username, password=self.config.MSPCompany.tenant_password, tfa_enabled_group=False)
        self.msp_object.validate_tfa_login(user_name=self.msp_user_username,password=self.config.MSPCompany.tenant_password, tfa_enabled_group=True)

    @test_step
    def validate_tfa_off(self):
        """To validate 2-factor authentiocation is disabled for all users in company"""
        self.msp_object.edit_company_general_settings(two_factor={'default': 'OFF'})
        self.admin_console.logout_silently(self.admin_console)
        self.msp_object.validate_tfa_login(user_name=self.msp_admin_username, password=self.config.MSPCompany.tenant_password, tfa_enabled_group=False)
        self.msp_object.validate_tfa_login(user_name=self.msp_user_username,password=self.config.MSPCompany.tenant_password, tfa_enabled_group=False)

    def add_AD(self):
        """Method to add AD identity server"""
        local_group = self.company_alias + '\\Tenant Admin'
        self.navigator.navigate_to_identity_servers()
        self.domain_obj = Domains(admin_console=self.admin_console)
        self.domain_obj.add_domain(domain_name=self.tcinputs['AD_name'],
                                   netbios_name=self.tcinputs['netbios'],
                                   username=self.tcinputs['AD_username'],
                                   password=self.tcinputs['AD_password'],
                                   company_name=self.company_name,
                                   user_group=self.tcinputs['AD_usergroup'],
                                   local_group=[local_group])

    @test_step
    def validate_use_UPN(self):
        """Validate use upn funtionality on Company page"""
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.__company_details.edit_general_settings({"UPN": 'ON'})
        self.add_AD()
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.login(username=self.tcinputs['user']['username'],
                                 password=self.tcinputs['user']['password'])
        time.sleep(60)
        self.commcell.refresh()
        email = self.commcell.users.get(self.tcinputs['user']['username']).email
        if email == self.tcinputs['user']['email']:
            self.log.info("Should have been different email")
        self.admin_console.logout_silently(self.admin_console)

    @test_step
    def validate_reseller(self):
        """Method to validate if reseller option is working on company page"""
        self.navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.__company_details.edit_general_settings({"reseller_mode": True})
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.login(self.username, self.config.MSPCompany.tenant_password)
        company_obj = CompanyMain(self.admin_console)
        company_obj.add_new_company(company_name=self.child_name)
        self.__companies.company_exists(company_obj.company_name)

        self.__companies.access_company(company_obj.company_name)
        self.__company_details.deactivate_and_delete_company_from_details()

    @test_step
    def validate_supported_solutions(self):
        """Method to validate if supported solution works on company page"""
        supported_solns = {'supported_solutions': ['File server', 'Laptop', 'Kubernetes']}
        self.navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.msp_object.supported_solutions = [supported_solns['supported_solutions']]
        self.__company_details.edit_general_settings(supported_solns)
        self.msp_object.validate_supported_solutions(self.inputJSONnode['commcell']['commcellUsername'],
                                                     self.inputJSONnode['commcell']['commcellPassword'],
                                                     self.username,
                                                     self.config.MSPCompany.tenant_password,
                                                     is_edited=True)

    @test_step
    def validate_infrastructure_type(self):
        """Method to validate if infrastructure type works on company page"""
        infra_type = {"infra_type": 'Own storage'}
        self.navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.msp_object._general_settings['Infrastructure type'] = infra_type['infra_type']
        self.__company_details.edit_general_settings(infra_type)
        self.msp_object.validate_infrastructure_type(self.inputJSONnode['commcell']['commcellUsername'],
                                                     self.inputJSONnode['commcell']['commcellPassword'],
                                                     self.username,
                                                     self.config.MSPCompany.tenant_password,
                                                     is_edited=True)

    @test_step
    def validate_data_encrypt(self):
        """Method to validate if data encryption works"""
        owner_details = {
            "client": self.tcinputs['data_encrypt']['client'],
            "username": self.tcinputs['data_encrypt']['username'],
            "password": self.tcinputs['data_encrypt']['password']
        }
        self.navigator.navigate_to_companies()
        self.__companies.access_company(self.tcinputs['data_encrypt']['company'])
        self.__company_details.edit_general_settings({"data_encryption": True})
        self.msp_object.validate_allow_owner_data_encryption(owner_details)
        self.admin_console.logout_silently(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:
            self.comp_details = {
                "alias": 'TestInc' + "_" + str(datetime.datetime.today())[-3:],
                "smtp": 'smtp.commvault{0}.com'.format(str(datetime.datetime.today())[-3:]),
                "contact": "Test Contact"
            }
            self.msp_object.add_new_company(company_name=self.company_name,
                                            email=self.config.MSPCompany.company.email,
                                            mail_template='Automatic',
                                            contact_name=self.comp_details['contact'],
                                            smtp=self.comp_details['smtp'],
                                            company_alias=self.comp_details['alias'])

            self.msp_object.edit_company_general_settings(
                smtp=self.config.MSPCompany.company.smtp, company_alias=self.company_alias)
            self.username = self.company_alias + "\\" + self.config.MSPCompany.company.email.split('@')[0]

            self.__navigator.switch_company_as_operator(self.company_name)
            self.__navigator.navigate_to_users()
            user_email = self.config.MSPCompany.company.email_1
            self.__user.add_local_user(email=user_email,
                                       username=self.msp_user,
                                       groups=[self.company_alias + '\\Tenant Users'],
                                       password=self.config.MSPCompany.tenant_password,
                                       upn=f"{str(time.time()).split('.')[0]}{user_email}")
            self.__navigator.switch_company_as_operator("Reset")

            # Commented till the time we get a way to bypass captch in reset password email
            # self.admin_console.logout_silently(self.admin_console)

            self.msp_object.parse_email_reset(self.config.MSPCompany.tenant_password, self.username,
                self.inputJSONnode['commcell']['commcellPassword'])
            self.mailbox.disconnect()
            # self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
            #                          self.inputJSONnode['commcell']['commcellPassword'])
            self.validate_tfa_all()

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.validate_tfa_tenant_admin()

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.validate_tfa_tenant_user()

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.validate_tfa_off()

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.validate_reseller()
            self.admin_console.logout_silently(self.admin_console)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            # For supported solutions
            # self.validate_supported_solutions()

            # For infrastructure type
            self.validate_infrastructure_type()

            # For job start time
            self.navigator.navigate_to_companies()
            self.__companies.access_company(self.company_name)
            self.msp_object.job_start_time = 19*60*60 + 0*60*60
            self.__company_details.edit_general_settings({'job_start_time': '07:00 PM'})
            self.msp_object.validate_general_tile(is_edited=True)

            # With webconsole disabled we don't have a entry point for this.
            # self.validate_data_encrypt()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info('Deleting the company')
        Organizations(self.commcell).delete(self.company_name)
        self.browser.close_silently(self.browser)
