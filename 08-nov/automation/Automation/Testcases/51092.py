# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, config, constants
from Install.softwarecache_helper import SoftwareCache
from Install.softwarecache_validation import DownloadValidation
from cvpysdk.internetoptions import InternetOptions
from cvpysdk.commcell import Commcell
from cvpysdk.job import JobController
from cvpysdk.deployment.deploymentconstants import DownloadOptions, DownloadPackages, OSNameIDMapping
import time


class TestCase(CVTestCase):
    """Testcase : Download software via CVInternet gateway using Unix client"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Download software via CVInternet gateway using Unix client"
        self.config_json = None
        self.log = None
        self.tcinputs = {}
        self.protocol = None
        self.download_helper = None
        self.validation_helper = None
        self.sw_cache_helper = None
        self.client_gateway = None
        self.cs_machine_obj = None
        self.job_controller = None

    def setup(self):
        """Setup function of this test case"""
        self.log = logger.get_log()
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=self.config_json.Install.commserve_client.webserver_username,
                commcell_password=self.config_json.Install.commserve_client.cs_password)
        self.protocol = "HTTPS"
        self.job_controller = JobController(self.commcell)
        self.download_helper = SoftwareCache(self.commcell)
        self.sw_cache_helper = self.commcell.commserv_cache
        self.client_gateway = self.config_json.Install.unix_client.client_name
        self.cs_machine_obj = Machine(machine_name=self.commcell.commserv_name, commcell_object=self.commcell)
        self._internet_options_obj = InternetOptions(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            self._internet_options_obj.disable_http_proxy()
            self._internet_options_obj.set_no_gateway()
            self.log.info("sleeping after removing gateway")
            time.sleep(30)
            self.log.info(f"Setting the client gateway in CS to {self.client_gateway}")
            self._internet_options_obj.set_internet_gateway_client(self.client_gateway)
            self.log.info("sleeping after setting gateway")
            time.sleep(30)
            self._internet_options_obj.set_gateway_for_sendlogs(self.client_gateway)
            time.sleep(30)
            self.download_helper.update_client_gateway_details_in_cs(self.client_gateway)
            self.log.info("Killing active download jobs in CS")
            for jid, data in self.job_controller.active_jobs().items():
                if data['operation'] == 'Download Software':
                    self.job_controller.get(jid).kill(wait_for_job_to_kill=True)
            self.log.info("Setting protocol type to HTTPS")
            self.download_helper.set_protocol_type(self.protocol)
            self.log.info("Deleting the Software cache")
            self.sw_cache_helper.delete_cache()
            self.sw_cache_helper.commit_cache()
            self.log.info(f"Adding incorrect host file entry for {self.config_json.Install.download_server}")
            self.cs_machine_obj.add_host_file_entry(ip_addr='127.0.0.1',
                                                    hostname=self.config_json.Install.download_server.split(":")[0])
            self.log.info("Starting Download Software Job")
            job_obj = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value])
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")
            self.log.info(f"Removing incorrect host file entry for {self.config_json.Install.download_server}")
            self.cs_machine_obj.remove_host_file_entry(hostname=self.config_json.Install.download_server.split(":")[0])
            self.log.info("Starting download validation")
            self.validation_helper = DownloadValidation(self.commcell, job_id=job_obj.job_id,
                                                        download_option=DownloadOptions.LATEST_HOTFIXES.value,
                                                        os_to_download=[OSNameIDMapping.WINDOWS_64.value,
                                                                     OSNameIDMapping.UNIX_LINUX64.value])
            self.validation_helper.download_validation()
        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info(f"Removing incorrect host file entry for {self.config_json.Install.download_server}")
        self.cs_machine_obj.remove_host_file_entry(hostname=self.config_json.Install.download_server.split(":")[0])
        self.log.info("Resetting the client gateway in CS to default value")
        self._internet_options_obj.set_no_gateway()
        time.sleep(30)
        self.download_helper.update_client_gateway_details_in_cs(reset=True)
