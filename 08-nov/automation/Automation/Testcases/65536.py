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

from Application.Exchange.ExchangeMailbox.utils import test_step
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Hub.constants import O365AppTypes
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
        self.name = "Metallic_O365_React_Sharepoint_Content_Indexing"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.app_type = None
        self.sites = None
        self.app_name = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        # This testcase needs an existing comcell user with client creation,
        # backup, Content Indexing and Compliance Search permissions
        self.admin_console.login(self.tcinputs['ExistingComcellUserName'],
                                 self.tcinputs['ExistingComcellPassword'])
        self.app_type = O365AppTypes.sharepoint
        self.navigator = self.admin_console.navigator
        self.sites = dict(zip(self.tcinputs['Site'].split(","), self.tcinputs['SiteTitle'].split(",")))
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

    @test_step
    def verify_ci_job(self):
        """Verifying that CI is triggered automatically after backup"""
        self.navigator.navigate_to_jobs()
        job_helper = Jobs(self.admin_console)
        job_helper.access_active_jobs()
        current_jobs = job_helper.get_job_ids()
        client_present = False
        if current_jobs:
            client_present = job_helper.check_if_item_present_in_column(column='Destination client',
                                                                        value=self.app_name)
        if client_present:
            job_helper.add_filter(column='Destination client', value=self.app_name)
            job_helper.add_filter(column='Operation', value='Content Indexing')
            jobid = job_helper.get_job_ids()
        # In case job completed before navigating to active jobs
        else:
            job_helper.access_job_history()
            self.admin_console.click_button('Show admin jobs')
            job_helper.add_filter(column='Destination client', value=self.app_name)
            job_helper.add_filter(column='Operation', value='Content Indexing')
            jobid = job_helper.get_job_ids()[0]

        try:
            cijob_details = job_helper.job_completion(jobid)
            if cijob_details['Status'] != 'Completed':
                raise CVTestStepFailure(f'Content Indexing job not completed successfully')
            self.log.info(f"CI Job got triggered and completed successfully")
            self.log.info(f"Job details are: {cijob_details}")
        except Exception as exp:
            self.log.info(exp)
            raise CVTestStepFailure(f'Problem with Content Indexing job starting/completing')

    @test_step
    def verify_compliance(self):
        """Verify Compliance search count"""
        compliance_search = ComplianceSearch(self.admin_console)
        gov_app = GovernanceApps(self.admin_console)

        self.navigator.navigate_to_governance_apps()
        gov_app.select_compliance_search()
        # Remove default Exchange Mailbox selection
        # Add default SharePoint Online selection
        compliance_search.unset_searchview_dropdown(search_view_types=['Exchange mailbox'])
        compliance_search.set_searchview_dropdown(search_view_types=['SharePoint Online'])
        compliance_search.click_search_button()
        total_count = compliance_search.get_total_rows_count()

        if int(total_count) != int(self.tcinputs['ExpectedCount']):
            raise CVTestStepFailure(f'Compliance search ContentSearch count mismatch')
        else:
            self.log.info(f"Compliance search ContentSearch count matched successfully")

        search_count = compliance_search.get_total_rows_count(self.tcinputs['SearchKeyword'])

        if int(search_count) != int(self.tcinputs['ExpectedSearchCount']):
            raise CVTestStepFailure(
                f'Compliance search ContentSearch count mismatch for {self.tcinputs["SearchKeyword"]}')
        else:
            self.log.info(
                f"Compliance search ContentSearch count matched successfully for {self.tcinputs['SearchKeyword']}")

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'])
            self.app_name = self.office365_obj.get_app_name()

            self.navigator.navigate_to_plan()
            self.office365_obj.get_plans_list()

            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.office365_obj.add_user(self.sites)
            bkp_job_details = self.office365_obj.run_backup()
            self.log.info(f"Backupjob details are:{bkp_job_details}")

            self.verify_ci_job()
            self.verify_compliance()

            self.log.info("Content Indexing and Compliance Search Metallic testcase is verified")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)