# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.

    teardown()  --  Performs final clean up after test case execution.


"""

import time,json
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Hub.constants import O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Components.panel import RModalPanel
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch, CustomFilter


class TestCase(CVTestCase):
    """
    Class for executing Test Case for Microsoft Office 365 Teams CI
    and Compliance search

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Microsoft Office 365 Teams CI and Compliance Search"
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
        self.teams = None
        self.datatype = None
        self.app_name = None
        self.global_admin = None
        self.__rmodalpanel = None
        self.password = None
        self.service_catalogue = None
        self.office365_plan = None
        self.expected_count = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['complianceUser'],
                                 self.tcinputs['compliancePassword'])
        self.app_type = O365AppTypes.teams
        self.navigator = self.admin_console.navigator
        self.teams = self.tcinputs['Teams'].split(",")
        self.app_name = self.tcinputs.get('Name', f"Teams_TC__{str(int(time.time()))}")
        self.__rmodalpanel = RModalPanel(self.admin_console)
        self.global_admin = self.tcinputs['GlobalAdmin']
        self.password = self.tcinputs['Password']
        self.datatype = json.loads(self.tcinputs['DataTypes'])
        is_react = False
        if self.inputJSONnode['commcell']['isReact'] == 'true':
            is_react = True
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react)
        self.expected_count = self.tcinputs["ExpectedCount"]

    @TestStep()
    def create_app(self):
        """Create the MS Teams Office 365 App."""
        self.navigator.navigate_to_office365()
        self.office365_obj.create_office365_app(name=self.app_name, global_admin=self.global_admin,
                                                password=self.password)
        self.app_name = self.office365_obj.get_app_name()

    @TestStep()
    def return_to_app_page(self):
        """Navigate back to the MS Teams Office 365 App Page."""
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)

    @TestStep()
    def apply_ci_filter_and_get_job(self, job_helper_obj):
        """Apply filters for ci job
            Args:
                job_helper_obj(Object): Object of JobHelper class
        """
        job_helper_obj.add_filter(column='Server', value=self.app_name)
        job_helper_obj.add_filter(column='Operation', value='Content Indexing')
        job_id = job_helper_obj.get_job_ids()
        return job_id

    @TestStep()
    def verify_ci_job(self):
        """Verifying that CI is triggered automatically after backup"""
        job_helper = Jobs(self.admin_console)
        self.office365_obj.access_ci_job()
        job_helper.add_filter(column='Server', value=self.app_name)
        job_helper.add_filter(column='Operation', value='Content Indexing')
        job_id = job_helper.get_job_ids()
        if job_id:
            job_id = job_id[0]
        else:
            self.log.info("CI Job not present in job history page. Accessing active jobs")
            job_helper.access_active_jobs()
            job_id = self.apply_ci_filter_and_get_job(job_helper)[0]
        self.log.info(f"Job id received is:{job_id}")
        try:
            ci_job_details = job_helper.job_completion(job_id)
            self.log.info(f"CI Job got triggered and completed successfully")
            return ci_job_details
        except Exception as exp:
            self.log.info(exp)
            raise CVTestStepFailure(f'CI job did not get triggered')

    @TestStep()
    def verify_compliance(self):
        """Verify compliance search is working
        """
        app = ComplianceSearch(self.admin_console)
        gov_app = GovernanceApps(self.admin_console)

        self.navigator.navigate_to_governance_apps()
        app.set_datatype(self.app_type, self.datatype)
        app.click_search_button()
        custom_filter = CustomFilter(self.admin_console)
        custom_filter.apply_custom_filters_with_search(
             select_value=self.app_name, id="emailFromAutoCompleteCLIENTID")

        totalcount = app.get_total_rows_count()

        if int(totalcount) != int(self.tcinputs['ExpectedCount']):
            raise CVTestStepFailure(f'Compliance search count mismatch')

        searchcount = app.get_total_rows_count(self.tcinputs['SearchKeyword'])

        if int(searchcount) != int(self.tcinputs['ExpectedSearchCount']):
            raise CVTestStepFailure(f'Compliance search ContentSearch count mismatch')

    def run(self):
        """Main function for test case execution"""
        try:
            self.create_app()
            self.return_to_app_page()
            self.office365_plan = self.tcinputs.get("plan")
            self.office365_obj.add_teams(self.teams, self.office365_plan)
            bkp_job = self.office365_obj.run_backup()
            count_backup_items = int(bkp_job[self.admin_console.props['label.noOfObjectsBackedup']])
            self.return_to_app_page()
            ci_job = self.verify_ci_job()
            count_ci_items = int(ci_job[self.admin_console.props['label.totalItemsProcessed']])
            if count_backup_items != count_ci_items:
                raise CVTestStepFailure(
                    f"CI count: {count_ci_items} and backup count: {count_backup_items} do not match")
            self.log.info("CI job verified")
            self.verify_compliance(self.expected_count)
            self.log.info("Compliance search verified")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
