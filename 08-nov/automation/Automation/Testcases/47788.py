# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase to verify Health report tile Prune database agent log
"""


from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.health import HealthConstants
from Web.WebConsole.Reports.Metrics.health_tiles import PruneDBAgentLogs

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure

from cvpysdk.metricsreport import PrivateMetrics


class TestCase(CVTestCase):
    """Testcase to verify Health report tile Prune database agent log"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics Health - Prune Database Agent Logs"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.private_metrics = None
        self.private_metrics_name = None
        self.prune_db_tile = None

    def setup(self):
        """Intializes Private metrics object required for this testcase"""
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics_name = self.private_metrics.private_metrics_server_name
        self.private_metrics.enable_health()
        self.private_metrics.save_config()

    def init_webconsole(self):
        """Initialize the application to the state required by the testcase"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.private_metrics_name)
            self.webconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.webconsole.goto_reports()
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_commcell_dashboard(self.commcell.commserv_name)
            self.prune_db_tile = PruneDBAgentLogs(self.webconsole)
        except Exception as msg:
            raise CVTestCaseInitFailure(msg) from msg

    def update_prune_db_log_setting(self, enabled=1):
        """updates prune DB log settings in MA configs table"""
        query = '''update MMConfigs
        SET value=%d  
        WHERE name = 'DA_CONFIG_PRUNE_ALL_DB_AGENT_LOGS_BY_DAYS_ONLY_RETENTION' 
        ''' % enabled
        self.utils.cre_api.execute_sql(
            query,
            desc='updating prune DB log settings in MA configs table'
        )

    @test_step
    def validate_good_status(self):
        """Validate good status is shown in Prune DB Agent log Tile"""
        self.navigator.goto_health_report()
        visible_status = self.prune_db_tile.get_health_status()
        if visible_status != HealthConstants.STATUS_GOOD:
            raise CVTestStepFailure(
                "Prune DB agent Tile not in [{0}] Status, visible status is [{1}]"
                .format(HealthConstants.STATUS_GOOD, visible_status)
            )
        if self.prune_db_tile.is_disabled() is False:  # outcome should be disabled status
            raise CVTestStepFailure(
                "Prune DB agent Tile outcome not in Disabled Status"
            )

    @test_step
    def validate_critical_status(self):
        """Validate critical status is shown in Prune DB Agent log Tile"""
        self.navigator.goto_health_report()
        visible_status = self.prune_db_tile.get_health_status()
        if visible_status != HealthConstants.STATUS_CRITICAL:
            raise CVTestStepFailure(
                "Prune DB agent Tile not in [{0}] Status, visible status is [{1}]"
                .format(HealthConstants.STATUS_CRITICAL, visible_status)
            )
        if self.prune_db_tile.is_disabled() is True:  # outcome should be Enabled status
            raise CVTestStepFailure(
                "Prune DB agent Tile outcome not in Enabled Status"
            )

    def run(self):
        try:
            self.init_webconsole()
            self.update_prune_db_log_setting(enabled=1)
            self.utils.private_metrics_upload()
            self.validate_critical_status()
            self.update_prune_db_log_setting(enabled=0)
            self.utils.private_metrics_upload()
            self.validate_good_status()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
