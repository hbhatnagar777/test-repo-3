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

    edit_tiles()    --  Method edit tiles present on company page

    add_AD()        --  Method to add AD identity server

    edit_as_MSP()   --  Edit Tiles on company page as MSP

    edit_as_TA()    --  Edit tiles on company page as Tenant Admin

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import time
from datetime import datetime

from cvpysdk.commcell import Commcell
from cvpysdk.organization import Organizations

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mail_box import MailBox
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.AdminConsolePages.identity_servers import Domains
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Helper.CompanyHelper import MSPHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep


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
        self.name = "MSP Test case: Login and edit validation for different persona"
        self.company_name = None
        self.company_alias = None
        self.password = None
        self.navigator = None
        self.__table = None
        self.user = None
        self.__company_details = None
        self.domain_obj = None
        self.MSP_obj = None
        self.config = get_config()
        self.random_string = str(time.time()).split(".")[0]
        self.tcinputs = {
            "AD_name": "",
            "netbios": "",
            "AD_username": "",
            "AD_password": "",
            "AD_usergroup": "",
            "user": {
                "username": "",
                "password": ""
            }
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.mailbox = MailBox(mail_server=self.config.email.server,
                               username=self.config.email.username,
                               password=self.config.email.password)
        self.mailbox.connect()

        self.navigator = self.admin_console.navigator
        self.__table = Table(self.admin_console)
        self.user = Users(self.admin_console)
        self.password = self.config.MSPCompany.tenant_password
        self.__companies = Companies(self.admin_console)
        self.__company_details = CompanyDetails(self.admin_console)
        self.MSP_obj = MSPHelper(admin_console=self.admin_console, commcell=self.commcell,
                                 mail_box=self.mailbox)

    def edit_tiles(self, persona='MSP'):
        """ Method edit tiles present on company page"""
        if persona == 'TA':
            self.navigator.navigate_to_company()
            self.__companies.access_self_company(self.company_name)
            gen_settings_dict_ta = {'authcode': 'OFF',
                                    '2-factor': {"default": "ON"},
                                    'data_encryption': 'OFF',
                                    'auto_discover_applications': 'OFF'}
            self.__company_details.edit_general_settings(gen_settings_dict_ta)
            self.__company_details.edit_company_security_associations(
                {f'{self.company_alias}\\{self.random_string}4': ['Tenant Admin']})
            self.__company_details.edit_contacts(contact_names=['TestName1'])
            self.__company_details.edit_sender_email(sender_name='Rimuru1', sender_email='Rimuru1@tempest.com')
            file_except_dict = {}
            self.__company_details.edit_company_file_exceptions(file_exceptions=file_except_dict)
        else:
            gen_settings_dict = {'company_alias': self.company_alias + "Changed",
                                 'authcode': 'ON',
                                 '2-factor': {"default": "ON"},
                                 'reseller_mode': 'ON',
                                 'data_encryption': 'ON',
                                 'auto_discover_applications': 'ON',
                                 'infra_type': 'Rented and own storage'}
            self.navigator.navigate_to_companies()
            self.__companies.access_company(self.company_name)
            self.__company_details.edit_general_settings(gen_settings_dict)
            self.company_alias = self.company_alias + "Changed"
            self.__company_details.edit_sites(primary_site='primarysit8e.com')
            self.__company_details.edit_company_plans(self.config.MSPCompany.company.plans)

            self.__company_details.edit_company_security_associations(
                {self.company_alias + f'\\{self.random_string}2': ['Tenant Admin']})
            self.__company_details.edit_contacts(contact_names=['TestName'])
            self.__company_details.edit_sender_email(sender_name='Rimuru', sender_email='Rimuru@tempest.com')
            file_except_dict = {}
            self.__company_details.edit_company_file_exceptions(file_exceptions=file_except_dict)
            self.__company_details.edit_company_operators(
                {f"{self.random_string}3.local": ['Tenant Operator']})
        self.__company_details.edit_general_settings({'2-factor': {"default": "OFF"}})

    def add_AD(self, is_msp=True):
        """Method to add AD identity server"""
        local_group = self.company_alias + '\\Tenant Admin'
        
        self.domain_obj = Domains(admin_console=self.admin_console)
        self.domain_obj.add_domain(domain_name=self.tcinputs['AD_name'],
                                   netbios_name=self.tcinputs['netbios'],
                                   username=self.tcinputs['AD_username'],
                                   password=self.tcinputs['AD_password'],
                                   user_group=self.tcinputs['AD_usergroup'],
                                   local_group=[local_group],
                                   is_creator_msp=True)

    @test_step
    def edit_as_MSP(self):
        """Edit Tiles on company page as MSP"""
        self.edit_tiles(persona='MSP')
        self.navigator.switch_company_as_operator(self.company_name)

        self.navigator.navigate_to_identity_servers()
        self.add_AD()
        self.delete_AD()
        self.navigator.switch_company_as_operator("Reset")

    @test_step
    def edit_as_TA(self):
        """Edit tiles on company page as Tenant Admin"""
        self.edit_tiles(persona='TA')

        self.navigator.navigate_to_users()
        self.user.add_local_user(name='TestName2', email='tempUser2@xyz.com',
                                 groups=[self.company_alias + "\\Tenant Users"],
                                 password=self.password,
                                 upn=f"{self.random_string}1@testcase.com")
        self.navigator.navigate_to_identity_servers()
        self.add_AD(is_msp=False)

    def delete_AD(self):
        """Method to delete AD"""
        local_group = self.company_alias + '\\Tenant Admin'
        self.log.info("Deleting the AD")
        self.navigator.navigate_to_identity_servers()
        self.domain_obj.delete_domain(self.tcinputs['netbios'], False, local_group)

    def run(self):
        """Run function of this test case"""
        try:
            self.input_dict = {
                "company": {
                    "name": "TestCompany" + "_" + str(datetime.today())[-3:],
                    "alias": 'TestInc' + "_" + str(datetime.today())[-3:],
                    "smtp": 'smtp.commvault{0}.com'.format(str(datetime.today())[-3:]),
                    "contact": "Test Contact"
                }
            }
            self.username = self.input_dict['company']['alias'] + "\\" + self.config.email.email_id.split('@')[0]
            self.comp_details = self.input_dict['company']
            self.company_name = self.comp_details['name']
            self.company_alias = self.comp_details['alias']
            self.log.info("Creating a new company")
            self.MSP_obj.add_new_company(company_name=self.company_name,
                                         email=self.config.email.email_id,
                                         contact_name=self.comp_details['contact'],
                                         company_alias=self.company_alias,
                                         smtp=self.comp_details['smtp'],
                                         mail_template='Add company')
            # self.admin_console.logout()
            self.commcell.refresh()
            self.MSP_obj.parse_email_reset(self.password,
                                           self.username,
                                           self.inputJSONnode['commcell']['commcellPassword'])
            # self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
            #                          self.inputJSONnode['commcell']['commcellPassword'])

            self.navigator.switch_company_as_operator(self.company_name)
            self.navigator.navigate_to_users()

            self.user.add_local_user(name='TestName', email='tempUser@xyz.com',
                                     groups=[self.company_alias + "\\Tenant Admin"],
                                     password=self.config.MSPCompany.tenant_password,
                                     upn=f"{self.random_string}2@testcase.com")
            self.navigator.switch_company_as_operator("Reset")

            self.navigator.navigate_to_users()
            self.user.add_local_user(name='TestNameOp', email='tempUserOp@xyz.com',
                                     password=self.config.MSPCompany.tenant_password,
                                     upn=f"{self.random_string}3@testcase.com")
            self.users_to_delete = f"{self.random_string}3.local"

            self.edit_as_MSP()

            self.log.info("Logging in as Tenant Admin")
            self.admin_console.logout_silently(self.admin_console)
            self.admin_console.login(self.company_alias + "\\" + self.config.email.email_id.split('@')[0],
                                     self.password)

            self.navigator.navigate_to_users()
            self.user.add_local_user(name='TestName1', email='tempUser1@xyz.com',
                                     groups=[self.company_alias + "\\Tenant Admin"],
                                     password=self.password,
                                     upn=f"{self.random_string}4@testcase.com")
            self.edit_as_TA()

            self.log.info("Logging in as Tenant User")
            self.admin_console.logout_silently(self.admin_console)
            self.admin_console.login(username=self.company_alias + '\\' + 'tempUser2',
                                     password=self.password)
            if self.navigator.check_if_element_exists('Company'):
                raise Exception("Company user should not be able to see company page")

            self.admin_console.logout_silently(self.admin_console)
            self.admin_console.login(username=self.tcinputs['user']['username'],
                                     password=self.tcinputs['user']['password'])

            self.admin_console.logout_silently(self.admin_console)
            self.admin_console.login(self.company_alias + "\\" + self.config.email.email_id.split('@')[0],
                                     self.password)
            self.log.info("Deleting AD as a Tenant Admin")
            self.delete_AD()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info('Deleting the company')
        commcell_admin = Commcell(webconsole_hostname=self.inputJSONnode['commcell']['webconsoleHostname'],
                                  commcell_username='admin',
                                  commcell_password=self.inputJSONnode['commcell']['commcellPassword'],
                                  verify_ssl=False)

        Organizations(commcell_admin).delete((self.input_dict['company']['name']))
        commcell_admin.users.delete(self.users_to_delete.lower())

        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
