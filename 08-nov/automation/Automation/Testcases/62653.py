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
import random
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Creation of Office365 client with modern authentication enabled"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.users = None
        self.exmb_client = None
        self.testdata = None
        self.mailboxes = None
        self.group_name = None
        self.manually_associate_mailboxes = None
        self.manual_mailbox_plan = None
        self.autodiscovered_mailboxes = None
        self.autodiscovered_mailbox_plan = None
        self.utils = TestCaseUtils(self)

    def create_mailboxes_and_group(self):
        """Create mailbox and AD group"""
        self.exmb_client = ExchangeMailbox(self)
        self.testdata = TestData(self.exmb_client)
        self.mailboxes = self.testdata.create_online_mailbox(use_json=False)
        self.manually_associate_mailboxes = random.sample(self.mailboxes, 2)
        self.autodiscovered_mailboxes = list(set(self.mailboxes) - set(self.manually_associate_mailboxes))
        self.mailboxes = [alias+"@"+self.tcinputs["DomainName"] for alias in self.mailboxes]
        self.log.info("Sending Mails to the mailboxes")
        self.exmb_client.exchange_lib.send_email(self.mailboxes)
        self.log.info("Creating O365 group and adding members")
        self.group_name = self.testdata.create_o365_group(use_json=False, group_members=self.mailboxes)
        self.log.info("Done creating mailboxes and adding members in the group")

    def run_backups(self, count=2):
        """Run multiple backup jobs and return the job ids"""
        job_ids = list()
        while count > 0:
            if self.admin_console.check_if_entity_exists('id', 'ARCHIVE_GRID'):
                job_details = self.office365_obj.run_backup()
                job_ids.append(job_details['Job Id'])
            else:
                self.navigator.navigate_to_office365()
                self.office365_obj.access_office365_app(self.tcinputs['Name'])
                job_details = self.office365_obj.run_backup()
                job_ids.append(job_details['Job Id'])
            count -= 1
        return job_ids

    def verify_recovery_point_operations(self, mailbox_names):
        """Creates recovery point by sending the job ids"""
        recovery_point_ids = self.office365_obj.create_recovery_point(mailbox_names, self.tcinputs["Name"])
        self.office365_obj.restore_recovery_point(recovery_point_ids, self.tcinputs["Name"])

    def restore_from_all_checkpoints(self,mailboxes):
        """Initiates restore jobs from all checkpoints"""
        self.office365_obj.run_restore()
        for user in mailboxes:
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.tcinputs["Name"])
            self.office365_obj.run_restore(user_mailbox=user)

    def perform_operations(self, association_name=None):
        """Perform operations on the associations"""
        self.admin_console.access_tab(self.office365_obj.app_type.ACCOUNT_TAB.value)
        # Check the plan associated and discovery type
        self.office365_obj.verify_discovery_status(self.manually_associate_mailboxes, "Manual")
        self.office365_obj.verify_plan_association(users=[mailbox+"@"+self.tcinputs["DomainName"] for mailbox in self.manually_associate_mailboxes],
                                                   plan=self.manual_mailbox_plan)
        if association_name == "AD group":
            # Change the plan of one of the autodiscovered mailbox with the content checkbox unchecked and check its type
            self.office365_obj.change_office365_plan(user=self.autodiscovered_mailboxes[0],
                                                     plan=self.manual_mailbox_plan)
            self.office365_obj.verify_discovery_status(self.autodiscovered_mailboxes[0:1], "Manual")
            self.office365_obj.verify_plan_association(users=[self.autodiscovered_mailboxes[0]+"@"+self.tcinputs["DomainName"]],
                                                       plan=self.manual_mailbox_plan)
            # Change the plan of one of the autodiscovered mailbox with the content checkbox checked this time and check its type
            self.office365_obj.change_office365_plan(user=self.autodiscovered_mailboxes[0],
                                                     plan=self.autodiscovered_mailbox_plan,
                                                     inherit_from_content=True)
            self.exmb_client.cvoperations.run_admailbox_monitor()
            self.admin_console.refresh_page()
            self.office365_obj.verify_discovery_status(self.autodiscovered_mailboxes[0:1], "Auto")
            self.office365_obj.verify_plan_association(users=[self.autodiscovered_mailboxes[0]+"@"+self.tcinputs["DomainName"]],
                                                       plan=self.autodiscovered_mailbox_plan)

    def setup(self):
        self.create_mailboxes_and_group()
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Apps.AppType.exchange_online
        self.office365_obj = Office365Apps(tcinputs=self.tcinputs,
                                           admin_console=self.admin_console
                                           )
        self.manual_mailbox_plan = self.tcinputs["ManualOffice365Plan"]
        self.autodiscovered_mailbox_plan = self.tcinputs["AutoDiscoverOffice365Plan"]

    def run(self):
        """Main function for test case execution"""

        try:
            self.admin_console.close_popup()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app()
            self.office365_obj.add_user(users=self.manually_associate_mailboxes, plan=self.manual_mailbox_plan)
            self.run_backups()
            # Performing recovery point operations
            self.verify_recovery_point_operations(self.manually_associate_mailboxes)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.tcinputs['Name'])
            # Restore from all buttons
            self.restore_from_all_checkpoints(self.manually_associate_mailboxes)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.tcinputs['Name'])
            # Selecting the all mailboxes and verify config values after performing operations
            self.office365_obj.select_content(content_type='All mailboxes')
            self.perform_operations()
            self.admin_console.access_tab(self.office365_obj.app_type.CONTENT_TAB.value)
            self.office365_obj.deselect_content(content_type="All mailboxes")
            self.admin_console.access_tab(self.office365_obj.app_type.ACCOUNT_TAB.value)
            self.office365_obj.verify_added_users(self.manually_associate_mailboxes)
            # Selecting the AD group and verify config values after performing operations
            self.office365_obj.add_AD_Group(groups=self.group_name, plan=self.autodiscovered_mailbox_plan)
            self.perform_operations(association_name="AD group")
            self.admin_console.access_tab(self.office365_obj.app_type.CONTENT_TAB.value)
            self.office365_obj.deselect_content(content_type=self.group_name)
            self.admin_console.access_tab(self.office365_obj.app_type.ACCOUNT_TAB.value)
            self.office365_obj.verify_added_users([mailbox+"@"+self.tcinputs["DomainName"] for mailbox in self.manually_associate_mailboxes])

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.testdata.delete_online_mailboxes(self.mailboxes)
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.tcinputs['Name'])
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
