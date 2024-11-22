# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initialize TestCase class

    setup()                 --  initial settings for the test case

    run()                   --  run function of this test case
"""

# Test Suite imports
from base64 import b64encode
from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import DownloadOptions
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing of App Mgr Node package installation testcase """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify Application manager Node package installation"
        self.tcinputs = {
            "ClientHostName": None,
            "ClientUserName": None,
            "ClientPassword": None,
        }

    def setup(self):
        """Setup function of this testcase"""

        self.server = ServerTestCases(self)

    def run(self):
        """Main function for test case execution"""

        try:

            download_job = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.WINDOWS_64.value])
            self.log.info("Job %s started for Windows packages",
                          download_job.job_id)

            if not download_job.wait_for_completion():
                raise Exception("Failed to run download job with error: %s",
                                download_job.delay_reason)

            if download_job.status == "Completed w/ one or more errors":
                raise Exception("Job Completed with one or more errors")

            self.log.info("Successfully finished Downloading packages")

            install_job = self.commcell.install_software(
                client_computers=[self.tcinputs["ClientHostName"]],
                windows_features=[WindowsDownloadFeatures.COMMSERVE_LITE.value],
                unix_features=None,
                username=self.tcinputs["ClientUserName"],
                password=b64encode(self.tcinputs["ClientPassword"].encode()).decode()
                )
            self.log.info("Job %s started for Installing Client",
                          install_job.job_id)

            if not install_job.wait_for_completion():
                raise Exception("Failed to run Install job with error: %s",
                                install_job.delay_reason)

            if install_job.status == "Completed w/ one or more errors":
                raise Exception("Job Completed with one or more errors")

            self.log.info("Successfully finished Installing Client")

        except Exception as excp:
            self.server.fail(excp)
