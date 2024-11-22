# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate download and install service pack on the CS.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install.update_helper import UpdateHelper
from Install import installer_utils
from cvpysdk.commcell import Commcell
from AutomationUtils import config, constants
from Install.installer_constants import DEFAULT_COMMSERV_USER
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures, WindowsDownloadFeatures
from AutomationUtils.machine import Machine
import time


class TestCase(CVTestCase):
    """Class for executing Daily CS, Webserver, LTS Client and RC Patching """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Daily CS, Webserver, LTS Client and RC Patching"
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.unix_machine = None
        self.unix_helper = None
        self.update_helper = None
        self.config_json = None
        self.default_log_directory = None
        self.clientgrp = ""
        self.tcinputs = {
            'ServicePack': None
        }
        self.cs_machine = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell)
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password)
        self.update_helper = UpdateHelper(self.commcell, self.cs_machine)
        self.unix_rc_1 = self.config_json.Install.rc_automation.rc_machines.rc_unix_1.hostname
        self.unix_rc_2 = self.config_json.Install.rc_automation.rc_machines.rc_unix_2.hostname
        self.windows_rc_1 = self.config_json.Install.rc_automation.rc_machines.rc_windows_1.hostname
        self.webserver = self.config_json.Install.webserver_client.machine_host
        self.lts_client = self.config_json.Install.lts_client.machine_host
        self.clientgrp = self.config_json.Install.daily_upgrade.client_group_name

    def run(self):
        """Main function for test case execution"""
        try:
            # Patching the CS
            _sp_transaction = installer_utils.get_latest_recut_from_xml(self.tcinputs.get("ServicePack"))
            self.log.info(f"Starting Service pack upgrade of CS from "
                          f"SP{str(self.commcell.commserv_version)} to {self.tcinputs.get('ServicePack')}")
            self.update_helper.push_sp_upgrade(client_computers=[self.commcell.commserv_name])
            self.log.info("SP upgrade of CS successful")

            self.log.info("Downloading and Installing latest updates on CS")
            self.update_helper.push_maintenance_release(
                client_computers=[self.commcell.commserv_name], download_software=False)

            self.log.info("Login to Commcell after CS Upgrade")
            time.sleep(600)
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)

            self.log.info("Checking Readiness of the CS machine")
            _commserv_client = self.commcell.commserv_client
            if _commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Check Readiness Failed")

            self.log.info("Starting Install Validation")
            package_list = [UnixDownloadFeatures.COMMSERVE.value] if self.commcell.is_linux_commserv \
                else [WindowsDownloadFeatures.COMMSERVE.value]
            install_validation = InstallValidator(_commserv_client.client_hostname, self,
                                                  machine_object=self.cs_machine, package_list=package_list,
                                                  feature_release=_sp_transaction, is_push_job=True)
            install_validation.validate_install()

            # Patching the RC's and the webserver
            self.log.info(f"Adding clients to the group {self.clientgrp}")
            if not self.commcell.client_groups.has_clientgroup(self.clientgrp):
                self.commcell.client_groups.add(
                    self.clientgrp,
                    [self.commcell.clients.get(self.unix_rc_1).client_name,
                     self.commcell.clients.get(self.unix_rc_2).client_name,
                     self.commcell.clients.get(self.windows_rc_1).client_name,
                     self.commcell.clients.get(self.webserver).client_name
                     ])
            else:
                _client_group_obj = self.commcell.client_groups.get(self.clientgrp)
                _client_group_obj.add_clients(
                    [self.commcell.clients.get(self.unix_rc_1).client_name,
                     self.commcell.clients.get(self.unix_rc_2).client_name,
                     self.commcell.clients.get(self.windows_rc_1).client_name,
                     self.commcell.clients.get(self.webserver).client_name
                     ], overwrite=True)

            # Calls the push service pack and hotfixes job
            job_obj = self.commcell.push_servicepack_and_hotfix(
                client_computer_groups=[self.clientgrp], reboot_client=True)
            if self.update_helper.check_job_status(job_obj, wait_time=90):
                self.log.info("Successfully finished Upgrading clients")
            else:
                raise Exception("Upgrade job failed!!")

            self.log.info("Initiating Check Readiness from the CS")
            for each_client in [self.unix_rc_1,
                                self.unix_rc_2,
                                self.windows_rc_1,
                                self.webserver]:
                if self.commcell.clients.has_client(each_client):
                    client_obj = self.commcell.clients.get(each_client)
                    if client_obj.is_ready:
                        self.log.info("Check Readiness of Client is successful")
                else:
                    self.log.error("Client failed Registration to the CS")
                    raise Exception(
                        f"Client: {each_client} failed registering to the CS, Please check client logs")

                self.log.info("Starting Install Validation")
                install_validation = InstallValidator(each_client, self, is_push_job=True)
                install_validation.validate_install()

            # Updating the LTS Client 
            self.log.info("Downloading and Installing latest updates on CS")
            self.update_helper.push_maintenance_release(
                client_computers=[self.commcell.clients.get(self.lts_client).client_name], 
                download_software=True)
            
            # Validating the LTS Client
            self.log.info("Starting LTS Install Validation")
            install_validation = InstallValidator(
                self.lts_client, 
                self,
                is_push_job=True,
                **{"feature_release": self.config_json.Install.lts_client.version})
            install_validation.validate_install(
                **{"validate_baseline": False})

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

