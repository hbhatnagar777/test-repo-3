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

    Test Case:          --  [Network & Firewall] : Smart topology

    validate_topology() --  Validates the topology in database based on type

"""

from datetime import datetime

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.Network.networkhelper import NetworkHelper
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
                    Two clients NetworkClient1 and NetworkClient2 can be any file system clients
                    Two media agents as MediaAgent1 and MediaAgent2
                    One client should be used as a proxy client

                Various Smart topology configurations are validated as part of the test case

        """
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Smart topology"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
            "NetworkClient1": None,
            "NetworkClient2": None,
            "ProxyClient": None,
            "MediaAgent1": None,
            "MediaAgent2": None
        }

        self.network_helper = None
        self.entities = None
        self.clients_obj = None

        # My CommServe Computer
        self.mnemonic_commserve = "My CommServe Computer"
        self.mnemonic_commserve_ma = "My CommServe Computer and MediaAgents"
        self.mnemonic_ma = "My MediaAgents"

        # Client Groups
        self.clientgrp1 = 'Trusted Client Group1'
        self.clientgrp_dmz = 'Network Gateway/DMZ Group'
        self.test_update_group = "Test Update Group"

        # Subclient Info
        self.test_subclient = "test_54266_subclient"
        self.content_drive = "C:\\"
        self.content_folder = "testData_54266"

        # Topology information
        self.network_topology_name = "Smart Topology 54266 "
        self.network_topology_description = "This is a test for validating Smart topology."

        # Client names
        self.client_1 = None
        self.client_2 = None
        self.proxy_client = None
        self.media_agent_1 = None
        self.media_agent_2 = None
        self.clients_list_dict = []

        # Client grp list
        self.client_grp_list = None
        self.clients_grps_obj = None

        # Client group objects
        self.clientgrp_dmz_obj = None
        self.clientgrp1_obj = None
        self.client_grp_id_map = None

        # Storage policies
        self.sp_ma1 = None
        self.sp_ma2 = None
        self.storage_policies_list = []
        self.disk_libraries = []
        self.ddb_path = None

        self.tc_timestamp = str(int(datetime.timestamp(datetime.now())))

    def setup(self):
        """Setup function of this test case"""

        try:
            self.network_helper = NetworkHelper(self)
            self.entities = self.network_helper.entities
            self.clients_obj = self.commcell.clients

            # Client names
            self.client_1 = self.tcinputs['NetworkClient1']
            self.client_2 = self.tcinputs['NetworkClient2']
            self.proxy_client = self.tcinputs['ProxyClient']
            self.media_agent_1 = self.tcinputs['MediaAgent1']
            self.media_agent_2 = self.tcinputs['MediaAgent2']

            # clients list of dict
            self.clients_list_dict = [{'clientName': self.client_1},
                                      {'clientName': self.client_2},
                                      {'clientName': self.proxy_client},
                                      {'clientName': self.media_agent_1},
                                      {'clientName': self.media_agent_2},
                                      ]

            # DDB Info
            self.ddb_path = 'C:\\DDBPath_54266' + self.tc_timestamp

            self.storage_policies_list = ["storagepolicy_54266_" + self.media_agent_1 + self.client_1,
                                          "storagepolicy_54266_" + self.media_agent_2 + self.client_2]
            #self.delete_storage_policies()

            self.sp_ma1 = self.create_storage_policy_assoc(self.storage_policies_list[0],
                                                           self.media_agent_1,
                                                           self.client_1,
                                                           self.test_subclient,
                                                           self.content_drive,
                                                           self.content_folder,
                                                           ddb_media_agent=self.media_agent_2,
                                                           ddb_path=self.ddb_path)

            self.sp_ma2 = self.create_storage_policy_assoc(self.storage_policies_list[1],
                                                           self.media_agent_2,
                                                           self.client_2,
                                                           self.test_subclient,
                                                           self.content_drive,
                                                           self.content_folder)

            # Client grp list
            self.client_grp_list = [self.clientgrp1, self.clientgrp_dmz, self.test_update_group]
            self.clients_grps_obj = self.commcell.client_groups

            # Create trusted grp 1
            self.clients_grps_obj.add(self.clientgrp1, clients=[self.client_1, self.client_2])
            self.clientgrp1_obj = self.clients_grps_obj.get(self.clientgrp1)

            # Create Network/DMZ grp
            self.clients_grps_obj.add(self.clientgrp_dmz, clients=[self.proxy_client])
            self.clientgrp_dmz_obj = self.clients_grps_obj.get(self.clientgrp_dmz)

            # Get client group id
            self.client_grp_id_map = {}
            for client_grp in [self.clientgrp1, self.clientgrp_dmz]:
                self.client_grp_id_map[client_grp] = self.clients_grps_obj.get(client_grp).clientgroup_id

            #self.network_helper.remove_network_config(self.clients_list_dict)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()

    def run(self):
        """Run function of this test case"""
        self.log.info("Started executing testcase %s", self.id)
        try:

            # Set smart topology
            self.log.info("Smart Topology. Mnemonic used : %s", self.mnemonic_commserve)
            self.network_helper.proxy_topology(self.clientgrp1, self.mnemonic_commserve, self.clientgrp_dmz,
                                               topology_name=self.network_topology_name)

            # Get topology id
            topology_id = self.network_helper.get_network_topology_id(self.network_topology_name)
            self.log.info("Topology id: %s", topology_id)

            self.network_helper.push_topology(self.network_topology_name)

            self.validate_topology(topology_id, '1')

            # Read the FwConfig.txt files & validate the routes populated
            self.network_helper.options.sleep_time(60)
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_1,
            #                                            client2=self.proxy_client, client3=self.commcell.commserv_name,
            #                                            )
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_2,
            #                                            client2=self.proxy_client, client3=self.commcell.commserv_name,
            #                                            )

            # Modify Topology
            self.log.info("Modifying Topology")
            self.clients_grps_obj.add(self.test_update_group, clients=[self.media_agent_1])
            self.network_helper.modify_topology(self.network_topology_name,
                                                [{'group_type': 1, 'group_name': self.test_update_group,
                                                  'is_mnemonic': False},
                                                 {'group_type': 2, 'group_name': self.clientgrp1,
                                                  'is_mnemonic': False},
                                                 {'group_type': 3, 'group_name': self.clientgrp_dmz,
                                                  'is_mnemonic': False}],
                                                topology_type=1,
                                                is_smart_topology=False, topology_description="Updated topology")
            self.network_helper.options.sleep_time(60)
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_1,
            #                                            client2=self.proxy_client, client3=self.media_agent_1,
            #                                            )
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_2,
            #                                            client2=self.proxy_client, client3=self.media_agent_1,
            #                                            )

            self.clients_grps_obj.delete(self.test_update_group)
            self.network_helper.delete_topology(self.network_topology_name)
            #self.network_helper.remove_network_config(self.clients_list_dict)

            # --------------------------------------------------------------------------------------------------------
            # --------------------------------------------------------------------------------------------------------
            # REPEAT FOR MY COMMSERV AND MEDIA AGENT

            # Set smart topology
            self.log.info("Smart Topology. Mnemonic used : %s", self.mnemonic_commserve_ma)
            self.network_helper.proxy_topology(self.clientgrp1, self.mnemonic_commserve_ma, self.clientgrp_dmz,
                                               topology_name=self.network_topology_name)

            # Get topology id
            topology_id = self.network_helper.get_network_topology_id(self.network_topology_name)
            self.log.info("Topology id: %s", topology_id)

            self.validate_topology(topology_id, '1')

            #  Read the FwConfig.txt files & validate the routes populated
            self.network_helper.options.sleep_time(60)
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_1,
            #                                            client2=self.proxy_client, client3=self.media_agent_1,
            #                                            )
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_1,
            #                                            client2=self.proxy_client, client3=self.commcell.commserv_name,
            #                                            )
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_2,
            #                                            client2=self.proxy_client, client3=self.commcell.commserv_name,
            #                                            )
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_2,
            #                                            client2=self.proxy_client, client3=self.media_agent_2,
            #                                            )

            self.network_helper.outgoing_route_settings({'clientGroupName': self.clientgrp1},
                                                        remote_entity=self.clientgrp_dmz,
                                                        streams=4,
                                                        is_client=False,
                                                        connection_protocol=2,
                                                        )

            # Run backup and restore
            # Run backup job
            client_1_obj = self.commcell.clients.get(self.client_1)
            agent_obj = client_1_obj.agents.get('File System')
            backupset_obj = agent_obj.backupsets.get('defaultBackupSet')
            fs_subclient = backupset_obj.subclients.get(self.test_subclient)
            self.log.info("Starting backup job")
            backup_job = fs_subclient.backup("FULL")
            if not backup_job.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: %s", backup_job.delay_reason
                )
            self.log.info("Backup job: %s completed successfully", backup_job.job_id)

            # Run restore job
            self.log.info("Starting Restore job")
            restore_job = fs_subclient.restore_in_place([self.content_drive + self.content_folder])
            if not restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run restore with error: %s", restore_job.delay_reason
                )
            self.log.info("Restore job: %s completed successfully", restore_job.job_id)

            self.network_helper.delete_topology(self.network_topology_name)
            #self.network_helper.remove_network_config(self.clients_list_dict)

            # --------------------------------------------------------------------------------------------------------
            # --------------------------------------------------------------------------------------------------------
            # MY MEDIA AGENT
            self.log.info("Smart Topology. Mnemonic used : %s", self.mnemonic_ma)
            self.network_helper.proxy_topology(self.clientgrp1, self.mnemonic_ma, self.clientgrp_dmz,
                                               topology_name=self.network_topology_name)

            # Get topology id
            topology_id = self.network_helper.get_network_topology_id(self.network_topology_name)

            self.log.info("Topology id: %s", topology_id)

            self.validate_topology(topology_id, '1')

            # Read the FwConfig.txt files & validate the routes populated
            self.network_helper.options.sleep_time(60)
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_1,
            #                                            client2=self.proxy_client, client3=self.media_agent_1)
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_2,
            #                                            client2=self.proxy_client, client3=self.media_agent_2,
            #                                            )

            self.network_helper.delete_topology(self.network_topology_name)
            #self.network_helper.remove_network_config(self.clients_list_dict)

            # --------------------------------------------------------------------------------------------------------
            # --------------------------------------------------------------------------------------------------------
            # Try the same if smart group(such as My Commserve/My MediaAgent) is in Trusted client Group1

            # Set smart topology
            self.log.info("Smart Topology. Mnemonic used : %s", self.mnemonic_commserve)
            self.network_helper.proxy_topology(self.mnemonic_commserve, self.clientgrp1, self.clientgrp_dmz,
                                               topology_name=self.network_topology_name)

            # Get topology id
            topology_id = self.network_helper.get_network_topology_id(self.network_topology_name)
            self.log.info("Topology id: %s", topology_id)

            self.validate_topology(topology_id, '1')

            # Read the FwConfig.txt files & validate the routes populated
            self.network_helper.options.sleep_time(60)
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_1,
            #                                            client2=self.proxy_client, client3=self.commcell.commserv_name,
            #                                            )
            # self.network_helper.validate_fwconfig_file(topology_type=1, client1=self.client_2,
            #                                            client2=self.proxy_client, client3=self.commcell.commserv_name,
            #                                            )

            self.network_helper.delete_topology(self.network_topology_name)
            #self.network_helper.remove_network_config(self.clients_list_dict)

            # --------------------------------------------------------------------------------------------------------
            # --------------------------------------------------------------------------------------------------------
            # Verify the routes are One-way and Two-way with smart groups in one of the groups.

            # ONE WAY TOPOLOGY
            self.log.info("One way topology. Mnemonic used : %s", self.mnemonic_commserve)
            self.network_helper.one_way_topology(self.clientgrp1, self.mnemonic_commserve,
                                                 topology_name=self.network_topology_name)

            # Get topology id
            topology_id = self.network_helper.get_network_topology_id(self.network_topology_name)

            self.log.info("Topology id: %s", topology_id)

            self.validate_topology(topology_id, topology_type='2')

            # Read the FwConfig.txt files & validate the routes populated
            # self.network_helper.options.sleep_time(60)
            # self.network_helper.validate_fwconfig_file(topology_type=2, client1=self.client_1,
            #                                            client2=self.commcell.commserv_name,
            #                                            )
            # self.network_helper.validate_fwconfig_file(topology_type=2, client1=self.client_2,
            #                                            client2=self.commcell.commserv_name,
            #                                            )

            self.network_helper.delete_topology(self.network_topology_name)
            #self.network_helper.remove_network_config(self.clients_list_dict)

            # TWO WAY
            self.log.info("Two way topology. Mnemonic used : %s", self.mnemonic_commserve)
            self.network_helper.two_way_topology(self.clientgrp1, self.mnemonic_commserve,
                                                 topology_name=self.network_topology_name)

            # Get topology id
            topology_id = self.network_helper.get_network_topology_id(self.network_topology_name)

            self.log.info("Topology id: %s", topology_id)

            self.validate_topology(topology_id, topology_type='3')

            # Read the FwConfig.txt files & validate the routes populated
            # self.network_helper.options.sleep_time(60)
            # self.network_helper.validate_fwconfig_file(topology_type=3, client1=self.client_1,
            #                                             client2=self.commcell.commserv_name,
            #                                            )
            # self.network_helper.validate_fwconfig_file(topology_type=3, client1=self.client_2,
            #                                            client2=self.commcell.commserv_name,
            #                                            )

            self.network_helper.delete_topology(self.network_topology_name)
            #self.network_helper.remove_network_config(self.clients_list_dict)

            # # --------------------------------------------------------------------------------------------------------
            # # --------------------------------------------------------------------------------------------------------
            # DDB on different MA

            self.log.info("Verifying network summary when DDB is on different MA")
            self.network_helper.one_way_topology(self.clientgrp1, self.mnemonic_ma, self.network_topology_name)
            network_summary = self.network_helper.get_network_summary([self.client_1])
            if "{0} {1}".format(self.client_1, self.media_agent_2) not in network_summary[self.client_1]:
                raise Exception("Incorrect smart topology network summary for DDB configuration")

            self.network_helper.delete_topology(self.network_topology_name)
            self.network_helper.entities.cleanup()
            storage_policies_obj = self.commcell.storage_policies
            if storage_policies_obj.has_policy(self.sp_ma2):
                storage_policies_obj.delete(self.sp_ma2)
            #self.network_helper.remove_network_config(self.clients_list_dict)

            # Remote cache configuration
            self.log.info("Verifying network summary when Remote Cache is configured")
            software_cache_obj = self.commcell.get_remote_cache(self.media_agent_2)
            software_cache_obj.configure_remotecache("C:\\Remote_cache_54266" + self.tc_timestamp)
            software_cache_obj.assoc_entity_to_remote_cache(self.client_1)
            self.network_helper.one_way_topology(self.clientgrp1, self.mnemonic_ma, self.network_topology_name)
            network_summary = self.network_helper.get_network_summary([self.client_1])
            if "{0} {1} ".format(self.client_1, self.media_agent_2) not in network_summary[self.client_1]:
                raise Exception("Incorrect smart topology network summary for Remote Cache")
            self.network_helper.delete_topology(self.network_topology_name)

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.tear_down()
            self.network_helper.delete_topology(self.network_topology_name)
            self.network_helper.cleanup_network()
            self.network_helper.entities.cleanup()
            #self.delete_storage_policies()


    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell.refresh()
        if self.network_helper is not None:
            if self.network_helper.topologies.has_network_topology(self.network_topology_name):
                self.log.info('Deleting topology : %s', self.network_topology_name)
                self.network_helper.delete_topology(self.network_topology_name)

            #self.network_helper.remove_network_config(self.clients_list_dict)

        self.log.info("Deleting client groups")
        for client_group in self.client_grp_list:
            if self.clients_grps_obj.has_clientgroup(client_group):
                self.clients_grps_obj.delete(client_group)

        # Delete DDB Subclient
        media_agent_2_obj = self.commcell.clients.get(self.media_agent_2)
        media_agent_2_obj = media_agent_2_obj.agents.get('File System')
        backupset_obj = media_agent_2_obj.backupsets.get('defaultBackupSet')
        if backupset_obj.subclients.has_subclient('DDBBackup'):
            self.log.info('Deleting subclient on {0} : DDBBackup'.format(self.media_agent_2))
            backupset_obj.subclients.delete('DDBBackup')

        #self.delete_storage_policies()

        # for disk_lib in self.disk_libraries:
        #     if self.commcell.disk_libraries.has_library(disk_lib):
        #         self.log.info('Deleting disk library : %s', disk_lib)
        #         self.commcell.disk_libraries.delete(disk_lib)

        media_agent_2_machine = Machine(self.media_agent_2, self.commcell)
        if media_agent_2_machine.check_directory_exists(self.ddb_path):
            media_agent_2_machine.remove_directory(self.ddb_path)

    # Helper functions for the test case

    def create_storage_policy_assoc(self,
                                    storage_policy_name,
                                    media_agent,
                                    client,
                                    subclient_name,
                                    content_drive,
                                    content_folder,
                                    ddb_path=None,
                                    ddb_media_agent=None,
                                    incremental_sp=None):
        # Create disklibrary
        media_agent_helper = MMHelper(self)
        disk_library_name = "disklibrary_test_" + media_agent + client
        media_agent_helper.configure_disk_library(disk_library_name,
                                                  media_agent,
                                                  self.entities.get_mount_path(media_agent))
        self.log.info("Created disk library using media agent %s", media_agent)
        self.disk_libraries.append(disk_library_name)

        # create storage policy
        storage_policies_obj = self.commcell.storage_policies
        if storage_policies_obj.has_policy(storage_policy_name):
            self.log.info("Storage policy is already present ignore")
        else:
            storage_policies_obj.add(storage_policy_name,
                                 disk_library_name,
                                 media_agent,
                                 dedup_path=ddb_path,
                                 incremental_sp=incremental_sp,
                                 dedup_media_agent=ddb_media_agent)

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
                    'data_path': content_drive + content_folder,
                    'level': 1,
                    'size': 1000,
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
                self.log.info("Deleting storage policy  %s", sp)
                storage_policies_obj.delete(sp)
        storage_policies_obj.refresh()

    def validate_topology(self, topology_id, topology_type):
        """ Helper function to validate the topology based on type

        Args:
            topology_id:    Topology id
            topology_type:  Type of topology
                            '1' - proxy topology
                            '2' - one way topology
                            '3' - two way topology

        Raises:
            Exception if validation fails

        """
        # RUN DATABASE QUERIES
        # Validate Name, Description &Topology type in  App_FirewallTopology table
        columns_dict = {'topologyName': 0, 'description': 1, 'topologyType': 2}
        col1, res = self.network_helper.options.exec_commserv_query(
            'select topologyName, description, topologyType from APP_FirewallTopology where topologyId={0}'.format(
                topology_id))

        if (res[0][columns_dict['topologyName']] != self.network_topology_name
                or
                res[0][columns_dict['topologyType']] != topology_type):
            raise Exception('DB data incorrect')

        if topology_type == '1':
            # Validate tunnel port & isDMZ of the clients in client groups
            # Check if lockdown= 0 for clients in DMZ group
            columns_dict = {'clientGroupId': 0, 'isDMZ': 1, 'tunnelconnectionPort': 2, 'lockDown': 3}
            col1, res = self.network_helper.options.exec_commserv_query(
                """SELECT AFO.clientGroupId,AFO.isDMZ,AFO.tunnelconnectionPort,AFO.lockDown
                    FROM App_FirewallOptions AFO
                    INNER JOIN APP_FirewallTopologyAssoc AFTA
                    ON AFO.clientGroupId = AFTA.groupId
                    WHERE AFTA.topologyId = {0}""".format(topology_id))
            for row in res:
                if row[columns_dict['clientGroupId']] == str(
                        self.client_grp_id_map[self.clientgrp_dmz]) and row[columns_dict['isDMZ']] != '1':
                    raise Exception('DMZ group expected to be 1 for DMZ group')
                if row[columns_dict['tunnelconnectionPort']] != '8403':
                    raise Exception('Incorrect tunnel port in db')
                if row[columns_dict['lockDown']] != '0':
                    raise Exception('Incorrect lockDown in db')

        # Validate the firewall configuration for the client groups in App_Firewall Table
        # Restriction type = 0 (Restricted)
        # Restriction type = 1 (Blocked)
        columns_dict = {'clientGroupId': 0, 'forClientGroupId': 1, 'restrictionType': 2}
        col1, res = self.network_helper.options.exec_commserv_query(
            """select af.clientGroupId,af.forClientGroupId,af.restrictionType
                from APP_Firewall af
                inner join App_FirewallRoutesTopoAssoc afta
                on af.id=afta.routeId
                where afta.topologyId={0} order by af.restrictionType""".format(topology_id))

        if topology_type == '1':
            for row in res:
                if row[columns_dict['restrictionType']] == '0' and row[columns_dict['clientGroupId']] != str(
                        self.client_grp_id_map[self.clientgrp_dmz]):
                    raise Exception('Incorrect Restriction for NetworkDMZ')
                elif row[columns_dict['restrictionType']] == '1' and row[columns_dict['clientGroupId']] == str(
                        self.client_grp_id_map[self.clientgrp_dmz]):
                    raise Exception('Incorrect Restriction for NetworkDMZ')
        elif topology_type == '2':
            for row in res:
                if row[columns_dict['restrictionType']] == '0' and row[columns_dict['clientGroupId']] != "-1":
                    raise Exception('Incorrect Restriction for My Commserve Computer')
                elif row[columns_dict['restrictionType']] == '1' and row[columns_dict['clientGroupId']] != str(
                        self.client_grp_id_map[self.clientgrp1]):
                    raise Exception('Incorrect Restriction for clientgrp 1')
        else:
            for row in res:
                if row[columns_dict['restrictionType']] == '1':
                    raise Exception('Incorrect Restriction in topology')
