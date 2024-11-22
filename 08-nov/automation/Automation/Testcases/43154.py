# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case


"""
import uuid
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from Server.Scheduler import schedulerhelper
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """[Network & Firewall] : SERVER_NETWORK_Firewall_ Network Throttle - General"""

    def __init__(self):
        """Initializes tset case class object"""
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : SERVER_NETWORK_Firewall_ Network Throttle - General"
        self.applicable_os = self.os_list.WINDOWS
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkMediaAgent": None,
        }
        self.network_helper = None
        self.entities = None
        self.clients_obj = None
        self._schedule_creator = None

        # Subclient Info
        self.test_subclient = "test_43154_subclient"

        # Client names
        self.client = None
        self.media_agent = None

        # Storage policies
        self.sp_ma1 = None

        # Objects
        self.client_obj = None
        self.agent_obj = None
        self.backupset_obj = None
        self.subclient_obj = None
        self.scheduler_helper_obj = None

        self.media_agent_machine_obj = None
        self.client_machine_obj = None

        # Protocols
        self.proto = ['http', 'https', 'httpsa', 'raw']

    def setup(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.network_helper = NetworkHelper(self)
            self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self.commcell)

            # Client names
            self.client = self.tcinputs['NetworkClient']
            self.media_agent = self.tcinputs['NetworkMediaAgent']

            self.client_machine_obj = Machine(self.client, self.commcell)
            self.media_agent_machine_obj = Machine(self.media_agent, self.commcell)

            # Creating Groups
            if self.commcell.client_groups.has_clientgroup("CG_43154_CL"):
                self.commcell.client_groups.delete("CG_43154_CL")
            self.commcell.client_groups.add("CG_43154_CL", [self.client])

            if self.commcell.client_groups.has_clientgroup("CG_43154_MA"):
                self.commcell.client_groups.delete("CG_43154_MA")
            self.commcell.client_groups.add("CG_43154_MA", [self.media_agent])

            # Storage policy
            self.sp_ma1 = self.create_storage_policy_assoc(
                self.media_agent,
                self.client,
                self.test_subclient
            )

            # Objects
            self.client_obj = self.commcell.clients.get(self.client)
            self.agent_obj = self.client_obj.agents.get('File System')
            self.backupset_obj = self.agent_obj.backupsets.get('defaultBackupSet')
            self.subclient_obj = self.backupset_obj.subclients.get(self.test_subclient)


        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)
            self.status = constants.FAILED

    def run(self):
        """Main function for test case execution"""
        try:
            # To check absolute throttle with low range
            self.absolute_throttle(3096, 3096, 24)
            # To check absolute throttle with high range
            self.absolute_throttle(9999999, 9999999, 4500)
            # To check relative throttle with low range
            self.relative_throttle(3096, 3096)
            # To check relative throttle with high range
            self.relative_throttle(9999999, 9999999)
            # To check all the combinations
            self.rel_throt_sch_dip_multistr_proto()
            self.abs_throt_sch_firewall_combi()
            self.log.info('[--> [SUCCESSFULL] <--]')
        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)
            self.status = constants.FAILED
        finally:
            if self._schedule_creator:
                self._schedule_creator.cleanup_schedules()
            if self.network_helper:
                self.network_helper.cleanup_network()
            self.network_helper.entities.cleanup()
        pass

    def absolute_throttle(self, send_rate, recv_rate, gbph):
        self.set_absolute_throttle(send_rate, recv_rate)
        network_throughput = self.backup_job()
        self.log.info(f"Set limit to (GBPH): {gbph}, Max network throughput our ssytem give(GBPH): {network_throughput}")
        if not (network_throughput < gbph):
            raise Exception("Average network throughput is greater than expected")
        self.network_helper.cleanup_network()

    def relative_throttle(self, send_rate, recv_rate):
        self.set_relative_throttle(send_rate, recv_rate)
        self.backup_job()
        self.network_helper.cleanup_network()

    def rel_throt_sch_dip_multistr_proto(self):
        self.create_automatic_schedule()

        # Setting DIPS
        self.log.info("Setting DIP between client and media agent.")
        dips_list = [
            (
                {'client': self.client, 'srcip': self.client_machine_obj.ip_address},
                {'client': self.media_agent, 'destip': self.media_agent_machine_obj.ip_address}
            )
        ]
        self.network_helper.add_dips(dips_list)
        self.network_helper.push_config_client([self.client])

        # Setting relative throttle
        self.relative_throttle(9999999, 9999999)

        # Setting Multistreaming with all the 4 protocols
        self.multistreaming_schedule_check()
        pass

    def abs_throt_sch_firewall_combi(self):
        self.absolute_throttle(9999999, 9999999, 4500)
        self.multistreaming_schedule_check()
        pass

    def multistreaming_schedule_check(self):
        for i in range(4):
            self.network_helper.delete_topology("NT_43154")
            self.network_helper.one_way_topology(
                "CG_43154_CL", "CG_43154_MA", "NT_43154", 
                number_of_streams=4, connection_protocol=i
            )
            
            self.network_helper.push_topology("NT_43154")
            # This same logic shuould be changed according to Groupbased rules. 
            # network_summary = self.client_obj.get_network_summary()
            # if network_summary.find("streams=4") == -1:
            #     raise Exception('Multistreaming did not set.')

            # if network_summary.find("proto=" + self.proto[i]) == -1:
            #     raise Exception('Protocol did not set to: ' + self.proto[i])

            job_executed = self.scheduler_helper_obj.automatic_schedule_wait(newcontent=True)
            if not job_executed:
                raise Exception("Automatic job did not trigger in scheduled time")
            
            self.network_helper.delete_topology("NT_43154")

        self.network_helper.remove_network_throttle(
            [
                {'clientName': self.client},
                {'clientName': self.media_agent}
            ]
        )

    def set_absolute_throttle(self, send_rate, recv_rate):
        self.log.info("Setting absolute throttle between client and mediaagent")
        self.network_helper.set_network_throttle(
            {'clientName': self.tcinputs['NetworkClient']},
            remote_clients=[self.tcinputs['NetworkMediaAgent']],
            throttle_rules=[
                {
                    "sendRate": send_rate,
                    "sendEnabled": True,
                    "receiveEnabled": True,
                    "recvRate": recv_rate,
                    "days": '1111111',
                    "isAbsolute": True
                }
            ]
        )

        self.log.info("Pushing network config")
        self.network_helper.push_config_client(
            [
                self.tcinputs['NetworkClient'],
                self.tcinputs['NetworkMediaAgent']
            ]
        )

    def set_relative_throttle(self, send_rate, recv_rate):
        self.log.info("Setting relative throttle between client and mediaagent")
        self.network_helper.set_network_throttle(
            {'clientName': self.tcinputs['NetworkClient']},
            remote_clients=[self.tcinputs['NetworkMediaAgent']],
            throttle_rules=[
                {
                    "sendRate": send_rate,
                    "sendEnabled": True,
                    "receiveEnabled": True,
                    "recvRate": recv_rate,
                    "days": '1111111',
                    "isAbsolute": False,
                    "sendRatePercent": 40,
                    "recvRatePercent": 40
                }
            ]
        )

        self.network_helper.push_config_client(
            [
                self.tcinputs['NetworkClient'],
                self.tcinputs['NetworkMediaAgent']
            ]
        )

    def create_automatic_schedule(self):
        self.log.info("Setting automatic schedule for " + self.client)
        schedule_obj = self._schedule_creator.create_schedule(
            'subclient_backup',
            schedule_pattern={
                'freq_type': 'automatic',
                'min_interval_hours': 0,
                'min_interval_minutes': 1
            },
            subclient=self.subclient_obj,
            backup_type="Incremental",
            wait=True,
            wait_time=120
        )
        self.scheduler_helper_obj = schedulerhelper.SchedulerHelper(schedule_obj, self.commcell)

    def create_storage_policy_assoc(self, media_agent, client, subclient_name):

        disk_library_name = "disklibrary_test_" + media_agent + client + uuid.uuid4().hex[:5]
        storage_policy_name = "storagepolicy_43154_" + media_agent + client + uuid.uuid4().hex[:5]
        self.delete_storage_policies(storage_policy_name)
        subclient_inputs = {
            'target':
                {
                    'client': client,
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'storagepolicy': storage_policy_name,
                    'backupset': "defaultBackupSet",
                    'force': True
                },
            'subclient':
                {
                    'name': subclient_name,
                    'client_name': client,
                    'content': None,
                    'level': 1,
                    'size': 5000,
                    'description': "Automation - Target properties"
                },
            'disklibrary':
                {
                    'name': disk_library_name,
                    'mediaagent': media_agent
                },
            "storagepolicy":
                {
                    'name': storage_policy_name,
                    'mediaagent': media_agent,
                    'library': disk_library_name
                }
        }
        self.network_helper.entities.create(subclient_inputs)
        return storage_policy_name

    def delete_storage_policies(self, name):
        """Helper function that deletes the storage policies created
        """
        storage_policies_obj = self.commcell.storage_policies
        self.log.info("Deleting " + name + " if exists")
        if storage_policies_obj.has_policy(name):
            storage_policies_obj.delete(name)

    def backup_job(self):
        self.log.info("Triggering backup job")
        job = self.subclient_obj.backup('FULL')
        while str(job.phase).lower() == 'SCAN'.lower():
            pass
        resultset, max_result = 0.0, 0.0
        self.log.info("Scan phase completed")
        self.log.info("Job phase: " + str(job.phase))
        while job.phase.lower() == 'BACKUP'.lower():
            self.csdb.execute("select networkAverageThroughput from JMBkpJobInfo")
            resultset = self.csdb.fetch_one_row()
            self.log.info("Current network throughput in(GBPH) value is : " + str(resultset[0]))
            if resultset[0] == '0.0' or resultset[0] == '':
                resultset = [0]
            else:
                resultset = list(map(float, resultset))
            if max_result < resultset[0]:
                max_result = resultset[0]
        job.wait_for_completion()

        self.log.info("Triggering restrore job")
        restore_job = self.subclient_obj.restore_out_of_place(
            client=self.client,
            destination_path="C:\\restore",
            paths=["C:\\"]
        )
        restore_job.wait_for_completion()
        return max_result
