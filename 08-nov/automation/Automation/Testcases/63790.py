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
import time
from datetime import datetime

from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic Exchange Case for recovery point creation and validation"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.users = None
        self.exmb_client = None
        self.testdata = None
        self.mailboxes = None
        self.group_name = None
        self.service = None
        self.app_type = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.testdata = None
        self.hub_dashboard = None
        self.app_name = None
        self.service_catalogue = None
        self.utils = TestCaseUtils(self)

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.now().strftime('Exchange-Auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@exchange{current_timestamp}.com')

    def run_backups(self, count=2):
        """Run multiple backup jobs and return the job ids"""
        job_ids = list()
        while count > 0:
            if self.admin_console.check_if_entity_exists('xpath', "//div[contains(@id,'Office365AppTabs')]"):
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

    def setup(self):
        self.create_tenant()
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name,
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.exchange
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_service_catalogue()
        self.service_catalogue.start_office365_trial()
        self.users = self.tcinputs['Users'].split(",")
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

    def run(self):
        """Main function for test case execution"""

        try:
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'])
            self.app_name = self.office365_obj.get_app_name()
            self.navigator.navigate_to_plan()
            plans = self.office365_obj.get_plans_list()
            self.office365_obj.verify_retention_of_o365_plans(self.tenant_name, plans)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.office365_obj.add_user(users=self.users)
            self.run_backups()
            self.verify_recovery_point_operations(self.users)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.hub_utils.deactivate_tenant(self.tenant_name)
        self.hub_utils.delete_tenant(self.tenant_name)