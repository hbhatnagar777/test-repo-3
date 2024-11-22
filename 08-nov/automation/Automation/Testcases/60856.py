# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import time

from AutomationUtils.cvtestcase import CVTestCase

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.inputs import (
     ListBoxController
)
from Reports.utils import TestCaseUtils
from Reports.Custom.utils import CustomReportUtils


class TestCase(CVTestCase):
    """
    Admin Console: Validate Backup job summary report custom report
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Admin Console: Validate Backup job summary job details"
        self.browser = None
        self.admin_console = None
        self.viewer = None
        self.utils = TestCaseUtils(self)
        self.table = None
        self.report = None
        self.job_obj = None
        self.child_app_size = None
        self.child_media_size = None

    def init_tc(self):
        """
        initialize adminconsole objects
        """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = webconsole
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            navigator = self.admin_console.navigator
            manage_report = ManageReport(self.admin_console)
            navigator.navigate_to_reports()
            manage_report.access_report("Backup job summary")
            self.viewer = viewer.CustomReportViewer(self.admin_console)
            self.table = viewer.DataTable("Job Details")
            self.viewer.associate_component(self.table)
            columns = ['Duration(mins)', 'Parent JobId']
            for column in columns:
                self.table.toggle_column_visibility(column)
        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    @test_step
    def run_backup(self):
        """ run backup and get job Id """
        self.job_obj = self.subclient.backup()
        time.sleep(10)
        self.admin_console.refresh_page()
        self.validate_end_time_and_duration()
        ret = self.job_obj.wait_for_completion()
        if ret is not True:
            raise CVTestStepFailure(f"Expected job status is completed but the current job status : {ret}")

    def get_child_vm_job_details(self):
        """get the chile VM job details"""
        custom_report_utils = CustomReportUtils(self)
        self.child_app_size = []
        self.child_media_size = []
        get_chile_jobs = self.table.get_column_data('Job ID')
        for each_job in get_chile_jobs:
            child_job_obj = self.commcell.job_controller.get(each_job)
            child_app_size = child_job_obj._get_job_summary()['sizeOfApplication']
            child_media_size = child_job_obj._get_job_summary()['sizeOfMediaOnDisk']
            converted_app_size = custom_report_utils.size_converter(child_app_size)
            converted_media_size = custom_report_utils.size_converter(child_media_size)
            self.child_app_size.append(converted_app_size)
            self.child_media_size.append(converted_media_size)
        return self.child_app_size, self.child_media_size

    @test_step
    def validate_app_media_details(self):
        """ validate the job details from the SDK with web report"""
        self.enable_report_input(select_filter=False)
        parent_job_id = self.job_obj.job_id
        self.table.set_filter('Parent JobId', parent_job_id)
        self.get_child_vm_job_details()
        web_app_size = self.table.get_column_data('Application Size')
        web_media_size = self.table.get_column_data('Media Size')
        if self.child_app_size != web_app_size and self.child_media_size != web_media_size:
            raise CVTestStepFailure(
                f"Expected application size is {self.child_app_size}"
                f"but received {web_app_size}Expected application size is "
                f"{self.child_media_size}but received {web_media_size}")

    @test_step
    def enable_report_input(self, select_filter=True):
        """ Enable the job status input and apply the status """
        drop_down = ListBoxController("Job status")
        self.viewer.associate_input(drop_down)
        drop_down.expand_input_controller()
        drop_down.select_all()
        if select_filter:
            drop_down.select_value("Running")
        drop_down.apply()

    def validate_end_time_and_duration(self):
        """
        Verify the end time and duration from report
        """
        duration = self.table.get_column_data('Duration(mins)')
        end_time = self.table.get_column_data('EndTime')
        if duration == -1 and end_time == -1:
            raise CVTestStepFailure(f"Expected duration is non-negative but received {duration},"
                                    f"Expected end_time is non-negative but received : {end_time}")

    def run(self):
        """ test case run method"""
        try:
            self.init_tc()
            self.enable_report_input()
            self.run_backup()
            self.validate_app_media_details()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
