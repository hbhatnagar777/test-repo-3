# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase to verify backward compatibility of Metrics Collection queries
Input Example:

    "testCases":
            {
                "50786":
                {
                    "v11_CS" :
                    [
                        {
                           "Commcell": "commcell1",
                           "CommcellUser": "Commcell User",
                           "CommcellPwd" : "Commcell Pwd"
                        },
                        {
                           "Commcell": "commcell2",
                           "CommcellUser": "Commcell User",
                           "CommcellPwd" : "Commcell Pwd"
                        }
                    ],
                    "email_receiver" : "email@example.com"
                }
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mailer import Mailer
from AutomationUtils import config

from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer
from cvpysdk.commcell import Commcell
from cvpysdk.metricsreport import CloudMetrics
from AutomationUtils import constants as cv_constants
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

_CONSTANTS = config.get_config()


class CommCellObj:
    """
    Class with required objects for commcells used in this testcase
    """

    def __init__(self, commcell_obj, cloud_metrics):
        self.commcell = commcell_obj
        self.cloud_metrics = cloud_metrics


class TestCase(CVTestCase):
    """Testcase to verify backward compatibility of Metrics Collection queries"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Public Metrics: Collection queries backward compatibility"
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "v11_CS": None,  # comma seperated value for multi commcells
            "email_receiver": None
        }
        self.config = config.get_config()
        self.cloud_metrics_server = self.config.Cloud
        self.commcell_list = []
        self.mailer = None
        self.email_receiver = None

    def create_objects(self, commcell):
        """method to create required objects with the inputs"""
        self.log.info(f"Connecting to Commcell {commcell['Commcell']}")
        commcell_obj = Commcell(commcell['Commcell'], commcell['CommcellUser'], commcell['CommcellPwd'],
                                verify_ssl=False)
        self.log.info(f"Getting CloudMetrics object of Commcell {commcell['Commcell']}")
        return CommCellObj(commcell_obj, CloudMetrics(commcell_obj))

    def init_tc(self):
        """Initialize the application to the state required by the testcase"""
        try:
            commcells = self.tcinputs["v11_CS"]
            self.commcell_list.extend(
                list(map(self.create_objects, commcells))
            )
            self.cloud_metrics_server = MetricsServer(self.cloud_metrics_server.host_name,
                                                      self.cloud_metrics_server.username,
                                                      self.cloud_metrics_server.password)
            self.email_receiver = self.tcinputs["email_receiver"]
            self.mailer = Mailer({'receiver': self.email_receiver}, self.commcell)
        except Exception as msg:
            raise CVTestCaseInitFailure(msg) from msg

    @test_step
    def intiate_public_uploadnow(self):
        """Validates Cloud Metrics uploadNow operation"""
        for cc_obj in self.commcell_list:
            self.log.info(
                f'Initiating Cloud  Metrics upload Now in [{cc_obj.commcell.commserv_name}]'
            )
            cc_obj.cloud_metrics.enable_all_services()
            cc_obj.cloud_metrics.upload_now()

    @test_step
    def wait_for_upload_completion(self):
        """Wait for upload completion"""
        for cc_obj in self.commcell_list:
            try:
                self.log.info(f"Waiting for upload completion for [{cc_obj.commcell.commserv_name}] cs")
                cc_obj.cloud_metrics.wait_for_uploadnow_completion(collection_timeout=20 * 60)
                self.log.info(f'Cloud  Metrics Upload completed in [{cc_obj.commcell.commserv_name}]')
            except TimeoutError as timeout_error:
                self.status = cv_constants.FAILED
                self.result_string += f"upload failure from [{cc_obj.commcell.commserv_name}] cs \n"
                self.log.exception(f"upload failure from [{cc_obj.commcell.commserv_name}] cs "
                                   f"with reason {timeout_error}")

    @test_step
    def wait_for_parsing_completion(self):
        """Wait for parsing completion in metrics server"""
        for cc_obj in self.commcell_list:
            try:
                self.cloud_metrics_server.wait_for_parsing(
                    cc_obj.cloud_metrics.get_uploaded_filename()
                )
                self.log.info(
                    f'Commcell [{cc_obj.commcell.commserv_name}] parsed in metrics server')
            except TimeoutError:
                self.status = cv_constants.FAILED
                self.result_string += f"Parsing did not complete for CS {cc_obj.commcell.commserv_name} \n"
                self.log.exception(f"Parsing did not complete for CS {cc_obj.commcell.commserv_name}")

    @staticmethod
    def create_parsing_error_table(parsing_failures):
        """Creates the table to sent in Email for parsing errors"""
        failure_msg = '''
        <p>Below is the list of parsing Failures in Metrics server </p>
        <table  border="1"><tr><th>Message</th></tr>
        '''
        for message in parsing_failures:
            failure_msg += '<tr><td>'
            failure_msg += message[0]
            failure_msg += '</td>'
            failure_msg += '</tr>'

        failure_msg += '</table>'
        return failure_msg

    @staticmethod
    def create_collection_errors_table(collection_failures):
        """Creates the table to sent in Email for Collection errors"""
        failure_msg = '''
        <p>Below is the list of Failure Messages From the Collection Query</p>
        <table  border="1"><tr><th width="18%">CommCell Id</th>
        <th>QueryId</th><th width="60%">Message</th></tr>
        '''
        for failures in collection_failures:
            failure_msg += '<tr><td>'

            failure_msg += str(failures['ccid'])
            failure_msg += '</td><td>'

            failure_msg += str(failures['queryid'])
            failure_msg += '</td><td>'

            failure_msg += str(failures['error'])
            failure_msg += '</td></tr>'

        failure_msg += '</table>'
        return failure_msg

    @test_step
    def check_collection_errors(self):
        """Look for collection errors in metrics server in last 1 day"""
        errors = self.cloud_metrics_server.get_collection_errors(days=1)
        if errors:
            self.status = cv_constants.FAILED
            self.result_string += "Collection Errors exist in past day \n"
            self.log.error('MCollection Errors exist in past day')
            self.mailer.mail("Metrics Collection Error on " + self.commcell.webconsole_hostname,
                             self.create_collection_errors_table(errors))


    @test_step
    def check_parsing_errors(self):
        """Look for parsing errors in metrics server in last 1 day"""
        query = """
        SELECT Message FROM CVCloud..cf_SurveyLogger WITH (NOLOCK)
        WHERE (Message like '%failed to%' or Message like '%parsing failed%' or 
        Message like '%Failed with%' or Message like '%Failed in%')
        and LogDateUTC >(GETUTCDATE()-1) order by LogDateUTC desc
        """
        errors = self.cloud_metrics_server.metrics_server_api.execute_sql(
            query,
            database_name="CVCloud",
            desc='Getting parsing failed logs from cf_SurveyLogger table',
            connection_type='METRICS'
        )
        if errors:
            self.status = cv_constants.FAILED
            self.result_string += "Parsing Errors exist for last 1 day \n"
            self.log.error('Parsing Errors exist for last 1 day')
            self.mailer.mail("Parsing Error on " + self.commcell.webconsole_hostname,
                             self.create_parsing_error_table(errors))

    def run(self):
        try:
            self.init_tc()
            self.intiate_public_uploadnow()
            self.wait_for_upload_completion()
            self.wait_for_parsing_completion()
            self.check_collection_errors()
            self.check_parsing_errors()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
