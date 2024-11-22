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

    generate_workload_authtoken()   --  creates auth token for workload commcell

    create_reseller_master_company()--  creates a master company and enable resller mode on it

    assign_wf_to_tenant_admin()     --  associate user with role on the MSP Tenant onboarding workflow

    execute_tenant_onboarding_wf()  --  Executes MSP tenant onboarding workflow

    validate_redirect_url()         --  Check if redirect URL from API and redirected URL in Command Center are same

    validate_workload_company_landing_page()    --  Validate if the CC is redirected to correct
     landing page after clicking on the company

    validate_logout()               --  Validate logging out from SP also logs out from IDP

    validate_company_landing_after_unlinking()  --  Validate that company is not redirected to other commcell
                                                    after unlinking

    tear_down()                     --  tear down function of this test case

"""
import time

from cvpysdk.commcell import Commcell
from cvpysdk.workflow import WorkFlow
from Server.Workflow.workflowhelper import WorkflowHelper

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Server.organizationhelper import OrganizationHelper
from Server.Security.userhelper import UserHelper
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
        self.name = "MSPTenantOnBoarding: Acceptance testcase for basic flow"
        self.config = get_config()
        self.master_company_name = None
        self.timestring = None
        self.master_company = None
        self.entities_to_delete = {}
        self.wl_commcell = None
        self.tcinputs = {
            "workload": {
                "webconsoleurl": "",
                "username": "",
                "password": ""
            }
        }

    def generate_workload_authtoken(self):
        """Method to create auth token for workload CS"""
        self.wl_commcell = Commcell(webconsole_hostname=self.workload_url, commcell_username=self.workload_username,
                               commcell_password=self.workload_password)

        return self.wl_commcell.auth_token

    def setup(self):
        """Setup function of this test case"""
        self.timestring = str(time.time()).split(".")[0]
        self.org_helper = OrganizationHelper(self.commcell)
        self.wf_name = "MSPTenantOnboarding"
        self.wf_path = self.tcinputs["wf_path"]
        self.password = UserHelper(self.commcell).password_generator()
        self.workload_url = self.tcinputs['workload']['webconsoleurl']
        self.workload_username = self.tcinputs['workload']['username']
        self.workload_password = self.tcinputs['workload']['password']
        self.wl_company_name = f"WorkloadCompany{self.timestring}"
        self.wl_domain_name = f"WLCompanyAlias{self.timestring}"
        self.wl_email_domain_name = f"Test{self.timestring}@email.com"
        self.wf_helper = WorkflowHelper(self, self.wf_name)

    @test_step
    def create_reseller_master_company(self):
        """Creates a master company and enable resller mode on it"""
        self.log.info("Creating master company")
        self.log.info(f"Password for TA {self.password}")
        self.master_company_name = f"TestMasterCompany{self.timestring}"
        self.master_company_details = self.org_helper.setup_company(company_name=self.master_company_name,
                                                                    ta_password=self.password)
        self.entities_to_delete["Company"] = [self.master_company_name]
        self.master_company = self.master_company_details['company_obj']
        self.log.info(f"Created Master company {self.master_company_name}")

        self.master_org_helper = OrganizationHelper(self.commcell, self.master_company_name)
        self.log.info("Enabling reseller mode on master company")
        self.master_org_helper.enable_reseller_and_verify()

    @test_step
    def assign_wf_to_tenant_admin(self):
        """Associate user with role on the MSP Tenant onboarding workflow"""
        RoleName = f"ExecuteWF{self.timestring}"
        self.log.info(f"Creating role with RoleName {RoleName}")
        self.commcell.roles.add(RoleName, ["Execute Workflow", "Edit Workflow"], ["commcell"])
        self.entities_to_delete['Role'] = [RoleName]
        self.log.info(f"Created role with RoleName {RoleName}")

        dict_ = {
            "assoc1":
                {
                    "workflowName": [self.wf_name],
                    "role": [RoleName]
                }
        }
        self.master_company_ta.update_security_associations(dict_, "UPDATE")
        self.log.info(f"Associated role {RoleName} to user {self.master_company_ta.user_name} "
                      f"on Workflow {self.wf_name}")
        self.master_company_ta.refresh()

    @test_step
    def execute_tenant_onboarding_wf(self, workflowInput):
        """Executes MSP tenant onboarding workflow"""
        executeWorkflow = WorkFlow(self.master_company_details["ta_loginobj"], workflow_name=self.wf_name)

        self.entities_to_delete["Company"].append(self.wl_company_name)

        self.log.info(f"Executing workflow with following inputs: {workflowInput}")

        executeWorkflow.execute_workflow(workflow_inputs=workflowInput)
        self.log.info(f"Finished executing workflow")

    @test_step
    def validate_redirect_url(self, workflowInput):
        """Check if redirect URL from API and redirected URL in Command Center are same"""
        wl_redirect_url = (self.commcell.organizations.all_organizations_props.get(self.wl_company_name.lower())[
            'redirect_url']).split("://")[1]

        if not wl_redirect_url.startswith((workflowInput['workloadWebconsoleUrl']).split("://")[1]):
            raise Exception(f"Redirect URL set on reseller ring [{wl_redirect_url}] "
                            f"is not same as cloud/workload commcell [{workflowInput['workloadWebconsoleUrl']}]")

    @test_step
    def validate_workload_company_landing_page(self, workflowInput):
        """Validate if the CC is redirected to correct landing page after clicking on the company"""
        self.navigator.navigate_to_companies()
        self.companies_object = Companies(self.admin_console)
        self.companies_object.access_company(self.wl_company_name)
        page_heading = self.admin_console.driver.title
        if page_heading != "Dashboard":
            raise Exception("Landing page should be company page")

        wl_ac_url = (self.admin_console.driver.current_url.split("/commandcenter")[0]).split("://")[1]

        if not (wl_ac_url in workflowInput['workloadWebconsoleUrl']):
            raise Exception(f"The url got in command center[{wl_ac_url}]"
                            f"is not same as cloud/workload commcell [{workflowInput['workloadWebconsoleUrl']}]")

    @test_step
    def validate_logout(self):
        """Validate logging out from SP also logs out from IDP"""
        self.admin_console.logout()
        self.admin_console.driver.get(f"http://{self.commcell.webconsole_hostname}")
        if self.admin_console._is_logout_page():
            raise Exception("The reseller commandcenter user should also be logged out")

    @test_step
    def validate_company_landing_after_unlinking(self):
        """Validate that company is not redirected to other commcell after unlinking"""
        self.admin_console.login(self.master_ta_name, self.password)
        self.navigator.navigate_to_companies()
        self.companies_object.unlink_company(self.wl_company_name)

        self.navigator.navigate_to_companies()
        self.companies_object.access_company(self.wl_company_name)
        if (self.admin_console.driver.current_url.split("/commandcenter")[0]).split("://")[1] \
                != self.commcell.webconsole_hostname:
            raise Exception("The commandcenter should not be redirected to workload commcell")

    def run(self):
        """Run function of this test case"""
        try:
            if not self.wf_helper.workflow_obj:
                self.wf_helper.import_workflow(self.wf_path)
                self.wf_helper.deploy_workflow()

            self.create_reseller_master_company()

            self.master_ta_name = self.master_company_details['ta_name']
            self.master_company_ta = self.commcell.users.get(self.master_ta_name)
            self.master_ta_email = self.master_company_ta.email

            self.assign_wf_to_tenant_admin()

            auth_token = self.generate_workload_authtoken()
            self.log.info(f"Generated auth token for workload commcell : {auth_token}")

            workflowInput = {
                "workloadWebconsoleUrl": "http://" + self.workload_url,
                "qsdkToken": auth_token,
                "connectName": self.wl_company_name,
                "domainName": self.wl_domain_name,
                "emailDomainName": self.wl_email_domain_name,
                "adminFullName": f"Dummy{self.timestring}",
                "adminEmail": f"Dummy{self.timestring}@aa.com"
            }

            self.execute_tenant_onboarding_wf(workflowInput)

            plan_dict = self.wl_commcell.plans.all_plans
            plan = list(plan_dict.keys())[0]

            self.wl_commcell.organizations.get(self.wl_company_name).plans = [plan]

            self.commcell.refresh()

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(self.master_ta_name, self.password)
            self.navigator = self.admin_console.navigator

            self.navigator.switch_company_as_operator(self.wl_company_name)
            GettingStarted(self.admin_console).mark_solution_complete("File servers")

            self.navigator.switch_service_commcell(self.commcell.commserv_name)

            self.validate_redirect_url(workflowInput)

            self.validate_workload_company_landing_page(workflowInput)

            self.validate_logout()

            self.validate_company_landing_after_unlinking()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        for entity in self.entities_to_delete:
            if entity == "Company":
                for i in self.entities_to_delete["Company"]:
                    self.log.info(f"Deleting company {i}")
                    self.commcell.organizations.delete(i.lower())
                    self.wl_commcell.organizations.delete(i.lower())

            if entity == "Role":
                for i in self.entities_to_delete["Role"]:
                    self.log.info(f"Deleting Role {i}")
                    self.commcell.roles.delete(i.lower())

        self.browser.close_silently(self.browser)
