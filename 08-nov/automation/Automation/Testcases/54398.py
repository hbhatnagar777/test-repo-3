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
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case

    Test Case:
            [Network & Firewall] : Verify the behavior of outgoing network option - "Force all data into tunnel"

    Instructions:
            Inputs:
                Source client - Any client
                Destination client - Media Agent

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.clientgroup import ClientGroups
from Server.Network.networkhelper import NetworkHelper


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
                features            (str)   —   qcconstants feature_list item
                                                             Ex: self.features_list.DATAPROTECTION
                show_to_user       (bool)   —   test case flag to determine if the test case is
                                                             to be shown to user or not
                Accept:
                                    True    –   test case will be shown to user from commcell gui
                                    False   –   test case will not be shown to user
                default: False

                tcinputs            (dict)  -   test case inputs with input name as dict key
                                                    and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Verify the behavior of outgoing network option - Force all data into tunnel"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
            "source_client": None,
            "destination_client": None
        }

        self.network_helper = None
        self.client_grp_map = None

        self.clientgrp_a = 'clientgrpA_54398'
        self.clientgrp_b = 'clientgrpB_54398'

        self.test_subclient = "test_subclient_54398"

        self.start_port = 1023
        self.end_port = 1025

        self.network_topology_name = "Test_topology_54398"

    def setup(self):
        """Setup function of this test case"""
        try:
            self.network_helper = NetworkHelper(self)

            self.clients_obj = self.commcell.clients
            self.entities = self.network_helper.entities

            # Client names
            self.client_a = self.tcinputs['source_client']
            self.client_b = self.tcinputs['destination_client']

            # Create Client groups
            self.client_names_list = [self.client_a, self.client_b]

            # Client grp list
            self.client_grp_list = [self.clientgrp_a, self.clientgrp_b]
            self.clients_grps_obj = self.commcell.client_groups
            for client_grp, client_name in zip(self.client_grp_list, self.client_names_list):
                self.log.info('Creating client group: {0} with client: {1}'.format(client_grp, client_name))
                self.clients_grps_obj.add(client_grp, clients=[client_name])

            self.network_helper.remove_network_config([{'clientName': self.client_a},
                                                       {'clientName': self.client_b},
                                                       ])

            # Create disklibrary
            disklibrary_inputs = {
                'disklibrary':
                    {
                        'name': "disklibrary_test_" + self.client_b,
                        'mediaagent': self.client_b,
                        'mount_path': self.entities.get_mount_path(self.client_b),
                        'username': '',
                        'password': '',
                        'cleanup_mount_path': True,
                        'force': False
                    }
            }
            disklibrary_props = self.entities.create(disklibrary_inputs)

            self.log.info("Creating disk library using media agent {0}".format(self.client_b))

            # create storage policy
            storagepolicy_inputs = {
                'target':
                    {
                        'library': "disklibrary_test_" + self.client_b,
                        'mediaagent': self.client_b,
                        'force': False
                    },
                'storagepolicy':
                    {
                        'name': "storagepolicy_54398_" + self.client_b,
                        'dedup_path': None,
                        'incremental_sp': None,
                        'retention_period': 3,
                    },
            }
            self.log.info(" Creating storage policy using library {0}".
                          format("disklibrary_test_" + self.client_b))
            self.entities.create(storagepolicy_inputs)

            # create subclient
            subclient_inputs = {
                'target':
                    {
                        'client': self.client_a,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'storagepolicy': "storagepolicy_54398_" + self.client_b,
                        'backupset': "defaultBackupSet",
                        'force': True
                    },
                'subclient':
                    {
                        'name': self.test_subclient,
                        'client_name': self.client_a,
                        'data_path': None,
                        'level': 1,
                        'size': 1000,
                        'description': "Automation - Target properties",
                        'subclient_type': None,
                    }
            }
            self.entities.create(subclient_inputs)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()

        def run(self):

            """Run function of this test case"""

        self.log.info('*' * 10 + "Started executing testcase 54398" + '*' * 10)
        try:

            # CLIENT GROUP LEVEL

            # Set one way between clientgrp_a and clientgrp_b
            self.network_helper.set_one_way({'clientGroupName': self.clientgrp_b},
                                            {'clientGroupName': self.clientgrp_a})
            # commenting this setting until we have issue resolved with empty proxy tag
            # self.network_helper.outgoing_route_settings({'clientGroupName': self.clientgrp_a},
            #                                            **{'remote_entity': self.clientgrp_b,
            #                                               'is_client': False,
            #                                               'force_all_data_traffic': False,
            #                                               'connection_protocol': 2})

            # Add extra ports on client_b machine
            self.log.info("Adding extra ports on client: {0}".format(self.client_b))
            self.network_helper.set_extra_ports(self.clientgrp_b, True,
                                                [{'startPort': self.start_port, 'endPort': self.end_port}])

            # Push Configuration
            self.network_helper.push_config_clientgroup(self.client_grp_list)

            # Check summary for extra ports
            clients_summary = self.network_helper.get_network_summary(self.client_names_list)
            client_a_summary = clients_summary[self.client_a]
            self.log.info("Client a network summary: {}".format(client_a_summary))
            client_b_summary = clients_summary[self.client_b]
            self.log.info("Client b network summary: {}".format(client_b_summary))

            # if ((self.client_a + " " + self.client_b) not in client_a_summary
            #        or 'extraports={0}-{1}'.format(self.start_port, self.end_port) not in
            #        client_a_summary):
            #    raise Exception("Network summary incorrect on client_a. extraports missing")

            # if ((self.client_b + " " + self.client_a) not in client_b_summary
            #        or '{0}-{1}'.format(self.start_port, self.end_port) not in
            #        client_b_summary):
            #    raise Exception("Network summary incorrect on client_b. data_ports missing.")

            # configure the force_all_data_traffic option on client_a machine
            self.log.info("Forcing all data traffic through tunnel on clientgrp: {0}".format(self.clientgrp_a))
            self.network_helper.outgoing_route_settings({'clientGroupName': self.clientgrp_a},
                                                        **{'remote_entity': self.clientgrp_b,
                                                           'is_client': False,
                                                           'force_all_data_traffic': True,
                                                           'connection_protocol': 2})

            self.network_helper.push_config_clientgroup(self.client_grp_list)

            # Check summary for extra ports
            clients_summary = self.network_helper.get_network_summary(self.client_names_list)
            client_a_summary = clients_summary[self.client_a]
            self.log.info("Client a network summary: {}".format(client_a_summary))
            client_b_summary = clients_summary[self.client_b]
            self.log.info("Client b network summary: {}".format(client_b_summary))

            # if ((self.client_a + " " + self.client_b) not in client_a_summary
            #        or 'extraports={0}-{1}'.format(self.start_port, self.end_port) in
            #        client_a_summary):
            #    raise Exception("Network summary incorrect on client_a. extraports present")

            # if ((self.client_b + " " + self.client_a) not in client_b_summary
            #        or '{0}-{1}'.format(self.start_port, self.end_port) not in
            #        client_b_summary):
            #    raise Exception("Network summary incorrect on client_b. data_ports missing.")

            # Enable firewall
            self.network_helper.enable_firewall([self.client_b], [8403])

            # Run backup job
            self.client_a_obj = self.commcell.clients.get(self.client_a)

            agent_obj = self.client_a_obj.agents.get('File System')
            backupset_obj = agent_obj.backupsets.get('defaultBackupSet')
            self.fs_subclient = backupset_obj.subclients.get(self.test_subclient)
            self.log.info("Starting backup job")
            backup_job = self.fs_subclient.backup("FULL")
            if not backup_job.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(backup_job.delay_reason)
                )
            self.log.info("Backup job: %s completed successfully", backup_job.job_id)

            self.log.info("*" * 10 + " Part 1 :TestCase {0} successfully passed for Client Group Level! ".format(
                self.id) + "*" * 10)

            self.log.info("Deleting client groups")
            for client_group in self.client_grp_list:
                if self.clients_grps_obj.has_clientgroup(client_group):
                    self.clients_grps_obj.delete(client_group)

            self.network_helper.disable_firewall([self.client_b], [8403])

            self.network_helper.remove_network_config([{'clientName': self.client_a},
                                                       {'clientName': self.client_b},
                                                       ])

            # CLIENT LEVEL

            # Set one way between client_a and client_b
            self.network_helper.set_one_way({'clientName': self.client_b}, {'clientName': self.client_a})

            self.network_helper.outgoing_route_settings({'clientName': self.client_a},
                                                        **{'remote_entity': self.client_b,
                                                           'is_client': True,
                                                           'force_all_data_traffic': False,
                                                           'connection_protocol': 2})

            # Add extra ports on client_b machine
            self.log.info("Adding extra ports on client: {}".format(self.client_b))
            self.network_helper.set_extra_ports(self.client_b, False,
                                                [{'startPort': self.start_port, 'endPort': self.end_port}])

            # Push Configuration
            self.network_helper.push_config_client(self.client_names_list)

            # Check summary for extra ports
            clients_summary = self.network_helper.get_network_summary(self.client_names_list)
            client_a_summary = clients_summary[self.client_a]
            self.log.info("Client a network summary: {}".format(client_a_summary))
            client_b_summary = clients_summary[self.client_b]
            self.log.info("Client b network summary: {}".format(client_b_summary))

            if ((self.client_a + " " + self.client_b) not in client_a_summary
                    or 'extraports={0}-{1}'.format(self.start_port, self.end_port) not in
                    client_a_summary):
                raise Exception("Network summary incorrect on client_a. extraports missing")

            if ((self.client_b + " " + self.client_a) not in client_b_summary
                    or '{0}-{1}'.format(self.start_port, self.end_port) not in
                    client_b_summary):
                raise Exception("Network summary incorrect on client_b. data_ports missing.")

            # configure the force_all_data_traffic option on client_a machine
            self.log.info("Forcing all data traffic through tunnel on client: {}".format(self.client_a))
            self.network_helper.outgoing_route_settings({'clientName': self.client_a},
                                                        **{'remote_entity': self.client_b,
                                                           'is_client': True,
                                                           'force_all_data_traffic': True,
                                                           'connection_protocol': 2})

            self.network_helper.push_config_client(self.client_names_list)

            # Check summary for extra ports
            clients_summary = self.network_helper.get_network_summary(self.client_names_list)
            client_a_summary = clients_summary[self.client_a]
            self.log.info("Client a network summary: {}".format(client_a_summary))
            client_b_summary = clients_summary[self.client_b]
            self.log.info("Client b network summary: {}".format(client_b_summary))

            if ((self.client_a + " " + self.client_b) not in client_a_summary
                    or 'extraports={0}-{1}'.format(self.start_port, self.end_port) in
                    client_a_summary):
                raise Exception("Network summary incorrect on client_a. extraports present")

            if ((self.client_b + " " + self.client_a) not in client_b_summary
                    or '{0}-{1}'.format(self.start_port, self.end_port) not in
                    client_b_summary):
                raise Exception("Network summary incorrect on client_b. data_ports missing.")

            self.network_helper.enable_firewall([self.client_b], [8403])

            # Run backup job
            self.log.info("Starting backup job")
            backup_job = self.fs_subclient.backup("FULL")
            if not backup_job.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(backup_job.delay_reason)
                )
            self.log.info("Backup job: %s completed successfully", backup_job.job_id)

            self.network_helper.disable_firewall([self.client_b], [8403])

            self.log.info("*" * 10 + " Part 2 :TestCase {0} successfully passed for Client Level! ".format(
                self.id) + "*" * 10)

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()

    def tear_down(self):
        """Tear down function of this test case"""

        self.log.info("Deleting client groups")
        for client_group in self.client_grp_list:
            if self.clients_grps_obj.has_clientgroup(client_group):
                self.clients_grps_obj.delete(client_group)

        if self.network_helper is not None:
            self.network_helper.remove_network_config([{'clientName': self.client_a},
                                                       {'clientName': self.client_b},
                                                       ])
            self.network_helper.entities.cleanup()
