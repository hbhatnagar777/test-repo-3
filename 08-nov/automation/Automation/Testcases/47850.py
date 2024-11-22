""""
TestCase to validate Metrics Client Group selection for Collection.
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer

from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.health import Health

from cvpysdk.metricsreport import PrivateMetrics


class TestCase(CVTestCase):
    """TestCase to validate Metrics Client Group selection for Collection. """

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Select Client Group for Private metrics Collection"
        self.show_to_user = True
        self.private_metrics = None
        self.tcinputs = {
            "clientgroup_names": None,  # this can be a comma separated entry
        }
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.health = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        """Initializes Private metrics object required for this test case"""
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics.enable_all_services()
        self.input_group_names = self.tcinputs["clientgroup_names"].split(',')
        self.private_metrics.set_clientgroups(self.input_group_names)
        self.private_metrics_name = self.private_metrics.private_metrics_server_name
        self.metrics_server = MetricsServer(self.private_metrics_name,
                                            self.inputJSONnode['commcell']["commcellUsername"],
                                            self.inputJSONnode['commcell']["commcellPassword"])

    def init_webconsole(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.private_metrics_name)
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_commcell_dashboard()
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_commcell_dashboard(self.commcell.commserv_name)
            self.navigator.goto_health_report()
            self.health = Health(self.webconsole)

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def validate_private_uploadnow(self):
        """Validates Private Metrics uploadNow operation """
        self.log.info('Initiating Private Metrics upload now')
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_uploadnow_completion()
        self.log.info('Private Metrics upload now completed Successfully')

    def get_group_in_webconsole(self):
        self.init_webconsole()
        return self.health.get_client_group_names()

    @test_step
    def validate_group_in_webconsole(self):
        """Validates group name present in webconsole"""
        groups_in_wc = self.get_group_in_webconsole()
        if groups_in_wc != self.input_group_names:
            raise CVTestStepFailure("Client Groups in Health page [{0}] not matching from"
                                    " expected group names[{1}]"
                                    .format(groups_in_wc, self.input_group_names)
                                    )

    def run(self):
        try:
            self.validate_private_uploadnow()
            self.metrics_server.wait_for_parsing(self.private_metrics.get_uploaded_filename())
            self.validate_group_in_webconsole()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        self.private_metrics.set_clientgroups()  # to set back all clients groups
        self.private_metrics.save_config()
