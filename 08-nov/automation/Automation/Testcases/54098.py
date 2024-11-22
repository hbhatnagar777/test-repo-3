# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Store Workflow: Metrics upload workflow"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Reports.storeutils import StoreUtils
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.API.webconsole import Store
from cvpysdk.metricsreport import CloudMetrics
from cvpysdk.metricsreport import PrivateMetrics

_CONFIG = get_config()


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.util = StoreUtils(self)
        self.workflow_name = 'Metrics Upload'
        self.name = "metrics upload workflow"
        self.store_api = None
        self.cloud_metrics = None
        self.private_metrics = None
        self.webconsole = None

    def login_to_store(self):
        """Login to store"""
        self.store_api = Store(
            machine=self.commcell.webconsole_hostname,
            wc_uname=self.inputJSONnode['commcell']["commcellUsername"],
            wc_pass=self.inputJSONnode['commcell']["commcellPassword"],
            store_uname=_CONFIG.email.username,
            store_pass=_CONFIG.email.password)

    @test_step
    def install_workflow(self):
        """Installs the workflow"""
        if self.commcell.workflows.has_workflow(self.workflow_name):
            self.log.info("Deleting workflow [%s] using API", self.workflow_name)
            self.commcell.workflows.delete_workflow(self.workflow_name)
        self.store_api.install_workflow(self.workflow_name)

    def setup(self):
        """Test case Pre Configuration"""
        self.login_to_store()
        self.cloud_metrics = CloudMetrics(self.commcell)
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics.update_url(self.inputJSONnode['commcell']["webconsoleHostname"])
        self.private_metrics.save_config()

    @test_step
    def execute_workflow(self, isprivate):
        """Executes the workflow"""
        self.commcell.workflows.refresh()
        workflow = self.commcell.workflows.get(self.workflow_name)
        mtype = 'Private' if isprivate else 'Cloud'
        self.log.info(f"Executing workflow [{self.workflow_name}] for {mtype} metrics")
        inputs = {
            'Type': isprivate
        }
        output, job = workflow.execute_workflow(inputs)
        if not job.wait_for_completion(timeout=60):
                raise CVTestStepFailure(
                    f'workflow [{self.workflow_name}] job id {job.job_id} failed to complete'
                )

    @test_step
    def validate_metrics_upload(self, isprivate):
        """Validates metrics upload"""
        if not isprivate:
            self.log.info("Validating Cloud metrics upload")
            self.cloud_metrics.wait_for_uploadnow_completion()
        else:
            self.log.info("Validating Private metrics upload")
            self.private_metrics.wait_for_uploadnow_completion()

    def run(self):
        try:
            self.install_workflow()
            isprivate = 0
            self.execute_workflow(isprivate)
            self.validate_metrics_upload(isprivate)
            isprivate = 1
            self.execute_workflow(isprivate)
            self.validate_metrics_upload(isprivate)

        except Exception as err:
            self.util.handle_testcase_exception(err)
