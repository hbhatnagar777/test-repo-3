# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case
"""

from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import DownloadOptions

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils.windows_machine import WindowsMachine
from Web.Common.page_object import handle_testcase_exception
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for downloading software job on non internet connected setup"""

    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Negative Scenario - Download on non internet connected setup"
        self.config_json = None
        self.machine_obj = None
        self.tcinputs = {
            "host": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.machine_obj = WindowsMachine(
            machine_name=self.commcell.commserv_name,
            commcell_object=self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:

            self.machine_obj.add_host_file_entry(ip_addr='127.0.0.1',
                                                 hostname=self.tcinputs["host"])

            job = self.commcell.download_software(
                options=DownloadOptions.LATEST_SERVICEPACK.value,
                os_list=[DownloadPackages.WINDOWS_64.value])
            self.log.info("Job %s started for downloading packages", job.job_id)
            JobManager(job, self.commcell).wait_for_state("failed")

            self.log.info("Removing incorrect host entry")
            self.machine_obj.remove_host_file_entry(hostname=self.tcinputs["host"])

            job = self.commcell.download_software(
                options=DownloadOptions.LATEST_SERVICEPACK.value,
                os_list=[DownloadPackages.WINDOWS_64.value])
            self.log.info("Job %s started for downloading packages", job.job_id)
            JobManager(job, self.commcell).wait_for_state()

        except Exception as exp:
            handle_testcase_exception(self, exp)
