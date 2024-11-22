# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" To verify only CommservSurveyQueries present in Metrics Server are present in CS cache """

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.metricsutils import MetricsServer
from Web.Common.page_object import TestStep
from cvpysdk.metricsreport import PrivateMetrics
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """
       TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.activity_dir = None
        self.download_dir = None
        self.commserv_client = None
        self.web_scripts_dir = None
        self.web_activity_dir = None
        self.cs_machine = None
        self.metrics_machine = None
        self.private_metrics = None
        self.utils = TestCaseUtils(self)
        self.name = "Metrics Queries Update validation in CS Cache"
        self.query_list = ["CommservSurveyQuery_134.sql",
                           "CommservSurveyQuery_137.sql"]
        self.metrics_server = None

    def setup(self):
        self.private_metrics = PrivateMetrics(self.commcell)
        self.metrics_server = MetricsServer(self.private_metrics.private_metrics_server_name,
                                            self._inputJSONnode["commcell"]["commcellUsername"],
                                            self._inputJSONnode["commcell"]["commcellPassword"])
        self.metrics_machine = self.metrics_server.metrics_machine
        self.commserv_client = self.commcell.commserv_client
        self.cs_machine = Machine(self.commserv_client)

    def init_tc(self):
        self.web_scripts_dir = self.metrics_server.get_script_dir()
        self.web_activity_dir = self.metrics_machine.join_path(self.web_scripts_dir, 'Activity')
        self.download_dir = self.cs_machine.join_path(self.commserv_client.install_directory, 'Reports',
                                                      'CommservSurvey', 'private', 'downloads', 'sqlscripts')
        self.activity_dir = self.cs_machine.join_path(self.download_dir, 'Activity')

    def move_queries_temporarily(self):
        for file in self.query_list:
            self.metrics_machine.move_file(self.metrics_machine.join_path(self.web_activity_dir, file),
                                           self.web_scripts_dir)
            self.log.info(f"Moved {file} file from {self.web_activity_dir} to {self.web_scripts_dir}")

    def private_metrics_download(self):
        self.log.info("Initiating Private Metrics Upload now")
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_download_completion()
        self.log.info("Private Metrics Queries are downloaded successfully")

    def verify_file_deleted(self):
        for file in self.query_list:
            if file in self.cs_machine.get_files_in_path(self.activity_dir):
                raise CVTestStepFailure(f"{file} File is still present in Activity directory. "
                                        f"Download cache is not getting updated ")
        self.log.info(f"{self.query_list} files are not present in Activity Directory. Download cache got updated ")

    def revert_metrics_server_changes(self):
        for file in self.query_list:
            self.metrics_machine.move_file(self.metrics_machine.join_path(self.web_scripts_dir, file),
                                           self.web_activity_dir)
            self.log.info(f"Moved {file} file back to {self.web_activity_dir} from {self.web_scripts_dir}")

    def run(self):
        try:
            self.init_tc()
            self.move_queries_temporarily()
            self.private_metrics_download()
            self.verify_file_deleted()
        finally:
            self.revert_metrics_server_changes()
            self.private_metrics_download()
