import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages import Roles
from Web.AdminConsole.Helper import roles_helper
from Server import organizationhelper
from Server.Security import securityhelper

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Duplicate entity] - Lookup validation for roles"
        self.browser = None
        self.admin_console = None
        self.role_name = f'Duplicate_Entity - role {str(time.time()).split(".")[0]}'
        self.navigator = None
        self.role_helper = None
        self.role = None
        self.organization_helper = None
        self.company = None
        self.user = None
        self.role_main_helper = None
        self.role_api_helper = None
        self.tcinputs = {
            "Company": None
        }

    def setup(self):
        """Setup function of this test case"""
        # open browser and login to CC
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.role_helper = roles_helper.RolesMain(self.admin_console)
        self.role = Roles.Roles(self.admin_console)
        self.organization_helper = organizationhelper.OrganizationHelper(self.commcell)
        self.role_api_helper = securityhelper.RoleHelper(self.commcell)

        # creating dummy entities
        self.company = self.organization_helper.create(
            name=f'duplicate entity - company {str(time.time()).split(".")[0]}').organization_name
        self.user = self.commcell.organizations.get(self.company).contacts_fullname[0]
        self.log.info(f'successfully created dummy entities : {self.company}, {self.user}')

    def run(self):
        """Run function of this test case"""
        try:
            # create a role as MSP and a duplicate roles as Tenant
            self.log.info("Step 1: Creating a role as MSP and a duplicate roles as Tenant")
            self.create_roles(name=self.role_name)
            self.create_roles(name=self.role_name, switch_company=True, company=self.tcinputs['Company'])

            # validating duplicate role lookup in various places
            self.log.info("Step 2: validating duplicate roles lookup in various places")
            validation_data = [
                ('COMPANY', self.company),
                ('USER', self.user)
            ]

            for entity_type, entity_name in validation_data:
                self.validate_roles(entity_type, self.role_name, entity_name)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    @test_step
    def create_roles(self, name: str, switch_company: bool = False, company: str = None):
        """Create a role and optionally switch company"""
        try:
            if switch_company:
                self.navigator.switch_company_as_operator(company)

            self.navigator.navigate_to_roles()
            permissions = ['Alert']
            self.role.add_role(role_name=name, permissions=permissions, is_tenant=True if switch_company else False)
            self.role_name = name

            if switch_company:
                self.navigator.switch_company_as_operator('Reset')
        except Exception as exp:
            CVTestStepFailure(f'failed to create role : {exp}')

    @test_step
    def validate_roles(self, entity_type: str, role_name: str, entity_name=None):
        """Helper function to validate roles from dropdowns."""
        roles_list = self.role_helper.roles_lookup(entity_type, role_name, entity_name)
        self.log.info(f"roles lookup for {entity_type}: {roles_list}")

        roles_with_suffix = [f'{self.role_name} (Commcell)', f'{self.role_name} ({self.tcinputs["Company"]})']

        if not all(item in roles_list for item in roles_with_suffix):
            raise CVTestStepFailure(f'Validation failed for {entity_type}')
        self.log.info(f"Validation successful for entity type : {entity_type}")

    @test_step
    def cleanup(self):
        """Cleanup function for dummy entities"""
        try:
            self.log.info('Starting cleanup process...')
            self.organization_helper.cleanup_orgs('duplicate entity - company')
            self.role_api_helper.cleanup_roles('Duplicate_Entity - role')
            self.role_api_helper.cleanup_roles('Duplicate_Entity - role')
            self.log.info("Cleanup process completed successfully.")
        except Exception as exp:
            self.log.error(f"Cleanup process failed: {exp}")
            raise


