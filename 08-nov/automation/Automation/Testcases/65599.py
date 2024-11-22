# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes TestCase class

    setup()         --  Sets up the variables required for running the testcase

    run()           --  Run function of this test case

    teardown()      --  Tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Hub.constants import O365AppTypes
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Application.Sharepoint.sharepoint_online import SharePointOnline


class TestCase(CVTestCase):
    """Class for testing Sharepoint Restore job restartability using web automation
    Uses one site as OOP restore source and another as OOP restore destination
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes the test case object
        """
        super(TestCase, self).__init__()
        self.name = 'Metallic O365 SharePoint Restore Restartability Validation'
        self.utils = TestCaseUtils(self)
        self.office_365 = None
        self.admin_console = None
        self.browser = None
        self.app_type = None
        self.app_name = None
        self.navigator = None
        self.backup_site = None
        self.backup_site_url = None
        self.restore_site = None
        self.restore_site_url = None
        self.sharepoint = None
        self.jobs = None
        self.job_details = None
        self.view_logs = None
        self.sp_api_object = None
        self.library_name = None

    def _initialize_sp_api_object(self):
        """Initializes SharePoint object to make api calls"""
        self.sp_api_object = SharePointOnline(self)
        self.sp_api_object.azure_app_id = self.tcinputs.get("ClientId", "")
        self.sp_api_object.azure_app_secret = self.tcinputs.get("ClientSecret", "")
        self.sp_api_object.azure_app_tenant_id = self.tcinputs.get("AzureDirectoryId", "")
        self.sp_api_object.tenant_url = self.tcinputs.get("SiteAdminUrl", "")

    def setup(self):
        """Setup function for this test case
        Initializes all the driver objects that will be used to perform operations
        """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.app_type = O365AppTypes.sharepoint
        self.navigator = self.admin_console.navigator

        sites = list(zip(self.tcinputs['Sites'].split(","),
                         self.tcinputs['SitesTitle'].split(",")))
        self.backup_site = {sites[0][0]: sites[0][1]}
        self.backup_site_url = sites[0][0]
        self.restore_site = {sites[1][0]: sites[1][1]}
        self.restore_site_url = sites[1][0]
        self.library_name = self.tcinputs["Library"]

        self.app_name = self.tcinputs['Name']
        self.office_365 = Office365Apps(self.admin_console, self.app_type, is_react=True)
        self.jobs = Jobs(self.admin_console)

        self._initialize_sp_api_object()
        self.sp_api_object.site_url = self.restore_site_url
        self.sp_api_object.delete_sp_library(self.library_name)

    @test_step
    def _validate_oop_restore_restartability(self):
        """Initiates an out-of-place restore job and verifies its restartability"""
        try:
            job_id = self.office_365.initiate_oop_restore(backup_site=self.backup_site,
                                                          oop_site=self.restore_site,
                                                          library=self.library_name)

            file_count = self.tcinputs.get('BackedUpFiles')
            if file_count is None:
                self.log.info("'BackedUpFiles' was not found in tcinputs. Checking from source")
                self.sp_api_object.site_url = self.backup_site_url
                file_count = self.sp_api_object.get_file_count_in_sp_library(self.library_name)
                self.sp_api_object.site_url = self.restore_site_url
            self.log.info(f"Backed up files: {file_count}")

            self.office_365.verify_sharepoint_restore_restartability(
                self.sp_api_object, job_id, self.library_name, file_count)
        except Exception as e:
            raise CVTestStepFailure(f'Error while verifying restore restartability: {e}')

    def run(self):
        """Run function for this test case
        Contains the main execution logic that determines if this testcase passed or failed
        """
        try:
            self.navigator.navigate_to_office365()
            self.office_365.access_office365_app(self.app_name)
            self._validate_oop_restore_restartability()
        except Exception as exception:
            self.utils.handle_testcase_exception(exception)

    def tear_down(self):
        """Tear down function for this test case
        Tears down all the items created for the purpose of this testcase
        """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
