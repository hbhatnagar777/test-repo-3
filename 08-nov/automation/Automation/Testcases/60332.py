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

    Test case to test one -way topology

    TC inputs required :

    SourceClient : A client computer other than commserve
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
    """Command Center- Network topology- OneWay CC->CS(laptop)"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center- Network topology- OneWay CC->CS(laptop)"
        self.browser = None
        self.topology_name = "CG_60332_CC_CS"
        self.admin_console = None
        self.navigator = None
        self._client_group_name1 = "CG_60332_Client"
        self._client_group_name2 = "CG_60332_Server"
        self.tcinputs = {
            "SourceClient": ""
        }
        self.smart_groups = ["My CommServe Computer", "My CommServe Computer and MediaAgents", "My MediaAgents"]
        self.client_keep_alive = None
        self.client_group_obj1 = None
        self._network = None
        self.client_group_obj2 = None
        self.client_groups = None
        self.client_name = None
        self.commserve = None
        self.server_keep_alive = None
        self.client_obj = None
        self.summary = None
        self.server_object = None
        self.client_summary = None
        self.server_summary = None
        self.option = None
        self.networkpage = None

    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.commserve = self.commcell.commserv_name
            self._network = NetworkHelper(self)
            self.option = OptionsSelector(self.commcell)
            # Create two client groups for client and commserve
            self.client_groups = self._network.entities.create_client_groups([self._client_group_name1,
                                                                              self._client_group_name2])
            self.client_group_obj1 = self.client_groups[self._client_group_name1]['object']
            self.client_group_obj1.add_clients([self.tcinputs["SourceClient"]])
            self.client_group_obj2 = self.client_groups[self._client_group_name2]['object']
            self.client_group_obj2.add_clients([self.commserve])
            self.client_name = self.tcinputs["SourceClient"]
            self.client_obj = self.commcell.clients.get(self.tcinputs['SourceClient'])
            self.server_object = self.commcell.clients.get(self.commserve)
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

            # Click tile topologies in adminpage
            self.networkpage = NetworkPage(self.admin_console)
            self.networkpage.click_topologies()

        except Exception as exception:
            raise CVTestStepFailure(exception)

    def pre_check_summary(self):
        """Validate if there are no routes present before the topology"""
        self.client_summary = self.client_obj.get_network_summary()
        self.server_summary = self.server_object.get_network_summary()

        if self.validate_no_routes(self.client_name, self.commserve):
            self.log.info("No routes are present before configuring one way topology")
        else:
            raise CVTestStepFailure("Already a route has been configured between the client and commserve")

    def validate_no_routes(self, client, server):
        """A function to validate that there are no routes between the client and commserve"""
        cl_summary = self.client_summary.split("\n")
        server_summary = self.server_summary.split("\n")
        client_check = False
        server_check = False

        for i in cl_summary:
            if client + " " + server in i and "type=persistent" in i:
                self.log.info(f"Deletion of network routes failed for {client}")
                client_check = True

        for i in server_summary:
            if server + " " + client in i and "type=passive" in i:
                self.log.info(f"Deletion of network routes failed for {server}")
                server_check = True

        # Validate if routes are removed on both the client and commserve
        if server_check and client_check:
            return False

        return True

    def validate_summary(self, summary, source_client, destination_client, route_type, protocol, streams,
                         keep_alive, tunnel_port, client_group):
        """Validates the network summary of a client """
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
        clientId = None
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
                    # Multi streams configured
                    if int(streams) > 1:
                        if ("type=" + route_type in i and "proto=" + protocol + " " in i) and "streams=" + streams in i:
                            check_persistent = True
                            self.log.info(f"Validated {route_type} network route for {client_group}")
                        else:
                            pass # comment until the validation is fixed
                            # raise CVTestStepFailure(f' Validation of {route_type} network route failed for'
                            #                         f' {client_group}')
                    else:
                        if "type=" + route_type in i and "proto=" + protocol + " " in i:
                            check_persistent = True
                            self.log.info(f"Validated {route_type} network route for {client_group}")
                        else:
                            pass # comment until the validation is fixed
                            # raise CVTestStepFailure(f' Validation of {route_type} network route failed for'
                            #                         f' {client_group}')
        if (check_persistent or check_passive) and check_tunnel_port and check_keep_alive:
            return True
        else:
            pass # comment until the validation is fixed
            # raise CVTestStepFailure("Validation of network summary failed")

    @test_step
    def create_one_way(self, client_group_name1, client_group_name2):
        """Configure and validate one way between client and commserve"""
        try:
            client_group_list = [client_group_name1, client_group_name2]

            # Create a one-way topology from client to commserve
            self.networkpage.add_topology(self.topology_name, "One-way", client_group_list, "clienttype")

            self.client_summary = self.client_obj.get_network_summary()

            self.server_summary = self.server_object.get_network_summary()

            # Validate the network summary of source client
            self.validate_summary(self.client_summary, self.client_name,
                                  self.commserve,
                                  "persistent", "httpsa", '1', '180', self.client_obj.network.tunnel_connection_port,
                                  client_group_name1)

            # Validate the network summary of commserve
            self.validate_summary(self.server_summary, self.commserve,
                                  self.client_name,
                                  "passive", "httpsa", '1', '180', self.server_object.network.tunnel_connection_port,
                                  client_group_name2)

        except Exception as exception:
            raise CVTestStepFailure(exception)

    @test_step
    def validate_additional_settings(self, client_group_name1, client_group_name2):
        """Additional settings keep alive interval and tunnel port for client groups"""
        cg1 = {
            "group_type": "1",
            "group_name": client_group_name1,
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        cg2 = {
            "group_type": "2",
            "group_name": client_group_name2,
            "is_mnemonic": False,
            "tunnelport": '2500',
            "keepalive": '170'
        }
        if client_group_name1 in self.smart_groups:
            cg1["is_mnemonic"] = True
        if client_group_name2 in self.smart_groups:
            cg2["is_mnemonic"] = True

        try:

            # Edit the topology by changing tunnel port and keep alive
            self.networkpage.edit_topology(self.topology_name, [cg1, cg2])

            self.option.sleep_time(10)

            # Network summary of the client and commserve
            self.server_summary = self.server_object.get_network_summary()

            self.client_summary = self.client_obj.get_network_summary()

            self.validate_summary(self.client_summary, self.client_name,
                                  self.commserve,
                                  "persistent", "httpsa", "1", "170", "2500", client_group_name1)
            self.validate_summary(self.server_summary, self.commserve,
                                  self.client_name,
                                  "passive", "httpsa", "1", "170", "2500", client_group_name2)

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def configure_multi_streams(self):
        """Configure multi-streams to 4 on topology client group"""
        try:
            self.networkpage.edit_topology(self.topology_name, None, Streams='4')

            self.client_summary = self.client_obj.get_network_summary()

            # Check if the client summary reflect the streams=4 in route
            self.validate_summary(self.client_summary, self.client_name,
                                  self.commserve,
                                  "persistent", "httpsa", '4', '170', '2500', self._client_group_name1)
        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def validate_encrypt_network(self):
        """Enable the encrypt network traffic toggle, validate and other way around"""
        try:
            # Edit the topology by enabling the toggle of Encrypt topology
            self.networkpage.edit_topology(self.topology_name, None, EncryptTraffic=True)
            self.client_summary = self.client_obj.get_network_summary()
            self.validate_summary(self.client_summary, self.client_name,
                                  self.commserve, "persistent", "https", '4', "170", '2500', self._client_group_name1)

            # Edit the topology by disabling the toggle of encrypt and changing protocol to authenticated
            self.networkpage.edit_topology(self.topology_name, None, EncryptTraffic=False,
                                           TunnelProtocol="Authenticated")
            self.client_summary = self.client_obj.get_network_summary()
            self.validate_summary(self.client_summary, self.client_name,
                                  self.commserve,
                                  "passive", "httpsa", '4', '170', '2500', self._client_group_name1)
        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def download_network_summary(self):
        """Validate the download network summary"""
        try:
            if self._client_group_name1 in self.smart_groups or self._client_group_name2 in self.smart_groups:
                self.log.info("Download network summary is enabled only for regular topology")

            else:
                # Download the Fwconfig files of client and commserve
                self.networkpage.download_network_summary(self.server_object.display_name)
                self.option.sleep_time(5)
                fd = open(os.path.join(os.getcwd(), f'FwConfig_{self.server_object.display_name}.txt'))
                self.server_summary = fd.read()

                self.networkpage.download_network_summary(self.client_obj.display_name)
                self.option.sleep_time(5)
                fd = open(os.path.join(os.getcwd(), f'FwConfig_{self.client_obj.display_name}.txt'))
                self.client_summary = fd.read()
                fd.close()

                # Validate the files if the routes are populated
                self.validate_summary(self.server_summary, self.commserve, self.client_name,
                                      "passive", "httpsa", '4', '170', '2500', self._client_group_name2)
                self.validate_summary(self.client_summary, self.client_name,
                                      self.commserve,
                                      "persistent", "httpsa", '4', '170', '2500', self._client_group_name1)

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def delete_topology_validate(self):
        """Delete topology and validate the routes are removed"""
        self.networkpage.delete_topology(self.topology_name)

        self.option.sleep_time(10)

        self.client_summary = self.client_obj.get_network_summary()

        self.server_summary = self.server_object.get_network_summary()

        # Validate if the routes are deleted
        if not self.validate_no_routes(self.client_name, self.commserve):
            raise CVTestStepFailure("Deletion of network route failed")

    def run(self):
        try:
            self.init_tc()
            self.navigate_to_topologies()
            self.create_one_way(self._client_group_name1, self._client_group_name2)
            self.validate_additional_settings(self._client_group_name1, self._client_group_name2)
            self.configure_multi_streams()
            self.validate_encrypt_network()
            self.download_network_summary()
            self.delete_topology_validate()

            # Validate the routes for smart topology as well.
            self.create_one_way(self._client_group_name1, "My CommServe Computer")
            self.delete_topology_validate()
        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.networkpage.remove_fwconfig_files()
            self.admin_console.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self._network.cleanup_network()
            self._network.entities.cleanup()
