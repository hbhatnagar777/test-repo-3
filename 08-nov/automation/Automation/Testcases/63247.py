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

    tear_down()                     --  tear down function of this test case

    generate_workload_authtoken()   --  Method to create auth token for router CS

    create_reseller_master_company()--  Creates a master company and enable resller mode on it

    assign_wf_to_tenant_admin()     --  Associate user with role on the MSP Tenant onboarding workflow

    execute_tenant_onboarding_wf()  --  Executes MSP tenant onboarding workflow

    validate_company_listing_fanout()   --  Method to validate if company listing page has fanned out list

    validate_commcell_switcher()    --  Method to validate commcell switcher

    validate_company_switcher()     -- Validates if company switcher works

"""
import time

from cvpysdk.commcell import Commcell
from cvpysdk.workflow import WorkFlow

from Server.MultiCommcell.multicommcellhelper import MultiCommcellHelper
from Server.Workflow.workflowhelper import WorkflowHelper

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Server.organizationhelper import OrganizationHelper
from Server.Security.userhelper import UserHelper
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
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
        self.name = "{Ring routing} V2 Tenant Onboarding"
        self.config = get_config()
        self.master_company_name = None
        self.timestring = None
        self.master_company = None
        self.entities_to_delete = {}
        self.wl_commcell = None
        self.wl_company_list = []
        self.tcinputs = {
            "wf_path": "",
            "reseller_webconsole_url": "",
            "router": {
                "webconsoleurl": "",
                "username": "",
                "password": ""
            },
            "workload": {
                "webconsoleurl": ""
            },
            "workload2": {
                "webconsoleurl": ""
            }
        }

    def generate_workload_authtoken(self):
        """Method to create auth token for router CS"""
        self.wl_commcell = Commcell(webconsole_hostname=self.router_url, commcell_username=self.router_username,
                                    commcell_password=self.router_password)

        return self.wl_commcell.auth_token

    def setup(self):
        """Setup function of this test case"""
        self.timestring = str(time.time()).split(".")[0]
        self.org_helper = OrganizationHelper(self.commcell)
        self.wf_name = "MSPTenantOnboardingV2"
        self.wf_path = self.tcinputs["wf_path"]
        self.password = UserHelper(self.commcell).password_generator()
        self.workload_url = self.tcinputs['workload']['webconsoleurl']
        self.wl_company_name = f"WorkloadCompany{self.timestring}"
        self.wl_domain_name = f"WLCompanyAlias{self.timestring}"
        self.wl_email_domain_name = f"Test{self.timestring}@email.com"
        self.wf_helper = WorkflowHelper(self, self.wf_name)
        self.router_url = self.tcinputs['router']['webconsoleurl']
        self.router_username = self.tcinputs['router']['username']
        self.router_password = self.tcinputs['router']['password']
        self.workload_url2 = self.tcinputs['workload2']['webconsoleurl']
        self.reseller_url = self.inputJSONnode['commcell']['webconsoleHostname']
        self.mcc_inputs = {
            "IDPCommserver": self.router_url,
            "IDPadminUser": self.router_username,
            "IDPadminUserPwd": self.router_password
        }
        self.commcellname_map = MultiCommcellHelper(self.mcc_inputs).get_commcell_displayName_hostname_map()
        self.companies = None

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
    def validate_company_switcher(self):
        """Validates if company switcher works"""
        self.navigator.switch_company_as_operator(
            self.wf_company1 + f" ({self.commcellname_map[self.workload_url]})")
        self.mcchelper.validate_redirect(self.workload_url)

        self.navigator.switch_company_as_operator(
            self.wf_company2 + f" ({self.commcellname_map[self.workload_url2]})")
        self.mcchelper.validate_redirect(self.workload_url2)

    @test_step
    def validate_commcell_switcher(self):
        """Method to validate commcell switcher"""
        self.navigator.switch_service_commcell(self.commcellname_map[self.reseller_url])
        self.mcchelper.validate_redirect(self.reseller_url)

    @test_step
    def validate_company_listing_fanout(self):
        """Method to validate if company listing page has fanned out list"""
        self.navigator.navigate_to_companies()

        self.companies.companies_exist(self.wl_company_list)

        self.companies.access_self_company(self.wl_company_list[0], True)
        self.mcchelper.validate_redirect(self.workload_url)

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
                "workloadWebconsoleUrl": "https://" + self.workload_url,
                "qsdkToken": auth_token,
                "connectName": self.wl_company_name,
                "domainName": self.wl_domain_name,
                "emailDomainName": self.wl_email_domain_name,
                "adminFullName": f"Dummy{self.timestring}",
                "adminEmail": f"Dummy{self.timestring}@aa.com"
            }
            self.wf_company1 = workflowInput["connectName"]
            self.wl_company_list.append(workflowInput["connectName"])
            self.execute_tenant_onboarding_wf(workflowInput)

            workflowInput2 = {
                "workloadWebconsoleUrl": "https://" + self.workload_url2,
                "qsdkToken": auth_token,
                "connectName": self.wl_company_name + "2",
                "domainName": self.wl_domain_name + "2",
                "emailDomainName": self.wl_email_domain_name + "2",
                "adminFullName": f"Dummy{self.timestring}2",
                "adminEmail": f"Dummy{self.timestring}2@aa.com"
            }
            self.wf_company2 = workflowInput2["connectName"]
            self.wl_company_list.append(workflowInput2["connectName"])
            self.execute_tenant_onboarding_wf(workflowInput2)

            self.commcell.refresh()

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(self.master_ta_name, self.password)
            self.navigator = self.admin_console.navigator
            self.companies = Companies(self.admin_console)
            self.mcchelper = MultiCommcellHelper(self.mcc_inputs, self.admin_console)

            self.validate_company_switcher()

            self.validate_commcell_switcher()

            self.validate_company_listing_fanout()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        for entity in self.entities_to_delete:
            if entity == "Company":
                for i in self.entities_to_delete["Company"]:
                    self.log.info(f"Deleting company {i}")
                    self.commcell.organizations.delete(i.lower())

            if entity == "Role":
                for i in self.entities_to_delete["Role"]:
                    self.log.info(f"Deleting Role {i}")
                    self.commcell.roles.delete(i.lower())
