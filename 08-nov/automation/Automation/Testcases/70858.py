import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVWebAutomationException,CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages import server_groups
from Web.AdminConsole.Helper import serverGroup_helper, global_search_helper
from Server.servergrouphelper import ServerGroupHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Duplicate entity] - CRUD operations for server groups"
        self.browser = None
        self.admin_console = None
        self.server_groups_names = []
        self.navigator = None
        self.server_group_helper = None
        self.server_group = None
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
        self.server_group_helper = serverGroup_helper.ServerGroupMain(self.admin_console)
        self.server_group = server_groups.ServerGroups(self.admin_console)
        self.gs_helper = global_search_helper.GlobalSearchHelper(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info("Step 1: Creating initial server group")
            self.create_server_group(name=f'Duplicate_Entity - Server Group {str(time.time()).split(".")[0]}')
            self.validate_listing_and_global_search(suffix='Commcell', name_index=0)

            # switch to company1 tenant operator
            self.log.info("Step 2: Switching to Company1 and creating a server group with swapped case name")
            self.create_server_group(name=self.server_groups_names[0].swapcase(),
                                     switch_company=True,
                                     company=self.tcinputs['Company1'])
            self.validate_listing_and_global_search(duplicate=True, suffix=self.tcinputs['Company1'], name_index=1)

            # switch to company2 tenant operator
            self.log.info("Step 3: Switching to Company2 and creating a new server group")
            self.create_server_group(name=f'Duplicate_Entity - Server Group {str(time.time()).split(".")[0]}',
                                     switch_company=True,
                                     company=self.tcinputs['Company2'])
            self.validate_listing_and_global_search(suffix='Commcell', name_index=2)

            # rename server group
            self.log.info("Step 4: Renaming the second server group and validating the listing grid")
            self.server_group_helper.edit_serverGroup_name(new_name=self.server_groups_names[1])
            self.navigator.navigate_to_server_groups()

            self.validate_listing_and_global_search(duplicate=True, suffix=self.tcinputs['Company2'], name_index=1)

            # delete server groups created by tenant operators
            self.log.info("Step 5: Deleting the server groups and validating the final listing grid")
            self.server_group.delete_server_group(name=self.server_groups_names[1],
                                                  company=self.tcinputs["Company2"])
            self.server_group.delete_server_group(name=self.server_groups_names[1],
                                                  company=self.tcinputs["Company1"])
            self.server_group.reset_filters()

            self.validate_listing_and_global_search(suffix='Commcell', name_index=0)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        ServerGroupHelper(self.commcell).cleanup_server_groups("duplicate_entity - server group")
        ServerGroupHelper(self.commcell).cleanup_server_groups("duplicate_entity - server group")
        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    @test_step
    def create_server_group(self, name: str, switch_company: bool = False, company: str = None):
        """Create a server group and optionally switch company"""
        try:
            if switch_company:
                self.navigator.switch_company_as_operator(company)

            self.server_group_helper.serverGroup_name = name
            self.server_group_helper.add_new_manual_server_group()
            self.server_groups_names.append(name)
            self.navigator.navigate_to_server_groups()

            if switch_company:
                self.navigator.switch_company_as_operator('Reset')
        except Exception as exp:
            CVTestStepFailure(f'failed to create server group : {exp}')

    @test_step
    def validate_listing_and_global_search(self,
                                           global_search: bool = True,
                                           listing: bool = True,
                                           duplicate: bool = False,
                                           suffix: str = None,
                                           name_index: int = None):
        """Validate server group names in listing grid and global search results"""
        try:
            if global_search:
                gs_res = self.navigator.get_category_global_search("Server groups", self.server_groups_names[name_index])
                self.log.info(f'global search result : {gs_res}')
                if not duplicate:
                    if f'{self.server_groups_names[name_index]} ({suffix})' in gs_res:
                        raise CVWebAutomationException(
                            "Company Name suffix displayed for non duplicate entity in global search.")
                    self.log.info('Company name suffix not displayed for non duplicate entity in global search.')
                else:
                    if f'{self.server_groups_names[0]} (Commcell)' not in gs_res \
                            and f'{self.server_groups_names[name_index]} ({suffix})' not in gs_res:
                        raise CVWebAutomationException(
                            "Company Name suffix not displayed for duplicate entity in global search results.")
                    self.log.info('Company name suffix displayed for duplicate entity in global search.')

            if listing:
                list_res = self.server_group.search_for(self.server_groups_names[name_index])
                self.log.info(f'listing page result : {list_res}')
                if not duplicate:
                    if f'{self.server_groups_names[name_index]} ({suffix})' in list_res:
                        raise CVWebAutomationException(
                            "Company Name suffix displayed for non duplicate entity in listing grid.")
                    self.log.info('Company name suffix not displayed for non duplicate entity in listing grid.')

                else:
                    if f'{self.server_groups_names[0]} (Commcell)' not in list_res \
                            and f'{self.server_groups_names[name_index]} ({suffix})' not in list_res:
                        raise CVWebAutomationException(
                            "Company Name suffix not displayed for duplicate entity in listing grid.")
                    self.log.info('Company name suffix displayed for duplicate entity in listing grid.')
        except Exception as exp:
            CVTestStepFailure(f'failed to validate : {exp}')
