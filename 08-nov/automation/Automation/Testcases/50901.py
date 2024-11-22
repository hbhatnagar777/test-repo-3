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

"""

from AutomationUtils import logger, config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Install.custom_package import CustomPackageCreation
from cvpysdk.commcell import Commcell
from AutomationUtils.machine import Machine
from Install.installer_constants import REMOTE_FILE_COPY_LOC
from Install.install_helper import InstallHelper
from Install.install_custom_package import InstallCustomPackage
from Install import installer_utils


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.service_pack = None
        self.client_host = None
        self.password = None
        self.username = None
        self.remote_credentials = None
        self.machine = None
        self.commcell = None
        self.custom_package_generator = None
        self.name = "Custom Package Restore only option"
        self.config_json = None
        self.machine_name = None
        self.instance = None
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
        self.machine_name = self.windows_machine.machine_name
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.username = self.config_json.Install.windows_client.machine_username
        self.password = self.config_json.Install.windows_client.machine_password
        self.client_host = self.config_json.Install.rc_client.machine_host
        self.default_log_directory = "C:\\Program Files\\Commvault\\ContentStore\\Log Files"

    def run(self):
        """Run function of this test case"""
        try:
            # Determining the Service Pack
            self.log.info(f"Service Pack to be Installed on the CS: {self.commcell.commserv_version}")
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
                **{"CustomPackageDir": self.id,
                   "RestoreOnly": True})

            # Creating the Custom Package with Interactive Installer
            self.custom_package_generator.create_custom_package()

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

            # Validating the Custom Package by installing it
            self.log.info("Validating Custom Package by Installation")
            self.install_helper = InstallCustomPackage(self.commcell, self.remote_credentials)
            self.install_helper.install_custom_package(f"{REMOTE_FILE_COPY_LOC}\\{self.id}\\WinX64",
                                                       self.commcell.commcell_username,
                                                       self.config_json.Install.cs_machine_password,
                                                       None,
                                                       **{"dir_name": "CustomPackageLOC",
                                                          "custom_package_flag": True,
                                                          "self.id": self.id})

        except Exception as exp:
            if not str(exp).find(f"\"{self.client_host}\" is not a Local Machine / Commvault client."):
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

        # Deleting the client installation
        if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
            self.windows_helper.uninstall_client(delete_client=True)
