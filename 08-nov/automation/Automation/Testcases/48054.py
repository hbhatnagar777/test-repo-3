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
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from cvpysdk.metricsreport import PrivateMetrics
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.health_tiles import GenericTile
from Web.AdminConsole.Components.table import Rtable


class TestCase(CVTestCase):
    """Testcase to verify Metrics Scrubbing in CommServer"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.manage_reports = None
        self.health_tile_mountPath = None
        self.health_tile = None
        self.health = None
        self.admin_console = None
        self.utils = None
        self.name = "Metrics: Scrubbing in CommServer"
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.private_metrics = None
        self.private_metrics_name = None
        self.prune_db_tile = None
        self.viewer = None
        self.table = None

    def setup(self):
        """Intializes Private metrics object required for this testcase"""
        self.utils = TestCaseUtils(self, username=self.inputJSONnode['commcell']["commcellUsername"],
                                   password=self.inputJSONnode['commcell']["commcellPassword"])
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics_name = self.private_metrics.private_metrics_server_name
        self.private_metrics.enable_health()
        self.private_metrics.save_config()

    def init_commandcenter(self):
        """Initialize the application to the state required by the testcase"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.private_metrics_name)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.manage_reports = ManageReport(self.admin_console)
            self.health_tile = GenericTile(self.admin_console, 'Index Cache Location')
            self.health_tile_mountPath = GenericTile(self.admin_console, 'Mount Path')
        except Exception as msg:
            raise CVTestCaseInitFailure(msg) from msg

    @test_step
    def enable_scrubbing(self):
        """Enable scrubbing in CommCell"""
        cmd = "-sn SetKeyIntoGlobalParamTbl.sql -si CommservSurveyPrivateScrubPathInfo -si y -si 1"
        exec_command = self.commcell._services['EXECUTE_QSCRIPT'] % cmd
        self.commcell._cvpysdk_object.make_request("POST", exec_command)

    @test_step
    def disable_scrubbing(self):
        """Disable scrubbing in CommCell"""
        cmd = "-sn SetKeyIntoGlobalParamTbl.sql -si CommservSurveyPrivateScrubPathInfo -si n"
        exec_command = self.commcell._services['EXECUTE_QSCRIPT'] % cmd
        self.commcell._cvpysdk_object.make_request("POST", exec_command)

    @test_step
    def check_exclude_scrubbing(self):
        """check if CommservSurveyPrivateExcludeScrubList is present in gxglobalParam table"""
        query = "SELECT value FROM GxGlobalParam WHERE name " \
                "='CommservSurveyPrivateExcludeScrubList' and modified=0"
        response = self.utils.cre_api.execute_sql(query)
        if not response:
            raise CVTestStepFailure(
                "CommservSurveyPrivateExcludeScrubList is not set in the GxGlobalParam table. "
                " Set this value [<ExcludeScrubList><Name>MountPathName</Name></ExcludeScrubList>]"
                " in the GxGlobalParam table "
                " and rerun the testcase. "
            )

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
    def verify_exclude_scrubbing(self):
        """Verifies Scubbing is successfull and reflected in reports"""
        self.navigator.navigate_to_metrics()
        self.manage_reports.access_commcell_health(self.commcell.commserv_hostname.lower().split('.')[0])
        self.health_tile_mountPath.access_view_details()
        table = Rtable(self.admin_console)
        values = table.get_column_data('Mount Path')
        values = list(set(values))
        if len(values) != 1 and values[0] == 'Masked Data':
            raise CVTestStepFailure(
                "Mouth Path report mount path name is still masked even after setting exclusion "
                "in scrubbing."
            )

    def run(self):
        try:
            self.enable_scrubbing()
            self.check_exclude_scrubbing()
            self.utils.private_metrics_upload()
            self.init_commandcenter()
            self.verify_scrubbing()
            self.verify_exclude_scrubbing()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            self.disable_scrubbing()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
