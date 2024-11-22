# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" MSP Testcase: Create Company and validation associated with it """
from datetime import datetime

from cvpysdk.organization import Organizations

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from cvpysdk.commcell import Commcell

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mail_box import MailBox
from Web.AdminConsole.Helper.CompanyHelper import MSPHelper, CompanyMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from AutomationUtils.config import get_config
from Web.Common.page_object import handle_testcase_exception

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "MSP Testcase :Create Company and validation associated with it"

        self.tcinputs = {

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
            self.password = self.config.MSPCompany.tenant_password
            self.username = self.input_dict['company']['alias'] + "\\" + self.config.email.email_id.split('@')[0]

            self.log.info("Logging in as MSP Admin")
            MSP_obj = MSPHelper(self.admin_console, self.commcell, self.mailbox)
            self.msp_object = MSP_obj
            comp_details = self.input_dict['company']

            self.log.info("Creating a new company")
            MSP_obj.add_new_company(company_name=comp_details['name'],
                                    email=self.config.email.email_id,
                                    contact_name=comp_details['contact'],
                                    company_alias=comp_details['alias'],
                                    smtp=comp_details['smtp'],
                                    mail_template='Add company')

            self.log.info("Validating default configuration for company")
            MSP_obj.validate_default_configurations()

            self.log.info("Validate and reset password for tenant user")
            MSP_obj.validate_template()
            MSP_obj.parse_email_reset(password=self.password)
            MSP_obj.login_as_tenant(self.username, self.password)

            self.log.info("Logging in as Tenant Admin")
            commcell_tenant = Commcell(webconsole_hostname=self.inputJSONnode['commcell']['webconsoleHostname'],
                                       commcell_username=self.username,
                                       commcell_password=self.password)

            self.log.info("Validating MSP details when logged in as tenant admin")
            MSP_obj_tenant = MSPHelper(self.admin_console, commcell_tenant, self.mailbox)
            MSP_obj_tenant.company_name = comp_details['name']
            self.msp_object = MSP_obj_tenant
            MSP_obj_tenant.validate_default_configurations()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.browser.close()
        self.mailbox.disconnect()

        self.log.info('Deleting the company')
        self.commcell.organizations.delete((self.input_dict['company']['name']))
