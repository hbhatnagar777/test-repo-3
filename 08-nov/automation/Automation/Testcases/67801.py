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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""
import datetime
import time

from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVWebAutomationException
from collections import defaultdict


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_Exchange_Include_Exclude_Backup_Verification:
    Metallic Exchange Online backup verification of excluded/included users/AD groups
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_Exchange_Include_Exclude_Backup_Verification for Service Catalogue"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.app_type = None
        self.users = None
        self.app_name = None
        self.service_catalogue = None
        self.server_plan=None
        self.mailbox_count={}
        self.audit_trail=defaultdict(list)
        self.utils = TestCaseUtils(self)

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['tenantUserName'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.exchange
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.navigator = self.admin_console.navigator
        self.users = self.tcinputs['Users'].split(",")
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_plan()
            plans = self.office365_obj.get_plans_list()
            server_plan = None
            for plan in plans:
                if "o365-storage" in plan.lower():
                    server_plan = plan
                    break

            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'],
                                                    plan=server_plan)
            self.app_name = self.office365_obj.get_app_name()
            self.admin_console.access_tab(self.office365_obj.constants.CONFIGURATION.value)

            self.office365_obj.disable_backup()
            self.audit_trail["Update Activity Control"].append("For activity type [BACKUP], enable activity: No")

            self.admin_console.access_tab(self.office365_obj.constants.CONTENT_TAB.value)
            self.office365_obj.add_user(self.users)
            for user in self.users:
                self.audit_trail["Add Content"].append(f'SMTP Address Set to [{user}]')
            self.office365_obj.add_ad_group(self.tcinputs['Groups'])
            for groups in self.tcinputs['Groups']:
                self.audit_trail["Add Content"].append(f'ADGroup name Set to [{groups}]')

            self.admin_console.access_tab(self.office365_obj.constants.ACCOUNT_TAB.value)
            self.mailbox_count["Mailboxes"]=int(self.office365_obj.get_app_stat(stat_type="Mailboxes"))
            if self.office365_obj.get_discovery_status_count(status="Manual")!=len(self.users):
                self.log.info("Mailbox count mismatched for Manual discovery type")
            self.log.info("Mailbox count are verified for Manual discovery type")
            self.admin_console.refresh_page()
            if self.office365_obj.get_discovery_status_count(status="Auto")!=(self.mailbox_count["Mailboxes"]-len(self.users)):
                self.log.info("Mailbox count mismatched for Auto discovery type")
            self.log.info("Mailbox count are verified for Auto discovery type")

            self.admin_console.access_tab(self.office365_obj.constants.CONTENT_TAB.value)
            self.office365_obj.exclude_from_backup(entity=self.tcinputs['ExcludeUser'])
            self.audit_trail["Update Content"].append(f"Content[{self.tcinputs['ExcludeUser']}]")
            self.office365_obj.exclude_from_backup(entity=self.tcinputs['ExcludeGroup'], is_group=True)
            self.audit_trail["Update Content"].append(f"Content[{self.tcinputs['ExcludeGroup']}]")

            self.office365_obj.remove_from_content(entity=self.tcinputs['RemoveUser'])
            self.audit_trail["Delete Content"].append(f"Content[{self.tcinputs['RemoveUser']}]")
            self.office365_obj.remove_from_content(entity=self.tcinputs['RemoveGroup'], is_group=True)
            self.audit_trail["Delete Content"].append(f"Content[{self.tcinputs['RemoveGroup']}]")

            self.admin_console.access_tab(self.office365_obj.constants.CONFIGURATION.value)
            self.office365_obj.enable_backup()
            self.audit_trail["Update Activity Control"].append("For activity type [BACKUP], enable activity: Yes")

            self.office365_obj.run_client_backup()
            self.audit_trail["Immediate Job Submitted"].append(f"Client : [{self.app_name}] Agent Type : [Exchange Mailbox] Instance : [DefaultInstanceName] (Added)")

            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.admin_console.access_tab(self.office365_obj.constants.ACCOUNT_TAB.value)

            self.include_exclude_verification_helper(self.tcinputs['RemoveUser'], 'user', 'removed', False)
            self.include_exclude_verification_helper(self.tcinputs['ExcludeUser'], 'user', 'excluded', False)

            for user in self.tcinputs['GroupsUsers'][self.tcinputs['RemoveGroup']]:
                self.include_exclude_verification_helper(user, 'group', 'removed', False)
            #
            for user in self.tcinputs['GroupsUsers'][self.tcinputs['ExcludeGroup']]:
                self.include_exclude_verification_helper(user, 'group', 'excluded', False)

            self.admin_console.access_tab(self.office365_obj.constants.CONTENT_TAB.value)

            self.office365_obj.include_in_backup(entity=self.tcinputs['ExcludeUser'])
            self.audit_trail["Add Content"].append(f'Content[{self.tcinputs['ExcludeUser']}]')
            self.office365_obj.include_in_backup(entity=self.tcinputs['ExcludeGroup'], is_group=True)
            self.audit_trail["Add Content"].append(f'Content[{self.tcinputs['ExcludeGroup']}]')

            self.office365_obj.add_user(users=[self.tcinputs['RemoveUser']])
            self.audit_trail["Add Content"].append(f'Content[{self.tcinputs['RemoveUser']}]')
            self.office365_obj.add_ad_group([self.tcinputs['RemoveGroup']])
            self.audit_trail["Add Content"].append(f'Content[{self.tcinputs['RemoveGroup']}]')

            self.office365_obj.run_client_backup()
            self.audit_trail["Immediate Job Submitted"].append(
                f"Client : [{self.app_name}] Agent Type : [Exchange Mailbox] Instance : [DefaultInstanceName] (Added)")

            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.admin_console.access_tab(self.office365_obj.constants.ACCOUNT_TAB.value)

            self.include_exclude_verification_helper(self.tcinputs['RemoveUser'], 'user', 'added', True)
            self.include_exclude_verification_helper(self.tcinputs['ExcludeUser'], 'user', 'included', True)

            for user in self.tcinputs['GroupsUsers'][self.tcinputs['RemoveGroup']]:
                self.include_exclude_verification_helper(user, 'group', 'added', True)

            for user in self.tcinputs['GroupsUsers'][self.tcinputs['ExcludeGroup']]:
                self.include_exclude_verification_helper(user, 'group', 'included', True)

            self.audit_trail = dict(self.audit_trail)
            self.log.info(self.audit_trail)
            data=self.office365_obj.get_audit_trail_data(app_name=self.app_name,user_name=self.inputJSONnode['commcell']['tenantUserName'])
            self.log.info(data)
            for operation in self.audit_trail:
                index = [i for i, value in enumerate(data["Operation"]) if value == operation]
                count = 0
                for idx in index:
                    for detail in self.audit_trail[operation]:
                        if detail in data["Details"][idx]:
                            count += 1
                if count < len(self.audit_trail[operation]):
                    raise CVWebAutomationException(f"Audit Report is not matching for operation {operation}")
            self.log.info("Audit Trail Report table is verified")

            self.admin_console.refresh_page()
            self.admin_console.access_tab(self.office365_obj.constants.ACCOUNT_TAB.value)
            self.mailbox_count["Mailboxes"]=int(self.office365_obj.get_app_stat(stat_type="Mailboxes"))
            if self.office365_obj.get_discovery_status_count(status="Manual")!=len(self.users):
                self.log.info("Mailbox count mismatched for Manual discovery type")
            self.log.info("Mailbox count are verified for Manual discovery type")
            self.admin_console.refresh_page()
            if self.office365_obj.get_discovery_status_count(status="Auto")!=(self.mailbox_count["Mailboxes"]-len(self.users)):
                self.log.info("Mailbox count mismatched for Auto discovery type")
            self.log.info("Mailbox count are verified for Auto discovery type")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def include_exclude_verification_helper(self, user, entity, remove_type, processed_backup):
        verification_result = self.office365_obj.verify_mailbox_backup(user=user, processed_backup=processed_backup)
        if not verification_result:
            raise CVWebAutomationException(
                f'Failed: Backup was {'not' if processed_backup else ''} run for {'user : ' + user + ' of' if entity == 'group' else ''} {remove_type} {entity} {':' + user if entity == 'user' else ''}!')
        else:
            self.log.info(
                f'Expected: Backup was {'not' if not processed_backup else ''} run for {'user: ' + user + ' of' if entity == 'group' else ''} {remove_type} {entity} {':' + user if entity == 'user' else ''}!')

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

