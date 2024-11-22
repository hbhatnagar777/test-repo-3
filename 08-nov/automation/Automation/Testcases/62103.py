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
    __init__()              --  initialize TestCase class

    init_tc()               --  initializes all the variables needed for the testcase

    add_one_time_schedule   --  Add one time schedule

    add_weekly_schedule     --  Add weekly schedule

    edit_monthly_schedule   --  Edit to monthly schedule

    daily_schedule_with_exception   --  Adds daily schedule with exception

    remove_schedule         --  Remove schedule

    cleanup                 --  Cleanup the activate entities

    create_entities         --  Creates new activate entities

    check_no_default_schedule   --  Check if no default schedule got created

    open_plan_details_page      --  Opens DC plan details page

    open_data_source_details    --  Opens FS data source details page

    verify_crawl_job            --  Verifies if the last collection time is later than the schedule time

    run                         --  Main function for test case execution

"""

import time
import datetime
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils.constants import *
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of GDPR Feature based on Plan's schedule"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Activate : SDG FS Crawls based on Plan's schedule"
        self.show_to_user = False
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "IndexServerName": None,
            "AccessNode": None,
            "ContentAnalyzer": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "TestDataSQLiteDBPath": None
        }
        # Test Case constants
        self.one_time_schedule_time = None
        self.inventory_name = None
        self.plan_name = None
        self.entities_list = None
        self.project_name = None
        self.file_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.schedule_options = None
        self.gdpr_obj = None
        self.wait_time = None

    @test_step
    def init_tc(self):
        """Initializes testcase with all the parameters"""
        self.log.info("Started executing '%s' testcase" % str(self.id))
        self.inventory_name = '%s_inventory' % self.id
        self.plan_name = '%s_plan' % self.id
        self.entities_list = [
            ENTITY_CREDIT_CARD,
            ENTITY_SSN,
            ENTITY_EMAIL]
        self.wait_time = 5
        self.project_name = '%s_project' % self.id
        self.file_server_display_name = '%s_file_server' % self.id
        self.country_name = INDIA_COUNTRY_NAME
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                          username=self.tcinputs['UserName'],
                                          password=self.tcinputs['Password'])
        self.admin_console.login(username=self.tcinputs['UserName'],
                                 password=self.tcinputs['Password'])
        self.log.info("Login completed successfully.")
        self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
        self.gdpr_obj.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])
        self.gdpr_obj.testdata_path = self.tcinputs['FileServerDirectoryPath']
        self.gdpr_obj.entities_list = self.entities_list
        self.gdpr_obj.data_source_name = self.file_server_display_name

    @test_step
    def add_one_time_schedule(self):
        """Add one time schedule"""
        self.schedule_options = dict()
        self.schedule_options['frequency'] = 'One time'
        custom_time = datetime.datetime.now()
        custom_time += datetime.timedelta(minutes=self.wait_time)
        self.one_time_schedule_time = custom_time.timestamp()
        self.schedule_options.update(self.gdpr_obj.get_schedule_datetime(frequency='One time'),
                                     custom_time=custom_time)
        self.gdpr_obj.inventory_details_obj.add_edit_schedule(self.schedule_options)
        if not self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                schedule_options=self.schedule_options):
            raise CVTestStepFailure("One Time schedule not found")

    @test_step
    def add_weekly_schedule(self):
        """Add weekly schedule"""
        self.schedule_options = dict()
        self.schedule_options['frequency'] = 'Weekly'
        self.schedule_options.update(self.gdpr_obj.get_schedule_datetime(frequency='Weekly'))
        self.gdpr_obj.inventory_details_obj.add_edit_schedule(self.schedule_options)
        if not self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                schedule_options=self.schedule_options):
            raise CVTestStepFailure("Weekly schedule not found")

    @test_step
    def edit_monthly_schedule(self):
        """Edit to monthly schedule"""
        self.schedule_options = dict()
        self.schedule_options['frequency'] = 'Monthly'
        self.schedule_options.update(self.gdpr_obj.get_schedule_datetime(frequency='Monthly'))
        self.gdpr_obj.inventory_details_obj.add_edit_schedule(self.schedule_options)
        if not self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                schedule_options=self.schedule_options):
            raise CVTestStepFailure("Monthly schedule not found")

    @test_step
    def daily_schedule_with_exception(self):
        """Adds daily schedule with exception"""
        self.schedule_options = dict()
        self.schedule_options['frequency'] = 'Daily'
        self.schedule_options.update(self.gdpr_obj.get_schedule_datetime(
            frequency='Daily', exceptions=True))
        self.gdpr_obj.inventory_details_obj.add_edit_schedule(self.schedule_options)
        if not self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                schedule_options=self.schedule_options):
            raise CVTestStepFailure("Daily schedule not found")

    @test_step
    def remove_schedule(self):
        """Remove schedule"""
        self.gdpr_obj.inventory_details_obj.remove_schedule()
        if self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned():
            raise CVTestStepFailure("Schedule found even after removal")

    @test_step
    def cleanup(self):
        """Cleanup the activate entities"""
        self.gdpr_obj.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name,
            pseudo_client_name=self.file_server_display_name)

    @test_step
    def create_entities(self):
        """Creates new activate entities"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])
        self.gdpr_obj.inventory_details_obj.add_asset_name_server(
            self.tcinputs['NameServerAsset'])
        if not self.gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise Exception("Could not complete Asset Scan")
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
            self.tcinputs['ContentAnalyzer'], self.entities_list)
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source()
        self.gdpr_obj.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], 'Host name',
            self.file_server_display_name, self.country_name,
            self.tcinputs['FileServerDirectoryPath'],
            username = self.tcinputs['FileServerUserName'],
            password = self.tcinputs['FileServerPassword'],
            access_node=self.tcinputs['AccessNode'],
            inventory_name = self.inventory_name)
        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete Data Source Scan")
        self.log.info(f"Sleeping for: {self.wait_time} minutes")
        time.sleep(self.wait_time*60)

    @test_step
    def check_no_default_schedule(self):
        """Check if no default schedule got created"""
        if self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                default_schedule=True):
            raise CVTestStepFailure("Default or some other schedule assigned")

    @test_step
    def open_plan_details_page(self):
        """Opens DC plan details page"""
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.select_plan(self.plan_name)

    @test_step
    def open_data_source_details(self):
        """Opens FS data source details page"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.navigate_to_project_details(self.project_name)
        self.gdpr_obj.file_server_lookup_obj.select_data_source(self.file_server_display_name)
        self.log.info(f"Sleeping for: {self.wait_time} minutes")
        time.sleep(self.wait_time*60)

    def verify_crawl_job(self):
        """Verifies if the last collection time is later than the schedule time"""
        crawl_time = self.gdpr_obj.file_server_lookup_obj.__table.get_column_data['Last analyzed'][0]
        crawl_time_stamp = datetime.datetime.strptime(crawl_time, "%m/%d/%y %I:%M %p").timestamp()
        if crawl_time_stamp <= self.one_time_schedule_time:
            self.log.info("Crawl was not invoked on the given schedule")
            raise Exception("Crawl was not invoked on the given schedule")
        self.log.info(f"Crawl was invoked on the given schedule on {crawl_time}")

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.cleanup()
            self.create_entities()
            self.open_plan_details_page()
            self.check_no_default_schedule()
            self.add_one_time_schedule()
            self.open_data_source_details()
            self.log.info(f"Sleeping for {self.wait_time} minutes.")
            time.sleep(self.wait_time*60)
            self.admin_console.refresh_page()
            self.verify_crawl_job()
            self.open_plan_details_page()
            self.check_no_default_schedule()
            self.add_weekly_schedule()
            self.edit_monthly_schedule()
            self.daily_schedule_with_exception()
            self.remove_schedule()
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
