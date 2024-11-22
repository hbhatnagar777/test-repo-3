import datetime
import traceback
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.Common.exceptions import CVWebAutomationException
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from cvpysdk.commcell import Commcell
from Server.organizationhelper import OrganizationHelper
from time import sleep

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Global CC]: Validate Companies Functionality"
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            "ServiceCommcellHostName": "",
            "ServiceCommcellUserName": "",
            "ServiceCommcellPassword": ""
        }

    def setup(self):
        """Setup function of this test case"""
        # connect to service commcell
        self.service_commcell = Commcell(self.tcinputs["ServiceCommcellHostName"],
                                         self.tcinputs["ServiceCommcellUserName"],
                                         self.tcinputs["ServiceCommcellPassword"])
        self.service_commcell_commserv_name = self.service_commcell.commserv_name
        self.sc_org_helper = OrganizationHelper(self.service_commcell)
        
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator

        # switch to global view
        self.log.info("Switching to Global view...")
        self.navigator.switch_service_commcell('Global')

        self.company_alias = f"testingalias{datetime.datetime.strftime(datetime.datetime.now(), '%H%M')}"
        self.company_name = f"TC_70583_{datetime.datetime.strftime(datetime.datetime.now(), '%H%M%S')}"
        self.email = f"testuser@{self.company_alias}.com"
        self.__companies = Companies(self.admin_console)
        self.__company_details = CompanyDetails(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:

            retry_count = 5
            
            while retry_count:
                try:
                    self.create_company()

                    self.configure_company()

                    self.switch_back_to_global_view()

                    self.manage_tags()

                    self.deactivate_company()

                    self.activate_company()

                    self.delete_company()

                    break

                except Exception as exp:
                    if retry_count == 1:
                        raise exp

                    self.log.info(traceback.format_exc())

                    retry_count -= 1
                    self.log.info("TC Failed, trying again")
                    self.tear_down()
                    self.setup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.sc_org_helper.cleanup_orgs(marker='TC_70583')

    @test_step
    def create_company(self):
        """Test to check if company can be created from company page"""
        self.navigator.navigate_to_companies()
        self.__companies.add_company(company_name=self.company_name,
                                    email=self.email,
                                    contact_name="Test User",
                                    company_alias=self.company_alias,
                                    service_commcell=self.service_commcell_commserv_name)
        self.admin_console.wait_for_completion()
        
        # check if company is created on service commcell
        self.service_commcell.organizations.refresh()

        if not self.service_commcell.organizations.has_organization(self.company_name):
            raise CVWebAutomationException(f"Company {self.company_name} not created on service commcell: [{self.service_commcell_commserv_name}]")
        
        self.service_commcell_company = self.service_commcell.organizations.get(self.company_name)

        self.log.info(f"Company {self.company_name} created successfully on service commcell: [{self.service_commcell_commserv_name}]")

        # check if company is listed on global view
        if not self.__companies.company_exists(self.company_name, raise_error=False, status="Active"):
            raise CVWebAutomationException(f"Company {self.company_name} not listed on Global view")

        self.log.info("Successfully validated company creation on Global view")

    @test_step
    def switch_back_to_global_view(self):
        """Switch back to Global view from service commcell view"""
        self.admin_console.navigate(self.admin_console.base_url)
        sleep(30)
        self.navigator.switch_service_commcell('Global')
        self.admin_console.wait_for_completion()
        self.log.info(f"Switched back to Global view. URL: {self.admin_console.current_url()}")

    @test_step
    def configure_company(self):
        """Test to check if company details can be loaded from company page"""
        self.navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        sleep(30) # wait for redirection to company details page
        self.admin_console.wait_for_completion()
        
        # change focus to new tab
        self.log.debug(f'Before switching to service commcell tab, Number of tabs open = {len(self.admin_console.driver.window_handles)}')
        self.admin_console.driver.switch_to.window(self.admin_console.driver.window_handles[-1])

        # check if company details are loaded successfully on service commcell cc
        current_page_url = self.admin_console.current_url()

        if self.service_commcell.webconsole_hostname not in current_page_url or f'/subscriptions/{self.service_commcell_company.organization_id}' not in current_page_url:
            raise CVWebAutomationException(f"Company details failed to load on service commcell command center: [{self.service_commcell_commserv_name}] URL: {current_page_url}")

        # Try simple edit to check if company details are editable
        self.__company_details.edit_general_settings({"authcode": "ON"})
        self.service_commcell_company.refresh()
        if not self.service_commcell_company.auth_code:
            raise CVWebAutomationException("Failed to enable auth code for company")
        
        # close the tab and change the focus back to main tab (Global view)
        self.log.debug(f'Number of tabs open before closing service commcell tab: {len(self.admin_console.driver.window_handles)}')
        self.admin_console.driver.close()
        self.admin_console.driver.switch_to.window(self.admin_console.driver.window_handles[0])
        self.log.debug(f'Number of tabs open after closing service commcell tab: {len(self.admin_console.driver.window_handles)}')

        self.log.info("Company details loaded successfully and editable on service commcell command center")

    @test_step
    def deactivate_company(self):
        """Test to check if company can be deactivated from company page"""
        self.navigator.navigate_to_companies()
        self.__companies.deactivate_company(self.company_name)
        self.admin_console.wait_for_completion()

        # check if company is deactivated on service commcell
        self.service_commcell_company.refresh()
        
        if not self.service_commcell_company.is_backup_disabled:
            raise CVWebAutomationException("Backup activity not disabled")
        
        if not self.service_commcell_company.is_restore_disabled:
            raise CVWebAutomationException("Restore activity not disabled")
        
        if not self.service_commcell_company.is_login_disabled:
            raise CVWebAutomationException("Login activity not disabled")

        self.log.info(f"Company {self.company_name} deactivated successfully on service commcell: [{self.service_commcell_commserv_name}]")

        # check if company is listed under deactivated companies
        if not self.__companies.company_exists(self.company_name, raise_error=False, status="Deactivated"):
            raise CVWebAutomationException(f"Company {self.company_name} not listed under deactivated companies")
        
        # check if company is not listed under active companies
        if self.__companies.company_exists(self.company_name, raise_error=False, status="Active"):
            raise CVWebAutomationException(f"Company {self.company_name} listed under active companies")
        
        self.log.info("Successfully validated company deactivation on Global view")

    @test_step
    def activate_company(self):
        """Test to check if company can be activated from global company listing page"""
        self.navigator.navigate_to_companies()
        self.__companies.activate_company(self.company_name)
        self.admin_console.wait_for_completion()

        # check if company is activated on service commcell
        self.service_commcell_company.refresh()
        
        self.log.info('Checking if company is activated..')

        if self.service_commcell_company.is_backup_disabled:
            raise CVWebAutomationException("Backup activity not enabled")
        
        if self.service_commcell_company.is_restore_disabled:
            raise CVWebAutomationException("Restore activity not enabled")
        
        if self.service_commcell_company.is_login_disabled:
            raise CVWebAutomationException("Login activity not enabled")

        self.log.info(f"Company {self.company_name} activated successfully on service commcell: [{self.service_commcell_commserv_name}]")

        # check if company is listed under active companies
        if not self.__companies.company_exists(self.company_name, raise_error=False, status="Active"):
            raise CVWebAutomationException(f"Company {self.company_name} not listed under active companies")
        
        # check if company is not listed under deactivated companies
        if self.__companies.company_exists(self.company_name, raise_error=False, status="Deactivated"):
            raise CVWebAutomationException(f"Company {self.company_name} listed under deactivated companies")
        
        self.log.info("Successfully validated company activation on Global view")

    @test_step
    def delete_company(self):
        """Test to check if company can be deleted from company page"""
        self.navigator.navigate_to_companies()
        self.__companies.deactivate_and_delete_company(self.company_name)
        self.admin_console.wait_for_completion()

        # check if company is deleted on service commcell
        self.service_commcell.organizations.refresh()
        if self.service_commcell.organizations.has_organization(self.company_name):
            raise CVWebAutomationException(f"Company {self.company_name} not deleted on service commcell: [{self.service_commcell_commserv_name}]")
        
        self.log.info(f"Company {self.company_name} deleted successfully on service commcell: [{self.service_commcell_commserv_name}]")

        # check if company is not listed under active companies
        if self.__companies.company_exists(self.company_name, raise_error=False, status="Active"):
            raise CVWebAutomationException(f"Company {self.company_name} listed under active companies")
        
        # check if company is not listed under deactivated companies
        if self.__companies.company_exists(self.company_name, raise_error=False, status="Deactivated"):
            raise CVWebAutomationException(f"Company {self.company_name} listed under deactivated companies")
        
        self.log.info("Successfully validated company deletion on Global view")

    @test_step
    def manage_tags(self):
        """Test to check if tags can be managed for a company from global"""
        self.navigator.navigate_to_companies()
        tags = [
            {
            "name": "key1",
            "value": "value1"
            },
            {
            "name": "key2",
            "value": "value2"
            }
        ]

        # add tags
        self.__companies.add_tags(self.company_name, tags)

        # check if tags are added on service commcell
        self.service_commcell_company.refresh()

        # Remove 'id' key from each dictionary for comparison
        service_commcell_tags = [{k: v for k, v in item.items() if k != 'id'} for item in self.service_commcell_company.tags]
        if service_commcell_tags != tags:
            raise CVWebAutomationException(f"Failed to add tags to company from global view. Expected: {tags}, Actual: {self.service_commcell_company.tags}")
        
        self.log.info(f"Tags {tags} added successfully to company {self.company_name} on service commcell: [{self.service_commcell_commserv_name}]")

        # remove tags
        self.__companies.delete_tags(self.company_name, tags)

        # check if tags are removed on service commcell
        self.service_commcell_company.refresh()
        if self.service_commcell_company.tags:
            raise CVWebAutomationException(f"Failed to remove tags from company from global view. Tags: {self.service_commcell_company.tags}")
        
        self.log.info(f"Tags {tags} removed successfully from company {self.company_name} on service commcell: [{self.service_commcell_commserv_name}]")

        self.log.info("Successfully validated tag management on Global view")