# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

Test cases to validate download and install service pack.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""
from AutomationUtils import constants, logger, config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Install.softwarecache_validation import DownloadValidation
from Install.installer_constants import CURRENT_RELEASE_VERSION, CURRENT_BUILD_VERSION
from Install.installer_constants import DOWNLOAD_SOFTWARE_DEFAULT_MEDIA
from Install import installer_utils
from cvpysdk.commcell import Commcell
from cvpysdk.job import JobController
from base64 import b64encode
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions, OSNameIDMapping
from cvpysdk.internetoptions import InternetOptions


class TestCase(CVTestCase):
    """Copy software of Hotfix Pack"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Copy software of Hotfix Pack"
        self.log = None
        self.latest_cu = None
        self.config_json = None
        self.dvd_loc = None
        self.updates_loc = None
        self.os_to_validate = None
        self.cs_machine = None
        self.latest_cu = None
        self.sw_cache_helper = None
        self.validation_helper = None
        self.job_controller = None
        self.loose_updates_path = None

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
        self.cs_machine = Machine(self.commcell.commserv_hostname, self.commcell)
        self.sw_cache_helper = self.commcell.commserv_cache
        self.dvd_loc = self.cs_machine.join_path(self.config_json.Install.dvd_loc, DOWNLOAD_SOFTWARE_DEFAULT_MEDIA,
                                                 CURRENT_RELEASE_VERSION, CURRENT_BUILD_VERSION)
        self.updates_loc = self.config_json.Install.updates_loc
        self.os_to_validate = []
        self.latest_cu = installer_utils.get_latest_cu_from_xml(installer_utils.get_latest_recut_from_xml(
            self.commcell.commserv_version))

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Killing active download jobs in CS")
            for jid, data in self.job_controller.active_jobs().items():
                if data['operation'] == 'Download Software':
                    self.job_controller.get(jid).kill(wait_for_job_to_kill=True)
            if not self.commcell.is_linux_commserv:
                self.dvd_loc = self.cs_machine.join_path(
                    self.dvd_loc, installer_utils.get_latest_recut_from_xml(self.commcell.commserv_version), "Windows")
                self.os_to_validate.append(OSNameIDMapping.WINDOWS_64.value)
                self.loose_updates_path = self.cs_machine.join_path(
                    self.sw_cache_helper.get_cs_cache_path(),
                    DOWNLOAD_SOFTWARE_DEFAULT_MEDIA, CURRENT_RELEASE_VERSION,
                    installer_utils.get_latest_recut_from_xml(self.commcell.commserv_version), "Windows",
                    "BinaryPayload", "LooseUpdates")
            else:
                self.dvd_loc = self.cs_machine.join_path(
                    self.dvd_loc, installer_utils.get_latest_recut_from_xml(self.commcell.commserv_version), "Unix")
                self.os_to_validate.append(OSNameIDMapping.UNIX_LINUX64.value)
                self.loose_updates_path = self.cs_machine.join_path(
                    self.sw_cache_helper.get_cs_cache_path(),
                    DOWNLOAD_SOFTWARE_DEFAULT_MEDIA, CURRENT_RELEASE_VERSION,
                    installer_utils.get_latest_recut_from_xml(self.commcell.commserv_version), "Unix",
                    "linux-x8664", "LooseUpdates")
            self.log.info("Deleting the Software cache")
            self.sw_cache_helper.delete_cache()
            self.sw_cache_helper.commit_cache()
            self.log.info("Populating DVD from internal server")
            self.log.info("Starting Copy Software Job")
            job_obj = self.commcell.copy_software(self.dvd_loc, self.config_json.Install.dvd_username,
                                                  b64encode(self.config_json.Install.dvd_password.encode()).decode())
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")
            self.log.info("Copy Software Job Successful")
            self.log.info("Removing existing Updates from SW cache media")
            self.cs_machine.clear_folder_content(self.loose_updates_path)
            self.sw_cache_helper.commit_cache()
            self.log.info("Populating Updates from internal server")
            self.log.info("Starting Copy Software Job")
            self.updates_loc = self.updates_loc.replace("{cs_sp}", str(self.commcell.commserv_version))
            job_obj = self.commcell.copy_software(self.updates_loc, self.config_json.Install.dvd_username,
                                                  b64encode(self.config_json.Install.dvd_password.encode()).decode())
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Copy Software Job Successful")
            else:
                raise Exception("Copy Software job failed")
            self.log.info("Copy Software Job Successful")
            self.log.info("Starting Download validation")
            self.validation_helper = DownloadValidation(self.commcell, job_id=job_obj.job_id,
                                                        download_option=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
                                                        os_to_download=self.os_to_validate,
                                                        service_pack=self.commcell.commserv_version,
                                                        cu_pack=self.latest_cu)
            self.validation_helper.download_validation()
            self.log.info("Download validation successful")
        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
