# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  initialize TestCase class
    init_tc()                               --  Initialize pre-requisites
    private_upload_from_cs()                --  method for private metrics upload
    check_file_in_metrics()                 --  method to check file processing
    verify_blocked_commcell()               --  method to verify blockedIPs feature
    verify_failed_commcell()                --  method to verify failed with restrict commcellID
    run()                                   --  run function of this test case
Input Example:

    "testCases":
            {
                "47925":
                        {
                           "RemoteCommcellName": "commcell",
                           "RemoteCommcellUser" : "Commcell User",
                           "RemoteCommcellPwd" : "Commcell Password"
                        }
            }


"""
import os
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.API.customreports import CustomReportsAPI
from cvpysdk.metricsreport import PrivateMetrics
from cvpysdk.commcell import Commcell

_CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """Metrics: acceptance of Metrics Driver"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.remote_commcell_ip = None
        self.name = "Metrics: acceptance of Metrics Driver"
        self.private_metrics_upload = None
        self.metrics_server = None
        self.commcell_obj = None
        self.commserv_client = None
        self.machine = None
        self.utils = None
        self.tcinputs = {
            "RemoteCommcellName": None,
            "RemoteCommcellUser": None,
            "RemoteCommcellPwd": None
        }
        self.current_wc = None
        self.blockedips_file = None
        self.commcell_id = None
        self.namemap_id = None
        self.commserv_guid = None
        self.backup_jobid = None
        self.cre_api = None
        self.blocked_file = None

    def init_tc(self):
        """Intializes Private metrics object required for this testcase"""
        self.utils = TestCaseUtils(self, self.inputJSONnode["commcell"]["commcellUsername"],
                                   self.inputJSONnode["commcell"]["commcellPassword"])
        self.commcell_obj = Commcell(self.tcinputs["RemoteCommcellName"],
                                     self.tcinputs["RemoteCommcellUser"],
                                     self.tcinputs["RemoteCommcellPwd"], verify_ssl=False)
        cs_machine = Machine(self.commcell_obj.commserv_name, self.commcell_obj)
        self.remote_commcell_ip = cs_machine.ip_address
        self.private_metrics_upload = PrivateMetrics(self.commcell_obj)
        self.private_metrics_upload.update_url(self.commcell.webconsole_hostname)
        self.private_metrics_upload.enable_all_services()
        self.metrics_server = MetricsServer(self.commcell.webconsole_hostname,
                                            self.inputJSONnode["commcell"]["commcellUsername"],
                                            self.inputJSONnode["commcell"]["commcellPassword"])
        self.metrics_server_machine = self.metrics_server.metrics_machine
        self.blockedips_file = self.metrics_server_machine.join_path(self.commcell.commserv_client.install_directory,
                                            "Reports",
                                            "MetricsUpload", "BlockedIPs.txt")
        self.cre_api = CustomReportsAPI(self.tcinputs["RemoteCommcellName"],
                                        username=self.tcinputs["RemoteCommcellUser"],
                                        password=self.tcinputs["RemoteCommcellPwd"])

    @test_step
    def reinitialize_metrics(self):
        """Reinitialize metrics Params"""
        sql = "UPDATE cf_surveyconfig set value = '1' where name = 'ReinitializeMetricsParameters'"
        self.utils.cre_api.execute_sql(sql, database_name="CVCloud", connection_type='METRICS')

    @test_step
    def private_upload_from_cs(self):
        """Validates Private Metrics uploadNow operation """
        self.log.info('Initiating Private Metrics upload now')
        self.private_metrics_upload.upload_now()
        self.private_metrics_upload.wait_for_uploadnow_completion()
        self.log.info('Private Metrics upload now completed Successfully')

    @test_step
    def check_file_in_metrics(self):
        """Verify uploaded file reached metrics server"""
        try:
            self.metrics_server.wait_for_parsing(self.private_metrics_upload.get_uploaded_filename())
        except TimeoutError:
            raise CVTestStepFailure(
                f" uploaded file [{self.private_metrics_upload.get_uploaded_filename()}] "
                f" didn't reach Metrics server '{self.metrics_server.webserver_name}'"
            )

    @test_step
    def verify_blocked_commcell(self):
        """verify blocked commcell is present in blocked folder"""

        self.metrics_server.metrics_machine.create_file(self.blockedips_file,
                                                        self.remote_commcell_ip)
        self.reinitialize_metrics()
        self.private_upload_from_cs()
        self.blocked_file = self.private_metrics_upload.get_uploaded_zip_filename(commserv_guid=self.commserv_guid,
                                                                                  backupjob_id=self.backup_jobid)
        try:
            self.metrics_server.wait_for_xml_blocked(self.blocked_file)
        except TimeoutError:
            raise CVTestStepFailure(
                f" uploaded file [{self.blocked_file}] "
                f" not present in the blocked folder "
            )

    def init_commcell_details(self):
        """initialzie commcell details"""
        ccquery = (f"select CommCellID, ID, CommservGUID from CVCloud..cf_CommcellIdNameMap WITH (NOLOCK) "
                   f"where CommServIP = '{self.remote_commcell_ip}'")
        self.log.info("Executing Query:" + ccquery)
        result = self.utils.cre_api.execute_sql(
            ccquery,
            database_name="CVCloud",
            desc="Getting commcell id from cf_CommcellIdNameMap table",
            connection_type='METRICS')
        self.commcell_id = str(result[0][0])
        self.namemap_id = str(result[0][1])
        self.commserv_guid = str(result[0][2])
        query = "select ISNULL(MAX(jobid),0) as jobid from JMBkpStats WITH (NOLOCK)"
        result = self.cre_api.execute_sql(query)
        self.backup_jobid = str(result[0][0])
        self.log.info("backup job id:" + str(self.backup_jobid))

    def update_restricted_commcell(self):
        """ udpate restricted commcell entry"""

        update_query = (
            f"update CVCloud..cf_SurveyConfig set Value ='CommCellId={self.commcell_id};"
            f"CommcellIP={self.remote_commcell_ip};IdNamemapID={self.namemap_id}' "
            f"where Name ='Restrict_CommCellid1'"
        )

        self.log.info("Executing Query:" + update_query)
        self.utils.cre_api.execute_sql(update_query, database_name="CVCloud", connection_type='METRICS')

    def create_restricted_commcell(self):
        """ udpate restricted commcell entry"""

        update_query = (
            f"insert into CVCloud..cf_SurveyConfig (Name, Value) values "
            f"('Restrict_CommCellid1', 'CommCellId={self.commcell_id};"
            f"CommcellIP=172.16.196.113;IdNamemapID={self.namemap_id}')"
        )
        self.log.info("Executing Query:" + update_query)
        self.utils.cre_api.execute_sql(update_query, database_name="CVCloud", connection_type='METRICS')

    def delete_restricted_commcell(self):
        """delete restricted commcell"""
        delete_query = "delete from CVCloud..cf_SurveyConfig where Name = 'Restrict_CommCellid1'"
        self.log.info("Executing Query:" + delete_query)
        self.utils.cre_api.execute_sql(delete_query, database_name="CVCloud", connection_type='METRICS')

    @test_step
    def verify_failed_commcell(self):
        """verify restrict commcell id with wrong ip for failed case"""
        self.create_restricted_commcell()
        self.reinitialize_metrics()
        self.private_upload_from_cs()
        try:
            self.metrics_server.wait_for_xml_failed(self.private_metrics_upload.get_uploaded_filename())
        except TimeoutError:
            raise CVTestStepFailure(
                f" uploaded file [{self.private_metrics_upload.get_uploaded_filename()}] "
                f" not present in the failed folder "
            )
        self.log.info("verify restrict commcell id with correct ip for success case")
        self.update_restricted_commcell()
        self.reinitialize_metrics()
        self.private_upload_from_cs()
        self.check_file_in_metrics()

    def run(self):
        try:
            self.init_tc()
            self.reinitialize_metrics()
            self.private_upload_from_cs()
            self.check_file_in_metrics()
            self.init_commcell_details()
            self.verify_blocked_commcell()
            self.metrics_server.metrics_machine.delete_file(self.blockedips_file)
            """self.verify_failed_commcell()"""

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            self.metrics_server.metrics_machine.delete_file(self.blockedips_file)
            self.delete_restricted_commcell()
            self.reinitialize_metrics()
