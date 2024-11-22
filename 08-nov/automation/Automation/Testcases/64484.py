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
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from Application.Exchange.ExchangeMailbox.utils import test_step
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch, CustomFilter
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    OneDrive Content Indexing and Compliance search:
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.__jobs = None
        self.name = "Metallic OneDrive CI verification"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_dashboard = None
        self.app_type = None
        self.users = None
        self.app_name = None
        self.office365_plan = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['tenant_user_name'],
                                 self.tcinputs['tenant_password'])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.onedrive
        self.navigator = self.admin_console.navigator
        self.users = self.tcinputs['Users'].split(",")
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        is_react = False
        if self.inputJSONnode['commcell']['isReact'] == 'true':
            is_react = True
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react)

    @test_step
    def createapp_runbackup(self):
        """Creates OneDrive app, adds users, triggers backup"""
        try:
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'])
            self.app_name = self.office365_obj.get_app_name()
            self.office365_plan = self.tcinputs['O365_Plan']
            self.office365_obj.add_user(self.users, self.office365_plan)
            bkp_job_details = self.office365_obj.run_backup()
            self.log.info(f"Backupjob details are:{bkp_job_details}")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    @test_step
    def verify_cijob(self):
        """Verifying that CI is triggered automatically after backup"""
        self.navigator.navigate_to_jobs()
        job_helper = Jobs(self.admin_console)
        job_helper.access_job_history()
        job_helper.show_admin_jobs()
        job_helper.add_filter(column='Destination client', value=self.app_name)
        job_helper.add_filter(column='Operation', value='Content Indexing')
        current_job_ids = job_helper.get_job_ids()

        if current_job_ids:
            jobid = current_job_ids[0]
        else:
            job_helper.access_active_jobs()
            job_helper.add_filter(column='Destination client', value=self.app_name)
            job_helper.add_filter(column='Operation', value='Content Indexing')
            jobid = job_helper.get_job_ids()[0]

        try:
            ci_job_details = job_helper.job_completion(jobid)
            if ci_job_details['Status'] != 'Completed':
                raise CVTestStepFailure(f'Content Indexing job not completed successfully')
            self.log.info(f"Job details are: {ci_job_details}")
        except Exception as exp:
            self.log.info(exp)
            raise CVTestStepFailure(f'Problem with Content Indexing job starting/completing')

    @test_step
    def verify_compliance(self):
        """Verify Compliance search count"""
        app = ComplianceSearch(self.admin_console)
        gov_app = GovernanceApps(self.admin_console)

        self.navigator.navigate_to_governance_apps()
        gov_app.select_compliance_search()
        app.set_datatype(self.tcinputs['Datatypes'])
        app.click_search_button()

        try:
            custom_filter = CustomFilter(self.admin_console)
            custom_filter.apply_custom_filters_with_search(
                {"Client name": [self.app_name]})
        except Exception as ex:
            self.log.info(ex)
            self.log.info(f"Failed to filter with client name, check if the client is created")

        totalcount = app.get_total_rows_count()

        if int(totalcount) != int(self.tcinputs['ExpectedCount']):
            raise CVTestStepFailure(f'Compliance search count mismatch')

        searchcount = app.get_total_rows_count(self.tcinputs['SearchKeyword'])

        if int(searchcount) != int(self.tcinputs['ExpectedSearchCount']):
            raise CVTestStepFailure(f'Compliance search ContentSearch count mismatch')

    def run(self):
        """Main function for test case execution"""
        try:
            self.createapp_runbackup()
            self.verify_cijob()
            self.verify_compliance()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
