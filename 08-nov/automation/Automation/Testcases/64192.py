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

from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install import installer_utils
from Install.installer_constants import DEFAULT_COMMSERV_USER
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from AutomationUtils.machine import Machine
from cvpysdk.organization import Organization


class TestCase(CVTestCase):
    """Testcase: Universal Installer: Pass endpointURL as cmdline argument - windows client"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Universal Installer: Pass endpointURL as cmdline argument - windows client"
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.config_json = None
        self.machine_name = None
        self.media_path = None
        self.client_obj = None
        self.silent_install_dict = {}
        self.security_helper = None
        self.authcode = None
        self.organization_helper = None
        self.cs_machine_obj = None
        self._service_pack_to_install = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.machine_name = self.windows_machine.machine_name
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.cs_machine_obj = Machine(machine_name=self.commcell.commserv_name, commcell_object=self.commcell)
        self.organization_helper = Organization(
            self.commcell,
            self.config_json.Install.mastercs.tenants.Auto_Tenant1.name)
        self.authcode = self.organization_helper.enable_auth_code()
        self.log.info(self.authcode)
        self.silent_install_dict = {
            "csClientName": "",
            "csHostname": "",
            "authCode": "",
            "cmdline_args": {
                "authcode": self.authcode,
                "endpointurl": self.config_json.Install.mastercs.endpoint}
        }

    def run(self):
        """Run function of this test case"""
        try:
            # Determining the media path for the installation
            self.log.info("Determining Media Path for Installation")
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else "SP" + str(self.commcell.commserv_version)
            self.log.info(f"Service pack to Install {_service_pack}")
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            self.log.info(f"Service Pack used for Installation: {_service_pack_to_install}")

            # Deleting a client if it exists
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=True)

            # Fresh Installation of a client
            self.log.info(f"Installing windows client on {self.machine_name}")
            self.windows_helper.silent_install(
                client_name=self.id,
                tcinputs=self.silent_install_dict,
                feature_release=_service_pack,
                packages=['FILE_SYSTEM'])

            # Registration of the client
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
            install_validation = InstallValidator(
                self.client_obj.client_hostname,
                self,
                machine_object=self.windows_machine,
                package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                media_path=None)
            install_validation.validate_install(
                **{"validate_company": True,
                   "company": self.config_json.Install.mastercs.tenants.Auto_Tenant1.name}
            )

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
