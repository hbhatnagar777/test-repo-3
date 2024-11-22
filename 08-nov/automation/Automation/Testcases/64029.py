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
import time

from AutomationUtils.options_selector import OptionsSelector
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install import installer_utils
from Install.installer_constants import DEFAULT_COMMSERV_USER
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from Install.sim_call_helper import SimCallHelper


class TestCase(CVTestCase):
    """Testcase : Register decoupled windows install"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self._service_pack_to_install = None
        self.name = "Register decoupled windows install"
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.config_json = None
        self.machine_name = None
        self.media_path = None
        self.client_obj = None
        self.sim_caller = None
        self.options_selector = None
        self.silent_install_dict = {}

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell, tc_object=self)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.machine_name = self.windows_machine.machine_name
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.sim_caller = SimCallHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        self.silent_install_dict = {
            "csClientName": "",
            "decoupledInstall": "1",
        }

    def run(self):
        """Run function of this test case"""
        try:
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=False)

            # Determining media path
            self.log.info("Determining Media Path for Installation")
            self.media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else "SP" + str(self.commcell.commserv_version)
            _service_pack = _service_pack.split('_')[0] if '_' in _service_pack else _service_pack

            # getting latest recut
            self._service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            if "{sp_to_install}" in self.media_path:
                self.media_path = self.media_path.replace("{sp_to_install}", self._service_pack_to_install)
            self.log.info(f"Service Pack used for Installation: {_service_pack}")
            self.log.info(f"Media Path used for Installation: {self.media_path}")

            self.log.info(f"Installing fresh windows client on {self.machine_name}")

            # Silent Installation on Windows Machine
            self.windows_helper.silent_install(
                client_name=self.id, tcinputs=self.silent_install_dict,
                feature_release=_service_pack, packages=['FILE_SYSTEM'])
            self.log.info("Client Installation Completed in decoupled mode")

            # registering client to cs using SIMCallWrapper with authcode
            self.log.info("starting registration of client using authcode")
            self.sim_caller.register_to_cs(self.windows_machine, self.id,
                                           url=self.config_json.Install.commserve_client.endPoint)
            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.machine_name} failed registering to the CS, Please "
                                f"check client logs")
            # de-registering the client
            self.sim_caller.deregister_to_cs(self.windows_machine)

            self.options_selector.delete_client(self.id)

            # registering client to cs using SIMCallWrapper with password
            self.log.info("starting registration of client using username and password")
            self.sim_caller.register_to_cs(self.windows_machine, client_name=self.id,
                                           url=self.config_json.Install.commserve_client.endPoint,
                                           user=self.commcell.commcell_username,
                                           password=self.config_json.Install.cs_machine_password)

            self.log.info("Refreshing Client List on the CS")
            time.sleep(60)
            self.commcell.refresh()

            # Doing Readiness Check from cs
            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.machine_name} failed registering to the CS, Please check client logs")

            # Initiating Validate Install
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.windows_machine,
                                                  package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                                                  media_path=self.media_path if self.media_path else None)
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
