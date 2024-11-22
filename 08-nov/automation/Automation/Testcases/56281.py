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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import time

from cvpysdk.job import Job

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory


class TestCase(CVTestCase):
    """Class for executing INCR backup - followed by replication and Validation"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "VMW - Incremental Backup - After Backup Replication and Validation"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {
            "ReplicationGroup": None
        }
        self.browser = None
        self.replication_group = None
        self.admin_page_obj = None
        self.vsa_obj = None
        self.admin_console = None

    def _suspend_and_resume_job(self, job_id):
        """Function for suspend and resume job"""
        try:
            self.log.info(f"Getting status for the job {job_id}")
            self.log.info("Sleep for 30 Secs.")
            time.sleep(30)
            job_obj = Job(self.commcell, job_id)
            self.log.info(f"Suspend Job {job_id}")
            # Suspend job
            job_obj.pause(wait_for_job_to_pause=True)
            time.sleep(60)
            self.log.info(f"Resume Job {job_id}")
            # Resume Job
            job_obj.resume(wait_for_job_to_resume=True)
            if not job_obj.wait_for_completion():
                raise Exception(f"Failed to complete job with job ID: {job_obj.job_id}")
            else:
                self.log.info(f"Job with job id {job_obj.job_id} completed")
        except Exception as exp:
            self.log.exception(
                f"Exception occurred in getting the job status: {str(exp)}"
            )
            raise exp

    def setup(self):
        """Setup function for this testcase"""
        decorative_log("Initializing browser Objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login Object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance,
                                                 self.browser.driver,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.replication_group = self.tcinputs["ReplicationGroup"]
        self.admin_page_obj = self.admin_console.navigator

    def run(self):
        """Run function for this testcase"""
        try:
            decorative_log("Performing INCREMENTAL Backup")
            self.vsa_obj.backup_type = "INCREMENTAL"
            self.vsa_obj.backup()
        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)
            self.log.info(str(exp))
            raise exp

        try:
            self.log.info("Perform Live Sync Validation")
            replication_job_id = self.vsa_obj.get_replication_job(self.replication_group)
            self._suspend_and_resume_job(replication_job_id)
            self.vsa_obj.validate_live_sync(replication_group_name=self.replication_group)

        finally:
            self.vsa_obj.logout_command_center()
            self.browser.close()
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        """Teardown function for this testcase"""
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
