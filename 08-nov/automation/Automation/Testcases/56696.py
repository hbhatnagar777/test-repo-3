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
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case

    tear_down()         --  tear down function of this test case

    Test Case:          --  [Network & Firewall] : SERVER_NETWORK_Firewall_ Network Throttle_DIPS_multistreams

"""

import uuid

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from Server.Scheduler import schedulerhelper
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)   -   name of this test case

                applicable_os       (str)   —   applicable os for this test case
                                                            Ex: self.os_list.WINDOWS

                product             (str)   —   applicable product for this test case
                                                                 Ex: self.products_list.FILESYSTEM

                show_to_user        (bool)  —   test case flag to determine if the test case is
                                                             to be shown to user or not

                tcinputs            (dict)  -   test case inputs with input name as dict key
                                                    and value as input type

            Instructions:
                Inputs:
                    NetworkClient as any client in commcell
                    NetworkMediaAgent as any client in commcell

                Various Smart topology configurations are validated as part of the test case

        """
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : SERVER_NETWORK_Firewall_ Network Throttle_DIPS_multistreams"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkMediaAgent": None,
        }

        self.network_helper = None
        self.entities = None
        self.clients_obj = None
        self._schedule_creator = None
        self.client_machine_obj = None
        self.new_data_count = 0

        # Subclient Info
        self.test_subclient = "test_56696_subclient"
        self.content_drive = "C:\\"
        self.content_folder = "testdata_56696"

        # Client names
        self.client = None
        self.media_agent = None
        self.clients_list_dict = []

        # Storage policies
        self.sp_ma1 = None
        self.storage_policies_list = []

    def setup(self):
        """Setup function of this test case"""

        try:
            self.network_helper = NetworkHelper(self)
            self.entities = self.network_helper.entities
            self.clients_obj = self.commcell.clients
            self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self.commcell)

            # Client names
            self.client = self.tcinputs['NetworkClient']
            self.media_agent = self.tcinputs['NetworkMediaAgent']

            # clients list of dict
            self.clients_list_dict = [{'clientName': self.client},
                                      {'clientName': self.media_agent},
                                      ]

            self.sp_ma1 = self.create_storage_policy_assoc(self.media_agent, self.client, self.test_subclient)
            self.storage_policies_list.append(self.sp_ma1)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()

    def run(self):
        """Run function of this test case"""
        self.log.info("Started executing testcase : %s", self.id)
        try:

            client_1_obj = self.commcell.clients.get(self.client)
            agent_obj = client_1_obj.agents.get('File System')
            backupset_obj = agent_obj.backupsets.get('defaultBackupSet')
            subclient_obj = backupset_obj.subclients.get(self.test_subclient)

            self.client_machine_obj = Machine(self.client, self.commcell)
            client_ip = self.client_machine_obj.ip_address
            ma_machine_obj = Machine(self.media_agent, self.commcell)
            ma_ip = ma_machine_obj.ip_address

            # AUTOMATIC SCHEDULE
            # Create Automatic Schedule
            self.log.info('Creating schedule if it doesnt exists')
            sch_obj = self._schedule_creator.create_schedule(
                'subclient_backup',
                schedule_pattern={
                    'freq_type': 'automatic',
                    'min_interval_hours': 0,
                    'min_interval_minutes': 2
                },
                subclient=subclient_obj,
                backup_type="Incremental",
                wait=False)
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)

            # CASE 1 - absolute/Relative Throttling , data interface pairs , multi-streaming
            # SETTING DIPS
            dips_list = [({'client': self.client, 'srcip': client_ip},
                          {'client': self.media_agent, 'destip': ma_ip})]
            self.network_helper.add_dips(dips_list)

            # Set Relative throttling
            self.network_helper.set_network_throttle({'clientName': self.client},
                                                     remote_clients=[self.media_agent],
                                                     throttle_rules=[{"sendRate": 102400,
                                                                      "sendEnabled": True,
                                                                      "receiveEnabled": True,
                                                                      "recvRate": 102400,
                                                                      "days": '1111111',
                                                                      "isAbsolute": False,
                                                                      "sendRatePercent": 40,
                                                                      "recvRatePercent": 40}])

            # Set multi-streaming (httpsa)
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=2,
                                                        )

            # BACKUP JOB
            self.log.info("validating if backup triggered for subclient")

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1
            # Remove network throttle
            self.network_helper.remove_network_throttle([{'clientName': self.client}, {'clientName': self.media_agent}])

            # Set Absolute throttling
            self.network_helper.set_network_throttle({'clientName': self.client},
                                                     remote_clients=[self.media_agent],
                                                     throttle_rules=[{"sendRate": 102400,
                                                                      "sendEnabled": True,
                                                                      "receiveEnabled": True,
                                                                      "recvRate": 102400,
                                                                      "days": '1111111',
                                                                      "isAbsolute": True}])

            # Set multi-streaming (https)
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=1,
                                                        )

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1

            # Remove network throttle
            self.network_helper.remove_network_throttle([{'clientName': self.client}, {'clientName': self.media_agent}])

            # delete dips
            self.network_helper.delete_dips(dips_list)

            ###############################################
            # CASE - RELATIVE THROTTLING , automatic schedule, firewall( one way , two way, proxy ),multistreaming

            # Set Relative throttling
            self.network_helper.set_network_throttle({'clientName': self.client},
                                                     remote_clients=[self.media_agent],
                                                     throttle_rules=[{"sendRate": 102400,
                                                                      "sendEnabled": True,
                                                                      "receiveEnabled": True,
                                                                      "recvRate": 102400,
                                                                      "days": '1111111',
                                                                      "isAbsolute": False,
                                                                      "sendRatePercent": 40,
                                                                      "recvRatePercent": 40}])

            # one way firewall (client to cs)
            self.network_helper.set_one_way({'clientName': self.client},
                                            {'clientName': self.commcell.commserv_name})

            # Set multi-streaming
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=0,
                                                        )

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1

            self.network_helper.remove_network_config([{'clientName': self.commcell.commserv_name},
                                                       {'clientName': self.client}])

            # one way firewall (cs to client )
            self.network_helper.set_one_way({'clientName': self.commcell.commserv_name},
                                            {'clientName': self.client})

            # Set multi-streaming
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=1,
                                                        )

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1

            self.network_helper.remove_network_config([{'clientName': self.commcell.commserv_name},
                                                       {'clientName': self.client}])

            # one way firewall (cs to client )
            self.network_helper.set_two_way({'clientName': self.commcell.commserv_name},
                                            {'clientName': self.client})

            # Set multi-streaming
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=2,
                                                        )

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1

            self.network_helper.remove_network_config([{'clientName': self.commcell.commserv_name},
                                                       {'clientName': self.client}])

            # proxy firewall (cs, client)
            self.network_helper.set_via_proxy({'entity': self.client, 'isClient': True},
                                              {'entity': self.media_agent, 'isClient': True},
                                              {'entity': self.commcell.commserv_name, 'isClient': True},
                                              )

            # Set multi-streaming
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=3,
                                                        )

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1

            self.network_helper.remove_network_config([{'clientName': self.commcell.commserv_name},
                                                       {'clientName': self.client}])

            # Remove network throttle
            self.network_helper.remove_network_throttle([{'clientName': self.client}, {'clientName': self.media_agent}])

            ###############################################
            # CASE - ABSOLUTE , automatic schedule, firewall( one way , two way, proxy ),multistreaming

            # Set Absolute throttling
            self.network_helper.set_network_throttle({'clientName': self.client},
                                                     remote_clients=[self.media_agent],
                                                     throttle_rules=[{"sendRate": 102400,
                                                                      "sendEnabled": True,
                                                                      "receiveEnabled": True,
                                                                      "recvRate": 102400,
                                                                      "days": '1111111',
                                                                      "isAbsolute": True}])

            # one way firewall (client to cs)
            self.network_helper.set_one_way({'clientName': self.client},
                                            {'clientName': self.commcell.commserv_name})

            # Set multi-streaming
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=0,
                                                        )

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1

            self.network_helper.remove_network_config([{'clientName': self.commcell.commserv_name},
                                                       {'clientName': self.client}])

            # one way firewall (cs to client )
            self.network_helper.set_one_way({'clientName': self.commcell.commserv_name},
                                            {'clientName': self.client})

            # Set multi-streaming
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=1,
                                                        )

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1

            self.network_helper.remove_network_config([{'clientName': self.commcell.commserv_name},
                                                       {'clientName': self.client}])

            # one way firewall (cs to client )
            self.network_helper.set_two_way({'clientName': self.commcell.commserv_name},
                                            {'clientName': self.client})

            # Set multi-streaming
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=2,
                                                        )

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1

            self.network_helper.remove_network_config([{'clientName': self.commcell.commserv_name},
                                                       {'clientName': self.client}])

            # proxy firewall (cs, client)
            self.network_helper.set_via_proxy({'entity': self.client, 'isClient': True},
                                              {'entity': self.media_agent, 'isClient': True},
                                              {'entity': self.commcell.commserv_name, 'isClient': True},
                                              )

            # Set multi-streaming
            self.network_helper.outgoing_route_settings({'clientName': self.client},
                                                        remote_entity=self.media_agent,
                                                        streams=4,
                                                        is_client=True,
                                                        connection_protocol=3,
                                                        )

            # Add content for automatic trigger
            self.log.info("Generating new test data for subclient as : %s",
                          self.content_drive + "addcontent" + str(self.new_data_count))
            self.client_machine_obj.generate_test_data(self.content_drive + "addcontent" + str(self.new_data_count))
            subclient_obj.content = [self.content_drive + "addcontent" + str(self.new_data_count)]
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            self.new_data_count += 1

            self.network_helper.remove_network_config([{'clientName': self.commcell.commserv_name},
                                                       {'clientName': self.client}])

            #self.client_machine_obj.remove_directory(self.content_drive + self.content_folder)
            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""

        self.log.info("Deleting generated test data")
        for i in range(self.new_data_count):
            self.client_machine_obj.remove_directory(self.content_drive + "addcontent" + str(i))

        if self.network_helper is not None:
            self._schedule_creator.cleanup_schedules()
            self.network_helper.entities.cleanup()
            self.network_helper.remove_network_config(self.clients_list_dict)
            self.delete_storage_policies()

    # Helper functions for the test case
    def create_storage_policy_assoc(self,
                                    media_agent,
                                    client,
                                    subclient_name,
                                    ):
        # Create disklibrary
        media_agent_helper = MMHelper(self)
        disk_library_name = "disklibrary_test_" + media_agent + client + uuid.uuid4().hex[:5]
        media_agent_helper.configure_disk_library(disk_library_name,
                                                  media_agent,
                                                  self.entities.get_mount_path(media_agent))
        self.log.info("Created disk library using media agent %s", media_agent)

        # create storage policy
        storage_policy_name = "storagepolicy_56696_" + media_agent + client + uuid.uuid4().hex[:5]
        storage_policies_obj = self.commcell.storage_policies

        storage_policies_obj.add(storage_policy_name,
                                 disk_library_name,
                                 media_agent,
                                 )

        self.log.info(" Creating storage policy using library %s", "disklibrary_test_" + media_agent)

        storage_policies_obj.refresh()

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
                    'data_path': None,
                    'level': 1,
                    'size': 100,
                    'description': "Automation - Target properties",
                    'subclient_type': None,
                }
        }
        self.entities.create(subclient_inputs)
        return storage_policy_name

    def delete_storage_policies(self):
        """Helper function that deletes the storage policies created
        """
        storage_policies_obj = self.commcell.storage_policies
        for sp in self.storage_policies_list:
            if storage_policies_obj.has_policy(sp):
                storage_policies_obj.delete(sp)
