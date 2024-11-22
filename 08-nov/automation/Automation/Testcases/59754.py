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

    add_client_groups()     -- creates the required client groups for the test case

    delete_client_groups()    -- deletes the client groups created in the test case

    verify_all_network_summaries_after_changes() -- verifies network summaries after adding a client to a client group

    verify_network_summary() -- verifies one network summary

    cleanup()  -- cleans up test case entities

    verify_init_conditions()  -- verifies initial conditions are correct for test case to run


"""
# Shubhankar
import traceback

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.Network import networkhelper
import time
from AutomationUtils import constants, idautils


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes testcase class object"""
        self.time_wait = 150  # (seconds)
        self.event_descriptions = []
        self.continue_running_test_case = True
        try:
            super(TestCase, self).__init__()
            self.client_groups_to_add = ['network_client_group_59754_1', 'network_client_group_59754_2',
                                         'network_client_group_59754_3']
            self.all_client_names = []
            self.product = self.products_list.COMMSERVER
            self.feature = self.features_list.NETWORK

            self.name = "[Network & Firewall] : Verify Network push behavior when client is added/removed from a " \
                        "firewalled client group for topology "
            self.tcinputs = {
                "network_client_1": None,
                "network_client_2": None,
                "network_client_3": None,
                "network_client_4": None
            }
            self.client_names = None
            self.all_client_names = None
            self._network = None
            self._idautil = None
            self.is_B_MA_or_CS = None
            self.is_C_MA_or_CS = None

        except Exception:
            self.continue_running_test_case = False

    def setup(self):
        self._network = networkhelper.NetworkHelper(self)
        self._idautil = idautils.CommonUtils(self)
        self.client_names = [self.tcinputs["network_client_1"],
                             self.tcinputs["network_client_2"],
                             self.tcinputs["network_client_3"]]

        self.all_client_names = list(self.client_names)
        self.all_client_names.append(self.tcinputs["network_client_4"])
        self._idautil.check_client_readiness(self.all_client_names)
        self.log.info("Test case setup done")
        self.prev_time = None

    def run(self):
        if not self.continue_running_test_case:
            self.log.error("There was an error in __init__() function, due to which test case execution is being "
                           "terminated")
        else:
            try:
                self.log.info("=" * 70)
                self.log.info("=" * 70)
                self.log.info("START OF RUN -> TEST CASE 59754")
                self.log.info("=" * 70)
                self.log.info("=" * 70)

                propsDictB = self.commcell.clients.get(self.tcinputs["network_client_2"]).properties
                propsDictC = self.commcell.clients.get(self.tcinputs["network_client_3"]).properties
                self.is_B_MA_or_CS = propsDictB['clientProps']['isMA'] or propsDictB['clientProps']['IsCommServer']
                self.is_C_MA_or_CS = propsDictC['clientProps']['isMA'] or propsDictC['clientProps']['IsCommServer']

                if not self.is_C_MA_or_CS:
                    self.log.error(f"network_client_3 ({self.tcinputs['network_client_3']}) "
                                   f"must be a CommServer or MA")
                    raise Exception(f"network_client_3 ({self.tcinputs['network_client_3']}) "
                                    f"must be a CommServer or MA")
                self.cleanup()
                self.verify_init_conditions()

                self.add_client_groups(self.client_groups_to_add, self.client_names)
                self.prev_time = int(time.time()) - 200
                self.log.info(f"Time at start of test case event: {self.prev_time}")
                self._network.proxy_topology(
                    self.client_groups_to_add[0], self.client_groups_to_add[2],
                    self.client_groups_to_add[1], 'newProxy59754', False
                )

                # client group = network_client_group_1, infra group = network_client_group_3,
                # MA group = network_client_group_2
                self.log.info("Proxy topology created")

                self.commcell.client_groups.get(self.client_groups_to_add[0]).add_clients(
                    self.tcinputs["network_client_4"])
                self.log.info(f"New client added. Waiting for {self.time_wait} seconds")
                time.sleep(self.time_wait)
                self.log.info("Waiting over")

                self.verify_all_network_summaries_after_changes()
                # THIS PART IS NOT NEEDED AFTER SP36 AS CLIENTS ARE PUSHED INDEPENDENTLY WITHOUT EVENTS
                # self.commcell.client_groups.get(self.client_groups_to_add[0]).remove_clients(
                #     self.tcinputs["network_client_4"])
                # self.log.info(f"New client removed. Waiting for {self.time_wait} seconds")
                # time.sleep(self.time_wait)
                # self.log.info("Waiting over")
                #
                # self.verify_all_network_summaries_after_changes()

                self.status = constants.PASSED
                self.log.info("Test case 59754 passed successfully.")
            except Exception as err:
                raise Exception(err)
            finally:
                self.log.info("Running finally block code")
                self._network.cleanup_network()
                self._network.entities.cleanup()
                self.cleanup()
                self.log.info("cleanup successful")

    def add_client_groups(self, client_groups_to_add, client_names):
        for i in range(len(client_groups_to_add)):
            self.commcell.client_groups.add(client_groups_to_add[i], client_names[i])
        self.log.info("Done creating groups and adding clients")

    def delete_client_groups(self, client_groups_to_add):
        for client_group_current in client_groups_to_add:
            try:
                self.commcell.client_groups.delete(client_group_current)
            except Exception as e:
                self.log.error(e)
        self.log.info("Groups deleted if they exist")

    def verify_all_network_summaries_after_changes(self):
        self.log.info("Verifying network summaries")
        events = self.commcell.event_viewer
        present_time = int(time.time())
        approx_add_del_start_time = self.prev_time
        keys = list(events.events({"fromTime": str(approx_add_del_start_time), "toTime": str(present_time)}).keys())
        self.log.info(f"Got {len(keys)} events for fromTime={approx_add_del_start_time} to toTime={present_time}")
        self.event_descriptions = []
        for i in range(0, len(keys)):
            key = keys[i]
            try:
                self.event_descriptions.append(events.get(key)._description)
            except Exception as err:
                self.log.info(f"Could not get event description for event {key}. {err}")
        if len(self.event_descriptions) == 0:
            self.log.error("Event descriptions list is empty.")
            raise Exception("Event descriptions list is empty.")
        self.log.info(f"Constructed list of event descriptions. Total {len(self.event_descriptions)} event "
                      f"descriptions.")
        for ev in self.event_descriptions:
            self.log.info("\t\t" + ev)
        self.verify_network_summary(self.tcinputs["network_client_1"], False)
        self.verify_network_summary(self.tcinputs["network_client_4"], False)
        self.log.info(f"{self.tcinputs['network_client_2']} is a media agent or CommServer : {self.is_B_MA_or_CS}")
        self.verify_network_summary(self.tcinputs["network_client_2"], self.is_B_MA_or_CS)
        self.verify_network_summary(self.tcinputs["network_client_3"])

    def verify_network_summary(self, client_name, check_events=True):
        """Verifies the network summary for a specific client"""
        try:
            self.log.info(f"Verifying network summary for client: {client_name}")

            # Check if event logs are necessary
            if check_events:
                self.log.info("Checking event descriptions.")
                client_config_pushed_in_event_list = any(
                    f"Network Configuration successfully pushed for client [{client_name}]" in desc
                    for desc in self.event_descriptions
                )
                if not client_config_pushed_in_event_list:
                    raise Exception(f"'Network Configuration successfully pushed' event not found for {client_name}")

            # Retrieve network summary using the correct method
            network_summary_local = self.commcell.clients.get(client_name).get_network_summary()
            client_machine = Machine(self.commcell.clients.get(client_name))

            # Construct the file path and read the config
            network_client_base_path = client_machine.join_path(
                self.commcell.clients.get(client_name).install_directory, 'Base', "FwConfig.txt"
            )
            fwconfig_contents = client_machine.read_file(network_client_base_path)

            # Strip spaces and compare the summaries
            network_summary_local_stripped = "".join(network_summary_local.split())
            fwconfig_contents_stripped = "".join(fwconfig_contents.split())

            if network_summary_local_stripped != fwconfig_contents_stripped:
                raise Exception(f"Network summary mismatch for {client_name}")

            self.log.info(f"Network summary verification passed for client {client_name}")
        except Exception as err:
            self.log_error(f"Error verifying network summary for {client_name}", err)
            raise

    def cleanup(self):
        self.log.info("Cleaning up (deleting topologies and client groups)")
        try:
            self._network.delete_topology('newProxyTopology')
        except Exception as err:
            self.log.info(err)
        try:
            self.delete_client_groups(self.client_groups_to_add)
        except Exception as err:
            self.log.info(err)
        self.log.info("Cleaning up (deleting topologies and client groups): SUCCESS")

    def verify_init_conditions(self):
        summaries_init = self._network.get_network_summary(self.all_client_names)
        blacklist = []
        for i in range(len(self.client_names)):
            for j in range(i + 1, len(self.client_names)):
                blacklist.append(self.client_names[i] + " " + self.client_names[j])
                blacklist.append(self.client_names[j] + " " + self.client_names[i])
        for key in summaries_init:
            net_sum = repr(summaries_init[key])
            for blacklisted_pair in blacklist:
                if blacklisted_pair in net_sum:
                    raise Exception(f"Checked client network summaries: INCORRECT. {blacklisted_pair} present in "
                                    f"network summary of {key}")

        self.log.info("Checked client network summaries: CORRECT")

    def log_error(self, description, err):
        """Helper function to log error details"""
        self.log.error(f"{description}: {str(err)}")
        self.log.debug(f"Traceback: {traceback.format_exc()}")
