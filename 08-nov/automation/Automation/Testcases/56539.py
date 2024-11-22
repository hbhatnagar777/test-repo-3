# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """
    Logging of per-node and per-sockect I/O statistics 
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : cvfwd statistics"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkMediaAgent": None
        }
        self.network_helper = None
        self.cl = None
        self.ma = None
        self.ma_obj = None
        self.machine_ma = None

    def setup(self):
        self.log.info("[+] Creating client and machine object [+]")
        self.network_helper = NetworkHelper(self)
        self.cl = self.tcinputs["NetworkClient"]
        self.ma = self.tcinputs["NetworkMediaAgent"]
        self.ma_obj = self.commcell.clients.get(self.ma)
        self.machine_ma = Machine(self.ma_obj)
        self.network_helper.remove_network_config([
            {'clientName': self.cl},
            {'clientName': self.ma}
        ])

    def run(self):
        try:
            self.log.info("[+] Configuring one-way firewall rule between client & mediaagent [+]")
            self.network_helper.set_one_way(
                {'clientName': self.ma},
                {'clientName': self.cl}
            )
            self.log.info("[+] Setting the registry keys [+]")
            self.machine_ma.create_registry("Firewall", "nSTATS_HIST_INTERVAL", "10")
            self.machine_ma.create_registry("Firewall", "nSTATS_HIST_LENGTH", "10")
            self.machine_ma.create_registry("Firewall", "nSTATS_LOG_INTERVAL", "10")
            self.machine_ma.create_registry("Firewall", "nSTATS_MEASURE_INTERVAL", "10")
            self.network_helper.push_config_client([self.cl, self.ma])

            self.log.info("[+] Restarting the services on mediaagent [+]")
            self.ma_obj.restart_services()

            self.network_helper.validate_with_plan([self.cl], self.ma)

            self.log.info("[+] Parsing and validing the cvfwd log file [+]")
            cvfwd_log = self.machine_ma.get_log_file("cvfwd.log")
            head_start = cvfwd_log.rfind("Per-socket send/recv rates over the last")
            data = cvfwd_log[head_start:head_start+400].split('\n')
            mid = data[1]
            end = data[2]
            table_head_str = "Size, bytes   Time, usec   Rate, MB/s   Tput, MB/s   LT Size, bytes   LT Rate, " \
                             "MB/s   Latency, ms   CName"
            if table_head_str not in mid:
                raise Exception("Table row headings are not populated correctly")
            if len((end.split("########")[-1]).split()) != 9:
                raise Exception("Incorrect number of columns are populated")
            self.log.info("[+] Completed Successfully [+]")
        except Exception as e:
            self.log.info("Exception: " + str(e))

        finally:
            self.log.info("[+] Executing cleanup part [+]")
            self.network_helper.cleanup_network()
            self.machine_ma.create_registry("Firewall", "nSTATS_HIST_INTERVAL", "0")
            self.machine_ma.create_registry("Firewall", "nSTATS_HIST_LENGTH", "0")
            self.machine_ma.create_registry("Firewall", "nSTATS_LOG_INTERVAL", "0")
            self.machine_ma.create_registry("Firewall", "nSTATS_MEASURE_INTERVAL", "0")
            self.ma_obj.restart_services()
