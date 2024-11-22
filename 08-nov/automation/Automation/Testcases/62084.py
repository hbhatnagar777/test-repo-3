import datetime
import traceback
from AutomationUtils import logger
from AutomationUtils.config import get_config
from Web.AdminConsole.AdminConsolePages.Companies import Companies

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.CompanyHelper import MSPHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[CC Acceptance] Companies: CRUD operations on company"
        self.browser = None
        self.admin_console = None
        self.config = None
        self.exp = None
        self.logger = logger.get_log()

    def setup(self):
        """Setup function of this test case"""
        self.config = get_config()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.company_alias = "testing_alias_" + \
                             datetime.datetime.strftime(datetime.datetime.now(), '%H_%M')
        self.company_name = "Company_" + \
                            datetime.datetime.strftime(datetime.datetime.now(), '%H_%M_%S')
        self.email = self.config.MSPCompany.company.email
        self.msp_object = MSPHelper(admin_console=self.admin_console,
                                    commcell=self.commcell,
                                    csdb=self.csdb)
        self.__companies = Companies(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:

            retry_count = 5
            while retry_count:
                try:
                    self.create_company()

                    self.validate_active_company_list()

                    self.validate_deactivated_company_list()

                    self.validate_deleted_company()
                    break

                except Exception as exp:
                    if retry_count == 1:
                        raise exp

                    self.logger.info(traceback.format_exc())
                    all_companies = self.commcell.organizations.all_organizations
                    if self.company_name in all_companies.keys():
                        self.commcell.organizations.delete(self.company_name)

                    retry_count -= 1
                    self.logger.info("TC Failed, trying again")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            self.commcell.organizations.delete(self.company_name)
        except:
            self.log.info("Company does not exist; skip deleting")

        self.browser.close()

    @test_step
    def create_company(self):
        """Test to check if company can be created from company page"""
        self.msp_object.add_new_company(company_name=self.company_name,
                                        email=self.email,
                                        contact_name="test User",
                                        company_alias=self.company_alias)

    @test_step
    def validate_active_company_list(self):
        """Validates if all the active companies are shown on company page"""
        self.msp_object.validate_active_company_list()

    @test_step
    def validate_deactivated_company_list(self):
        """Validates if all the deactivated companies are listed on company page"""
        self.__companies.deactivate_company(self.company_name)
        self.msp_object.validate_deactivated_company_list()

    @test_step
    def validate_deleted_company(self):
        """Test to check if company can be deleted from company page and validate if deleted companies are listed"""
        self.__companies.delete_company(self.company_name)
        self.msp_object.validate_deleted_company_list()
