# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Verification of Server Plan Scheduled Backups for SharePoint v2 client

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""


import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.panel import RModalPanel
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Office365Pages import constants as o365_constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.sharepoint import SharePoint
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "SharePoint V2: Verification of Server Plan Scheduled Backups"
        self.epoch_time = str(int(time.time()))
        self.browser = None
        self.plan = None
        self.navigator = None
        self.table = None
        self.admin_console = None
        self.sharepoint = None
        self.plans_page = None
        self.bkp_start_time = None
        self.jobs = None
        self.modal_panel = None
        self.server_plan = None
        self.sites = {}
        self.site_url_list = []

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])

            self.jobs = Jobs(self.admin_console)
            self.modal_panel = RModalPanel(self.admin_console)
            self.table = Rtable(self.admin_console)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.sites = self.tcinputs['Sites']
            self.site_url_list = list(self.sites.keys())
            self.plan = self.tcinputs['Office365Plan']

            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = SharePoint.AppType.share_point_online
            self.sharepoint = SharePoint(self.tcinputs, self.admin_console, is_react=True)

            self.bkp_start_time = str(int(self.epoch_time) + (60 * 60))  # 60 minutes
            server_plan_time = self.sharepoint.convert_timestamp_to_server_plan_time(
                int(self.bkp_start_time))
            rpo_dict = [{
                'BackupType'    : 'Incremental',
                'Agents'        : 'All agents',
                'Frequency'     : '1',
                'FrequencyUnit' : 'Day(s)',
                'StartTime'     : server_plan_time
            }]
            storage = o365_constants.SharePointOnline.STORAGE_DICT.value
            storage['pri_storage'] = self.tcinputs['Storage']
            self.server_plan = o365_constants.SharePointOnline.SERVER_PLAN_NAME.value + self.epoch_time

            self.navigator.navigate_to_plan()
            self.plans_page = Plans(self.admin_console)
            self.plans_page.create_server_plan(
                self.server_plan, storage, rpo_dict)
            self.tcinputs['ServerPlan'] = self.server_plan
            self.navigator.navigate_to_office365()
            self.sharepoint.create_office365_app()
            self.sharepoint.wait_for_discovery_to_complete()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_bkp_job_initiation(self):
        """Verify that backup jobs complete successfully"""
        try:
            self.sharepoint.view_jobs()
            retry = 0
            while retry <= 10:
                time.sleep(90)
                if int(self.table.get_total_rows_count()) >= 1:
                    job_id = self.jobs.get_job_ids()[0]
                    self.jobs.access_job_by_id(job_id)
                    job_details = self.jobs.job_details()
                    self.modal_panel.close()
                    if (job_details[self.admin_console.props['Status']] not in
                            ["Committed", "Completed", "Completed w/ one or more errors",
                             "Completed w/ one or more warnings"]):
                        raise Exception(f'Job {job_id} did not complete successfully')
                    else:
                        self.log.info(f'Job {job_id} completed successfully')
                    break
                self.browser.driver.refresh()
                retry += 1
            if retry > 10:
                raise Exception('Backup Job did not get initiated according to server plan or '
                                'Job is not completed in stipulated time')
        except Exception:
            raise CVTestStepFailure(f'Exception while verifying backup job initiation')

    def run(self):
        try:
            self.sharepoint.add_user(users=self.sites)
            sleep_time = int(self.bkp_start_time) - (current_time := int(time.time()))
            self.log.debug(f'{self.bkp_start_time} - {current_time} = {sleep_time}')
            if sleep_time > 0:
                self.log.info(f'Sleeping for {sleep_time // 60} mins and {sleep_time % 60} secs')
                time.sleep(sleep_time)
            self.verify_bkp_job_initiation()
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_office365()
                self.sharepoint.delete_office365_app(self.tcinputs['Name'])
                self.navigator.navigate_to_plan()
                self.plans_page.delete_plan(self.server_plan)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
