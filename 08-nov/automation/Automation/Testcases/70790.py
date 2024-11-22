# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

This test case verifies "API Viewer in Command Center" feature

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Helper.ApiViewerHelper import ApiViewer
import random

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "Web automation to test API Viewer feature in Command Center"
        self.browser = None
        self.admin_console = None
        self.api_viewer = None

    def setup(self):
        """Setup function of this test case"""
        self.cs_user = self.inputJSONnode['commcell']['commcellUsername']
        self.cs_password = self.inputJSONnode['commcell']['commcellPassword']
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.cs_user, self.cs_password)
        self.api_viewer = ApiViewer(self.admin_console)
    
    @TestStep()
    def run_test(self):
        """Run function of this test case"""
        # 1. On entering the keyboard shortcut recording should start
        self.api_viewer.toggle_api_viewer()
        if not self.api_viewer.is_recording():
            self.log.error("API recording didn't start")
            raise CVTestStepFailure("API recording didn't start")
        self.log.info("API Recording started")
        self.api_viewer.populate_apis()

        # 2. On stopping the recording a modal should be opened
        self.api_viewer.toggle_api_viewer()
        if not self.api_viewer.is_listing_table_present():
            self.log.error("API listing modal not opened")
            raise CVTestStepFailure("API listing modal not opened")
        self.log.info("API listing modal is opened")

        # 3. Table has columns Type, API, Description, Request, Response
        self.api_viewer.display_all_columns()
        self.log.info("Table has columns Type, API, Description, Request, Response")

        # 4. Adjust pagination in the table
        if not self.api_viewer.test_pagination():
            self.log.error("Pagination is not proper")
            raise CVTestStepFailure("Pagination is not proper")
        self.log.info("Adjusting pagination in the table is success")

        # 5. Ensure all the GET, POST, DELETE and PUT APIs are listed
        check, api_type = self.api_viewer.check_api_types()
        if not check:
            self.log.error(f"{api_type} API is not present in API viewer table")
            raise CVTestStepFailure(f"{api_type} API is not present in API viewer table")
        self.log.info("All types of API are present")

        # 6. .do APIs are listed
        if not self.api_viewer.check_do_apis():
            self.log.error(".do API is not present in API viewer table")
            raise CVTestStepFailure(".do API is not present in API viewer table")
        self.log.info(".do APIs are present")

        # 7. Reports APIs are listed
        if not self.api_viewer.check_report_apis():
            self.log.error("Report API is not present in API viewer table")
            raise CVTestStepFailure("Report API is not present in API viewer table")
        self.log.info("Reports APIs are present")

        # 8. Apply filters on all columns
        if not self.api_viewer.apply_filters():
            self.log.error("Filtering of API list is not working")
            raise CVTestStepFailure("Filtering of API list is not working")
        self.log.info("Filtering of API list is working")

        # 9. Creating and deleting views
        view_name = "testview" + str(random.randint(1, 1000))
        self.api_viewer.create_view(view_name)
        self.api_viewer.delete_view(view_name)
        self.log.info("Creation and deletion of views is success")

        self.api_viewer.close_table()

    def run(self):
        """run function of this test case"""
        try:
            self.run_test()
            if self.commcell.client_groups.get("apiviewertest"):
                self.commcell.client_groups.delete("apiviewertest")
        except Exception:
            pass
        finally:
            AdminConsole.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
