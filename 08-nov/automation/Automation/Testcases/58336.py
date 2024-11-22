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
    """[Laptop] [Admin Console]: Derived Plan Override restriction from REQUIRED to NOTALLOWED"""
    test_step = TestStep()
    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [Admin Console]: Derived Plan Override restriction from REQUIRED to NOTALLOWED"
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

        self.plan_obj.rpo_hours = '40'
        self.plan_obj.backup_data = {'file_system': ["Windows"],
                                     'content_backup': [],
                                     'content_library': [],
                                     'custom_content': ['C:\\From_Base_content'],
                                     'exclude_folder': [],
                                     'exclude_folder_library': [''],
                                     'exclude_folder_custom_content': ['C:\\From_Base_Filter']}

        self.plan_obj.alerts = {"Backup" : "No backup for last 4 days",
                                "Jobfail": "Restore Job failed",
                                "edge_drive_quota": "Edge drive quota alert",
                                "file_system_quota": "File system quota alert"}
        self.plan_obj.allowed_features = {
            "DLP": "OFF"
        }
        self.plan_obj.user_usergroup_association = []

        self.plan_obj.add_plan()
        self.log.info(""" ***** BasePlan [{0}] created successfully *****""".format(self.base_plan_name))

    @test_step
    def override_required_for_base_plan(self):
        """ Allowing base plan to be overridden, with all parameters as Override required """
        self.plan_obj.edit_plan_dict = {
            "throttle_send": "",
            "throttle_receive": "",
            "file_system_quota": None,
            "rpo_hours": None,
            "additional_storage": None,
            "allowed_features": None,
            "backup_data": "",
            "alerts": None,
            "override_restrictions": {"Storage pool": "Override required",
                                      "RPO": "Override required",
                                      "Backup content": "Override required",
                                      "Retention": "Override required"}}
        self.plan_obj.retention = None
        self.plan_obj.allow_override = {"Storage_pool": "Override required",
                                        "RPO": "Override required",
                                        "Folders_to_backup": "Override required",
                                        "Retention": "Override required"}
        self.plan_obj.edit_laptop_plan()
        self.log.info(""" ***** Override restrictions set successfully at base plan*****""")

    @test_step
    def create_derived_plan(self):
        """ Creation of the Derived plan"""
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
        self.plan_obj.storage = {'pri_storage': self.plan_inputs['Derived_storage']}
        self.plan_obj.add_laptop_derivedplan()
        self.log.info(""" ***** Derived Plan [{0}] created successfully *****""".format(self.derived_plan))

    @test_step
    def validate_overriding(self):
        """ Validation of override restrictions and inheritance with all components required"""

        override_entities = {
            'Backup content': {'Windows': ['Desktop', 'Documents', 'User Settings', 'C:\\From_Derived_content'],
                               'Mac': ['Desktop', 'Documents', 'User Settings'],
                               'Unix': ['Desktop', 'Documents']},
            'Inherit settings': {'Base plan': self.base_plan_name,
                                 'Storage pool': 'Overriding base plan',
                                 'RPO': 'Overriding base plan',
                                 'Folders to backup': 'Overriding base plan',
                                 'Retention': 'Overriding base plan'},
            'RPO': {'Backup frequency': 'Runs every 20 hour(s)'},
            'Retention': {'Deleted item retention': '10 year(s)', 'File versions': '10 versions'},
            'Backup destinations': [self.plan_inputs['Derived_storage']]}

        self.plan_obj.validate_derivedplan_overriding(override_entities)
        self.log.info(""" ***** Validation of override restrictions completed successfully *****""")

    @test_step
    def edit_base_plan(self):
        """ Modify Base plan Override restrictions from Required to Not Allowed"""

        self.plan_obj.edit_plan_dict = {
            "throttle_send": "",
            "throttle_receive": "",
            "file_system_quota": None,
            "rpo_hours": None,
            "additional_storage": None,
            "allowed_features": None,
            "backup_data": "",
            "alerts": "",
            "override_restrictions": {
                "Storage pool": "Override not allowed",
                "RPO": "Override not allowed",
                "Backup content": "Override not allowed",
                "Retention": "Override not allowed"}}
        self.plan_obj.retention = None
        self.plan_obj.allow_override = {"Storage_pool": "Override not allowed",
                                        "RPO": "Override not allowed",
                                        "Folders_to_backup": "Override not allowed",
                                        "Retention": "Override not allowed"}
        self.plan_obj.edit_laptop_plan()
        self.log.info(""" ***** Override restrictions modified successfully at base plan*****""")

    @test_step
    def vaildate_derive_plan(self):
        """ Validate derive plan after Override restrictions changed from Required to Not Allowed"""

        override_entities = {
            'Backup content': {'Windows': ['Desktop', 'Documents', 'User Settings', 'C:\\From_Base_content'],
                               'Mac': ['Desktop', 'Documents', 'User Settings'],
                               'Unix': ['Desktop', 'Documents']},
            'Inherit settings': {'Base plan': self.base_plan_name,
                                 'Storage pool': 'Inheriting from base plan',
                                 'RPO': 'Inheriting from base plan',
                                 'Folders to backup': 'Inheriting from base plan',
                                 'Retention': 'Inheriting from base plan'},
            'RPO': {'Backup frequency': 'Runs every 40 hour(s)'},
            'Retention': {'Deleted item retention': '2 year(s)', 'File versions': '5 versions'},
            'Backup destinations': [self.plan_inputs['Primary_storage']]}

        self.plan_obj.validate_derivedplan_overriding(override_entities)
        self.log.info(""" ***** Validation of override restrictions completed successfully *****""")


    def setup(self):
        """ Login to adminconsole with given user """

        self.log.info(""" Initialize browser objects """)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.log.info(""" Logged into adminconsole with {0} successfully"""\
                      .format(self.inputJSONnode['commcell']['commcellUsername']))
        self.plan_obj = PlanMain(self.admin_console, self.commcell)
        self.plans = Plans(self.admin_console)
        self.company_details = CompanyDetails(self.admin_console)
        self.base_plan_name = "Automation_Base_58336" 
        self.derived_plan = "Automation_derived_58336" 
        self.plan_obj.plan_name = {"laptop_plan": self.base_plan_name}
        self.plan_obj.derived_plan = self.derived_plan
        self.navigator = self.admin_console.navigator
        self.table = Rtable(self.admin_console)
        laptop_config = get_config().Laptop
        self.plan_inputs = laptop_config._asdict()['DerivedPlans']._asdict()


    def run(self):

        try:
            self.server_obj = ServerTestCases(self)
            #-------------------------------------------------------------------------------------
            self.server_obj.log_step("""
                1. Login to Adminconsole as MSP admin
                2. Create Base Plan With required components as "OverrideRequired"
                3. Create derived plan by overriding base plan
                4. Validate override restrictions
                5. Change the base plan entites from "Required " to "not allowed"
                6. Validates whether inheritance is appropriately followed on derivation
            """, 200)

            #-------------------------------------------------------------------------------------
            self.create_base_plan()
            self.override_required_for_base_plan()
            self.create_derived_plan()
            self.validate_overriding()
            self.edit_base_plan()
            self.vaildate_derive_plan()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            self.navigator.navigate_to_plan()
            self.plans.delete_plan(self.derived_plan)
            self.plans.delete_plan(self.base_plan_name)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
