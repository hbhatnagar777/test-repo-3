# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Verifying the type filter on File Servers page

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    create_company()            --  Creates company if doesnt exist and creates tenant admin and tenant user
    
    start_job()                 --  Starts backup for subclient and keeps in suspended state
    
    msp_operator_test()         --  Tests job visibility for msp admin as company operator
    
    tenant_admin_test()         --  Tests job visibility for tenant admin
    
    tenant_user_test()          --  Tests job visibility for tenant user and also performs job operations
    
    job_operations_test()       --  Performs resume,suspend,kill and verifies result


Test pre-requisites:
    - Client, Agent, Backupset, Subclient must be provided
    - The client given must be valid for company migration

"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Server.Security.userhelper import UserHelper
from Server.organizationhelper import OrganizationHelper
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.jd_wait = None
        self.user_helper = None
        self.company_name1 = None
        self.company_name2 = None
        self.org_helper = None
        self.jobs_page = None
        self.name = "Multi-tenant job visibility"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            'ClientName': None,
            'AgentName': None,
            'BackupsetName': None,
            'SubclientName': None,
            'wait_time': None
        }

    def setup(self):
        if not self.subclient.plan:
            raise CVTestStepFailure("given subclient is not associated with any plan. please use a subclient with plan")
        self.org_helper = OrganizationHelper(self.commcell)
        self.user_helper = UserHelper(self.commcell)
        self.company_name1, self.company_name2 = "autotest_company1", "autotest_company2"
        self.create_company(self.company_name1)
        self.create_company(self.company_name2)
        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.jobs_page = Jobs(self.admin_console)
        self.jd_wait = self.tcinputs['wait_time']

    def run(self):
        self.client.change_company_for_client(self.company_name1)
        job_id = self.start_job()
        try:
            self.msp_operator_test(job_id, self.company_name1)
            self.tenant_admin_test(job_id, self.company_name1)

            self.admin_console.logout()
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.msp_operator_test(False, self.company_name2)
            self.tenant_admin_test(False, self.company_name2)
            self.tenant_user_test(False, self.company_name2)

            self.tenant_user_test(job_id, self.company_name1)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
            try:
                self.commcell.job_controller.get(job_id).kill(True)
            except:
                pass

        finally:
            self.client.change_company_for_client('CommCell')
            self.commcell.organizations.delete(self.company_name1)
            self.commcell.organizations.delete(self.company_name2)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def create_company(self, company_name):
        """ Creates company and tenant admin, tenant user if they don't already exist """
        if not self.commcell.organizations.has_organization(company_name):
            company_obj = self.org_helper.create(company_name, company_alias=company_name)
        else:
            company_obj = self.commcell.organizations.get(company_name)
        company_obj.plans = [self.subclient.plan]
        ta_name = f"{company_name}_admin"
        tu_name = f"{company_name}_user"
        if not self.commcell.users.has_user(f"{company_name}\\{ta_name}"):
            self.user_helper.create_user(
                f"{company_name}\\{ta_name}",
                email=f"{ta_name}@{company_name}.in",
                password=self.inputJSONnode['commcell']['commcellPassword'],
                local_usergroups=[company_name + '\\Tenant Admin']
            )
        if not self.commcell.users.has_user(f"{company_name}\\{tu_name}"):
            self.user_helper.create_user(
                f"{company_name}\\{tu_name}",
                email=f"{tu_name}@{company_name}.in",
                password=self.inputJSONnode['commcell']['commcellPassword'],
                local_usergroups=[company_name + '\\Tenant Users']
            )

    @test_step
    def start_job(self):
        """ starts backup job """
        bkp_job = self.subclient.backup("Full")
        bkp_job.pause(True)

    @test_step
    def msp_operator_test(self, job_id, company):
        """ Tests job visibility for admin as company operator """
        self.admin_console.navigator.switch_company_as_operator(company)
        self.admin_console.navigator.navigate_to_jobs()
        job_presence = self.jobs_page.if_table_job_exists(job_id, search=False)
        if not job_id:
            job_presence = not job_presence
        if not job_presence:
            raise CVTestStepFailure("company job not visible as admin operator")
        self.log.info("admin operator job visibility verified")

    @test_step
    def tenant_admin_test(self, job_id, company):
        """ Tests job visibility for tenant admin """
        self.admin_console.logout()
        self.admin_console.login(f"{company}\\{company}_admin",
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.navigator.navigate_to_jobs()
        job_presence = self.jobs_page.if_table_job_exists(job_id, search=False)
        if not job_id:
            job_presence = not job_presence
        if not job_presence:
            raise CVTestStepFailure("company job not visible as tenant admin")
        self.log.info("tenant admin job visibility verified")

    @test_step
    def tenant_user_test(self, job_id, company):
        """ Tests job visibility and operations for tenant user """
        self.admin_console.logout()
        self.admin_console.login(f"{company}\\{company}_user",
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.navigator.navigate_to_jobs()
        job_presence = self.jobs_page.if_table_job_exists(job_id, search=False)
        if not job_id:
            job_presence = not job_presence
        if not job_presence:
            raise CVTestStepFailure("company job not visible as tenant user")
        self.log.info("tenant user job visibility verified")
        if job_id:
            self.job_operations_test(job_id)
            self.log.info("tenant user job operations verified")

    @test_step
    def job_operations_test(self, job_id):
        """ Performs resume suspend kill and checks for status change """
        self.jobs_page.resume_job(job_id, search=False, wait=self.jd_wait)
        self.jobs_page.suspend_job(job_id, "Forever", wait=self.jd_wait)
        sleep(5)
        self.jobs_page.kill_job(job_id, search=False, wait=self.jd_wait)
