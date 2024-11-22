# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from datetime import datetime as dt
from AutomationUtils.machine import Machine
from Install import installer_utils
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils import constants, config, logger
from cvpysdk.commcell import Commcell
from Install.install_validator import InstallValidator
from Install.install_helper import InstallHelper
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures

class TestCase(CVTestCase):
    """Testcase : Fresh Push Install to Windows Client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Install & Firewall] Windows- Push - client can open communication to CS"
        self.install_helper = None
        self.config_json = None
        self.option_selector = None
        self.rc_client = None
        self.client_machine = None
        self.client_helper = None
        self.client_obj = None

        self.dummy_client_name = None
        self.client_group_name = None
        self.commserv = None
        self.clientCSName = None
        self.time_stamp = None
        self.port_number = None
        self.cs_machine = None
        self.service_pack = None

        # Helper objects
        self._network = None
        self.tcinputs = {
            'ServicePack': None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.log = logger.get_log()
        self.log.info("running setup function")
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=self.config_json.Install.commserve_client.webserver_username,
                commcell_password=self.config_json.Install.commserve_client.cs_password)

        self.commserv = self.commcell.commserv_name
        self._network = NetworkHelper(self)
        self.cs_machine = Machine(self.commcell.commserv_client)

        self.install_helper = InstallHelper(self.commcell)
        self.client_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.machine_name = self.client_machine.machine_name
        self.client_helper = InstallHelper(self.commcell, self.client_machine)

        # Set tcinputs
        self.firewall_inputs = {
            "enableFirewallConfig": True,
            "firewallConnectionType": 0,
            "proxyClientName": "",
            "proxyHostName": "",
            "portNumber": self.config_json.Install.firewall_port,
            "httpProxyConfigurationType": 0,
            "encryptedTunnel": False
        }
        self.port_number = str(self.config_json.Install.firewall_port)
        self.time_stamp = str(dt.now().microsecond)
        self.tcinputs["clientGroupName"] = "cl_to_cs_client_group"

        self.client_group_name = self.tcinputs["clientGroupName"]
        self.dummy_client_name = "test_50852_" + self.time_stamp
        self.clientCSName = "cl_to_cs_commserv_group"
        self.log.info("Setup function executed")

    def set_firewall_prerequisites(self):
        """
        This method does all the firewall setiing to be executed for the testcase
        Returns: None
        """
        self.log.info("Step 1: Enable firewall on commserve")
        self.cs_machine.add_firewall_machine_exclusion()
        self._network.enable_firewall([self.commserv], [int(self.port_number)])

        self.log.info("Step 2: setting tunnel port")
        self._network.set_tunnelport([{'clientName': self.commserv}], [int(self.port_number)])

        self.log.info("Step 3: Create client group and commserve group")
        if not self.commcell.client_groups.has_clientgroup(self.client_group_name):
            self.commcell.client_groups.add(self.client_group_name)
        if not self.commcell.client_groups.has_clientgroup(self.clientCSName):
            self.commcell.client_groups.add(self.clientCSName, [self.commserv])
        else:
            _client_group_obj = self.commcell.client_groups.get(self.clientCSName)
            _client_group_obj.remove_all_clients()
            _client_group_obj.add_clients([self.commserv],
                                          overwrite=False)

        self.log.info("Step 4: Set one way network Topology from commserve group to client group")
        topology_name = "cl_to_cs"
        self._network.one_way_topology(self.clientCSName, self.client_group_name, topology_name)

    def set_remote_cache_configuration(self):
        """
        Push Installation from LinuxCS to Windows client is not possible without RC
        This Method does RC configuration
        """
        # Configuring Remote Cache Client to Push Software to Windows Client
        self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                      "Direct push Installation to Windows Client")
        is_windows = False
        rc_client_name = self.config_json.Install.rc_client.client_name
        if self.commcell.clients.has_client(rc_client_name):
            self.rc_client = self.commcell.clients.get(rc_client_name)
            if "windows" in self.rc_client.os_info.lower():
                is_windows = True

        # Finding a Windows Machine and Configuring it as an RC
        if not is_windows:
            self.rc_client = None
            self.log.info("Finding any Windows Machine from Client List to Configure it as an RC")
            all_clients_list = self.commcell.clients.all_clients
            for client_name in all_clients_list:
                if "windows" in self.commcell.clients.get(client_name).os_info.lower():
                    self.log.info(f"Found windows machine: {client_name}--> Configuring it as RC")
                    self.rc_client = self.commcell.clients.get(client_name)
                    break
                else:
                    continue

            if self.rc_client is None:
                self.log.error("Please configure a Windows Machine as RC to Push Software")
                self.log.error("Linux CS do not support Push Software to Windows Machine")
                raise Exception("Windows RC needed to push software to a new Windows Client")

        self.log.info(f"Configuring {self.rc_client.client_name} as Remote Cache")
        rc_helper = self.commcell.get_remote_cache(self.rc_client.client_name)
        cache_path = f"{self.rc_client.install_directory}\\SoftwareCache"
        rc_helper.configure_remotecache(cache_path=cache_path)
        self.log.info(f"Configured Remote Cache Path: {cache_path}")
        rc_helper.configure_packages_to_sync(win_os=["WINDOWS_64"],
                                             win_package_list=["FILE_SYSTEM", "MEDIA_AGENT"])
        self.log.info(f"Starting a Sync Job on the client : {self.rc_client.client_name}")
        sync_job = self.commcell.sync_remote_cache(client_list=[self.rc_client.client_name])
        if sync_job.wait_for_completion(20):
            self.log.info("WindowsX64 Packages Synced to RC successfully")

        else:
            job_status = sync_job.delay_reason
            self.log.error("Sync Job Failed; Please check the Logs on CS")
            raise Exception(job_status)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Inside run function")

            if self.client_machine.check_registry_exists("Session", "nCVDPORT"):
                self.client_helper.uninstall_client(delete_client=True)
            if self.commcell.is_linux_commserv:
                self.set_remote_cache_configuration()
            self.set_firewall_prerequisites()
            # Pushing Packages from CS to the client
            self.log.info(f"Starting a Push Install Job on the Machine: {self.machine_name}")

            if self.rc_client:
                push_job = self.client_helper.install_software(
                                client_computers=[self.machine_name],
                                features=['FILE_SYSTEM'],
                                username=self.config_json.Install.windows_client.machine_username,
                                password=self.config_json.Install.windows_client.machine_password,
                                client_group_name=[self.client_group_name],
                                sw_cache_client=self.rc_client.client_name,
                                firewall_inputs=self.firewall_inputs)
            else:
                push_job = self.client_helper.install_software(
                                client_computers=[self.machine_name],
                                features=['FILE_SYSTEM'],
                                username=self.config_json.Install.windows_client.machine_username,
                                password=self.config_json.Install.windows_client.machine_password,
                                client_group_name=[self.client_group_name],
                                firewall_inputs=self.firewall_inputs)
            self.log.info(f"Job Launched Successfully, Will wait until Job: {push_job.job_id} Completes")
            if push_job.wait_for_completion():
                self.log.info("Push Install Job Completed successfully")

            else:
                job_status = push_job.delay_reason
                self.log.error(f"Job failed with an error: {job_status}")
                raise Exception(job_status)

            # Refreshing the Client list to me the New Client Visible on GUI
            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            # Check if the services are up on Client and is Reachable from CS
            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.machine_name} failed registering to the CS, "
                                f"Please check client logs")

            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.client_machine,
                                                  package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                                                  is_push_job=True)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if not self.commcell.is_linux_commserv:
            self.cs_machine.stop_firewall()
            self.cs_machine.remove_firewall_allow_port_rule(int(self.port_number))
            self.cs_machine.remove_firewall_machine_exclusion()
        if self.status == "FAILED":
            installer_utils.collect_logs_after_install(self, self.client_machine)
        if self.client_machine.check_registry_exists("Session", "nCVDPORT"):
            self.client_helper.uninstall_client(delete_client=False)
        if self.commcell.clients.has_client(self.client_obj.client_name):
            self.commcell.clients.delete(self.client_obj.client_name)
