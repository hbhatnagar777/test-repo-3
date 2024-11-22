# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase to verify Scrubbing in CommServer
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.metricsutils import MetricsServer
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Reports.health_tiles import GenericTile
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from cvpysdk.metricsreport import PrivateMetrics

class TestCase(CVTestCase):
    """Testcase to verify Scrubbing on tiered metrics"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.metrics_webserver = None
        self.manage_reports = None
        self.admin_console = None
        self.name = "Metrics: Scrubbing on tiered metrics"
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.private_metrics = None
        self.private_metrics_name = None
        self.prune_db_tile = None
        self.tcinputs = {
            "TieredMetricsServer": None
        }
        self.machine = None
        self.old_file = None
        self.new_file = None
        self.tieredmetrics_server = None
        self.health_tile = None
        self.health_tile_mountPath = None
        self.metrics_user_name = None
        self.metrics_password = None
        self.viewer = None
        self.table = None

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        self.tieredmetrics_server = self.tcinputs["TieredMetricsServer"]
        self.old_file = "HttpServer_orig.xml"
        self.new_file = "HttpServer.xml"
        self.metrics_user_name = self.tcinputs["MetericsUser"]
        self.metrics_password = self.tcinputs["MetricsPassword"]
        self.utils = TestCaseUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                   password=self.inputJSONnode['commcell']['commcellPassword'])

    def setup(self):
        """Intializes Private metrics object required for this testcase"""
        self.private_metrics = PrivateMetrics(self.commcell)
        self.metrics_server = MetricsServer(self.private_metrics.private_metrics_server_name,
                                            self.inputJSONnode['commcell']["commcellUsername"],
                                            self.inputJSONnode['commcell']["commcellPassword"])
        self.metrics_webserver = self.commcell.clients.get(self.metrics_server.webserver_name)
        self.machine = self.metrics_server.metrics_machine
        self.private_metrics_name = self.private_metrics.private_metrics_server_name
        self.private_metrics.enable_health()
        self.private_metrics.save_config()

    def init_adminconsole(self):
        """Initialize the application to the state required by the testcase"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.tieredmetrics_server)
            self.admin_console.login(self.metrics_user_name, self.metrics_password)
            self.navigator = self.admin_console.navigator
            self.manage_reports = ManageReport(self.admin_console)
            self.health_tile = GenericTile(self.admin_console, 'Index Cache Location')
        except Exception as msg:
            raise CVTestCaseInitFailure(msg) from msg

    @test_step
    def verify_scrubbing(self):
        """Verifies Scubbing is successfull and reflected in reports"""
        self.navigator.navigate_to_metrics()
        self.manage_reports.access_commcell_health(self.commcell.commserv_hostname.lower().split('.')[0])
        self.health_tile.access_view_details()
        table = Rtable(self.admin_console)
        values = table.get_column_data('Index Cache Path')
        allowed_values = ['Masked Data', 'None']
        if set(values).difference(set(allowed_values)):
            raise CVTestStepFailure(
                "Index cache location report path info is not masked. "
                f"expected data in path [Masked Data] received data {values}"
            )

    @test_step
    def reinitialize_metrics(self):
        """Reinitialize metrics Params"""
        sql = "UPDATE cf_surveyconfig set value = '1' where name = 'ReinitializeMetricsParameters'"
        self.utils.cre_api.execute_sql(sql, database_name="CVCloud", connection_type='METRICS')

    def run(self):
        try:
            self.init_tc()
            self.old_file = self.machine.join_path(self.metrics_webserver.install_directory, "Reports",
                                                   "MetricsUpload",
                                                   self.old_file)
            self.new_file = self.machine.join_path(self.metrics_webserver.install_directory, "Reports",
                                                   "MetricsUpload",
                                                   self.new_file)
            self.machine.rename_file_or_folder(self.old_file, self.new_file)
            self.reinitialize_metrics()
            self.utils.private_metrics_upload()
            self.init_adminconsole()
            self.verify_scrubbing()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            self.machine.rename_file_or_folder(self.new_file, self.old_file)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
