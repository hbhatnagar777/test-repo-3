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
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    run()                           --  run function of this test case

    validate_redirect_url()         --  Check if redirect URL from API and redirected URL in Command Center are same

    validate_workload_company_landing_page()    --  Validate if the CC is redirected to correct
     landing page after clicking on the company

    validate_logout()               --  Validate logging out from SP also logs out from IDP

    tear_down()                     --  tear down function of this test case

"""

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
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
        self.name = "MSPTenantOnBoarding: Reseller user flow to operate tenant"
        self.config = get_config()
        self.master_company_name = None
        self.timestring = None
        self.master_company = None
        self.entities_to_delete = {}
        self.wl_commcell = None
        self.tcinputs = {
            "wl_webconsole_url": "",
            "MasterTAPassword": "",
            "MasterTAUsername": "",
            "WLCompany": ""
        }

    def setup(self):
        """Setup function of this test case"""
        self.password = self.tcinputs["MasterTAPassword"]
        self.workload_url = "http://" + self.tcinputs['wl_webconsole_url']
        self.wl_company_name = self.tcinputs["WLCompany"]

    @test_step
    def validate_redirect_url(self):
        """Check if redirect URL from API and redirected URL in Command Center are same"""
        wl_redirect_url = (self.commcell.organizations.all_organizations_props.get(self.wl_company_name.lower())[
            'redirect_url']).split("://")[1]

        if not wl_redirect_url.startswith((self.workload_url).split("://")[1]):
            raise Exception(f"Redirect URL set on reseller ring [{wl_redirect_url}] "
                            f"is not same as cloud/workload commcell [{self.workload_url}]")

    @test_step
    def validate_workload_company_landing_page(self):
        """Validate if the CC is redirected to correct landing page after clicking on the company"""
        self.navigator.navigate_to_companies()
        self.companies_object = Companies(self.admin_console)
        self.companies_object.access_company(self.wl_company_name)
        page_heading = self.admin_console.driver.title
        if page_heading != "Dashboard":
            raise Exception("Landing page should be company page")

        wl_ac_url = (self.admin_console.driver.current_url.split("/commandcenter")[0]).split("://")[1]

        if not (wl_ac_url in self.workload_url):
            raise Exception(f"The url got in command center[{wl_ac_url}]"
                            f"is not same as cloud/workload commcell [{self.workload_url}]")

    @test_step
    def validate_logout(self):
        """Validate logging out from SP also logs out from IDP"""
        self.admin_console.logout()
        self.admin_console.driver.get(f"http://{self.commcell.webconsole_hostname}")
        if self.admin_console._is_logout_page():
            raise Exception("The reseller commandcenter user should also be logged out")

    def run(self):
        """Run function of this test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(self.tcinputs["MasterTAUsername"], self.password)
            self.navigator = self.admin_console.navigator

            self.navigator.switch_company_as_operator(self.wl_company_name)
            GettingStarted(self.admin_console).mark_solution_complete("File servers")

            self.navigator.switch_service_commcell(self.commcell.commserv_name)

            self.validate_redirect_url()

            self.validate_workload_company_landing_page()

            self.validate_logout()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.browser.close_silently(self.browser)
