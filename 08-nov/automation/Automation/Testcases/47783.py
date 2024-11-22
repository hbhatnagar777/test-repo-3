# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase to verify Tiered architecture for private metrics server

TestCase:
    __init__()                                 --  initialize TestCase class
    init_tc()                                  --  Initialize pre-requisites
    reinitialize_metrics()                     --  re intialize metrics global parameter value
    verify_forwarding()                        --  verfiy forwarding is working
    run()                                      --  run function of this test case
Input Example:

    "testCases":
            {
                "47783":
                        {
                           "TieredMetricsServer": "metrics_server"
                        }
            }


"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer
from Web.Common.page_object import TestStep
from cvpysdk.metricsreport import PrivateMetrics
from urllib.parse import urlparse

class TestCase(CVTestCase):
    """Testcase to verify Tiered architecture for private metrics server"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Tiered architecture for private metrics server"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.private_metrics = None
        self.private_metrics_name = None
        self.prune_db_tile = None
        self.tcinputs = {
            "TieredMetricsServer": None,
            "TieredMetricsServerUser": None,
            "TieredMetricsServerPwd": None
        }
        self.machine = None
        self.tieredmetrics_server_name = None
        self.tieredmetrics_server = None

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        self.tieredmetrics_server_name = urlparse(self.tcinputs["TieredMetricsServer"]).hostname
        self.machine = Machine(self.commcell.commserv_client)
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics_name = self.private_metrics.private_metrics_server_name
        self.private_metrics.enable_health()
        forwarding_url = self.tcinputs["TieredMetricsServer"]
        self.private_metrics.enable_forwarding(forwarding_url)
        self.private_metrics.save_config()
        self.tieredmetrics_server = MetricsServer(self.tieredmetrics_server_name,
                                                  self.tcinputs["TieredMetricsServerUser"],
                                                  self.tcinputs["TieredMetricsServerPwd"])
        self.utils = TestCaseUtils(self, self.inputJSONnode["commcell"]["commcellUsername"],
                                   self.inputJSONnode["commcell"]["commcellPassword"])

    @test_step
    def verify_forwarding(self):
        """Verifies forwarding is working"""
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_uploadnow_completion()
        self.tieredmetrics_server.wait_for_parsing(self.private_metrics.get_uploaded_filename())

    @test_step
    def reinitialize_metrics(self):
        """Reinitialize metrics Params"""
        sql = "UPDATE cf_surveyconfig set value = '1' where name = 'ReinitializeMetricsParameters'"
        self.utils.cre_api.execute_sql(sql, database_name="CVCloud", connection_type='METRICS')

    def run(self):
        try:
            self.init_tc()
            self.reinitialize_metrics()
            self.verify_forwarding()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            self.private_metrics.disable_forwarding()
