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
from Install.install_validator import InstallValidator
from Install.installer_constants import DEFAULT_COMMSERV_USER
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Fresh Installation of Linux CS as a non root user"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Fresh Installation of CS as a non root user"
        self.config_json = None
        self.install_helper = None
        self.cs_machine = None
        self.install_inputs = {}
        self.commcell = None
        self.media_path = None
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
            "instance": "Instance001",
            "rootUser": "0"
        }

    def run(self):
        """Run function of this test case"""
        try:
            # Deleting the commcell if it exists
            if self.cs_machine.check_registry_exists("Session", "nCVDPORT"):
                self.install_helper.uninstall_client(delete_client=False)

            # Determing the media path
            self.log.info("Determining Media Path for Installation")
            _service_pack = self.tcinputs.get("ServicePack")
            self.log.info(f"Service pack to Install {_service_pack}")
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            self.log.info(f"Service Pack used for Installation: {_service_pack_to_install}")

            # Installing the CS
            self.log.info("Starting CS Installation")
            self.install_helper.install_commserve(install_inputs=self.install_inputs, feature_release=_service_pack)

            # Creating the commcell object
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

            # Performing check readiness
            self.log.info("Checking Readiness of the CS machine")
            commserv_client = self.commcell.commserv_client
            if commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Check Readiness Failed")

            # Validating the Install  
            self.log.info("Validating the Install")         
            install_validation = InstallValidator(
                commserv_client.client_hostname, 
                self,
                machine_object=self.cs_machine, 
                package_list=[UnixDownloadFeatures.COMMSERVE.value],
                media_path= None)
            
            install_validation.validate_install(
                 **{"validate_nonroot_services": True,
                   "validate_nonroot_install": True})

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.cs_machine)
