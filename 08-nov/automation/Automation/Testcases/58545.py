# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to validate indexing force checkpoint

TestCase:
    __init__()                       --  Initializes the TestCase class

    setup()                          --  All testcase objects are initializes in this method

    checkpoint_after_time_change()   -- Moves CS/MA time ahead by the number of
                                        days specified, run checkpoint and return
                                        the list of DBs checkpointed

    restart_time_service()           -- Restart time service on the given client

    run()                            --  Contains the core testcase logic and it is the one executed

    tear_down()                      --  Cleans the data created for Indexing validation
"""

import traceback
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db



class TestCase(CVTestCase):

    """Verify Force checkpoint"""

    def __init__(self):
        """Initializes the TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Indexing - Force checkpoint verification"
        self.tcinputs = {
            'StoragePolicy': None
        }

        self.ctree_obj = None
        self.cs_machine_obj = None
        self.storage_policy = None
        self.index_class_obj = None
        self.cl_machine = None
        self.indexingtestcase = None
        self.backupset_obj = None
        self.subclient_obj = None
        self.ctree_obj = None
        self.indexing_level = None
        self.indexing_version = None

    def setup(self):
        """All testcase objects are initializes in this method"""
        try:

            self.cl_machine = Machine(self.client)
            self.cs_machine_obj = Machine(
                self.commcell.clients.get(self.commcell.commserv_name))

            # Storage policy
            self.storage_policy = self.tcinputs.get('StoragePolicy')

            # Indexing class object initialization
            self.index_class_obj = IndexingHelpers(self.commcell)
            self.indexingtestcase = IndexingTestcase(self)

            self.log.info("Creating backupset and subclient..")
            self.backupset_obj = self.indexingtestcase.create_backupset(
                name='backupset_force_checkpoint',
                for_validation=False)

            self.subclient_obj = self.indexingtestcase.create_subclient(
                name="sc1",
                backupset_obj=self.backupset_obj,
                storage_policy=self.storage_policy,
                register_idx=False)

            self.log.info("Subclient content is: {0}".format(self.subclient_obj.content))
            self.log.info("Generating test data for subclient content")
            self.indexingtestcase.new_testdata(self.subclient_obj.content)

            self.subclient_obj.allow_multiple_readers = True
            self.subclient_obj.data_readers = 4

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def checkpoint_after_time_change(self, client_object,
                                     ctree_object, move_days=0, stop_time__service=True):
        """ Move system time ahead by the number of days specified on the specified client.

                Args:
                    client_object    (obj)   --  object of the client
                                                    where time has to be moved.

                    ctree_object    (obj)      --  ctree class object.

                    move_days    (integer)   --  number of days to be moved

                    stop_time__service (boolean)  -- Decided weather to restart time service or not

                Returns:
                    list -   list of checkpoints

                """

        if stop_time__service:
            self.log.info("Stopping time service..")
            client_object.toggle_time_service(stop=True)

        if move_days > 0:
            self.log.info("Current time of CS/MA is "
                          ": {0} ".format(client_object.current_time()))
            self.log.info("Moving system time ahead for {0} days..".format(move_days))
            try:
                client_object.add_days_to_system_time(move_days)
            except Exception as exp:
                self.log.info("Excepetion occured {0}".format(exp))

            self.log.info("Current time of CS/MA is "
                          ": {0} ".format(client_object.current_time()))

        self.log.info("Checkpointing all backupset DBs")
        ctree_object.checkpoint_db(by_all_index_backup_clients=True, registry_keys=False)

        list = ctree_object.get_index_db_checkpoints()
        self.log.info("list of index checkpoints made for the database.. {0}".format(list))

        return list

    def restart_time_service(self, client_obj):
        """ Restart time service on the given client.

                       Args:
                           client_object    (obj)   --  object of the client on which time
                                                        service has to be restarted.

                       Returns:
                           None

                       """

        self.log.info("Restarting time service to set "
                      "system time to current time")
        client_obj.toggle_time_service(stop=True)
        try:
            client_obj.toggle_time_service(stop=False)
        except Exception as exp:
            self.log.info(" Exception occured is: {0}".format(exp))

    def run(self):
        """Contains the core testcase logic and it is the one executed

        Steps:
            1 - Restart time service to make sure system time is set to current time
            2-  Delete all the registry keys related to checkpoint and compaction
            3 - Run full backup job and wait for its completion
            3 - Run Index backup job and check if checkpoint has been created or not
            4 - Move system time ahead for 5 days
            5 - Run Index backup job and check if checkpoint has been created or not
            6 - Move system time ahead for 8 days
            7 - Run Index backup job and check if force checkpoint has happened or not
            8 - Restart time service to change system time to current time in teardown()


        """

        try:
            # Starting the testcase
            self.log.info("Started executing {0} testcase ".format(self.id))

            self.restart_time_service(self.cs_machine_obj)

            self.log.info("Current time of CS/MA at the start of the testcase "
                          "is : {0} ".format(self.cs_machine_obj.current_time()))

            # Deleting registry keys
            self.log.info("Deleting registry keys ")
            self.cs_machine_obj.remove_registry('Indexing', 'CHKPOINT_ENFORCE_DAYS')
            self.cs_machine_obj.remove_registry('Indexing', 'CHKPOINT_ITEMS_ADDED_MIN')
            self.cs_machine_obj.remove_registry('Indexing', 'CHKPOINT_MIN_DAYS')
            self.cs_machine_obj.remove_registry('Indexing', 'CHKPOINT_AFILES_AGED_MIN')
            self.cs_machine_obj.remove_registry('Indexing', 'COMPACTION_ENFORCE_DAYS')
            self.cs_machine_obj.remove_registry(
                'Indexing',
                'FULL_COMPACTION_MIN_PERCENT_AFILE_AGED')
            self.log.info("deleted reg keys..")

            # Checking client's Indexing version
            self.indexing_version = self.index_class_obj.get_agent_indexing_version(
                self.client,
                agent_short_name=None
            )
            self.log.info("Indexing Version is: {0}".format(self.indexing_version))

            if self.indexing_version == 'v1':
                raise Exception(" This is V1 client ")

            self.log.info('************* Running backup jobs *************')
            # Starting full backup and not waiting for that

            self.indexingtestcase.run_backup(
                self.subclient_obj,
                backup_level='Full',
                verify_backup=False,
                restore=False)

            self.log.info("Creating object for CTreeDB class")
            self.indexing_level = self.index_class_obj.get_agent_indexing_level(self.agent)
            self.log.info("Agent Index Level is: {0}".format(self.indexing_level))
            if self.indexing_level == 'backupset':
                self.ctree_obj = index_db.get(self.backupset_obj)
            else:
                self.ctree_obj = index_db.get(self.subclient_obj)
            self.log.info("Created object for CTreeDB class")
            ########################################################################

            list1 = self.checkpoint_after_time_change(
                client_object=self.cs_machine_obj,
                ctree_object=self.ctree_obj,
                move_days=0,
                stop_time__service=False)

            self.log.info("Verifying list..")
            if len(list1) == 1:
                self.log.info("DB has been checkpointed as expected..")
            else:
                raise Exception("DB has not been checkpointed which is not expected")

            list2 = self.checkpoint_after_time_change(
                client_object=self.cs_machine_obj,
                ctree_object=self.ctree_obj,
                move_days=5,
                stop_time__service=True)

            self.log.info("Verifying list..")
            if len(list2) == 1:
                self.log.info("DB has not been force checkpointed as expected..")
            else:
                raise Exception("DB has been force checkpointed which is not expected")

            self.restart_time_service(self.cs_machine_obj)
            list3 = self.checkpoint_after_time_change(
                client_object=self.cs_machine_obj,
                ctree_object=self.ctree_obj,
                move_days=8,
                stop_time__service=True)

            self.log.info("Verifying list..")
            if len(list3) == 2:
                self.log.info("DB has been force checkpointed as expected..")
            else:
                raise Exception("DB hasn't been force checkpointed ")

            self.log.info("Current time of CS/MA at the end of the testcase "
                          "is : {0} ".format(self.cs_machine_obj.current_time()))

        except Exception as exp:
            self.log.error("Test case failed with error: {0}".format(exp))
            self.log.exception(exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def tear_down(self):
        """Cleans the data created for Indexing validation"""
        try:
            self.restart_time_service(self.cs_machine_obj)
            self.log.info("Changed system time to current time")
            self.log.info("Current time of CS/MA is "
                          ": {0} ".format(self.cs_machine_obj.current_time()))

        except Exception as exp:
            self.log.exception(exp)
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)
