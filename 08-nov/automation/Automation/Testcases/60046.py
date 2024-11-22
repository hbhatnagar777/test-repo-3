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

from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_Exchange_Acceptance:
    Basic Validation for Metallic Exchange existing and new tenant
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_Exchange_Acceptance"
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
        self.exmbclient_object = None
        self.utils = TestCaseUtils(self)

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('Exchange-Auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@exchange{current_timestamp}.com')

    def initialize_exchange_object(self):
        """Initializes Exchange Object"""
        self.tcinputs['ProxyServers'] = ["dummy_name"]
        self.exmbclient_object = ExchangeMailbox(self)
        self.exmbclient_object.environment_type = 4
        self.exmbclient_object.client_name = self.app_name
        self.exmbclient_object.exchange_online_user = self.tcinputs['GlobalAdmin']
        self.exmbclient_object.exchange_online_password = self.tcinputs['Password']

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
        self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
        self.hub_dashboard.click_get_started()
        self.hub_dashboard.choose_service_from_dashboard()
        self.hub_dashboard.click_continue()
        self.hub_dashboard.wait_for_creation_of_storage_and_plan()
        self.hub_dashboard.select_option_to_enable_region_based_storage(value='No')
        self.hub_dashboard.click_new_configuration()
        self.navigator = self.admin_console.navigator
        self.users = self.tcinputs['Users'].split(",")
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type)

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
            self.office365_obj.add_user(self.users)
            bkp_job_details = self.office365_obj.run_backup()
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.initialize_exchange_object()
            for user in self.users:
                self.exmbclient_object.exchange_lib.modify_subject(user)
            restore_job_details = self.office365_obj.run_restore()
            if bkp_job_details['Successful messages'] != restore_job_details['Successful messages'] + \
                    restore_job_details['Skipped messages'] and restore_job_details['Successful messages'] == 0:
                raise Exception(f'Restore is not verified')
            self.log.info("Restore is verified")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.hub_utils.deactivate_tenant(self.tenant_name)
        self.hub_utils.delete_tenant(self.tenant_name)
