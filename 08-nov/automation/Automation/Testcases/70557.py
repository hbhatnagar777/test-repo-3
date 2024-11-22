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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Plans import PlanRules
from Server.Plans.planshelper import PlansHelper
from Server.servergrouphelper import ServerGroupHelper
from cvpysdk.subclient import Subclients
from time import sleep
from random import randint

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
        self.name = "Plan rules - Automatic Execution validation"
        self.tcinputs = {
            "file_server_1": "",
            "file_server_2": ""
        }
        self.plan_rule_interval_key = 'Auto Plan Rules Execution Interval'
        self.sdk_server_group_helper = None
        self.sdk_plans_helper = None
        self.browser = None
        self.admin_console = None
        self.subclient_1 = None
        self.subclient_2 = None

    def setup(self):
        """Setup function of this test case"""

        self.make_sure_clients_does_not_have_plan()

        self.make_sure_clients_are_at_commcell()

        self.create_required_client_groups()

        self.create_required_plans()
        
        self.set_auto_plan_rule_execution_key() # setting to run plan rule thread every 30 minutes

        # open browser and login to CC
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.plan_rules = PlanRules(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:
            self.clean_up_existing_plan_rules()

            self.plan_rules.set_execution_mode('automatic')

            self.create_plan_rule(self.client_group_1, self.plan_name_1)

            self.create_plan_rule(self.client_group_2, self.plan_name_2)

            self.validate_plan_to_be_associated(self.tcinputs["file_server_1"], 'default', self.plan_name_1)
            self.validate_plan_to_be_associated(self.tcinputs["file_server_2"], 'default', self.plan_name_2)

            self.restart_evmgrs() # Restarting EvMgrS service to run plan rule thread

            # Check every 5 minutes if plan rules are executed until 35 minutes
            total_wait_time = 0
            for _ in range(7):
                if self.is_automatic_execution_completed():
                    break
                self.log.info('Plan rule execution is not completed, waiting for 5 minutes...')
                sleep(300)
                total_wait_time += 300
                self.log.info(f'Current Wait time: {total_wait_time//60} minutes')
            self.log.info(f'Total wait time: {total_wait_time//60} minutes')

            self.validate_automatic_plan_association()

            self.log.info('Test case executed successfully')

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

        # remove plan assoc and delete plans
        self.subclient_1.plan = None
        self.subclient_2.plan = None

        self.sdk_plans_helper.cleanup_plans(marker='TC 70557')
        self.sdk_server_group_helper.cleanup_server_groups(marker='TC 70557 CG')

    @test_step
    def make_sure_clients_are_at_commcell(self):
        """Make sure clients are at commcell"""
        for client in [self.tcinputs["file_server_1"], self.tcinputs["file_server_2"]]:
            try:
                self.commcell.clients.get(client).change_company_for_client(destination_company_name='Commcell')
            except Exception as exp:
                self.log.error('Failed to change company for client [%s] with error: %s', client, exp)
                self.log.info('Ignoring this error and continuing...')

    @test_step
    def make_sure_clients_does_not_have_plan(self):
        """Make sure clients does not have any plan"""
        self.file_server_1 = self.commcell.clients.get(self.tcinputs['file_server_1'])
        self.file_server_2 = self.commcell.clients.get(self.tcinputs['file_server_2'])

        self.subclient_1 = Subclients(self.file_server_1.agents.get('File System').backupsets.get('defaultBackupSet')).get('default')
        self.subclient_2 = Subclients(self.file_server_2.agents.get('File System').backupsets.get('defaultBackupSet')).get('default')

        self.subclient_1.plan = None
        self.subclient_2.plan = None

    @test_step
    def create_required_client_groups(self):
        """Create required client groups"""
        self.sdk_server_group_helper = ServerGroupHelper(self.commcell)

        self.client_group_1 = f"TC 70557 CG {randint(0,1000)}"
        self.client_group_2 = f"TC 70557 CG {randint(0,1000)}"

        self.log.info(f'Creating client groups... {self.client_group_1}, {self.client_group_2}')
        self.commcell.client_groups.add(clientgroup_name=self.client_group_1, 
                                        clients=[self.tcinputs["file_server_1"]])
        
        self.commcell.client_groups.add(clientgroup_name=self.client_group_2,
                                        clients=[self.tcinputs["file_server_2"]])
        
        self.log.info('Created required client groups')

    @test_step
    def create_required_plans(self):
        """Create required plans"""
        self.plan_name_1 = f'TC 70557 Plan 1 - {str(randint(0, 100000))}'
        self.plan_name_2 = f'TC 70557 Plan 2 - {str(randint(0, 100000))}'

        self.sdk_plans_helper = PlansHelper(commcell_obj=self.commcell)
        self.storage_name = self.sdk_plans_helper.get_storage_pool()

        self.log.info(f'Creating required plans... {self.plan_name_1}, {self.plan_name_2} with storage pool {self.storage_name}')
        self.commcell.plans.create_server_plan(
            plan_name=self.plan_name_1, backup_destinations=[{'storage_name': self.storage_name}]
        )
        self.commcell.plans.create_server_plan(
            plan_name=self.plan_name_2, backup_destinations=[{'storage_name': self.storage_name}]
        )
        self.log.info('Created required plans')

    @test_step
    def clean_up_existing_plan_rules(self):
        """Delete all existing plan rules"""
        self.plan_rules.go_to_plan_rules_page()
        for plan_rule in reversed(self.plan_rules.available_plan_rules()):
            self.plan_rules.delete(plan_rule)

    @test_step
    def set_auto_plan_rule_execution_key(self):
        """Set auto plan rule execution key to 30 minutes"""
        existing_additional_settings = [key['displayLabel'] for key in self.commcell.get_configured_additional_setting()]
        
        if self.plan_rule_interval_key not in existing_additional_settings:
            self.log.info(f"Setting additional settings key [{self.plan_rule_interval_key}] to run plan rule thread every 30 minutes")
            self.commcell.add_additional_setting(category='CommServDB.GxGlobalParam', key_name=self.plan_rule_interval_key,
                                                 data_type='INTEGER', value=30)

    @test_step
    def create_plan_rule(self, client_group, plan_name):
        """Create plan rule with given client group and plan name"""
        rule_props = {
            'serverGroups'  :   [client_group],
            'serverPlan'    :   plan_name
        }
        self.log.info(f'Creating plan rule with properties: {rule_props}')
        self.plan_rules.go_to_plan_rules_page()
        self.plan_rules.add(rule_props)

    @test_step
    def validate_plan_to_be_associated(self, server_name, subclient_name, expected_plan_name):
        """Validate plan to be associated with given server and subclient"""
        self.log.info('Validate if correct matching plans are shown in waiting room...')
        waiting_room_plan = self.plan_rules.get_plan_to_be_assigned(server_name, subclient_name)

        if waiting_room_plan.lower() != expected_plan_name.lower():
            raise Exception(f'Waiting room plan is not as expected. Expected: {expected_plan_name}, Waiting room plan: {waiting_room_plan}')

        self.log.info('Waiting room plan is shown as expected')

    @test_step
    def restart_evmgrs(self):
        """Restart EvMgrS service"""
        if self.commcell.is_linux_commserv:
            self.commcell.commserv_client.restart_service('EvMgrS')
        else:
            self.commcell.commserv_client.restart_service('GxEvMgrS(Instance001)')
        self.log.info('EvMgrS service restarted')

    @test_step
    def is_automatic_execution_completed(self):
        """Check if automatic execution is completed"""
        self.plan_rules.go_to_plan_rules_page()
        subclient1_status = self.plan_rules.is_subclient_present_in_waiting_room(server_name=self.tcinputs["file_server_1"], subclient_name='default')
        subclient2_status = self.plan_rules.is_subclient_present_in_waiting_room(server_name=self.tcinputs["file_server_2"], subclient_name='default')

        self.log.info(f'[Waiting Room]: Subclient1 waiting status: {subclient1_status}, Subclient2 waiting status: {subclient2_status}')
        if subclient1_status or subclient2_status:
            return False # one of the subclient is still in waiting room
        return True
    
    @test_step
    def validate_automatic_plan_association(self):
        """Validate plan association after automatic execution is completed"""
        self.log.info('Validating plan association...')
        self.subclient_1.refresh()
        self.subclient_2.refresh()

        self.log.info(f'Subclient1 plan: {self.subclient_1.plan}, Subclient2 plan: {self.subclient_2.plan}')
        self.log.info(f'Expected plan for subclient 1: {self.plan_name_1}, Expected plan for subclient 2: {self.plan_name_2}')

        if self.subclient_1.plan.lower() != self.plan_name_1.lower() or self.subclient_2.plan.lower() != self.plan_name_2.lower():
            raise Exception('Plan association is not as expected')
        self.log.info('Plan association is as expected')

