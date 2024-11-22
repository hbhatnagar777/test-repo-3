# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

import time
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """ Monitor cvfwd upon change in system time change  """
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall]:Monitor cvfwd upon change in system time change"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkMediaAgent": None
        }
        self.client = None
        self.ma = None
        self.network_helper = None
        self.cl_obj = None
        self.machine = None
        self.cl_grp = "cl_grp_53598"
        self.proxy_grp = "proxy_grp_53598"
        self.cs_grp = "cs_grp_53598"

    def setup(self):
        self.network_helper = NetworkHelper(self)
        self.client = self.tcinputs["NetworkClient"]
        self.ma = self.tcinputs["NetworkMediaAgent"]
        self.log.info("[*] Getting client object [*]")
        self.cl_obj = self.commcell.clients.get(self.client)
        self.machine = Machine(self.cl_obj)

        if self.commcell.client_groups.has_clientgroup(self.cl_grp):
            self.commcell.client_groups.delete(self.cl_grp)
        self.commcell.client_groups.add(self.cl_grp, [self.client])

        if self.commcell.client_groups.has_clientgroup(self.proxy_grp):
            self.commcell.client_groups.delete(self.proxy_grp)
        self.commcell.client_groups.add(self.proxy_grp, [self.ma])

        if self.commcell.client_groups.has_clientgroup(self.cs_grp):
            self.commcell.client_groups.delete(self.cs_grp)
        self.commcell.client_groups.add(self.cs_grp, [self.commcell.commserv_name])

    def run(self):
        try:
            self.log.info("[*] Setting up proxy topology [*]")
            self.network_helper.proxy_topology(self.cl_grp, self.cs_grp,
                                               self.proxy_grp, "Topology_53598")

            self.log.info("[*] Change time to 2 hours ahead of current time [*]")
            old_mem_usage = self.get_mem_usage()
            self.machine.change_system_time(7200)
            self.cl_obj.restart_services()
            new_mem_usage = self.get_mem_usage()
            if new_mem_usage > (1.5*old_mem_usage):
                raise Exception("After changing the time memory consumption increased drastically!")
            if not self.machine.execute_command(
                    f'netstat -ano | findstr "0.0.0.0:{self.cl_obj.network.tunnel_connection_port}"').output:
                raise Exception("Machine is not listening on cvfwd port")
            self.network_helper.validate([self.client], self.ma)

            self.log.info("[*] Resting the time to current time [*]")
            self.machine.change_system_time(-7200)
            self.cl_obj.restart_services()
            time.sleep(60)

            self.log.info("[*] Change time to 2 hours behind of current time [*]")
            old_mem_usage = self.get_mem_usage()
            self.machine.change_system_time(-7200)
            self.cl_obj.restart_services()
            new_mem_usage = self.get_mem_usage()
            if new_mem_usage > (1.5*old_mem_usage):
                raise Exception("After changing the time memory consumption increased drastically!")
                
            if not self.machine.execute_command(
                    f'netstat -ano | findstr "0.0.0.0:{self.cl_obj.network.tunnel_connection_port}"').output:
                raise Exception("Machine is not listening on cvfwd port")
            self.network_helper.validate([self.client], self.ma)

        except Exception as e:
            self.log.info(f"Failed with Exception : {str(e)}")

        finally:
            self.machine.change_system_time(7200)
            self.network_helper.delete_topology("Topology_53598")
            self.commcell.client_groups.delete(self.cl_grp)
            self.commcell.client_groups.delete(self.proxy_grp)
            self.commcell.client_groups.delete(self.cs_grp)

    def get_mem_usage(self):
        pid = self.machine.get_process_id("cvfwd.exe")[0]
        statistics = []
        for _ in range(10):
            time.sleep(10)
            stats = self.machine.get_process_stats(pid)
            statistics.append(stats.get('memory'))
        return sum(statistics)//10
