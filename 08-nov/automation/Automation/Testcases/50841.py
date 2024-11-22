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

from AutomationUtils.cvtestcase import CVTestCase
from datetime import datetime as dt
from cvpysdk.commcell import Commcell
from AutomationUtils.machine import Machine
from Install.installer_constants import BLOCK_OUT_GOING_PORTS_COMMAND, DEFAULT_OUTGOING_PORTS, \
    BLOCK_DIRECT_CONNECTION_TO_CS
from Server.Network.networkhelper import NetworkHelper
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from AutomationUtils import logger, config, constants
from Install import installer_utils
import socket


class TestCase(CVTestCase):
    """Testcase : Fresh Installation of Windows Client"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "[Install & Firewall] Windows- Interactive - client can open communication to CS - Explicit Proxy"
        self.install_helper = None
        self.client_machine = None
        self.client_helper = None
        self.config_json = None
        self.machine_name = None
        self.client_obj = None

        self.dummy_client_name = None
        self.client_group_name = None
        self.commserv = None
        self.clientCSName = None
        self.time_stamp = None
        self.cs_machine = None
        self.service_pack = None
        self.port_number = None

        # Helper objects
        self._network = None
        self.tcinputs = {
            'ServicePack': None
        }

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.log = logger.get_log()
        self.log.info("running setup function")
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
        self.tcinputs["force_ipv4"] = "1"
        self.tcinputs["firewallConnectionType"] = "0"
        self.tcinputs["httpProxyConfigurationType"] = "1"
        self.tcinputs["portNumber"] = str(self.config_json.Install.firewall_port)
        self.tcinputs["httpProxyHostName"] = str(self.config_json.Install.httpProxyHostName)
        self.tcinputs["httpProxyPortNumber"] = str(self.config_json.Install.httpProxyPortNumber)
        self.tcinputs["enableFirewallConfig"] = "1"
        self.tcinputs["showFirewallConfigDialogs"] = "1"
        self.tcinputs["csClientName"] = self.commcell.commserv_name
        self.tcinputs["csHostname"] = self.commcell.commserv_hostname
        self.tcinputs["authCode"] = self.commcell.enable_auth_code()

        self.time_stamp = str(dt.now().microsecond)
        self.tcinputs["clientGroupName"] = "cl_to_cs_client_group"
        self.port_number = str(self.config_json.Install.firewall_port)
        self.client_group_name = self.tcinputs["clientGroupName"]
        self.dummy_client_name = "test_50841_" + self.time_stamp
        self.clientCSName = "cl_to_cs_commserv_group"
        self.log.info("Setup function executed")

    def get_service_pack_to_install(self):
        """
        This method determines the service pack and it's path for Installation
        Returns: None
        """
        self.log.info("Determining Media Path for Installation")
        if self.tcinputs.get('MediaPath') is None:
            media_path = self.config_json.Install.media_path
        else:
            media_path = self.tcinputs.get('MediaPath')
        _service_pack = self.tcinputs.get("ServicePack")
        _service_pack_to_install = _service_pack
        if "{sp_to_install}" in media_path:
            if self.tcinputs.get("ServicePack") is None:
                _service_pack_to_install = self.commcell.commserv_version
            else:
                if '_' in _service_pack:
                    _service_pack_to_install = _service_pack.split('_')[0]
                _service_pack_to_install = _service_pack.lower().split('sp')[1]
        self.log.info(f"Service pack to Install {_service_pack_to_install}")
        if not '_' in _service_pack:
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_to_install)
            media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
        self.service_pack = _service_pack_to_install

    def set_firewall_prerequisites(self):
        """
        This method does all the firewall setiing to be executed for the testcase
        Returns: None
        """
        self.log.info("Step 1: Enable firewall on commserve")
        self.cs_machine.add_firewall_machine_exclusion()
        self._network.enable_firewall([self.commserv], [int(self.tcinputs["portNumber"])])

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
        self._network.one_way_topology(self.client_group_name, self.clientCSName, topology_name)

        self.client_machine.add_firewall_machine_exclusion()
        self.client_machine.start_firewall()
        self.log.info("step 2: Block the outgoing ports on the client")
        _cmd = BLOCK_OUT_GOING_PORTS_COMMAND.format('BLOCK_PORTS', ','.join([str(i) for i in DEFAULT_OUTGOING_PORTS]))
        _output = self.client_machine.execute_command(_cmd)
        self.log.info(_output.output)

        self.log.info("step 3: Block direct connection from client to CS")
        _cmd = BLOCK_DIRECT_CONNECTION_TO_CS.format('BLOCK_CS',
                                                    str(socket.gethostbyname
                                                        (self.config_json.Install.commserve_client.machine_host)))
        _output = self.client_machine.execute_command(_cmd)
        self.log.info(_output.output)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Inside run function")

            if self.client_machine.check_registry_exists("Session", "nCVDPORT"):
                self.client_helper.uninstall_client(delete_client=True)

            self.get_service_pack_to_install()
            self.set_firewall_prerequisites()

            self.log.info(f"Service Pack to be Installed on the client: {self.commcell.commserv_version}")
            self.log.info(f"Installing fresh windows client on {self.machine_name} with Firewall configuration"
                          f"client can open communication to CS ")

            self.log.info("Step 5: Perform silent install")

            self.client_helper.silent_install(client_name=self.dummy_client_name,
                                              tcinputs=self.tcinputs,
                                              feature_release=self.service_pack)

            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.dummy_client_name):
                self.client_obj = self.commcell.clients.get(self.dummy_client_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(
                    f"Client: {self.machine_name} failed registering to the CS, Please check client logs")

            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.client_machine)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if not self.commcell.is_linux_commserv:
            self.cs_machine.stop_firewall()
            self.cs_machine.remove_firewall_allow_port_rule(int(self.port_number))
            self.cs_machine.remove_firewall_machine_exclusion()
        self.client_machine.remove_firewall_machine_exclusion()
        self.client_machine.remove_firewall_rules(['BLOCK_PORTS', 'BLOCK_CS'])
        self.client_machine.stop_firewall()
        if self.status == "FAILED":
            installer_utils.collect_logs_after_install(self, self.client_machine)
        if self.client_machine.check_registry_exists("Session", "nCVDPORT"):
            self.client_helper.uninstall_client(delete_client=True)
        if self.commcell.clients.has_client(self.machine_name):
            self.commcell.clients.delete(self.machine_name)
