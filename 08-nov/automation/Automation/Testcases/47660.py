# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase to look for any Parsing errors in Metrics server
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mailer import Mailer

from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Testcase to look for any Parsing errors in Metrics server"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Check parsing errors in Metrics server"
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
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'],
            )
            self.email_receiver = self.tcinputs["email_receiver"]
            self.mailer = Mailer({'receiver': self.email_receiver}, self.commcell)
        except Exception as msg:
            raise CVTestCaseInitFailure(msg) from msg

    def create_parsing_error_table(self, parsing_failures):
        """Creates the table to sent in Email for parsing errors"""
        failure_msg = '''
        <p>Below is the list of parsing Failures in Metrics server </p>
        <table  border="1"><tr><th>CommCell ID</th><th>Version</th><th>Query ID</th>
        <th>Name</th><th>Message</th></tr>
        '''
        url = (
            "http://" + self.commcell.webconsole_hostname +
            '/webconsole/survey/reports/dashboard.jsp?commUniId=%s'
        )
        for message in parsing_failures:
            failure_msg += '<tr><td>'
            ccid = hex(int(message[1])).split('0x')[1].upper()
            failure_msg += f"<a href='{url % message[0]}'>{ccid}</a>"
            failure_msg += '</td><td>'
            failure_msg += message[2]
            failure_msg += '</td><td>'
            failure_msg += message[3]
            failure_msg += '</td><td>'
            failure_msg += message[4]
            failure_msg += '</td><td>'
            failure_msg += message[5]
            failure_msg += '</td>'

            failure_msg += '</tr>'

        failure_msg += '</table>'
        return failure_msg

    @test_step
    def check_parsing_errors(self):
        """Look for collection errors in metrics server in last 1 day"""
        query = """
        DECLARE @process_error table (CommCellUniqueId varchar(150),queryid varchar(50), result varchar(50), Message varchar(max))
        INSERT INTO @process_error
            SELECT	SUBSTRING(message, CHARINDEX('CSUniqueId:', message)+12,CHARINDEX(') - ', message) -  (CHARINDEX('CSUniqueId:', message)+12)) as 'CommCell UniqueId',
            SUBSTRING(message, CHARINDEX('QueryId: ', message)+9, CHARINDEX(' CSUniqueId:', message) -  (CHARINDEX('QueryId: ', message)+10)) as 'queryid', 
            SUBSTRING(message, CHARINDEX('Parsing result', message)+15,8) as 'result', 
            message
            FROM cf_SurveyLogger WITH (NOLOCK)
            WHERE (Message like '%failed to%' or Message like '%parsing failed%' or 
                    Message like '%Failed with%' or Message like '%Failed in%') and LogDateUTC >(GETUTCDATE()-1 ) 
            order by LogDateUTC desc

        SELECT  pr.CommCellUniqueId,
                cc.CommCellID as 'CommCellID',
                cc.CommServVersion,
                pr.queryid as 'Query ID',
                qr.name as 'Query Name',
                pr.Message
        FROM @process_error pr left outer join cf_CommcellIdNameMap cc
        on pr.commcellUniqueId=cc.id
        left outer join cf_commservsurveyqueries qr
        on pr.queryid = qr.queryid
        """
        errors = self.metrics_server.metrics_server_api.execute_sql(
            query,
            database_name="CVCloud",
            desc='Getting parsing failed logs from cf_SurveyLogger table',
            connection_type='METRICS'
        )
        if errors:
            self.log.error('Mailing parsing Errors')
            self.mailer.mail("Parsing Error on " + self.commcell.webconsole_hostname,
                             self.create_parsing_error_table(errors))
            raise CVTestStepFailure('Parsing Errors exist for last 1 day')

    def run(self):
        try:
            self.init_tc()
            self.check_parsing_errors()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
