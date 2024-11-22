# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Report Page load Acceptance
Every Report in worlwide level and commcell level are checked for errors and load time
TestCase:

    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    split_process           --  splits into multiple process base on report count

    make_html_table         -- Prepares the html table for the mail

    generate_html_page      -- Generate html page for mail

    get_notification_errors_html --  Get notification errors from report objects

    get_console_errors_html --  Get console error as html table

p_wrapper  --   Wrapper to create object for process

ReportAcceptance        -- class to feed into process
    ReportDetails       -- class to store report status
    collect_reports_access_details      -- Collects report page status

    verify_health_view_details_pages    -- Verify health report detail pages

    verify_report_page                  -- Verify page load status

    get_browser_logs                    -- Gets browser console logs

    check_page_load_time                -- checks load time

    check_console_error                 -- checks browser console error

    check_no_data_in_page               -- checks if report has data

    check_page_blank                    -- check if page is blank

"""

import time
from selenium.common.exceptions import TimeoutException
from multiprocessing import Process, Queue
import math
import os

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.home import ReportsHomePage
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.Metrics.health_tiles import GenericTile
from Web.WebConsole.Reports.Metrics.config_audit import ConfigurationAuditReport
from Web.WebConsole.Reports.Metrics.health import Health

from Web.Common.exceptions import CVTimeOutException

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mailer import Mailer
from AutomationUtils import config
from AutomationUtils import constants, logger
from Reports.utils import TestCaseUtils
from Reports import reportsutils
from Reports import utils

_CONSTANTS = config.get_config()


class ReportAcceptance:
    """Performs Report Acceptance passed in each process"""
    test_step = TestStep()

    class ReportStatus:
        """Set report status"""
        WARNING = "Warning"
        CRITICAL = "Critical"
        SUCCESS = "Success"

    class ReportDetails:
        def __init__(self, name, url):
            self.load_time = "NA"
            self.status = ReportAcceptance.ReportStatus.SUCCESS
            self.notifications = None
            self.console_errors = None
            self.is_page_no_data = False
            self.failure_reason = None
            self.is_page_blank = False
            self.url = url
            self.name = name

    def __init__(self, machine_name, wc_uname, wc_pwd, reports_list, batch_name):
        self.webconsole_name = machine_name
        self.wc_uname = wc_uname
        self.wc_pwd = wc_pwd
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.metrics_report = None
        self.reports = reports_list
        self.batch_name = batch_name
        self.reports_home_page = None
        _ = logger.Logger(constants.LOG_DIR, __name__, os.getpid())
        self.log = logger.get_log()
        self.health_reports = list()
        self.report_details = list()
        self.configuration_audit_report = None

    def init(self):
        """Opens browse and moves to reports page"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.webconsole_name)
        self.webconsole.login(self.wc_uname, self.wc_pwd)
        self.metrics_report = MetricsReport(self.webconsole)
        self.navigator = Navigator(self.webconsole)
        self.webconsole.goto_reports()
        self.reports_home_page = ReportsHomePage(webconsole=self.webconsole)
        self.configuration_audit_report = ConfigurationAuditReport(self.webconsole)

    def check_page_load_time(self, report_object, time_out=100):
        """Collect page load time for the report"""
        try:
            start_time = time.time()
            self.webconsole.wait_till_load_complete(timeout=time_out)
            report_object.load_time = str(int((time.time() - start_time)))
        except CVTimeOutException:
            pass

    def check_console_error(self, report_object):
        """Collect console errors on report"""
        report_object.console_errors = self.get_browser_logs("SEVERE")

    def check_no_data_in_page(self, report_object):
        """Verify No data available on chart"""
        if self.metrics_report.is_no_data_error_exists():
            report_object.is_page_no_data = True

    def check_page_blank(self, report_object):
        """Verify 'page is blank"""
        if self.metrics_report.is_page_blank():
            report_object.is_page_blank = True

    def check_notification_error(self, report_object):
        """Check for any notification errors if exists"""
        report_object.notifications = self.webconsole.get_all_unread_notifications()
        if report_object.notifications:  # once the notifications are found clear the
            # notifications for next report
            msg = 'No search engine clouds found. Contact your Administrator or try again later.'
            name = 'eDiscovery Exception Report'
            if report_object.notifications[0] == msg and report_object.name == name:
                report_object.notifications = []
            self.webconsole.clear_all_notifications()

    def get_browser_logs(self, log_level="SEVERE"):
        """ Get browser console logs filtered by log level as SEVERE/WARNING/INFO"""
        logs = self.browser.driver.get_log('browser')
        return [log for log in logs if log["level"] == log_level]

    def set_report_status(self, report_object):
        """Set report status"""
        if report_object.notifications:
            report_object.failure_reason = "Notification Error"
            return
        if report_object.console_errors:
            report_object.failure_reason = "Console Error"
            return
        if report_object.is_page_no_data or report_object.is_page_blank is True:
            report_object.status = self.ReportStatus.WARNING
            report_object.failure_reason = "No data available"
            return
        if report_object.load_time == "NA":
            report_object.failure_reason = "Page is not loaded within timout[%s sec] period" % \
                                           "100"
            report_object.status = self.ReportStatus.CRITICAL

    def verify_report_page(self, report_object):
        """Verify page load status"""
        self.check_page_load_time(report_object)
        self.check_no_data_in_page(report_object)
        # self.check_console_error(report_object)
        self.check_notification_error(report_object)
        self.set_report_status(report_object)

    @test_step
    def verify_health_view_details_pages(self):
        """Verify health report detail pages"""
        health = Health(self.webconsole)
        tiles = health.get_view_details_tiles()
        for each_tile in tiles:
            health_tile = GenericTile(self.webconsole, each_tile)
            health_tile.access_view_details()
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
            report_object = ReportAcceptance.ReportDetails(
                each_tile, self.browser.driver.current_url
            )
            self.verify_report_page(report_object)
            self.health_reports.append(report_object)
            self.browser.driver.close()
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])

    @test_step
    def verify_config_audit_report(self):
        """Verify Configuration audit report"""
        _type = ConfigurationAuditReport.EntityType
        self.configuration_audit_report.configure_report(_type.STORAGE_POLICY, True)

    def collect_reports_access_details(self):
        """Collects report page status"""
        _temp_report_names = []
        self.webconsole.clear_all_notifications()
        for each_report in self.reports:
            # skip accessing all custom report during security test
            if _CONSTANTS.SECURITY_TEST and reportsutils.is_custom_report(each_report['href']):
                continue
            #  skip report if its already present in different tag.
            if each_report['name'] in _temp_report_names:
                continue
            # if report is present different tags maintain temp for skipping the report.
            report_url = each_report['href']
            _temp_report_names.append(each_report['name'])
            report_object = ReportAcceptance.ReportDetails(each_report['name'], report_url)
            self.get_browser_logs()  # to clear existing console error
            try:
                self.browser.driver.get(report_url)
            except TimeoutException:
                self.log.warning("Timed out while redirecting to url", report_url)
            if each_report['name'] == "Configuration Audit (Deprecated)":
                self.verify_config_audit_report()
            self.log.info("%s [Count:%s/%s] Verifying page for the report [%s] with url [%s]",
                          self.batch_name,
                          (self.reports.index(each_report) + 1),
                          len(self.reports),
                          each_report['name'],
                          report_object.url)
            report_object.url = self.browser.driver.current_url
            self.verify_report_page(report_object)
            self.report_details.append(report_object)
            if each_report['name'] == "Health":
                self.verify_health_view_details_pages()
        self.log.info(f"{self.batch_name} processing completed")
        return self.report_details, self.health_reports

    def close(self):
        """Closes the browser"""
        WebConsole.logout_silently(self.webconsole)
        Browser.close_silently(self.browser)

    def run(self):
        """Starting method for each process"""
        try:
            self.init()
            self.log.info(
                f"{self.batch_name}, {len(self.reports)} reports : reports list [{self.reports}]"
            )
            report_details, health_reports = self.collect_reports_access_details()
            self.close()
            return report_details, health_reports
        except Exception as exception:
            self.log.exception(f"Validation failure in batch: {exception}")
            self.close()
            return [], []


def p_wrapper(webconsole, uname, pwd, reports, name, queue):
    """Wrapper to create object for each process"""
    validator = ReportAcceptance(webconsole, uname, pwd, reports, name)
    queue.put(validator.run())


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics Report Page load Acceptance"
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.reports_home_page = None
        self.utils = TestCaseUtils(self)
        self.metrics_report = None
        self.commcell_name = None
        self.email_receiver = None
        self.mailer = None
        self.worldwide_reports = []
        self.commcell_reports = []
        self.health_reports = []
        self.html_heading = None
        self.mail_sent = False
        self.is_metrics_enabled = True
        self.max_process = 6

    def init_tc(self):
        """
        Initial configuration for the testcase
        """
        try:
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.tcinputs["cloud_name"])
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = Navigator(self.webconsole)
            self.reports_home_page = ReportsHomePage(webconsole=self.webconsole)
            if not self.webconsole.is_commcell_dashboard_visible():
                self.is_metrics_enabled = False
            self.webconsole.goto_reports()
            self.commcell_name = self.tcinputs["commcell_name"]
            self.utils.get_browser_logs("SEVERE")  # to clear existing console error
            self.html_heading = ("<body><p>Hello, Some Metrics Report Pages are having loading "
                                 "issues on <a href>%s</a><br/><br/> Browser used for this TC: "
                                 "<b>%s</b></p>" % (self.webconsole.base_url,
                                                    self.browser.driver.name.upper()))
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def set_testcase_status(self):
        """Set test case status """
        for each_report in self.worldwide_reports:
            if each_report.notifications:  # or each_report.console_errors:
                raise CVTestStepFailure("Notification errors are found in worldwide "
                                        "reports.")
            if each_report.status == ReportAcceptance.ReportStatus.CRITICAL:
                raise CVTestStepFailure("Reports found with Critical status in worldwide reports")
        for each_report in self.commcell_reports:
            if each_report.notifications:  # or each_report.console_errors:
                raise CVTestStepFailure("Notification errors are found in commcell "
                                        "reports.")
            if each_report.status == ReportAcceptance.ReportStatus.CRITICAL:
                raise CVTestStepFailure("Reports found with Critical status in commcell reports")

    def get_console_errors_html(self, reports_objects):
        """Get console error as html table"""
        _list = []
        html = ""
        for each_report in reports_objects:
            if each_report.console_errors:
                _list.append(("<a href=%s >%s</a>" % (each_report.url, each_report.name)))
                _list.append(str(each_report.console_errors))
        if _list:
            _list.insert(0, 'Console Error')
            _list.insert(0, 'Report')
            html += ''.join(self.make_html_table(self.prep_page_status_list(_list, 2)))
        return html

    def get_notification_errors_html(self, reports_objects):
        """Get notification errors from report objects"""
        _list = []
        html = ""
        for each_report in reports_objects:
            if each_report.notifications:
                _list.append(("<a href=%s >%s</a>" % (each_report.url, each_report.name)))
                _list.append(str(each_report.notifications))
        if _list:
            _list.insert(0, 'Notification Error')
            _list.insert(0, 'Report')
            html += ''.join(self.make_html_table(self.prep_page_status_list(_list, 2)))
        return html

    def get_reports_html(self, reports_objects):
        """ Get reports as html table"""
        _list = []
        html = ""
        for each_report in reports_objects:
            if not each_report.console_errors and not each_report.notifications:
                if each_report.status == 'Success':
                    continue
                _list.append(("<a href=%s >%s</a>" % (each_report.url, each_report.name)))
                _list.append(each_report.status)
                _list.append(each_report.failure_reason)
                _list.append(each_report.load_time)
        if _list:
            _list.insert(0, "LoadTime(sec)")
            _list.insert(0, "Comments")
            _list.insert(0, "Status")
            _list.insert(0, "Report")
            html += ''.join(self.make_html_table((self.prep_page_status_list(_list, 4))))
        return html

    def generate_html_page(self):
        """Generate html page for mail"""
        html = self.html_heading
        html_string = self.get_notification_errors_html(self.worldwide_reports)
        if html_string:
            html += """<h3> Notification Errors from worldwide reports<h3>"""
            html += html_string
        html_string = self.get_notification_errors_html(self.commcell_reports)
        if html_string:
            html += """<h3> Notification Errors from commcell reports<h3>"""
            html += html_string
        html_string = self.get_notification_errors_html(self.health_reports)
        if html_string:
            html += """<h3> Notification Errors from health reports<h3>"""
            html += html_string

        html_string = self.get_reports_html(self.worldwide_reports)
        if html_string:
            html += """<h3> Worldwide Reports </h3>"""
            html += html_string
        html_string = self.get_reports_html(self.commcell_reports)
        if html_string:
            html += """<h3> Commcell Reports </h3>"""
            html += html_string
        html_string = self.get_reports_html(self.health_reports)
        if html_string:
            html += """<h3> Health Reports </h3>"""
            html += html_string

        html_string = self.get_console_errors_html(self.worldwide_reports)
        if html_string:
            html += """<h3> Console Errors from worldwide reports </h3>"""
            html += html_string
        html_string = self.get_console_errors_html(self.commcell_reports)
        if html_string:
            html += """<h3> Console Errors from commcell level reports </h3>"""
            html += html_string
        html_string = self.get_console_errors_html(self.health_reports)
        if html_string:
            html += """<h3> Console Errors from Health reports </h3>"""
            html += html_string
        self.log.info("Email html string:" + str(html))
        return html

    def send_mail(self, html_content):
        """Send mail """
        if self.mail_sent is False:
            if html_content != self.html_heading:
                self.mailer.mail("Issue in loading Reports on " + self.tcinputs["cloud_name"],
                                 html_content)
            self.mail_sent = True

    @staticmethod
    def prep_page_status_list(s_list, sub_length):
        """Prepare page status list"""
        prepared_list = [s_list[i:i + sub_length] for i in range(0, len(s_list), sub_length)]
        return prepared_list

    def make_html_table(self, prepared_list):
        """Prepares the html table for the mail """
        yield '    <table border="1">'
        headings_list = ['Report', 'Console Error', 'Notification Error', 'Status', 'Comments',
                         'LoadTime']
        for sublist in prepared_list:
            self.log.info("Making html for:%s", sublist)
            if sublist[1] == ReportAcceptance.ReportStatus.CRITICAL:
                yield '  <tr style="color:red;"><td>'
                yield '    </td><td>'.join(sublist)
            elif sublist[1] == ReportAcceptance.ReportStatus.WARNING:
                yield '  <tr style="color:orange;"><td>'
                yield '    </td><td>'.join(sublist)
            else:
                if sublist[0] in headings_list:
                    yield '  <tr><td><b>'
                    yield '    </td><td><b>'.join(sublist)
                else:
                    yield '  <tr><td>'
                    yield '    </td><td>'.join(sublist)
            yield '  </b></td></tr>'
        yield '    </table><br><br>'

    def get_reports(self):
        """returns list of reports grouped by process bucket"""
        reports = self.reports_home_page.get_all_report_details()
        health = list()
        if 'Health' in reports:
            reports.remove('Health')
            health.append('Health')
        size = math.ceil(len(reports) / self.max_process)
        report_list = [
            reports[i * size: (i + 1) * size]
            for i in range(math.ceil(len(reports) / size))
        ]
        if health:
            report_list.append(health)
        return report_list

    def split_process(self, commcell_level):
        """Splits into multiple process based on report count"""
        reports_list = self.get_reports()
        # reports_list = [['a'],['b'],['c'],['d']]
        queues = [Queue() for _ in reports_list]
        processes = [
            Process(
                target=p_wrapper,
                args=(
                    self.commcell.webconsole_hostname,
                    self.inputJSONnode['commcell']["commcellUsername"],
                    self.inputJSONnode['commcell']["commcellPassword"],
                    report,
                    f"Batch_{index}",
                    queues[index]
                ),
            )
            for index, report in enumerate(reports_list)
        ]
        for process in processes:
            self.log.info(f"Spawning new process [{id(process)}]")
            process.start()
            self.log.info(f"Spawned new process [{id(process)}], PID [{process.ident}]")
        self.log.info("Collecting results from queue")
        for queue in queues:
            reports, health = queue.get()
            if not commcell_level:
                self.worldwide_reports.extend(reports)
            else:
                self.commcell_reports.extend(reports)
            self.health_reports.extend(health)
        for process in processes:
            self.log.info(f"Closing Process [{process.ident}]")
            process.join()
            self.log.info(f"Closed Process[{process.ident}]")

    def run(self):
        try:
            self.init_tc()
            self.email_receiver = self.tcinputs["email_receiver"]
            self.mailer = Mailer({'receiver': self.email_receiver}, self.commcell)
            self.utils = utils.TestCaseUtils(self)
            if self.is_metrics_enabled:
                self.split_process(commcell_level=False)  # access reports in different process
                if not self.worldwide_reports:
                    raise CVTestStepFailure('Exceptions in Worldwide Report validation check logs')
                self.log.info("Access commcell level reports")
                Browser.close_silently(self.browser)
                self.init_tc()
                self.navigator.goto_commcell_dashboard(self.commcell_name)
                self.navigator.goto_commcell_reports(commcell_name=self.commcell_name)
            self.split_process(commcell_level=True)
            if not self.commcell_reports:
                raise CVTestStepFailure('Exceptions in Commcell Report validation check logs')
            html = self.generate_html_page()
            self.send_mail(html_content=html)
            self.log.info("Survey completed")
            self.set_testcase_status()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
            html = self.generate_html_page()
            self.send_mail(html_content=html)
        finally:
            Browser.close_silently(self.browser)
