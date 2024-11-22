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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    validate_rolesmanager_xml()   -- to validate the install.xml created while making a custom package

"""
import time
from Install.install_custom_package import InstallCustomPackage
from AutomationUtils import logger, config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Install.custom_package import CustomPackageCreation
from cvpysdk.commcell import Commcell
from AutomationUtils.machine import Machine
from Install.installer_constants import REMOTE_FILE_COPY_LOC
from Install.install_helper import InstallHelper
from Install import installer_utils
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from Install.install_validator import InstallValidator
import xml.etree.ElementTree as ET


class TestCase(CVTestCase):
    """Testcase : Install Custom Package with Roles Manager"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Install Custom Package with Roles Manager"
        self.client_obj = None
        self.service_pack = None
        self.client_host = None
        self.remote_credentials = None
        self.machine = None
        self.commcell = None
        self.custom_package_generator = None
        self.config_json = None
        self.machine_name = None
        self.default_log_directory = None
        self.log = None
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.tcinputs = {
            "ServicePack": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.log = logger.get_log()
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
        self.machine_name = Machine(machine_name=self.remote_credentials["remote_clientname"],
                                    commcell_object=self.commcell,
                                    username=self.config_json.Install.rc_client.machine_username,
                                    password=self.config_json.Install.rc_client.machine_password)
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.client_host = self.config_json.Install.rc_client.machine_host
        self.default_log_directory = "C:\\Program Files\\Commvault\\ContentStore\\Log Files"

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
            # Determining the Service Pack
            self.log.info(f"Service Pack to be Installed: {self.commcell.commserv_version}")
            self.log.info("Determining Media Path for Installation")

            if self.tcinputs.get('MediaPath') is None:
                media_path = self.config_json.Install.media_path
            else:
                media_path = self.tcinputs.get('MediaPath')

            _service_pack = self.tcinputs.get("ServicePack")
            _service_pack_to_install = _service_pack if _service_pack else self.commcell.commserv_version

            if "{sp_to_install}" in media_path:
                if self.tcinputs.get("ServicePack") is None:
                    _service_pack_to_install = self.commcell.commserv_version
                else:
                    if '_' in _service_pack:
                        _service_pack_to_install = _service_pack.split('_')[0]
                    _service_pack_to_install = _service_pack.lower().split('sp')[1]

            self.log.info(f"Service pack to Install {_service_pack_to_install}")

            if not '_' in _service_pack:
                _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_to_install)
                media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)

            self.service_pack = _service_pack_to_install
            self.tcinputs.update({"mediaPath": media_path})

            # Deleting a client if it exists
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=True)

            self.custom_package_generator = CustomPackageCreation(self.commcell,
                                                                  self.service_pack,
                                                                  self.machine,
                                                                  self.remote_credentials)

            # Generating the JSON for Custom Package
            self.log.info("Generating JSON for custom package creation")
            self.custom_package_generator.generate_json_for_custom_package(
                **{"SaveUserAnswers": True,
                   "CreateSeedPackage": True,
                   "ShowToUsers": False,
                   "CustomPackageDir": self.id,
                   "CommserveName": self.config_json.Install.commserve_client.client_name,
                   "commcellPassword": self.config_json.Install.cs_machine_password,
                   "SelectedOS": ["WinX64", "Unix"],
                   "commcellUser": self.config_json.Install.cs_machine_username,
                   "FEATURE_SELECTION": {
                       "Microsoft Windows": [
                           "File System Core",
                           "File System"
                       ],
                       "Virtualization": [
                            "Virtual Server"
                       ]
                   }})

            # Creating the Custom Package with Interactive Installer
            self.custom_package_generator.create_custom_package()

            # Validating the install.xml created for installing
            self.validate_rolesmanager_xml(roles=[WindowsDownloadFeatures.FILE_SYSTEM.value,
                                                WindowsDownloadFeatures.VIRTUAL_SERVER.value])

            # Installing the Custom Package
            time.sleep(60)
            self.log.info("Installing the Custom Package ")
            self.install_helper = InstallCustomPackage(self.commcell, self.remote_credentials)
            self.install_helper.install_custom_package(f"{REMOTE_FILE_COPY_LOC}\\{self.id}\\WinX64",
                                                       self.commcell.commcell_username,
                                                       self.config_json.Install.cs_machine_password,
                                                       None,
                                                       **{"dir_name": "CustomPackageLOC",
                                                          "custom_package_flag": True,
                                                          "self.id": self.id}
                                                       )

            # Refreshing the CS
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

            # Validating the Installation
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.windows_machine,
                                                  package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value,
                                                                WindowsDownloadFeatures.VIRTUAL_SERVER.value],
                                                  media_path=media_path if media_path else None)
            install_validation.validate_install()

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error('Failed to execute test case with error: %s', exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == "FAILED":
            try:
                if self.windows_machine.check_directory_exists(self.default_log_directory):
                    self.windows_machine.copy_folder(self.default_log_directory, REMOTE_FILE_COPY_LOC)
                    self.windows_machine.rename_file_or_folder(
                        self.windows_machine.join_path(REMOTE_FILE_COPY_LOC, "Log_Files"),
                        self.id + self.windows_machine.get_system_time())
            except Exception as exp:
                self.log.info("Unable to copy the logs", exp)

        # Deleting the client
        if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
            self.windows_helper.uninstall_client(delete_client=True)
