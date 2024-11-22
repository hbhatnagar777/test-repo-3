import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVWebAutomationException,CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages import Roles
from Web.AdminConsole.Helper import roles_helper, global_search_helper
from Server.Security.securityhelper import RoleHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Duplicate entity] - CRUD operations for Roles"
        self.browser = None
        self.admin_console = None
        self.role_names = []
        self.navigator = None
        self.role_helper = None
        self.roles = None
        self.gs_helper = None
        self.tcinputs = {
            "Company1": None,
            "Company2": None,
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
        self.role_helper = roles_helper.RolesMain(self.admin_console, self.commcell)
        self.roles = Roles.Roles(self.admin_console)
        self.gs_helper = global_search_helper.GlobalSearchHelper(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info("Step 1: Creating initial role")
            self.create_roles(name=f'Duplicate_Entity - role {str(time.time()).split(".")[0]}')
            self.validate_listing_and_global_search(suffix='Commcell', name_index=0)

            # switch to company1 tenant operator
            self.log.info("Step 2: Switching to Company1 and creating a role with swapped case name")
            self.create_roles(name=self.role_names[0].swapcase(), switch_company=True, company=self.tcinputs['Company1'])
            self.validate_listing_and_global_search(duplicate=True, suffix=self.tcinputs['Company1'], name_index=1)

            # switch to company2 tenant operator
            self.log.info("Step 3: Switching to Company2 and creating a new role")
            self.create_roles(name=f'Duplicate_Entity - role {str(time.time()).split(".")[0]}', switch_company=True,
                              company=self.tcinputs['Company2'])
            self.validate_listing_and_global_search(suffix='Commcell', name_index=2)

            # rename role
            self.log.info("Step 4: Renaming the second role and validating the listing grid")
            self.roles.select_role(self.role_names[2])
            self.roles.edit_role_name(self.role_names[1])

            self.validate_listing_and_global_search(duplicate=True, suffix=self.tcinputs['Company2'], name_index=1)

            # delete Roles created by tenant operators
            self.log.info("Step 5: Deleting the Roles and validating the final listing grid")
            self.roles.action_delete_role(role_name=self.role_names[1], company=self.tcinputs["Company2"])
            self.roles.action_delete_role(role_name=self.role_names[1], company=self.tcinputs["Company1"])

            self.validate_listing_and_global_search(suffix='Commcell', name_index=0)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        RoleHelper(self.commcell).cleanup_roles("duplicate_entity - role")
        RoleHelper(self.commcell).cleanup_roles("duplicate_entity - role")
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
            self.roles.add_role(role_name=name, permissions=permissions, is_tenant=True if switch_company else False)
            self.role_names.append(name)

            if switch_company:
                self.navigator.switch_company_as_operator('Reset')
        except Exception as exp:
            CVTestStepFailure(f'failed to create role : {exp}')

    @test_step
    def validate_listing_and_global_search(self,
                                           global_search: bool = True,
                                           listing: bool = True,
                                           duplicate: bool = False,
                                           suffix: str = None,
                                           name_index: int = None):
        """Validate role names in listing grid and global search results"""
        try:
            if global_search:
                gs_res = self.navigator.get_category_global_search("Roles", self.role_names[name_index])
                self.log.info(f'global search result : {gs_res}')
                if not duplicate:
                    if f'{self.role_names[name_index]} ({suffix})' in gs_res:
                        raise CVWebAutomationException(
                            "Company Name suffix displayed for non duplicate entity in global search.")
                    self.log.info('Company name suffix not displayed for non duplicate entity in global search.')
                else:
                    if f'{self.role_names[0]} (Commcell)' not in gs_res \
                            and f'{self.role_names[name_index]} ({suffix})' not in gs_res:
                        raise CVWebAutomationException(
                            "Company Name suffix not displayed for duplicate entity in global search results.")
                    self.log.info('Company name suffix displayed for duplicate entity in global search.')

            if listing:
                self.navigator.navigate_to_roles()
                list_res = self.roles.search_for(self.role_names[name_index])
                self.log.info(f'listing page result : {list_res}')
                if not duplicate:
                    if f'{self.role_names[name_index]} ({suffix})' in list_res:
                        raise CVWebAutomationException(
                            "Company Name suffix displayed for non duplicate entity in listing grid.")
                    self.log.info('Company name suffix not displayed for non duplicate entity in listing grid.')

                else:
                    if f'{self.role_names[0]} (Commcell)' not in list_res \
                            and f'{self.role_names[name_index]} ({suffix})' not in list_res:
                        raise CVWebAutomationException(
                            "Company Name suffix not displayed for duplicate entity in listing grid.")
                    self.log.info('Company name suffix displayed for duplicate entity in listing grid.')
        except Exception as exp:
            CVTestStepFailure(f'failed to validate : {exp}')
