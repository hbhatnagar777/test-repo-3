from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from random import randint, sample, choice
from cvpysdk.commcell import Commcell
from Server.Plans.planshelper import PlansHelper
from Server.Security.userhelper import UserHelper
from cvpysdk.subclient import Subclients


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "Plan Details Edit Validation: Applicable Solutions Validation"
        self.tcinputs = {}

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.password = self.inputJSONnode['commcell']['commcellPassword']
        self.admin_console.login(
            self.inputJSONnode['commcell']['commcellUsername'], self.password)
        self.navigator = self.admin_console.navigator

        self.plans_helper = PlanMain(
            admin_console=self.admin_console, commcell=self.commcell, csdb=self.csdb)
        self.sdk_plans_helper = PlansHelper(commcell_obj=self.commcell)
        self.plans = Plans(self.admin_console)
        self.plan_details = PlanDetails(self.admin_console)
        self.file_server = FileServers(self.admin_console)

        # constants
        self.plan_name = self.plans_helper.plan_name = f"TC 63278 PLAN - {str(randint(0, 100000))}"
        self.derived_plan_name = f"TC 63278 PLAN - {str(randint(0, 100000))}"
        self.applicable_solns = []
        self.supported_solns = list(
            self.commcell.plans.get_supported_solutions().keys())
        self.editable_permissions = [
            ['Plan Solution Association', 'View'], ['Edit Plan']]
        self.non_editable_permissions = [['View'], ['Use Plan']]

        # Get file server details
        self.file_server_name = (
            self.tcinputs.get('file_server')
            or
            choice(list(self.commcell.clients.file_server_clients.values()))[
                'displayName']
        )
        self.log.info(f'FS Client => {self.file_server_name}')
        self.client = self.commcell.clients.get(self.file_server_name)
        self.default_backupset = self.client.agents.get('File System').backupsets.get('defaultBackupSet')
        self.subclients_obj = Subclients(self.default_backupset)
        self.subclients_obj.get('default').plan = None
        self.client.change_company_for_client('Commcell')

        # Get storage details to create plan
        self.storage_name = (
            self.tcinputs.get('storage_pool')
            or
            self.sdk_plans_helper.get_storage_pool()
        )
        self.log.info(f'Storage Pool => {self.storage_name}')

        # create role
        self.role_name = 'TC_63278_ROLE'
        if not self.commcell.roles.has_role(self.role_name):
            self.commcell.roles.add(
                rolename=self.role_name, permission_list=['View'])

        # create user
        self.user_helper = UserHelper(self.commcell)
        self.user_name = f"TC_63278_USER{str(randint(0, 100000))}"
        self.commcell.users.add(
            user_name=self.user_name, email=f'tc63278{str(randint(0, 100000))}@abcd.com', password=self.password)

    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_plan()
            self.plans.create_server_plan(
                self.plan_name, {'pri_storage': self.storage_name})
            self.commcell.plans.refresh()
            self.admin_console.wait_for_completion()
            self.log.info(f'Created Server Plan : {self.plan_name}')

            # validate default behaviour without setting applicable solutions
            self.validate_default_behaviour()

            # validate applicable solutions edit from plan details page
            random_solns = sample(self.supported_solns, 3)
            ui_status, api_status = self.plans_helper.validate_appl_soln_edits(
                self.plan_name, random_solns)
            if not (ui_status and api_status):
                raise CVTestStepFailure(
                    f'Applicable Solutions Edit Failed for {random_solns}. UI: {ui_status}. API: {api_status}')

            # validate applicable solutions for file server solutions
            self.validate_fs_as_appl_soln()

            # validate applicable solutions for other than file server solutions
            self.validate_for_other_solutions()

            # TODO: Add validation for edit on derived plans

            # log out and login as other user
            self.admin_console.logout()
            self.admin_console.login(self.user_name, self.password)
            self.commcell.plans.get(self.plan_name).update_security_associations(
                [{'user_name': self.user_name, 'role_name': self.role_name}])
            self.user_sdk_obj = Commcell(
                self.commcell.webconsole_hostname, self.user_name, self.password, verify_ssl=False)
            self.user_plan_helper = PlanMain(
                self.admin_console, self.user_sdk_obj, csdb=self.csdb)

            # validate edit wrt permissions
            for permission in self.non_editable_permissions:
                self.validate_edit_wrt_permission(
                    permission, self.plan_name, False)

            for permission in self.editable_permissions:
                self.validate_edit_wrt_permission(
                    permission, self.plan_name, True)

            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.default_backupset.plan = None
        self.sdk_plans_helper.cleanup_plans('TC 63278 PLAN')
        self.user_helper.cleanup_users('TC_63278_USER')
        self.user_helper.cleanup_users('del_automated')

    @test_step
    def validate_default_behaviour(self):
        """Method to validate default behaviour of Applicable Solutions"""
        # validate by default plan can be successfully associated to FS client or not
        ui_status, api_status = self.plans_helper.validate_plan_association(
            self.file_server_name, self.plan_name)
        if not (ui_status and api_status):
            raise CVTestStepFailure(
                f'Failed to associate plan to FS client with default behaviour. UI: {ui_status}. API: {api_status}')

        # validate from plan details page
        self.plans.select_plan(self.plan_name)
        self.applicable_solns = self.plan_details.get_applicable_solns()
        if self.applicable_solns:
            raise CVTestStepFailure(
                f'By default plans applicable solution is not set to ALL. Applicable Soln : {self.applicable_solns}')

        self.log.info('Successfully validated default behaviour.')

    @test_step
    def validate_fs_as_appl_soln(self):
        """Method to validate File Server applicable solutions"""
        # set applicable solutions as File Servers
        self.plans.select_plan(self.plan_name)
        self.plan_details.edit_applicable_solns(solutions=['File Servers'])

        # validate if plan can be successfully associated to file server or not
        ui_status, api_status = self.plans_helper.validate_plan_association(
            self.file_server_name, self.plan_name)
        if not (ui_status and api_status):
            raise CVTestStepFailure(
                f'Failed to associate plan to FS client with Applicable Solutions set as File Server. UI: {ui_status}. API: {api_status}')
        self.admin_console.refresh_page()

        self.log.info('Trying to create subclient using eligible plan...')
        subclient_name = f'subclient_{str(randint(0, 1000))}'
        self.subclients_obj.add(subclient_name, self.plan_name)
        self.subclients_obj.delete(subclient_name)

        self.log.info(
            'Successfully validated applicable solutions for FS solution.')

    @test_step
    def validate_for_other_solutions(self):
        """Method to validate applicable solns for other solutions"""
        # restrict plan to random 3 solutions other than "File Servers"
        random_solns = sample(
            [soln for soln in self.supported_solns if soln != 'File Servers'], 3)
        self.plans.select_plan(self.plan_name)
        self.plan_details.edit_applicable_solns(solutions=random_solns)

        # validate that plan cannot be associated to file server via UI or API
        ui_status, api_status = self.plans_helper.validate_plan_association(
            self.file_server_name, self.plan_name)
        if ui_status or api_status:
            raise CVTestStepFailure(
                f'Non Applicable Plan can be associated to File Server Client. UI: {ui_status}. API: {api_status}')
        self.admin_console.refresh_page()

        self.log.info('Trying to create subclient using ineligible plan...')
        try:
            self.subclients_obj.add(
                f'subclient_{str(randint(0, 1000))}', self.plan_name)
        except Exception as err:
            self.log.info(f'Negative case: {err}')
        else:
            raise CVTestStepFailure(
                'Non Applicable Plan can be used to create FS subclient')

        self.log.info(
            'Successfully validated applicable solutions for Non FS solutions.')

    @test_step
    def validate_edit_wrt_permission(self, permissions, plan_name, editable: bool = bool()):
        """Method to validate appl solns edit wrt user permsisions"""
        self.log.info(
            f"Validating applicable solution edit wrt permission  : {permissions}")
        self.commcell.roles.get(self.role_name).modify_capability(
            'OVERWRITE', permissions)

        # perform edit via UI and API
        ui_status, api_status = self.user_plan_helper.validate_appl_soln_edits(
            plan_name, sample(self.supported_solns, 3))

        # if editing is not allowed but user can edit either from UI or API
        if not editable and (ui_status or api_status):
            raise CVTestStepFailure(
                f'Applicable Solutions is editable for user with {permissions} permission. UI: {ui_status} & API: {api_status}')

        # if editing is allowed but user can not edit either from UI or API
        if editable and not (ui_status and api_status):
            raise CVTestStepFailure(
                f'Applicable Solutions is not editable for user with {permissions} permission. UI: {ui_status} & API: {api_status}')
