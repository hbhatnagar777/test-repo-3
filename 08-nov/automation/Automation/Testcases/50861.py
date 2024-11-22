# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate download and install service pack on the CS.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures, UnixDownloadFeatures
import time
from Install.bootstrapper_helper import BootstrapperHelper
from Install.install_helper import InstallHelper
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Install import installer_utils
from AutomationUtils.machine import Machine
from Install.install_validator import InstallValidator
from AutomationUtils import config, constants


class TestCase(CVTestCase):
    """Class for executing Download and Install service pack and hotfixes"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Interactive - Fresh Installation using Bootstrapper downloaded media"
        self.install_helper = None
        self.tcinputs = {
            'ServicePack': None
        }
        self.config_json = None
        self.service_pack = None
        self.cs_machine = None
        self.install_inputs = None
        self.bootstrapper_obj = None
        self.download_inputs = None
        self.media_path = None
        self.status = None
        self.result_string = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.log.info("Creating CS Machine Object")
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password)
        self.install_helper = InstallHelper(None, machine_obj=self.cs_machine)
        self.download_inputs = {
            "download_full_kit": True
        }

    def get_service_pack_to_install(self, minus_value = 0):
        """
        This method determines the service pack and it's path for Installation
        Returns: None
        """
        self.log.info("Determining Media Path for Installation")
        self.media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
        _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
            else self.config_json.Install.commserve_client.sp_version
        _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
        if "{sp_to_install}" in self.media_path:
            _service_pack = _service_pack.split('_')[0] if '_' in _service_pack else _service_pack
            self.media_path = self.media_path.replace("{sp_to_install}", _service_pack_to_install)
        _service_pack_to_install = "SP" + str(int(_service_pack.lower().split('sp')[-1]) - int(minus_value))
        self.log.info(f"Service pack to Install {_service_pack_to_install}")
        self.service_pack = _service_pack_to_install
        if self.media_path:
            self.install_inputs["mediaPath"] = self.media_path
            self.log.info(f"Media Path used for Installation: {self.media_path}")

    def run(self):
        """Main function for test case execution"""
        try:
            if self.cs_machine.check_registry_exists("Session", "nCVDPORT"):
                self.install_helper.uninstall_client(delete_client=False)

            _cs_password = self.config_json.Install.cs_encrypted_password if \
                'windows' in self.cs_machine.os_info.lower() else self.config_json.Install.cs_password
            self.install_inputs = {
                "csClientName": self.config_json.Install.commserve_client.client_name,
                "csHostname": self.config_json.Install.commserve_client.machine_host,
                "commservePassword": _cs_password,
                "instance": "Instance001"}

            self.log.info("downloading the media using bootstrapper")
            self.get_service_pack_to_install()
            self.bootstrapper_obj = BootstrapperHelper(feature_release=self.service_pack, machine_obj=self.cs_machine)
            self.log.info("Downloading Media using Bootstrapper")
            self.bootstrapper_obj.extract_bootstrapper()
            _media_path = self.bootstrapper_obj.download_payload_from_bootstrapper(download_inputs=self.download_inputs)
            self.install_inputs['mediaPath'] = _media_path
            self.install_helper.install_commserve(
                                    install_inputs=self.install_inputs,
                                    feature_release=self.service_pack)
            self.log.info("Login to Commcell after CS Upgrade")
            time.sleep(600)
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=self.config_json.Install.commserve_client.webserver_username,
                                     commcell_password=self.config_json.Install.commserve_client.cs_password)

            self.log.info("Checking Readiness of the CS machine")
            _commserv_client = self.commcell.commserv_client
            if _commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Check Readiness Failed")

            self.log.info("Starting Install Validation")
            package_list = [UnixDownloadFeatures.COMMSERVE.value] if self.commcell.is_linux_commserv \
                else [WindowsDownloadFeatures.COMMSERVE.value]
            install_validation = InstallValidator(_commserv_client.client_hostname, commcell_object=self.commcell,
                                                  machine_object=self.cs_machine, package_list=package_list)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.cs_machine)

