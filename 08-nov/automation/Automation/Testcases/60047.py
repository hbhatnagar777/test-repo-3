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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_OneDrive_Acceptance:
    Basic Validation for Metallic Onedrive existing and new tenant
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_OneDrive_Acceptance"
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
        self.utils = TestCaseUtils(self)

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('OneDrive-Auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@onedrive{current_timestamp}.com')

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
        self.app_type = O365AppTypes.onedrive
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
            time.sleep(20)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            bkp_job_details_incr_1 = self.office365_obj.run_backup()
            if int(bkp_job_details_incr_1['No of objects']) > 0:
                raise Exception(f'Incremental backup is again backing up previously backed up items')
            time.sleep(20)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            restore_job_details = self.office365_obj.run_restore()
            if int(bkp_job_details['No of objects'])+3 != int(restore_job_details['No of files restored']):
                raise Exception(f'Restore is not verified')
            self.log.info("Restore is verified")
            time.sleep(10)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            bkp_job_details_incr_2 = self.office365_obj.run_backup()
            if int(bkp_job_details_incr_2['No of objects']) != int(bkp_job_details['No of objects']):
                raise Exception(f'Incremental backup is not backing up new items')
            self.log.info("Incremental is verified")

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