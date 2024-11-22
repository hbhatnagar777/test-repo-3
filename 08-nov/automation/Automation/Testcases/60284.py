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

from cvpysdk.organization import Organizations

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mail_box import MailBox
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
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
        self.name = "MSP Testcase: Plan creation and deletion"
        self.company_name = None
        self.company_alias = None
        self.navigator = None
        self.__table = None
        self.__company_details = None
        self.__companies = None
        self.MSP_obj = None
        self.file_server = None
        self.client_name = None
        self.config = get_config()
        self.tcinputs = {
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
        self.__company_details = CompanyDetails(self.admin_console)
        self.__companies = Companies(self.admin_console)

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
            self.password = self.config.MSPCompany.tenant_password
            self.username = self.input_dict['company']['alias'] + "\\" + self.config.email.email_id.split('@')[0]
            comp_details = self.input_dict['company']
            self.company_name = comp_details['name']
            self.company_alias = comp_details['alias']
            self.user_details = {
                "parent_username": self.inputJSONnode['commcell']['commcellUsername'],
                "parent_password": self.inputJSONnode['commcell']['commcellPassword'],
                "tenant_username": self.username,
                "tenant_password": self.password
            }

            self.plan_details = {
                "plan_name": self.tcinputs['plan'],
                "derived_plan_name": self.tcinputs['derived_plan'],
                "storage": self.tcinputs['storage'],
                "allow_override": self.tcinputs['allow_override'],
                "backup_data": self.tcinputs['backup_data']
            }

            self.log.info("Logging in as MSP Admin")
            self.MSP_obj = MSPHelper(self.admin_console, self.commcell, self.mailbox)

            self.log.info("Creating a new company")
            self.MSP_obj.add_new_company(company_name=comp_details['name'],
                                         email=self.config.email.email_id,
                                         contact_name=comp_details['contact'],
                                         company_alias=comp_details['alias'],
                                         smtp=comp_details['smtp'],
                                         mail_template='Add company')

            self.MSP_obj.parse_email_reset(password=self.password)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.navigator.navigate_to_companies()
            self.__companies.access_company(self.company_name)
            self.MSP_obj.validate_plan_functionality(self.user_details, self.plan_details)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.mailbox.disconnect()
        self.log.info('Deleting the company')
        Organizations(self.commcell).delete(self.company_name)
