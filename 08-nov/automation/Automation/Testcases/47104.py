# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
TestCase to validate Cloud Metrics UploadNow operation from CommServe

TestCase:
    setup()                    --  initializes objects required for this TestCase

    validate_cloud_uploadnow() --  Validates Cloud Metrics uploadNow operation

    run()           -          --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.metricsutils import MetricsServer
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from AutomationUtils import config
from Reports.utils import TestCaseUtils

from cvpysdk.metricsreport import CloudMetrics


class TestCase(CVTestCase):
    """TestCase to validate Cloud Metrics UploadNow operation from CommServe"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Cloud Metrics Upload Now"
        self.show_to_user = True
        self.config = config.get_config()
        self.cloud_metrics = None
        self.cloud_metrics_server = self.config.Cloud
        self.utils = TestCaseUtils(self)

    def setup(self):
        """Intializes cloud metrics object required for this testcase"""
        self.cloud_metrics = CloudMetrics(self.commcell)
        self.cloud_metrics.enable_all_services()

    @test_step
    def validate_cloud_uploadnow(self):
        """Validates Cloud Metrics uploadNow operation"""
        self.log.info('Initiating Cloud Metrics upload now')
        self.cloud_metrics.upload_now()
        self.cloud_metrics.wait_for_uploadnow_completion()
        self.log.info('Cloud Metrics upload now completed Successfully')

    @test_step
    def verify_no_zip_files_in_failed(self):
        """Validates Failed folder does not have latest collected zip files"""
        cloud_metrics_server = MetricsServer(self.cloud_metrics_server.host_name,
                                             self.cloud_metrics_server.username,
                                             self.cloud_metrics_server.password)
        filename = self.cloud_metrics.get_uploaded_filename()
        commcell_id = filename[:-4].split('_')[1]
        timestamp = filename[:-4].split('_')[0]
        if cloud_metrics_server.check_files_in_failed(pattern=f'CSS{timestamp}_{commcell_id}_*.zip'):
            raise CVTestStepFailure("All queries are not parsed")
        else:
            self.log.info("All queries are successfully parsed")

    def run(self):
        try:
            self.validate_cloud_uploadnow()
            self.verify_no_zip_files_in_failed()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
