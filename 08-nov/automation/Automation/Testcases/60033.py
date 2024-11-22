# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for  SharePoint v2 Verification of Content Management

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans
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
        self.name = "SharePoint V2: Verification of Content Management - Sites Tab Manage Options"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.sharepoint = None
        self.sites = {}
        self.sites_url_list = []
        self.site = None
        self.o365_plan = None
        self.new_o365_plan = None
        self.plans_page = None
        self.new_site = None

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
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.plans_page = Plans(self.admin_console)
            self.sites = self.tcinputs['Sites']
            self.sites_url_list = list(self.sites.keys())
            self.o365_plan = self.tcinputs['Office365Plan']
            self.new_o365_plan = self.tcinputs['NewOffice365Plan']
            self.new_site = self.tcinputs['NewSite']
            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = SharePoint.AppType.share_point_online
            self.sharepoint = SharePoint(self.tcinputs, self.admin_console, is_react=True)
            self.sharepoint.create_office365_app()
            self.sharepoint.wait_for_discovery_to_complete()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @staticmethod
    def convert_date_job_format_to_site_page_format(job_date_str):
        """Method to convert date from job details format to the format as shown on Sites page"""
        split1 = job_date_str.split(",")
        datestr = split1[0]
        timesplit = split1[2].split(":", 3)[:2] + [split1[2].split()[-1]]
        final_timestr = f"{timesplit[0].strip()}:{timesplit[1].strip()} {timesplit[2][-2:].strip()}"
        return datestr + ", " + final_timestr

    @test_step
    def verify_associate_sites(self):
        """Associates sites and verifies whether sites and its subsites are associated correctly or not"""
        try:
            # Verify multiple sites association
            self.sharepoint.add_user(users=self.sites, plan=self.o365_plan)
            self.sharepoint.verify_added_users(users=self.sites_url_list)
            self.sharepoint.verify_plan_association(users=self.sites_url_list, plan=self.o365_plan)

            # Add 1 more site which has subsites, validate auto association of its subsites and verify o365 plan
            self.sharepoint.add_user(users={
                self.new_site['URL']: self.new_site['Title']
            },
                plan=self.new_o365_plan)

            sites_list = [self.new_site['URL']] + self.new_site['SubsitesUrlList']
            self.sharepoint.verify_added_users(users=sites_list)

            self.sharepoint.refresh_cache(wait_for_discovery_to_complete=True)
            self.sharepoint.verify_plan_association(users=sites_list, plan=self.new_o365_plan)
        except Exception:
            raise CVTestStepFailure('Exception while verifying association of sites')

    @test_step
    def verify_change_o365_plan(self):
        """Changes o365 plan for an associated site and verifies it"""
        try:
            # Change plan for 1 site and verify that plan is changed
            self.sharepoint.change_office365_plan(user=self.sites_url_list[0], plan=self.new_o365_plan)
            self.sharepoint.verify_plan_association(users=[self.sites_url_list[0]], plan=self.new_o365_plan)

            # Change plan for 1 root site and verify that plan is changed for its subsites too
            self.sharepoint.change_office365_plan(user=self.new_site['URL'], plan=self.o365_plan)

            self.sharepoint.refresh_cache(wait_for_discovery_to_complete=True)
            self.sharepoint.verify_plan_association(users=[self.new_site['URL']] + self.new_site['SubsitesUrlList'],
                                                    plan=self.o365_plan)
        except Exception:
            raise CVTestStepFailure('Exception while verifying change of o365 plan')

    @test_step
    def verify_disable_site(self):
        """Disables a site and verifies whether the site is disabled or not"""
        try:
            self.sharepoint.exclude_user(user=self.sites_url_list[0])
            self.sharepoint.verify_user_status(
                o365_constants.StatusTypes.DISABLED.value, self.sites_url_list[0])
        except Exception:
            raise CVTestStepFailure('Exception while verifying disable site')

    @test_step
    def verify_enable_site(self):
        """Enables a site and verifies whether the site is enabled or not"""
        try:
            self.sharepoint.include_in_backup(self.sites_url_list[0])
            self.sharepoint.verify_user_status(
                o365_constants.StatusTypes.ACTIVE.value, self.sites_url_list[0])
        except Exception:
            raise CVTestStepFailure('Exception while verifying enable site')

    @test_step
    def verify_remove_active_site_from_backup(self):
        """Disassociates an active site and verifies whether the site is removed or not"""
        try:
            self.sharepoint.remove_from_content(self.new_site['URL'])
            self.sharepoint.verify_user_status(
                o365_constants.StatusTypes.REMOVED.value, self.new_site['URL'])
        except Exception:
            raise CVTestStepFailure('Exception while verifying remove active content from backup')

    @test_step
    def verify_associating_removed_site(self):
        """Associates a disassociated site and verifies whether the site and its subsites are
        associated with new o365 plan or not"""
        try:
            # Associate removed site with new o365 plan and
            # verify that plan is overridden for earlier associated its subsites too
            self.sharepoint.add_user(users={
                self.new_site['URL']: self.new_site['Title']
            },
                plan=self.new_o365_plan)

            self.sharepoint.refresh_cache(wait_for_discovery_to_complete=True)
            sites_list = [self.new_site['URL']] + self.new_site['SubsitesUrlList']

            self.admin_console.access_tab(o365_constants.SharePointOnline.ACCOUNT_TAB.value)
            self.sharepoint.verify_added_users(users=[self.new_site['URL']])
            self.sharepoint.verify_plan_association(users=sites_list, plan=self.new_o365_plan)
        except Exception:
            raise CVTestStepFailure('Exception while verifying associating removed sites')

    @test_step
    def verify_remove_disabled_site_from_backup(self):
        """Disassociates a disabled site and verifies whether the site is removed or not"""
        try:
            self.sharepoint.exclude_user(self.sites_url_list[1])
            self.sharepoint.remove_from_content(self.sites_url_list[1])
            self.sharepoint.verify_user_status(
                o365_constants.StatusTypes.REMOVED.value, self.sites_url_list[1])
        except Exception:
            raise CVTestStepFailure('Exception while verifying remove disabled content from backup')

    @test_step
    def backup_and_verify_site_details(self):
        """Initiates backup at backupset level and verifies site details with input site details"""
        try:
            self.sharepoint.exclude_user(self.new_site['URL'])
            self.new_o365_plan = self.tcinputs['NewOffice365Plan2']
            self.sharepoint.change_office365_plan(user=self.new_site['SubsitesUrlList'][0], plan=self.new_o365_plan)
            validate_site_details = self.tcinputs['ValidateSiteDetails']
            backupset_level_bkp = self.sharepoint.initiate_backup()
            self.sharepoint.verify_backup_job(job_id=backupset_level_bkp,
                                              status_tab_expected_stats={
                                                  "Total": len(validate_site_details),
                                                  "Successful": len(validate_site_details)
                                              })
            latest_backup_job_start_time = self.convert_date_job_format_to_site_page_format(
                self.sharepoint.job_details['Start time'])
            for site in validate_site_details.keys():
                validate_site_details[site]['Last backup'] = latest_backup_job_start_time
            self.navigator.navigate_to_office365()
            self.sharepoint.access_office365_app(self.tcinputs['Name'])
            self.sharepoint.verify_site_details(expected_sites_details=validate_site_details)
        except Exception:
            raise CVTestStepFailure('Exception while verifying site details after backup')

    def run(self):
        try:
            self.verify_associate_sites()
            self.verify_change_o365_plan()
            self.verify_disable_site()
            self.verify_enable_site()
            self.verify_remove_active_site_from_backup()
            self.verify_associating_removed_site()
            self.verify_remove_disabled_site_from_backup()
            self.backup_and_verify_site_details()
            self.tcinputs['NewPlan'] += f'{int(time.time())}'
            self.sharepoint.change_plan()
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_office365()
                self.sharepoint.delete_office365_app(self.tcinputs['Name'])
                self.navigator.navigate_to_plan()
                self.plans_page.delete_plan(self.tcinputs['NewPlan'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
