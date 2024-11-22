# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Negative Test case - Download job when Download server is unreachable

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""
from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import DownloadOptions
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils.machine import Machine
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for initiating a download job when server is unreachable"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - download job when server is unreachable"
        self.machine_obj = None
        self.client_obj = None
        self.config_json = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.client_obj = self.commcell.commserv_client
        self.config_json = config.get_config()
        self.machine_obj = Machine(self.client_obj)

    def run(self):
        """Main function for test case execution"""
        self.log.info("Adding Incorrect host entry for download server")
        download_server = self.commcell.get_gxglobalparam_value('Patch HTTP Site').split(":")[0]
        self.machine_obj.add_host_file_entry(
            ip_addr='11.11.11.11', hostname=download_server)
        try:
            self.log.info("Computing checksum before downloading")
            checksum_before_job = self.machine_obj.get_checksum_list(
                data_path=self.commcell.commserv_cache.get_cs_cache_path())

            self.log.info("Initiating a download job with incorrect download server address")
            job = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value])
            self.log.info("Job %s started for downloading packages", job.job_id)

            if not job.wait_for_completion(10):
                self.log.info("Failed to run download job with error: %s", job.delay_reason)
            else:
                raise Exception("Download job passed. Testcase Failed.Check host file entry on the CS machine")

            self.log.info("Computing checksum after downloading")
            checksum_after_job = self.machine_obj.get_checksum_list(
                data_path=self.commcell.commserv_cache.get_cs_cache_path())

            self.log.info("Comparing checksum")
            result = self.machine_obj.compare_lists(
                checksum_after_job, checksum_before_job, sort_list=True)
            if not result:
                raise Exception("Cache Validation Failed")
            self.log.info("Checksum Validation Successful")

            self.log.info("Removing incorrect host entry")
            self.machine_obj.remove_host_file_entry(hostname=download_server)

            self.log.info("Initiating a download job")
            job = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value])
            self.log.info("Job %s started for downloading packages", job.job_id)

            if not job.wait_for_completion():
                self.log.info("Failed to run download job with error: %s", job.delay_reason)
                raise Exception("Download job Failed. Please check logs")
            self.log.info("Download software job completed")

        except Exception as exp:
            self.log.info("Removing incorrect host entry")
            self.machine_obj.remove_host_file_entry(hostname=download_server)
            handle_testcase_exception(self, exp)
