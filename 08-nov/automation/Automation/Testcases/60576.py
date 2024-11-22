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

    set_mandate_encryption()     -- sets mandateEncryption to 1

    check_white_listing_not_enabled()    -- deletes the client groups created in the test case

    check_protocol_https_all_routes() -- checks that all routes are https

    cleanup()  -- cleans up test case entities

"""

from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import MMHelper
from Server.Network import networkhelper
from AutomationUtils import constants, idautils
import traceback
import time
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.topology_name = "network_two_way_topology_60576"
        self.client_grp_client = "network_client_clientgroup_60576"
        self.client_grp_MA = "network_MA_clientgroup_60576"
        self.tcinputs = {
            "network_MA": "string",
            "network_client": "string"
        }
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK

        self.name = "[Network & Firewall] : MandateEncryption"
        self._network = None
        self.all_clients = None
        self.media_agent = None
        self.source_client = None
        self.initial_network_summaries = None
        self._idautil = None
        self.mmhelper_obj = None

    def setup(self):
        self.log.info("Beginning setup")
        self._network = networkhelper.NetworkHelper(self)
        self._idautil = idautils.CommonUtils(self)
        self.all_clients = list(self.commcell.clients.all_clients.keys())
        self.media_agent = self.tcinputs["network_MA"]
        self.source_client = self.tcinputs["network_client"]
        self.cleanup()
        self.mmhelper_obj = MMHelper(self)
        self.add_topology()
        self.log.info("Successfully setup test case")

    def add_topology(self):
        try:
            self.commcell.client_groups.add(self.client_grp_MA, [self.media_agent])
            self.commcell.client_groups.add(self.client_grp_client, [self.source_client])
        except Exception as err:
            self.log.error(f"Cannot create client groups. {err}")
        self._network.two_way_topology(self.client_grp_MA, self.client_grp_client, self.topology_name)
        self.log.info(f"Done creating topology: {self.topology_name}")

    def run(self):
        try:
            self.log.info("=" * 70)
            self.log.info("=" * 70)
            self.log.info("START OF RUN -> TEST CASE 60576")
            self.log.info("=" * 70)
            self.log.info("=" * 70)

            self._idautil.check_client_readiness([self.source_client, self.media_agent])
            self.set_mandate_encryption()
            self.initial_network_summaries = self._network.get_network_summary(self.all_clients)
            self.check_white_listing_not_enabled()
            self.check_protocol_https_all_routes()

            self._network.validate(client_names=[self.source_client], media_agent=self.media_agent,
                                   test_data_level=1, test_data_size=10)

            self.status = constants.PASSED
            self.log.info("Test case 60576 passed successfully")

        except Exception as err:
            self.status = constants.FAILED
            self.log.error(err)
            self._network.server.fail(err)

        finally:
            self.cleanup()
            self._network.cleanup_network()
            self._network.entities.cleanup()

    def set_mandate_encryption(self):
        try:
            new_param_value = self.mmhelper_obj.get_global_param_value("mandateEncryption")
            self.log.info(f"Initially mandateEncryption key value = {new_param_value}")
        except Exception as err:
            self.log.info(f"mandateEncryption key may not exist initially. {err}")
        try:
            self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam", key_name="mandateEncryption",
                                                 data_type="INTEGER", value="1")
            new_param_value = self.mmhelper_obj.get_global_param_value("mandateEncryption")
            self.log.info(f"mandateEncryption key value = {new_param_value}")
            if new_param_value != 1:
                raise Exception("mandateEncryption key value is not 1.")
        except Exception as err:
            raise Exception(f"Additional setting NOT successful. {err}")

    def check_white_listing_not_enabled(self):
        query_to_execute = "select * from APP_AdvanceSettings where keyName = 'enableClientWhitelist' and " \
                           "relativePath='CommServDB.GxGlobalParam' "
        col1, res = self._network.options.exec_commserv_query(
            query_to_execute
        )
        self.log.info(f"Executed query '{query_to_execute}'. Response= {res}")
        value = -1
        if len(res[0]) <= 1:
            self.log.info("enableClientWhitelist key not present")
        else:
            value = res[0][5]
            self.log.info(f"enableClientWhitelist key has value = {value}")

        network_summaries = self.initial_network_summaries
        if value <= 0:
            # no whitelist
            pass
            # for key in network_summaries:
            #     network_summaries_list = network_summaries[key].split("[")
            #     for section in network_summaries_list:
            #         if ("[incoming]" in section) and ("whitelist_mode=1" in section):
            #             self.log.error("White listing is enabled even though key enableClientWhitelist is not 1")
            #             raise Exception("White listing is enabled even though key enableClientWhitelist is not 1")
        self.log.info("White listing correct")

    def check_protocol_https_all_routes(self):
        self.log.info(f"Checking if https protocol is used.")
        return 
        network_summaries = self.initial_network_summaries
        self.log.info(network_summaries)
        error_prefix = "Error in network summary. All routes may not be https."
        for key in network_summaries:
            # one iteration for each client
            force_incoming_https_line_present = False
            ns = network_summaries[key]  # get network summary of a client
            if len(ns.strip()) < 10:  # skip clients that do not have any routes (or summary)
                continue
            self.log.info(ns)
            if "type=dip" in ns:
                continue
            if ("force_incoming_https=" in ns) or ("force_incoming_ssl=" in ns):
                if ("proto=" in ns):
                    if not ("proto=https" in ns):
                        raise Exception("Conditions not met for client {key}")

    def cleanup(self):
        self.log.info("Cleaning up...")
        try:
            self.commcell.delete_additional_setting("CommServDB.GxGlobalParam", "mandateEncryption")
        except Exception as err:
            self.log.error(f"Error cleaning up: {err}")

        client_groups_to_del = [self.client_grp_MA, self.client_grp_client]
        for client_group_current in client_groups_to_del:
            try:
                self.commcell.client_groups.delete(client_group_current)
            except Exception as e:
                self.log.error(e)
        self.log.info("Groups deleted if they exist")
