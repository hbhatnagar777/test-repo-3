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
from threading import Thread
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install.update_helper import UpdateHelper
from Install import installer_utils
from AutomationUtils import config, constants
from AutomationUtils.machine import Machine
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures, WindowsDownloadFeatures

class TestCase(CVTestCase):
    """Testcase : Push SP Upgrade of windows and unix Web Servers"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Push SP Upgrade of windows and unix Web Servers"
        self.windows_machine = None
        self.unix_machine = None
        self.windows_helper = None
        self.unix_helper = None
        self.config_json = None
        self.update_helper = None
        self.tcinputs = {
            'ServicePack': None
        }
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)
        self.windows_machine = Machine(
            machine_name=self.config_json.Install.win_web_server.machine_host,
            username=self.config_json.Install.win_web_server.machine_username,
            password=self.config_json.Install.win_web_server.machine_password)
        self.unix_machine = Machine(
            machine_name=self.config_json.Install.unix_web_server.machine_host,
            username=self.config_json.Install.unix_web_server.machine_username,
            password=self.config_json.Install.unix_web_server.machine_password)
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.unix_helper = InstallHelper(self.commcell, self.unix_machine)
        self.update_helper = UpdateHelper(self.commcell)

    def install_client(self, q, bootstrapper_install=False, is_unix_machine=False):
        """
        Interactively Install the client
        Args:
            q                       --  queue with details of the client machine and its helper file

            bootstrapper_install    --  bool value to determine if it's a bootstrapper install

        Returns:

        """
        try:
            client_machine = q
            self.log.info(f"Launched Thread to install client {client_machine.machine_name}")
            self.log.info("Installing client in SP-2")
            client_helper = InstallHelper(self.commcell, client_machine)
            if client_machine.check_registry_exists("Session", "nCVDPORT"):
                client_helper.uninstall_client(delete_client=True)

            silent_install_dict = {
                "csClientName": self.commcell.commserv_name,
                "csHostname": self.commcell.commserv_hostname,
                "commservePassword": self.config_json.Install.cs_encrypted_password
            }

            if is_unix_machine:
                silent_install_dict["sqlSaPassword"] = self.config_json.Install.unix_web_server.saPassword

            self.log.info("Determining Media Path for Installation")
            media_path = '' if bootstrapper_install else (self.tcinputs.get('MediaPath')
                                                          if self.tcinputs.get('MediaPath') else '')
            _service_pack = self.tcinputs.get("ServicePack")
            if "{sp_to_install}" in media_path:
                if self.tcinputs.get("ServicePack") is None:
                    _service_pack = self.commcell.commserv_version
                else:
                    if '_' in _service_pack:
                        _service_pack = _service_pack.split('_')[0]
            _service_pack = _service_pack.lower().split('sp')[1]
            _minus_value = self.config_json.Install.minus_value
            _service_pack_to_install = int(_service_pack[2:]) - int(_minus_value) if _minus_value \
                else int(_service_pack)
            self.log.info(f"Service pack to Install {_service_pack_to_install}")
            if '_' not in _service_pack:
                _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_to_install)
                media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
            if media_path:
                silent_install_dict.update({"mediaPath": media_path})
                self.log.info("Media Path used for Installation: %s" % media_path)
            self.log.info(f"Installing client on {client_machine.machine_name}")
            client_helper.silent_install(
                client_name=client_machine.machine_name,
                tcinputs=silent_install_dict,
                feature_release=_service_pack_to_install,
                packages=["WEB_SERVER"])

            self.log.info("Refreshing Client List on the CS")
            time.sleep(60)
            self.commcell.refresh()

            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(client_machine.machine_name):
                client_obj = self.commcell.clients.get(client_machine.machine_name)
                if client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(
                    f"Client: {client_machine.machine_name} failed registering to the CS, Please check client logs")

            media_path = None if bootstrapper_install else media_path
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(client_obj.client_name, self, machine_object=client_machine,
                                                  media_path=media_path if media_path else None)
            install_validation.validate_install(validate_sp_info_in_db=False, validate_baseline=False)

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def run(self):
        """Run function of this test case"""
        try:
            t1 = Thread(target=self.install_client, args=(self.windows_machine, True))
            t2 = Thread(target=self.install_client, args=(self.unix_machine, True, True))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            self.log.info("All Threads executed successfully")
            if self.status == constants.FAILED:
                raise Exception(self.result_string)

            _windows_client_obj = self.commcell.clients.get(self.windows_machine.machine_name)
            _unix_client_obj = self.commcell.clients.get(self.unix_machine.machine_name)
            clients = [_windows_client_obj.client_name, _unix_client_obj.client_name]

            # Push SP upgrade on clients
            self.log.info(f"Push SP upgrade on clients {clients[0]}, {clients[1]}")
            job_obj = self.commcell.push_servicepack_and_hotfix(
                client_computers=clients, reboot_client=True)
            if self.update_helper.check_job_status(job_obj, wait_time=90):
                self.log.info(f"Successfully finished Upgrading clients")
            else:
                raise Exception("Upgrade job failed!!")
            self.log.info("Initiating Check Readiness from the CS")
            for each_client in [self.windows_machine.machine_name, self.unix_machine.machine_name]:
                if self.commcell.clients.has_client(each_client):
                    client_obj = self.commcell.clients.get(each_client)
                    if client_obj.is_ready:
                        self.log.info(f"Check Readiness of Client {each_client} is successful")
                else:
                    self.log.error(f"Client {each_client} failed Registration to the CS")
                    raise Exception(
                        f"Client: {each_client} failed registering to the CS, Please check client logs")
                if each_client == self.windows_machine.machine_name:
                    pkg_list = [WindowsDownloadFeatures.WEB_SERVER.value]
                else:
                    pkg_list = [UnixDownloadFeatures.WEB_SERVER.value]
                self.log.info(f"Starting Upgrade Validation of client {each_client}")
                install_validation = InstallValidator(each_client, self, is_push_job=True, package_list=pkg_list)
                install_validation.validate_install()

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == "FAILED":
            installer_utils.collect_logs_after_install(self, self.windows_machine)
            installer_utils.collect_logs_after_install(self, self.unix_machine)