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
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures, WindowsDownloadFeatures
from Install.install_helper import InstallHelper
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Install import installer_utils
from AutomationUtils.machine import Machine
import time
from Install.install_validator import InstallValidator
from AutomationUtils import config, constants


class TestCase(CVTestCase):
    """Class for executing Download and Install service pack and hotfixes"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Windows- Install - Interactive Installation of Virtual Server Protection"
        self.install_helper = None
        self.tcinputs = {
            'ServicePack': None
        }
        self.config_json = None
        self.service_pack = None
        self.cs_machine = None
        self.install_inputs = None
        self.bootstrapper_obj = None
        self.oem_id = 106

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.log.info("Creating CS Machine Object")
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password)
        self.install_helper = InstallHelper(None, machine_obj=self.cs_machine)

    def get_service_pack_to_install(self, minus_value = 0):
        """
        This method determines the service pack and it's path for Installation
        Returns: None
        """
        self.log.info("Determining Media Path for Installation")
        if self.tcinputs.get('MediaPath') is None:
            media_path = self.config_json.Install.media_path
        else:
            media_path = self.tcinputs.get('MediaPath')
        _service_pack = self.tcinputs.get("ServicePack")
        _service_pack_to_install = _service_pack
        if "{sp_to_install}" in media_path:
            if self.tcinputs.get("ServicePack") is None:
                _service_pack_to_install = self.commcell.commserv_version
            else:
                if '_' in _service_pack:
                    _service_pack_to_install = _service_pack.split('_')[0]
                _service_pack_to_install = _service_pack.lower().split('sp')[1]
        _service_pack_to_install = _service_pack_to_install - int(minus_value)
        self.log.info(f"Service pack to Install {_service_pack_to_install}")
        if not '_' in _service_pack:
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_to_install)
            media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
        self.service_pack = _service_pack_to_install
        self.tcinputs.update({"mediaPath": media_path})

    def run(self):
        """Main function for test case execution"""
        try:
            if self.cs_machine.check_registry_exists("Session", "nCVDPORT"):
                self.install_helper.uninstall_client(delete_client=False)

            self.get_service_pack_to_install()
            self.install_inputs = {
                "csClientName": self.config_json.Install.commserve_client.client_name,
                "csHostname": self.config_json.Install.commserve_client.machine_host,
                "commservePassword": self.config_json.Install.commserve_client.cs_password,
                "mediaPath": self.tcinputs["mediaPath"],
                "instance": "Instance001",
                "oem_id":self.oem_id}

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
            install_validation = InstallValidator(_commserv_client.client_hostname, self,
                                                  machine_object=self.cs_machine,
                                                  package_list=package_list,
                                                  oem_id=self.oem_id)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.cs_machine)
