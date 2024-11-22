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
import random
from Install import installer_utils
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install.installer_constants import DEFAULT_COMMSERV_USER
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Fresh Installation of Unix Client"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Fresh Installation of Unix Client"
        self.install_helper = None
        self.unix_machine = None
        self.unix_helper = None
        self.config_json = None
        self.machine_name = None
        self.client_obj = None
        self.media_path = None
        self.update_acceptance = False
        self.silent_install_dict = {}
        self.tcinputs = {}
        self.default_log_directory = None
        self.commcell = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell, tc_object=self)
        self.unix_machine = self.install_helper.get_machine_objects(type_of_machines=2)[0]
        self.machine_name = self.unix_machine.machine_name
        self.unix_helper = InstallHelper(self.commcell, self.unix_machine)
        self.silent_install_dict = {
            "csClientName": self.commcell.commserv_name,
            "csHostname": self.commcell.commserv_hostname,
            "authCode": self.commcell.enable_auth_code()
        }
        self.update_acceptance = self.config_json.Install.update_acceptance_database

    def run(self):
        """Run function of this test case"""
        try:
            if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
                self.unix_helper.uninstall_client(delete_client=False)

            self.log.info("Determining Media Path for Installation")
            self.media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else "SP" + str(self.commcell.commserv_version)
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            if "{sp_to_install}" in self.media_path:
                _service_pack = _service_pack.split('_')[0] if '_' in _service_pack else _service_pack
                self.media_path = self.media_path.replace("{sp_to_install}", _service_pack_to_install)
            self.log.info(f"Service Pack used for Installation: {_service_pack}")
            if self.media_path:
                self.log.info(f"Media Path used for Installation: {self.media_path}")
                self.silent_install_dict.update({"mediaPath": self.media_path})

            self.log.info(f"Installing fresh unix client on {self.machine_name}")
            if self.update_acceptance:
                self.install_helper.install_acceptance_insert()
            self.unix_helper.silent_install(
                client_name=self.name.replace(" ", "_") + "_" + str(random.randint(1000, 9999)),
                tcinputs=self.silent_install_dict, packages=['FILE_SYSTEM'])
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

            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.unix_machine,
                                                  package_list=[UnixDownloadFeatures.FILE_SYSTEM.value],
                                                  media_path=self.media_path if self.media_path else None)
            install_validation.validate_install()

            if self.update_acceptance:
                self.install_helper.install_acceptance_update('Pass', '-', self.unix_machine.machine_name)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            if self.update_acceptance:
                self.install_helper.install_acceptance_update(
                    'Fail', str(exp).replace("'", ''), self.unix_machine.machine_name,
                    _service_pack_to_install.split('_R')[-1])

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.unix_machine)
            if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
                self.unix_helper.uninstall_client(delete_client=True)
