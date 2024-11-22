# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
TestCase to validate Private Metrics UploadNow operation from CommServe

TestCase:
    setup()                         --  initializes objects required for this TestCase

    validate_private_uploadnow()    --  Validates Private Metrics uploadNow operation

    run()           -               --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from cvpysdk.metricsreport import PrivateMetrics


class TestCase(CVTestCase):
    """TestCase to validate Private Metrics UploadNow operation from CommServe"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Private Metrics Upload Now"
        self.show_to_user = True
        self.private_metrics = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        """Intializes Private metrics object required for this testcase"""
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics.enable_all_services()

    @test_step
    def validate_private_uploadnow(self):
        """Validates Private Metrics uploadNow operation """
        self.log.info('Initiating Private Metrics upload now')
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_uploadnow_completion()
        self.log.info('Private Metrics upload now completed Successfully')

    @test_step
    def verify_no_zip_files_in_failed(self):
        """Validates Failed folder does not have latest collected zip file"""
        private_metrics_server = MetricsServer(self.private_metrics.private_metrics_server_name,
                                               self.inputJSONnode['commcell']["commcellUsername"],
                                               self.inputJSONnode['commcell']["commcellPassword"])
        filename = self.private_metrics.get_uploaded_filename()
        commcell_id = filename[:-4].split('_')[1]
        timestamp = filename[:-4].split('_')[0]
        if private_metrics_server.check_files_in_failed(pattern=f'CSS{timestamp}_{commcell_id}_*.zip'):
            raise CVTestStepFailure("All queries are not parsed")
        else:
            self.log.info("All queries are successfully parsed")

    def run(self):
        try:
            self.validate_private_uploadnow()
            self.verify_no_zip_files_in_failed()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
