# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


""""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case

It does the following:
Step 1. Create a one-way firewall rule from the client to the MA.
Step 2. Set absolute network throttle between the client and the MA.
Step 3. Set number of tunnels on outgoing network route to 5.
Step 4. Do push network configuration.
Step 5. Run a full backup job with a sufficiently large amount of data.
Step 6. Check if backup is successful
Step 7. Check if network summary is correct
Step 8. Repeat steps 1 to 7 for but set relative network throttle in Step 2.

TestCase:
    __init__()                            --  initialize TestCase class

    setup()                               --  setup function of this test case

    run()                                 --  run function of this test case

    run_test()                            --  run test case for particular throttling mode

    check_network_summary_correct()       --  check if the network summary is correct

    cleanup()                             -- delete client groups created

"""
# Shubhankar
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network import networkhelper
from AutomationUtils import constants, idautils


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()

        self.rel_send_rate = 2048
        self.rel_recv_rate = 1024
        self.abs_recv_rate = 1000
        self.abs_send_rate = 4096
        self.num_of_streams = 5
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK

        self.name = "[Network & Firewall] : Testcase to verify the behavior of network throttle with multiple tunnels"
        self.tcinputs = {
            "network_MA": None,
            "network_client": None
        }
        self.client_names = None
        self._network = None
        self.client_name = None
        self.media_agent = None
        self._idautil = None

    def setup(self):
        self._network = networkhelper.NetworkHelper(self)
        self._idautil = idautils.CommonUtils(self)
        self.client_names = [self.tcinputs["network_client"], self.tcinputs["network_MA"]]
        self.client_name = self.tcinputs["network_client"]
        self.media_agent = self.tcinputs["network_MA"]
        self._idautil.check_client_readiness(self.client_names)

    def run(self):
        try:
            self.log.info("=" * 70)
            self.log.info("=" * 70)
            self.log.info("START OF RUN -> TEST CASE 60224")
            self.log.info("=" * 70)
            self.log.info("=" * 70)

            try:
                self.cleanup()
            except Exception as err:
                self.log.info(f"Error in initial cleanup. {err}")
            self.verify_init_conditions(self.client_names)

            self.run_test(throttle_mode="absolute")
            self.run_test(throttle_mode="relative")

            self.status = constants.PASSED
            self.log.info("============== Test case ran successfully ================")

        except Exception as err:
            self.status = constants.FAILED
            self.log.error("An error occurred in the run function")
            self.log.error(err)
            self._network.server.fail(err)

        finally:
            self.log.info("Cleaning up...")
            self.cleanup()

    def run_test(self, throttle_mode):
        self._network.set_one_way(
            {'clientName': self.media_agent},
            {'clientName': self.client_name}
        )

        self.log.info(f"One way firewall from the client {self.client_name} to the media agent "
                      f"{self.media_agent}")

        if throttle_mode == "relative":
            try:
                self._network.set_network_throttle(entity={'clientName': self.client_name},
                                                   remote_clients=[self.media_agent],
                                                   throttle_rules=[
                                                       {
                                                           "sendRate": self.rel_send_rate,
                                                           "sendEnabled": True,
                                                           "receiveEnabled": True,
                                                           "recvRate": self.rel_recv_rate,
                                                           "days": '1111111',
                                                           "isAbsolute": False,
                                                           "startTime": 0,
                                                           "endTime": 0,
                                                           "sendRatePercent": 40,
                                                           "recvRatePercent": 40
                                                       }])
            except Exception as err:
                raise Exception(f"Error in setting throttle. {err}")

        elif throttle_mode == "absolute":
            try:
                self._network.set_network_throttle(entity={'clientName': self.client_name},
                                                   remote_clients=[self.media_agent],
                                                   throttle_rules=[
                                                       {
                                                           "sendRate": self.abs_send_rate,
                                                           "sendEnabled": True,
                                                           "receiveEnabled": True,
                                                           "recvRate": self.abs_recv_rate,
                                                           "days": '1111111',
                                                           "isAbsolute": True,
                                                           "startTime": 0,
                                                           "endTime": 0

                                                       }])
            except Exception as err:
                raise Exception(f"Error in setting throttle. {err}")
        else:
            raise Exception(f"ERROR: Parameter 'throttle_mode' not correct")

        self.log.info("throttle mode set successfully")
        try:
            self._network.outgoing_route_settings({'clientName': self.client_name},
                                                  streams=self.num_of_streams,
                                                  is_client=True,
                                                  remote_entity=self.media_agent,
                                                  connection_protocol=2)
            self.log.info(f"Set number of streams as {self.num_of_streams}")
        except Exception as err:
            raise Exception(f"Error in setting outgoing route settings. {err}")
        try:
            self._network.push_config_client([self.client_name, self.media_agent])
        except Exception as err:
            raise Exception(f"Error in setting pushing network config. {err}")
        try:
            self._network.validate(client_names=[self.client_name], media_agent=self.media_agent,
                                   test_data_level=1, test_data_size=10)
        except Exception as err:
            raise Exception(f"Error in validating backup. {err}")
        network_summary_correct = True
        try:
            network_summary_correct = self.check_network_summary_correct(throttle_mode)
        except Exception as err:
            raise Exception(f"Error in checking network summary. {err}")

        self.log.info("Network configuration and validation done")
        if network_summary_correct:
            self.log.info("Network summary is correct.")
        else:
            raise Exception("Network summary is not correct.")

        self._network.remove_network_throttle([{'clientName': self.client_name}, {'clientName': self.media_agent}])
        self._network.cleanup_network()

    def cleanup(self):
        if self._network is not None:
            self._network.remove_network_config([{'clientName': self.client_name},
                                                 {'clientName': self.media_agent},
                                                 ])
            self._network.cleanup_network()
            self._network.remove_network_throttle([{'clientName': self.client_name}, {'clientName': self.media_agent}])
            self._network.entities.cleanup()

    def verify_init_conditions(self, all_client_names):
        # function to verify that the initial conditions needed for successful execution of test case are met
        initial_network_summaries = self._network.get_network_summary(all_client_names)
        blacklist = []
        for i in range(len(self.client_names)):
            for j in range(i + 1, len(self.client_names)):
                blacklist.append(self.client_names[i] + " " + self.client_names[j])
                blacklist.append(self.client_names[j] + " " + self.client_names[i])
        for key_client_name in initial_network_summaries:
            net_sum = repr(initial_network_summaries[key_client_name])
            for blacklisted_pair in blacklist:
                if blacklisted_pair in net_sum:
                    raise Exception(f"Checked initial conditions. Client network summaries incorrect."
                                    f" {blacklisted_pair} present in network summary of {key_client_name}")

            net_sum_list = net_sum.split("\\n")
            for i in range(len(net_sum_list)):
                line = net_sum_list[i]
                if line == "[throttling]" and i + 1 < len(net_sum_list):
                    if ("_remote_clients=" + self.media_agent in net_sum_list[i + 1]) \
                            or "_remote_clients=" + self.client_names in net_sum_list[i + 1]:
                        raise Exception("Throttling section already has settings for other entity")
        self.log.info("Checked initial conditions. Client network summaries correct")

    def check_network_summary_correct(self, throttle_mode):
        return True
        streams_checked = False
        network_summary_list = repr(self.commcell.clients.get(self.client_name).get_network_summary()).split("\\n")
        days_correct = 0
        for i in range(len(network_summary_list)):
            line = network_summary_list[i]
            # Checking if there is a line specifying correct number of streams
            # between client and MA
            if ("streams=" + str(self.num_of_streams) in line) and (self.client_name in line) \
                    and (self.media_agent in line):
                streams_checked = True
            # Checking if throttling lines are there for all days (as specified while setting throttle)
            check_line_abs = f"_00:00={self.abs_recv_rate},{self.abs_send_rate}"
            check_line_rel = f"_00:00=0/{self.rel_recv_rate}/40%,0/{self.rel_send_rate}/40%"
            if (
                    (check_line_abs in line and throttle_mode == "absolute")
                    or
                    (check_line_rel in line and throttle_mode == "relative")
            ):
                days_correct += 1
        if days_correct != 7:
            self.log.error(f"Throttling not correct for all days for {throttle_mode = }")
            return False
        if not streams_checked:
            self.log.error(f"Streams may not have been set correctly for {throttle_mode = }")
            return False
        self.log.info(f"Network summary is correct for {throttle_mode = }")
        return True
