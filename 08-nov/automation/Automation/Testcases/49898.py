""""
TestCase to validate Metrics server as Internet Gateway.
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer

from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from cvpysdk.metricsreport import CloudMetrics, PrivateMetrics
from cvpysdk.internetoptions import InternetOptions

from time import sleep

_CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to validate Metrics server as Internet Gateway"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Public Metrics using Private metric server as Gateway"
        self.private_metrics = None
        self.utils = TestCaseUtils(self)
        self.internet = None
        self.metrics_server = None
        self.public_metrics = None
        self.tcinputs = {
            "CloudMetricsServer": None,
            "Private_metrics_server": None,
            "CloudMetricsServerUser": None,
            "CloudMetricsServerPwd": None
        }
        self.cre_api = None
        self.old_url = None

    def setup(self):
        """Initializes Private metrics object required for this test case"""
        self.public_metrics = CloudMetrics(self.commcell)
        self.private_metrics = PrivateMetrics(self.commcell)
        self.internet = InternetOptions(self.commcell)
        self.metrics_server = MetricsServer(
            self.tcinputs["CloudMetricsServer"],
            metrics_commcell_user=self.tcinputs["CloudMetricsServerUser"],
            metrics_commcell_pwd=self.tcinputs["CloudMetricsServerPwd"]
        )
        self.utils = TestCaseUtils(
            self,
            username=self.inputJSONnode['commcell']["commcellUsername"],
            password=self.inputJSONnode['commcell']["commcellPassword"]
        )
        self.cre_api = self.utils.cre_api

    def init_tc(self):
        self.public_metrics.enable_metrics()
        self.private_metrics.update_url(self.tcinputs["Private_metrics_server"])
        sql = "SELECT value FROM gxglobalparam	 where name = 'CommservSurveyUploadsite'"
        result = self.cre_api.execute_sql(sql)
        self.old_url = result[0][0]
        self.log.info(
            f'Setting edc site public url in CommCell {self.commcell}'
        )
        sql = (
            "UPDATE GXGlobalParam SET value='https://edc.commvault.com/httplogupload/'"
            " where name='CommservSurveyUploadsite'"
        )
        self.utils.cs_db.execute(sql)

    @test_step
    def set_metrics_gateway(self):
        """Sets Metrics server gateway"""
        self.internet.set_metrics_internet_gateway()

    @test_step
    def initiate_public_uploadnow(self):
        """Validates Private Metrics uploadNow operation """
        self.log.info('Initiating public Metrics upload now')
        self.public_metrics.upload_now()
        self.public_metrics.wait_for_uploadnow_completion()
        self.log.info('Cloud Metrics upload now completed Successfully')

    @test_step
    def validate_metrics_gateway(self):
        """Validate uploaded file reached Cloud metrics server"""
        try:
            self.metrics_server.wait_for_parsing(self.public_metrics.get_uploaded_filename())
        except TimeoutError as msg:
            raise CVTestStepFailure("Cloud metrics :" + str(msg)) from msg

    def run(self):
        try:
            self.init_tc()
            self.set_metrics_gateway()
            self.initiate_public_uploadnow()
            self.log.info("wait for 2 min for private metrics to forward the result")
            sleep(120)
            self.validate_metrics_gateway()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            self.internet.set_no_gateway()
            sql = (
                f"UPDATE GXGlobalParam SET value='{self.old_url}'"
                " where name='CommservSurveyUploadsite'"
            )
            self.utils.cs_db.execute(sql)