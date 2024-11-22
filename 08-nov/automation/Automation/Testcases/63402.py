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
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Tenant User View of
    Metallic OneDrive V2 client :
    Basic Tenant View Validation for Metallic Onedrive existing Tenant
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_OneDrive_TenantView"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.tenant_password = None
        self.app_type = None
        self.users = None
        self.backup_user = None
        self.app_name = None
        self.utils = TestCaseUtils(self)

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.tenant_user_name = self.tcinputs['TenantUsername']
        self.tenant_password = self.tcinputs['TenantPassword']

    def setup(self):
        self.create_tenant()
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name,
                                 self.tenant_password)
        self.app_type = O365AppTypes.onedrive
        self.navigator = self.admin_console.navigator
        self.users = self.tcinputs['Users'][0]
        self.backup_user = self.tcinputs['Users'][1]
        self.app_name = self.tcinputs['AppName']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type , is_react=True )

    def verify_overviewpage(self, stats_dict, calendar_exists):
        """
        Verification of the details in overview page
        """
        try:
            for key in stats_dict:
                if stats_dict[key] is None:
                    raise Exception("{} is having value {}".format(key, stats_dict[key]))
                else:
                    self.log.info("{} is having value {}".format(key, stats_dict[key]))
            if calendar_exists:
                self.log.info("Overview Page is Verified")
            else:
                raise Exception("Calendar is missing in the Overview Page")
        except Exception:
            raise CVTestStepFailure(f'Overview Page is not shown properly')

    def verify_browsepage(self,browse_stats ):
        """
        Verification of the details in browse page
        """
        try:
            for key in browse_stats:
                if browse_stats[key] is None:
                    raise Exception("{} is having value {}".format(key, browse_stats[key]))
                else:
                    self.log.info("{} is having value {}".format(key, browse_stats[key]))
            self.log.info("Browse Page is Verified")
        except Exception:
            raise CVTestStepFailure(f'Browse Page is not shown properly')

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.admin_console.wait_for_completion()
            stats_dict, calendar_exists = self.office365_obj.fetch_onedrive_overview_details()
            self.verify_overviewpage(stats_dict, calendar_exists)
            self.office365_obj.browse_entity(entity_name=self.users)
            browse_stats = self.office365_obj.get_browse_page_details(folder_name="My Drive")
            self.verify_browsepage(browse_stats)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            restore_details=self.office365_obj.run_restore(email=self.backup_user, unconditional_overwrite=True)
            if restore_details['No of files restored'] == '2':
                self.log.info("Restore was successful")
            else:
                raise CVTestStepFailure("Restore was failure , No. of files restored = {} out of 2 ".format(restore_details['No of files restored']))
            self.log.info("Tenant User view is verified")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)