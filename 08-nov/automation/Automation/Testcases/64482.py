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
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Validation Test of Metallic_O365_React_Sharepoint_Calendar_View_PIT_Restore:
    Basic Validation for Calendar View (Point in Time) Restore in an existing Metallic SharePoint Client
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_React_Sharepoint_Calender_View_PIT_Restore"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.service_catalogue = None
        self.app_type = None
        self.sites = None
        self.app_name = None
        self.utils = TestCaseUtils(self)
        self.groups = None

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        # This testcase needs an existing comcell user with client creation, backup and restore permissions
        self.admin_console.login(self.tcinputs['ExistingComcellUserName'],
                                 self.tcinputs['ExistingComcellPassword'])
        self.app_type = O365AppTypes.sharepoint
        self.navigator = self.admin_console.navigator
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            for backed_up_entity in self.tcinputs['BackedUpEntities']:
                if backed_up_entity['ClientLevel']:
                    restore_level = "Client level"
                else:
                    restore_level = "Site level"
                # Verify PIT Restore
                backup_application_size, restore_application_size = self.office365_obj.perform_point_in_time_restore(backed_up_entity)
                # Difference between backup size and restore size can maximum be 1 MB
                if abs(backup_application_size - restore_application_size) > 1:
                    # Automation Folder is restored for each entity
                    raise Exception(f'Backup and Restore Size mismatch in {restore_level} Restore')

                self.log.info(f"{restore_level} PIT Restore is verified")

            self.log.info("Calender View and Point in Time Restore verified")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)