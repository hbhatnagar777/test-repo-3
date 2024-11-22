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

    validate_rolesmanager_xml()   -- to validate the install.xml created while making a custom package

"""
import random
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install import installer_utils
from Install.bootstrapper_helper import BootstrapperHelper
from Install.custom_package import CustomPackageCreation
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from Install.installer_constants import REMOTE_FILE_COPY_LOC
from Install.install_custom_package import InstallCustomPackage
import xml.etree.ElementTree as ET


class TestCase(CVTestCase):
    """Testcase :Service pack upgrade with roles manager enabled"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Service pack upgrade with roles manager enabled"
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.config_json = None
        self.machine_name = None
        self.client_obj = None
        self.media_path = None
        self.custom_package_generator = None
        self.service_pack = None
        self.silent_install_dict = {}

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
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
        self.client_host = self.config_json.Install.rc_client.machine_host
        self.default_log_directory = "C:\\Program Files\\Commvault\\ContentStore\\Log Files"
        self.silent_install_dict = {
            "csClientName": self.commcell.commserv_name,
            "csHostname": self.commcell.commserv_hostname,
            "authCode": self.commcell.enable_auth_code(),
            "instance": "Instance001"
        }
        self.media_path = BootstrapperHelper("SP" + str(self.commcell.commserv_version),
                                             self.windows_machine).bootstrapper_download_url()

    def validate_rolesmanager_xml(self, roles=None):

        # Validating roles manager xml

        if roles is None:
            roles = []

        try:
            custom_xml = self.machine_name.read_file(f"{REMOTE_FILE_COPY_LOC}\\{self.id}\\install.xml")
            root = ET.fromstring(custom_xml)

            for neighbor in root.iter('installFlags'):
                installerflags_dict = neighbor.attrib

            # Validating the Selected Roles during Install Time
            roles_selected_in_xml = [int(i) for i in (installerflags_dict["selectedRoles"]).split(',')]
            for role in roles:
                if role not in roles_selected_in_xml:
                    raise Exception("Validation for Selected roles failed ")
            self.log.info("Selected roles have been validated")

            # Validating if launchRolesManager flag is set properly 
            if installerflags_dict["launchRolesManager"] == "1":
                self.log.info("Flag set for LaunchRolesManager")
            else:
                raise Exception("launchRolesManager flag is not set properly")

            # Validating that only FSCore Component has been selected during install time 
            for neighbor in root.iter('clientComposition'):
                for element in neighbor:
                    if element.tag == "components":
                        for components in element:
                            if components.tag == "componentInfo":
                                if components.attrib['ComponentName'] == "File System Core":
                                    self.log.info("FS Core package is selected")
                                else:
                                    raise Exception("Additional packages selected for install")
            self.log.info("Validation for FSCore selection passed")

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error('Validation failed, please check the xml on client')

    def run(self):
        """Run function of this test case"""
        try:
            # Deleting a client if it exists
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=False)

            # Installing SP-1 Client
            self.log.info("Determining Media Path for Installation")
            media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else "SP" + str(self.commcell.commserv_version)
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            if "{sp_to_install}" in media_path:
                _service_pack = _service_pack.split('_')[0] if '_' in _service_pack else _service_pack
                media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
            _service_pack = _service_pack[:2] + str(int(_service_pack[2:]) - 2)
            self.log.info(f"Service Pack used for Installation: {_service_pack}")
            self.log.info(f"Media Path used for Installation: {media_path}")

            self.log.info(f"Installing fresh windows client on {self.machine_name}")
            self.windows_helper.silent_install(
                client_name=self.name.replace(" ", "_") + "_" + str(random.randint(1000, 9999)),
                tcinputs=self.silent_install_dict, feature_release=_service_pack, packages=['FILE_SYSTEM'])

            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.machine_name} failed registering to the CS, Please check client logs")

            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.windows_machine,
                                                  package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                                                  media_path=media_path if media_path else None)
            install_validation.validate_install()

            # Creating custom package and then updating the client
            self.service_pack = _service_pack[:2] + str(int(_service_pack[2:]) + 2)
            self.custom_package_generator = CustomPackageCreation(self.commcell,
                                                                  self.service_pack,
                                                                  self.machine,
                                                                  self.remote_credentials)

            # Generating the JSON for Custom Package
            self.log.info("Generating JSON for custom package creation")
            self.custom_package_generator.generate_json_for_custom_package(
                **{"SaveUserAnswers": True,
                   "ShowToUsers": False,
                   "CustomPackageDir": self.id,
                   "CommserveName": self.config_json.Install.commserve_client.client_name,
                   "commcellPassword": self.config_json.Install.cs_machine_password,
                   "commcellUser": self.config_json.Install.cs_machine_username,
                   "CreateSeedPackage": True,
                   "FEATURE_SELECTION": {
                       "Server": [
                            "MediaAgent"
                        ]}})

            # Creating the Custom Package with Interactive Installer
            self.custom_package_generator.create_custom_package()

            # Validating the install.xml created for installing
            self.validate_rolesmanager_xml(roles=[WindowsDownloadFeatures.MEDIA_AGENT.value])

            # Generating the JSON for Custom Package Installation
            self.log.info("Generating JSON for custom package installation")
            self.custom_package_generator.generate_json_for_custom_package(
                **{"CommserveName": self.config_json.Install.commserve_client.client_name,
                   "commcellPassword": self.config_json.Install.cs_machine_password,
                   "commcellUser": self.config_json.Install.cs_machine_username,
                   "clientName": self.config_json.Install.rc_client.client_name,
                   "ClientHostName": self.config_json.Install.rc_client.machine_host,
                   "IsInstallingFromCustomPackage": True,
                   "installOption": "Install packages on this computer",
                   "IsToDownload": False
                   })

            # Installing the Custom Package
            self.log.info("Installing the Custom Package")
            self.install_helper = InstallCustomPackage(self.commcell, self.remote_credentials)
            self.install_helper.install_custom_package(f"{REMOTE_FILE_COPY_LOC}\\{self.id}\\WinX64",
                                                       self.commcell.commcell_username,
                                                       self.config_json.Install.cs_machine_password,
                                                       None,
                                                       **{"dir_name": "CustomPackageLOC",
                                                          "custom_package_flag": True,
                                                          "self.id": self.id})

            # Validating Install
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.windows_machine,
                                                  package_list=[WindowsDownloadFeatures.MEDIA_AGENT.value,
                                                                WindowsDownloadFeatures.FILE_SYSTEM.value],
                                                  media_path=media_path if media_path else None)
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
