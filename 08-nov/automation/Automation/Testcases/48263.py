# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase to look for any collection errors in Metrics server
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mailer import Mailer

from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Testcase to look for any collection errors in Metrics server"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Look for any collection errors"
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "email_receiver": None
        }
        self.metrics_server = None
        self.mailer = None
        self.email_receiver = None

    def init_tc(self):
        """Initialize the application to the state required by the testcase"""
        try:
            self.metrics_server = MetricsServer(
                self.commcell.webconsole_hostname,
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.email_receiver = self.tcinputs["email_receiver"]
            self.mailer = Mailer({'receiver': self.email_receiver}, self.commcell)
        except Exception as msg:
            raise CVTestCaseInitFailure(msg) from msg

    @staticmethod
    def create_collection_errors_table(collection_failures):
        """Creates the table to sent in Email for Collection errors"""
        failure_msg = '''
        <p>Below is the list of Failure Messages From the Collection Query</p>
        <table  border="1"><tr><th width="18%">CommCell Id</th>
        <th>Version</th><th>QueryId</th><th>Report Name</th><th width="60%">Message</th></tr>
        '''
        for failures in collection_failures:
            failure_msg += '<tr><td>'

            failure_msg += str(failures['ccid'])
            failure_msg += '</td><td>'

            failure_msg += str(failures['Version'])
            failure_msg += '</td><td>'

            failure_msg += str(failures['queryid'])
            failure_msg += '</td><td>'

            failure_msg += str(failures['report_name'])
            failure_msg += '</td><td>'

            failure_msg += str(failures['error'])
            failure_msg += '</td></tr>'

        failure_msg += '</table>'
        return failure_msg

    @test_step
    def check_collection_errors(self):
        """Look for collection errors in metrics server in last 1 day"""
        errors = self.metrics_server.get_collection_errors(days=1)
        if errors:
            self.log.error('Mailing Collection Errors')
            self.mailer.mail("Metrics Collection Error on " + self.commcell.webconsole_hostname,
                             self.create_collection_errors_table(errors))
            raise CVTestStepFailure('Collection Errors exist for last 1 day')

    def run(self):
        try:
            self.init_tc()
            self.check_collection_errors()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
