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

import time
from Install import installer_utils
from cvpysdk.commcell import Commcell
from AutomationUtils.machine import Machine
from Install.install_helper import InstallHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config, constants
from Install.install_validator import InstallValidator
from Install.softwarecache_helper import SoftwareCache
from Install.installer_constants import DEFAULT_COMMSERV_USER
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures, UnixDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Fresh Installation of CS"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self._service_pack_to_install = None
        self.name = "Fresh Installation of Windows CS"
        self.config_json = None
        self.install_helper = None
        self.cs_machine = None
        self.software_cache_helper = None
        self.update_acceptance = False
        self.media_path = None
        self.install_inputs = {}
        self.tcinputs = {
            'ServicePack': None
        }

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.log.info("Creating CS Machine Object")
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password)
        self.install_helper = InstallHelper(None, machine_obj=self.cs_machine, tc_object=self)
        _cs_password = self.config_json.Install.cs_encrypted_password if 'windows' in self.cs_machine.os_info.lower() \
            else self.config_json.Install.cs_password
        self.install_inputs = {
            "csClientName": self.config_json.Install.commserve_client.client_name,
            "csHostname": self.config_json.Install.commserve_client.machine_host,
            "commservePassword": _cs_password,
            "instance": "Instance001"
        }
        self.update_acceptance = self.config_json.Install.update_acceptance_database

    def run(self):
        """Run function of this test case"""
        try:
            if self.cs_machine.check_registry_exists("Session", "nCVDPORT"):
                self.install_helper.uninstall_client(delete_client=False)

            self.log.info("Determining Media Path for Installation")
            self.media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else self.config_json.Install.commserve_client.sp_version
            _service_pack = _service_pack.split('_')[0] if '_' in _service_pack else _service_pack
            self._service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            if "{sp_to_install}" in self.media_path:
                self.media_path = self.media_path.replace("{sp_to_install}", self._service_pack_to_install)
            self.log.info("Service Pack used for Installation: %s" % _service_pack)
            if self.media_path:
                self.install_inputs["mediaPath"] = self.media_path
                self.log.info("Media Path used for Installation: %s" % self.media_path)
            self.log.info("Starting CS Installation")
            if self.update_acceptance:
                self.install_helper.install_acceptance_insert()
            self.install_helper.install_commserve(install_inputs=self.install_inputs, feature_release=_service_pack)
            self.log.info("Login to Commcell after CS Installation")
            time.sleep(400)
            try:
                self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                         commcell_username=DEFAULT_COMMSERV_USER,
                                         commcell_password=self.config_json.Install.cs_password)
            except Exception:
                time.sleep(500)
                self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                         commcell_username=DEFAULT_COMMSERV_USER,
                                         commcell_password=self.config_json.Install.cs_password)

            self.log.info("Checking Readiness of the CS machine")
            commserv_client = self.commcell.commserv_client
            if commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Check Readiness Failed")

            self.log.info("Starting download software job")
            self.software_cache_helper = SoftwareCache(self.commcell)
            job_obj = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value])
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                self.log.error("Download job failed")

            self.log.info("Starting Install Validation")
            package_list = [UnixDownloadFeatures.COMMSERVE.value] if self.commcell.is_linux_commserv \
                else [WindowsDownloadFeatures.COMMSERVE.value]
            install_validation = InstallValidator(commserv_client.client_hostname, self,
                                                  machine_object=self.cs_machine, package_list=package_list,
                                                  media_path=self.media_path if self.media_path else None)
            install_validation.validate_install(validate_mongodb=True)
            if self.update_acceptance:
                self.install_helper.commcell = self.commcell
                self.install_helper.install_acceptance_update('Pass', '-', self.cs_machine.machine_name)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            if self.update_acceptance:
                self.install_helper.install_acceptance_update(
                    'Fail', str(exp).replace("'", ''), self.cs_machine.machine_name,
                    self._service_pack_to_install.split('_R')[-1])

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.cs_machine)
