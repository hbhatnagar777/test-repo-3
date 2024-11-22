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
from Install.update_helper import UpdateHelper


class TestCase(CVTestCase):
    """Testcase : Push Service Pack Upgrade of a 32bit Client"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Push Service Pack Upgrade of a 32bit Client"
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.config_json = None
        self.machine_name = None
        self.client_obj = None
        self.media_path = None
        self.update_acceptance = False
        self.clientgrp = "SPUpgrade"
        self.silent_install_dict = {}
        self.update_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell, tc_object=self)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=3)[0]
        self.machine_name = self.windows_machine.machine_name
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.silent_install_dict = {
            "csClientName": self.commcell.commserv_name,
            "csHostname": self.commcell.commserv_hostname,
            "authCode": self.commcell.enable_auth_code(),
            "instance": "Instance001"
        }
        self.update_helper = UpdateHelper(self.commcell)
        self.clientgrp = self.config_json.Install.windowspush.client_group_name

    def run(self):
        """Run function of this test case"""
        try:
            # Deleting a client if it exists
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=False)

            # Determining the media path for the installation
            self.log.info("Determining Media Path for Installation")
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else "SP" + str(self.commcell.commserv_version)

            # Reducing the service pack value
            _service_pack = int(_service_pack[2:]) - int(self.tcinputs["MinusValue"])
            self.log.info(f"Service pack to Install {_service_pack}")
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            self.log.info(f"Service Pack used for Installation: {_service_pack_to_install}")

            # Installing a fresh client on 32 bit machine on lower media 
            self.log.info(f"Installing fresh windows client on {self.machine_name}")
            self.windows_helper.silent_install(
                client_name=self.id,
                tcinputs=self.silent_install_dict, feature_release=_service_pack_to_install, packages=['FILE_SYSTEM'])
            
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

            # Calls the push service pack and hotfixes job
            job_obj = self.commcell.push_servicepack_and_hotfix(
                client_computers=[self.id], reboot_client=False)
            if self.update_helper.check_job_status(job_obj, wait_time=90):
                self.log.info("Successfully finished Upgrading clients")
            else:
                raise Exception("Upgrade job failed!!")
            
            # Refreshing the client list on the CS
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
        # Deleting the client
        self.windows_helper.uninstall_client(delete_client=True)
