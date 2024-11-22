# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""TestCase to validate Private Metrics UploadNow using Remote Webconsole"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer

from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from cvpysdk.metricsreport import PrivateMetrics


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Upload using remote webconsole"
        self.show_to_user = True
        self.private_metrics = None
        self.metrics_server = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "RemoteWC": None
        }
        self.current_wc = None

    def setup(self):
        """Intializes Private metrics object required for this testcase"""
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics.enable_all_services()
        self.private_metrics.update_url(self.tcinputs['RemoteWC'])
        self.current_wc = (
            self.private_metrics.downloadurl.split('://')[1].split('/')[0].split(':')[0]
        )
        self.metrics_server = MetricsServer(self.private_metrics.private_metrics_server_name,
                                            self.inputJSONnode['commcell']["commcellUsername"],
                                            self.inputJSONnode['commcell']["commcellPassword"])

    @test_step
    def private_upload_from_cs(self):
        """Validates Private Metrics uploadNow operation """
        self.log.info('Initiating Private Metrics upload now')
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_uploadnow_completion()
        self.log.info('Private Metrics upload now completed Successfully')

    @test_step
    def check_file_in_metrics(self):
        """Verify uploaded file reached metrics server"""
        try:
            self.metrics_server.wait_for_parsing(self.private_metrics.get_uploaded_filename())
        except TimeoutError:
            raise CVTestStepFailure(
               f"uploaded file [{self.private_metrics.get_uploaded_filename()}] "
               f"didn't reach Metrics server '{self.metrics_server.webserver_name}'"
            )

    def run(self):
        try:
            self.private_upload_from_cs()
            self.check_file_in_metrics()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            self.private_metrics.update_url(self.current_wc)
