# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

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
from Install.update_helper import UpdateHelper
from Install.install_validator import InstallValidator
from Install.softwarecache_helper import SoftwareCache
from Install.installer_constants import DEFAULT_COMMSERV_USER
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures, UnixDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Fresh Installation of Linux CS"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "SP-1 installation of Linux CS"
        self.config_json = None
        self.install_helper = None
        self.cs_machine = None
        self.install_inputs = {}
        self.commcell = None
        self.media_path = None
        self.tcinputs = {
            'ServicePack': None,
            'MediaPath': None
        }

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.log.info("Creating CS Machine Object")
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password)
        self.install_helper = InstallHelper(None, machine_obj=self.cs_machine)
        _cs_password = self.config_json.Install.cs_encrypted_password if 'windows' in self.cs_machine.os_info.lower() \
            else self.config_json.Install.cs_password

    def run(self):
        """Run function of this test case"""
        try:
            if self.cs_machine.check_registry_exists("Session", "nCVDPORT"):
                self.install_helper.uninstall_client(delete_client=False)

            self.log.info("Determining Media Path for Installation")
            if self.tcinputs.get('MediaPath') is None:
                media_path = self.config_json.Install.media_path
            else:
                media_path = self.tcinputs.get('MediaPath')
            _service_pack = self.tcinputs.get("ServicePack")
            if "{sp_to_install}" in media_path:
                if self.tcinputs.get("ServicePack") is None:
                    _service_pack = str(self.commcell.commserv_version)
                else:
                    if '_' in _service_pack:
                        _service_pack = _service_pack.split('_')[0]
            _service_pack = _service_pack.lower().split('sp')[-1]
            _minus_value = self.config_json.Install.minus_value
            _service_pack_to_install = int(_service_pack) - int(_minus_value)
            self.log.info(f"Service pack to Install {_service_pack_to_install}")
            if not '_' in _service_pack:
                _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_to_install)
                media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
            self.log.info("Media Path used for Installation: %s" % media_path)
            _cs_password = self.config_json.Install.cs_encrypted_password if 'windows' in self.cs_machine.os_info.lower() \
                else self.config_json.Install.cs_password
            self.install_inputs = {
                "csClientName": self.config_json.Install.commserve_client.client_name,
                "csHostname": self.config_json.Install.commserve_client.machine_host,
                "commservePassword": _cs_password,
                "mediaPath": media_path,
                "instance": "Instance001"}

            self.log.info("Starting CS Installation")
            self.install_helper.install_commserve(install_inputs=self.install_inputs,
                                                  feature_release=str(_service_pack_to_install))

            self.log.info("Login to Commcell after CS Installation")
            time.sleep(900)
            try:
                self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                         commcell_username=DEFAULT_COMMSERV_USER,
                                         commcell_password=self.config_json.Install.cs_password)
            except Exception:
                time.sleep(300)
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
            _software_cache_helper = SoftwareCache(self.commcell)
            job_obj = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value])
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                self.log.error("Download job failed")

            package_list = [UnixDownloadFeatures.COMMSERVE.value] if self.commcell.is_linux_commserv \
                else [WindowsDownloadFeatures.COMMSERVE.value]

            self.log.info("Updating CS to latest version")
            _update_helper = UpdateHelper(self.commcell, self.cs_machine)
            _update_helper.push_maintenance_release([self.config_json.Install.commserve_client.client_name])

            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(commserv_client.client_hostname, self, package_list=package_list,
                                                  machine_object=self.cs_machine, is_push_job=True)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.cs_machine)
