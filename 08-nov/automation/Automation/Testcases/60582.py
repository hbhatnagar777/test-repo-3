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
    __init__()                                   -- Initializes TestCase class

    setup()                                      -- setup function of this test case

    run()           --  run function of this test case

    create_clients_groups_and_topologies()     -- creates the client groups and topology required for the test case

    install_real_client()    -- Function to install a real client on the specified machine via proxy

    check_new_client() -- Ensures new client is installed successfully and is change is pushed to network summaries

    check_topology_change_effects()      -- Changes topology to and from smart topology, then deletes topology

    check_routes_are_clear() -- Ensures routes are cleared after topology is deleted

    cleanup()  -- cleans up test case entities

"""

# Shubhankar
# 20 July 2021

from AutomationUtils.cvtestcase import CVTestCase
from Install.install_helper import InstallHelper
from Server.Network import networkhelper
from AutomationUtils import constants, idautils
import traceback
from AutomationUtils.machine import Machine
import os
from datetime import datetime


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.client_group_names = None
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.name = "[Network & Firewall] : Client Install via cascading gateways topology"
        self.tcinputs = {
            "Network_Proxy1": "string",
            "Network_Proxy2": "string",
            "Network_Proxy3": "string",
            "Network_Proxy4": "string",
            "Install_Proxy": "string",  # needs to be a media agent
            "Network_Proxy5": "string",

            "Install_Proxy_TunnelPort": "string",

            # "csClientName": "string",
            # "csHostname": "string",
            # "commservePassword": "string",

            "install_machine_name": "string",
            # The machine must be part of automation.commvault.com domain for correct permissions.
            # Otherwise "Exception: Authentication Failed. Invalid credentials provided." error may be encountered.

            "install_machine_username": "string",
            "install_machine_password": "string"

        }

        self.storage_policy_name = None
        self._network = None
        self.new_client_name = None
        self.topology_name = None
        self.cont = True
        self.proxy_name = None
        self.proxy_port = None
        self.proxy_hostname = None
        self.client_install_machine = None
        self.install_inputs = None
        self._idautil = None
        self.C1 = None
        self.C2 = None
        self.C3 = None
        self.C4 = None
        self.C5 = None
        self.C6 = None
        self.all_C_clients = None
        self.client_install_machine_name = None
        self._install_helper1 = None

    def setup(self):
        try:
            self.log.info("Beginning setup")
            self.tcinputs["csClientName"] = self.commcell.commserv_name
            self.tcinputs["csHostname"] = self.commcell.commserv_hostname
            self.log.info(f"csClientName = {self.tcinputs['csClientName']}, and csHostname = "
                          f"{self.tcinputs['csHostname']}")
            self.C1 = self.tcinputs["Network_Proxy1"]
            self.C2 = self.tcinputs["Network_Proxy2"]
            self.C3 = self.tcinputs["Network_Proxy3"]
            self.C4 = self.tcinputs["Network_Proxy4"]
            self.C5 = self.tcinputs["Install_Proxy"]
            self.C6 = self.tcinputs["Network_Proxy5"]
            self.all_C_clients = [self.C1, self.C2, self.C3, self.C4, self.C5, self.C6]
            self.client_install_machine_name = self.tcinputs["install_machine_name"]

            self.name = "[Network & Firewall] : Client Install via cascading gateways topology"

            self.new_client_name = "client_60582_" + str(datetime.now().microsecond)
            self._network = networkhelper.NetworkHelper(self)
            self.log.info("network_helper created")
            self._idautil = idautils.CommonUtils(self)
            self.log.info("idautils.CommonUtils created")

            self.client_group_names = ["Trusted Client Group1", "DMZ group near Trusted Client Group1",
                                       "DMZ group near Trusted Client Group2", "Trusted Client Group2"]
            self.storage_policy_name = "spolicy60582"

            self.topology_name = "Cascading Gateway Topology"
            self.tcinputs["proxy_name"] = self.C5

            self.log.info("Doing initial cleanup")
            self.cleanup()

            self.log.info("setup done")
        except Exception as err:
            self.status = constants.FAILED
            self.log.info(f"Error: {err}")
            self.cont = False
            traceback.print_exc()

    def run(self):
        if self.cont:
            try:
                self.log.info(f"=" * 70)
                self.log.info(f"=" * 70)
                self.log.info(f"START OF RUN TEST CASE 60582")
                self.log.info(f"=" * 70)
                self.log.info(f"=" * 70)

                self._idautil.check_client_readiness(self.all_C_clients)
                self.log.info("All clients ready")

                network_summaries_initial = self._network.get_network_summary(
                    [self.C1, self.C2, self.C3, self.C4, self.C5, self.C6])
                self.check_routes_are_clear(network_summaries_initial)

                self.log.info(f"Creating groups and topology")
                self.create_clients_groups_and_topologies()

                self.log.info(f"Installing real client")
                self.install_real_client()
                self.log.info("Installed client. Checking installation success.")
                self.check_new_client()

                self.log.info("Starting validation")
                self._network.validate(client_names=[self.new_client_name], media_agent=self.tcinputs["proxy_name"],
                                       test_data_level=1, test_data_size=10)
                self.log.info("Validation done.")

                self.log.info("Checking effects of topology changes.")
                try:
                    topology_changes_successful = self.check_topology_change_effects()
                    if topology_changes_successful:
                        self.log.info("Successfully checked effects of topology changes.")
                    else:
                        raise Exception("Topology changes not successful")
                except Exception:
                    raise Exception("Topology changes not successful")

                self.status = constants.PASSED
                self.log.info(f"Test case 60582 passed successfully")

            except Exception as err:
                self.status = constants.FAILED
                self.log.error(f"Error in run function. {err}")
                self._network.server.fail(err)

            finally:
                self._network.cleanup_network()
                self._install_helper1.uninstall_client()
                self._network.entities.cleanup()
                self.cleanup()
                self.log.info(f"Done cleanup")

    def cleanup(self):
        try:
            clients_to_del = ["dummy_client_1", "dummy_client_2", "dummy_client_3", self.new_client_name]
            for client_ in clients_to_del:
                try:
                    self.commcell.clients.delete(client_)
                except Exception as err:
                    self.log.info(f"Tried to delete client {client_} that does not exist. {err}")
            try:
                self._network.delete_topology(self.topology_name)
            except Exception as err:
                self.log.error(f"Tried to delete topology {self.topology_name} that does not exist. {err}")
            client_groups_to_del = ["Trusted Client Group1", "DMZ group near Trusted Client Group1",
                                    "DMZ group near Trusted Client Group2", "Trusted Client Group2"]
            for client_group_current in client_groups_to_del:
                try:
                    self.commcell.client_groups.delete(client_group_current)
                except Exception as e:
                    self.log.error(e)
            self.log.info("Groups deleted if they exist")
        except Exception as err:
            self.log.info(f"Error in cleanup: {err}")

    def create_clients_groups_and_topologies(self):
        try:
            self.commcell.clients.create_pseudo_client("dummy_client_1")
            self.commcell.clients.create_pseudo_client("dummy_client_2")
            self.commcell.clients.create_pseudo_client("dummy_client_3")
        except Exception as err:
            self.log.info(f"Error while creating dummy_client_ clients. {err}")
        # create groups
        try:
            self.commcell.client_groups.add(self.client_group_names[0], [self.C1, "dummy_client_1"])
            self.commcell.client_groups.add(self.client_group_names[1], [self.C2, self.C5, "dummy_client_2"])
            self.commcell.client_groups.add(self.client_group_names[2], [self.C3, self.C6, "dummy_client_3"])
            self.commcell.client_groups.add(self.client_group_names[3], [self.C4])
        except Exception as err:
            self.log.error(f"Error while creating groups. {err}")

        try:
            self._network.cascading_gateways_topology(self.client_group_names[0], self.client_group_names[3],
                                                      self.client_group_names[1],
                                                      self.client_group_names[2],
                                                      self.topology_name)
        except Exception as err:
            self.log.error(f"Error while creating topology {self.topology_name}. {err}")
            raise Exception(f"Error while creating topology {self.topology_name}. {err}")
        self.log.info("Done creating client groups and topology")

    def install_real_client(self):
        self.log.info(f"Beginning install prep")
        self.log.info(self.commcell.client_groups)

        self.proxy_name = self.tcinputs["proxy_name"]
        self.proxy_port = self.tcinputs["Install_Proxy_TunnelPort"]
        self.proxy_hostname = self.commcell.clients.get(self.proxy_name).client_hostname

        self.log.info("Creating machine object of machine on which to install client")
        self.client_install_machine = Machine(machine_name=self.tcinputs["install_machine_name"],
                                              username=self.tcinputs["install_machine_username"],
                                              password=self.tcinputs["install_machine_password"])

        self.log.info(f"Machine on which to install client: {self.client_install_machine}")

        self.install_inputs = {
            "force_ipv4": "1",
            "csClientName": self.tcinputs["csClientName"],
            "csHostname": self.tcinputs["csHostname"],
            "enableProxyClient": "1",
            "proxyHostname": self.proxy_hostname,
            "Install_Proxy_TunnelPort": self.proxy_port,
            "authCode": self.commcell.enable_auth_code(),
            "clientGroupName": self.client_group_names[0],
            "networkGateway": self.proxy_hostname + ':' + str(self.proxy_port),
            "mediaPath": "/media"
        }

        self.log.info(f"{self.install_inputs = }")
        self.log.info(f"Performing Silent Install")
        self.log.info(f"INSTALLING CLIENT")

        self._install_helper1 = InstallHelper(self.commcell, self.client_install_machine)
        self._install_helper1.silent_install(tcinputs=self.install_inputs,
                                             client_name=self.new_client_name)

        self.log.info(f"Done installing client. {self.new_client_name = }")

    def check_new_client(self):
        client_obj = None
        try:
            client_obj = self.commcell.clients.get(self.new_client_name)
            self.log.info(f"Client has been successfully created.")
        except Exception as err:
            self.log.error(f"The installed client can not be found. Error: {err}")

        client_base_path = self.client_install_machine.join_path(client_obj.install_directory, 'Base')
        file_path = os.path.join(client_base_path, "FwConfig.txt")
        try:
            file = self.client_install_machine.read_file(file_path)
            self.log.info(f"FwConfig.txt is present at expected location. {file = }")
        except Exception as err:
            self.log.info(f"Error: FwConfig.txt not present. {err}")

        network_summaries = self._network.get_network_summary([self.C2, self.C3, self.C4, self.C5, self.C6,
                                                               "dummy_client_2", "dummy_client_3"])

        for key in network_summaries:
            summary = network_summaries[key]
            summary = repr(summary)
            if self.new_client_name not in summary:
                self.log.error(f"Network summary may not be updated for client {key}")
                raise Exception(f"Network summary may not be updated for client {key}")
        self.log.info("Push after install was successful")

    def check_topology_change_effects(self):
        smart_group_type = 2
        self.log.info(f"Changing topology {self.topology_name} to smart topology")
        self._network.modify_topology(self.topology_name, is_smart_topology=True, firewall_groups=[
            {'group_type': smart_group_type, 'group_name': 'My MediaAgents', 'is_mnemonic': True}])
        self.log.info("Changing topology to regular topology")
        self._network.modify_topology(self.topology_name, is_smart_topology=False, firewall_groups=[
            {'group_type': smart_group_type, 'group_name': "Trusted Client Group2", 'is_mnemonic': False}])
        self.log.info("Changing topology to smart topology")
        self._network.modify_topology(self.topology_name, is_smart_topology=True, firewall_groups=[
            {'group_type': smart_group_type, 'group_name': 'My MediaAgents', 'is_mnemonic': True}])
        self.log.info(f"Deleting topology {self.topology_name}")
        self._network.delete_topology(self.topology_name)
        network_summaries = self._network.get_network_summary([self.C1, self.C2, self.C3, self.C4, self.C5, self.C6,
                                                               self.new_client_name, "dummy_client_1", "dummy_client_2",
                                                               "dummy_client_3"])
        self.check_routes_are_clear(network_summaries)

        self.log.info(f"All routes removed")
        return True

    def check_routes_are_clear(self, network_summaries):
        for key1 in network_summaries:
            summary = network_summaries[key1]
            summary = repr(summary)
            for key2 in network_summaries:
                if key2 == key1:
                    continue
                if (key1 + " " + key2 + " " in summary) or (key2 + " " + key1 + " " in summary):
                    self.log.error(f"Routes are incorrect. '{key1} {key2} ' is present in "
                                   f"network summary of {key1}")
                    raise Exception(f"Routes sre incorrect. '{key1} {key2} ' is present in "
                                    f"network summary of {key1}")
        self.log.info("No routes that are in conflict with requirements")
