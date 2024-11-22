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
from Web.AdminConsole.Hub.constants import HubServices, GoogleWorkspaceAppTypes
from Web.AdminConsole.Hub.googleworkspace_apps import GoogleWorkspaceApps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_GoogleWorkspace_Basic_Acceptance:
    Basic Validation for Metallic Google Drive existing and new tenant
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.google_obj = None
        self.name = "Metallic_GooleWorkspace_GDrive_Acceptance for Service Catalogue"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.app_type = None
        self.users = None
        self.inc_user = None
        self.inc_files = None
        self.app_name = None
        self.service_catalogue = None
        self.utils = TestCaseUtils(self)

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('Google-Auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@gdrive{current_timestamp}.com')

    def setup(self):
        self.create_tenant()
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name,
                                 self.inputJSONnode['commcell']['tenant_password'])
        self.service = HubServices.google_workspace
        self.app_type = GoogleWorkspaceAppTypes.gdrive
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_service_catalogue()
        self.service_catalogue.start_googleworkspace_trial()
        self.users = self.tcinputs['Users'].split(",")
        self.inc_user = self.tcinputs['IncrementalUser'].split(",")
        self.inc_files = self.tcinputs['IncrementalFiles']
        self.app_name = datetime.datetime.now().strftime('Client%d%b%H%M')
        self.log.info("Creating an object for Google Workspace helper")
        self.google_obj = GoogleWorkspaceApps(self.admin_console, self.app_type)

    def run(self):
        """Main function for test case execution"""
        try:
            self.google_obj.create_googleworkspace_app(name=self.app_name,
                                                       super_admin=self.tcinputs['SuperAdmin'],
                                                       password=self.tcinputs['Password'])
            self.app_name = self.google_obj.app_name
            self.navigator.navigate_to_plan()
            plans = self.google_obj.get_plans_list()
            self.gw_plan = [value for value in plans if 'google-workspace-plan' in value][0]
            self.google_obj.verify_retention_of_gw_plans(self.tenant_name.replace("-", ""), plans)
            self.navigator.navigate_to_usage()
            self.google_obj.verify_google_usage_report()
            self.navigator.navigate_to_googleworkspace()
            self.google_obj.access_googleworkspace_app(self.app_name)
            self.google_obj.add_content(self.users, self.gw_plan)
            bkp_job_details = self.google_obj.run_backup()
            self.navigator.navigate_to_googleworkspace()
            self.google_obj.access_googleworkspace_app(self.app_name)
            self.google_obj.add_content(self.inc_user, self.gw_plan)
            bkp_job_details_incr = self.google_obj.run_backup()
            if int(bkp_job_details_incr['No of objects backed up']) != self.inc_files:
                raise Exception(f'Incremental backup is not backing up new items')
            self.log.info("Incremental is verified")
            self.navigator.navigate_to_googleworkspace()
            self.google_obj.access_googleworkspace_app(self.app_name)
            restore_job_details = self.google_obj.run_restore(destination='Restore to original location',
                                                              restore_option='UNCONDITIONALLY_OVERWRITE')
            if (int(bkp_job_details['No of objects backed up']) + int(
                    bkp_job_details_incr['No of objects backed up']) !=
                int(restore_job_details['No. of successes'])) or (
                    restore_job_details['Failures'] != '0 Folders, 0 Files'):
                raise Exception(f'Restore is not verified')
            self.log.info("Restore is verified")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        try:
            self.admin_console.logout()
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.hub_utils.deactivate_tenant(self.tenant_name)
            self.hub_utils.delete_tenant(self.tenant_name)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
        finally:
            self.log.info("Tear down function executed")
