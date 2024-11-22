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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from datetime import datetime
import random

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mail_box import MailBox
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.identity_servers import Domains, IdentityServers
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Helper.UserGroupHelper import UserGroupMain
from Web.AdminConsole.Helper.CompanyHelper import MSPHelper
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestStepFailure
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
        self.name = "MSP Testcase: External Authentication and validation"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.sso_url = None
        self.sp_entity_id = None
        self.__table = None
        self.saml_obj = None
        self.webconsole_url = None
        self.tcinputs = {
            "IDP admin username": "",
            "IDP admin password": "",
            "appname": "",
            "metadata path": "",
            "SMTP": "",
            "SAML user name": "",
            "SAML user pwd": "",
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
        self.config = get_config()
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
        self.__company_details = CompanyDetails(self.admin_console)
        self.MSP_obj = MSPHelper(self.admin_console, self.commcell, self.mailbox)
        self.__identity_server = IdentityServers(self.admin_console)
        self.usergroup_helper = UserGroupMain(self.admin_console)

        self.azure_url = self.tcinputs['IDP URL']
        self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
        self.adminconsole_url = "https://" + self.commcell.webconsole_hostname + "/adminconsole"

    def add_AD(self):
        """Method to add AD identity server"""
        local_group = self.company_alias + '\\Tenant Admin'
        self.navigator.navigate_to_identity_servers()
        self.domain_obj = Domains(admin_console=self.admin_console)
        self.domain_obj.add_domain(domain_name=self.tcinputs['AD_name'],
                                   netbios_name=self.tcinputs['netbios'],
                                   username=self.tcinputs['AD_username'],
                                   password=self.tcinputs['AD_password'],
                                   user_group=self.tcinputs['AD_usergroup'],
                                   local_group=[local_group])

    def add_SAML_app(self):
        self.navigator.navigate_to_identity_servers()

        self.saml_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
        self.saml_obj.app_name = self.saml_app_name
        self.saml_obj.create_saml_app(self.tcinputs['metadata path'],
                                      description="Created via Automation for verify user landing page",
                                      email_suffix=[self.tcinputs['SMTP']]
                                      )
        self.saml_obj.sp_metadata_values()

        self.admin_console.logout()

        self.sso_url = self.saml_obj.sso_url

        self.saml_obj.login_to_azure_and_edit_basic_saml_configuration(self.tcinputs['IDP admin username'],
                                                                       self.tcinputs['IDP admin password'],
                                                                       self.tcinputs['appname'],
                                                                       self.saml_obj.sp_entity_id,
                                                                       self.sso_url,
                                                                       self.saml_obj.slo_url)
        self.saml_obj.logout_from_azure()

    def login_as_TA(self):
        """Login as Tenant Admin"""
        self.admin_console.logout()
        self.admin_console.login(self.username, self.password)

    @test_step
    def login_as_SAML_user(self):
        """Verify if SAML user can login"""
        self.saml_obj.initiate_saml_login_with_azure(self.adminconsole_url,
                                                     self.tcinputs['SAML user name'],
                                                     self.tcinputs['SAML user pwd'],
                                                     self.tcinputs['appname'],
                                                     False)

        self.saml_obj.sp_init_logout(self.commcell.webconsole_hostname)
        self.admin_console.wait_for_completion()
        self.admin_console.login(username=self.username,
                                 password=self.password)


        self.usergroup_helper.group_name = self.company_alias + '\\Tenant Users'
        if not self.usergroup_helper.has_user(self.tcinputs['SAML user name']):
            raise CVTestStepFailure(f"The User should become a part of group {self.usergroup_helper.group_name}")

    @test_step
    def login_as_AD_user(self):
        """Verify if AD user can login and become a part of usergroup"""
        self.admin_console.login(self.tcinputs['user']['username'],
                                 self.tcinputs['user']['password'])
        self.login_as_TA()

        group_name = self.tcinputs['AD_usergroup']
        self.usergroup_helper.group_name = group_name
        if not self.usergroup_helper.has_user(self.tcinputs['user']['username']):
            raise CVTestStepFailure(f"The User should become a part of group {group_name}")

    def run(self):
        """Run function of this test case"""
        try:
            self.input_dict = {
                "company": {
                    "name": "TestCompany" + "_" + str(datetime.today())[-3:],
                    "alias": 'TestInc' + "_" + str(datetime.today())[-3:],
                    "smtp": 'hello.world{0}.com'.format(str(datetime.today())[-3:]),
                    "contact": "Test Contact"
                }
            }
            self.saml_app_name = self.tcinputs['appname'] + str(random.randint(0, 100000))
            self.password = self.config.MSPCompany.tenant_password
            self.username = self.input_dict['company']['alias'] + "\\" + self.config.email.email_id.split('@')[0]

            self.log.info("Logging in as MSP Admin")
            self.MSP_obj = MSPHelper(self.admin_console, self.commcell, self.mailbox)
            comp_details = self.input_dict['company']
            self.MSP_obj.company_name = self.company_name = comp_details['name']
            self.MSP_obj.company_alias = self.company_alias = comp_details['alias']

            self.log.info("Creating a new company")
            self.MSP_obj.add_new_company(company_name=comp_details['name'],
                                         email=self.config.email.email_id,
                                         contact_name=comp_details['contact'],
                                         company_alias=comp_details['alias'],
                                         smtp=comp_details['smtp'],
                                         mail_template='Add company')

            self.MSP_obj.parse_email_reset(password=self.password)
            self.admin_console.login(self.username, self.password)
            self.add_AD()
            self.add_SAML_app()
            self.login_as_SAML_user()
            self.admin_console.logout()
            self.login_as_AD_user()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.browser.close()
        self.mailbox.disconnect()
        
        self.commcell.organizations.refresh()
        self.commcell.organizations.delete(self.input_dict['company']['name'])
