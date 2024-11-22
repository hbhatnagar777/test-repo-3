# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.inputs import (
    ListBoxController, DateRangeController
)
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Admin Console: Validate Backup job summary report filters
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Admin Console: Validate Backup job summary report job status filters"
        self.browser = None
        self.admin_console = None
        self.webconsole: WebConsole = None
        self.viewer = None
        self.utils = TestCaseUtils(self)
        self.table = None
        self.job_status = None

    def init_tc(self):
        """
        initialize adminconsole objects
        """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
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
            columns = ['MediaAgent', 'Storage Policy']
            for column in columns:
                self.table.toggle_column_visibility(column)
            input_ctrl = DateRangeController("Time frame")
            self.viewer.associate_input(input_ctrl)
            input_ctrl.expand_input_controller()
            time_range_options = input_ctrl.get_available_options()
            input_ctrl.set_relative_daterange(time_range_options[1])  # run report for last 7 days
            self.job_status = {'Running': ['in progress', 'running'],
                               'Completed': 'completed', 'Failed': 'failed',
                               'No Run': ['no run', 'skipped', 'skipped by user', 'suspended'],
                               'Killed': ['killed', 'kill pending'],
                               'Delayed': ['delayed', 'waiting', 'pending'],
                               'Completed with Errors': ['partial success', 'completed with errors']}

        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    def get_chart_data(self):
        """
        get the list or legend text and values
        Returns: legend test and legend values
        """
        pie_chart = viewer.PieChart('Job status')
        self.viewer.associate_component(pie_chart)
        legend_text, legend_values = pie_chart.get_chart_legend()
        return legend_text, legend_values

    def get_summary_job_count(self):
        """
        get the summary job count
        Returns: list
        """
        s_viewer = viewer.CustomReportViewer(self.admin_console)
        sum_table = viewer.DataTable("Summary")
        s_viewer.associate_component(sum_table)
        return [int(i) for i in sum_table.get_column_data('Total Jobs')]

    def enable_report_input(self, job_status=None):
        """ Enable the job status input and apply the status """
        drop_down = ListBoxController("Job status")
        self.viewer.associate_input(drop_down)
        if job_status is None:
            drop_down.select_all()
            drop_down.apply()
        else:
            drop_down.select_all()
            drop_down.select_value(job_status)
            drop_down.apply()

    @test_step
    def validate_running_job_status(self):
        """
        Filter the running job status form input and validate the summary and detail tables.
        """
        self.enable_report_input(list(self.job_status.keys())[0])
        legend_text, legend_values = self.get_chart_data()
        if legend_text != [] and legend_values != []:
            job_status = self.job_status['Running']
            for each_legend in legend_values:
                each_legend = each_legend.split(':')[0]
                if each_legend.lower() not in job_status:
                    raise CVTestStepFailure(f"Expected job status is {job_status} "
                                            f"but received status is {each_legend}")
            running_jobs_chart = sum(map(int, legend_text))
            summary_job_Count = sum(self.get_summary_job_count())
            table_row_count = self.table.get_pagination()
            # verify chart, summary and job details table job counts are matching
            if table_row_count != running_jobs_chart or summary_job_Count != running_jobs_chart:
                raise CVTestStepFailure(f"Expected job count is {running_jobs_chart} but received {table_row_count}"
                                    f"Expected job count from summary {running_jobs_chart} "
                                    f"but received {summary_job_Count}")
            if running_jobs_chart != 0 and summary_job_Count != 0 and table_row_count != 0:
                table_dic = self.table.get_table_data()
                table_dic.pop('Failure Reason')
                # verify all the rows are having valid data and job status is only Running
                for key, val in table_dic.items():
                    if val == '' and table_dic.get('Job status') not in job_status:
                        raise CVTestStepFailure(f"Expected the non- zero values but "
                                                f"received {key} : {val} and expected job status is completed"
                                                f"but received {table_dic.get('Job status')}")
        self.enable_report_input()

    @test_step
    def validate_completed_job_status(self):
        """
         Filter the completed job status from input and validate the summary and details tables
        """
        self.enable_report_input(list(self.job_status.keys())[1])
        legend_text, legend_values = self.get_chart_data()
        if legend_text != [] and legend_values != []:
            job_status = self.job_status['Completed']
            for each_legend in legend_values:
                each_legend = each_legend.split(':')[0]
                if each_legend.lower() not in job_status:
                    raise CVTestStepFailure(f"Expected job status is {job_status} "
                                        f"but received status is {each_legend}")
            completed_jobs = sum(map(int, legend_text))
            # verify chart, summary and job details table job counts are matching
            summary_job_Count = sum(self.get_summary_job_count())
            table_row_count = self.table.get_pagination()
            if table_row_count != completed_jobs or summary_job_Count != completed_jobs:
                raise CVTestStepFailure(f"Expected job count is {completed_jobs} but received {table_row_count}"
                                        f"Expected job count from summary {completed_jobs} "
                                        f"but received {summary_job_Count}")
            table_dic = self.table.get_table_data()
            table_dic.pop('Failure Reason')
            # verify all the rows are having valid data and job status is only completed
            for key, val in table_dic.items():
                if val == '' and table_dic.get('Job status') not in job_status:
                    raise CVTestStepFailure(f"Expected the non- zero values but"
                                        f"received {key} : {val} and expected job status is completed "
                                            f"but received {table_dic.get('Job status')}")
        self.enable_report_input()

    @test_step
    def validate_failed_job_status(self):
        """
        Filter the failed job status from input and validate the summary and details tables.
        """
        self.enable_report_input(list(self.job_status.keys())[2])
        legend_text, legend_values = self.get_chart_data()
        if legend_text != [] and legend_values != []:
            job_status = self.job_status['Failed']
            for each_legend in legend_values:
                each_legend = each_legend.split(':')[0]
                if each_legend.lower() not in job_status:
                    raise CVTestStepFailure(f"Expected job status is {self.job_status['Failed']} "
                                        f"but received status is {each_legend}")
        failed_jobs = int(legend_text[0])
        # verify chart, summary and job details table job counts are matching
        summary_job_Count = sum(self.get_summary_job_count())
        table_row_count = self.table.get_pagination()
        if self.table.get_pagination() != failed_jobs or summary_job_Count != failed_jobs:
            raise CVTestStepFailure(f"Expected job count is {failed_jobs} but received {table_row_count}"
                                f"Expected job count from summary {failed_jobs} but received {summary_job_Count}")
        failed_reason = self.table.get_column_data('Failure Reason')
        if failed_reason == ' ':
            raise CVTestStepFailure("Expected to have a failure reason but receive it blank")
        for each_job_state in self.table.get_column_data('Job status'):
            if each_job_state.lower() not in job_status:
                raise CVTestStepFailure(f"Excepted job status in details table is {each_job_state} "
                                        f"but received {job_status}")
        self.enable_report_input()

    @test_step
    def validate_no_run_job_status(self):
        """
        Filter the no run job status from input and validate the summary and details tables.
        """
        self.enable_report_input(list(self.job_status.keys())[3])
        legend_text, legend_values = self.get_chart_data()
        if legend_text != [] and legend_values != []:
            job_status = self.job_status['No Run']
            for each_legend in legend_values:
                each_legend = each_legend.split(':')[0]
                if each_legend.lower() not in job_status:
                    raise CVTestStepFailure(f"Expected job status is {self.job_status['No Run']} "
                                        f"but received status is {each_legend.lower}")
        no_run_jobs = sum(map(int, legend_text))
        # verify chart, summary and job details table job counts are matching
        summary_job_count = sum(self.get_summary_job_count())
        table_row_count = self.table.get_pagination()

        if table_row_count != no_run_jobs or summary_job_count != no_run_jobs:
            raise CVTestStepFailure(f"Expected job count is {no_run_jobs} but received {table_row_count}"
                                    f"Expected job count from summary {no_run_jobs} "
                                    f"but received {summary_job_count}")
        failed_reason = self.table.get_column_data('Failure Reason')
        if failed_reason == ' ':
            raise CVTestStepFailure(f"Expected to have a failure reason but receive it blank {failed_reason} "
                                    f"and Expected job status is no run "
                                    f"but received {self.table.get_column_data('Job status')}")
        for each_job_state in self.table.get_column_data('Job status'):
            if each_job_state.lower() not in job_status:
                raise CVTestStepFailure(f"Excepted job status is {each_job_state.lower()} but received {job_status}")
        self.enable_report_input()

    @test_step
    def validate_killed_job_status(self):
        """
        Filter the killed job status from input and validate the summary and details tables.
        """
        self.enable_report_input(list(self.job_status.keys())[4])
        legend_text, legend_values = self.get_chart_data()
        if legend_text != [] and legend_values != []:
            job_status = self.job_status['Killed']
            for each_legend in legend_values:
                each_legend = each_legend.split(':')[0]
                if each_legend.lower() not in job_status:
                    raise CVTestStepFailure(f"Expected job status is {job_status} "
                                            f"but received status is {each_legend.lower()}")
            killed_jobs = int(legend_text[0])
            # verify chart, summary and job details table job counts are matching
            summary_job_count = sum(self.get_summary_job_count())
            table_row_count = self.table.get_pagination()
            if table_row_count != killed_jobs or summary_job_count != killed_jobs:
                raise CVTestStepFailure(f"Expected job count is {killed_jobs} but received {table_row_count}"
                                    f"Expected job count from summary {killed_jobs} but received {summary_job_count}")
            failed_reason = self.table.get_column_data('Failure Reason')
            if failed_reason == ' ':
                raise CVTestStepFailure(f"Expected to have a failure reason but receive it blank {failed_reason} "
                                    f"and Expected job status is no run "
                                    f"but received {self.table.get_column_data('Job status')}")
            for each_job_state in self.table.get_column_data('Job status'):
                if each_job_state.lower() not in job_status:
                    raise CVTestStepFailure(f"Excepted job status is {each_job_state.lower()} "
                                            f"but received {job_status}")
        self.enable_report_input()

    @test_step
    def validate_delayed_job_status(self):
        """
        Filter the delayed job status from input and validate the summary and details tables.
        """
        self.enable_report_input(list(self.job_status.keys())[5])
        legend_text, legend_values = self.get_chart_data()
        job_status = self.job_status['Delayed']
        if legend_text != [] and legend_values != []:
            for each_legend in legend_values:
                each_legend = each_legend.split(':')[0]
                if each_legend.lower() not in job_status:
                    raise CVTestStepFailure(f"Expected job status is {job_status} "
                                        f"but received status is {each_legend.lower()}")
            delayed_jobs = sum(map(int, legend_text))
            # verify chart, summary and job details table job counts are matching
            summary_job_count = sum(self.get_summary_job_count())
            table_row_count = self.table.get_pagination()
            if table_row_count != delayed_jobs or summary_job_count != delayed_jobs:
                raise CVTestStepFailure(f"Expected job count is {delayed_jobs} but received {table_row_count}"
                                    f"Expected job count from summary {delayed_jobs} "
                                    f"but received {summary_job_count}")
            failed_reason = self.table.get_column_data('Failure Reason')
            if failed_reason == ' ':
                raise CVTestStepFailure(f"Expected to have a failure reason but receive it blank {failed_reason} "
                                    f"and Expected job status is no run "
                                    f"but received {self.table.get_column_data('Job status')}")
            for each_job_state in self.table.get_column_data('Job status'):
                if each_job_state.lower() not in job_status:
                    raise CVTestStepFailure(
                        f"Excepted job status is {each_job_state.lower()} but received {job_status}")
        self.enable_report_input()

    @test_step
    def validate_cwe_job_status(self):
        """
        Filter by cwe job status from the input and verify the summary and details tables
        """
        self.enable_report_input(list(self.job_status.keys())[6])
        legend_text, legend_values = self.get_chart_data()
        if legend_text != [] and legend_values != []:
            job_status = self.job_status['Completed with Errors']
            for each_legend in legend_values:
                each_legend = each_legend.split(':')[0]
                if each_legend.lower() not in job_status:
                    raise CVTestStepFailure(f"Expected job status is {self.job_status['Completed with Errors']} "
                                        f"but received status is {each_legend.lower()}")
            cwe_jobs = sum(map(int, legend_text))
            # verify chart, summary and job details table job counts are matching
            summary_job_count = sum(self.get_summary_job_count())
            table_row_count = self.table.get_pagination()
            if table_row_count != cwe_jobs or summary_job_count != cwe_jobs:
                raise CVTestStepFailure(f"Expected job count is {cwe_jobs} but received {table_row_count}"
                                     f"Expected job count from summary {cwe_jobs} but received {summary_job_count}")
            failed_reason = self.table.get_column_data('Failure Reason')
            if failed_reason == ' ':
                raise CVTestStepFailure(f"Expected to have a failure reason but receive it blank")
            for each_job_state in self.table.get_column_data('Job status'):
                if each_job_state.lower() not in job_status:
                    raise CVTestStepFailure(f"Excepted job status is {each_job_state.lower()} "
                                            f"but received {job_status}")
        self.enable_report_input()

    def run(self):
        """ test case run method"""
        try:
            self.init_tc()
            self.validate_running_job_status()
            self.validate_completed_job_status()
            self.validate_failed_job_status()
            self.validate_killed_job_status()
            self.validate_delayed_job_status()
            self.validate_no_run_job_status()
            self.validate_cwe_job_status()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
