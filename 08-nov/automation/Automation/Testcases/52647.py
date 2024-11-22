"""
TestCase to validate Metrics collection query upgrade script
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.metricsutils import MetricsServer

from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """TestCase to validate Metrics collection query upgrade script"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: verify metrics upgrade script"
        self.metrics_server = None

    def int_tc(self):
        self.metrics_server = MetricsServer(
            self.commcell.webconsole_hostname,
            self.inputJSONnode['commcell']["commcellUsername"],
            self.inputJSONnode['commcell']["commcellPassword"]
        )

    def get_enabled_offline_scripts(self):
        query = """
        SELECT CollectScriptName FROM cf_CommservSurveyQueries WITH (NOLOCK) 
        WHERE flags & 2 = 2 AND QueryId >= 10000"""
        result = self.metrics_server.metrics_server_api.execute_sql(
            query,
            database_name='CVCloud',
            desc='Getting enabled offline queries',
            connection_type="METRICS"
        )
        query_list = []
        for query in result:
            query_list.append(query[0])
        return query_list

    @test_step
    def verify_offline_query_exist(self, offline_scripts):
        """Verifies offline queries exist"""
        for script in offline_scripts:
            if not self.metrics_server.is_offline_query_exist(script):
                raise CVTestStepFailure(f'Offline query [{script}] not found in script directory')

    def run(self):
        self.int_tc()
        offline_scripts = self.get_enabled_offline_scripts()
        self.verify_offline_query_exist(offline_scripts)
