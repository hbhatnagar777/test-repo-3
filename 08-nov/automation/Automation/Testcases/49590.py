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
from threading import Thread
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install import installer_utils
from AutomationUtils import config, constants


class TestCase(CVTestCase):
    """Testcase : SP-1 Installation of Windows,Linux Clients"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "SP-2 Installation of Windows,Linux Clients"
        self.install_helper = None
        self.commcell = None
        self.windows_machine = None
        self.windows_helper = None
        self.config_json = None
        self.client_obj = None
        self.unix_machine = None
        self.unix_helper = None
        self.authcode = None
        self.default_log_directory = None
        self.clientgrp = "SPUpgrade"
        self.tcinputs = {
            'ServicePack': None
        }

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
        self.unix_machine = self.install_helper.get_machine_objects(type_of_machines=2)[0]

        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.unix_helper = InstallHelper(self.commcell, self.unix_machine)
        self.authcode = self.commcell.enable_auth_code()

    def install_client(self, q, bootstrapper_install=False):
        """
        Interactively Install the client
        Args:
            q                       --  queue with details of the client machine and its helper file

            bootstrapper_install    --  bool value to determine if it's a bootstrapper install

        Returns:

        """
        try:
            self.log.info("Launched Thread to install client")
            client_machine = q
            client_helper = InstallHelper(self.commcell, client_machine)
            if client_machine.check_registry_exists("Session", "nCVDPORT"):
                client_helper.uninstall_client(delete_client=False)

            silent_install_dict = {
                "csClientName": self.commcell.commserv_name,
                "csHostname": self.commcell.commserv_hostname,
                "authCode": self.authcode
            }

            self.log.info("Determining Media Path for Installation")
            _media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else self.config_json.Install.commserve_client.sp_version
            _minus_value = self.config_json.Install.minus_value
            _service_pack = "SP" + str(int(_service_pack.lower().split('sp')[-1]) - _minus_value)
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            if "{sp_to_install}" in _media_path:
                _service_pack = _service_pack.split('_', maxsplit=1)[0] if '_' in _service_pack else _service_pack
                _media_path = _media_path.replace("{sp_to_install}", _service_pack_to_install)

            self.log.info(f"Service pack to Install {_service_pack}")
            _media_path = '' if bootstrapper_install else _media_path
            if _media_path:
                silent_install_dict["mediaPath"] = _media_path
                self.log.info(f"Media Path used for Installation: {_media_path}")
            self.log.info(f"Installing client on {client_machine.machine_name}")
            client_helper.silent_install(
                client_name=client_machine.machine_name, tcinputs=silent_install_dict, feature_release=_service_pack)

            self.log.info("Refreshing Client List on the CS")
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

            media_path = None if bootstrapper_install else _media_path
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(
                client_obj.client_hostname, self, machine_object=client_machine,
                media_path=media_path if media_path else None,
                feature_release=str(int(_service_pack.lower().split('sp')[-1])))
            install_validation.validate_install()

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def run(self):
        """Run function of this test case"""
        try:
            t1 = Thread(target=self.install_client, args=(self.windows_machine, True))
            t2 = Thread(target=self.install_client, args=(self.unix_machine,))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            self.log.info("all Threads Executed successfully")
            self.log.info(f"adding clients to the group {self.clientgrp}")
            if not self.commcell.client_groups.has_clientgroup(self.clientgrp):
                self.commcell.client_groups.add(
                    self.clientgrp, [self.commcell.clients.get(self.windows_machine.machine_name).client_name,
                                     self.commcell.clients.get(self.unix_machine.machine_name).client_name])
            else:
                _client_group_obj = self.commcell.client_groups.get(self.clientgrp)
                _client_group_obj.add_clients(
                    [self.commcell.clients.get(self.windows_machine.machine_name).client_name,
                     self.commcell.clients.get(self.unix_machine.machine_name).client_name], overwrite=True)

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == "FAILED":
            installer_utils.collect_logs_after_install(self, self.windows_machine)
            installer_utils.collect_logs_after_install(self, self.unix_machine)
