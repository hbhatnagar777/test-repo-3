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

from AutomationUtils.cvtestcase import CVTestCase
from random import choice, randint
from Server.Plans.planshelper import PlansHelper
from Server.organizationhelper import OrganizationHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep, CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.Helper.PlanHelper import PlanMain

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
        self.name = "Plan association validation with company and FS client"
        self.tcinputs = {}

    def setup(self):
        """Setup function of this test case"""
        self.sdk_plans_helper = PlansHelper(commcell_obj=self.commcell)
        self.org_helper = OrganizationHelper(self.commcell)

        # file server details
        self.file_server_name = (
            self.tcinputs.get('file_server')
            or choice(list(self.commcell.clients.file_server_clients.values()))['displayName']
        )

        # set the names for companies and plans
        self.company_name = f'TC 62726 Company - {str(randint(0, 100000))}'
        self.plan_name_1 = f'TC 62726 Plan 1 - {str(randint(0, 100000))}'
        self.plan_name_2 = f'TC 62726 Plan 2 - {str(randint(0, 100000))}'

        # get storage pool name
        self.log.info('Getting storage pool name...')
        self.storage_name = self.sdk_plans_helper.get_storage_pool()

        # create required plans
        self.log.info('Creating plans...')
        self.commcell.plans.create_server_plan(
            plan_name=self.plan_name_1, backup_destinations=[{'storage_name': self.storage_name}]
        )
        self.commcell.plans.create_server_plan(
            plan_name=self.plan_name_2, backup_destinations=[{'storage_name': self.storage_name}]
        )

        # create required company
        self.log.info('Creating company along with plan...')
        self.company_details = self.org_helper.setup_company(company_name=self.company_name, plans=[self.plan_name_1])

        # login to CC
        self.log.info('Logging into Command Center...')
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode['commcell']['commcellUsername'],
            self.inputJSONnode['commcell']['commcellPassword'],
        )
        self.navigator = self.admin_console.navigator
        self.plans = Plans(self.admin_console)
        self.plan_details = PlanDetails(self.admin_console)
        self.plans_ui_helper = PlanMain(self.admin_console, self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            self.validate_plan_assoc_with_company()

            self.plans_ui_helper.validate_plan_assoc_with_fs_client(self.file_server_name, self.plan_name_1)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.sdk_plans_helper.cleanup_plans(marker='TC 62726')
        self.org_helper.cleanup_orgs(marker='TC 62726')

    @test_step
    def validate_plan_assoc_with_company(self) -> None:
        """Method to validate plan association / disassociation with company during / post company creation"""
        if not self.plans_ui_helper.is_plan_associated_with_company(self.plan_name_1, self.company_name):
            raise CVTestStepFailure('Failed to associate plan with company during company creation')
        
        self.plans_ui_helper.validate_plan_association_to_company(self.plan_name_2, self.company_name, old_plan=self.plan_name_1)
        self.plans_ui_helper.validate_plan_disassociation_from_company(self.plan_name_1, self.company_name)
