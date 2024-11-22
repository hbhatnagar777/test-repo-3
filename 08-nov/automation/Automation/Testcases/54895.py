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
    Compare backup peformance on AIX client between with and without encrypted network routes configured between Client and MA.

    steps to do:

    1. configure the storage policy, subclient -- on LINUX Agent
    2. run backup and get the job details for performance measure
    3. Change the network settings for the client ( one way firewall, outgoing routes , push config , enable firewall)
    4. Run backup job and get the job details for performance
    5. Compare backup vs backup_encrypted ?? ( Falling into particular range )

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.network import Network
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.options_selector import CVEntities
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)     -  name of this test case
                applicable_os       (str)     —  applicable os for this test case
                                                            Ex: self.os_list.WINDOWS
                product             (str)     —  applicable product for this test case
                                                                 Ex: self.products_list.FILESYSTEM
                features            (str)     —  qcconstants feature_list item
                                                             Ex: self.features_list.DATAPROTECTION
                show_to_user        (bool)    —  test case flag to determine if the test case is
                                                             to be shown to user or not
                Accept:             (bool)
                                    True      –   test case will be shown to user from commcell gui
                                    False     –   test case will not be shown to user
                default: False
                tcinputs            (dict)    -  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "Compare backup peformance on AIX client between with " \
                    "and without encrypted network routes configured between Client and MA."
        self.applicable_os = self.os_list.LINUX
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None,
            "media_agent_name": None,
        }

        self.network_sdk = None
        self.network_helper = None
        self.entities = None

        # Subclient Info
        self.test_subclient = "test_54895_subclient"
        self.content_drive = "/"
        self.content_folder = "testData_54266"

        self.media_agent = None
        self.fs_subclient = None
        self.sp_ma = None
        self.client_port = None
        self.ma_port = None

    def setup(self):
        """Setup function of this test case"""

        self.network_sdk = Network(self.client)
        self.network_helper = NetworkHelper(self)
        self.entities = CVEntities(self.commcell)

        self.media_agent = self.media_agent

        self.sp_ma = self.create_storage_policy_assoc(self.media_agent, self.client, self.test_subclient,
                                                      self.content_drive,
                                                      self.content_folder)

        self.network_helper.remove_network_config([{'clientName': self.client.client_name},
                                                   {'clientName': self.media_agent},
                                                   ])

    def run(self):
        """Run function of this test case"""
        self.log.info("Started executing testcase 54895")
        agent_obj = self.client.agents.get('File System')
        backupset_obj = agent_obj.backupsets.get('defaultBackupSet')
        self.fs_subclient = backupset_obj.subclients.get(self.test_subclient)
        try:

            # Run FULL backup without network route configuration
            self.log.info("Starting backup job")
            backup_job = self.fs_subclient.backup("FULL")
            if not backup_job.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(backup_job.delay_reason)
                )
            self.log.info("Backup job: %s completed successfully", backup_job.job_id)

            # Configuring the encrypted network between the client and MA

            # Setting one way firewall
            self.network_helper.set_one_way({'clientName': self.media_agent},
                                            {'clientName': self.client.client_name})

            # Setting outgoing route
            self.network_helper.outgoing_route_settings({'clientName': self.client.client_name},
                                                        is_client=True,
                                                        remote_entity=self.media_agent,
                                                        connection_protocol=1,
                                                        streams=1,
                                                        route_type="DIRECT")

            # Push network configuration onto clients
            self.network_helper.push_config_client([self.client.client_name,
                                                    self.media_agent])

            # Enabling system firewall on client and media agent machine
            self.client_port = self.network_helper.client_tunnel_port(self.client.client_name)
            self.ma_port = self.network_helper.client_tunnel_port(self.media_agent)
            self.network_helper.enable_firewall([self.client.client_name, self.media_agent],
                                                [self.client_port, self.ma_port])

            # Checking readiness of the client for max 3 tries
            check_readiness = 1
            while check_readiness <= 3:
                self.log.info("Trying check readiness. Attempt no: {0}".format(check_readiness))
                if (self.network_helper.serverbase.check_client_readiness(
                        [self.client.client_name, self.media_agent], hardcheck=False)):
                    self.log.info("Check readiness for clients is successful")
                    break
                self.network_helper.options.sleep_time(10)
                check_readiness += 1
            else:
                self.log.error("Check readiness failed")
                raise Exception

                # Running the backup job with encrypted network settings
            self.log.info("Starting backup job with encryption")
            backup_job_encrypted = self.fs_subclient.backup("FULL")
            if not backup_job_encrypted.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(backup_job_encrypted.delay_reason)
                )
            self.log.info("Backup job: %s completed successfully", backup_job_encrypted.job_id)


        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()

    def tear_down(self):
        """Tear down function of this test case"""

        if self.network_helper is not None:
            self.network_helper.disable_firewall([self.client.client_name], [self.client_port])
            self.network_helper.remove_network_config([{'clientName': self.client.client_name},
                                                       {'clientName': self.media_agent},
                                                       ])
            self.network_helper.cleanup_network()
            storage_policies_obj = self.commcell.storage_policies
            if storage_policies_obj.has_policy(self.sp_ma):
                storage_policies_obj.delete(self.sp_ma)

        if self.entities is not None:
            self.entities.cleanup()

    def create_storage_policy_assoc(self,
                                    media_agent,
                                    client,
                                    subclient_name,
                                    content_drive,
                                    content_folder,
                                    ):
        # Create disklibrary
        media_agent_helper = MMHelper(self)
        disk_library_name = "disklibrary_test_" + media_agent + client
        media_agent_helper.configure_disk_library(disk_library_name,
                                                  media_agent,
                                                  self.entities.get_mount_path(media_agent))
        self.log.info("Created disk library using media agent %s", media_agent)

        # create storage policy
        storage_policy_name = "storagepolicy_54266_" + media_agent + client
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
                    'data_path': content_drive + content_folder,
                    'level': 1,
                    'size': 1000,
                    'description': "Automation - Target properties",
                    'subclient_type': None,
                }
        }
        self.entities.create(subclient_inputs)
        return storage_policy_name


    def verify_performance_metrics(self):
        # TODO : add Logic for performance comparision
        # backup_job performance dict
        # backup_job_performance = {'transfer_time': backup_job.details['jobDetail']['detailInfo']['transferTime'],
        #                           'throughput': backup_job.details['jobDetail']['detailInfo']['throughPut'],
        #                           'read_throughput_Mbpersec': backup_job.details['jobDetail']['generalInfo'][
        #                               'readThroughtputInMBPerSec'],
        #                           'write_throughput_Mbpersec': backup_job.details['jobDetail']['generalInfo'][
        #                               'writeThroughtputInMBPerSec']}

        # backup_job_encrypted performance dict
        # backup_job_encrypted_performance = {
        #     'transfer_time': backup_job_encrypted.details['jobDetail']['detailInfo']['transferTime'],
        #     'throughput': backup_job_encrypted.details['jobDetail']['detailInfo']['throughPut'],
        #     'read_throughput_Mbpersec': backup_job_encrypted.details['jobDetail']['generalInfo'][
        #         'readThroughtputInMBPerSec'],
        #     'write_throughput_Mbpersec': backup_job_encrypted.details['jobDetail']['generalInfo'][
        #         'writeThroughtputInMBPerSec']}

        # Printing the required performance metrics ( to use later )
        pass
