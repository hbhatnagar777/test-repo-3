from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Laptop.laptophelper import LaptopHelper
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Laptop] [Elastic Plan]: Validation of User migration from One Elastic Plan to another Elastic" \
                    " Plan"
        self.browser = None
        self.admin_console = None
        self.table = None
        self.company_details = None
        self.navigator = None
        self.plan_obj1 = None
        self.plan_obj2 = None
        self.plan_obj = None
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.tcinputs = {
            "User": None,
            "Activation_User": None,
            "Activation_Password": None,
            "tenant_username": None,
            "tenant_password": None,
            "Plan1": None,
            "Plan2": None,
            "Role_name": None
        }
        self.lap_obj = None
        self._utility = None

    def setup(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company3'))
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'],
                                     stay_logged_in=True)
            self._commcell.is_linux_commserv = False
            self.lap_obj = LaptopHelper(self, company=self.tcinputs['Tenant_company'])
            self.lap_obj.tc.log_step("""
                            ***** PREREQUISITE: Create a company, and assign a user with appropriate permissions as one 
                            of its operators *****
                            1. As MSP admin, Create 2 Plans 'Elastic Plan -01' and 'Elastic Plan -02' , make sure both 
                                has different content, schedule RPO, throttling and associate to same company

                            2.  Now As a Tenant admin, Try to add the new domain user to 'Elastic Plan -01' and verify 
                                user should added successfully.

                            3. Activate the laptop to 'Elastic Plan -01' with new user and verify below

                                After laptop activated verify below to makesure it activated to correct region
                                1. Region set correctly from laptop summary section
                                2. Verify correct Storage Policy is associated to subclient
                                3. Backup completed successfully 
                                4. Restore should work without any issue

                            4. As a Tenant Admin, Migrate/ Directly associate the new domain user added from  
                                'Elastic Plan -01' to "Elastic Plan -02'

                            5. Laptop Should be migrated from 'Elastic Plan -01' to 'Elastic Plan-02' Without any issues

                            6. Verify below after laptop migrated successfully:
                                1. Laptop migrated successfully to new plan without deactivation
                                2. New Content, Schedules, Storage is associated correctly
                                3. Modify content and run backup and verify backups are working fine
                                4. Restore the data and verify completed successfully
                        """, 200)
            self.navigator = self.admin_console.navigator
            self.plan_obj = PlanMain(self.admin_console)
            self._utility = OptionsSelector(self._commcell)
            self.table = Table(self.admin_console)
            self.company_details = CompanyDetails(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': True,
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
        }

    def create_plan(self, plan_obj, secondary_storage):
        """ Creation of the plan """
        self.log.info(f"Creating Laptop Plan: {plan_obj['Name']}")
        self.navigator.navigate_to_plan()

        self.plan_obj.plan_name = {"laptop_plan": plan_obj.get("Name")}
        self.plan_obj.storage = {'pri_storage': plan_obj.get("Primary_storage")}

        self.plan_obj.retention = {}

        self.plan_obj.rpo_hours = str(plan_obj.get("RPO"))
        self.plan_obj.backup_data = {'file_system': [],
                                     'content_backup': [],
                                     'content_library': [],
                                     'custom_content': None,
                                     'exclude_folder': None,
                                     'exclude_folder_library': None,
                                     'exclude_folder_custom_content': None}
        # self.plan_obj.backup_data = None
        self.plan_obj.file_system_quota = None
        self.plan_obj.throttle_send = str(plan_obj.get("throttle_send"))

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
        self.log.info(
            """***** Laptop Plan [{0}] created successfully *****""".format(self.plan_obj.plan_name['laptop_plan']))
        self.log.info(f"Converting {plan_obj['Name']} into an Elastic Plan")
        self.navigator.navigate_to_plan()
        Plans(self.admin_console).select_plan(plan_obj.get("Name"))
        PlanDetails(self.admin_console).convert_elastic_plan(plan_obj, secondary_storage)
        self.log.info(f"{plan_obj['Name']} is now an elastic plan")

    def assign_user_to_company(self, plan_obj):
        self.navigator.navigate_to_companies()
        self.table.access_link(self.tcinputs['Tenant_company'])
        CompanyDetails.edit_company_operators(operators={"add": {self.tcinputs["Activation_User"]:
                                                    self.tcinputs["Role_name"]}})

    def assign_plans_to_company(self):
        """ Associating the plan with Company"""
        self.navigator.navigate_to_companies()
        self.table.access_link(self.tcinputs['Tenant_company'])
        self.company_details.edit_company_plans([self.plan_obj1.get("Name"), self.plan_obj2.get("Name")],
                                                laptop_default_plan=self.plan_obj1.get("Name"))

        self.log.info(""" ***** Associated plans to company {0} successfully *****"""
                      .format(self.tcinputs['Tenant_company']))

    def verify_association_plan(self):
        """ Checks for proper association with the plan, by checking the storage rules and running backup and restore"""
        self.lap_obj.validate_postactivation_laptop_region_association(self.admin_console, self.tcinputs)
        self.lap_obj.validate_backup_and_restore(self.admin_console, self.tcinputs)

    def associate_user_plan(self, plan_obj):
        """ Associates User group to the given plan"""
        self.navigator.navigate_to_plan()
        Plans(self.admin_console).select_plan(plan_obj["Name"])
        PlanDetails(self.admin_console).edit_plan_associate_users_and_groups([self.tcinputs["User"]])

    def dissociate_user_plan(self, plan_obj):
        """ Dissociates User group from the given plan"""
        self.navigator.navigate_to_plan()
        Plans(self.admin_console).select_plan(plan_obj["Name"])
        PlanDetails(self.admin_console).remove_associated_users_and_groups(user_user_group_de_association=
                                                                           {"DeleteAll": False,
                                                                            "DeleteAllUsers": True,
                                                                            "DeleteAllUserGroups": False,
                                                                            "Delete_Specific_user_user_or_group": False}
                                                                           )

    def run(self):
        try:
            self.refresh()
            self.plan_obj1 = self.tcinputs["Plan1"]
            self.plan_obj2 = self.tcinputs["Plan2"]
            self.create_plan(self.plan_obj1, self.tcinputs['Secondary_storage1'])
            self.create_plan(self.plan_obj2, self.tcinputs['Secondary_storage2'])
            self.assign_plans_to_company()
            AdminConsole.logout_silently(self.admin_console)
            self.admin_console.login(self.tcinputs['tenant_username'], self.tcinputs['tenant_password'],
                                     stay_logged_in=True)
            self.log.info(f"Associating User {self.tcinputs['User']} to Plan {self.plan_obj1['Name']}")
            self.associate_user_plan(self.plan_obj1)
            self.lap_obj.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            self.verify_association_plan()
            self.log.info(f"Dissociating User {self.tcinputs['User']} from Plan {self.plan_obj1['Name']}")
            self.dissociate_user_plan(self.plan_obj1)
            self.log.info(f"Associating User {self.tcinputs['User']} to Plan {self.plan_obj2['Name']}")
            self.associate_user_plan(self.plan_obj2)
            self.verify_association_plan()
            self.log.info(f"Dissociating User {self.tcinputs['User']} from Plan {self.plan_obj2['Name']}")
            self.dissociate_user_plan(self.plan_obj2)
            AdminConsole.logout_silently(self.admin_console)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'],
                                     stay_logged_in=True)
            self.navigator.navigate_to_plan()
            Plans(self.admin_console).action_delete_plan(self.plan_obj1["Name"])
            Plans(self.admin_console).action_delete_plan(self.plan_obj2["Name"])
        except Exception as excp:
            handle_testcase_exception(self, excp)

    def tear_down(self):
        self._commcell.refresh()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
