'''
Created on 22-Mar-2021

@author: admin
'''

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Laptop.laptophelper import LaptopHelper
from Web.AdminConsole.AdminConsolePages.regions import Regions
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.Components.table import Rtable
import re


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Laptop] [Elastic Plan]: Validation of Elastic Plan Creation"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.plan_obj = None
        self.tcinputs = {
            "PlanName": None,
            "Region": None,
            "user": None,
            "usergroup": None
        }
        self.lap_obj = None
        self._utility = None

    def setup(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'],
                                     stay_logged_in=True)
            self._commcell.is_linux_commserv = False
            self.lap_obj = LaptopHelper(self)
            self.lap_obj.tc.log_step("""
                            1. Create Elastic Laptop Plan by adding the region based storage 

                            2. Verify for each region, new storage policy created 

                                NOTE: Region based Rules and associated Storage policies will be available in 
                                "App_PlanRule"

                            3. Associate the User to Elastic Plan and user should be added successfully

                            4. Add the user group to Elastic Plan and group should be added successfully
                            
                            5. Delete Elastic Plan and verify associated storage policies deleted successfully
                            
                                NOTE: Verify Associated storage policies and rules from App_planRule table
                            
                        """, 200)
            self.navigator = self.admin_console.navigator
            self.plan_obj = PlanMain(self.admin_console)
            self._utility = OptionsSelector(self._commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        try:
            self.create_plan()
            self.log.info(f"Added a laptop plan: {self.plan_obj.plan_name['laptop_plan']}")
            self.log.info("Converting into elastic plan by adding region based storage")
            plan_obj = {"Name": self.tcinputs["PlanName"], "Region": self.tcinputs["Region"]}
            self.navigator.navigate_to_plan()
            Plans(self.admin_console).select_plan(plan_obj.get("Name"))
            PlanDetails(self.admin_console).convert_elastic_plan(plan_obj, self.tcinputs['Secondary_storage'])
            self.log.info("Added Region Based Storage to the plan")
            self.verify_region_based_storage()
            plan_id = self.get_planid()
            self.verify_api(plan_id)
            self.log.info("Associating User and User Group to the Plan")
            self.associate_user_groups()
            self.plan_obj.delete_plans()
            self.verify_region_based_storage()
            self.verify_api(plan_id)
        except Exception as ex:
            handle_testcase_exception(self, ex)

    def tear_down(self):
        self._commcell.refresh()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

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

    def verify_region_based_storage(self):
        """ Verifies storage rules in the regions after elastic plan creation """
        self.log.info("Checking storage policy in regions")
        regions = self.tcinputs["Region"]
        for region in regions:
            if '(' in region:
                region = re.search(r'\(([^)]+)', region).group(1)
            self.navigator.navigate_to_regions()
            Regions(self.admin_console).access_region_details(region)
            self.admin_console.driver.find_elements(By.XPATH, 
                "//*[contains(@class,'MuiTab-root')]")[2].click()
            list_of_plans = Rtable(self.admin_console, title='Associated region based plans')\
                .get_column_data('Plan name')
            self.log.info(f"Column Names: {list_of_plans}")
            if self.plan_obj.plan_name['laptop_plan'] not in list_of_plans:
                self.log.info(f"Region {region} does not have the plan, {self.plan_obj.plan_name['laptop_plan']}")
            else:
                self.log.info(f"Validated: Laptop Plan {self.plan_obj.plan_name['laptop_plan']} is correctly attached to the region {region}")

    def associate_user_groups(self):
        """ Associates users and user groups to the elastic plan """
        self.navigator.navigate_to_plan()
        Plans(self.admin_console).select_plan(self.plan_obj.plan_name['laptop_plan'])
        PlanDetails(self.admin_console).edit_plan_associate_users_and_groups(self.tcinputs["user"])
        PlanDetails(self.admin_console).edit_plan_associate_users_and_groups(self.tcinputs["usergroup"])
        PlanDetails(self.admin_console).remove_associated_users_and_groups(user_user_group_de_association=
                                                                           {"DeleteAll": True,
                                                                            "DeleteAllUsers": False,
                                                                            "DeleteAllUserGroups": False,
                                                                            "Delete_Specific_user_or_group": False}
                                                                           )

    def get_planid(self):
        """ Fetches the plan ID of the plan, for further use """
        req_url = self.commcell._services.get("PLANS")
        bRes, response = self.commcell._cvpysdk_object.make_request("GET", req_url)
        if not bRes:
            raise Exception("Failed to get the Plan Information")
        if response.status_code != 200:
            self.log.error(f"Failed to get the API response, getting status code: {response.status_code}")
            raise Exception("Failed to get the planID")
        plans = response.json().get("plans", {})
        for i in plans:
            if i.get("plan").get("planName") == self.plan_obj.plan_name['laptop_plan']:
                return i.get("plan").get("planId")

    def verify_api(self, plan_id):
        """ Sends API request and displays the plan rule information for a plan """
        req_url = self.commcell._services.get("PLAN") % (int(plan_id))
        bRes, response = self.commcell._cvpysdk_object.make_request("GET", req_url)
        if not bRes:
            self.log.error("Failed to get the Plan Information")
        if response.status_code != 200:
            self.log.error(f"Failed to get the API response, getting status code: {response.status_code}")
            return
        rule_names = []
        storage_pools = []
        regions = []
        for i in response.json().get("plan").get("storageRules").get("rules"):
            if self.plan_obj.plan_name['laptop_plan'] in i.get("rule").get("ruleName"):
                regions.append(i.get("regions").get("region")[0].get("displayName"))
                storage_pools.append(i.get("storagePool").get("storagePoolName"))
                rule_names.append(i.get("rule").get("ruleName"))
        self.log.info("********** Response from the API *************")
        self.log.info(f"Rule Names: {rule_names}")
        self.log.info(f"Storage Pools: {storage_pools}")
        self.log.info(f"Regions: {regions}")
