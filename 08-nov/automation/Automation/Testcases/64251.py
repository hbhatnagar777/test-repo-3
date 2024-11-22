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
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole import Office365Pages
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of Metallic_O365_React_Sharepoint_Acceptance:
    Basic Validation for Metallic SharePoint existing and new tenant
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_Sharepoint_Acceptance"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.service_catalogue = None
        self.app_type = None
        self.sites = None
        self.inc_sites = None
        self.inc_count =  None
        self.app_name = None
        self.utils = TestCaseUtils(self)

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('O365-Auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@sharepoint{current_timestamp}.com')

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
        self.app_type = O365AppTypes.sharepoint
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)

        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_service_catalogue()
        self.service_catalogue.start_office365_trial()
        self.sites = dict(zip(self.tcinputs['Sites'].split(","), self.tcinputs['SitesTitle'].split(",")))
        self.inc_sites = dict(zip(self.tcinputs['IncrementalSites'].split(","), self.tcinputs['IncrementalSitesTitle'].split(",")))
        self.inc_count = self.tcinputs["IncrementalCount"]
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
            total_associated_sites = self.office365_obj.add_user(self.sites)
            self.office365_obj.refresh_cache()
            bkp_job_details = self.office365_obj.run_backup()
            self.office365_obj.verify_status_tab_stats(job_id=bkp_job_details['Job Id'],
                                                       status_tab_expected_stats={
                                                           "Total": total_associated_sites,
                                                           "Successful": total_associated_sites
                                                       })
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.office365_obj.add_user(self.inc_sites)
            total_associated_sites = total_associated_sites+1
            bkp_job_details_incr = self.office365_obj.run_backup()
            self.office365_obj.verify_status_tab_stats(job_id=bkp_job_details_incr['Job Id'],
                                                       status_tab_expected_stats={
                                                           "Total": total_associated_sites,
                                                           "Successful": total_associated_sites
                                                       })

            if int(bkp_job_details_incr['No of objects backed up']) != self.inc_count:
                raise Exception(f'Incremental backup is not backing up new items')
            self.log.info("Incremental is verified")
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            restore_job_details = self.office365_obj.run_restore()
            if restore_job_details['To be restored'] == restore_job_details['Skipped files'] or \
                    restore_job_details['No of files restored'] == '0' or restore_job_details[
                'Failures'] != '0 Folders, 0 Files':
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
