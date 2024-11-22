# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for verification of all restore options

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
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.sharepoint import SharePoint
from Web.AdminConsole.Office365Pages import constants as o365_constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "SharePoint V2 Web Automation: Verification of restore - all options"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.sharepoint = None
        self.jobs = None
        self.sites = {}
        self.site_url_list = []
        self.site = None
        self.full_bkp_start_time = None

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
            self.sites = self.tcinputs['Sites']
            self.site_url_list = list(self.sites.keys())
            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = SharePoint.AppType.share_point_online
            self.sharepoint = SharePoint(self.tcinputs, self.admin_console, is_react=True)
            self.sharepoint.create_office365_app()
            self.sharepoint.wait_for_discovery_to_complete()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def navigate_to_app_page(self):
        """Navigates to SharePoint app page"""
        self.navigator.navigate_to_office365()
        self.sharepoint.access_office365_app(self.tcinputs['Name'])

    @test_step
    def associate_sites_and_run_backup(self):
        """Associates sites and runs backup"""
        try:
            self.sharepoint.add_user(users=self.sites)
            backupset_level_bkp = self.sharepoint.initiate_backup()
            self.sharepoint.verify_backup_job(job_id=backupset_level_bkp)
            self.full_bkp_start_time = self.sharepoint.job_details['Start time']
            self.navigate_to_app_page()
            incremental_backupset_level_bkp = self.sharepoint.initiate_backup()
            self.sharepoint.verify_backup_job(job_id=incremental_backupset_level_bkp)
        except Exception:
            raise CVTestStepFailure('Exception while associating sites or running backup')

    def _validate_restore_failure(self, job_details):
        """Checks if there were any failures in the restore

            Args:

                job_details (dict)      :   Dict containing items from job details page

        """
        failures = job_details['Failures']
        if failures != '0 Folders, 0 Files':
            raise Exception(f'Failures in restore job: {failures}')

    @test_step
    def verify_skip_restore(self):
        """Opens browse page from office 365 apps page,initiates restore job with skip option
        and verifies restore job completion"""
        try:
            self.navigator.navigate_to_office365()
            self.sharepoint.click_client_level_restore(self.tcinputs['Name'])
            self.sharepoint.browse_items_for_restore(self.tcinputs['SearchKeywords'][0])
            job_details = self.sharepoint.run_restore(
                destination=o365_constants.RestoreType.IN_PLACE)

            to_be_restored = int(job_details['To be restored'])
            skipped_files = int(job_details['Skipped files'])
            if abs(to_be_restored - skipped_files) > 10 or skipped_files == 0:
                raise Exception(f"Too few files skipped: {skipped_files} for {to_be_restored - skipped_files} files")

            files_restored = int(job_details['No of files restored'])
            if files_restored > 10:
                raise Exception(f"Too many files restored: {files_restored}")

            self._validate_restore_failure(job_details)
        except Exception as e:
            raise CVTestStepFailure(f'Exception while verifying client level restore with skip option: {e}')

    @test_step
    def verify_unconditional_overwrite_restore(self):
        """Clicks on the app in apps page, initiates restore job with unconditional overwrite option
         and verifies restore job completion"""
        try:
            self.navigate_to_app_page()
            self.admin_console.access_tab(o365_constants.SharePointOnline.OVERVIEW_TAB.value)
            self.sharepoint.click_point_in_time_browse(restore_time=self.full_bkp_start_time)
            self.sharepoint.browse_items_for_restore(self.tcinputs['SearchKeywords'][0])
            job_details = self.sharepoint.run_restore(
                destination=o365_constants.RestoreType.IN_PLACE, file_option='Unconditionally overwrite')

            skipped_files = int(job_details['Skipped files'])
            restored_files = int(job_details['No of files restored'])
            if restored_files < 10 and skipped_files != 0:
                raise Exception(f"Too many files were skipped: {skipped_files} for {restored_files} files")

            if int(job_details['No of files restored']) == 0:
                raise Exception(f'No files were restored')

            self._validate_restore_failure(job_details)
        except Exception as e:
            raise CVTestStepFailure(f'Exception while verifying PIT restore with unconditional overwrite option: {e}')

    @test_step
    def verify_workflows_only_restore(self):
        """Clicks on restore of app page, initiates restore job with workflows only option
         and verifies restore job completion"""
        try:
            self.navigate_to_app_page()
            self.admin_console.access_tab(o365_constants.SharePointOnline.ACCOUNT_TAB.value)
            self.sharepoint.click_backupset_level_restore()
            self.sharepoint.browse_items_for_restore(self.tcinputs['SearchKeywords'][0])
            job_details = self.sharepoint.run_restore(
                destination=o365_constants.RestoreType.IN_PLACE, file_option='Unconditionally overwrite',
                advanced_option=self.admin_console.props['sp.offline.restore.workflowAndAlert'])

            skipped_files = int(job_details['Skipped files'])
            restored_files = int(job_details['No of files restored'])
            if restored_files < 10 and skipped_files != 0:
                raise Exception(f"Too many files were skipped: {skipped_files} for {restored_files} files")

            if int(job_details['No of files restored']) == 0:
                raise Exception(f'No files were restored')

            self._validate_restore_failure(job_details)
        except Exception as e:
            raise CVTestStepFailure(f'Exception while verifying backupset level restore only workflows: {e}')

    @test_step
    def verify_disk_as_original_files_restore(self):
        """Selects a single site, searches for a document, initiates disk restore as original files job
        and verifies restore job completion"""
        try:
            self.navigate_to_app_page()
            self.admin_console.access_tab(o365_constants.SharePointOnline.ACCOUNT_TAB.value)
            self.sharepoint.click_site_level_restore(sites=self.site_url_list[-1:])
            self.sharepoint.browse_items_for_restore(self.tcinputs['SearchKeywords'][0])
            job_details = self.sharepoint.run_restore(
                destination=o365_constants.RestoreType.TO_DISK,
                file_server=self.tcinputs['FileServer'],
                dest_path=self.tcinputs['DestPath'])

            skipped_files = int(job_details['Skipped files'])
            restored_files = int(job_details['No of files restored'])
            if restored_files < 10 and skipped_files != 0:
                raise Exception(f"Too many files were skipped: {skipped_files} for {restored_files} files")

            self._validate_restore_failure(job_details)
        except Exception as e:
            raise CVTestStepFailure(f'Exception while verifying restore to disk as original files: {e}')

    @test_step
    def verify_OOP_restore(self):
        """Selects a single site, searches for a document,
        initiates OOP restore job for a file/list and verifies restore job completion"""
        try:
            self.navigate_to_app_page()
            self.admin_console.access_tab(o365_constants.SharePointOnline.ACCOUNT_TAB.value)
            self.sharepoint.click_site_level_restore(sites=self.site_url_list[-1:])
            self.sharepoint.browse_items_for_restore(self.tcinputs['SearchKeywords'][0])
            job_details = self.sharepoint.run_restore(
                destination=o365_constants.RestoreType.OOP,
                oop_site=self.tcinputs['OOPSite'])

            skipped_files = int(job_details['Skipped files'])
            restored_files = int(job_details['No of files restored'])
            if restored_files < 10 and skipped_files != 0:
                raise Exception(f"Too many files were skipped: {skipped_files} for {restored_files} files")

            if int(job_details['No of files restored']) == 0:
                raise Exception(f'No files were restored')

            self._validate_restore_failure(job_details)
        except Exception as e:
            raise CVTestStepFailure(f'Exception while verifying OOP restore: {e}')

    @test_step
    def verify_restore_acls_only_restore(self):
        """Selects multiple sites, initiates restore ACLS only job  and verifies restore job completion"""
        try:
            self.navigate_to_app_page()
            self.admin_console.access_tab(o365_constants.SharePointOnline.ACCOUNT_TAB.value)
            self.sharepoint.click_site_level_restore(sites=self.site_url_list, site_restore=True)
            job_details = self.sharepoint.run_restore(
                destination=o365_constants.RestoreType.IN_PLACE,
                advanced_option=self.admin_console.props['sp.offline.restore.acls'])

            self._validate_restore_failure(job_details)
        except Exception as e:
            raise CVTestStepFailure(f'Exception while verifying restore acls only: {e}')

    def run(self):
        try:
            self.associate_sites_and_run_backup()
            self.verify_skip_restore()
            self.verify_unconditional_overwrite_restore()
            self.verify_workflows_only_restore()
            self.verify_disk_as_original_files_restore()
            self.verify_OOP_restore()
            self.verify_restore_acls_only_restore()
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
