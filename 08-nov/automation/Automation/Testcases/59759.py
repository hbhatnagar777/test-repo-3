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

import time
import uuid
from datetime import datetime
from AutomationUtils.machine import Machine
from cvpysdk.storage_pool import StoragePools
from Server.Plans.planshelper import PlansHelper
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from cvpysdk.network_topology import NetworkTopology


class TestCase(CVTestCase):
    """
    [Network & Firewall] : Topology test cases
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Topology test cases"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "networkClientRegion1": None,
            "networkProxy": None,
            "networkProxy1": None,
            "networkProxy2": None,
            "mediaAgentRegion2": None
        }
        self.storage_pool = None
        self.network_helper = None
        self.JOB_EXECUTED_TIME = 0
        self.JOB_STARTED = 0
        self.JOB_ENDED = 0
        self.proxy_cs = None
        self.proxy_cl = None
        self.proxy_cl1 = None
        self.ma = None
        self.test_data_size = 59000
        self.storage_policy_name = None
        self.client_obj = None
        self.agent_obj = None
        self.backupset_obj = None
        self.subclient_obj = None
        self.plan_name = None
        self.storage_pool_name = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.network_helper = NetworkHelper(self)
            self.storage_pool = StoragePools(self.commcell)
            self.client = self.tcinputs['networkClientRegion1']
            self.proxy_cs = self.tcinputs['networkProxy']
            self.proxy_cl = self.tcinputs['networkProxy1']
            self.proxy_cl1 = self.tcinputs['networkProxy2']
            self.ma = self.tcinputs['mediaAgentRegion2']

            self.log.info("[+] Creating client groups and adding clients [+]")
            if self.commcell.client_groups.has_clientgroup("External_CG_59759"):
                self.commcell.client_groups.delete('External_CG_59759')
            self.commcell.client_groups.add("External_CG_59759", [self.client])

            if self.commcell.client_groups.has_clientgroup("Proxy_CG_59759"):
                self.commcell.client_groups.delete('Proxy_CG_59759')
            self.commcell.client_groups.add("Proxy_CG_59759", [self.proxy_cs])

            if self.commcell.client_groups.has_clientgroup("External_Proxy_CG_59759"):
                self.commcell.client_groups.delete('External_Proxy_CG_59759')
            self.commcell.client_groups.add("External_Proxy_CG_59759", [self.proxy_cl])

            if self.commcell.client_groups.has_clientgroup("CS_CG_59759"):
                self.commcell.client_groups.delete('CS_CG_59759')
            self.commcell.client_groups.add("CS_CG_59759", [self.commcell.commserv_name])

            self.storage_policy_name = self.create_storage_policy_assoc(self.ma, self.client)

            # Objects
            self.client_obj = self.commcell.clients.get(self.client)
            self.agent_obj = self.client_obj.agents.get('File System')
            self.backupset_obj = self.agent_obj.backupsets.get('defaultBackupSet')
            self.subclient_obj = self.backupset_obj.subclients.get("test_59759_subclient")

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)

    def run(self):
        """Run function """
        try:
            self.log.info("[*] STEP 1 [*]")

            self.log.info("[+] Creating network gatway topology [+]")
            self.network_helper.proxy_topology(
                "External_CG_59759",
                "My CommServe Computer",
                "Proxy_CG_59759",
                "proxy_topology_59759"
            )
            self.log.info("[+] Setting tunnel port to 443 [+]")
            self.network_helper.set_tunnelport(
                [{'clientGroupName': "Proxy_CG_59759"}], [443]
            )

            self.log.info("[+] Upgrading topology to cascading network gateway [+]")
            topology = NetworkTopology(self.commcell, "proxy_topology_59759")
            topology.update(
                [
                    {'group_type': 1, 'group_name': "External_CG_59759", 'is_mnemonic': False},
                    {'group_type': 2, 'group_name': "My CommServe Computer", 'is_mnemonic': True},
                    {'group_type': 3, 'group_name': "Proxy_CG_59759", 'is_mnemonic': False},
                    {'group_type': 4, 'group_name': "External_Proxy_CG_59759", 'is_mnemonic': False},
                ],
                is_smart_topology=True,
                topology_type=4
            )

            self.commcell.refresh()
            summary = self.network_helper.get_network_summary([self.proxy_cs])[self.proxy_cs]
            if summary.find(f"tunnel_ports=443") == -1:
                raise Exception(f"Tunnel port for {self.proxy_cs} is not 443")

            self.network_helper.topologies.delete("proxy_topology_59759")
            self.log.info("[*] STEP 2 [*]")
            self.log.info("[+] Creating network topology with 4 streams and httpsa protocol [+]")
            self.network_helper.topologies.add(
                "proxy_topology_59759", [
                    {'group_type': 1, 'group_name': "External_CG_59759", 'is_mnemonic': False},
                    {'group_type': 2, 'group_name': "CS_CG_59759", 'is_mnemonic': False},
                    {'group_type': 3, 'group_name': "Proxy_CG_59759", 'is_mnemonic': False}],
                number_of_streams=4,
                encrypt_traffic=0,
                topology_type=1,
                topology_description="This is a test for validating proxy firewall topology."
            )

            # self.log.info("[+] Checking the network routes [+]")
            # summary = self.network_helper.get_network_summary([self.client])[self.client]
            # temp_idx1 = summary.find(f"{self.client} {self.proxy_cs}") + len(f"{self.client} {self.proxy_cs}")
            # temp_idx1 += 66  # Length of GUID + len("type=persistent")
            # if summary[temp_idx1:temp_idx1 + 11] == "proto=https" and summary[temp_idx1 + 11] != 'a':
            #     raise Exception(f"Protocol for {self.client} is https")

            # summary = self.network_helper.get_network_summary([self.client])[self.client]
            # if summary.find("streams=4") == -1:
            #     raise Exception(f"Streams did not set for client {self.client}")

            self.log.info("[+] Setting encrypt traffic to True [+]")
            topology = NetworkTopology(self.commcell, "proxy_topology_59759")
            topology.update(encrypt_traffic=1)
            self.commcell.refresh()

            self.log.info("[+] Checking the network routes [+]")
            # summary = self.network_helper.get_network_summary([self.client])[self.client]
            # if summary.find("streams=4") == -1:
            #     raise Exception(f"Streams did not set for client {self.client}")

            # temp_idx1 = summary.find(f"{self.client} {self.proxy_cs}") + len(f"{self.client} {self.proxy_cs}")
            # temp_idx1 += 66  # Length of GUID + len("type=persistent")
            # if summary[temp_idx1:temp_idx1 + 11] == "proto=https" and summary[temp_idx1 + 11] != ' ':
            #     raise Exception(f"Protocol for {self.client} is not https")

            self.network_helper.topologies.delete("proxy_topology_59759")

            self.log.info("[*] STEP 3 [*]")
            self.network_helper.proxy_topology(
                "External_CG_59759", "CS_CG_59759",
                "Proxy_CG_59759", "proxy_topology_59759", wildcard=True
            )

            self.commcell.refresh()
            self.log.info("[+] Creating machine object [+]")
            client_obj = self.commcell.clients.get(self.client)
            machine_obj = Machine(client_obj)
            dt = machine_obj.current_time()
            s = f"{dt.day}/{dt.month} {dt.hour}:{dt.minute}:{dt.second} ######## ######## Creating tracking tunnel toward CommServe"
            if machine_obj.check_if_pattern_exists_in_log(s, 'cvfwd.log'):
                raise Exception(f"Tracking tunnels are being created.")

            self.log.info(f"[+] Checking routes for {self.client} [+]")
            # summary = self.network_helper.get_network_summary([self.client])[self.client]
            # if f"{self.client} * proxy={self.proxy_cs}" not in summary:
            #     raise Exception(f"Topology did not set properly.")

            # idx = summary.find(f"{self.client} {self.proxy_cs}") + len(f"{self.client} {self.proxy_cs}") + 50
            # if summary[idx:idx+15] != 'type=persistent':
            #     raise Exception(f"Topology did not set properly.")

            # self.log.info(f"[+] Checking routes for {self.commcell.commserv_name} [+]")
            # summary = self.network_helper.get_network_summary([self.commcell.commserv_name])[self.commcell.commserv_name]
            # if f"{self.commcell.commserv_name} * proxy=" in summary:
            #     raise Exception(f"Topology did not set properly.")
            # if f"{self.commcell.commserv_name} {self.client} proxy={self.proxy_cs}" not in summary:
            #     raise Exception(f"Topology did not set properly.")

            # route = f"{self.commcell.commserv_name} {self.proxy_cs}"
            # idx = summary.find(route) + len(route) + 50
            # if summary[idx:idx+15] != 'type=persistent':
            #     raise Exception(f"Topology did not set properly.")

            self.network_helper.topologies.delete("proxy_topology_59759")
            
            self.log.info("[*] STEP 4 [*]")
            self.commcell.client_groups.add("MultiProxy_CG_59759",
                                            [self.proxy_cs, self.proxy_cl1,
                                             self.proxy_cl1])
            self.commcell.client_groups.add("CS_MA_59759",
                                            [self.ma, self.commcell.commserv_name])

            self.network_helper.proxy_topology(
                "External_CG_59759", "CS_MA_59759",
                "MultiProxy_CG_59759", "proxy_topology_59759_15")

            self.set_absolute_throttle()
                
            time.sleep(10)

            while self.JOB_EXECUTED_TIME < 20:
                self.JOB_STARTED = datetime.now()
                if self.run_backup_job():
                    raise Exception("[+] Job goes to pending state [+]")
                self.JOB_ENDED = datetime.now()
                self.JOB_EXECUTED_TIME = (self.JOB_ENDED - self.JOB_STARTED).seconds / 60
                self.test_data_size *= 1.5
                self.log.info(f"[+] Validation took: {self.JOB_EXECUTED_TIME} minutes [+]")
            self.network_helper.topologies.delete("proxy_topology_59759_15")

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)
            self.status = 'FAILED'

        finally:
            if self.network_helper.topologies.has_network_topology("proxy_topology_59759"):
                self.network_helper.topologies.delete("proxy_topology_59759")
            self.commcell.client_groups.delete('External_CG_59759')
            self.commcell.client_groups.delete('CS_CG_59759')
            self.commcell.client_groups.delete('External_Proxy_CG_59759')
            self.commcell.client_groups.delete('Proxy_CG_59759')
            self.commcell.client_groups.delete('CS_MA_59759')
            self.commcell.client_groups.delete('MultiProxy_CG_59759')
            self.network_helper.entities.cleanup()
            self.delete_storage_policies()

    def run_backup_job(self):
        self.log.info("Triggering backup job")
        job = self.subclient_obj.backup('FULL')
        self.log.info(f"""
            *********************
            job Id : {job.job_id}
            *********************
        """)
        while not job.is_finished:
            
            if str(job.status).lower() == 'pending':
                self.log.info(f"""
                ========================================
                job Id : {job.job_id}
                Job State : {job.status}
                Job Phase : {job.phase}
                Delay Reason : {job.delay_reason}
                Pending Reason : {job.pending_reason} 
                ========================================
                """)
                job.kill()
                return True
        # job.kill()
        return False

    def create_storage_policy_assoc(self, media_agent, client):
        self.storage_pool_name = "storage_pool_59759_" + media_agent + uuid.uuid4().hex[:5]
        self.plan_name = "plan_59759_" + media_agent + uuid.uuid4().hex[:5]
        mount_path = self.network_helper.entities.get_mount_path(media_agent)

        # create storage pool
        self.log.info(f"Creating Storage pool with name {self.storage_pool_name}")
        self.storage_pool.add(self.storage_pool_name, mount_path, media_agent)

        # create plan
        self.plans_helper = PlansHelper(commcell_obj=self.commcell)
        self.log.info(f"Creating base plan with name {self.plan_name}")
        self.plans_helper.create_base_plan(self.plan_name, "Server", self.storage_pool_name)
        self.log.info(f"{self.plan_name} created successfully")

        subclient_inputs = {
            'target':
                {
                    'client': client,
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'storagepolicy': self.plan_name,
                    'backupset': "defaultBackupSet",
                    'force': True
                },
            'subclient':
                {
                    'name': "test_59759_subclient",
                    'client_name': client,
                    'content': None,
                    'level': 1,
                    'size': self.test_data_size,
                    'description': "Automation - Target properties"
                }
        }
        self.network_helper.entities.create(subclient_inputs)
        

    def delete_storage_policies(self):
        """Helper function that deletes the storage policies created
        """
        self.log.info(f"Deleting plan: {self.plan_name} and storage pool {self.storage_pool_name}")
        self.plans_helper.delete_plan(self.plan_name)
        self.storage_pool.delete(self.storage_pool_name)

    def set_absolute_throttle(self):
        self.log.info("Setting absolute throttle between client and mediaagent")
        self.network_helper.set_network_throttle(
            {'clientName': self.tcinputs['networkClientRegion1']},
            remote_clients=[self.tcinputs['networkProxy'],
                            self.tcinputs['networkProxy1'],
                            self.tcinputs['networkProxy2']],
            throttle_rules=[
                {
                    "sendRate": 4096,
                    "sendEnabled": True,
                    "receiveEnabled": True,
                    "recvRate": 4096,
                    "days": '1111111',
                    "isAbsolute": True
                }
            ]
        )
