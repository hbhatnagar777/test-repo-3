# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Verification of backupset level, site level, single page and multi pages backups

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
        self.name = "SharePoint V2 Web Automation: " \
                    "Verification of client level, backupset level, site level, single page and multi pages backups"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.sharepoint = None
        self.jobs = None
        self.plans_page = None
        self.sites = {}
        self.site_url_list = []
        self.site = None

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
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.plans_page = Plans(self.admin_console)
            self.sites = self.tcinputs['Sites']
            self.site_url_list = list(self.sites.keys())
            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = SharePoint.AppType.share_point_online
            self.sharepoint = SharePoint(self.tcinputs, self.admin_console, is_react=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def navigate_to_app_page(self):
        """Navigates to SharePoint app page"""
        self.admin_console.wait_for_completion()
        self.navigator.navigate_to_office365()
        self.sharepoint.access_office365_app(self.tcinputs['Name'])

    @test_step
    def verify_client_level_backup(self, total_webs_in_backup):
        """Initiates client level backup job and verifies it"""
        try:
            client_level_bkp = self.sharepoint.initiate_backup(client_level=True)
            self.sharepoint.verify_backup_job(job_id=client_level_bkp,
                                              status_tab_expected_stats={
                                                  "Total": total_webs_in_backup,
                                                  "Successful": total_webs_in_backup
                                              })
        except Exception:
            raise CVTestStepFailure('Exception while verifying client level backup')

    @test_step
    def verify_backupset_level_backup(self, total_webs_in_backup):
        """Initiates backupset level backup job and verifies it"""
        try:
            self.navigate_to_app_page()
            backupset_level_bkp = self.sharepoint.initiate_backup()
            self.sharepoint.verify_backup_job(job_id=backupset_level_bkp,
                                              status_tab_expected_stats={
                                                  "Total": total_webs_in_backup,
                                                  "Successful": total_webs_in_backup
                                              })
        except Exception:
            raise CVTestStepFailure('Exception while verifying backupset level backup')

    @test_step
    def verify_site_level_backup(self):
        """Initiates site level backup jobs and verifies them"""
        try:
            # Single and Multiple Sites Backup
            self.site = self.site_url_list[-1]
            # self.site_url_list.remove(self.site)
            self.navigate_to_app_page()
            single_site_bkp = self.sharepoint.initiate_backup(sites=[self.site])
            self.sharepoint.verify_backup_job(job_id=single_site_bkp,
                                              status_tab_expected_stats={
                                                  "Total": 1,
                                                  "Successful": 1
                                              })
            self.browser.driver.refresh()
            self.navigate_to_app_page()
            multiple_sites_bkp = self.sharepoint.initiate_backup(sites=self.site_url_list)
            self.sharepoint.verify_backup_job(job_id=multiple_sites_bkp,
                                              status_tab_expected_stats={
                                                  "Total": 2,
                                                  "Successful": 2
                                              })
        except Exception:
            raise CVTestStepFailure('Exception while verifying site level backup')

    @test_step
    def verify_single_page__backup(self):
        """Initiates single page backup job and verifies it"""
        try:
            # Single Page Backup, here the assumption is more than 15 webs are associated with the SharePoint app
            self.navigate_to_app_page()
            single_page_bkp = self.sharepoint.initiate_backup(page_option=1)
            self.sharepoint.verify_backup_job(job_id=single_page_bkp,
                                              status_tab_expected_stats={
                                                  "Total": 15,
                                                  "Successful": 15
                                              })
        except Exception:
            raise CVTestStepFailure('Exception while verifying single page backup')

    @test_step
    def verify_multi_page__backup(self):
        """Initiates all pages backup job and verifies it"""
        try:
            self.navigate_to_app_page()
            total_webs_in_backup = self.sharepoint.get_total_associated_sites_count()
            all_pages_bkp = self.sharepoint.initiate_backup(page_option=2)
            self.sharepoint.verify_backup_job(job_id=all_pages_bkp,
                                              status_tab_expected_stats={
                                                  "Total": total_webs_in_backup,
                                                  "Successful": total_webs_in_backup
                                              })
        except Exception:
            raise CVTestStepFailure('Exception while verifying all pages backup')

    @test_step
    def verify_disable_activity_control(self):
        """Verifies disable of backup by disabling activity control"""
        try:
            self.navigate_to_app_page()
            self.sharepoint.disable_activity_control_toggle()
            time.sleep(5)
            backupset_level_bkp = self.sharepoint.initiate_backup()
            job_details = self.sharepoint.get_job_details(backupset_level_bkp)
            if job_details:
                raise Exception('The backup did not fail to start as expected')
        except Exception:
            raise CVTestStepFailure('Exception while verifying disable activity control')

    def run(self):
        try:
            self.sharepoint.create_office365_app()
            self.sharepoint.wait_for_discovery_to_complete()
            total_webs_in_backup = self.sharepoint.add_user(users=self.sites, plan=self.tcinputs['Office365Plan'])
            self.verify_client_level_backup(total_webs_in_backup)
            self.verify_backupset_level_backup(total_webs_in_backup)
            self.verify_site_level_backup()
            # self.verify_single_page__backup()
            # self.verify_multi_page__backup()
            self.verify_disable_activity_control()
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_office365()
                self.sharepoint.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
