# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics and custom report Schedule - Acceptance """
import time

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.WebConsole.Reports import cte
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.manage_schedules import ScheduleSettings
from Web.WebConsole.Reports.cte import ConfigureAlert
from Web.WebConsole.Reports.Metrics.commcellgroup import CommcellGroup
from Web.WebConsole.Reports.manage_alerts import AlertSettings
from Web.WebConsole.Reports.Custom import viewer

from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports.Custom.report_templates import DefaultReport

CONSTANTS = config.get_config()
Format = cte.ConfigureSchedules.Format


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Web Security testing on reports"
        self.show_to_user = False
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.report = None
        self.recipient_id = CONSTANTS.email.email_id
        self.schedule_window = None
        self.alert_window = None
        self.schedules_list = []
        self.alerts_list = []
        self.custom_report_table = None
        self.schedule_settings = None
        self.alert_settings = None
        self.custom_report_name = self.name
        self.metrics_report_name = "Strike Count"
        self.dashboard_report = "Worldwide Dashboard"
        self.commcell_group_name = "Automated_group_50589"
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            if not self.recipient_id:
                raise CVTestCaseInitFailure("Recipient's id is not specified in config file")

            # open browser
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
            self.browser.open()

            # login to web console
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login()
            self.webconsole.goto_commcell_dashboard()
            self.navigator = Navigator(self.webconsole)
            self.report = MetricsReport(self.webconsole)
            self.utils.webconsole = self.webconsole
            self.schedule_settings = ScheduleSettings(self.webconsole)
            self.alert_settings = AlertSettings(self.webconsole)
            self.alert_window = ConfigureAlert(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup_schedules(self):
        """ Deletes the schedules which contain 'Schedule_50589_' in schedule name """
        self.navigator.goto_schedules_configuration()
        self.schedule_settings.cleanup_schedules("Schedule_50589_")

    def cleanup_alerts(self):
        """ Deletes the alert which contain 'Alert_tc_50589' in alert name """
        self.navigator.goto_alerts_configuration()
        self.alert_settings.cleanup_alerts("Alert_tc_50589")

    def redirect_to_reports_page(self, report_name):
        """Redirect to report's page"""
        if report_name == 'Worldwide Dashboard':
            self.navigator.goto_worldwide_dashboard()
        elif report_name == self.name:
            # create custom report if it does not exist and open it
            _viewer = viewer.CustomReportViewer(self.webconsole)
            DefaultReport(self.utils).build_default_report(overwrite=False)
            self.custom_report_table = viewer.DataTable("Automation Table")
            _viewer.associate_component(self.custom_report_table)
        else:
            self.navigator.goto_worldwide_report(report_name)

    def _create_metrics_report_alert(self):
        """Create metrics report alert"""
        table = self.report.get_tables()[0]
        column_name = table.get_visible_column_names()[0]
        condition_string = table.get_data_from_column(column_name)[0]
        self.log.info("Creating alert for [%s] report for [%s] column with condition string:"
                      "[%s]", self.metrics_report_name, column_name, condition_string)
        alert_name = "Alert_tc_50589_%s" % str(int(time.time()))
        self.alert_window = table.open_alert()
        self.alert_window.set_time(hour="6", minute="30")
        self.alert_window.create_alert(alert_name=alert_name, column_name=column_name,
                                       column_value=condition_string)
        self.log.info("Alert [%s] created successfully on [%s] report ", alert_name,
                      self.metrics_report_name)
        self.alerts_list.append(alert_name)

    def _create_custom_report_alert(self):
        """Create custom report alert"""
        data = self.custom_report_table.get_table_data()
        column_name = list(data)[0]
        if not data[column_name]:
            raise CVTestStepFailure("Report [%s] might be empty. Please verify!" %
                                    self.custom_report_name)
        condition_string = data[column_name][0]
        self.log.info("Creating alert for [%s] report for [%s] column with condition string:"
                      "[%s]", self.custom_report_name, column_name, condition_string)
        self.custom_report_table.configure_alert()
        self.alert_window.set_time(hour="6", minute="30")
        alert_name = "Alert_50589_%s" % str(int(time.time()))
        self.alert_window.create_alert(alert_name=alert_name, column_name=column_name,
                                       column_value=condition_string)
        self.log.info("Alert [%s] created successfully on [%s] report ", alert_name,
                      self.custom_report_name)
        self.alerts_list.append(alert_name)

    def _access_schedule_pages(self, report_name):
        """# Create Schedules in custom and metrics reports #"""
        for each_file_format in [Format.PDF, Format.HTML, Format.CSV]:
            if report_name == "Worldwide Dashboard" and each_file_format == Format.CSV:
                continue  # csv schedule for worldwide dashboard is not supported.
            schedule_window = self.report.open_schedule()
            self.log.info("Creating schedule for the [%s] report with [%s] file format",
                          report_name, each_file_format)
            schedule_name = "Schedule_50589_%s_%s" % \
                            (each_file_format, str(int(time.time())))
            schedule_window.set_schedule_name(schedule_name)
            schedule_window.set_recipient(self.recipient_id)
            schedule_window.select_format(each_file_format)
            schedule_window.save()
            self.schedules_list.append(schedule_name)
            self.log.info("Schedule created for the [%s] report with [%s] file format",
                          report_name, each_file_format)
        self.log.info("Schedule created successfully for the report [%s]", report_name)

    @test_step
    def _access_page_level_export_option(self, report_name):
        """# Access page level export #"""
        self.utils.reset_temp_dir()
        self.log.info("Page level export for the report %s", report_name)
        _export = self.report.export_handler()
        _export.to_pdf()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.wait_for_file_to_download('pdf')

        _export.to_html()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.wait_for_file_to_download('html')
        self.log.info("Page level export completed for the report %s", report_name)

        if report_name == self.dashboard_report:
            self.log.info("In dashboard page, csv export doesn't exists. so skipping it")
            return
        _export.to_csv()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.wait_for_file_to_download('csv')

    def _metrics_table_level_export(self):
        """Trigger metrics report's table level export"""
        self.utils.reset_temp_dir()
        _table_objs = self.report.get_tables()
        if not _table_objs:
            raise CVTestStepFailure("No tables are found in report [%s] for csv export"
                                    % self.metrics_report_name)
        _table_index = None
        for each_table_obj in _table_objs:
            if each_table_obj.is_csv_export_exists:
                each_table_obj.csv_export()  # click on 1st csv export of table
                # collect table index on which export is clicked
                _table_index = _table_objs.index(each_table_obj)
                break
        if _table_index is None:
            raise CVTestStepFailure("No table level csv exports are found in report [%s]"
                                    % self.metrics_report_name)
        _file_name = self.utils.poll_for_tmp_files(ends_with="csv", min_size=40)[0]
        self.log.info("Table level export csv [%s] file is downloaded for the report [%s]",
                      _file_name, self.metrics_report_name)

    def _custom_report_table_level_export(self):
        """Trigger custom report's table level export"""
        self.log.info("Triggering table level export for [%s] report", self.custom_report_name)
        self.utils.reset_temp_dir()
        self.custom_report_table.export_to_csv()
        _file_name = self.utils.poll_for_tmp_files(ends_with="csv")[0]
        self.log.info("Table level export completed for [%s] report", self.custom_report_name)

    def _access_email_now_option(self, report_name):
        """# Access email now option #"""
        self.log.info("Accessing email now option for [%s] report", report_name)
        for each_file_type in [Format.PDF, Format.HTML, Format.CSV]:
            if report_name == "Worldwide Dashboard" and each_file_type == Format.CSV:
                continue
            self.log.info(" ## Performing EmailNow for the report [%s], with file format [%s]",
                          report_name, each_file_type)
            # for Worldwide Dashboard csv file email option is not available.
            # so this is skipped.
            self.webconsole.clear_all_notifications()
            email_window = self.report.open_email_now()
            email_window.email_now(each_file_type, self.recipient_id)
            self.log.info(" ## Email is done for the report [%s], with file format [%s]",
                          report_name, each_file_type)
        self.log.info("Email now option is accessed for [%s] report", report_name)

    @test_step
    def access_custom_report_cte(self):
        """Access custom report cte options"""
        self.redirect_to_reports_page(self.custom_report_name)
        self._access_page_level_export_option(self.custom_report_name)
        self._custom_report_table_level_export()
        self._access_email_now_option(self.custom_report_name)
        self._access_schedule_pages(self.custom_report_name)
        self._create_custom_report_alert()

    @test_step
    def access_metrics_report_cte(self):
        """Access metrics report cte options"""
        self.redirect_to_reports_page(self.metrics_report_name)
        self._access_page_level_export_option(self.custom_report_name)
        self._metrics_table_level_export()
        self._access_email_now_option(self.metrics_report_name)
        self._access_schedule_pages(self.metrics_report_name)
        self._create_metrics_report_alert()

    @test_step
    def access_dashboard_cte(self):
        """Access dashboard CTE options"""
        self.redirect_to_reports_page(self.dashboard_report)
        self._access_page_level_export_option(self.dashboard_report)

    @test_step
    def access_commcell_group_pages(self):
        """Access commcell group pages"""
        self.navigator.goto_commcell_group()
        commcell_group = CommcellGroup(self.webconsole)
        self.log.info("Creating [%s] commcell group", self.commcell_group_name)
        if commcell_group.is_group_exist(self.commcell_group_name):
            commcell_group.delete(self.commcell_group_name)
        commcell_group.create(self.commcell_group_name, [self.commcell.commserv_name])
        commcell_group.delete(self.commcell_group_name)

    def cleanup(self):
        """Cleanup alerts and schedules"""
        self.cleanup_alerts()
        self.cleanup_schedules()

    def run(self):
        try:
            self.init_tc()
            self.access_dashboard_cte()
            self.access_custom_report_cte()
            self.access_metrics_report_cte()
            self.access_commcell_group_pages()
            self.cleanup()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            self.status = constants.PASSED
