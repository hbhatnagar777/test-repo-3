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

    run()           --  run function of this test case
"""

import time
import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """Admin Console: GDPR Schedules For Inventory Manager"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "GDPR Schedules For Inventory Manager"
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "IndexServerName": None,
            "NameServerAsset": None
        }
        # Test Case constants
        self.inventory_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.schedule_options = {}

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # Test Case constants
        self.inventory_name = f'{self.id}_inventory'

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def cleanup(self):
        """cleanup the testcase created entities"""
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name)

    @test_step
    def wait_for_asset_status_completion(self):
        """Wait for asset status completion"""
        if not self.gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete Asset Scan")

    @test_step
    def create_inventory_add_datasource(self):
        """create inventory and add datasource"""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])
        self.gdpr_obj.inventory_details_obj.add_asset_name_server(
            self.tcinputs['NameServerAsset'])

    @test_step
    def check_default_schedule(self):
        """Check if default schedule created"""
        if not self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                default_schedule=True):
            raise CVTestStepFailure("Default schedule not created")

    @test_step
    def remove_schedule(self):
        """Remove schedule"""
        self.gdpr_obj.inventory_details_obj.remove_schedule()
        if self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned():
            raise CVTestStepFailure("Schedule found even after removal")

    @test_step
    def add_one_time_schedule(self):
        """Add one time schedule"""
        self.schedule_options = {}
        self.schedule_options['frequency'] = 'One time'
        custom_time = datetime.datetime.now()
        custom_time += datetime.timedelta(minutes=10)
        self.schedule_options.update(self.gdpr_obj.get_schedule_datetime(frequency='One time',
                                     custom_time=custom_time))
        self.gdpr_obj.inventory_details_obj.add_edit_schedule(self.schedule_options)
        if not self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                schedule_options=self.schedule_options):
            raise CVTestStepFailure("One Time schedule not found")

    @test_step
    def verify_last_collection_time(self):
        """Verify last collection time"""
        last_collection_time = self.gdpr_obj.inventory_details_obj.get_last_collection_time(
            self.tcinputs['NameServerAsset'])
        self.schedule_options['schedule_time'] -= datetime.timedelta(minutes=2)
        self.gdpr_obj.verify_last_collection_time(last_collection_time, self.schedule_options)
        # Verify that one time schedule got deleted
        if self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned():
            raise CVTestStepFailure("Schedule found even after One time schedule ran")

    @test_step
    def add_weekly_schedule(self):
        """Add weekly schedule"""
        self.schedule_options = {}
        self.schedule_options['frequency'] = 'Weekly'
        self.schedule_options.update(self.gdpr_obj.get_schedule_datetime(frequency='Weekly'))
        self.gdpr_obj.inventory_details_obj.add_edit_schedule(self.schedule_options)
        if not self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                schedule_options=self.schedule_options):
            raise CVTestStepFailure("Weekly schedule not found")

    @test_step
    def edit_monthly_schedule(self):
        """Edit to monthly schedule"""
        self.schedule_options = {}
        self.schedule_options['frequency'] = 'Monthly'
        self.schedule_options.update(self.gdpr_obj.get_schedule_datetime(frequency='Monthly'))
        self.gdpr_obj.inventory_details_obj.add_edit_schedule(self.schedule_options)
        if not self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                schedule_options=self.schedule_options):
            raise CVTestStepFailure("Monthly schedule not found")

    @test_step
    def add_exception(self):
        """Adds exception to the existing schedule"""
        self.schedule_options.update(self.gdpr_obj.get_schedule_datetime(exceptions=True))
        self.gdpr_obj.inventory_details_obj.select_add_or_edit_schedule()
        self.gdpr_obj.inventory_details_obj.add_exception(self.schedule_options)
        if not self.gdpr_obj.inventory_details_obj.check_if_schedule_is_assigned(
                schedule_options=self.schedule_options):
            raise CVTestStepFailure("Exception not found")

    def run(self):
        """Main function for test case execution"""

        try:
            self.init_tc()
            self.cleanup()
            self.create_inventory_add_datasource()
            self.wait_for_asset_status_completion()
            self.check_default_schedule()
            self.remove_schedule()
            self.add_one_time_schedule()
            self.log.info("Sleeping for 15 mins")
            time.sleep(15*60)
            self.wait_for_asset_status_completion()
            self.verify_last_collection_time()
            self.add_weekly_schedule()
            self.edit_monthly_schedule()
            self.add_exception()
            self.remove_schedule()
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)