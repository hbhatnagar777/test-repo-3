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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    ServerClient    --  A client computer

    InfrastructureClient : A client computer

    ProxyClient : A client computer


Inputs for smart topology (Optional)

    is_smart : True or False for smart topology

    MediaAgent : A media agent client name other than input clients
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Server.Network.networkhelper import NetworkHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.AdminConsolePages.NetworkPage import NetworkPage
import os


class TestCase(CVTestCase):
    """Command Center- Network topology- Network Gateway(Servers)"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center- Network topology- Network Gateway(Servers)"
        self.browser = None
        self.topology_name = "CG_60338_NETWORK_GATEWAY"
        self.admin_console = None
        self.navigator = None
        self._client_group_name1 = "CG_60338_SERVER"
        self._client_group_name2 = "CG_60338_INFRASTRUCTURE"
        self._client_group_name3 = "CG_PROXY"
        self.tcinputs = {
            "ServerClient": "",
            "InfrastructureClient": "",
            "ProxyClient": ""
        }
        self.smart_groups = ["My CommServe Computer", "My CommServe Computer and MediaAgents", "My MediaAgents"]
        self.server_client = None
        self.Infrastructure = None
        self.proxy = None
        self.client_group_obj1 = None
        self._network = None
        self.client_group_obj2 = None
        self.client_group_obj3 = None
        self.client_groups = None
        self.client_name = None
        self.number_of_streams = None
        self.commserve = None
        self.client_obj = None
        self.option = None
        self.networkpage = None
        self.Server_obj = None
        self.server_summary = None
        self.proxy_summary = None
        self.infrastructure_summary = None
        self.infrastructure_obj = None
        self.Server_obj = None
        self.proxy_obj = None
        self.client_name_list = []
        self.client_group_list = []
        self.client_obj_list = []
        self.tunnel_port_list = []
        self.summary_list = []

    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.commserve = self.commcell.commserv_name
            self._network = NetworkHelper(self)
            self.option = OptionsSelector(self.commcell)
            self.client_groups = self._network.entities.create_client_groups([self._client_group_name1,
                                                                              self._client_group_name2,
                                                                              self._client_group_name3])
            self.client_group_obj1 = self.client_groups[self._client_group_name1]['object']
            self.client_group_obj1.add_clients([self.tcinputs["ServerClient"]])
            self.client_group_obj2 = self.client_groups[self._client_group_name2]['object']
            self.client_group_obj2.add_clients([self.tcinputs["InfrastructureClient"]])
            self.client_group_obj3 = self.client_groups[self._client_group_name3]['object']
            self.client_group_obj3.add_clients([self.tcinputs["ProxyClient"]])
            self.client_group_list.extend([self._client_group_name1,
                                           self._client_group_name2, self._client_group_name3])
            self.server_client = self.tcinputs['ServerClient']
            self.Infrastructure = self.tcinputs["InfrastructureClient"]
            self.proxy = self.tcinputs['ProxyClient']
            self.client_name_list.extend([self.server_client, self.Infrastructure, self.proxy])
            self.Server_obj = self.commcell.clients.get(self.tcinputs['ServerClient'])
            self.infrastructure_obj = self.commcell.clients.get(self.tcinputs['InfrastructureClient'])
            self.proxy_obj = self.commcell.clients.get(self.tcinputs['ProxyClient'])
            self.tunnel_port_list.extend([self.Server_obj.network.tunnel_connection_port,
                                          self.infrastructure_obj.network.tunnel_connection_port,
                                          self.proxy_obj.network.tunnel_connection_port])
            self.client_obj_list.extend([self.Server_obj, self.infrastructure_obj, self.proxy_obj])
            self.summary_list.extend([self.server_summary, self.infrastructure_summary, self.proxy_summary])

            self.pre_check_summary()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def navigate_to_topologies(self):
        """Open browser and navigate to the network page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(os.getcwd())
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_network()
            self.networkpage = NetworkPage(self.admin_console)

            self.networkpage.click_topologies()
            self.pre_check_summary()

        except Exception as exception:
            raise CVTestStepFailure(exception)

    def pre_check_summary(self):
        """Validate if there are no routes present before the topology"""
        # Populate the network summaries
        self.get_summaries()
        if self.validate_no_routes(self.client_name_list, self.summary_list):
            self.log.info("No routes are present before configuring two way topology")
        else:
            raise CVTestStepFailure("Already a route has been configured between the Server client and Infrastructure")

    def validate_no_routes(self, client_list, summary_list):
        """A function to validate that there are no routes between the client and commserve"""
        cl_summary = summary_list[0].split("\n")
        dest_summary = summary_list[1].split("\n")
        proxy_summary = summary_list[2].split("\n")
        server_check = 0
        infrastructure_check = 0
        proxy_check = 0

        for i in cl_summary:
            if client_list[0] + " " + client_list[2] + " " in i and "type=persistent" in i:
                self.log.info(f'Persistent route in {client_list[0]}')
                server_check += 1
            if client_list[0] + " " + client_list[1] + " " in i and "proxy=" + client_list[2] in i:
                self.log.info(f'Proxy route in {client_list[0]} ')
                server_check += 1

        for i in proxy_summary:
            if client_list[2] + " " + client_list[0] + " " in i and "type=passive" in i:
                self.log.info(f'Passive route in {client_list[2]}')
                proxy_check += 1
            if client_list[2] + " " + client_list[1] + " " in i and "type=passive" in i:
                self.log.info(f'Passive route in {client_list[2]}')
                proxy_check += 1

        for i in dest_summary:
            if client_list[1] + " " + client_list[2] + " " in i and "type=persistent" in i:
                self.log.info(f'Persistent route in {client_list[1]}')
                server_check += 1
            if client_list[1] + " " + client_list[0] + " " in i and "proxy=" + client_list[2] in i:
                self.log.info(f'Proxy route in {client_list[1]} ')
                server_check += 1

        # Validate if routes are removed on both the client and Infrastructure client
        if server_check > 0 and infrastructure_check > 0 and proxy_check > 0:
            return False

        return True

    def get_summaries(self):
        self.summary_list[0] = self.client_obj_list[0].get_network_summary()
        self.summary_list[1] = self.client_obj_list[1].get_network_summary()
        self.summary_list[2] = self.client_obj_list[2].get_network_summary()

    def validate_summary(self, summary, source, destination, group_type, streams,
                         keep_alive, tunnel_port, client_group, **kwargs):
        """Validates the network summary of a client

            Args --
                summary : Network summary

                source : client name of servers or infrastructure

                destination : client name of servers or infrastructure

                group_type (int) : Group type in topology 1 for Servers 2 for insfrastructure 3 for proxy

                streams : Number of tunnels

                keep_alive : Keep alive interval of the client group configured

                tunnel port : tunnel port of client group

                client group : Client group name of that client


                **kwargs :
                    Supported key word arguments are
                        Proxy : Proxy Client

                        Protocol : Tunnel Protocol

                        client_id : Client ID
        """
        # Variables to validate the properties of the network summary set
        check_keep_alive = False
        check_tunnel_port = False
        check_server = 0
        check_proxy = 0
        proxy = kwargs.get("Proxy")
        protocol = kwargs.get('Protocol')
        summary_split = summary.split("\n")
        col1, res = self.option.exec_commserv_query("""SELECT clientId FROM App_FirewallOptions WHERE clientId != 0
                                                    UNION ALL
                                                    SELECT clientId FROM APP_ClientGroupAssoc WHERE clientGroupId in 
                                                    (SELECT clientGroupId FROM App_FirewallOptions)""")
        # Variable to check the firewall options set to this client. If there are more than one ignore the keepalive
        # and tunnel port changes at topology level
        firewall_option_count = 0

        for row in res:
            if row[0] == kwargs.get("client_id", self.client_obj_list[group_type - 1].client_id):
                firewall_option_count += 1

        if firewall_option_count > 1 or client_group in self.smart_groups:
            check_keep_alive = True
            check_tunnel_port = True

        for i in summary_split:
            # Validation of Keep alive interval
            if "keepalive_interval" in i:
                if "keepalive_interval=" + keep_alive in i:
                    check_keep_alive = True
                    self.log.info(f"Validated the keep alive configured in the topology for {client_group}")
                elif not check_keep_alive:
                    raise CVTestStepFailure(
                        'Validation of Keep alive interval failed of {}. Keep alive found : {} vs {}'.
                            format(client_group, i.split("=")[-1], keep_alive))

            # Validation of Tunnel port
            if "tunnel_ports" in i:
                if str(tunnel_port) in i:
                    check_tunnel_port = True
                    self.log.info("Validated the tunnel port of {}".format(client_group))
                elif not check_tunnel_port:
                    raise CVTestStepFailure(' Validation of tunnel port failed for {}. Found {} vs {}'.format(
                        client_group, i.split("=")[-1], tunnel_port))

            # Validation of Outgoing network routes for servers and infrastructures
            if group_type <= 2:
                if source + " " + proxy + " " in i and ("type=persistent" in i and " proto=" + protocol + " " in i):
                    if int(streams) > 1 and "streams=" + streams in i:
                        check_server += 1
                    else:
                        check_server += 1
                if source + " " + destination + " " in i and "proxy=" + proxy in i:
                    check_server += 1

            # Validation of Two outgoing passive routes in proxy client
            if group_type == 3:
                if proxy + " " + source + " " in i and "type=passive" in i:
                    check_proxy += 1
                if proxy + " " + destination + " " in i and "type=passive" in i:
                    check_proxy += 1
        self.log.info(summary)
        # if group_type == 3 and not check_proxy == 2:
        #     raise CVTestStepFailure(f"Validation of network summary failed for client {source} in group {client_group}: Proxy route is incorrect")
        # elif group_type <= 2 and not check_server == 2:
        #     raise CVTestStepFailure(f"Validation of network summary failed for client {source} in group {client_group}: Server route is incorrect")
        # elif not check_tunnel_port:
        #     raise CVTestStepFailure(f"Validation of network summary failed for client {source} in group {client_group}: Tunnel port is incorrect")
        # elif not check_keep_alive:
        #     raise CVTestStepFailure(f"Validation of network summary failed for client {source} in group {client_group}: Keep alive is incorrect")
        # else:
        #     return True

    @test_step
    def create_network_gateway(self, client_group_list, client_list):
        """Configure and validate network gateway topology between clients"""
        try:
            # Create a two-way topology from client to Infrastructure client group
            self.networkpage.add_topology(self.topology_name, "Network gateway", client_group_list, "servertype")

            self.get_summaries()

            # Validation of network summary of servers
            self.validate_summary(self.summary_list[0], client_list[0], client_list[1],
                                  1, '1', '180', self.tunnel_port_list[0], client_group_list[0],
                                  Proxy=client_list[2], Protocol='httpsa')

            # Validate the network summary of Infrastructure client
            self.validate_summary(self.summary_list[1], client_list[1], client_list[0], 2,
                                  '1', '180', self.tunnel_port_list[1], client_group_list[1],
                                  Proxy=client_list[2], Protocol='httpsa')

            self.validate_summary(self.summary_list[2], client_list[1], client_list[0], 3,
                                  '1', '180', self.tunnel_port_list[2], client_group_list[2],
                                  Proxy=client_list[2], Protocol='httpsa')

        except Exception as exception:
            raise CVTestStepFailure(exception)

    @test_step
    def validate_additional_settings(self, client_group_list: list, client_list: list):
        """Additional settings keep alive interval and tunnel port for client groups"""
        cg1 = {
            "group_type": "1",
            "group_name": client_group_list[0],
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        cg2 = {
            "group_type": "2",
            "group_name": client_group_list[1],
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        cg3 = {
            "group_type": "3",
            "group_name": client_group_list[2],
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        if client_list[0] in self.smart_groups:
            cg1["is_mnemonic"] = True
        if client_list[1] in self.smart_groups:
            cg2["is_mnemonic"] = True
        if client_list[2] in self.smart_groups:
            cg2["is_mnemonic"] = True

        try:

            # Edit the topology by changing tunnel port and keep alive
            self.networkpage.edit_topology(self.topology_name, [cg1, cg2, cg3])

            self.option.sleep_time(10)

            self.get_summaries()

            # Validation of network summary of servers
            self.validate_summary(self.summary_list[0], client_list[0], client_list[1],
                                  1, '1', '170', "2500", client_group_list[0],
                                  Proxy=client_list[2], Protocol='httpsa')

            # Validate the network summary of Infrastructure client
            self.validate_summary(self.summary_list[1], client_list[1], client_list[0], 2,
                                  '1', '170', "2500", client_group_list[1],
                                  Proxy=client_list[2], Protocol='httpsa')

            self.validate_summary(self.summary_list[2], client_list[1], client_list[0], 3,
                                  '1', '170', "2500", client_group_list[2],
                                  Proxy=client_list[2], Protocol='httpsa')

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def configure_multi_streams(self, client_group_list, client_list):
        """Configure multi-streams to 4 on topology client group"""
        try:
            self.networkpage.edit_topology(self.topology_name, None, Streams='4')

            self.get_summaries()

            # Validation of network summary of servers
            self.validate_summary(self.summary_list[0], client_list[0], client_list[1],
                                  1, '4', '170', "2500", client_group_list[0],
                                  Proxy=client_list[2], Protocol='httpsa')

            # Validate the network summary of Infrastructure client
            self.validate_summary(self.summary_list[1], client_list[1], client_list[0], 2,
                                  '4', '170', "2500", client_group_list[1],
                                  Proxy=client_list[2], Protocol='httpsa')

            self.validate_summary(self.summary_list[2], client_list[1], client_list[0], 3,
                                  '4', '170', "2500", client_group_list[2],
                                  Proxy=client_list[2], Protocol='httpsa')
        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def validate_encrypt_network(self, client_group_list, client_list):
        """Enable the encrypt network traffic toggle, validate and other way around"""
        try:
            self.networkpage.edit_topology(self.topology_name, None, EncryptTraffic=True)

            self.get_summaries()

            # Validation of network summary of servers
            self.validate_summary(self.summary_list[0], client_list[0], client_list[1],
                                  1, '4', '170', "2500", client_group_list[0],
                                  Proxy=client_list[2], Protocol='https')

            # Validate the network summary of Infrastructure client
            self.validate_summary(self.summary_list[1], client_list[1], client_list[0], 2,
                                  '4', '170', "2500", client_group_list[1],
                                  Proxy=client_list[2], Protocol='https')

            self.networkpage.edit_topology(self.topology_name, None, EncryptTraffic=False,
                                           TunnelProtocol="Authenticated")

            self.get_summaries()
            self.validate_summary(self.summary_list[0], client_list[0], client_list[1],
                                  1, '4', '170', "2500", client_group_list[0],
                                  Proxy=client_list[2], Protocol='httpsa')

            # Validate the network summary of Infrastructure client
            self.validate_summary(self.summary_list[1], client_list[1], client_list[0], 2,
                                  '4', '170', "2500", client_group_list[1],
                                  Proxy=client_list[2], Protocol='httpsa')

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def download_network_summary(self, client_group_list, client_obj_list, client_list):
        """Validate the download network summary"""
        try:
            if client_group_list[0] in self.smart_groups or client_group_list[1] in self.smart_groups \
                    or client_group_list[2] in self.smart_groups:
                self.log.info("Download network summary is enabled only for regular topology")

            else:
                self.networkpage.download_network_summary(client_obj_list[0].display_name)
                self.option.sleep_time(5)
                fd = open(os.path.join(os.getcwd(), f'FwConfig_{client_obj_list[0].display_name}.txt'))
                self.summary_list[0] = fd.read()

                self.networkpage.download_network_summary(client_obj_list[1].display_name)
                self.option.sleep_time(5)
                fd = open(os.path.join(os.getcwd(), f'FwConfig_{client_obj_list[1].display_name}.txt'))
                self.summary_list[1] = fd.read()
                fd.close()

                self.networkpage.download_network_summary(client_obj_list[2].display_name)
                self.option.sleep_time(5)
                fd = open(os.path.join(os.getcwd(), f'FwConfig_{client_obj_list[2].display_name}.txt'))
                self.summary_list[2] = fd.read()
                fd.close()

                # Validation of network summary of servers
                self.validate_summary(self.summary_list[0], client_list[0], client_list[1],
                                      1, '4', '170', "2500", client_group_list[0],
                                      Proxy=client_list[2], Protocol='httpsa')

                # Validate the network summary of Infrastructure client
                self.validate_summary(self.summary_list[1], client_list[1], client_list[0], 2,
                                      '4', '170', "2500", client_group_list[1],
                                      Proxy=client_list[2], Protocol='httpsa')

                # Validate the network summary of the Proxy client group
                self.validate_summary(self.summary_list[2], client_list[1], client_list[0], 3,
                                      '1', '170', "2500", client_group_list[2],
                                      Proxy=client_list[2])

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def delete_topology_validate(self):
        """Delete topology and validate the routes are removed"""
        self.networkpage.delete_topology(self.topology_name)

        self.option.sleep_time(10)

        self.get_summaries()

        # Validate if the routes are deleted
        if not self.validate_no_routes(self.client_name_list, self.summary_list):
            raise CVTestStepFailure("Deletion of network route failed")

    @test_step
    def validate_smart_topology(self):
        """Validate the topology with smart client group"""
        # create a subclient and storage policy to validate the routes with the smart client group
        media_agent = self.tcinputs.get('MediaAgent')
        disklibrary_inputs = {
            'disklibrary': {
                'name': "disklibrary_" + media_agent,
                'mediaagent': media_agent,
                'mount_path': self._network.entities.get_mount_path(media_agent),
                'username': '',
                'password': '',
                'cleanup_mount_path': True,
                'force': False,
            }
        }
        self.log.info("Creating disk library using media agent {0}".format(media_agent))
        self._network.entities.create(disklibrary_inputs)
        # create storage policy
        storagepolicy_inputs = {
            'target':
                {
                    'library': "disklibrary_" + media_agent,
                    'mediaagent': media_agent,
                    'force': False
                },
            'storagepolicy':
                {
                    'name': "storagepolicy_" + media_agent,
                    'dedup_path': None,
                    'incremental_sp': None,
                    'retention_period': 3,
                },
        }
        self.log.info("Creating storage policy using library {0}".
                      format("disklibrary_" + media_agent))
        self._network.entities.create(storagepolicy_inputs)

        cg_type = self.tcinputs.get("SmartGroupType", 1)  # Either servers or infrastructure

        client_type = 0 if cg_type == 2 else 1

        self.log.info("Creating subclient for client {0}".format(self.client_name_list[client_type]))

        subclient_name = "subclient_" + self.client_name_list[client_type] + self._network.options.get_custom_str()
        backupset_name = "defaultBackupSet"
        # create subclient
        subclient_inputs = {
            'target':
                {
                    'client': self.client_name_list[client_type],
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'storagepolicy': "storagepolicy_" + media_agent,
                    'force': True
                },

            'subclient':
                {
                    'name': subclient_name,
                    'client_name': self.client_name_list[client_type],
                    'backupset': backupset_name,
                    'data_path': "C:\\Testdata",
                    'level': 1,
                    'size': 5,
                    'description': "Automation - Target properties",
                    'subclient_type': None,
                }
        }
        self._network.entities.create(subclient_inputs)

        self.client_group_list[cg_type - 1] = self.smart_groups[0]
        self.client_name_list[cg_type - 1] = self.commserve
        self.client_obj_list[cg_type - 1] = self.commcell.clients.get(self.commserve)
        self.tunnel_port_list[cg_type - 1] = self.client_obj_list[cg_type - 1].network.tunnel_connection_port

        def validate_summaries():
            self.get_summaries()
            self.log.info(self.summary_list[0])
            self.log.info(self.summary_list[1])
            self.validate_summary(self.summary_list[0], self.client_name_list[0], self.client_name_list[1],
                                  1, '1', '180', self.tunnel_port_list[0], self.client_group_list[0],
                                  Proxy=self.client_name_list[2], Protocol='httpsa')

            # Validate the network summary of Infrastructure client
            self.validate_summary(self.summary_list[1], self.client_name_list[1], self.client_name_list[0], 2,
                                  '1', '180', self.tunnel_port_list[1], self.client_group_list[1],
                                  Proxy=self.client_name_list[2], Protocol='httpsa')

            self.validate_summary(self.summary_list[2], self.client_name_list[1], self.client_name_list[0], 3,
                                  '1', '180', self.tunnel_port_list[2], self.client_group_list[2],
                                  Proxy=self.client_name_list[2], Protocol='httpsa')

        try:
            # Create a topology from client to Infrastructure client group
            self.networkpage.add_topology(self.topology_name, "Network gateway", self.client_group_list, "servertype")

            validate_summaries()

            cg1 = {
                "group_type": str(cg_type),
                "group_name": self.smart_groups[1],
                "is_mnemonic": False
            }

            # Now change the smart topology to the My CommServe and Media agents
            self.networkpage.edit_topology(self.topology_name, [cg1], CgChanges=True)

            self.client_group_list[cg_type - 1] = self.smart_groups[1]
            self.client_name_list[cg_type - 1] = self.commserve
            self.client_obj_list[cg_type - 1] = self.commcell.clients.get(self.commserve)
            self.tunnel_port_list[cg_type - 1] = self.client_obj_list[cg_type - 1].network.tunnel_connection_port
            validate_summaries()

            # Verify the summary for the media agent for this topology
            self.client_name_list[cg_type - 1] = self.tcinputs["MediaAgent"]
            self.client_obj_list[cg_type - 1] = self.commcell.clients.get(self.tcinputs["MediaAgent"])
            self.tunnel_port_list[cg_type - 1] = self.client_obj_list[cg_type - 1].network.tunnel_connection_port
            validate_summaries()

            # Change the topology to My MediaAgents
            cg1 = {
                "group_type": str(cg_type),
                "group_name": self.smart_groups[2],
                "is_mnemonic": False
            }
            self.client_group_list[cg_type - 1] = self.smart_groups[2]
            self.networkpage.edit_topology(self.topology_name, [cg1], CgChanges=True)
            validate_summaries()

            cg_list = [self._client_group_name1, self._client_group_name2, self._client_group_name3]
            cl_list = [self.server_client, self.Infrastructure, self.proxy]
            # Inputs to change topology from smart to regular
            cg1 = {
                "group_type": str(cg_type),
                "group_name": cg_list[cg_type - 1],
                "is_mnemonic": False
            }
            self.client_name_list[cg_type - 1] = cl_list[cg_type - 1]
            self.client_obj_list[cg_type - 1] = self.commcell.clients.get(cl_list[cg_type - 1])
            self.tunnel_port_list[cg_type - 1] = self.client_obj_list[cg_type - 1].network.tunnel_connection_port
            self.networkpage.edit_topology(self.topology_name, [cg1], CgChanges=True)
            validate_summaries()
        except Exception as exception:
            raise CVTestStepFailure(exception)

    def run(self):
        try:
            self.init_tc()
            self.navigate_to_topologies()
            self.create_network_gateway(self.client_group_list, self.client_name_list)
            self.validate_additional_settings(self.client_group_list, self.client_name_list)
            self.configure_multi_streams(self.client_group_list, self.client_name_list)
            self.validate_encrypt_network(self.client_group_list, self.client_name_list)
            self.download_network_summary(self.client_group_list, self.client_obj_list, self.client_name_list)
            self.delete_topology_validate()
            if self.tcinputs.get('is_smart'):
                self.validate_smart_topology()
                self.delete_topology_validate()

        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.networkpage.remove_fwconfig_files()
            self.admin_console.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self._network.cleanup_network()
            self._network.entities.cleanup()