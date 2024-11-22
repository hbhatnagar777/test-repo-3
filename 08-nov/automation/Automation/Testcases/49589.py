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
from AutomationUtils import constants, logger, config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Install.softwarecache_helper import SoftwareCache
from Install.softwarecache_validation import DownloadValidation
from cvpysdk.internetoptions import InternetOptions
from cvpysdk.client import Client
from cvpysdk.commcell import Commcell
from cvpysdk.job import JobController
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions, OSNameIDMapping


class TestCase(CVTestCase):
    """Download Software on CS- Automatic download"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Download Software on CS- Automatic download"
        self.log = None
        self.config_json = None
        self.sw_cache_helper = None
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
        self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                             key_name="ForceDownloadSoftwareFromInternet",
                                             data_type="INTEGER", value=str(0))
        self._internet_options_obj = InternetOptions(self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Killing active download jobs in CS")
            for jid, data in self.job_controller.active_jobs().items():
                if data['operation'] == 'Download Software':
                    self.job_controller.get(jid).kill(wait_for_job_to_kill=True)
            client_dict = self.commcell.clients.all_clients
            filtered_clients = []
            os_list = set()
            os_list_validation = set()
            for client, details in client_dict.items():
                if client != self.commcell.commserv_name:
                    client_obj = Client(self.commcell, client)
                    filtered_clients.append(client_obj.client_name)
                    if "windows" in client_obj.os_info.lower():
                        os_list.add(DownloadPackages.WINDOWS_64.value)
                        os_list_validation.add(OSNameIDMapping.WINDOWS_64.value)
                    elif "unix" in client_obj.os_info.lower():
                        os_list.add(DownloadPackages.UNIX_LINUX64.value)
                        os_list_validation.add(OSNameIDMapping.UNIX_LINUX64.value)
            self.log.info("Deleting the Software cache")
            self.sw_cache_helper.delete_cache()
            self.sw_cache_helper.commit_cache()
            self._internet_options_obj.set_no_gateway()
            # calls the push service pack and hotfixes job
            job_obj = self.commcell.push_servicepack_and_hotfix(filtered_clients)
            self.log.info("Job %s started for Installing packages", job_obj.job_id)
            try:
                job_obj.wait_for_completion()
            except Exception:
                self.log.error("Update job Failed")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run Install job with error: " + job_obj.delay_reason)

            if job_obj.status == "Completed w/ one or more errors":
                self.log.error("Job Completed with one or more errors please check the logs")
            self.log.info("Successfully finished Installing packages")
            download_job_id = str(int(job_obj.job_id) + 1)
            self.log.info("Starting download validation")
            self.validation_helper = DownloadValidation(self.commcell, job_id=download_job_id,
                                                        download_option=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
                                                        os_to_download=list(os_list_validation),
                                                        service_pack=self.commcell.commserv_version,
                                                        cu_pack=int(self.commcell.version.split('.')[-1]))
            self.validation_helper.download_validation()
            self.log.info("Download validation for automation download successful")
        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
