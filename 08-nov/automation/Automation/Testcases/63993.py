# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import time
from Install.custom_package import CustomPackageCreation
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install import installer_utils, installer_constants
from AutomationUtils.machine import Machine
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Fresh Installation of Windows Client and Interactive Repair Install"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Fresh Installation of Windows Client and Interactive Repair Install"
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.config_json = None
        self.machine_name = None
        self.client_obj = None
        self.service_pack = None
        self.silent_install_dict = {}
        self.custom_package_generator = None
        self.tcinputs = {
            "ServicePack": None
        }
        self.remote_credentials = None
        self.machine = None

    def setup(self):
        """Setup function of this test case"""

        self.config_json = config.get_config()
        self.machine = Machine()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=self.config_json.Install.commserve_client.webserver_username,
                commcell_password=self.config_json.Install.commserve_client.cs_password)
        self.remote_credentials = {"remote_clientname": self.config_json.Install.rc_client.machine_host,
                                   "remote_username": self.config_json.Install.rc_client.machine_username,
                                   "remote_userpassword": self.config_json.Install.rc_client.machine_password,
                                   "remote_client_os_name": "Windows"}
        self.install_helper = InstallHelper(self.commcell)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.machine_name = self.windows_machine.machine_name
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.silent_install_dict = {"csClientName": self.commcell.commserv_name,
                                    "csHostname": self.commcell.commserv_hostname,
                                    "authCode": self.commcell.enable_auth_code()}

    @staticmethod
    def get_services_list(packages):
        """Get List of services running on client"""
        services = []
        unix_services = installer_constants.UNIX_SERVICES
        [services.append(service) for package in packages if int(package) in unix_services.keys()
         for service in unix_services[int(package)] if service not in services]
        return services

    def run(self):
        """Run function of this test case"""
        try:
            # Determining the Service Pack
            self.log.info(f"Service Pack to be Installed: {self.commcell.commserv_version}")
            self.log.info("Determining Media Path for Installation")
            _service_pack = self.tcinputs.get("ServicePack")
            _service_pack_to_install = _service_pack if _service_pack else self.commcell.commserv_version
            self.log.info(f"Service pack to Install {_service_pack_to_install}")
            if not '_' in _service_pack:
                _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_to_install)
            self.service_pack = _service_pack_to_install

            # Deleting a client if it exists
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=True)
            self.log.info(f"Installing fresh windows client on {self.machine_name}")

            # Fresh Installation of a client
            self.windows_helper.silent_install(
                client_name=self.id,
                tcinputs=self.silent_install_dict, feature_release=_service_pack, packages=['FILE_SYSTEM'])

            # Validating the registration
            self.log.info("Refreshing Client List on the CS")
            time.sleep(60)
            self.commcell.refresh()
            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception("Client: %s failed registering to the CS, Please check client logs"
                                % self.machine_name)

            # Repairing the Instance Interactively
            self.custom_package_generator = CustomPackageCreation(self.commcell,
                                                                  self.service_pack,
                                                                  self.machine,
                                                                  self.remote_credentials)

            self.client_obj = self.commcell.clients.get(self.machine_name)

            self.log.info("Generating JSON for repair on existing instance")
            self.custom_package_generator.generate_json_for_custom_package(
                **{"CreateNewInstanceCustomPackage": False,
                   "CommserveName": self.config_json.Install.commserve_client.client_name,
                   "commcellPassword": self.config_json.Install.cs_machine_password,
                   "commcellUser": self.config_json.Install.cs_machine_username,
                   "clientName": self.config_json.Install.rc_client.client_name,
                   "ClientHostName": self.config_json.Install.rc_client.machine_host,
                   "installOption": "Repair Existing Instance",
                   "IsToDownload": False,
                   "IsBootstrapper": True
                   })

            # Creating the Custom Package with Interactive Installer
            self.custom_package_generator.create_custom_package()

            # Validating the Repair Install
            self.client_obj = self.commcell.clients.get(self.machine_name)
            self.log.info("Starting Repair Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.windows_machine,
                                                  package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                                                  media_path=None)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.windows_machine)
        if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
            self.windows_helper.uninstall_client(delete_client=True)
