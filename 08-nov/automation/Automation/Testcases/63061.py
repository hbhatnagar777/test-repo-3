# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" To verify Metrics Upload files are not deleted on upload failure """
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.API.customreports import CustomReportsAPI
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from cvpysdk.metricsreport import PrivateMetrics


class TestCase(CVTestCase):
    """
       TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.old_metrics_server = None
        self.utils = TestCaseUtils(self)
        self.cs_ip = None
        self.backup_jobid = None
        self.cre_api = None
        self.old_url = None
        self.commserv_client = None
        self.name = "Metrics Upload file are not deleted on Upload failure"
        self.cs_machine = None
        self.upload_dir = None
        self.private_metrics = None

    def setup(self):
        self.private_metrics = PrivateMetrics(self.commcell)
        self.commserv_client = self.commcell.commserv_client
        self.cs_machine = Machine(self.commserv_client)
        self.cs_ip = self.cs_machine.ip_address
        self.cre_api = CustomReportsAPI(self._inputJSONnode["commcell"]["webconsoleHostname"],
                                        username=self._inputJSONnode["commcell"]["commcellUsername"],
                                        password=self._inputJSONnode["commcell"]["commcellPassword"])
        self.upload_dir = self.cs_machine.join_path(self.commserv_client.install_directory, 'Reports',
                                                    'CommservSurvey', 'privateupload')

    def get_latest_job_details(self):
        query = "select ISNULL(MAX(jobid),0) as jobid from JMBkpStats WITH (NOLOCK)"
        result = self.cre_api.execute_sql(query)
        self.backup_jobid = str(result[0][0])
        self.log.info("backup job id:" + str(self.backup_jobid))

    def private_metrics_upload(self):
        self.log.info("Initiating Private Metrics Upload")
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_download_completion()
        self.private_metrics.wait_for_collection_completion()

    def modify_upload_url(self):
        invalid_url = 'http://bdcmetrics.invalid.url'
        self.old_url = self.private_metrics.uploadurl
        sql = f"UPDATE GXGlobalParam SET value='{invalid_url}' where name='CommservSurveyPrivateUploadsite'"
        self.utils.cs_db.execute(sql)

    def verify_upload_failed(self):
        if self.private_metrics.lastuploadtime > self.private_metrics.lastcollectiontime:
            raise CVTestStepFailure("Upload happened after last collection")

    def verify_upload_file_still_present(self):
        filename = self.private_metrics.get_uploaded_zip_filename(commserv_guid=self.commcell.commserv_guid,
                                                                  backupjob_id=self.backup_jobid)
        self.log.info(f"Last uploaded zip filename : {filename}")
        if not self.cs_machine.check_file_exists(self.cs_machine.join_path(self.upload_dir, filename)):
            raise CVTestStepFailure("Metrics Upload file got deleted")
        self.log.info("Upload file is present in PrivateUpload directory")

    def run(self):
        try:
            self.modify_upload_url()
            self.private_metrics.refresh()
            self.get_latest_job_details()
            self.private_metrics_upload()
            self.verify_upload_failed()
            self.verify_upload_file_still_present()
        finally:
            sql = f"UPDATE GXGlobalParam SET value='{self.old_url}' where name='CommservSurveyPrivateUploadsite'"
            self.utils.cs_db.execute(sql)

