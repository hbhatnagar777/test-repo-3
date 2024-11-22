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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from Install.install_validator import InstallValidator
from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import DownloadOptions


class TestCase(CVTestCase):
    """Testcase : Push Updates to the Exisiting Unix Client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Push Updates to the Exisiting Unix Client"
        self.config_json = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()

    def run(self):
        """Main function for test case execution"""
        try:
            # Get previously installed information of the client from CS
            self.log.info("Fetching Client Information from CS")
            unix_client = self.commcell.clients.get(self.config_json.Install.unix_client.machine_host)

            # Download Software for Pushing Updates to the client
            self.log.info("Starting Download Software and Sync Job")
            download_job = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.UNIX_LINUX64.value])
            if download_job.wait_for_completion(10):
                self.log.info("Unix Packages Downloaded successfully")

            else:
                job_status = download_job.delay_reason
                self.log.error("Download Job Failed; Please check the Logs on CS")
                raise Exception(job_status)

            # Pushing Feature Release Upgrade to the client
            self.log.info("Pushing Feature release upgrades to the client: {0}".format(unix_client.client_name))
            upgrade_job = unix_client.push_servicepack_and_hotfix()
            if upgrade_job.wait_for_completion():
                self.log.info("Push Upgrade Job Completed successfully")

            else:
                job_status = upgrade_job.delay_reason
                self.log.error("Job failed with an error: %s", job_status)
                raise Exception(job_status)

            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(unix_client.client_hostname, self)
            self.log.info("Validating Baseline")
            install_validation.validate_baseline()
            self.log.info("Validating Services Running on the Client")
            install_validation.validate_services()
            self.log.info("Validating SP Version Installed on the Client")
            install_validation.validate_sp_version()
            self.log.info("Packages successfully Upgraded on client machine")

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
