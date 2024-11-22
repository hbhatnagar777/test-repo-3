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
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures

from AutomationUtils.cvtestcase import CVTestCase
from datetime import datetime as dt
from AutomationUtils.machine import Machine
from Install import installer_utils
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils import constants, config, logger
from cvpysdk.commcell import Commcell
from Install.install_validator import InstallValidator
from Install.install_helper import InstallHelper
from Install.installer_constants import WINDOWS_FIREWALL_INBOUND_EXCLUSION_LIST, BLOCK_INCOMING_CONNECTION
from Install.installer_constants import BLOCK_OUT_GOING_PORTS_COMMAND, DEFAULT_OUTGOING_PORTS, \
    BLOCK_DIRECT_CONNECTION_TO_CS
import socket


class TestCase(CVTestCase):
    """Testcase : Fresh Push Install to Windows Client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Install & Firewall] Windows- Push - CS can open communication to client"
        self.config_json = None
        self.option_selector = None
        self.rc_client = None
        self.client_machine = None
        self.machine_name = None
        self.client_helper = None
        self.client_obj = None

        self.dummy_client_name = None
        self.client_group_name = None
        self.commserv = None
        self.clientCSName = None
        self.time_stamp = None
        self.cs_machine = None
        self.service_pack = None
        self.port_number = None
        self.incoming_ports = ','.join(['135', '445', '24158'])

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
            "firewallConnectionType": 1,
            "proxyClientName": "",
            "proxyHostName": "",
            "portNumber": self.config_json.Install.firewall_port,
            "httpProxyConfigurationType": 0,
            "encryptedTunnel": False
        }
        self.port_number = str(self.config_json.Install.firewall_port)
        self.time_stamp = str(dt.now().microsecond)
        self.tcinputs["clientGroupName"] = "cs_to_cl_client_group"

        self.client_group_name = self.tcinputs["clientGroupName"]
        self.dummy_client_name = "test_50853_" + self.time_stamp
        self.clientCSName = "cs_to_cl_commserv_group"
        self.cs_machine = Machine(self.commcell.commserv_client)
        self.log.info("Setup function executed")

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

    def set_firewall_prerequisites(self):
        """
        This method does all the firewall setiing to be executed for the testcase
        Returns: None
        """
        self.log.info("Step 1: Enable firewall on commserve")
        self._network.enable_firewall([self.commserv], [int(self.port_number)])
        self._network.set_tunnelport([{'clientName': self.commserv}], [int(self.port_number)])
        self.cs_machine.add_firewall_machine_exclusion()
        if not self.commcell.is_linux_commserv:
            self.cs_machine.disable_firewall_rules(WINDOWS_FIREWALL_INBOUND_EXCLUSION_LIST)
            _cmd = BLOCK_INCOMING_CONNECTION.format("Block_client",
                                                    str(socket.gethostbyname(self.machine_name)),
                                                    self.port_number)
            self.log.info("command to block client is {0}".format(_cmd))
            _output = self.cs_machine.execute_command(_cmd)
            self.log.info(_output.output)

        self.log.info("Step 2: disable firewall on client and add inbound rule")
        self.client_machine.stop_firewall()
        self.client_machine.add_firewall_allow_port_rule(int(self.port_number))

        self.log.info("Step 3: Create Dummy Client with default port")
        self.commcell.clients.create_pseudo_client(self.dummy_client_name, self.machine_name)

        self.log.info("Step 4: setting tunnel port")
        self._network.set_tunnelport([{'clientName': self.dummy_client_name}], [int(self.port_number)])

        self.log.info("Step 5: Create client group and commserve group")
        # self.commcell.client_groups.add(self.client_group_name, [self.dummy_client_name])
        if not self.commcell.client_groups.has_clientgroup(self.client_group_name):
            self.commcell.client_groups.add(self.client_group_name, [self.dummy_client_name])
        else:
            _client_group_obj = self.commcell.client_groups.get(self.client_group_name)
            _client_group_obj.remove_all_clients()
            _client_group_obj.add_clients([self.dummy_client_name],
                                          overwrite=False)
        if not self.commcell.client_groups.has_clientgroup(self.clientCSName):
            self.commcell.client_groups.add(self.clientCSName, [self.commserv])
        else:
            _client_group_obj = self.commcell.client_groups.get(self.clientCSName)
            _client_group_obj.remove_all_clients()
            _client_group_obj.add_clients([self.commserv],
                                          overwrite=False)

        self.log.info("Step 6: Set one way network Topology from commserve group to client group")
        topology_name = "cs_to_cl"
        self._network.one_way_topology(self.clientCSName, self.client_group_name, topology_name)

        self.client_machine.add_firewall_machine_exclusion()
        self.client_machine.start_firewall()
        self.log.info("step 7: Block the outgoing ports on the client")
        _cmd = BLOCK_OUT_GOING_PORTS_COMMAND.format('BLOCK_PORTS', ','.join([str(i) for i in DEFAULT_OUTGOING_PORTS]))
        _output = self.client_machine.execute_command(_cmd)
        self.log.info(_output.output)

        self.log.info("step 8: Block direct connection from client to CS")
        _cmd = BLOCK_DIRECT_CONNECTION_TO_CS.format('BLOCK_CS',
                                                    str(socket.gethostbyname
                                                        (self.config_json.Install.commserve_client.machine_host)))
        _output = self.client_machine.execute_command(_cmd)

        self.log.info("step 9: Allow Connection on WMI port and other necessary ports")
        self.client_machine.add_firewall_allow_port_rule(self.incoming_ports)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Inside run function")

            if self.client_machine.check_registry_exists("Session", "nCVDPORT"):
                self.client_helper.uninstall_client(delete_client=True)

            # Configuring Windows Remote Cache for Fresh Push Install to Windows Machine
            # Please provide RC Client Name on config file - [Install.rc_client.client_name]
            if self.commcell.is_linux_commserv:
                self.set_remote_cache_configuration()

            self.log.info(f"Service Pack to be Installed on the client: {self.commcell.commserv_version}")
            self.log.info(f"Pushing fresh windows client on {self.machine_name} with Firewall configuration"
                          f"CS can open communication to client ")

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
            self.cs_machine.remove_firewall_rules(["Block_client"])
            self.cs_machine.remove_firewall_machine_exclusion()
        self.client_machine.stop_firewall()
        self.client_machine.remove_firewall_allow_port_rule(int(self.port_number))
        self.client_machine.remove_firewall_allow_port_rule(self.incoming_ports)
        self.client_machine.remove_firewall_machine_exclusion()
        self.client_machine.remove_firewall_rules(['BLOCK_PORTS', 'BLOCK_CS'])
        if self.status == "FAILED":
            installer_utils.collect_logs_after_install(self, self.client_machine)
        if self.client_machine.check_registry_exists("Session", "nCVDPORT"):
            self.client_helper.uninstall_client(delete_client=False)
        if self.commcell.clients.has_client(self.client_obj.client_name):
            self.commcell.clients.delete(self.client_obj.client_name)
