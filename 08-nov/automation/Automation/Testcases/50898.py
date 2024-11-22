# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to run download and install service pack.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""

from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import DownloadOptions

from Install.install_helper import InstallHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Download and Install service pack and hotfixes"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Download Latest service pack and Push service Pack and Hotfixes Test Case"
        self.install_helper = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.install_helper = InstallHelper(self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:

            # calls the Download job
            job = self.commcell.download_software(
                options=DownloadOptions.LATEST_SERVICEPACK.value,
                os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value]
            )
            self.log.info("Job %s started for downloading packages", job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run download job with error: " + job.delay_reason
                )

            if job.status == "Completed w/ one or more errors":
                raise Exception("Job Completed with one or more errors please check the logs")

            self.log.info("Successfully finished Downloading packages")

            # calls the push service pack and hotfixes job
            job = self.commcell.push_servicepack_and_hotfix(
                all_client_computers=True,
                reboot_client=True,
                run_db_maintenance=False
            )
            self.log.info("Job %s started for Installing packages", job.job_id)

            try:

                job.wait_for_completion()

            except Exception:
                self.install_helper.wait_for_services()

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run Install job with error: " + job.delay_reason
                )

            if job.status == "Completed w/ one or more errors":
                raise Exception("Job Completed with one or more errors please check the logs")

            self.log.info("Successfully finished Installing packages")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
