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
from Install.update_helper import UpdateHelper
from Install.installer_constants import DEFAULT_COMMSERV_USER
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Testcase : Push upgrade of RC"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Push SP Upgrade of Windows RC and Linux RC with cache synced"
        self.config_json = None
        self.update_helper = None
        self.windows_machine = None
        self.unix_machine = None
        self.windows_helper = None
        self.unix_helper = None
        self.client_obj = None
        self.client_group = "RC Client Group"
        self.silent_install_dict = {}

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.windows_machine = Machine(
            machine_name=self.config_json.Install.rc_automation.rc_machines.rc_windows_2.hostname,
            username=self.config_json.Install.rc_automation.rc_machines.rc_windows_2.username,
            password=self.config_json.Install.rc_automation.rc_machines.rc_windows_2.password)
        self.unix_machine = Machine(
            machine_name=self.config_json.Install.rc_automation.rc_machines.rc_unix_2.hostname,
            username=self.config_json.Install.rc_automation.rc_machines.rc_unix_2.username,
            password=self.config_json.Install.rc_automation.rc_machines.rc_unix_2.password)
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.unix_helper = InstallHelper(self.commcell, self.unix_machine)
        self.update_helper = UpdateHelper(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            # Creating a new client group and adding the clients to it
            _windows_client_obj = self.commcell.clients.get(self.windows_machine.machine_name)
            _unix_client_obj = self.commcell.clients.get(self.unix_machine.machine_name)
            clients = [_windows_client_obj.client_name, _unix_client_obj.client_name]
            self.log.info(f"Adding clients {clients} to the Client group {self.client_group}")
            if not self.commcell.client_groups.has_clientgroup(self.client_group):
                self.commcell.client_groups.add(
                    self.client_group, clients)
            else:
                _client_group_obj = self.commcell.client_groups.get(self.client_group)
                _client_group_obj.add_clients(clients)

            # Push upgrade The RC
            job_obj = self.commcell.push_servicepack_and_hotfix(client_computers=clients,
                                                                reboot_client=True)
            if self.update_helper.check_job_status(job_obj, wait_time=90):
                self.log.info("Successfully finished Upgrading clients")
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

                self.log.info(f"Starting Upgrade Validation of client {each_client}")
                install_validation = InstallValidator(each_client, self, is_push_job=True)
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
            self.windows_helper.uninstall_client(delete_client=False)
        if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
            self.unix_helper.uninstall_client(delete_client=False)
