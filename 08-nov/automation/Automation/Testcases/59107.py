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

    validate_deleted_entities() -- Validates if entities are deleted after company deletion

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from datetime import datetime

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Helper.CompanyHelper import MSPHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.Companies import Companies


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
        self.name = "MSP Test case: Delete and Validation"
        self.navigator = None
        self.MSP_obj = None
        self.company_page_obj = None
        self.config = get_config()
        self.tcinputs = {
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.navigator = self.admin_console.navigator
        self.__table = Table(self.admin_console)
        self.__company_details = CompanyDetails(self.admin_console)
        self.MSP_obj = MSPHelper(admin_console=self.admin_console, commcell=self.commcell)
        self.company_page_obj = Companies(self.admin_console)

    @test_step
    def validate_deleted_entities(self):
        """Method to validate if entities are deleted after company deletion"""
        deleted_companies = self.company_page_obj.get_deleted_companies()
        if self.company_name in deleted_companies:
            return

        if self.company_page_obj.company_exists(self.company_name, False):
            raise Exception(
                f"The company {self.company_name} not present in the deleted tab after deletion but is present for 'all' tab"
            )

    def run(self):
        """Run function of this test case"""
        try:
            self.input_dict = {
                "company": {
                    "name": "TestCompany" + "_" + str(datetime.today())[-3:],
                    "alias": 'TestInc' + "_" + str(datetime.today())[-3:],
                    "smtp": 'hello.world{0}.com'.format(str(datetime.today())[-3:]),
                    "email": 'tadmin{0}@commvault.com'.format(str(datetime.today())[-3:]),
                    "contact_name": "TestName"
                }
            }
            self.username = self.input_dict['company']['alias'] + "\\" + self.config.email.email_id.split('@')[0]
            self.comp_details = self.input_dict['company']
            self.company_name = self.comp_details['name']
            self.log.info("Creating a new company")
            self.MSP_obj.add_new_company(company_name=self.comp_details['name'],
                                         email=self.comp_details['email'],
                                         contact_name=self.comp_details['contact_name'],
                                         company_alias=self.comp_details['alias'],
                                         smtp=self.comp_details['smtp'],
                                         mail_template='Add company')

            self.company_page_obj.company_exists(self.comp_details['name'])

            self.log.info("Deleting the newly created company")
            self.MSP_obj.delete_existing_company()

            self.validate_deleted_entities()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell.refresh()
        if self.commcell.organizations.get(self.company_name.lower()):
            self.commcell.organizations.delete(self.company_name.lower())

        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
