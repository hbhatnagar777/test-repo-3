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

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Hub.office365_apps import DashboardTile
from Web.AdminConsole.Office365Pages import constants
from Web.AdminConsole.Office365Pages.onedrive import OneDrive
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """OneDrive Self-service verification"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "OneDrive Self Service Metallic Testcase"
        self.browser = None
        self._driver = None
        self.backup_jobID = None
        self.client_name = None
        self.cvcloud_object = None
        self.users = None
        self.o365_plan = None
        self.onedrive = None
        self.navigator = None
        self.admin_console = None
        self.dashboard_tile = None
        self.mssql = None
        self.office365_obj = None
        self.tcinputs = {
            'Name': None,
            'Email': None,
            'O365Plan': None,
            'Size': None,
            'Items': None
        }

    def setup(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()

            self.admin_console = AdminConsole(
                self.browser, self.inputJSONnode['commcell']['webconsole_url'])

            self.admin_console.login(
                self.inputJSONnode['commcell']['loginUsername'],
                self.inputJSONnode['commcell']['loginPassword'], saml=True)

            self._driver = self.admin_console.driver
            self.app_type = O365AppTypes.onedrive
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365(access_tab=False)
            self.tcinputs['office_app_type'] = OneDrive.AppType.one_drive_for_business
            self.onedrive = OneDrive(self.tcinputs, self.admin_console)
            self.dashboard_tile = DashboardTile(self.admin_console)
            self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def verify_dashboard(self):
        """Verifies if client present in dashboard"""

        panel_info = RPanelInfo(self.admin_console)
        is_secure = True

        dashboard_tiles = self.dashboard_tile.get_all_details()
        self.log.info(f"User details are: {dashboard_tiles}")

        client_list = []
        for tile in dashboard_tiles:
            client_list.append(tile['App name'])
        self.log.info(client_list)

        for client in client_list:
            self.dashboard_tile.click_details_by_client(client)
            client_details = panel_info.get_details()
            if client_details['Email address'] != self.tcinputs['Email']:
                is_secure = False
            self._driver.back()

        if is_secure:
            self.log.info("Only user related clients are visible")
        else:
            raise CVTestStepFailure(f"User can see other's clients")

    @test_step
    def verify_restore(self):
        """Verifies restore page"""
        restore_job_details = self.office365_obj.perform_operations_on_self_user_client(
            client_name=self.tcinputs["Name"],
            operation="Restore")
        self.log.info(restore_job_details)

        if int(restore_job_details['No of files restored']) != self.tcinputs['RowNum']:
            raise CVTestStepFailure(f"Restore Count Mismatch")

    def run(self):
        try:
            self.verify_dashboard()
            self.verify_restore()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            self.log.info(f'Test case status: {self.status}')
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
