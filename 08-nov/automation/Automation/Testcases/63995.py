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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import time

from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures

from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Install import installer_utils
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install.installer_constants import DEFAULT_COMMSERV_USER
from cvpysdk.client import Client


class TestCase(CVTestCase):
    """Testcase : Fresh Installation of Windows Client and Push Repair Install"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Fresh Installation of Windows Client and Push Repair Install"
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.config_json = None
        self.machine_name = None
        self.client_obj = None
        self.silent_install_dict = {}
        self.tcinputs = {
            "ServicePack": None
        }
        self.service_pack = None

    def setup(self):
        """Setup function of this test case"""

        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.machine_name = self.windows_machine.machine_name
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.silent_install_dict = {"csClientName": self.commcell.commserv_name,
                                    "csHostname": self.commcell.commserv_hostname,
                                    "authCode": self.commcell.enable_auth_code()}
        self.clientgrp = self.config_json.Install.windowspush.client_group_name

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
            
            # Adding client to clientgroup 
            self.log.info(f"Adding clients to the group {self.clientgrp}")
            if not self.commcell.client_groups.has_clientgroup(self.clientgrp):
                self.commcell.client_groups.add(
                    self.clientgrp,
                    [self.machine_name])
            else:
                _client_group_obj = self.commcell.client_groups.get(self.clientgrp)
                _client_group_obj.add_clients(
                    [self.machine_name], overwrite=True)

            # Repairing the client with services running
            self.log.info("Starting Repair Install")
            self.windows_helper.repair_client(repair_with_creds=False)
            self.log.info("Repair Install Completed")

            # Validating the Repair Install
            self.log.info("Starting Repair Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.windows_machine,
                                                  package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                                                  media_path=None)
            install_validation.validate_install()

            # Stopping cvd service
            self.client = Client(self.commcell, self.machine_name)
            self.client._service_operations("GxCVD(Instance001)", 'STOP')
            time.sleep(30)
            machine_services = self.windows_machine.execute_command('Get-Service | Where Status'
                                                                    ' -eq "Running" | select Name')
            running_services = [service[0] for service in machine_services.formatted_output]
            self.log.info(running_services)

            # Repairing the client with services not running 
            self.log.info("Starting Repair Install")
            self.windows_helper.repair_client(repair_with_creds=True)
            self.log.info("Repair Install Completed")

            # Validating the Repair Install
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