# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import datetime

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.components import MetricsTable
from Web.WebConsole.Reports.Metrics.activity import MetricsActivity

from Reports.utils import TestCaseUtils

from FileSystem.FSUtils.fshelper import FSHelper
from cvpysdk.metricsreport import PrivateMetrics


class TestCase(CVTestCase):
    """
    Metrics Activity Job Details report validation
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics Activity Job Details report validation"
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.navigator: Navigator = None
        self.activity = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.subclients = "sc1"
        self.private_metrics = None
        self.utils: TestCaseUtils = None
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.job_id = None

    def init_tc(self):
        """initialize Fs helper """
        try:
            self.utils = TestCaseUtils(self)
            self.helper = None
            FSHelper.populate_tc_inputs(self)

        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    def init_webconsole(self):
        """
        initialize webconsole objects
        """
        try:
            self.private_metrics = PrivateMetrics(self.commcell)
            self.private_metrics.enable_activity()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login()
            self.navigator = Navigator(self.webconsole)
            self.activity = MetricsActivity(self.webconsole)
            self.webconsole.goto_reports()
            self.navigator.goto_commcell_reports('Activity',
                                                 commcell_name=self.commcell.commserv_name)
            self.activity.access_last16_day_chart()
        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    def generate_current_time(self):
        """Generate the hour for activity"""
        now = datetime.datetime.now()
        hours = str(int(datetime.datetime.strftime(now, "%I")))
        ampm = str(datetime.datetime.strftime(now, "%p"))
        return hours + ":00" + ' ' + ampm

    def create_backupset(self):
        """"create backupset"""
        self.backupset = "backupset_" + self.id
        self.helper.create_backupset(self.backupset, True)

    def create_valid_path(self, subclient_name):
        """create a valid path to backup"""
        test_path = self.test_path
        slash_format = self.slash_format
        test_path = test_path + slash_format + "subclient_" + subclient_name
        self.client_machine.generate_test_data(
            test_path,
            file_size=200
        )
        return test_path

    def create_sc(self, subclient_name):
        """
        create new subclient with valid path will be given as content
        """
        storage_policy = self.storage_policy
        subclient_content = []
        path = self.create_valid_path(subclient_name)
        subclient_content.append(path)
        self.helper.create_subclient(name=subclient_name,
                                     storage_policy=storage_policy,
                                     content=subclient_content,
                                     delete=True)

    def run_backup(self, subclient):
        """ run backup and get job Id """
        self.create_sc(subclient)
        job_obj = self.helper.run_backup(wait_to_complete=False)
        self.job_id = job_obj[0].job_id
        ret = job_obj[0].wait_for_completion(timeout=300)
        if ret is not True:
            job_obj[0].kill()

    @test_step
    def access_hourly_report(self):
        """
        access hourly report
        """
        self.init_webconsole()
        self.activity.access_hourly_details(self.generate_current_time())

    @test_step
    def verify_data(self):
        """
        validate the hourly jobs in job details page
        """
        table = MetricsTable(self.webconsole, table_name='Job Details')
        job_obj = table.get_data_from_column('Job ID')
        if self.job_id in job_obj:
            self.log.info("The Job Id [%s] is available in the Job Details table" % self.job_id)
        else:
            raise CVTestStepFailure(" The Job Id [%s] is missing from Job details table" % self.job_id)

    def run(self):
        try:
            self.init_tc()
            self.create_backupset()
            self.run_backup(self.subclients)
            self.utils.private_metrics_upload()
            self.access_hourly_report()
            self.verify_data()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
