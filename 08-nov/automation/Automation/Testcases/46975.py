""""
TestCase to validate Metrics- Upload Now using Internet Gateway

TestCase:
    setup()                         --  initializes objects required for this TestCase

    validate_private_uploadnow()    --  Validates Private Metrics uploadNow operation

    run()           -               --  run function of this test case
"""
import os
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger
from Reports.metricsutils import MetricsServer
from Reports.utils import TestCaseUtils

from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure

from AutomationUtils.machine import Machine

from cvpysdk.metricsreport import PrivateMetrics
from cvpysdk.internetoptions import InternetOptions
from cvpysdk.client import Clients
from cvpysdk.license import LicenseDetails
import socket


class TestCase(CVTestCase):
    """TestCase to validate Private and cloud Metrics Upload using Internet Gateway Client"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.license_details = None
        self.name = "Metrics: Private Upload Now using Internet Gateway"
        self.show_to_user = True
        self.log = logger.get_log()
        self.private_metrics = None
        self.tcinputs = {
            "GatewayClientName": None,
        }
        self.internet = None
        self.utils = TestCaseUtils(self)
        self.gateway_client = None
        self.metrics_server = None
        self.private_metrics_wc = None
        self.commcell_info = None
        self.private_metrics_name = None
        self.gateway_machine = None

    def setup(self):
        """Initializes Private metrics object required for this test case"""
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics.enable_metrics()
        self.internet = InternetOptions(self.commcell)
        self.gateway_client = Clients(self.commcell).get(self.tcinputs["GatewayClientName"])
        self.internet.set_internet_gateway_client(self.gateway_client.client_name)
        self.private_metrics_name = self.private_metrics.private_metrics_server_name
        self.metrics_server = MetricsServer(self.private_metrics_name,
                                            self.inputJSONnode['commcell']["commcellUsername"],
                                            self.inputJSONnode['commcell']["commcellPassword"])
        self.gateway_machine = Machine(
            machine_name=self.tcinputs["GatewayClientName"],
            commcell_object=self.commcell)
        self.license_details = LicenseDetails(self.commcell)
        
    def get_gateway_ip(self):
        return socket.gethostbyname(self.gateway_client.client_hostname)

    @test_step
    def validate_private_uploadnow(self):
        """Validates Private Metrics uploadNow operation """
        self.log.info('Initiating Private Metrics upload now')
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_uploadnow_completion()
        self.log.info('Private Metrics upload now completed Successfully')

    @test_step
    def validate_geteway_ip(self):
        """Validates gateway ip in CommCell info Page"""
        gateway_ip = self.get_gateway_ip()
        ip_from_db = self.metrics_server.get_commcell_upload_ip(self.license_details.commcell_id_hex)
        if gateway_ip != ip_from_db:
            raise CVTestStepFailure("Gateway IP [{0}] not matching from commcell info page [{1}]"
                                    .format(gateway_ip, ip_from_db)
                                    )

    @test_step
    def validate_upload_directory(self):
        """validate upload directory is empty"""
        upload_dir = self.gateway_machine.join_path(self.gateway_client.install_directory, "Reports",
                                                    "CommservSurvey", "privateupload")
        if self.gateway_machine.check_directory_exists(upload_dir):
            files = self.gateway_machine.get_files_in_path(upload_dir)
            if files:
                raise CVTestStepFailure(
                    "Upload directory is not [{0}] empty"
                    .format(upload_dir)
                    )
        else:
            self.log.info('Upload directory [{0}] is empty.'.format(upload_dir))

    def run(self):
        try:
            self.validate_private_uploadnow()
            self.metrics_server.wait_for_parsing(self.private_metrics.get_uploaded_filename())
            self.validate_geteway_ip()
            self.validate_upload_directory()
        except Exception as error:
            self.utils.handle_testcase_exception(error)

    def tear_down(self):
        """Tear down function of this test case"""
        self.internet.set_no_gateway()
