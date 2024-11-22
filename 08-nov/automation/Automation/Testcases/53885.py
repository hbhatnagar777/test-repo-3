# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics: one shot collection for cloud metrics"""

from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Reports.metricsutils import MetricsServer
from Reports.utils import TestCaseUtils
from cvpysdk.metricsreport import CloudMetrics


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics one shot collection validation"
        self.utils = None
        self.metrics_server = None
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.navigator: Navigator = None
        self.one_shot_id = None
        self.scripts_path = None
        self.cloud_metrics = None
        self.query_id = None

    def init(self):
        """initialize with user/password as cloud11 doesn't have default admin/admin password"""
        self.utils = TestCaseUtils(self,
                                   username=self.inputJSONnode["commcell"]["commcellUsername"],
                                   password=self.inputJSONnode["commcell"]["commcellPassword"])

        self.cloud_metrics = CloudMetrics(self.commcell)
        self.metrics_server = MetricsServer(self.commcell.webconsole_hostname,
                                            self.inputJSONnode["commcell"]["commcellUsername"],
                                            self.inputJSONnode["commcell"]["commcellPassword"])
        self.query_id = "90"

    def generate_one_shot_file(self):
        """ Get last one shot query id , delete the one shot include file,
        generate new one shot id"""
        query = "SELECT value FROM GxGlobalParam WHERE name ='MetricsOneShotLatestID'"
        response = self.utils.cre_api.execute_sql(query)
        if response:
            self.scripts_path = self.metrics_server.get_script_dir()
            self.one_shot_id = "0" + str(int(response[0][0]) + 1)
            if response[0][0] != '0':
                one_shot_file_path = self.metrics_server.metrics_machine.join_path(
                    self.scripts_path, "MetricsIncludeOneShot_" + response[0][0] + ".txt")
                self.metrics_server.metrics_machine.delete_file(one_shot_file_path)
        else:
            self.one_shot_id = "01"

    @test_step
    def validate_metrics_one_shot(self):
        """ validates the metrics oneshot collection time from the database"""
        query = "CommservSurveyQuery_" + self.query_id + ".sql"
        one_shot_file_path = self.metrics_server.metrics_machine.join_path(
            self.scripts_path, "MetricsIncludeOneShot_" + self.one_shot_id + ".txt")
        self.metrics_server.metrics_machine.create_file(one_shot_file_path, query)
        self.log.info("Waiting 2 hours as createhash is taking around 8 minutes and"
                      " there is a chance that CVD wakes up first time within this 8 mins,"
                      " causing oneshot to get skipped as timestamp file is not yet updated")
        sleep(7200)
        # need to reset cre api, as token is getting expired in an hour, so that it can initialize
        # again
        self.utils.reset_cre()
        self.cloud_metrics.wait_for_uploadnow_completion()
        query = "SELECT value FROM GxGlobalParam WHERE name ='MetricsOneShotLatestID'"
        response = self.utils.cre_api.execute_sql(query)
        if response[0][0] != self.one_shot_id:
            raise CVTestStepFailure(
                f'Metrics one shot query id [{response[0][0]}] is'
                f' not udpated in the GxGlobalParam Table'
            )
        file_name = self.cloud_metrics.get_uploaded_filename()
        self.log.info("Waiting for the [{0}] file to be parsed".format(file_name))
        self.metrics_server.wait_for_parsing(file_name)

    def run(self):
        try:
            self.init()
            self.generate_one_shot_file()
            self.validate_metrics_one_shot()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
