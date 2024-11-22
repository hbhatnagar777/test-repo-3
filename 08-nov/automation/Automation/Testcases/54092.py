# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import os
import math
from time import sleep
from multiprocessing import Process, Queue
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import ElementNotVisibleException
from AutomationUtils import constants, logger
from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common import page_object
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVWebAutomationException,
    CVTimeOutException,
    CVWebAPIException,
    CVWebNoData,
    CVTestStepFailure,
)

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.Custom.viewer import CustomReportViewer
from Web.WebConsole.Reports.Custom.inputs import ListBoxController

from Web.API.customreports import CustomReportsAPI
from Web.API.webconsole import Store

from AutomationUtils.config import get_config

from Reports.utils import TestCaseUtils

_CONFIG = get_config()


class CloudReportsValidator:

    test_step = page_object.TestStep()
    InstallFailure = 'Install Failure'
    Timeout = 'Load Time out'
    NoData = 'No Data'
    Errors = 'Errors'
    Success = 'Success'
    unknown = 'Unknown'

    def __init__(self, machine_name, wc_uname, wc_pwd, reports, batch_name):
        self.webconsole_name = machine_name
        self.wc_uname = wc_uname
        self.wc_pwd = wc_pwd
        self.store_reports = reports
        self._cre_api = None
        self._store_api = None
        self.batch_name = batch_name + ", PID " + str(os.getpid())
        self.p_name = batch_name
        _ = logger.Logger(constants.LOG_DIR, "54092", os.getpid())  # mapping caller thread to TC
        self.log = logger.get_log()
        self.browser = None
        self.webconsole = None
        self.metrics_report = None
        self.failed_reports = {}

    def init(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.webconsole_name)
        self.webconsole.login(self.wc_uname, self.wc_pwd)
        self.metrics_report = MetricsReport(self.webconsole)

    def close(self):
        WebConsole.logout_silently(self.webconsole)
        Browser.close_silently(self.browser)

    @property
    def cre_api(self):
        if self._cre_api is None:
            self._cre_api = CustomReportsAPI(
                self.webconsole_name,
                username=self.wc_uname,
                password=self.wc_pwd
            )
        return self._cre_api

    @property
    def store_api(self):
        if self._store_api is None:
            self._store_api = Store(
                machine=self.webconsole_name,
                wc_uname=self.wc_uname,
                wc_pass=self.wc_pwd,
                store_uname=_CONFIG.email.username,
                store_pass=_CONFIG.email.password
            )
        return self._store_api

    def install_report(self, report):
        _ = logger.Logger(constants.LOG_DIR, "54092", os.getpid())  # mapping caller thread to TC
        retry_delete_idx = 0
        while retry_delete_idx < 2:
            try:
                sleep(2)
                self.cre_api.delete_custom_report_by_name(report, suppress=True)
                break
            except Exception as e:
                sleep(5)
                retry_delete_idx += 1
                self.log.exception(f"Delete report {report} failed : {e}")
        sleep(4)
        self.store_api.install(report, "Reports")
        return "Installed Successfully"

    @test_step
    def install_reports(self):
        """Installing all the store reports"""
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                (report, executor.submit(self.install_report, report))
                for report in self.store_reports
            ]
            finished = {}
            failed = {}
            for report_name, future in futures:
                try:
                    finished[report_name] = future.result(timeout=120)
                except CVWebAPIException as e:
                    self.log.exception(f'Install Failure of report {report_name}: [{e}]')
                    failed[report_name] = {
                        'status': CloudReportsValidator.InstallFailure,
                        'message': str(e),
                        'url': ''
                    }
                except Exception as e:
                    self.log.exception(f'Unknown Install Failure of report {report_name}: [{e}]')
                    failed[report_name] = {
                        'status': CloudReportsValidator.unknown,
                        'message': str(e),
                        'url': ''
                    }
        return finished, failed

    def recheck_will_all_commcell(self):
        viewer = CustomReportViewer(self.webconsole)
        if "CommCell" in viewer.get_all_input_names():
            cc = ListBoxController('CommCell')
            try:
                cc.select_all()
            except:
                pass
            else:
                cc.apply()
                self.webconsole.wait_till_load_complete()
            self.metrics_report.raise_for_no_data_error()

    @test_step
    def validate_report(self, report):
        """Validate report"""
        self.log.info(f"Starting browser validation on report [{report}]")
        store_rpt_url = self.store_api.get_package(report, "Reports")["launchURL"]
        report_url = self.webconsole.base_url + store_rpt_url.split("webconsole/")[-1]
        self.browser.driver.get(report_url)
        self.webconsole.wait_till_load_complete()
        self.webconsole.get_all_unread_notifications(expected_count=0)
        try:
            self.metrics_report.raise_for_no_data_error()
        except CVWebNoData:
            self.recheck_will_all_commcell()

        return {
            'status': 'Success',
            'message': 'Successfully validated',
            'url': report_url
        }

    def log_cache_summary(self):
        self.log.info(
            ("." * 5) +
            f" Cache summary ({self.batch_name}): " +
            ("." * 5)
        )
        c_info = self.store_api.get_packages.cache_info()
        self.log.info(f"self.store_api.get_packages(): {c_info}")
        c_info = self.store_api.get_all_categories.cache_info()
        self.log.info(f"self.store_api.get_all_categories(): {c_info}")

    def handle_exception(self, report, e, message, url):
        self.log.error(
            f"\nReport [{report}], " +
            page_object.formatted_error_summary(e).strip()
        )
        self.log.exception(f"Validation failure in {report}: {e}")
        self.failed_reports[report].update(
            {
                'message': message,
                'url': url
            }
        )

    def run(self):
        self.store_api.get_packages("Reports", None, details=True)  # TO build cache
        self.log.info(f'Reports to install [{self.store_reports}]')
        installed_reports, self.failed_reports = self.install_reports()
        # failed_reports = {}
        # installed_reports = self.store_reports
        self.init()
        self.store_api.get_packages.cache_clear()
        validated_reports = {}
        for report in installed_reports:
            try:
                sleep(2)
                try:
                    self.webconsole.clear_all_notifications()
                except ElementNotVisibleException:
                    pass
                ret_msg = self.validate_report(report)
                validated_reports[report] = ret_msg

            except CVTimeOutException as e:
                self.failed_reports[report] = {'status': CloudReportsValidator.Timeout}
                message = (
                    f"Timeout occurred, operation=[{e.operation}] "
                    f"wait_time=[{e.timeout_seconds} sec]"
                )
                self.handle_exception(report, e, message, e.url)
            except CVWebNoData as e:
                self.failed_reports[report] = {'status': CloudReportsValidator.NoData}
                self.handle_exception(report, e, e.msg, e.url)
            except CVWebAutomationException as e:
                self.failed_reports[report] = {'status': CloudReportsValidator.Errors}
                self.handle_exception(report, e, str(e), self.browser.driver.current_url)
            except Exception as e:
                self.failed_reports[report] = {'status': CloudReportsValidator.unknown}
                self.handle_exception(report, e, str(e), self.browser.driver.current_url)

        self.log_cache_summary()
        self.close()
        self.log.info(f'{self.p_name} success - {validated_reports}')
        self.log.info(f'{self.p_name} Failure - {self.failed_reports}')
        return validated_reports, self.failed_reports


def p_wrapper(reports, webconsole, uname, pwd, name, queue):
    validator = CloudReportsValidator(webconsole, uname, pwd, reports, name)
    queue.put(validator.run())


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Acceptance for all Reports in store"
        self.max_workers = 6
        self.tcinputs = {
            "Failed_only": None
        }
        self.utils = None

    def init(self):
        self.utils = TestCaseUtils(
            self,
            username=self.inputJSONnode['commcell']["commcellUsername"],
            password=self.inputJSONnode['commcell']["commcellPassword"]
        )
        self.create_table()

    def create_table(self):
        sql_string = """
        IF not EXISTS (SELECT * FROM dbo.sysobjects where id = object_id(N'dbo.[StoreReportStatus]')) 
        BEGIN 
            create table StoreReportStatus
                (
                name                nvarchar(Max),
                Status              nvarchar(50),
                Reason				nvarchar(Max),
                url					nvarchar(Max),
                reviewdate			datetime
                );
            End
        """
        self.utils.cre_api.execute_sql(sql_string)

    def get_failed_reports(self):
        sql_string = """
        SELECT Name FROM StoreReportStatus WHERE Status != 'Success'
        """
        reports = []
        result = self.utils.cre_api.execute_sql(sql_string)
        for row in result:
            reports.append(row[0])
        return reports

    def get_reports(self):
        try:
            failed_only = self.tcinputs['Failed_only']
            if (failed_only == 1 or str(failed_only).lower() == 'true'
                    or str(failed_only).lower() == 'yes'):
                reports = self.get_failed_reports()
            else:
                store = Store(
                    machine=self.commcell.webconsole_hostname,
                    wc_uname=self.inputJSONnode['commcell']["commcellUsername"],
                    wc_pass=self.inputJSONnode['commcell']["commcellPassword"],
                    store_uname=_CONFIG.email.username,
                    store_pass=_CONFIG.email.password
                )
                reports = store.get_reports()
            if not reports:
                return []
            size = math.ceil(len(reports) / self.max_workers)
            return [
                reports[i * size: (i + 1) * size]
                for i in range(math.ceil(len(reports) / size))
            ]
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @staticmethod
    def form_sql(report_name, result):
        return f"""
        SELECT @name = '{report_name}'
        IF EXISTS (SELECT name FROM StoreReportStatus WHERE Name = @name)
            UPDATE StoreReportStatus SET Status='{result["status"]}',
             Reason='{result["message"].replace("'", "''")}',
             url='{result["url"]}',reviewdate=GETDATE() WHERE Name=@name
        ELSE
            INSERT INTO StoreReportStatus VALUES(@name,'{result["status"]}',
            '{result['message'].replace("'", "''")}','{result["url"]}', GETDATE())


        """

    @staticmethod
    def form_sql_success(report_name, result):
        status = 'Success'
        return f"""
            SELECT @name = '{report_name}'
            IF EXISTS (SELECT name FROM StoreReportStatus WHERE name = @name)
                UPDATE StoreReportStatus SET Status='{result["status"]}', Reason='',
                url='{result["url"]}',reviewdate=GETDATE() WHERE Name=@name
            ELSE
                INSERT INTO StoreReportStatus VALUES(@name, '{status}','','{result["url"]}', GETDATE())

            """

    def update_db(self, sql_string):
        self.utils.cre_api.execute_sql(sql_string)

    def remove_deleted_reports(self):
        sql_string = """
        select name from StoreReportStatus where Reason like 'Package % not found'
        """
        result = self.utils.cre_api.execute_sql(sql_string)
        if result:
            temp = '\n'
            for report in result:
                temp += report[0] + '\n'
            self.log.info(f"Following reports are not present in store: {temp}")
        del_string = """
        Delete from StoreReportStatus where Reason like 'Package % not found'
        """
        self.utils.cre_api.execute_sql(del_string)

    def run(self):
        try:
            self.init()
            reports = self.get_reports()
            queues = [Queue() for _ in reports]
            success_dict = {}
            failed_dict = {}
            processes = [
                Process(
                    target=p_wrapper,
                    args=(
                        report,
                        self.commcell.webconsole_hostname,
                        self.inputJSONnode['commcell']["commcellUsername"],
                        self.inputJSONnode['commcell']["commcellPassword"],
                        f"Batch_{index}, {len(report)} reports",
                        queues[index]
                    ),
                )
                for index, report in enumerate(reports)
            ]
            for process in processes:
                self.log.info(f"Spawning new process [{id(process)}]")
                process.start()
                self.log.info(f"Spawned new process [{id(process)}], PID [{process.ident}]")
            self.log.info("Collecting results from queue")
            for queue in queues:
                success, failed = queue.get()
                success_dict.update(success)
                failed_dict.update(failed)

            results_str = "\n" + "\n".join([
                "%-65s  : %s" % (rpt, str(msg))
                for rpt, msg in failed_dict.items()
            ]).strip()
            results_str += "\n" + "\n".join([
                "%-65s  : %s" % (rpt, str(msg))
                for rpt, msg in success_dict.items()
            ]).strip()
            self.log.info(results_str)

            sql_string = 'DECLARE @name nvarchar(max) \n'
            for rpt, msg in failed_dict.items():
                sql_string += self.form_sql(rpt, msg)
                sql_string += '\n'

            for rpt, msg in success_dict.items():
                sql_string += self.form_sql_success(rpt, msg)
                sql_string += '\n'

            self.log.info(sql_string)
            self.update_db(sql_string)
            self.remove_deleted_reports()  # remove report packages that are removed from store
            for process in processes:
                self.log.info(f"Closing [{process.ident}]")
                process.join()
                self.log.info(f"Closed [{process.ident}]")
            for rpt, msg in failed_dict.items():
                if msg['status'] == 'Errors':
                    raise CVTestStepFailure('Some reports have failed status')
        except Exception as excep:
            page_object.handle_testcase_exception(self, excep)