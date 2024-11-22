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

    This testcase supports adminconsole network page testing in multi locale

    SourceClient : A client computer

    InfrastructureClient :  An infrastructure client computer

    GatewayClient : A Proxy client computer

    languages : List of comma separated languages in which the testcase needs to be run
"""
import time

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
    """Command Center - [Network & Firewall] : Create/Update/Delete Network Topology (with all options) in a
    non-English locale """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Create/Update/Delete Network Topology (with all options) in a non-English " \
                    "locale "
        self.browser = None
        self.topology_name = "CG_62847_CC_CS"
        self.admin_console = None
        self.navigator = None
        self._client_group_name1 = "CG_62847_Client"
        self._client_group_name2 = "CG_62847_Infrastructure"
        self._client_group_name3 = 'CG_62847_Proxy'
        self.tcinputs = {
            "SourceClient": ""
        }
        self.smart_groups = ["My CommServe Computer", "My CommServe Computer and MediaAgents", "My MediaAgents"]
        self.client_name = None
        self.client_keep_alive = None
        self.client_group_obj1 = None
        self._network = None
        self.client_group_obj2 = None
        self.client_groups = None
        self.commserve = None
        self.server_keep_alive = None
        self.client_obj = None
        self.summary = None
        self.server_object = None
        self.client_summary = None
        self.server_summary = None
        self.option = None
        self.networkpage = None
        self.infrastructure_name = None
        self.infrastructureobj = None
        self.gatewayobj = None
        self.gatewayclient = None
        self.client_obj_list = None
        self.client_group_obj3 = None
        self.tunnel_port_list = []

    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.commserve = self.commcell.commserv_name
            self._network = NetworkHelper(self)
            self.option = OptionsSelector(self.commcell)
            # Create two client groups for client and commserve
            self.client_groups = self._network.entities.create_client_groups([self._client_group_name1,
                                                                              self._client_group_name2,
                                                                              self._client_group_name3])
            self.client_group_obj1 = self.client_groups[self._client_group_name1]['object']
            self.client_group_obj1.add_clients([self.tcinputs["SourceClient"]])
            self.client_group_obj2 = self.client_groups[self._client_group_name2]['object']
            self.client_group_obj2.add_clients([self.tcinputs["InfrastructureClient"]])
            self.client_group_obj3 = self.client_groups[self._client_group_name3]['object']
            self.client_group_obj3.add_clients([self.tcinputs['GatewayClient']])
            self.client_name = self.tcinputs["SourceClient"]
            self.client_obj = self.commcell.clients.get(self.tcinputs['SourceClient'])
            self.infrastructure_name = self.tcinputs["InfrastructureClient"]
            self.infrastructureobj = self.commcell.clients.get(self.tcinputs.get("InfrastructureClient"))
            self.gatewayclient = self.tcinputs.get("GatewayClient")
            self.gatewayobj = self.commcell.clients.get(self.gatewayclient)
            self.client_obj_list = [self.client_obj, self.infrastructureobj, self.gatewayobj]
            self.tunnel_port_list.extend([self.client_obj.network.tunnel_connection_port,
                                          self.infrastructureobj.network.tunnel_connection_port,
                                          self.gatewayobj.network.tunnel_connection_port])
            self.client_list = [self.client_name, self.infrastructure_name, self.gatewayclient]

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

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
            # Click tile topologies in adminpage
            self.networkpage = NetworkPage(self.admin_console)
            self.networkpage.click_topologies()

        except Exception as exception:
            raise CVTestStepFailure(exception)

    def validate_oneway(self, summary, source_client, destination_client, route_type, protocol, streams,
                        keep_alive, tunnel_port, client_group):
        """Validates the network summary of a client """
        self.log.info(summary)
        check_keep_alive = False
        check_tunnel_port = False
        check_persistent = False
        check_passive = False
        self.summary = summary.split("\n")
        col1, res = self.option.exec_commserv_query("""SELECT clientId FROM App_FirewallOptions WHERE clientId != 0
                                                            UNION ALL
                                                            SELECT clientId FROM APP_ClientGroupAssoc WHERE clientGroupId in 
                                                            (SELECT clientGroupId FROM App_FirewallOptions)""")
        firewall_option_count = 0
        if source_client != self.commserve:
            clientId = self.client_obj.client_id
        else:
            clientId = self.server_object.client_id
        for row in res:
            if row[0] == clientId:
                firewall_option_count += 1

        if firewall_option_count > 1 or client_group in self.smart_groups:
            check_keep_alive = True
            check_tunnel_port = True
        for i in self.summary:
            # Validation of Keep alive interval
            if "keepalive_interval" in i and not check_keep_alive:
                if "keepalive_interval=" + keep_alive in i:
                    check_keep_alive = True
                    self.log.info(f"Validated the keep alive configured in the topology for {client_group}")
                else:
                    raise CVTestStepFailure(
                        'Validation of Keep alive interval failed of {}. Keep alive found : {} vs {}'.
                            format(client_group, i.split("=")[-1], keep_alive))

            # Validation of Tunnel port
            if "tunnel_ports" in i and not check_tunnel_port:
                if str(tunnel_port) in i:
                    check_tunnel_port = True
                    self.log.info("Validated the tunnel port of {}".format(client_group))
                else:
                    raise CVTestStepFailure(' Validation of tunnel port failed for {}. Found {} vs {}'.format(
                        client_group, i.split("=")[-1], tunnel_port))

            # Validation of Outgoing network route
            if source_client + " " + destination_client in i:
                # Validate passive route
                if route_type == "passive":
                    check_passive = True
                    self.log.info("Validated the passive route : {}".format(i))
                else:
                    if int(streams) > 1:
                        if ("type=" + route_type in i and "proto=" + protocol + " " in i) and "streams=" + streams in i:
                            check_persistent = True
                            self.log.info(f"Validated {route_type} network route for {client_group}")
                        else:
                            raise CVTestStepFailure(f' Validation of {route_type} network route failed for'
                                                    f' {client_group}')
                    else:
                        if "type=" + route_type in i and "proto=" + protocol + " " in i:
                            check_persistent = True
                            self.log.info(f"Validated {route_type} network route for {client_group}")
                        else:
                            raise CVTestStepFailure(f' Validation of {route_type} network route failed for'
                                                    f' {client_group}')
        if check_tunnel_port and check_keep_alive:
            return True
        else:
            self.log.info(summary)
            self.log.info(f"Keep alive : {check_keep_alive} Tunnel port : {check_tunnel_port}")
            self.log.info(f"Inputs {keep_alive} {tunnel_port}")
            raise CVTestStepFailure("Validation of network summary failed")

    def validate_proxy(self, summary, source, destination, group_type, streams,
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

                        type : oneway if topology type is one way
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

        if check_tunnel_port and check_keep_alive:
            return True
        else:
            self.log.info(summary)
            raise CVTestStepFailure("Validation of network summary failed")

    def get_summaries(self):
        """Get the network summaries of the clients"""
        time.sleep(10)
        self.summary_list = [self.client_obj_list[0].get_network_summary(),
                             self.client_obj_list[1].get_network_summary(),
                             self.client_obj_list[2].get_network_summary()]

    @test_step
    def step1(self, language):
        """Create one way topology between 62849_SERVERS and 62847_NETWORK_GATEWAYS"""
        self.networkpage.locale = self.admin_console.change_language(language, self.networkpage)
        self.networkpage = NetworkPage(self.admin_console)
        client_group_list = [self._client_group_name1, self._client_group_name2]
        self.networkpage.add_topology(self.topology_name, "One-way", client_group_list, "servertype")
        self.get_summaries()
        self.validate_oneway(self.summary_list[0], self.client_name, self.infrastructure_name, "persistent", "httpsa", 1
                             , '180', self.tunnel_port_list[0], self._client_group_name1)
        self.validate_oneway(self.summary_list[1], self.infrastructure_name, self.client_name, "passive", "httpsa", 1,
                             "180", self.tunnel_port_list[1], self._client_group_name2)
        cg1 = {
            "group_type": "1",
            "group_name": self._client_group_name1,
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        cg2 = {
            "group_type": "2",
            "group_name": self._client_group_name2,
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        if self._client_group_name1 in self.smart_groups:
            cg1["is_mnemonic"] = True
        if self._client_group_name2 in self.smart_groups:
            cg2["is_mnemonic"] = True

        # Edit the topology by changing tunnel port and keep alive
        self.networkpage.edit_topology(self.topology_name, [cg1, cg2])
        self.option.sleep_time(10)
        self.get_summaries()
        self.validate_oneway(self.summary_list[0], self.client_name, self.infrastructure_name, "persistent", "httpsa", 1
                             , '170', '2500', self._client_group_name1)
        self.validate_oneway(self.summary_list[1], self.infrastructure_name, self.client_name, "passive", "httpsa", 1,
                             "170", '2500', self._client_group_name2)
        # self.networkpage.delete_topology(self.topology_name)

    @test_step
    def step2(self):
        """Modify topology from one-way to Network-Gateway and edit the tunnel ports,keep-alive"""
        cg3 = {
            "group_type": "3",
            "group_name": self._client_group_name3,
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        cg1 = {
            "group_type": "1",
            "group_name": self._client_group_name1,
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        cg2 = {
            "group_type": "2",
            "group_name": self._client_group_name2,
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        self.networkpage.edit_topology(self.topology_name, [cg1, cg2, cg3], ModifyTopologyType="Network gateway",
                                       ModifyTopologyName="CG_62847_NW_GATEWAY", Streams='4', CgChanges=True)
        self.get_summaries()
        self.validate_proxy(self.summary_list[0], self.client_list[0], self.client_list[1],
                            1, '4', '170', '2500', self._client_group_name1,
                            Proxy=self.client_list[2], Protocol='httpsa')

        # Validate the network summary of Infrastructure client
        self.validate_proxy(self.summary_list[1], self.client_list[1], self.client_list[0], 2,
                            '4', '170', '2500', self._client_group_name2,
                            Proxy=self.client_list[2], Protocol='httpsa')

        self.validate_proxy(self.summary_list[2], self.client_list[1], self.client_list[0], 3,
                            '4', '170', '2500', self._client_group_name3,
                            Proxy=self.client_list[2], Protocol='httpsa')
        self.topology_name = "CG_62847_NW_GATEWAY"

    @test_step
    def step3(self):
        """Encrypt the network traffic on the topologies"""
        self.networkpage.edit_topology(self.topology_name, None, EncryptTraffic=True)
        self.get_summaries()
        self.validate_proxy(self.summary_list[0], self.client_list[0], self.client_list[1],
                            1, '1', '170', '2500', self._client_group_name1,
                            Proxy=self.client_list[2], Protocol='https')

        # Validate the network summary of Infrastructure client
        self.validate_proxy(self.summary_list[1], self.client_list[1], self.client_list[0], 2,
                            '1', '170', '2500', self._client_group_name2,
                            Proxy=self.client_list[2], Protocol='https')

        self.validate_proxy(self.summary_list[2], self.client_list[1], self.client_list[0], 3,
                            '1', '170', '2500', self._client_group_name3,
                            Proxy=self.client_list[2], Protocol='https')
        # Download the network summary of the clients and verify
        self.networkpage.download_network_summary(self.client_name)

    @test_step
    def step4(self):
        """Unselect the encrypt trafiic toggle and select the tunnel protocol as raw"""
        self.networkpage.edit_topology(self.topology_name, None, TunnelProtocol="Raw")
        self.get_summaries()

        self.networkpage.delete_topology(self.topology_name)

    def run(self):
        """Run function"""
        try:
            self.init_tc()
            self.navigate_to_topologies()
            languages = self.tcinputs.get("languages")
            languages = languages.split(",") if languages else None
            if languages is None:
                languages = ["Japanese", "German"]
            for i in languages:
                self.step1(i)
                self.step2()
                self.step3()
                self.step4()
            self.admin_console.change_language("english", self.networkpage)
        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.log.info("Changing the language back to English after an exception")
            self.admin_console.change_language("english", self.networkpage)
            if self.networkpage:
                self.networkpage.remove_fwconfig_files()
            self.admin_console.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self._network.cleanup_network()
            self._network.entities.cleanup()
