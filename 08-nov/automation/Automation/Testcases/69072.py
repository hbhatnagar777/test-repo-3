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
from AutomationUtils import constants
from Metallic.hubutils import HubManagement
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.Office365Pages.constants import O365Region
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVWebAutomationException


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_Exchange_NonEnglish_Backup_Browse_Restore
    Metallic Exchange Online backup, browse and restore in a non-english language
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_Exchange_NonEnglish_Backup_Browse_Restore for Service Catalogue"
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
        self.utils = TestCaseUtils(self)
        self.report = None

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['tenantUserName'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.report = Report(self.admin_console)
        self.admin_console.change_language(self.tcinputs['Language'], self.report)
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
                if O365Region.PLAN_EASTUS2.value in plan.lower():
                    server_plan = plan
                    break

            self.navigator.navigate_to_service_catalogue()
            self.service_catalogue.choose_service_from_service_catalogue(service=self.service.value,
                                                                         id=self.app_type.value)
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'],
                                                    plan=server_plan)
            self.app_name = self.office365_obj.get_app_name()

            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)

            self.office365_obj.add_user(self.users)

            backup_job_details = self.office365_obj.run_backup()

            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)

            self.office365_obj.click_restore_page_action()

            self.office365_obj.access_folder_in_browse(folder_name=self.users[0].split("@")[0])
            self.office365_obj.access_sub_folder_in_browse_tree('Inbox')
            self.office365_obj.click_browse_bread_crumb_item(self.app_name)

            restore_job_details = self.office365_obj.perform_restore_operation()

            Successful_messages=self.admin_console.props['label.successfulMessages']
            Skipped_messages=self.admin_console.props['label.skippedMessages']

            if backup_job_details[Successful_messages] != restore_job_details[Successful_messages] + \
                    restore_job_details[Skipped_messages] and restore_job_details[Successful_messages] == 0:
                raise Exception(f'Restore is not verified')
            self.log.info("Restore is verified")

            restore_dict = {'ClientLevel': True, 'Job ID': backup_job_details['Job Id'], 'Entity': ''}

            backup_count, point_in_time_restore_job_details = (
                self.office365_obj.perform_point_in_time_restore(restore_dict, backup_job_details))

            if backup_job_details[Successful_messages] != point_in_time_restore_job_details[Successful_messages] + \
                    point_in_time_restore_job_details[Skipped_messages] and point_in_time_restore_job_details[Successful_messages] == 0:
                raise Exception(f'Point in time Restore is verified')
            self.log.info("Point in time Restore is verified")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
    def tear_down(self):
        """Tear Down function of this test case"""
        if self.status == constants.PASSED:
            self.navigator.navigate_to_office365()
            self.office365_obj.delete_office365_app(self.app_name)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)