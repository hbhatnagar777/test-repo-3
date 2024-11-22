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
import datetime

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.SchedulePolicyPage.BackupSchedules import BackupSchedules
from Web.AdminConsole.SchedulePolicyPage.BackupSchedule import BackupSchedule


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

                    Properties to be initialized:

                        name            (str)       --  name of this test case

                """
        super(TestCase, self).__init__()
        self.backupSchedule = None
        self.backupSchedules = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.name = "[Backup SchedulePolicy Automation]: CRUD operations and Validations."
        self.tcinputs = {
            "agentType": ["Files"]
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(
            self.inputJSONnode['commcell']["commcellUsername"],
            self.inputJSONnode['commcell']["commcellPassword"],
            stay_logged_in=True,
            enable_sso=False,
            max_tries=1
        )
        self.navigator = self.admin_console.navigator
        self.backupSchedules = BackupSchedules(self.admin_console)
        self.backupSchedule = BackupSchedule(self.admin_console)

    @test_step
    def create_and_validate_policy(self) -> str:
        """
        This is a teststep method which will validate creation logic of backup schedules.
        """
        policyName = f"AutomationPolicy{datetime.datetime.now()}"
        schedules = [
            {
                "name": "SchedulePolicyAutomationDaily",
                "backup_level": "Full",
                "frequency": "Daily"
            },
            {
                "name": "SchedulePolicyAutomationWeekly",
                "backup_level": "SynthFull",
                "frequency": "Weekly",
                "Days": ["Monday", "Sunday"]
            },
            {
                "name": "SchedulePolicyAutomationDailyContinuous",
                "backup_level": "Incremental",
                "frequency": "Continuous"
            }
        ]
        self.backupSchedules.create_backup_schedules(
            policyName=policyName,
            schedules=schedules,
            agentType=self.tcinputs["agentType"],
            associations=["Servers", "Server groups"]

        )
        self.navigator.navigate_to_backup_schedules()
        schedulePolicies = self.backupSchedules.list_backup_schedules()
        if policyName not in schedulePolicies:
            raise "Schedule policy Creation Wizard is broken."
        return policyName

    @test_step
    def modify_and_validate_policy(self, policyName) -> str:
        """
        This method will check modification logic of backupschedules.
        """
        self.backupSchedule.disable_policy()
        newPolicyName = policyName + "Edited"
        self.backupSchedule.edit_policy_name(newPolicyName)
        self.navigator.navigate_to_backup_schedules()
        schedulePolicies = self.backupSchedules.list_backup_schedules()
        self.backupSchedules.select_backup_schedule(newPolicyName)
        status = self.backupSchedule.get_general_information()
        if newPolicyName not in schedulePolicies or status["Enabled"] is True:
            raise "Schedule policy Update is not working"
        self.backupSchedule.navigate_to_schedules()
        self.backupSchedule.add_schedule({
            "name": "NewScheduleAddCheck",
            "backup_level": "Full",
            "frequency": "Daily"
        })
        self.backupSchedule.delete_schedule("NewScheduleAddCheck")
        self.backupSchedule.navigate_to_associations()
        return newPolicyName

    def run(self):
        """ run function of this test case """
        try:
            self.navigator.navigate_to_backup_schedules()
            policyName = self.create_and_validate_policy()
            self.log.info("Schedule Policy Creation is successful")
            self.backupSchedules.select_backup_schedule(policyName)
            newName = self.modify_and_validate_policy(policyName)
            self.log.info("Schedule Policy Modification is successful")
            self.navigator.navigate_to_backup_schedules()
            self.backupSchedules.delete_backup_schedule(newName)
            self.log.info("Schedule Policy Deletion is successful")
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """ Tear down function of this test case """
        try:
            pass
        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close()
