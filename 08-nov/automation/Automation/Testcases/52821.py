# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate download and install service pack.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""
import random
from AutomationUtils import constants, logger, config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Install.softwarecache_helper import SoftwareCache
from Install.softwarecache_validation import DownloadValidation
from cvpysdk.internetoptions import InternetOptions
from cvpysdk.commcell import Commcell
from cvpysdk.job import JobController
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions, OSNameIDMapping


class TestCase(CVTestCase):
    """Download pre-check software cache to determine missing files"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Download pre-check software cache to determine missing files"
        self.log = None
        self.config_json = None
        self.cs_machine = None
        self.os_to_download = None
        self.sw_cache_helper = None
        self.download_helper = None
        self.validation_helper = None
        self.job_controller = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.log = logger.get_log()
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=self.config_json.Install.commserve_client.webserver_username,
                commcell_password=self.config_json.Install.commserve_client.cs_password)
        self.job_controller = JobController(self.commcell)
        self.download_helper = SoftwareCache(self.commcell)
        self.sw_cache_helper = self.commcell.commserv_cache
        self.cs_machine = Machine(self.commcell.commserv_hostname, self.commcell)
        self.os_to_download = [DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value]
        self._internet_options_obj = InternetOptions(self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:
            self._internet_options_obj.disable_http_proxy()
            self._internet_options_obj.set_no_gateway()
            self.log.info("Killing active download jobs in CS")
            for jid, data in self.job_controller.active_jobs().items():
                if data['operation'] == 'Download Software':
                    self.job_controller.get(jid).kill(wait_for_job_to_kill=True)
            self.log.info("Deleting the Software cache")
            self.sw_cache_helper.delete_cache()
            self.sw_cache_helper.commit_cache()
            self.log.info("Starting Download Software Job")
            job_obj = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value, os_list=self.os_to_download)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")
            self.log.info("Download Software Job Successful")

            self.log.info("Starting to delete random files in cache")
            deleted_files_list = []
            sw_cache_path = self.commcell.commserv_cache.get_cs_cache_path()
            cache_files = self.cs_machine.get_files_in_path(sw_cache_path, recurse=True)

            for file in cache_files:
                if (random.randint(1000, 9999) % 17) == 0:
                    if "LooseUpdates" not in file:
                        try:
                            self.cs_machine.delete_file(file)
                            deleted_files_list.append(file)
                        except Exception as exp:
                            self.log.error(f"Failed to remove file {file} with error {exp}")

            self.log.info("Starting Download Software Job")
            job_obj = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value, os_list=self.os_to_download)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")
            self.log.info("Download Software Job Successful")

            self.log.info("Validating if deleted files are downloaded again")
            file_checkflag = True
            for every_file in deleted_files_list:
                if self.cs_machine.check_file_exists(every_file):
                    continue
                else:
                    file_checkflag = False
                    self.log.error(f"File {every_file} is not been re-downloaded")
            if file_checkflag:
                self.log.info("Deleted files have been repopulated successfully")
            else:
                raise Exception("Failed to repopulate corrupted cache")

            self.log.info("Starting download validation")
            self.validation_helper = DownloadValidation(self.commcell, job_id=job_obj.job_id,
                                                        download_option=DownloadOptions.LATEST_HOTFIXES.value,
                                                        os_to_download=[OSNameIDMapping.WINDOWS_64.value,
                                                                     OSNameIDMapping.UNIX_LINUX64.value])
            self.validation_helper.download_validation()
            self.log.info("Download validation for automation download successful")
        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
