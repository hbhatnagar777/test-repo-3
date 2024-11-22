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


from Install.custom_package import CustomPackageCreation
from Install.installer_constants import REMOTE_FILE_COPY_LOC
from Install.install_helper import InstallHelper
from Install.install_custom_package import InstallCustomPackage
from Install.install_validator import InstallValidator
from Install import installer_utils
from AutomationUtils.machine import Machine
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures


class TestCase(CVTestCase):
    """Testcase: Fresh Installation of Windows Client using URL"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Fresh Installation of Windows Client using URL"
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

    def run(self):
        """Run function of this test case"""
        try:
            # Determining the Service Pack
            self.log.info("Determining Media Path for Installation")
            self.log.info(f"Service Pack installed on commserver {self.commcell.commserv_version}")
            _service_pack = self.tcinputs.get("ServicePack")
            _service_pack_to_install = _service_pack if _service_pack else self.commcell.commserv_version
            self.log.info(f"Service pack to Install {_service_pack_to_install}")
            if not '_' in _service_pack:
                _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_to_install)
            self.service_pack = _service_pack_to_install

            # Creating custom package object
            self.custom_package_generator = CustomPackageCreation(self.commcell,
                                                                  self.service_pack,
                                                                  self.machine,
                                                                  self.remote_credentials)

            # Generating the JSON for Custom Package
            self.log.info("Generating JSON for custom package creation")
            self.custom_package_generator.generate_json_for_custom_package(
            **{"SaveUserAnswers": True,
                "CustomPackageDir": self.id,
                "CommserveName": self.config_json.Install.commserve_client.endpoint,
                "commcellUser": self.config_json.Install.mastercs.tenants.Auto_Tenant1.users.user1,
                "commcellPassword": self.config_json.Install.mastercs.tenants.Auto_Tenant1.users.password1})

            # Creating the Custom Package with Interactive Installer
            self.custom_package_generator.create_custom_package()
            
            # Creating JSON for the installing 
            self.log.info("Generating JSON for install using URL")
            self.custom_package_generator.generate_json_for_custom_package(
                **{"CreateNewInstanceCustomPackage": True,
                   "CommserveName": self.config_json.Install.commserve_client.endpoint,
                   "commcellPassword": self.config_json.Install.mastercs.tenants.Auto_Tenant1.users.password1,
                   "commcellUser": self.config_json.Install.mastercs.tenants.Auto_Tenant1.users.user1,
                   "clientName": self.config_json.Install.rc_client.client_name,
                   "ClientHostName": self.config_json.Install.rc_client.machine_host,
                   "IsToDownload": False,
                   "IsBootstrapper": True})

            # Installing Package with Interactive Installer
            self.install_helper = InstallCustomPackage(self.commcell, self.remote_credentials)
            self.install_helper.install_custom_package(f"{REMOTE_FILE_COPY_LOC}\\{self.id}\\WinX64",
                                                       self.commcell.commcell_username,
                                                       self.config_json.Install.cs_machine_password,
                                                       None,
                                                       **{"dir_name": "CustomPackageLOC",
                                                          "custom_package_flag": True,
                                                          "self.id": self.id})

            # Validating the Install
            self.client_obj = self.commcell.clients.get(self.machine_name)
            self.log.info("Starting Install Validation")
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
