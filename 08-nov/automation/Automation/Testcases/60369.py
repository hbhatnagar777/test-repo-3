# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for [Laptop] [Elastic Plan] - Validation of Laptop activation with Elastic Plan

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails


class TestCase(CVTestCase):
    """Test case class for validating [Laptop] [Elastic Plan] - Validation of Laptop activation with Elastic Plan"""

    # PRE-REQUISITES OF THE TESTCASE
    # - Tenant_company and Default_Plan should be created on commcell

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop] [Elastic Plan] - Validation of Laptop activation with Elastic Plan"""
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.plan_obj = None
        self.table = None
        self.company_details = None
        self.tcinputs = {
            "Default_Plan": None,
            "PlanName": None,
            "Region": None,
            "Primary_storage": None,
            "user": None
        }

    def setup(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'],
                                     stay_logged_in=True)
            self.navigator = self.admin_console.navigator
            self.plan_obj = PlanMain(self.admin_console)
            self.table = Table(self.admin_console)
            self.company_details = CompanyDetails(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def create_plan(self):
        """ Creation of the plan """
        self.log.info(f"Creating Laptop Plan: {self.tcinputs['PlanName']}")
        self.navigator.navigate_to_plan()
        self.plan_obj.plan_name = {"laptop_plan": self.tcinputs["PlanName"]}

        self.plan_obj.storage = {'pri_storage': self.tcinputs['Primary_storage']}

        self.plan_obj.retention = {}

        self.plan_obj.rpo_hours = '10'
        self.plan_obj.backup_data = {'file_system': [],
                                     'content_backup': [],
                                     'content_library': [],
                                     'custom_content': [],
                                     'exclude_folder': [],
                                     'exclude_folder_library': [''],
                                     'exclude_folder_custom_content': ['']}

        self.plan_obj.allow_override = {}

        self.plan_obj.allowed_features = {
            "Edge Drive": "OFF",
            "audit_drive_operations": "False",
            "notification_for_shares": "False",
            "edge_drive_quota": "0",
            "DLP": "OFF",
            "Archiving": "OFF"}

        self.plan_obj.user_usergroup_association = []

        self.plan_obj.add_plan()
        self.log.info("""***** Laptop Plan [{0}] created successfully *****""".format(self.tcinputs["PlanName"]))

    def assign_plans_to_company(self):
        """ Associating the plan with Company"""
        self.navigator.navigate_to_companies()
        self.table.access_link(self.tcinputs['Tenant_company'])
        self.company_details.edit_company_plans([self.plan_obj.plan_name['laptop_plan']],
                                                laptop_default_plan=self.plan_obj.plan_name['laptop_plan'])
        self.log.info(""" ***** Associated plans to company {0} successfully *****"""
                      .format(self.tcinputs['Tenant_company']))

    def run(self):
        """ Main function for test case execution."""
        laptop_helper = None
        try:
            default_plan = self.tcinputs['Default_Plan']
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company3'))
            self.tcinputs['Default_Plan'] = default_plan
            self.create_plan()
            self.log.info(f"Added a laptop plan: {self.plan_obj.plan_name['laptop_plan']}")
            plan_obj = {"Name": self.tcinputs["PlanName"], "Region": self.tcinputs["Region"]}
            self.assign_plans_to_company()
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            # -------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                1. Enable auth code and set Default plan for Tenant company
                
                2. Activate and verify auto-activation of laptop with elastic plan

                3. After laptop activated verify below to make sure it activated to correct region

                    a. Region set correctly from laptop summary section

                    b. Verify from adminconsole --> manage --> regions, laptop is showing from correct Region

                    c. Verify correct Storage Policy is associated to subclient

                    d. Backup complete successfully

                    e. Restore should work without any issue  
            """, 200)
            install_authcode = laptop_helper.set_authcode()
            self.refresh(install_authcode)
            self.log.info("Converting into elastic plan by adding region based storage")
            self.navigator.navigate_to_plan()
            Plans(self.admin_console).select_plan(plan_obj.get("Name"))
            PlanDetails(self.admin_console).convert_elastic_plan(plan_obj, self.tcinputs['Secondary_storage'])
            self.navigator.navigate_to_plan()
            Plans(self.admin_console).select_plan(self.plan_obj.plan_name['laptop_plan'])
            PlanDetails(self.admin_console).edit_plan_associate_users_and_groups(self.tcinputs["user"])
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            laptop_helper.validate_laptop_elasticplan_association(self.admin_console, self.tcinputs, self.config_kwargs)
            laptop_helper.validate_postactivation_laptop_region_association(self.admin_console, self.tcinputs)
            laptop_helper.validate_backup_and_restore(self.admin_console, self.tcinputs)
            self.navigator.navigate_to_plan()
            Plans(self.admin_console).select_plan(plan_obj.get("Name"))
            PlanDetails(self.admin_console).remove_associated_users_and_groups(user_user_group_de_association=
                                                                               {"DeleteAll": True,
                                                                                "DeleteAllUsers": False,
                                                                                "DeleteAllUserGroups": False,
                                                                                "Delete_Specific_user_or_group": False}
                                                                               )
            self.plan_obj.delete_plans()
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            handle_testcase_exception(self, excp)
            laptop_helper.cleanup(self.tcinputs)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def refresh(self, authcode):
        """ Refresh the dicts
        Args:
            authcode (str): Authcode for organization

        """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': True,
            'org_set_default_plan': True,
            'override_auth_code': False
        }

        self.install_kwargs = {
            'install_with_authcode': True,
            'execute_simcallwrapper': False,
            'authcode': authcode,
            'wait_for_reinstalled_client': True
        }

        self.custompackage_kwargs = {
            'authcode_flag': True
        }