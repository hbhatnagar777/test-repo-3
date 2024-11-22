# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""
import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Server.serverhelper import ServerTestCases
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails


class TestCase(CVTestCase):
    """[Laptop] [Admin Console]: Derived Plan validation with override restriction as optional"""
    test_step = TestStep()
    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [Admin Console]: Derived Plan validation with override restriction as optional"
        self.browser = None
        self.admin_console = None
        self.plan_obj = None
        self.plans = None
        self.derivedplan_obj = None
        self.base_plan_name = None
        self.table = None
        self.derived_plan = None
        self.company_details = None
        self.server_obj = None
        self.navigator = None
        self.plan_inputs = None

    @test_step
    def create_base_plan(self):
        """ Creation of the Base plan """
        self.navigator.navigate_to_plan()
        plan_names = self.table.get_column_data('Plan name')
        if self.base_plan_name in plan_names:
            self.plans.delete_plan(self.base_plan_name)
            self.admin_console.wait_for_completion()

        self.plan_obj.storage = {'pri_storage': self.plan_inputs['Primary_storage']}
        self.plan_obj.retention = {'deleted_item_retention': {'value': '2', 'unit': ['year(s)']},
                                   'file_version_retention': {'duration': None,
                                                              'versions': 5,
                                                              'rules': {'days': '0',
                                                                        'weeks': '0',
                                                                        'months': '0'}}}

        self.plan_obj.alerts = {"Backup" : "No backup for last 4 days",
                                "Jobfail": "Restore Job failed",
                                "edge_drive_quota":"Edge drive quota alert",
                                "file_system_quota":"File system quota alert"}

        self.plan_obj.allowed_features = {
            "DLP": "OFF"
        }
        self.plan_obj.backup_data = None
        self.plan_obj.user_usergroup_association = []

        self.plan_obj.add_plan()
        self.log.info(""" ***** BasePlan [{0}] created successfully *****""".format(self.base_plan_name))

    @test_step
    def override_required_for_base_plan(self):
        """ Allowing base plan to be overridden, with all parameters as Override optional """
        self.plan_obj.edit_plan_dict = {
            "throttle_send": "",
            "throttle_receive": "",
            "file_system_quota": None,
            "rpo_hours": None,
            "additional_storage": None,
            "allowed_features": None,
            "backup_data": "",
            "alerts": None,
            "override_restrictions": {"Storage pool": "Override optional",
                                      "RPO": "Override optional",
                                      "Backup content": "Override optional",
                                      "Retention": "Override optional"}}
        self.plan_obj.retention = None
        self.plan_obj.edit_laptop_plan()
        self.log.info(""" ***** Override restrictions set successfully at base plan*****""")

    @test_step
    def assigin_plan_to_company(self):
        """ Associating the Base plan with Company"""
        self.navigator.navigate_to_companies()
        self.table.access_link(self.plan_inputs['Tenant_company'])
        self.company_details.edit_company_plans([self.base_plan_name],
                                                laptop_default_plan=self.base_plan_name)

        self.log.info(""" ***** Associated BasePlan {0} to company {1} successfully *****"""
                      .format(self.base_plan_name, self.plan_inputs['Tenant_company']))

    @test_step
    def create_derived_plan(self):
        """ Creation of the Derived plan as tenant admin"""
        self.plan_obj.allow_override = {"Storage_pool": "Override optional",
                                        "RPO": "Override optional",
                                        "Folders_to_backup": "Override optional",
                                        "Retention": "Override optional"}
        self.plan_obj.backup_data = {'file_system': ["Windows"],
                                     'content_backup': [],
                                     'content_library': [],
                                     'custom_content': ['C:\\From_Derived_content'],
                                     'exclude_folder': [],
                                     'exclude_folder_library': [''],
                                     'exclude_folder_custom_content': ['C:\\From_Derived_Filter']}
        self.plan_obj.rpo_hours = 20
        self.plan_obj.retention = {'deleted_item_retention': {'value': '10', 'unit': ['year(s)']},
                                   'file_version_retention': {'duration': None,
                                                              'versions': 10,
                                                              'rules': {'days': '0',
                                                                        'weeks': '0',
                                                                        'months': '0'}}}

        self.plan_obj.storage = None
        self.plan_obj.add_laptop_derivedplan()
        self.log.info(""" ***** Derived Plan [{0}] created successfully *****""".format(self.derived_plan))

    @test_step
    def validate_overriding(self):
        """ Validation of override restrictions and inheritance"""

        override_entities = {
            'Backup content': {'Windows': ['Desktop', 'Documents', 'User Settings', 'C:\\From_Derived_content'],
                               'Mac': ['Desktop', 'Documents', 'User Settings'],
                               'Unix': ['Desktop', 'Documents']},
            'Inherit settings': {'Base plan': self.base_plan_name,
                                 'Storage pool': 'Inheriting from base plan',
                                 'RPO': 'Overriding base plan',
                                 'Folders to backup': 'Overriding base plan',
                                 'Retention': 'Overriding base plan'},
            'RPO': {'Backup frequency': 'Runs every 20 hour(s)'},
            'Retention': {'Deleted item retention': '10 year(s)', 'File versions': '10 versions'},
            'Backup destinations': [self.plan_inputs['Primary_storage']]}

        self.plan_obj.validate_derivedplan_overriding(override_entities)
        self.log.info(""" ***** Validation of override restrictions and inheritance completed successfully *****""")


    @test_step
    def login_to_adminconsole(self, login_username, login_password):
        """ Login to adminconsole with given user """

        self.log.info(""" Initialize browser objects """)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(login_username,
                                 login_password)
        self.log.info(""" Logged into adminconsole with {0} successfully""".format(login_username))
        self.plan_obj = PlanMain(self.admin_console, self.commcell)
        self.plans = Plans(self.admin_console)
        self.company_details = CompanyDetails(self.admin_console)
        self.base_plan_name = "Automation_Base_58166" 
        self.derived_plan = "Automation_derived_58166"
        self.plan_obj.plan_name = {"laptop_plan": self.base_plan_name}
        self.plan_obj.derived_plan = self.derived_plan
        self.navigator = self.admin_console.navigator
        self.table = Rtable(self.admin_console)

    def run(self):

        try:
            self.server_obj = ServerTestCases(self)
            #-------------------------------------------------------------------------------------
            self.server_obj.log_step("""
                1. Login to Adminconsole as MSP admin
                2. Create Base Plan AS MSP Admin With required components as "override optional"
                  [Backup content as "Required" and Retention as "Optional"]
                3. Assign Base plan to company
                4. Login to adminconsole as tenant admin and derive the plan from base plan by overriding required components
                5. Modify the derived plan entities.
                6. Validate override restrictions
                7. Validates whether inheritance is appropriately followed on derivation

            """, 200)

            #-------------------------------------------------------------------------------------
            laptop_config = get_config().Laptop
            self.plan_inputs = laptop_config._asdict()['DerivedPlans']._asdict()
            self.login_to_adminconsole(self.inputJSONnode['commcell']['commcellUsername'],
                                       self.inputJSONnode['commcell']['commcellPassword'])
            self.create_base_plan()
            self.override_required_for_base_plan()
            self.assigin_plan_to_company()
            self.admin_console.logout()
            self.browser.close()
            self.login_to_adminconsole(self.plan_inputs['Tenant_username'],
                                       self.plan_inputs['Tenant_Password'])
            self.create_derived_plan()
            self.validate_overriding()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            self.navigator.navigate_to_plan()
            self.plans.delete_plan(self.derived_plan)

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
